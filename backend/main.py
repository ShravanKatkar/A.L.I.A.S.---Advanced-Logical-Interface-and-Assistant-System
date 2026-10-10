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
from core.image_service import ImageGenerationService
from core.image_models import ImageGenRequest, ImageGenAPIRequest
from pydantic import BaseModel
import core.auth as auth
import core.history_memory as history_memory

from dotenv import load_dotenv
from pathlib import Path

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

from typing import Optional

class LoginRequest(BaseModel):
    email: str
    password: str

class GoogleLoginRequest(BaseModel):
    credential: str

class FirebaseLoginRequest(BaseModel):
    id_token: Optional[str] = None
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    uid: Optional[str] = None
    provider: Optional[str] = None

class UpdateKeysRequest(BaseModel):
    gemini_key: Optional[str] = None
    groq_key: Optional[str] = None
    deepseek_key: Optional[str] = None
    openai_key: Optional[str] = None

class TestKeyRequest(BaseModel):
    provider: str
    key: str

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
image_service = ImageGenerationService(llm=llm)

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
from fastapi.responses import FileResponse, JSONResponse
images_dir = Path(__file__).parent.parent / 'friday' / 'project' / 'images'
os.makedirs(images_dir, exist_ok=True)

@app.get("/images/{filename}")
async def serve_image(filename: str):
    file_path = images_dir / filename
    if not file_path.is_file():
        return JSONResponse({"error": "Image not found", "filename": filename}, status_code=404)
    media_type = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
    return FileResponse(
        str(file_path),
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=86400", "Access-Control-Allow-Origin": "*"}
    )

app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")

docs_dir = Path(__file__).parent / 'uploads' / 'documents'
os.makedirs(docs_dir, exist_ok=True)

@app.get("/documents/{filename}")
async def serve_document(filename: str):
    file_path = docs_dir / filename
    if not file_path.is_file():
        return JSONResponse({"error": "Document not found", "filename": filename}, status_code=404)
    media_type = "application/pdf" if filename.lower().endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return FileResponse(
        str(file_path),
        media_type=media_type,
        filename=filename,
        headers={"Access-Control-Allow-Origin": "*"}
    )

app.mount("/documents", StaticFiles(directory=str(docs_dir)), name="documents")

@app.get("/api/settings/keys")
async def get_keys_status():
    """Returns the configuration status and masked values for all supported API keys."""
    return llm.get_provider_status()

@app.post("/api/settings/keys/test")
async def test_key(request: TestKeyRequest):
    """Tests an API key for a specified provider."""
    result = llm.test_api_key(request.provider, request.key)
    return result

@app.post("/api/settings/keys")
async def update_keys(request: UpdateKeysRequest):
    """Updates API keys in .env and reloads the LLM engine."""
    env_file = Path(__file__).parent / '.env'
    lines = []
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
    key_updates = {}
    if request.gemini_key is not None:
        key_updates["GEMINI_API_KEY"] = request.gemini_key.strip()
    if request.groq_key is not None:
        key_updates["GROQ_API_KEY"] = request.groq_key.strip()
    if request.deepseek_key is not None:
        key_updates["DEEPSEEK_API_KEY"] = request.deepseek_key.strip()
    if request.openai_key is not None:
        key_updates["OPENAI_API_KEY"] = request.openai_key.strip()

    updated_keys = set()
    new_lines = []
    for line in lines:
        matched = False
        for k, v in key_updates.items():
            if line.strip().startswith(f"{k}=") or line.strip().startswith(f"# {k}="):
                new_lines.append(f"{k}={v}\n")
                updated_keys.add(k)
                matched = True
                break
        if not matched:
            new_lines.append(line)

    for k, v in key_updates.items():
        if k not in updated_keys:
            new_lines.append(f"{k}={v}\n")

    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    # Reload engine
    llm.reload_keys()
    
    # Broadcast updated models to frontend
    new_models = llm.get_available_models()
    await sio.emit('available_models', {'models': new_models})
    
    return {
        "status": "success",
        "message": "API keys updated successfully.",
        "provider_status": llm.get_provider_status(),
        "available_models": new_models
    }

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
    return JSONResponse(
        status_code=400,
        content={"error": result.get("message", "Login failed"), "status": "failed"}
    )

