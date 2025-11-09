# src/ai_parser.py
import os
from openai import OpenAI
import json
from dotenv import load_dotenv

# Load environment variables from config/.env
# Try different possible locations for the config/.env file
config_paths = [
    '../config/.env',      # if config/.env is in parent directory
    './config/.env',       # if config/.env is in same directory as src
    '../../config/.env',   # if config/.env is two levels up
    'config/.env',         # if config is in current directory
    '../config/.env'       # if running from src folder
]

loaded = False
for path in config_paths:
    if os.path.exists(path):
        load_dotenv(path)
        print(f"Loaded environment from: {path}")
        loaded = True
        break

if not loaded:
    print("Warning: config/.env not found in common locations")
    # Print current directory for debugging
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in current directory: {os.listdir('.')}")
    if os.path.exists('..'):
        print(f"Files in parent directory: {os.listdir('..')}")

def parse_user_request(user_message: str) -> dict:
    """
    Takes a user's natural language message and extracts structured info
    """
    
    # Debug: Check what environment variables are available
    print(f"USE_MOCK_AI: {os.getenv('USE_MOCK_AI')}")
    print(f"OPENAI_API_KEY set: {os.getenv('OPENAI_API_KEY') is not None}")
    
    # Check if we should use mock data
    use_mock = os.getenv("USE_MOCK_AI", "").lower()
    if use_mock == "true":
        print("Using mock data")
        # Return mock data for testing
        return {
            "participants": ["alice123", "bob456"],
            "date": "friday", 
            "mood": "comedy"
        }
    
    # Real OpenAI implementation
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY environment variable not set"}
    
    client = OpenAI(api_key=api_key)

    prompt = f"""
    You are a helpful assistant that extracts structured information
    from a user's natural language request for a movie night.
    Return ONLY valid JSON with keys:
      - participants: list of usernames
      - date: string (optional)
      - mood: string (optional)
    User message: "{user_message}"
    """

    try:
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        text = response.choices[0].message.content.strip()
        data = json.loads(text)
        return data
        
    except Exception as e:
        return {"error": f"API call failed: {str(e)}"}