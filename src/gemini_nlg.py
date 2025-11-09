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
        participants = parsed_data.get('participants', [])
        date = parsed_data.get('date', 'soon')
        mood = parsed_data.get('mood', 'any genre')
        
        context = f"""You are a friendly movie night assistant helping friends plan their outing.

User requested:
- Participants: {', '.join(participants) if participants else 'not specified'}
- Date: {date}
- Mood: {mood}
"""
        
        if recommendations and len(recommendations) > 0:
            # Get top 3 movies
            top_movies = recommendations[:3]
            context += f"\n\nTop {len(top_movies)} recommendations based on everyone's availability:\n\n"
            
            for i, movie in enumerate(top_movies, 1):
                title = movie.get('title', 'Unknown')
                score = movie.get('group_score', 0)
                showtimes = movie.get('showtimes', [])
                
                # Get unique cinemas for this movie
                cinemas = {}
                for showtime in showtimes:
                    cinema = showtime.cinema  # ← FIXED
                    time = showtime.start.isoformat() if showtime.start else 'Unknown'  # ← FIXED
                    if cinema not in cinemas:
                        cinemas[cinema] = []
                    cinemas[cinema].append(time)
                
                context += f"{i}. {title}\n"
                context += f"   - Group Score: {score:.1f}\n"
                context += f"   - Available at {len(cinemas)} cinema(s) with {len(showtimes)} total showtimes\n"
                
                # Show first 2 cinemas as examples
                shown_cinemas = list(cinemas.items())[:2]
                for cinema, times in shown_cinemas:
                    context += f"   - {cinema}: {len(times)} showing(s)\n"
                
                if len(cinemas) > 2:
                    context += f"   - ...and {len(cinemas) - 2} more cinema(s)\n"
                context += "\n"
        else:
            context += "\n\nNo recommendations found yet."
        
        prompt = f"""{context}

Generate a brief, enthusiastic response (3-4 sentences) that:
1. Acknowledges their request for {date} with {', '.join(participants) if participants else 'the group'}
2. Mentions ALL 3 movie recommendations by name
3. Highlights that these showtimes work for everyone's calendars
4. Sounds natural and friendly

Do NOT list all showtimes - just mention the movies and that there are multiple options.
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
        # Get top 3 movies
        top_3 = recommendations[:3]
        movie_titles = [m.get('title', 'a movie') for m in top_3]
        
        if len(movie_titles) == 1:
            movies_text = movie_titles[0]
        elif len(movie_titles) == 2:
            movies_text = f"{movie_titles[0]} or {movie_titles[1]}"
        else:
            movies_text = f"{movie_titles[0]}, {movie_titles[1]}, or {movie_titles[2]}"
        
        # Count total showtimes
        total_showtimes = sum(len(m.get('showtimes', [])) for m in top_3)
        
        if participants and date:
            return f"Perfect! I found 3 great options for {date}: {movies_text}. All {total_showtimes} showtimes work with everyone's calendars! 🎬"
        elif participants:
            return f"Great! Top picks for {', '.join(participants)}: {movies_text} ({total_showtimes} available showtimes) 🍿"
        else:
            return f"Here are your top 3: {movies_text}. {total_showtimes} showtimes available! 🎥"
    else:
        parts = []
        if participants:
            parts.append(f"with {', '.join(participants)}")
        if date:
            parts.append(f"on {date}")
        if mood:
            parts.append(f"in the mood for {mood}")
        
        if parts:
            return f"Got it! Looking for movies {' '.join(parts)}... 🔍"
        else:
            return "What kind of movie are you looking for? Tell me the participants, date, and mood! 🎬"