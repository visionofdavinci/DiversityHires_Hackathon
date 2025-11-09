from flask import Flask, request, jsonify, redirect, session
from flask_cors import CORS
import os
from src.orchestrator import get_group_recommendations
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

app = Flask(__name__)
# Use a consistent secret key (in production, use environment variable)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production-12345678')

# Get allowed origins from environment variable or use defaults
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
allowed_origins = [FRONTEND_URL, "http://localhost:3000", "http://localhost:5000"]

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

# Initialize services
scraper = CinevilleScraper()

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
        
        # Generate OAuth URL
        auth_url, state = get_authorization_url()
        
        # Store username in in-memory dict (more reliable than session for OAuth)
        oauth_states[state] = username
        print(f"[OAuth] Stored state {state} for username {username}")
        
        # Also try session as backup
        session[f'oauth_state_{state}'] = username
        
        return jsonify({
            'auth_url': auth_url,
            'state': state,
            'message': 'Please visit the auth_url to grant calendar access'
        })
    except Exception as e:
        print(f"[OAuth] Error in auth_start: {e}")
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
            return redirect(f'http://localhost:3000/calendar?error={error}')
        
        if not code or not state:
            print(f"[OAuth] Missing code or state")
            return redirect('http://localhost:3000/calendar?error=missing_params')
        
        # Try to get username from in-memory storage first, then session
        username = oauth_states.get(state) or session.get(f'oauth_state_{state}')
        
        print(f"[OAuth] Retrieved username: {username} for state: {state}")
        print(f"[OAuth] Available states in memory: {list(oauth_states.keys())}")
        
        if not username:
            print(f"[OAuth] No username found for state {state}")
            return redirect('http://localhost:3000/calendar?error=invalid_state')
        
        # Exchange code for tokens
        print(f"[OAuth] Exchanging code for tokens for user: {username}")
        credentials = exchange_code_for_tokens(code, state)
        
        # Save credentials
        print(f"[OAuth] Saving credentials for user: {username}")
        save_credentials(credentials, username)
        
        # Clean up
        oauth_states.pop(state, None)
        session.pop(f'oauth_state_{state}', None)
        
        print(f"[OAuth] Success! Redirecting to frontend")
        # Redirect to frontend success page
        return redirect(f'http://localhost:3000/calendar?authenticated=true&username={username}')
    except Exception as e:
        print(f"[OAuth] Exception in callback: {e}")
        import traceback
        traceback.print_exc()
        return redirect(f'http://localhost:3000/calendar?error={str(e)}')



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


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=os.getenv('FLASK_ENV') != 'production', host='0.0.0.0', port=port)
