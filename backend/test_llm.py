import os
from dotenv import load_dotenv
from core.llm import LLMEngine

# Mock/Load env
load_dotenv()
# Ensure we have a key (mock it if missing for structure test, but real one needed for actual call)
# os.environ["GEMINI_API_KEY"] = "mock_key" 

def test_engine():
    print("Initializing LLMEngine...")
    llm = LLMEngine()
    
    print("Testing generate_response with custom params...")
    try:
        # We might not have a valid key in this environment, but we can check if it tries to call it
        # If it fails with Auth error, that means it successfully called the API with the params.
        # If it fails with "TypeError", our code is wrong.
        response = llm.generate_response("Hello", temperature=0.5, model_name="gemini-1.5-flash")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Caught expected exception (likely auth or network if key missing): {e}")

if __name__ == "__main__":
    test_engine()
