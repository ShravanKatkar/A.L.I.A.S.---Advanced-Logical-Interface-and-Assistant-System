from core.llm import LLMEngine
from core.tts import TTSEngine
import core.history_memory as history_memory
from modules.app_control import AppController
from modules.file_ops import FileOps
from modules.window_awareness import WindowAwareness
from modules.email_ops import EmailOps
from core.rag import RAGEngine
import sys
import os
import platform
import importlib.util

# Paths to Friday modules (friday is a sibling of backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRIDAY_PATH = os.path.join(BASE_DIR, "friday")

if FRIDAY_PATH not in sys.path:
    sys.path.append(FRIDAY_PATH)

try:
    # Load image_generator from friday/image_generator.py dynamically to prevent IDE resolution errors
    spec_img = importlib.util.spec_from_file_location("image_generator", os.path.join(FRIDAY_PATH, "image_generator.py"))
    image_generator = importlib.util.module_from_spec(spec_img)
    spec_img.loader.exec_module(image_generator)

    # Load main from friday/main.py dynamically to prevent collisions with backend/main.py
    spec_main = importlib.util.spec_from_file_location("friday_main", os.path.join(FRIDAY_PATH, "main.py"))
    cli_main = importlib.util.module_from_spec(spec_main)
    spec_main.loader.exec_module(cli_main)
    
    print("[+] Successfully loaded Friday image generation modules dynamically.")
except Exception as e:
    print(f"[-] Warning: Failed to import Friday image generation module: {e}")
    image_generator = None
    cli_main = None

