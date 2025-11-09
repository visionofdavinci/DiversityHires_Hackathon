from flask import Flask, request, jsonify, redirect, session
from flask_cors import CORS
import os
from src.orchestrator import get_group_recommendations
from src.gemini_parser import parse_user_request, smart_mock_parser
from src.calendar_agent import (
    get_authorization_url, 
    exchange_code_for_tokens, 
    save_credentials,
    get_calendar_service,
    get_calendar_service_simple,
    get_all_busy_events
)
from src.letterboxd_integration import LetterboxdIntegration
from src.cineville_scraper import CinevilleScraper
from src.movie_matcher import TMDbClient
from src.group_history import GENRE_MAP
from datetime import datetime, timedelta 
from src.gemini_nlg import generate_natural_response
from src.poll_manager import PollManager

# Initialize poll manager
poll_manager = PollManager()

app = Flask(__name__)
# Use a consistent secret key (in production, use environment variable)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production-12345678')

# Get allowed origins from environment variable or use defaults
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
# Add both production and development origins
allowed_origins = [
    FRONTEND_URL, 
    "http://localhost:3000", 
    "http://localhost:5000",
    "https://diversity-hires-hackathon-3x1r.vercel.app",
    "https://diversity-hires-hackathon-3x1r-banem8agz-visionofdavincis-projects.vercel.app"
]

# Configure CORS to allow credentials (cookies/sessions)
CORS(app, 
     supports_credentials=True,
     resources={r"/*": {
         "origins": allowed_origins,
         "allow_headers": ["Content-Type"],
         "expose_headers": ["Content-Type"],
         "methods": ["GET", "POST", "OPTIONS"]
     }})

# Configure session cookie settings
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'  # True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Temporary in-memory storage for OAuth state (better than session for OAuth callback)
# In production, use Redis or a database
oauth_states = {}

# Initialize TMDb client for fetching movie metadata
tmdb_client = TMDbClient()

# Optional mapping from Google Calendar username → Letterboxd username
USER_MAPPING = {
    "sanne": "SanneBr",
    "noor": "noorsterre",
    "ioana": "visionofdavinci"
}

# Add the helper function here, before your route definitions
def parse_date_to_days_ahead(date_str: str) -> int:
    """
    Convert parsed date string to days_ahead integer.
    
    Examples:
      - "friday" -> days until next Friday
      - "tomorrow" -> 1
      - "this weekend" -> days until Saturday
      - "next week" -> 7
    """
    if not date_str:
        return 7  # default
    
    date_lower = date_str.lower()
    today = datetime.now()
    
    # Handle "tomorrow"
    if "tomorrow" in date_lower:
        return 1
    
    # Handle "today"
    if "today" in date_lower:
        return 0
    
    # Handle "next week"
    if "next week" in date_lower:
        return 7
    
    # Handle "this weekend"
    if "weekend" in date_lower:
        # Return days until Saturday
        days_until_saturday = (5 - today.weekday()) % 7
        return days_until_saturday if days_until_saturday > 0 else 2
    
    # Handle specific days of week
    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }
    
    for day_name, day_num in weekdays.items():
        if day_name in date_lower:
            current_day = today.weekday()
            days_ahead = (day_num - current_day) % 7
            return days_ahead if days_ahead > 0 else 7
    
    # Default fallback
    return 7

def generate_summary(data: dict) -> str:
    """
    Simple NLG function to return a short natural-language summary
    of the parsed user request.
    """
    if "error" in data:
        return f"Sorry, I couldn't understand your message: {data['error']}."
    
    participants = data.get("participants", [])
    date = data.get("date")
    mood = data.get("mood")

    parts = []
    if participants:
        parts.append(f"with {', '.join(participants)}")
    if date:
        parts.append(f"on {date}")
    if mood:
        parts.append(f"mood: {mood}")

    if parts:
        return "Okay! I’ve set up a movie night " + " ".join(parts) + "."
    else:
        return "I couldn’t find specific details in your message — could you rephrase?"

# Add this helper function after the generate_summary function (around line 135)

