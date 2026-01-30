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

from dotenv import load_dotenv
from pathlib import Path

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
        return {"filename": file.filename, "path": file_path, "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

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
            
        model_name = data.get('model', 'gemini-2.0-flash-exp')
        
        print(f"DEBUG: Processing with Temp: {temperature} (Type: {type(temperature)})")
        
        # Run blocking processor in a separate thread to keep asyncio loop healthy
        loop = asyncio.get_running_loop()
        response_text = await loop.run_in_executor(None, processor.process, user_text, temperature, model_name)
        
        # Send back to Frontend
        print(f"Sending response: {response_text[:50]}...")
        await sio.emit('response', {'data': response_text, 'type': 'ai_response'})
        
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
