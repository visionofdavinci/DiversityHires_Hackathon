# src/gemini_nlg.py
import os
import google.generativeai as genai
from dotenv import load_dotenv
from functools import wraps
import time

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '../config/.env')
load_dotenv(dotenv_path)

# Rate limiting (same as parser)
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


@rate_limit(calls_per_minute=50)
def generate_natural_response(parsed_data: dict, recommendations: list = None) -> str:
    """
    Use Gemini to generate a natural, friendly response based on parsed request
    and movie recommendations.
    
    Args:
        parsed_data: Dict with participants, date, mood
        recommendations: Optional list of movie recommendation objects
    
    Returns:
        Natural language response string
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return fallback_response(parsed_data, recommendations)
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        
        # Build context for Gemini
        context = f"""You are a friendly movie night assistant helping friends plan their outing.

User requested:
- Participants: {', '.join(parsed_data.get('participants', [])) or 'not specified'}
- Date: {parsed_data.get('date') or 'not specified'}
- Mood: {parsed_data.get('mood') or 'not specified'}
"""
        
        if recommendations and len(recommendations) > 0:
            top_movies = recommendations[:3]
            context += f"\n\nTop recommendations found:\n"
            for i, movie in enumerate(top_movies, 1):
                title = movie.get('title', 'Unknown')
                score = movie.get('group_score', 0)
                showtimes_count = len(movie.get('showtimes', []))
                context += f"{i}. {title} (score: {score:.1f}, {showtimes_count} showtimes)\n"
        else:
            context += "\n\nNo recommendations found yet."
        
        prompt = f"""{context}

Generate a brief, enthusiastic response (2-3 sentences max) that:
1. Acknowledges their request
2. Mentions the top movie recommendation if available
3. Sounds natural and friendly

Do NOT use phrases like "Okay! I've set up..." - be more conversational.
Response:"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"Gemini NLG error: {e}")
        return fallback_response(parsed_data, recommendations)


def fallback_response(parsed_data: dict, recommendations: list = None) -> str:
    """Simple template-based fallback if Gemini fails"""
    participants = parsed_data.get("participants", [])
    date = parsed_data.get("date")
    mood = parsed_data.get("mood")
    
    if recommendations and len(recommendations) > 0:
        top_movie = recommendations[0].get('title', 'a great movie')
        if participants and date:
            return f"Perfect! How about watching {top_movie} {date} with {', '.join(participants)}? 🎬"
        elif participants:
            return f"Great! I found {top_movie} for you and {', '.join(participants)} to watch together! 🍿"
        else:
            return f"I found some great options! Top pick: {top_movie} 🎥"
    else:
        parts = []
        if participants:
            parts.append(f"with {', '.join(participants)}")
        if date:
            parts.append(f"on {date}")
        if mood:
            parts.append(f"in the mood for {mood}")
        
        if parts:
            return f"Got it! Looking for movies {' '.join(parts)} 🔍"
        else:
            return "What kind of movie are you looking for? Tell me more! 🎬"