# src/orchestrator.py
import os
from datetime import datetime, timedelta
from src.movie_matcher import GroupMovieMatcher, CinevilleScraper, TMDbClient

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "0ad625d2ef7503df5817998ca55e0bdf")


def get_group_recommendations(
    usernames,
    days_ahead: int = 7,
    limit_amsterdam: bool = True,
    max_results: int = 10,
    use_calendar: bool = True,
    min_slot_minutes: int = 120,
    mood: str | None = None,
    learn_from_history: bool = True,
):
    """
    High-level group recommendation flow:
    - usernames: list of Letterboxd usernames
    - days_ahead: how many days into the future to consider
    - limit_amsterdam: if True, only fetch Cineville movies in Amsterdam
    - use_calendar: filter recommendations by common free time
    - min_slot_minutes: minimum duration of free slot
    - mood: optional mood filter
    - learn_from_history: optionally boost based on past group history
    """
    print("🔄 Starting group recommendation flow...")

    cineville = CinevilleScraper()
    tmdb = TMDbClient(api_key=TMDB_API_KEY)
    matcher = GroupMovieMatcher(cineville, tmdb)

    results, group_history = matcher.match_group(
        usernames=usernames,
        days_ahead=days_ahead,
        limit_amsterdam=limit_amsterdam,
        max_results=max_results,
        use_calendar=use_calendar,
        min_slot_minutes=min_slot_minutes,
        mood=mood,
        learn_from_history=learn_from_history,
    )

    # Convert results and history into plain JSON-safe dicts
    serialized_results = [
        r.to_dict() if hasattr(r, "to_dict") else r.__dict__
        for r in results
    ]

    serialized_history = {
        "group_id": getattr(group_history, "group_id", None),
        "history": getattr(group_history, "history", []),
        "preferences": getattr(group_history, "preferences", {}),
    }

    return {
        "recommendations": serialized_results,
        "group_history": serialized_history,
    }
