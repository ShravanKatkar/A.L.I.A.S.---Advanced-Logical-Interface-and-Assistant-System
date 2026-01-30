from core.llm import LLMEngine
from core.tts import TTSEngine
from modules.app_control import AppController
from modules.file_ops import FileOps
from modules.window_awareness import WindowAwareness
from modules.email_ops import EmailOps
# from core.rag import RAGEngine
import os
import platform

class CommandProcessor:
    def __init__(self, llm: LLMEngine, tts: TTSEngine):
        self.llm = llm
        self.tts = tts
        self.app_ctrl = AppController()
        self.file_ops = FileOps()
        self.vision = WindowAwareness()
        self.email_ops = EmailOps()
        # self.rag = RAGEngine()
        self.system_os = platform.system()

    def process(self, text, temperature=0.7, model='gemini-2.0-flash-exp'):
        """
        Analyzes the text and routes to the appropriate action.
        """
        text = text.lower()
        
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
            "CRITICAL: If the user says 'hello', 'hi', or 'hey', IGNORE all context and ONLY respond with: 'Hey Shravan, how can I help you?'. "
            "Present complex information in structured lists or tables, avoiding long paragraphs. "
            "Present complex information in structured lists or tables, avoiding long paragraphs. "
            "If asked for a diagram, use Mermaid.js syntax wrapped in ```mermaid blocks."
        )
        
        full_prompt = f"{system_instruction}\n\nUser: {text}{current_context}"
        response = self.llm.generate_response(full_prompt, temperature=temperature, model_name=model)
        return response

    def execute_system_command(self, command):
        """
        Legacy method kept for reference, now handled by AppController.
        """
        return self.app_ctrl.open_app(command)
