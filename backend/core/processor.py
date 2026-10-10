from core.llm import LLMEngine
from core.tts import TTSEngine
import core.history_memory as history_memory
from modules.app_control import AppController
from modules.document_ops import DocumentOps
from modules.file_ops import FileOps
from modules.window_awareness import WindowAwareness
from modules.email_ops import EmailOps
from core.rag import RAGEngine
from core.image_service import ImageGenerationService
from core.image_models import ImageGenRequest
import os
import re
import platform

class CommandProcessor:
    def __init__(self, llm: LLMEngine, tts: TTSEngine):
        self.llm = llm
        self.tts = tts
        self.app_ctrl = AppController()
        self.document_ops = DocumentOps()
        self.file_ops = FileOps()
        self.vision = WindowAwareness()
        self.email_ops = EmailOps()
        self.rag = RAGEngine()
        self.image_service = ImageGenerationService(llm=llm)
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
        text_lower = text.lower()
        
        # --- 1. Image Generation Hook (via ImageGenerationService) ---
        if self.image_service.detect_image_intent(raw_text):
            try:
                request = ImageGenRequest.from_text(raw_text)
                result = self.image_service.generate(request)
                
                if result.success and result.image_url:
                    response_parts = [
                        f"Here's your generated image for **\"{request.prompt}\"**:\n",
                        f"![Generated Image]({result.image_url})\n",
                        f"**Model:** {result.model} · **Size:** {result.width}×{result.height} · **Provider:** {result.provider}",
                    ]
                    if result.enhanced_prompt and result.enhanced_prompt != request.prompt:
                        response_parts.append(f"\n\n*Enhanced prompt: \"{result.enhanced_prompt[:120]}...\"*")
                    response_parts.append(f"\n*Generated in {result.generation_time:.1f}s*")
                    return "\n".join(response_parts)
                else:
                    return f"Sorry, I encountered an issue generating the image: {result.error_message or 'Please verify your connection.'}"
                    
            except Exception as e:
                print(f"[-] Image Gen Hook Error: {e}")
                import traceback
                traceback.print_exc()
                return f"Sorry, image generation failed unexpectedly: {str(e)}"

        # --- 2. Document Creation Hook (PDF & Word DOCX via DocumentOps) ---
        doc_intent = self.document_ops.detect_document_intent(raw_text)
        if doc_intent:
            try:
                result = self.document_ops.generate_document_from_prompt(
                    raw_text=raw_text,
                    llm_engine=self.llm,
                    model_name=model,
                    user_name=user_name
                )
                
                if result.get("success"):
                    resp_lines = [
                        f"📄 **{result['type']} Document Generated Successfully!**\n",
                        f"- **Title:** {result['title']}",
                        f"- **File:** `{result['filename']}`",
                        f"- **Saved To:** `{result['file_path']}`",
                        f"- **Size:** {result.get('file_size_kb', 0):.1f} KB",
                        f"- **Sections:** {result.get('sections_count', 0)} structured sections",
                        f"\n*The document has been created on your Desktop and opened automatically.*"
                    ]
                    if result.get("preview"):
                        resp_lines.append(f"\n**Document Overview:**\n{result['preview']}")
                    return "\n".join(resp_lines)
                else:
                    return f"Sorry, I encountered an issue creating your document: {result.get('error', 'Unknown error')}"
            except Exception as de:
                print(f"[-] Document Creation Hook Error: {de}")
                import traceback
                traceback.print_exc()
                return f"Sorry, document creation failed: {str(de)}"

        # --- 3. App Control & Web Navigation / YouTube / Google Search Hook ---
        open_intent = self.app_ctrl.detect_open_intent(raw_text)
        if open_intent:
            action_msg = self.app_ctrl.execute_open(open_intent)
            return action_msg

        # --- 4. Email Operations ---
        if "send email to" in text_lower:
            try:
                parts = text_lower.split("send email to")[-1].strip().split("saying")
                recipient_name = parts[0].strip()
                body = parts[1].strip() if len(parts) > 1 else "No content"
                
                if "@" not in recipient_name:
                    return f"I need an email address for {recipient_name}."
                
                return self.email_ops.send_email(recipient_name, "Message from ALIAS", body)
            except Exception:
                return "I didn't catch the email details."

        # --- 5. Media Control ---
        if "play music" in text_lower or "resume music" in text_lower:
            return self.app_ctrl.control_media("play")
        elif "pause music" in text_lower:
            return self.app_ctrl.control_media("pause")
        elif "next song" in text_lower:
            return self.app_ctrl.control_media("next")

        # --- 6. File Operations (Search & Open) ---
        if "search for file" in text_lower or (text_lower.startswith("search for ") and not any(k in text_lower for k in ["youtube", "google", "web"])):
            filename = text_lower.split("search for")[-1].replace("file", "").strip()
            if filename:
                file_path = self.file_ops.search_file(filename)
                if file_path:
                    self.file_ops.open_file(file_path)
                    return f"Found and opened {filename}"
                else:
                    return f"I couldn't find a file named {filename}"

        # --- 7. Context Awareness ---
        if "what am i looking at" in text_lower or "what is open" in text_lower:
            window_title = self.vision.get_active_window()
            return f"You are currently looking at {window_title}."

        try:
            current_context = f" [User is currently focusing on: {self.vision.get_active_window()}]"
        except Exception:
            current_context = ""
             
        # --- 8. Fallback to LLM with Autonomous Action Capabilities ---
        system_instruction = (
            "You are ALIAS, an advanced AI desktop assistant. "
            "When providing code or technical explanations, use strict Markdown formatting. "
            "Always wrap code in ```language blocks. "
            "Do NOT use blockquotes for code. "
            "Do NOT use asterisks (*) for emphasis or lists. Use dashes (-) for bullet points. "
            f"CRITICAL: If the user says 'hello', 'hi', or 'hey', IGNORE all context and ONLY respond with: 'Hey {user_name}, how can I help you?'. "
            "Present complex information in structured lists or tables, avoiding long paragraphs. "
            "If asked for a diagram, use Mermaid.js syntax wrapped in ```mermaid blocks. "
            "If the user asks you to open an application, visit a website, or search the web and it was not processed automatically, "
            "you can append an action tag at the end of your response: `[ACTION: OPEN <app_name_or_url>]`."
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

        # Check if the LLM emitted an action tag
        action_match = re.search(r'\[ACTION:\s*OPEN\s+([^\]]+)\]', response, re.IGNORECASE)
        if action_match:
            action_target = action_match.group(1).strip()
            self.app_ctrl.open_app(action_target)
            response = re.sub(r'\[ACTION:\s*OPEN\s+[^\]]+\]', '', response).strip()

        return response

    def execute_system_command(self, command):
        """
        Legacy method kept for reference, now handled by AppController.
        """
        return self.app_ctrl.open_app(command)
