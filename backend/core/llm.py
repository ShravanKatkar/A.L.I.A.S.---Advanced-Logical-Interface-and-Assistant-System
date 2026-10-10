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
        self._init_clients()

    def _init_clients(self):
        """Initializes AI provider clients from environment variables."""
        # Reload env variables
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)

        # 1. Google Gemini Setup
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        print(f"DEBUG: GEMINI_API_KEY loaded: {bool(api_key)}")
        if not api_key:
            print("WARNING: GEMINI_API_KEY not found.")
            self.api_key_set = False
        else:
            try:
                genai.configure(api_key=api_key)
                self.api_key_set = True
            except Exception as e:
                print(f"[-] Gemini configure error: {e}")
                self.api_key_set = False

        # 2. OpenAI Setup
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        if openai_key and not openai_key.startswith("#"):
            try:
                if openai_key.startswith("ghp_"):
                    self.openai_client = OpenAI(
                        api_key=openai_key,
                        base_url="https://models.inference.ai.azure.com"
                    )
                else:
                    self.openai_client = OpenAI(api_key=openai_key)
            except Exception as e:
                print(f"[-] OpenAI init error: {e}")
                self.openai_client = None
        else:
            self.openai_client = None

        # 3. DeepSeek Setup
        deepseek_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        self.deepseek_balance_error = False
        if deepseek_key and not deepseek_key.startswith("#"):
            try:
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
                # Quick verification of balance/validity with short timeout
                try:
                    self.deepseek_client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": "hi"}],
                        max_tokens=1,
                        timeout=3.0
                    )
                except Exception as de:
                    err_str = str(de).lower()
                    if "402" in err_str or "insufficient balance" in err_str:
                        print("[-] DeepSeek key has Insufficient Balance (402). Omitting DeepSeek models.")
                        self.deepseek_balance_error = True
                    elif "401" in err_str or "invalid" in err_str:
                        print(f"[-] DeepSeek key invalid: {de}")
                        self.deepseek_client = None
                    else:
                        print(f"[-] DeepSeek check warning: {de}")
            except Exception as e:
                print(f"[-] DeepSeek init error: {e}")
                self.deepseek_client = None
        else:
            self.deepseek_client = None

        # 4. Qubrid Setup
        qubrid_key = os.getenv("QUBRID_API_KEY", "").strip()
        self.qubrid_key = qubrid_key if qubrid_key and not qubrid_key.startswith("#") else None

        # 5. Groq Setup
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        if groq_key and not groq_key.startswith("#"):
            try:
                self.groq_client = OpenAI(
                    api_key=groq_key,
                    base_url="https://api.groq.com/openai/v1"
                )
            except Exception as e:
                print(f"[-] Groq init error: {e}")
                self.groq_client = None
        else:
            self.groq_client = None

    def reload_keys(self):
        """Reloads environment variables and re-initializes all AI clients."""
        print("[+] Reloading API keys and re-initializing LLM engine...")
        self._init_clients()

    def get_provider_status(self) -> dict:
        """Returns the configuration status and masked keys for all supported providers."""
        def mask(k):
            if not k:
                return ""
            if len(k) <= 8:
                return "****"
            return f"{k[:4]}...{k[-4:]}"

        gemini_k = os.getenv("GEMINI_API_KEY", "").strip()
        groq_k = os.getenv("GROQ_API_KEY", "").strip()
        deepseek_k = os.getenv("DEEPSEEK_API_KEY", "").strip()
        openai_k = os.getenv("OPENAI_API_KEY", "").strip()

        return {
            "gemini": {
                "configured": bool(gemini_k and getattr(self, 'api_key_set', False)),
                "key_masked": mask(gemini_k),
                "status": "Active" if getattr(self, 'api_key_set', False) else "Not configured"
            },
            "groq": {
                "configured": bool(groq_k and self.groq_client),
                "key_masked": mask(groq_k),
                "status": "Active" if self.groq_client else "Not configured"
            },
            "deepseek": {
                "configured": bool(deepseek_k and self.deepseek_client),
                "key_masked": mask(deepseek_k),
                "has_balance": not getattr(self, 'deepseek_balance_error', False),
                "status": "Insufficient Balance (402)" if getattr(self, 'deepseek_balance_error', False) else ("Active" if self.deepseek_client else "Not configured")
            },
            "openai": {
                "configured": bool(openai_k and self.openai_client),
                "key_masked": mask(openai_k),
                "status": "Active" if self.openai_client else "Not configured"
            }
        }

    def test_api_key(self, provider: str, key: str) -> dict:
        """Tests an API key for a specified provider before saving."""
        if not key or not key.strip():
            return {"success": False, "message": "Key cannot be empty."}

        key = key.strip()
        provider = provider.lower().strip()

        try:
            if provider == "gemini":
                genai.configure(api_key=key)
                m = genai.GenerativeModel("gemini-2.5-flash")
                res = m.generate_content("Hello")
                if res and res.text:
                    return {"success": True, "message": "Gemini API key is valid and connected!"}
                return {"success": False, "message": "Gemini returned empty response."}

            elif provider == "groq":
                client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
                res = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=3
                )
                if res.choices:
                    return {"success": True, "message": "Groq API key is valid and connected!"}
                return {"success": False, "message": "Groq returned empty response."}

            elif provider == "deepseek":
                client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=3
                )
                if res.choices:
                    return {"success": True, "message": "DeepSeek API key is valid and active!"}
                return {"success": False, "message": "DeepSeek returned empty response."}

            elif provider == "openai":
                client = OpenAI(api_key=key)
                models = client.models.list()
                return {"success": True, "message": "OpenAI API key is valid and connected!"}

            else:
                return {"success": False, "message": f"Unsupported provider: {provider}"}

        except Exception as e:
            err_msg = str(e)
            if "402" in err_msg or "Insufficient Balance" in err_msg:
                return {"success": False, "message": "API key recognized, but account has 0 balance (402 Insufficient Balance)."}
            if "401" in err_msg or "invalid_api_key" in err_msg:
                return {"success": False, "message": "Invalid API key."}
            return {"success": False, "message": f"Connection test failed: {err_msg}"}

    def get_available_models(self):
        """Returns a list of verified, fully functioning models based on set API keys."""
        models = []

        # 1. Gemini Models (only active, working models - removed 404 deprecated ones)
        if getattr(self, 'api_key_set', False):
            models.extend([
                "gemini-2.5-flash",
                "gemini-3.5-flash",
                "gemini-3.7-flash",
                "gemini-3.8-flash",
                "gemini-flash-latest"
            ])

        # 2. Groq Models (verified working on Groq LPU)
        if self.groq_client:
            models.extend([
                "groq/openai/gpt-oss-120b",
                "groq/openai/gpt-oss-20b",
                "groq/qwen/qwen3.8-27b"
            ])

        # 3. OpenAI Models (only if valid key set)
        if self.openai_client:
            models.append("gpt-4o")

        # 4. DeepSeek Models (only if valid and funded)
        if self.deepseek_client and not getattr(self, 'deepseek_balance_error', False):
            models.extend([
                "deepseek-chat",
                "deepseek-reasoner"
            ])

        # 5. Qubrid Models
        if self.qubrid_key:
            models.append("openai/gpt-oss-120b")

        return models

    def generate_response(self, text_input, temperature=0.7, model_name='gemini-2.5-flash', token_callback=None):
        """
        Generates a response from the selected model, supporting streaming when token_callback is provided.
        """
        try:
            # --- ROUTING LOGIC ---

            # A. Gemini Models
            if "gemini" in model_name.lower():
                if not getattr(self, 'api_key_set', False):
                    return "I am not connected to Gemini (API Key missing)."

                generation_config = genai.types.GenerationConfig(temperature=temperature)
                model = genai.GenerativeModel(model_name)

                if token_callback:
                    response = model.generate_content(text_input, generation_config=generation_config, stream=True)
                    full_text = ""
                    for chunk in response:
                        try:
                            token = chunk.text
                            if token:
                                full_text += token
                                token_callback(token)
                        except Exception:
                            pass
                    return full_text
                else:
                    chat = model.start_chat(history=[])
                    response = chat.send_message(text_input, generation_config=generation_config)

                    try:
                        return response.text
                    except Exception:
                        if response.candidates:
                            parts = response.candidates[0].content.parts
                            if parts:
                                return parts[0].text
                        return "I received an empty response from the model."

            # B. Groq Models (Check before generic gpt/qubrid to catch groq/ prefixed or Groq-hosted models)
            elif "groq" in model_name.lower() or (self.groq_client and any(m in model_name for m in ["gpt-oss", "qwen"])):
                if not self.groq_client:
                    return "I am not connected to Groq (API Key missing)."

                # Strip 'groq/' prefix cleanly without stripping model organization
                actual_model = model_name
                if actual_model.startswith("groq/"):
                    actual_model = actual_model[5:]

                if token_callback:
                    completion = self.groq_client.chat.completions.create(
                        model=actual_model,
                        messages=[{"role": "user", "content": text_input}],
                        temperature=temperature,
                        stream=True
                    )
                    full_text = ""
                    for chunk in completion:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_text += content
                            token_callback(content)
                    return full_text
                else:
                    completion = self.groq_client.chat.completions.create(
                        model=actual_model,
                        messages=[{"role": "user", "content": text_input}],
                        temperature=temperature
                    )
                    return completion.choices[0].message.content

            # C. Qubrid Models
            elif "qubrid" in model_name.lower() or ("gpt-oss" in model_name.lower() and getattr(self, 'qubrid_key', None)):
                if not getattr(self, 'qubrid_key', None):
                    return "I am not connected to Qubrid (API Key missing)."

                url = "https://platform.qubrid.com/api/v1/qubridai/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.qubrid_key}",
                    "Content-Type": "application/json"
                }

                target_model = "openai/gpt-oss-120b"
                data = {
                    "model": target_model,
                    "messages": [{"role": "user", "content": text_input}],
                    "temperature": temperature,
                    "max_tokens": 4096,
                    "stream": False,
                    "top_p": 1
                }

                response = requests.post(url, headers=headers, data=json.dumps(data), timeout=120)
                if response.status_code == 200:
                    json_resp = response.json()
                    text_out = ""
                    if 'choices' in json_resp and len(json_resp['choices']) > 0:
                        text_out = json_resp['choices'][0]['message']['content']
                    elif 'content' in json_resp:
                        text_out = json_resp['content']
                    else:
                        text_out = f"Unexpected Qubrid format keys: {list(json_resp.keys())}"

                    if token_callback and text_out:
                        token_callback(text_out)
                    return text_out
                else:
                    return f"Error from Qubrid: {response.status_code} - {response.text}"

            # D. OpenAI Models (GPT)
            elif "gpt" in model_name.lower():
                if not self.openai_client:
                    return "I am not connected to OpenAI (API Key missing)."

                if token_callback:
                    completion = self.openai_client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": text_input}],
                        temperature=temperature,
                        stream=True
                    )
                    full_text = ""
                    for chunk in completion:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_text += content
                            token_callback(content)
                    return full_text
                else:
                    completion = self.openai_client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": text_input}],
                        temperature=temperature
                    )
                    return completion.choices[0].message.content

            # E. DeepSeek Models
            elif "deepseek" in model_name.lower():
                if not self.deepseek_client:
                    return "I am not connected to DeepSeek (API Key missing)."
                if getattr(self, 'deepseek_balance_error', False):
                    return "DeepSeek account has insufficient balance (402). Please top up your DeepSeek balance or choose a Gemini or Groq model."

                if token_callback:
                    completion = self.deepseek_client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": text_input}],
                        temperature=temperature,
                        stream=True
                    )
                    full_text = ""
                    for chunk in completion:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_text += content
                            token_callback(content)
                    return full_text
                else:
                    completion = self.deepseek_client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": text_input}],
                        temperature=temperature
                    )
                    return completion.choices[0].message.content

            else:
                return f"Model {model_name} is not supported."

        except Exception as e:
            print(f"LLM Error: {e}")
            return f"I'm having trouble thinking with {model_name} right now. ({e})"

    def extract_memory_operations(self, user_input: str, assistant_response: str, existing_memories: list) -> list:
        """
        Uses Gemini to extract memory operations (add, update, delete) from a conversation turn.
        """
        if not getattr(self, 'api_key_set', False):
            return []

        memories_str = "\n".join([f"- ID {m['id']}: {m['fact']}" for m in existing_memories])

        prompt = f"""
You are the memory manager of ALIAS, a personal AI assistant.
Your task is to analyze the latest user message and ALIAS's response to determine if any updates are needed for the user's long-term memory.

Existing user memories:
{memories_str}

Conversation turn:
User: {user_input}
ALIAS: {assistant_response}

Instructions:
1. Identify facts about the user that are likely to remain useful in future conversations (e.g. name, goals, preferences, skills, background, projects, tools, etc.).
2. You can perform three actions:
   - "add": Add a new fact if it is not already in the existing memories and is useful.
   - "update": Update an existing memory (by its ID) if the user is changing or correcting that specific information (e.g. changing their major, moving to a new city).
   - "delete": Delete an existing memory (by its ID) if the user explicitly asks you to forget/delete that information (e.g. "forget that I use Python" or "delete my favorite programming language").
3. Do not store temporary or irrelevant details (like "user is looking at VS Code", "user generated an image of a car", or chat niceties).
4. Output ONLY a valid JSON array of objects representing the memory operations. If no changes are needed, output an empty array: [].
5. Format details:
   - For add: {{"action": "add", "fact": "fact text"}}
   - For update: {{"action": "update", "id": <memory_id>, "fact": "new fact text"}}
   - For delete: {{"action": "delete", "id": <memory_id>}}

JSON Output:
"""
        try:
            generation_config = genai.types.GenerationConfig(temperature=0.1)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt, generation_config=generation_config)

            text = response.text.strip()
            if text.startswith("```json"):
                text = text.split("```json")[1].split("```")[0].strip()
            elif text.startswith("```"):
                text = text.split("```")[1].split("```")[0].strip()

            ops = json.loads(text)
            if isinstance(ops, list):
                return ops
        except Exception as e:
            print(f"[-] Error extracting memory operations: {e}")

        return []
