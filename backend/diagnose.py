import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Setup paths
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

# 1. Check .env file
env_path = backend_dir / '.env'
print(f"Checking .env at: {env_path}")
if env_path.exists():
    print("✅ .env file found.")
    load_dotenv(dotenv_path=env_path)
else:
    print("❌ .env file NOT found!")

# 2. Check Keys
gemini_key = os.getenv("GEMINI_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
deepseek_key = os.getenv("DEEPSEEK_API_KEY")

print(f"GEMINI_API_KEY: {'Found' if gemini_key else 'Missing'}")
print(f"OPENAI_API_KEY: {'Found' if openai_key else 'Missing'}")
print(f"DEEPSEEK_API_KEY: {'Found' if deepseek_key else 'Missing'}")

# 3. Initialize Engines
try:
    print("\n--- Initializing LLM Engine ---")
    from core.llm import LLMEngine
    llm = LLMEngine()
    models = llm.get_available_models()
    print(f"✅ LLM Initialized. Available Models: {models}")
except Exception as e:
    print(f"❌ LLM Initialization Failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n--- Initializing TTS Engine ---")
    from core.tts import TTSEngine
    tts = TTSEngine()
    print("✅ TTS Initialized.")
except Exception as e:
    print(f"❌ TTS Initialization Failed: {e}")

try:
    print("\n--- Initializing App Control ---")
    from modules.app_control import AppController
    app_ctrl = AppController()
    print("✅ App Control Initialized.")
except Exception as e:
    print(f"❌ App Control Initialization Failed: {e}")

print("\nDiagnostic Complete.")