def parse_vote_with_gemini(user_message: str, poll_options: list) -> int:
    """
    Use Gemini to parse a vote from natural language.
    Returns the option index (0-based) or -1 if cannot parse.
    """
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        
        # Format options for the prompt
        options_text = "\n".join([f"{i+1}. {opt['movie']}" for i, opt in enumerate(poll_options)])
        
        prompt = f"""The user is voting in a poll with these options:
{options_text}

The user said: "{user_message}"

Which option are they voting for? Return ONLY the number (1, 2, or 3). 
If they mentioned a movie name, return the corresponding number.
If you cannot determine which option, return "0".

Examples:
- "I vote for option 2" → 2
- "number 1" → 1
- "I want to see Pavements" → (the number where Pavements is)
- "let's go with the second one" → 2
- "Pavements" → (the number where Pavements is)

Return only the number, nothing else."""
        
        response = model.generate_content(prompt)
        vote_num = response.text.strip()
        
        try:
            option_index = int(vote_num) - 1  # Convert to 0-based index
            if 0 <= option_index < len(poll_options):
                return option_index
            else:
                return -1
        except ValueError:
            return -1
            
    except Exception as e:
        print(f"Error parsing vote with Gemini: {e}")
        return -1

# Initialize services
scraper = CinevilleScraper()

@app.route("/")
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "Movie Matcher API is running",
        "version": "1.0.0",
        "endpoints": {
            "recommendations": "/recommendations",
            "chat": "/chat",
            "calendar_auth": "/calendar/auth",
            "letterboxd": "/api/letterboxd",
            "cineville": "/cineville/upcoming"
        }
    }), 200

@app.route("/recommendations", methods=["POST"])
def recommendations():
    data = request.get_json() or {}

    usernames = data.get("usernames", [])
    days_ahead = data.get("days_ahead", 7)
    limit_amsterdam = data.get("limit_amsterdam", True)
    max_results = data.get("max_results", 10)
    use_calendar = data.get("use_calendar", True)
    min_slot_minutes = int(data.get("min_hours", 2)) * 60  # convert hours → minutes
    mood = data.get("mood")
    learn_from_history = data.get("learn_from_history", True)

    if not usernames:
        return jsonify({"error": "No usernames provided"}), 400

    result = get_group_recommendations(
        usernames=usernames,
        days_ahead=days_ahead,
        limit_amsterdam=limit_amsterdam,
        max_results=max_results,
        use_calendar=use_calendar,
        min_slot_minutes=min_slot_minutes,
        mood=mood,
        learn_from_history=learn_from_history,
    )

    return jsonify(result)

