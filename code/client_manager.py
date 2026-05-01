import os
from google import genai
from dotenv import load_dotenv

# Find .env in the parent directory
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

# Collect all available keys
KEYS = []
for i in range(1, 7):
    key = os.getenv(f"GEMINI_API_KEY_{i}")
    if key:
        KEYS.append(key)

# Add the main key if not in the list
main_key = os.getenv("GEMINI_API_KEY")
if main_key and main_key not in KEYS:
    KEYS.append(main_key)

_current_key_index = 0

def get_client():
    global _current_key_index
    if not KEYS:
        raise ValueError("No Gemini API keys found in .env")
    
    key = KEYS[_current_key_index]
    # Simple round-robin for the next call
    _current_key_index = (_current_key_index + 1) % len(KEYS)
    
    return genai.Client(api_key=key)
