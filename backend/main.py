from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uvicorn
import socketio
import threading
import asyncio
from core.llm import LLMEngine
from core.tts import TTSEngine
from core.stt import SpeechEngine
from core.processor import CommandProcessor
from pydantic import BaseModel
import core.auth as auth
import core.history_memory as history_memory

from dotenv import load_dotenv
from pathlib import Path

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

# Explicit setup for environment to avoid path issues
print(f"DEBUG: Startup CWD: {os.getcwd()}")
env_path = Path(__file__).parent / '.env'
print(f"DEBUG: Loading .env from: {env_path.absolute()}")
load_dotenv(dotenv_path=env_path)

# Verify API Keys immediately
print(f"DEBUG: GEMINI_API_KEY: {bool(os.getenv('GEMINI_API_KEY'))}")
print(f"DEBUG: QUBRID_API_KEY: {bool(os.getenv('QUBRID_API_KEY'))}")

# AI Components Initialization
llm = LLMEngine()
tts = TTSEngine()
stt = SpeechEngine()
processor = CommandProcessor(llm, tts)

# Socket.IO Setup
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
images_dir = Path(__file__).parent.parent / 'friday' / 'project' / 'images'
os.makedirs(images_dir, exist_ok=True)
app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")

socket_app = socketio.ASGIApp(sio, app)

