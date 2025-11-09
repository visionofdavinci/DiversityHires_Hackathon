# src/ai_parser.py
import os
import json
import re
import time
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv('../config/.env')

GEMINI_MODELS = [
    'gemini-2.0-flash-lite',      # 30 RPM - highest limits
    'gemini-2.0-flash',           # 15 RPM - good backup
    'gemini-2.5-flash-lite',      # 15 RPM - another backup
]

# Rate limiting decorator for Gemini (60 requests per minute)
def rate_limit(calls_per_minute=50):
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            wait_time = min_interval - elapsed
            if wait_time > 0:
                time.sleep(wait_time)
            last_called[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator

def smart_mock_parser(user_message: str) -> dict:
    """
    Rule-based fallback parser
    """
    participants = []
    
    # Extract names after "with"
    if "with" in user_message.lower():
        match = re.search(r'with\s+([^.?!]+?)(?:\s+mood|$|\.)', user_message, re.IGNORECASE)
        if match:
            names_text = match.group(1)
            # Extract words that look like names/usernames
            names = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_]+\b', names_text)
            participants.extend(names)
    
    # Extract explicit Letterboxd usernames
    if "letterboxd" in user_message.lower() or "usernames" in user_message.lower() or "account" in user_message.lower():
        lb_matches = re.findall(r'(\w+)\s*[,]?\s*(\w+)(?:\s*$|\.)', user_message)
        for match in lb_matches:
            participants.extend([m for m in match if m])
    
    # Extract date
    date = None
    date_match = re.search(r'(this|on|next)\s+(\w+day|friday|saturday|sunday|tomorrow)', user_message.lower())
    if date_match:
        date = date_match.group(2)
    
    # Extract mood/genre
    mood = None
    mood_match = re.search(r'mood:\s*(\w+)', user_message.lower())
    if mood_match:
        mood = mood_match.group(1)
    else:
        # Look for common genres
        genres = ['comedy', 'action', 'drama', 'horror', 'romance', 'scifi', 'thriller', 'adventure']
        for genre in genres:
            if genre in user_message.lower():
                mood = genre
                break
    
    return {
        "participants": list(set([p for p in participants if p.lower() not in ['mood', 'comedy', 'movie']])),
        "date": date,
        "mood": mood
    }

@rate_limit(calls_per_minute=50)
def parse_with_gemini(user_message: str) -> dict:
    """
    Parse using Google Gemini API
    """
    for model_name in GEMINI_MODELS:
            try:
                import google.generativeai as genai
                
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    print("Gemini API key not found")
                    continue
                    
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name)
                
                prompt = f"""
                You are a helpful assistant that extracts structured information from movie night requests.
                
                Extract the following information from this user message and return ONLY valid JSON:
                - participants: list of usernames or names mentioned
                - date: string representing the date or day mentioned (e.g., "friday", "this weekend")
                - mood: string representing the preferred mood or genre
                
                Important: Return ONLY the JSON object, no other text.
                
                User message: "{user_message}"
                """
                
                print(f"Trying model: {model_name}")
                response = model.generate_content(prompt)
                text = response.text.strip()
                
                print(f"Gemini raw response: {text}")
                
                # Clean the response
                if text.startswith('```json'):
                    text = text[7:]
                if text.endswith('```'):
                    text = text[:-3]
                text = text.strip()
                
                # Parse JSON
                data = json.loads(text)
                
                # Validate structure
                if not isinstance(data, dict):
                    continue  # Try next model
                    
                # Ensure required fields exist
                if 'participants' not in data:
                    data['participants'] = []
                if 'date' not in data:
                    data['date'] = None
                if 'mood' not in data:
                    data['mood'] = None
                    
                print(f"Success with model: {model_name}")
                return data
                
            except Exception as e:
                error_msg = str(e).lower()
                print(f"Model {model_name} failed: {e}")
                
                # If it's a rate limit, try next model
                if any(limit_word in error_msg for limit_word in ['quota', 'limit', 'rate', 'exceeded']):
                    print(f"Rate limit hit on {model_name}, trying next model...")
                    continue  # Try next model in the list
                else:
                    # For other errors, also try next model
                    continue
    
    # All models failed
    print("All Gemini models failed")
    return None


def parse_user_request(user_message: str) -> dict:
    """
    Main parser function with fallback strategy
    """
    print(f"Parsing message: {user_message}")
    
    # Check if we should use mock mode
    if os.getenv("USE_MOCK_AI", "").lower() == "true":
        print("Using mock mode")
        return smart_mock_parser(user_message)
    
    # Try Gemini first
    print("Attempting Gemini parse...")
    gemini_result = parse_with_gemini(user_message)
    
    if gemini_result and not gemini_result.get("error"):
        print("Gemini parse successful")
        return gemini_result
    
    # Fall back to smart mock parser
    print("Gemini failed, using smart mock parser")
    return smart_mock_parser(user_message)