class CommandProcessor:
    def __init__(self, llm: LLMEngine, tts: TTSEngine):
        self.llm = llm
        self.tts = tts
        self.app_ctrl = AppController()
        self.file_ops = FileOps()
        self.vision = WindowAwareness()
        self.email_ops = EmailOps()
        self.rag = RAGEngine()
        self.system_os = platform.system()

    def process(self, text, temperature=0.7, model='gemini-2.5-flash', user_name='Guest', user_email='guest@alias.com', conversation_id=None, token_callback=None):
        """
        Main entry point for processing commands and queries.
        Retrieves memory and past conversations context, calls internal routing,
        logs the output to the database, and processes memory updates.
        """
        raw_text = text
        
        # Load user memories & search context
        memory_context = ""
        past_context = ""
        rag_context = ""
        memories = []
        if conversation_id and user_email:
            try:
                memories = history_memory.get_memories(user_email)
                if memories:
                    memory_context += "\n- Stored facts you remember about the user:\n"
                    for m in memories:
                        memory_context += f"  * {m['fact']}\n"
                
                # Proactive historical context search
                keywords = history_memory.extract_search_keywords(raw_text)
                past_excerpts = history_memory.search_past_conversations(user_email, keywords, current_conv_id=conversation_id)
                if past_excerpts:
                    past_context += "\n- Relevant context from past conversations with the user:\n"
                    for pe in past_excerpts:
                        role_str = "User" if pe['role'] == 'user' else "ALIAS"
                        past_context += f"  * [{pe['title']}] {role_str}: {pe['content']}\n"
            except Exception as e:
                print(f"[-] Error loading memory/past context: {e}")
                
        # Load document context from RAG Engine
        if hasattr(self, 'rag') and self.rag:
            try:
                rag_context = self.rag.retrieve_context(raw_text)
            except Exception as re:
                print(f"[-] Error retrieving document context: {re}")
                
        # Call the internal routing and generation logic
        response = self._process_internal(raw_text, temperature, model, user_name, memory_context, past_context, rag_context, token_callback)
        
        # Save assistant response and run memory extraction
        if conversation_id and user_email:
            try:
                history_memory.add_message(conversation_id, 'ai', response)
                
                # Extract and apply memory updates
                ops = self.llm.extract_memory_operations(raw_text, response, memories)
                for op in ops:
                    action = op.get("action")
                    if action == "add" and op.get("fact"):
                        history_memory.add_memory(user_email, op["fact"])
                        print(f"[+] Added fact to user memories: {op['fact']}")
                    elif action == "update" and op.get("id") and op.get("fact"):
                        history_memory.update_memory(user_email, op["id"], op["fact"])
                        print(f"[+] Updated memory ID {op['id']}: {op['fact']}")
                    elif action == "delete" and op.get("id"):
                        history_memory.delete_memory(user_email, op["id"])
                        print(f"[+] Deleted memory ID {op['id']}")
            except Exception as me:
                print(f"[-] Error applying memory operations: {me}")
                
        return response

    def _process_internal(self, text, temperature=0.7, model='gemini-2.5-flash', user_name='Guest', memory_context="", past_context="", rag_context="", token_callback=None):
        """
        Analyzes the text and routes to the appropriate action.
        """
        raw_text = text
        text = text.lower()
        
        # --- Image Generation Hook ---
        is_image_intent = False
        intents = [
            "generate image", "create image", "make image", "draw image", 
            "generate wallpaper", "create wallpaper", "make wallpaper",
            "generate logo", "create logo", "make logo", 
            "generate photo", "create photo", "make photo",
            "draw a picture", "draw an illustration", "paint a picture"
        ]
        
        for intent in intents:
            if intent in text:
                is_image_intent = True
                break
                
        if not is_image_intent:
            nouns = ["image", "photo", "wallpaper", "logo", "drawing", "sketch", "illustration", "painting", "artwork"]
            verbs = ["generate", "create", "make", "draw", "paint", "render"]
            for v in verbs:
                if text.startswith(v):
                    for n in nouns:
                        if n in text:
                            is_image_intent = True
                            break
                            
        if is_image_intent:
            try:
                # Parse prompt parameters
                parsed = cli_main.parse_command(text)
                prompt = parsed.get("prompt")
                width = parsed.get("width")
                height = parsed.get("height")
                model_type = parsed.get("model", "flux")
                
                if prompt:
                    # Vocal confirmation via Assistant's TTS
                    self.tts.speak(f"Sure, generating your image for {prompt}")
                    
                    # Generate and save image
                    saved_path = image_generator.generate_custom_image(
                        prompt=prompt,
                        width=width,
                        height=height,
                        model=model_type
                    )
                    
                    if saved_path and os.path.exists(saved_path):
                        filename = os.path.basename(saved_path)
                        return f"I have successfully generated the image for '{prompt}' and opened it on your screen.\n\n![Generated Image](http://127.0.0.1:8000/images/{filename})"
                    else:
                        error_detail = "Please verify your connection."
                        try:
                            history = image_generator.load_history()
                            # Check if the latest generation matches our prompt and has failed
                            if history and history[0].get("prompt") == prompt and not history[0].get("success"):
                                error_detail = history[0].get("error_message", "Please verify your connection.")
                        except Exception as he:
                            print(f"[-] Failed to read history error details: {he}")
                        return f"Sorry Shravan, I encountered an issue generating the image: {error_detail}"
            except Exception as e:
                print(f"[-] Image Gen Hook Error: {e}")
                # Fallback to standard flow if the module fails
                pass
        
        # -1. Email
        if "send email to" in text:
            # Heuristic: "send email to bob saying hello"
            try:
                parts = text.split("send email to")[-1].strip().split("saying")
                recipient_name = parts[0].strip()
                body = parts[1].strip() if len(parts) > 1 else "No content"
                
                # In a real app, we'd look up contact email from name
                # For demo, let's assume recipient is an email or we fail
                if "@" not in recipient_name:
                    return f"I need an email address for {recipient_name}."
                
                return self.email_ops.send_email(recipient_name, "Message from ALIAS", body)
            except Exception:
                return "I didn't catch the email details."

        # 0. RAG / Document Analysis
        # if "analyze document" in text or "read this file" in text:
        #     # Simple heuristic: look for file path in text or use last opened file
        #     # For this MVP, let's assume user passes full path or filename we can find
        #     target_file = text.replace("analyze document", "").replace("read this file", "").strip()
        #     # Try to find file
        #     full_path = self.file_ops.search_file(target_file)
        #     if full_path:
        #          msg = self.rag.ingest_document(full_path)
        #          return msg
        #     else:
        #          return "Please specify a valid file name to analyze."
        
        # if "from the document" in text or "according to the file" in text:
        #      return self.rag.query_document(text)

        # 1. App Control
        if text.startswith("open "):
            app_name = text.replace("open ", "").strip()
            return self.app_ctrl.open_app(app_name)
        
        # 2. Media Control
        if "play music" in text or "resume music" in text:
            return self.app_ctrl.control_media("play")
        elif "pause music" in text:
            return self.app_ctrl.control_media("pause")
        elif "next song" in text:
            return self.app_ctrl.control_media("next")
            
        # 3. File Operations
        if "search for" in text:
            filename = text.split("search for")[-1].strip()
            file_path = self.file_ops.search_file(filename)
            if file_path:
                self.file_ops.open_file(file_path)
                return f"Found and opened {filename}"
            else:
                return f"I couldn't find a file named {filename}"

        # 4. Context Awareness
        if "what am i looking at" in text or "what is open" in text:
            window_title = self.vision.get_active_window()
            return f"You are currently looking at {window_title}."

        # 5. Smart Context for LLM
        # We append the active window to the context implicitly
        try:
             current_context = f" [User is currently focusing on: {self.vision.get_active_window()}]"
        except:
             current_context = ""
             
        # 6. Fallback to LLM
        system_instruction = (
            "You are ALIAS, an AI desktop assistant. "
            "When providing code or technical explanations, use strict Markdown formatting. "
            "Always wrap code in ```language blocks. "
            "Do NOT use blockquotes for code. "
            "Do NOT use asterisks (*) for emphasis or lists. Use dashes (-) for bullet points. "
            f"CRITICAL: If the user says 'hello', 'hi', or 'hey', IGNORE all context and ONLY respond with: 'Hey {user_name}, how can I help you?'. "
            "Present complex information in structured lists or tables, avoiding long paragraphs. "
            "If asked for a diagram, use Mermaid.js syntax wrapped in ```mermaid blocks."
        )
        
        # Append memories and past context
        if memory_context:
            system_instruction += "\n" + memory_context
        if past_context:
            system_instruction += "\n" + past_context
        if rag_context:
            system_instruction += "\n- Context from analyzed documents:\n" + rag_context
            
        full_prompt = f"{system_instruction}\n\nUser: {raw_text}{current_context}"
        response = self.llm.generate_response(full_prompt, temperature=temperature, model_name=model, token_callback=token_callback)
        return response

    def execute_system_command(self, command):
        """
        Legacy method kept for reference, now handled by AppController.
        """
        return self.app_ctrl.open_app(command)