@app.get("/")
def read_root():
    return {"message": "ALIAS Backend Operational"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        os.makedirs("uploads", exist_ok=True)
        file_path = f"uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Ingest file into RAG Engine
        if hasattr(processor, 'rag') and processor.rag:
            status_msg = processor.rag.ingest_document(file_path)
            return {"filename": file.filename, "path": file_path, "status": "success", "message": status_msg}
        else:
            return {"filename": file.filename, "path": file_path, "status": "success", "message": "File uploaded but RAG engine is not active."}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@app.post("/register")
async def register(request: RegisterRequest):
    result = auth.register_user(request.name, request.email, request.password)
    if result["status"] == "success":
        return result
    return {"error": result["message"], "status": "failed"}

@app.post("/login")
async def login(request: LoginRequest):
    result = auth.authenticate_user(request.email, request.password)
    if result.get("status") == "success":
        return result
    return {"error": result.get("message", "Login failed"), "status": "failed"}

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit('response', {'data': 'Connected to ALIAS Brain', 'type': 'system'})
    
    # Emit available models
    available_models = llm.get_available_models()
    await sio.emit('available_models', {'models': available_models})

@sio.event
async def get_models(sid):
    print(f"Client requested models: {sid}")
    available_models = llm.get_available_models()
    await sio.emit('available_models', {'models': available_models})

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def change_voice(sid, data):
    """Event to change the TTS voice."""
    voice = data.get('voice', 'male')
    print(f"Changing voice to: {voice}")
    tts.set_voice(voice)

@sio.event
async def get_conversations(sid, data):
    email = data.get("email")
    print(f"DEBUG: get_conversations requested by {sid} for email: {email}")
    if email:
        convs = history_memory.get_conversations(email)
        print(f"DEBUG: get_conversations returning {len(convs)} conversations")
        await sio.emit("conversations_list", {"conversations": convs}, room=sid)

@sio.event
async def get_conversation(sid, data):
    conv_id = data.get("conversation_id")
    print(f"DEBUG: get_conversation requested by {sid} for ID: {conv_id}")
    if conv_id:
        msgs = history_memory.get_messages(conv_id)
        print(f"DEBUG: get_conversation returning {len(msgs)} messages")
        await sio.emit("conversation_history", {"conversation_id": conv_id, "messages": msgs}, room=sid)

@sio.event
async def rename_conversation(sid, data):
    conv_id = data.get("conversation_id")
    title = data.get("title")
    print(f"DEBUG: rename_conversation requested by {sid} for ID: {conv_id} to: {title}")
    if conv_id and title:
        history_memory.rename_conversation(conv_id, title)
        await sio.emit("conversation_renamed", {"conversation_id": conv_id, "title": title}, room=sid)

@sio.event
async def delete_conversation(sid, data):
    conv_id = data.get("conversation_id")
    print(f"DEBUG: delete_conversation requested by {sid} for ID: {conv_id}")
    if conv_id:
        history_memory.delete_conversation(conv_id)
        await sio.emit("conversation_deleted", {"conversation_id": conv_id}, room=sid)

@sio.event
async def get_memories(sid, data):
    email = data.get("email")
    print(f"DEBUG: get_memories requested by {sid} for email: {email}")
    if email:
        mems = history_memory.get_memories(email)
        print(f"DEBUG: get_memories returning {len(mems)} memories")
        await sio.emit("memories_list", {"memories": mems}, room=sid)

@sio.event
async def delete_memory(sid, data):
    email = data.get("email")
    memory_id = data.get("memory_id")
    print(f"DEBUG: delete_memory requested by {sid} for ID: {memory_id}")
    if email and memory_id:
        history_memory.delete_memory(email, int(memory_id))
        mems = history_memory.get_memories(email)
        await sio.emit("memories_list", {"memories": mems}, room=sid)

@sio.event
async def process_text(sid, data):
    """
    Handles text input from the frontend.
    """
    try:
        user_text = data.get('text')
        # Ensure temperature is a float, fallback to 0.7 if invalid
        try:
            temperature = float(data.get('temperature', 0.7))
        except (ValueError, TypeError):
            temperature = 0.7
            
        model_name = data.get('model', 'gemini-2.5-flash')
        user_name = data.get('username', 'Guest')
        user_email = data.get('email', 'guest@alias.com')
        conversation_id = data.get('conversation_id')
        
        # If conversation_id is not provided, create a new conversation
        if user_email and not conversation_id:
            title = user_text[:30] + "..." if len(user_text) > 30 else user_text
            conversation_id = history_memory.create_conversation(user_email, title)
            # Notify frontend of the new conversation ID and title
            await sio.emit('conversation_started', {'conversation_id': conversation_id, 'title': title}, room=sid)
            
        # Save user message to database
        if conversation_id:
            history_memory.add_message(conversation_id, 'user', user_text)
            
        print(f"DEBUG: Processing with Temp: {temperature} (Type: {type(temperature)})")
        
        # Run blocking processor in a separate thread to keep asyncio loop healthy
        loop = asyncio.get_running_loop()
        response_text = await loop.run_in_executor(
            None, 
            processor.process, 
            user_text, 
            temperature, 
            model_name, 
            user_name,
            user_email,
            conversation_id
        )
        
        # Send back to Frontend
        print(f"Sending response: {response_text[:50]}...")
        await sio.emit('response', {'data': response_text, 'type': 'ai_response', 'conversation_id': conversation_id})
        
        # Speak the response
        if response_text:
             threading.Thread(target=tts.speak, args=(response_text,)).start()

    except Exception as e:
        print(f"CRITICAL ERROR in process_text: {e}")
        import traceback
        traceback.print_exc()
        await sio.emit('response', {'data': f"Error processing request: {str(e)}", 'type': 'error'})

@sio.event
async def stop_tts(sid):
    """
    Stops the TTS playback.
    """
    print(f"Client requested TTS stop: {sid}")
    tts.stop()

@sio.event
async def start_listening(sid):
    """
    Triggers the STT engine to listen.
    """
    await sio.emit('status', {'status': 'listening'})
    
    # Run STT in a separate thread/process ideally, but for now simple blocking call in thread
    def listen_and_process():
        text = stt.listen()
        if text:
            # Send recognized text to frontend
            # asyncio.run_coroutine_threadsafe(sio.emit('recognized_text', {'text': text}), loop)
            # For simplicity in this sync thread, we might need a workaround or callback.
            # But the STT is blocking. 
            pass # TODO: Implement proper async callback for STT
    
    # For now, let's keep it simple: Frontend handles microphone? 
    # Actually, USER wants "Full Desktop Control (Voice-Driven)" and "Uses speech-to-text (STT)... for real-time interaction".
    # Typically web apps do STT in the browser (Web Speech API) and send text to backend.
    # But user wants "desktop assistant".
    # If we do STT in Backend (Python), we use the system microphone.
    # Let's assume Backend STT for now as per `core/stt.py`.
    
    # Run STT in a separate thread to avoid blocking the event loop
    loop = asyncio.get_running_loop()
    text = await loop.run_in_executor(None, stt.listen)
    
    if text:
         await sio.emit('recognized_text', {'text': text})
         # Process immediately
         await process_text(sid, {'text': text})
    else:
         await sio.emit('status', {'status': 'idle'})

if __name__ == "__main__":
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