@app.get("/api/auth/config")
async def get_auth_config():
    """Returns authentication configuration, including Firebase and Google settings if available."""
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    return {
        "google_client_id": google_client_id,
        "google_enabled": bool(google_client_id),
        "firebase": {
            "apiKey": os.getenv("FIREBASE_API_KEY", "").strip(),
            "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", "").strip(),
            "projectId": os.getenv("FIREBASE_PROJECT_ID", "").strip(),
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", "").strip(),
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", "").strip(),
            "appId": os.getenv("FIREBASE_APP_ID", "").strip(),
            "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID", "").strip()
        }
    }

@app.post("/auth/google")
@app.post("/google-login")
async def google_login(request: GoogleLoginRequest):
    """Authenticates or registers a user via Google ID Token."""
    result = auth.authenticate_google_user(request.credential)
    if result.get("status") == "success":
        return result
    return JSONResponse(
        status_code=400,
        content={"error": result.get("message", "Google authentication failed"), "status": "failed"}
    )

@app.post("/auth/firebase")
async def firebase_login(request: FirebaseLoginRequest):
    """Authenticates or registers a user via Firebase Authentication."""
    result = auth.authenticate_firebase_user(
        email=request.email,
        name=request.name,
        picture=request.picture or "",
        uid=request.uid or "",
        provider=request.provider or "firebase",
        id_token=request.id_token
    )
    if result.get("status") == "success":
        return result
    return JSONResponse(
        status_code=400,
        content={"error": result.get("message", "Firebase authentication failed"), "status": "failed"}
    )

# =============================================================================
# IMAGE GENERATION API ENDPOINTS
# =============================================================================

@app.get("/api/images/config")
async def get_image_config():
    """Returns available models, styles, aspect ratios, and quality presets."""
    return image_service.get_config()

@app.post("/api/images/generate")
async def generate_image(request: ImageGenAPIRequest):
    """
    Generate an image via the full pipeline.
    Runs in a thread pool to avoid blocking the event loop.
    """
    try:
        loop = asyncio.get_running_loop()
        
        gen_request = ImageGenRequest(
            prompt=request.prompt,
            model=request.model,
            quality=request.quality,
            aspect_ratio=request.aspect_ratio,
            style=request.style,
            width=request.width or 1024,
            height=request.height or 1024,
            seed=request.seed,
            negative_prompt=request.negative_prompt,
            enhance_prompt=request.enhance_prompt,
            user_email=request.user_email,
            conversation_id=request.conversation_id,
        )
        
        result = await loop.run_in_executor(None, image_service.generate, gen_request)
        
        return {
            "status": "success" if result.success else "failed",
            "id": result.id,
            "image_url": result.image_url,
            "original_prompt": result.original_prompt,
            "enhanced_prompt": result.enhanced_prompt,
            "model": result.model,
            "provider": result.provider,
            "width": result.width,
            "height": result.height,
            "seed": result.seed,
            "generation_time": round(result.generation_time, 2),
            "error_message": result.error_message,
        }
    except Exception as e:
        return {"status": "failed", "error_message": str(e)}

@app.get("/api/images/history")
async def get_image_history(limit: int = 20):
    """Returns recent image generation history."""
    return {"history": image_service.get_history(limit=limit)}

