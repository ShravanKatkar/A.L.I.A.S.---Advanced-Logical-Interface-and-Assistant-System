import google.generativeai as genai
import os
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
import requests
import json

# Explicitly load .env from backend directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class LLMEngine:
    def __init__(self):
        # 1. Google Gemini Setup
        api_key = os.getenv("GEMINI_API_KEY")
        print(f"DEBUG: GEMINI_API_KEY loaded: {bool(api_key)}") # Debug
        if not api_key:
            print("WARNING: GEMINI_API_KEY not found.")
        else:
            genai.configure(api_key=api_key)
            self.api_key_set = True

        # 2. OpenAI Setup (GitHub Models)
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.openai_client = OpenAI(
                api_key=openai_key,
                base_url="https://models.inference.ai.azure.com"
            )
        else:
            self.openai_client = None

        # 3. DeepSeek Setup
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            # Check if key is also a GitHub token (starts with ghp_)
            if deepseek_key.startswith("ghp_"):
                 self.deepseek_client = OpenAI(
                    api_key=deepseek_key,
                    base_url="https://models.inference.ai.azure.com"
                )
            else:
                self.deepseek_client = OpenAI(
                    api_key=deepseek_key,
                    base_url="https://api.deepseek.com"
                )
        else:
            self.deepseek_client = None

        # 4. Qubrid Setup (GPT-OSS 120B)
        # 4. Qubrid Setup (GPT-OSS 120B)
        self.qubrid_key = os.getenv("QUBRID_API_KEY")

        # 5. Groq Setup
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            self.groq_client = OpenAI(
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1"
            )
        else:
            self.groq_client = None

    def get_available_models(self):
        """Returns a list of available models based on set API keys."""
        models = []
        
        # Gemini Models
        if hasattr(self, 'api_key_set'):
            models.extend([
                "gemini-3-flash-preview",
                "gemini-2.5-flash-preview-09-2025",
                "gemini-3-pro-preview"
            ])
            
        # OpenAI Models
        if self.openai_client:
            models.append("gpt-4o")
            
        # DeepSeek Models
        if self.deepseek_client:
            models.append("DeepSeek-R1")

        # Qubrid Models
        if self.qubrid_key:
            models.append("openai/gpt-oss-120b")

        if self.groq_client:
            models.append("groq/llama-3.3-70b-versatile")
            
        return models

    def generate_response(self, text_input, temperature=0.7, model_name='gemini-2.0-flash-exp'):
        """
        Generates a response from the selected model.
        """
        try:
            # --- ROUTING LOGIC ---
            
            # A. Gemini Models
            if "gemini" in model_name.lower():
                if not hasattr(self, 'api_key_set'):
                    return "I am not connected to Gemini (API Key missing)."
                
                generation_config = genai.types.GenerationConfig(temperature=temperature)
                model = genai.GenerativeModel(model_name)
                chat = model.start_chat(history=[])
                response = chat.send_message(text_input, generation_config=generation_config)
                
                # Robust extraction for newer models
                try:
                    return response.text
                except Exception:
                    # Fallback for "Invalid operation" or empty text
                    if response.candidates:
                        parts = response.candidates[0].content.parts
                        if parts:
                            return parts[0].text
                    return "I received an empty response from the model."

            # D. Qubrid Models (Check this BEFORE generic 'gpt' to avoid catching 'gpt-oss')
            elif "gpt-oss" in model_name.lower() or "qubrid" in model_name.lower():
                if not getattr(self, 'qubrid_key', None):
                    return "I am not connected to Qubrid (API Key missing)."

                url = "https://platform.qubrid.com/api/v1/qubridai/chat/completions"
                headers = {
                  "Authorization": f"Bearer {self.qubrid_key}",
                  "Content-Type": "application/json"
                }

                # Ensure proper model name usage
                target_model = "openai/gpt-oss-120b"

                data = {
                  "model": target_model,
                  "messages": [{"role": "user", "content": text_input}],
                  "temperature": temperature,
                  "max_tokens": 4096,
                  "stream": False,
                  "top_p": 1
                }
                
                # Using explicit timeout as observed in testing
                response = requests.post(url, headers=headers, data=json.dumps(data), timeout=120)
                
                if response.status_code == 200:
                    # Parse response safely
                    try:
                        json_resp = response.json()
                        if 'choices' in json_resp and len(json_resp['choices']) > 0:
                            return json_resp['choices'][0]['message']['content']
                        elif 'content' in json_resp:
                            return json_resp['content']
                        else:
                            return f"Unexpected Qubrid format keys: {list(json_resp.keys())}"
                    except (KeyError, IndexError, json.JSONDecodeError) as e:
                        return f"Error parsing Qubrid response: {e}"
                else:
                    return f"Error from Qubrid: {response.status_code} - {response.text}"

            # E. Groq Models
            elif "groq" in model_name.lower():
                if not self.groq_client:
                    return "I am not connected to Groq (API Key missing)."
                
                # Strip prefix if present (e.g. "groq/llama..." -> "llama...")
                actual_model = model_name.split('/')[-1] if '/' in model_name else model_name

                completion = self.groq_client.chat.completions.create(
                    model=actual_model,
                    messages=[{"role": "user", "content": text_input}],
                    temperature=temperature
                )
                return completion.choices[0].message.content

            # B. OpenAI Models (GPT)
            elif "gpt" in model_name.lower():
                if not self.openai_client:
                    return "I am not connected to OpenAI (API Key missing)."
                
                completion = self.openai_client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": text_input}],
                    temperature=temperature
                )
                return completion.choices[0].message.content

            # C. DeepSeek Models
            elif "deepseek" in model_name.lower():
                if not self.deepseek_client:
                    return "I am not connected to DeepSeek (API Key missing)."
                
                completion = self.deepseek_client.chat.completions.create(
                    model=model_name, # Note: DeepSeek V3 on GitHub might use 'DeepSeek-V3'
                    messages=[{"role": "user", "content": text_input}],
                    temperature=temperature
                )
                return completion.choices[0].message.content

            else:
                return f"Model {model_name} is not supported."

        except Exception as e:
            print(f"LLM Error: {e}")
            return f"I'm having trouble thinking with {model_name} right now. ({e})"
