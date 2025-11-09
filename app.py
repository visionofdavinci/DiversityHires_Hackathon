from flask import Flask, request, jsonify
from src.orchestrator import get_group_recommendations
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