@app.get("/api/images/{gen_id}")
async def get_image_by_id(gen_id: str):
    """Get a specific generation by ID."""
    item = image_service.get_generation_by_id(gen_id)
    if item:
        return item
    return {"error": "Generation not found", "status": "failed"}

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
        
        # Emit stream start and avatar thinking state
        await sio.emit('avatar_state', {'state': 'thinking'}, room=sid)
        await sio.emit('chat_start', {'conversation_id': conversation_id}, room=sid)

        # Setup thread-safe queue structure
        queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        
        def token_callback(token):
            # Thread-safe write to asyncio queue
            loop.call_soon_threadsafe(queue.put_nowait, token)

        # Run blocking processor in a separate thread to keep asyncio loop healthy
        task = loop.run_in_executor(
            None, 
            processor.process, 
            user_text, 
            temperature, 
            model_name, 
            user_name,
            user_email,
            conversation_id,
            token_callback
        )
        
        # Stream tokens as they arrive
        full_response = ""
        first_chunk_sent = False
        while not task.done() or not queue.empty():
            try:
                token = await asyncio.wait_for(queue.get(), timeout=0.1)
                full_response += token
                if not first_chunk_sent:
                    first_chunk_sent = True
                    await sio.emit('avatar_state', {'state': 'working'}, room=sid)
                await sio.emit('chat_chunk', {'chunk': token, 'conversation_id': conversation_id}, room=sid)
                queue.task_done()
            except asyncio.TimeoutError:
                continue

        # Get the final returned text
        response_text = await task
        
        # Fallback if no chunks were generated (e.g. static/bypassed command routing)
        if not full_response and response_text:
            full_response = response_text
            await sio.emit('avatar_state', {'state': 'working'}, room=sid)
            await sio.emit('chat_chunk', {'chunk': response_text, 'conversation_id': conversation_id}, room=sid)

        # Emit stream end event
        await sio.emit('chat_end', {'conversation_id': conversation_id}, room=sid)
        
        # Determine avatar state based on response content
        resp_lower = full_response.lower()
        if any(term in resp_lower for term in ["created document", "document created", "generated image", "image generated", "saved to desktop", "successfully created", "launched", "opened"]):
            await sio.emit('avatar_state', {'state': 'celebrate'}, room=sid)
        elif any(term in resp_lower for term in ["error", "failed", "could not find", "balance", "quota"]):
            await sio.emit('avatar_state', {'state': 'confused'}, room=sid)
        else:
            await sio.emit('avatar_state', {'state': 'happy'}, room=sid)

        # Send full response (mostly backward compatibility/reference)
        print(f"Sending full response: {full_response[:50]}...")
        await sio.emit('response', {'data': full_response, 'type': 'ai_response', 'conversation_id': conversation_id})
        
        # Speak the response with synchronized avatar states
        if full_response:
            def tts_runner():
                def on_start():
                    asyncio.run_coroutine_threadsafe(
                        sio.emit('avatar_state', {'state': 'happy'}, room=sid),
                        loop
                    )
                def on_end():
                    asyncio.run_coroutine_threadsafe(
                        sio.emit('avatar_state', {'state': 'idle'}, room=sid),
                        loop
                    )
                tts.speak(full_response, on_start=on_start, on_end=on_end)

            threading.Thread(target=tts_runner, daemon=True).start()

    except Exception as e:
        print(f"CRITICAL ERROR in process_text: {e}")
        import traceback
        traceback.print_exc()
        await sio.emit('avatar_state', {'state': 'confused'}, room=sid)
        await sio.emit('response', {'data': f"Error processing request: {str(e)}", 'type': 'error'})

@sio.event
async def stop_tts(sid):
    """
    Stops the TTS playback.
    """
    print(f"Client requested TTS stop: {sid}")
    tts.stop()
    await sio.emit('avatar_state', {'state': 'idle'}, room=sid)

@sio.event
async def start_listening(sid):
    """
    Triggers the STT engine to listen.
    """
    await sio.emit('status', {'status': 'listening'})
    await sio.emit('avatar_state', {'state': 'listening'}, room=sid)
    
    # Run STT in a separate thread to avoid blocking the event loop
    loop = asyncio.get_running_loop()
    text = await loop.run_in_executor(None, stt.listen)
    
    if text:
         await sio.emit('recognized_text', {'text': text})
         # Process immediately
         await process_text(sid, {'text': text})
    else:
         await sio.emit('status', {'status': 'idle'})
         await sio.emit('avatar_state', {'state': 'idle'}, room=sid)

if __name__ == "__main__":
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
