from flask import Flask, request, jsonify
from src.orchestrator import get_group_recommendations
from flask_cors import CORS
from src.calendar_agent import get_user_events


app = Flask(__name__)
CORS(app)
USER_MAPPING = {
    "sanne": "SanneBr",
    "noor": "noorsterre",
    "ioana": "visionofdavinci"
}

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

@app.route("/calendar/<username>", methods=["GET"])
def calendar(username):
    try:
        events = get_user_events(username)
        return jsonify({"username": username, "events": events})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# app.py (add near your other imports)
from src.letterboxd_integration import LetterboxdIntegration

# Optional mapping from Google Calendar username → Letterboxd username
USER_MAPPING = {
    "my_calendar_user": "my_letterboxd_user"
}

@app.route("/letterboxd/<username>", methods=["GET"])
def letterboxd(username):
    try:
        # Map calendar username to Letterboxd username
        letterboxd_username = USER_MAPPING.get(username, username)

        # Create the integration object
        lb = LetterboxdIntegration(username=letterboxd_username)

        # Fetch recent movies
        recent_movies = lb.get_preferences(include_rss=True, include_manual=True)

        # Format for JSON
        formatted = [
            {
                "title": m.title,
                "year": m.year,
                "rating": m.rating,
                "liked": m.liked,
                "rewatch": m.rewatch,
                "source": m.source,
                "watched_date": m.watched_date.isoformat() if m.watched_date else None
            }
            for m in recent_movies
        ]

        return jsonify({
            "calendar_username": username,
            "letterboxd_username": letterboxd_username,
            "recent_movies": formatted
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
from src.cineville_scraper import CinevilleScraper

scraper = CinevilleScraper()

@app.route("/cineville/upcoming", methods=["GET"])
def cineville_upcoming():
    try:
        movies = scraper.get_movies_with_schedule(days_ahead=7)  # next 7 days
        return jsonify({"movies": movies})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True, port=5000)