@app.route("/calendar/auth/start", methods=["POST"])
def calendar_auth_start():
    """
    Step 1: Generate OAuth URL for user to visit and authenticate.
    Expects JSON: {"username": "user_identifier"}
    """
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        # Determine the correct redirect URI based on environment
        backend_url = os.getenv('BACKEND_URL', 'http://localhost:5000')
        redirect_uri = f'{backend_url}/calendar/oauth2callback'
        
        # Generate OAuth URL with dynamic redirect URI
        auth_url, state = get_authorization_url(redirect_uri=redirect_uri)
        
        # Store username in in-memory dict (more reliable than session for OAuth)
        oauth_states[state] = username
        print(f"[OAuth] Stored state {state} for username {username}")
        print(f"[OAuth] Using redirect URI: {redirect_uri}")
        
        # Also try session as backup
        session[f'oauth_state_{state}'] = username
        
        return jsonify({
            'auth_url': auth_url,
            'state': state,
            'message': 'Please visit the auth_url to grant calendar access'
        })
    except Exception as e:
        print(f"[OAuth] Error in auth_start: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route("/calendar/oauth2callback", methods=["GET"])
def calendar_oauth_callback():
    """
    Step 2: OAuth callback endpoint - Google redirects here after user grants permission.
    """
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        print(f"[OAuth] Callback received - state: {state}, code: {'present' if code else 'missing'}, error: {error}")
        
        if error:
            print(f"[OAuth] OAuth error: {error}")
            return redirect(f'{FRONTEND_URL}/calendar?error={error}')
        
        if not code or not state:
            print(f"[OAuth] Missing code or state")
            return redirect(f'{FRONTEND_URL}/calendar?error=missing_params')
        
        # Try to get username from in-memory storage first, then session
        username = oauth_states.get(state) or session.get(f'oauth_state_{state}')
        
        print(f"[OAuth] Retrieved username: {username} for state: {state}")
        print(f"[OAuth] Available states in memory: {list(oauth_states.keys())}")
        
        if not username:
            print(f"[OAuth] No username found for state {state}")
            return redirect(f'{FRONTEND_URL}/calendar?error=invalid_state')
        
        # Determine the correct redirect URI (must match the one used in auth_start)
        backend_url = os.getenv('BACKEND_URL', 'http://localhost:5000')
        redirect_uri = f'{backend_url}/calendar/oauth2callback'
        
        # Exchange code for tokens with matching redirect URI
        print(f"[OAuth] Exchanging code for tokens for user: {username}")
        print(f"[OAuth] Using redirect URI: {redirect_uri}")
        credentials = exchange_code_for_tokens(code, state, redirect_uri=redirect_uri)
        
        # Save credentials
        print(f"[OAuth] Saving credentials for user: {username}")
        save_credentials(credentials, username)
        
        # Clean up
        oauth_states.pop(state, None)
        session.pop(f'oauth_state_{state}', None)
        
        print(f"[OAuth] Success! Redirecting to frontend")
        # Redirect to frontend success page
        return redirect(f'{FRONTEND_URL}/calendar?authenticated=true&username={username}')
    except Exception as e:
        print(f"[OAuth] Exception in callback: {e}")
        import traceback
        traceback.print_exc()
        return redirect(f'{FRONTEND_URL}/calendar?error={str(e)}')



@app.route("/calendar/<username>/events", methods=["GET"])
def get_calendar_events(username):
    """
    Step 3: Get calendar events for an authenticated user.
    User must have completed OAuth flow first or have a valid token file.
    """
    try:
        # Try to get authenticated service using existing token
        try:
            service = get_calendar_service_simple(username)
        except:
            # Fall back to full OAuth service if simple version fails
            service = get_calendar_service(username)
        
        # Get events for the next 2 weeks
        days_ahead = request.args.get('days_ahead', 14, type=int)
        busy_events = get_all_busy_events(service, days_ahead=days_ahead)
        
        # Format events to match expected structure
        formatted_events = [{
            'title': title,
            'start': start.isoformat(),
            'end': end.isoformat()
        } for start, end, title in busy_events]
        
        return jsonify({
            "username": username,
            "events": formatted_events
        })
    except ValueError as e:
        # User not authenticated
        return jsonify({
            'error': str(e),
            'needs_auth': True
        }), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/calendar/<username>/check-auth", methods=["GET"])
def check_calendar_auth(username):
    """
    Check if a user has valid calendar credentials.
    """
    try:
        tokens_folder = os.getenv("GOOGLE_TOKENS_FOLDER", "./tokens")
        token_path = os.path.join(tokens_folder, f"{username}.json")
        
        if os.path.exists(token_path):
            # Try to get service to verify token is valid
            try:
                get_calendar_service_simple(username)
                return jsonify({'authenticated': True, 'username': username})
            except:
                return jsonify({'authenticated': False, 'needs_auth': True})
        else:
            return jsonify({'authenticated': False, 'needs_auth': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/calendar", methods=["GET"])
def api_calendar():
    """
    Get calendar events for all authenticated users.
    This endpoint is called by the frontend calendar page.
    """
    try:
        tokens_folder = os.getenv("GOOGLE_TOKENS_FOLDER", "./tokens")
        
        # Check if tokens folder exists
        if not os.path.exists(tokens_folder):
            return jsonify([])  # Return empty array if no tokens
        
        # Get all user tokens
        user_tokens = [f.replace('.json', '') for f in os.listdir(tokens_folder) if f.endswith(".json")]
        
        if not user_tokens:
            return jsonify([])  # Return empty array if no users
        
        all_events = []
        
        # Get events for each user
        for username in user_tokens:
            try:
                service = get_calendar_service_simple(username)
                busy_events = get_all_busy_events(service, days_ahead=14)
                
                # Format events with user info
                for start, end, title in busy_events:
                    all_events.append({
                        'id': f"{username}_{start.isoformat()}",
                        'title': f"{title} ({username})",
                        'start': start.isoformat(),
                        'end': end.isoformat(),
                        'description': f"Event for {username}",
                        'username': username
                    })
            except Exception as e:
                print(f"Error getting events for {username}: {e}")
                continue
        
        return jsonify(all_events)
    except Exception as e:
        print(f"Error in api_calendar: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/letterboxd/<username>", methods=["GET"])
def letterboxd(username):
    """
    Get Letterboxd profile data for a given username.
    Includes TMDb metadata (genres, overview) for each movie.
    Query param 'quick=true' skips TMDb lookup for faster loading.
    """
    try:
        # Map calendar username to Letterboxd username
        letterboxd_username = USER_MAPPING.get(username, username)

        # Create the integration object
        lb = LetterboxdIntegration(username=letterboxd_username)

        # Fetch recent movies
        recent_movies = lb.get_preferences(include_rss=True, include_manual=True)
        
        # Check if quick mode (skip TMDb for faster loading)
        quick_mode = request.args.get('quick') == 'true'
        
        if quick_mode:
            # Fast mode - no TMDb lookups
            formatted = [{
                "title": m.title,
                "year": m.year,
                "rating": m.rating,
                "liked": m.liked,
                "rewatch": m.rewatch,
                "source": m.source,
                "watched_date": m.watched_date.isoformat() if m.watched_date else None,
                "genres": [],
                "overview": None
            } for m in recent_movies]
        else:
            # Full mode - fetch TMDb metadata for unique movies
            unique_movies = {}
            for movie in recent_movies:
                key = (movie.title, movie.year)
                if key not in unique_movies:
                    try:
                        tmdb_data = tmdb_client.search_movie(movie.title, movie.year)
                        unique_movies[key] = tmdb_data
                    except Exception as e:
                        print(f"Failed to fetch TMDb data for {movie.title}: {e}")
                        unique_movies[key] = None

            # Format for JSON with TMDb data
            formatted = []
            for m in recent_movies:
                key = (m.title, m.year)
                tmdb_data = unique_movies.get(key)
                
                # Extract genre names and overview
                genres = []
                overview = None
                if tmdb_data:
                    genre_ids = tmdb_data.get('genre_ids', [])
                    genres = [GENRE_MAP.get(gid, f"Genre {gid}") for gid in genre_ids]
                    overview = tmdb_data.get('overview', '')
                
                formatted.append({
                    "title": m.title,
                    "year": m.year,
                    "rating": m.rating,
                    "liked": m.liked,
                    "rewatch": m.rewatch,
                    "source": m.source,
                    "watched_date": m.watched_date.isoformat() if m.watched_date else None,
                    "genres": genres,
                    "overview": overview
                })

        return jsonify({
            "calendar_username": username,
            "letterboxd_username": letterboxd_username,
            "recent_movies": formatted
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/cineville/upcoming", methods=["GET"])
def cineville_upcoming():
    """
    Get all Cineville movies for the next 7 days.
    No username required - shows all available movies.
    Includes TMDb metadata (genres, overview).
    """
    try:
        # Get all showtimes for the next 7 days in Amsterdam
        movies = scraper.get_all_showtimes(days_ahead=7, limit_amsterdam=True)
        
        # Fetch TMDb metadata for each unique movie
        unique_movies = {}
        for movie in movies:
            title = movie.get('title', '')
            year = movie.get('year')
            
            # Use (title, year) as key to avoid duplicate API calls
            key = (title, year)
            if key not in unique_movies:
                try:
                    tmdb_data = tmdb_client.search_movie(title, year)
                    unique_movies[key] = tmdb_data
                except Exception as e:
                    print(f"Failed to fetch TMDb data for {title}: {e}")
                    unique_movies[key] = None
        
        # Format movies to match expected structure with TMDb data
        formatted_movies = []
        for movie in movies:
            title = movie.get('title', '')
            year = movie.get('year')
            key = (title, year)
            tmdb_data = unique_movies.get(key)
            
            # Extract genre names from TMDb data
            genres = []
            overview = None
            if tmdb_data:
                genre_ids = tmdb_data.get('genre_ids', [])
                genres = [GENRE_MAP.get(gid, f"Genre {gid}") for gid in genre_ids]
                overview = tmdb_data.get('overview', '')
            
            formatted_movies.append({
                'title': title,
                'location': movie.get('cinema', 'Amsterdam'),
                'theater': movie.get('cinema', ''),
                'showtime': movie.get('showtime').isoformat() if movie.get('showtime') else '',
                'year': year,
                'genres': genres,
                'overview': overview
            })
        
        return jsonify(formatted_movies)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/parse", methods=["POST"])
def parse_message():
    """
    Parse a natural language movie-night request using Gemini or fallback parser.
    Example input:
      {"message": "Let's watch a movie this Friday with Alice and Bob. Mood: comedy."}
    """
    try:
        data = request.get_json() or {}
        user_input = data.get("message", "").strip()

        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        # Use main parser (handles Gemini + fallback)
        parsed_data = parse_user_request(user_input)

        if not parsed_data:
            return jsonify({"error": "Parsing failed"}), 500

        summary_text = generate_summary(parsed_data)
        parsed_data["summary"] = summary_text

        return jsonify(parsed_data), 200

    except Exception as e:
        print(f"Error in /parse route: {e}")
        return jsonify({"error": str(e)}), 500

# Add this new endpoint to app.py

@app.route("/chat", methods=["POST"])
def chat():
    """
    Natural language movie recommendation endpoint.
    Creates a poll with movie titles only (not individual showtimes).
    Also handles natural language voting.
    """
    try:
        data = request.get_json() or {}
        user_input = data.get("message", "").strip()
        active_poll_id = data.get("active_poll_id")  # Frontend sends this if there's an active poll

        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        # CHECK IF THIS IS A VOTE FOR AN ACTIVE POLL
        if active_poll_id:
            poll = data.get("poll")  # Frontend sends poll data
            if poll:
                poll_options = poll.get('options', [])
                recommendations = poll.get('recommendations', [])
                vote_index = parse_vote_with_gemini(user_input, poll_options)
                
                if vote_index >= 0:
                    # User voted! Find movie details and announce winner
                    voted_movie = poll_options[vote_index]['movie']
                    movie_data = next((r for r in recommendations if r.get('title') == voted_movie), None)
                    
                    if movie_data and movie_data.get('showtimes'):
                        first_showtime = movie_data['showtimes'][0]
                        cinema = first_showtime.cinema
                        time_str = first_showtime.start.strftime("%A at %H:%M")
                        
                        winner_message = f"🎉 Great choice! '{voted_movie}' wins with 3 votes!\n\n"
                        winner_message += f"📍 Location: {cinema}\n"
                        winner_message += f"🕐 Time: {time_str}\n\n"
                        winner_message += f"✅ I've added this to everyone's calendar. See you there! 🎬"
                    else:
                        winner_message = f"🎉 Great choice! '{voted_movie}' wins with 3 votes!\n\n✅ I've added this to everyone's calendar. See you there! 🎬"
                    
                    return jsonify({
                        "message": winner_message,
                        "poll_complete": True,
                        "winner": {"movie": voted_movie, "votes": 3},
                        "poll": None
                    }), 200
                else:
                    # Couldn't parse vote
                    return jsonify({
                        "message": "I couldn't understand your vote. Please try:\n- Saying the movie name (e.g., 'Bugonia')\n- Using a number (e.g., 'number 1' or 'option 2')",
                        "vote_recorded": False,
                        "poll": {"poll_id": active_poll_id, "options": poll_options}
                    }), 200

        # 1. Parse the user message
        print(f"📝 Parsing message: {user_input}")
        parsed = parse_user_request(user_input)
        
        if not parsed or parsed.get("error"):
            return jsonify({
                "error": "Could not parse your request",
                "parsed": parsed
            }), 400

        # 2. Check for participants - USE GEMINI FOR CONVERSATIONAL RESPONSE
        participants = parsed.get("participants", [])
        if not participants:
            try:
                import google.generativeai as genai
                
                # Use GEMINI_API_KEY like in gemini_nlg.py
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError("GEMINI_API_KEY not found")
                
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.0-flash-lite')
                
                prompt = f"""You are a friendly movie recommendation assistant. The user said: "{user_input}"

        This doesn't seem to be a complete movie request. Help them by:
        1. If they're asking about a specific movie, tell them you can help find showtimes
        2. If they're greeting you, greet back warmly and explain what you do
        3. If they're asking what you can do, explain briefly
        4. If it's unclear, gently guide them to provide: who's watching, when, and mood

        Keep it natural, friendly, and under 3 sentences. Don't use the exact same phrases repeatedly."""
                
                response = model.generate_content(prompt)
                conversational_response = response.text.strip()
                
                return jsonify({
                    "message": conversational_response,
                    "parsed": parsed,
                    "recommendations": [],
                    "poll": None
                }), 200
                
            except Exception as e:
                print(f"Gemini conversational error: {e}")
                return jsonify({
                    "message": "I'd love to help you find a movie! Just let me know who's watching, when, and what mood you're in.",
                    "parsed": parsed,
                    "recommendations": [],
                    "poll": None
                }), 200
        
        letterboxd_usernames = []
        for participant in participants:
            mapped_name = None
            for key, value in USER_MAPPING.items():
                if participant.lower() == key.lower():
                    mapped_name = value
                    break
            letterboxd_usernames.append(mapped_name or participant)
        
        print(f"👥 Mapped participants: {participants} -> {letterboxd_usernames}")

        # 3. Extract other parameters
        mood = parsed.get("mood")
        date_str = parsed.get("date")
        days_ahead = parse_date_to_days_ahead(date_str)
        print(f"📅 Date requested: {date_str} -> days_ahead={days_ahead}")

        # 4. Get recommendations using orchestrator
        print(f"🎬 Getting recommendations for {letterboxd_usernames}")
        recommendations_result = get_group_recommendations(
            usernames=letterboxd_usernames,
            days_ahead=days_ahead,
            limit_amsterdam=True,
            max_results=10,
            use_calendar=True,
            min_slot_minutes=120,
            mood=mood,
            learn_from_history=True,
        )

        recommendations = recommendations_result.get("recommendations", [])

               # 5. Create fake poll data (no real poll manager)
        poll_id = None
        poll_data = None
        
        if recommendations and len(recommendations) > 0:
            top_3_movies = recommendations[:3]
            poll_options = [
                {
                    'text': f"{m.get('title')} ({len(m.get('showtimes', []))} showtimes available)",
                    'movie': m.get('title'),
                    'showtime_count': len(m.get('showtimes', []))
                }
                for m in top_3_movies
            ]
            
            poll_id = "fake_poll_123"
            poll_data = {
                "poll_id": poll_id,
                "title": f"Movie Night - {date_str or 'Soon'}",
                "options": poll_options,
                "voted_count": 2,  # Fake: sanne and ioana "voted"
                "total_participants": len(participants),
                "recommendations": top_3_movies
            }

        # 6. Generate natural language response
        if poll_id:
            summary = f"Great! I've found some perfect matches for your movie night.\n\n📊 Vote for your favorite:"
            for i, opt in enumerate(poll_data['options']):
                summary += f"\n{i+1}. {opt['movie']} ({opt['showtime_count']} showtimes available)"
            summary += f"\n\n✅ 2 out of {len(participants)} have already voted!"
        else:
            summary = generate_natural_response(parsed_data=parsed, recommendations=recommendations)

        return jsonify({
            "message": summary,
            "parsed": {
                "participants": participants,
                "letterboxd_usernames": letterboxd_usernames,
                "date": date_str,
                "mood": mood
            },
            "recommendations": recommendations,
            "group_history": recommendations_result.get("group_history", {}),
            "poll": poll_data
        }), 200

    except Exception as e:
        print(f"❌ Error in /chat route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
        
        # 6. Generate natural language response
        # if poll_id:
        #     # Use Gemini to generate natural poll introduction
        #     try:
        #         import google.generativeai as genai
                
        #         # Use GEMINI_API_KEY like in gemini_nlg.py
        #         api_key = os.getenv("GEMINI_API_KEY")
        #         if not api_key:
        #             raise ValueError("GEMINI_API_KEY not found")
                
        #         genai.configure(api_key=api_key)
        #         model = genai.GenerativeModel('gemini-2.0-flash-lite')
                
        #         # Build participant list naturally
        #         if len(participants) > 1:
        #             participant_list = ", ".join(participants[:-1]) + f" and {participants[-1]}"
        #         else:
        #             participant_list = participants[0]
                
        #         date_text = date_str if date_str else "soon"
        #         mood_text = mood if mood else "any mood"
                
        #         # Get movie titles for the prompt
        #         movie_titles = [opt['movie'] for opt in poll_data['options']]
                
        #         prompt = f"""You're helping organize a movie night. Generate a friendly, natural confirmation message.

# Details:
# - The user is going with: {participant_list}
# - Date: {date_text}
# - Mood: {mood_text}
# - Top movie options: {', '.join(movie_titles)}

# Create a warm, enthusiastic message that:
# 1. Confirms the plan (YOU are watching with [others] on [date])
# 2. Says you found great matches
# 3. Asks which movie YOU'D like to see

# Address the USER directly (use "you" and "your"). Don't greet anyone or use names in the opening. 
# Keep it conversational and under 2 sentences. Vary your phrasing - don't be repetitive."""
                
#                 response = model.generate_content(prompt)
#                 intro_message = response.text.strip()
                
#                 summary = intro_message
#                 summary += f"\n\n📊 Vote for your favorite:"
#                 for i, opt in enumerate(poll_data['options']):
#                     summary += f"\n{i+1}. {opt['movie']} ({opt['showtime_count']} showtimes available)"
#                 summary += f"\n\n✅ {poll_data['voted_count']} out of {poll_data['total_participants']} have already voted!"
                
#             except Exception as e:
#                 print(f"Gemini poll message error: {e}")
#                 # Fallback to simple message
#                 if len(participants) > 1:
#                     participant_names = "you, " + ", ".join(participants[:-1]) + f" and {participants[-1]}"
#                 else:
#                     participant_names = "you"
                
#                 date_text = date_str if date_str else "soon"
#                 mood_text = f"in the mood for something {mood}" if mood else "ready for a movie"
                
#                 summary = f"Great! So we have {participant_names} watching a movie {date_text}, {mood_text}. "
#                 summary += f"I've found some perfect matches! Which one would you like to see?"
#                 summary += f"\n\n📊 Vote for your favorite:"
#                 for i, opt in enumerate(poll_data['options']):
#                     summary += f"\n{i+1}. {opt['movie']} ({opt['showtime_count']} showtimes available)"
#                 summary += f"\n\n✅ {poll_data['voted_count']} out of {poll_data['total_participants']} have already voted!"
#         else:
#             # No poll - just show the NLG summary
#             summary = generate_natural_response(
#                 parsed_data=parsed,
#                 recommendations=recommendations
#             )

#         return jsonify({
#             "message": summary,
#             "parsed": {
#                 "participants": participants,
#                 "letterboxd_usernames": letterboxd_usernames,
#                 "date": date_str,
#                 "mood": mood
#             },
#             "recommendations": recommendations,
#             "group_history": recommendations_result.get("group_history", {}),
#             "poll": poll_data
#         }), 200

#     except Exception as e:
#         print(f"❌ Error in /chat route: {e}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({"error": str(e)}), 500
    
@app.route("/create-poll", methods=["POST"])
def create_poll():
    """
    Create a poll from movie recommendations.
    
    Expected JSON:
    {
        "recommendations": [...],  // From /chat response
        "participants": ["sanne", "noor", "ioana"],
        "poll_title": "Movie Night - Friday Comedy"
    }
    """
    try:
        data = request.get_json() or {}
        recommendations = data.get("recommendations", [])
        participants = data.get("participants", [])
        poll_title = data.get("poll_title", "Movie Night Poll")
        
        if not recommendations:
            return jsonify({"error": "No recommendations provided"}), 400
        
        if not participants:
            return jsonify({"error": "No participants provided"}), 400
        
        # Take top 3 movies
        top_3_movies = recommendations[:3]
        
        # Build poll options from showtimes
        poll_options = []
        for movie in top_3_movies:
            title = movie.get('title')
            showtimes = movie.get('showtimes', [])
            
            # Add each showtime as a poll option
            for showtime in showtimes:
                cinema = showtime.cinema  # ← FIXED
                start_time = showtime.start.isoformat()  # ← FIXED
                
                option_text = f"{title} - {cinema} at {start_time}"
                poll_options.append({
                    'text': option_text,
                    'movie': title,
                    'cinema': cinema,
                    'time': start_time
                })
        
        # Create the poll
        poll_id = poll_manager.create_poll(
            title=poll_title,
            options=poll_options,
            participants=participants,
            max_votes_per_user=3
        )
        
        # DEMO: Hardcode votes for non-demo users
        # Assume the demo user is 'noor' - others vote automatically
        demo_user = "noor"
        
        # Pre-vote for sanne (likes first movie, different times)
        if "sanne" in participants and "sanne" != demo_user:
            sanne_votes = []
            for i, option in enumerate(poll_options):
                if option['movie'] == top_3_movies[0].get('title') and len(sanne_votes) < 3:
                    sanne_votes.append(i)
            
            if sanne_votes:
                poll_manager.submit_vote(poll_id, "sanne", sanne_votes)
                print(f"[DEMO] Auto-voted for sanne: {sanne_votes}")
        
        # Pre-vote for ioana (likes second movie, different cinemas)
        if "ioana" in participants and "ioana" != demo_user:
            ioana_votes = []
            second_movie = top_3_movies[1].get('title') if len(top_3_movies) > 1 else top_3_movies[0].get('title')
            
            for i, option in enumerate(poll_options):
                if option['movie'] == second_movie and len(ioana_votes) < 3:
                    ioana_votes.append(i)
            
            if ioana_votes:
                poll_manager.submit_vote(poll_id, "ioana", ioana_votes)
                print(f"[DEMO] Auto-voted for ioana: {ioana_votes}")
        
        # Get current results
        results = poll_manager.get_poll_results(poll_id)
        
        return jsonify({
            "poll_id": poll_id,
            "title": poll_title,
            "options": poll_options,
            "participants": participants,
            "demo_user": demo_user,
            "current_votes": results['votes'],
            "message": f"Poll created! {len([p for p in participants if p != demo_user])} user(s) have already voted."
        })
        
    except Exception as e:
        print(f"Error creating poll: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/vote", methods=["POST"])
def vote():
    """
    Submit a vote to a poll.
    
    Expected JSON:
    {
        "poll_id": "abc123",
        "username": "noor",
        "option_indices": [0, 2, 5]  // Up to 3 options
    }
    """
    try:
        data = request.get_json() or {}
        poll_id = data.get("poll_id")
        username = data.get("username")
        option_indices = data.get("option_indices", [])
        
        if not poll_id:
            return jsonify({"error": "poll_id required"}), 400
        
        if not username:
            return jsonify({"error": "username required"}), 400
        
        if not option_indices or len(option_indices) == 0:
            return jsonify({"error": "Must select at least one option"}), 400
        
        if len(option_indices) > 3:
            return jsonify({"error": "Maximum 3 options allowed"}), 400
        
        # Submit vote
        success = poll_manager.submit_vote(poll_id, username, option_indices)
        
        if not success:
            return jsonify({"error": "Vote submission failed"}), 400
        
        # Get updated results
        results = poll_manager.get_poll_results(poll_id)
        
        return jsonify({
            "success": True,
            "message": f"Vote recorded for {username}!",
            "results": results
        })
        
    except Exception as e:
        print(f"Error submitting vote: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/poll/<poll_id>/results", methods=["GET"])
def get_poll_results(poll_id):
    """
    Get current poll results and determine winner.
    If all voted, suggest a specific showtime.
    """
    try:
        results = poll_manager.get_poll_results(poll_id)
        
        if not results:
            return jsonify({"error": "Poll not found"}), 404
        
        # Determine winner (most votes)
        option_tallies = results.get('option_tallies', {})
        movie_tallies = results.get('movie_tallies', {})
        
        poll = poll_manager.polls.get(poll_id)
        all_voted = len(results['votes']) == len(poll['participants'])
        
        if option_tallies:
            # Find option with most votes
            winner_option_id = max(option_tallies.items(), key=lambda x: x[1])[0]
            winner_votes = option_tallies[winner_option_id]
            winner_option = poll['options'][int(winner_option_id.replace('option_', ''))]
            winner_movie = winner_option.get('movie')
            
            # If everyone voted, find specific showtime suggestion
            showtime_suggestion = None
            if all_voted:
                # Get the winning movie's full recommendation data
                # (You'd need to store recommendations with the poll or fetch them again)
                # For now, generate a message template
                showtime_suggestion = {
                    "movie": winner_movie,
                    "message": f"Great choice! Would you like to watch '{winner_movie}'?",
                    "note": "Specific showtime will be suggested based on availability"
                }
            
            return jsonify({
                "poll_id": poll_id,
                "results": results,
                "winner": {
                    "option_id": winner_option_id,
                    "option_text": winner_option['text'],
                    "movie": winner_movie,
                    "votes": winner_votes
                },
                "movie_tallies": movie_tallies,
                "all_voted": all_voted,
                "showtime_suggestion": showtime_suggestion
            })
        else:
            return jsonify({
                "poll_id": poll_id,
                "results": results,
                "winner": None,
                "all_voted": False,
                "message": "No votes yet"
            })
        
    except Exception as e:
        print(f"Error getting poll results: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/poll/<poll_id>/suggest-showtime", methods=["GET"])
def suggest_showtime(poll_id):
    """
    After voting ends, suggest a specific showtime for the winning movie.
    Returns a natural language message.
    """
    try:
        # Get poll results
        results = poll_manager.get_poll_results(poll_id)
        if not results:
            return jsonify({"error": "Poll not found"}), 404
        
        poll = poll_manager.polls.get(poll_id)
        
        # Check if everyone voted
        all_voted = len(results['votes']) == len(poll['participants'])
        if not all_voted:
            return jsonify({
                "message": f"Waiting for {len(poll['participants']) - len(results['votes'])} more vote(s)..."
            })
        
        # Get winner
        option_tallies = results.get('option_tallies', {})
        if not option_tallies:
            return jsonify({"error": "No votes yet"}), 400
        
        winner_option_id = max(option_tallies.items(), key=lambda x: x[1])[0]
        winner_option = poll['options'][int(winner_option_id.replace('option_', ''))]
        winner_movie = winner_option.get('movie')
        
        # Get the stored recommendations from poll metadata
        # (We need to store recommendations with the poll)
        recommendations = poll.get('recommendations', [])
        
        # Find the winning movie's showtimes
        winning_movie_data = None
        for rec in recommendations:
            if rec.get('title') == winner_movie:
                winning_movie_data = rec
                break
        
        if not winning_movie_data or not winning_movie_data.get('showtimes'):
            return jsonify({
                "message": f"'{winner_movie}' won! Let me check showtimes..."
            })
        
        # Pick first available showtime (could be smarter - e.g., earliest convenient time)
        first_showtime = winning_movie_data['showtimes'][0]
        cinema = first_showtime.cinema
        time_str = first_showtime.start.strftime("%A at %H:%M")  # "Friday at 13:30"
        
        # Generate natural message
        message = f"Perfect! Would you like to go to '{winner_movie}' on {time_str} at {cinema}? 🎬"
        
        return jsonify({
            "poll_id": poll_id,
            "winner_movie": winner_movie,
            "suggested_showtime": {
                "cinema": cinema,
                "time": first_showtime.start.isoformat(),
                "formatted_time": time_str
            },
            "message": message,
            "all_voted": True
        })
        
    except Exception as e:
        print(f"Error suggesting showtime: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=os.getenv('FLASK_ENV') != 'production', host='0.0.0.0', port=port)
