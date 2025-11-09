"""
poll_manager.py

Handles creation and management of group movie polls.

- Creates a poll from top movie recommendations
- Stores votes in memory (for now; can be replaced by a DB later)
- Returns poll results in ranked order
"""

from __future__ import annotations
from typing import Dict, List
from datetime import datetime
from uuid import uuid4

from src.orchestrator import get_group_recommendations

# ----------------------------------------------------------------------
# In-memory storage (simple, replace with DB later)
# ----------------------------------------------------------------------

ACTIVE_POLLS: Dict[str, dict] = {}


# ----------------------------------------------------------------------
# Create a poll
# ----------------------------------------------------------------------
def create_poll(usernames: List[str], **kwargs) -> dict:
    """
    Create a poll based on top group recommendations.
    """
    recommendations = get_group_recommendations(usernames=usernames, **kwargs)
    movies = recommendations.get("movies", recommendations)  # support both dict or list output

    poll_id = str(uuid4())

    poll_data = {
        "poll_id": poll_id,
        "created_at": datetime.utcnow().isoformat(),
        "usernames": usernames,
        "movies": [],
        "votes": {},  # {username: movie_title}
    }

    for m in movies:
        poll_data["movies"].append({
            "title": m.get("title"),
            "year": m.get("year"),
            "group_score": m.get("group_score"),
            "showtimes": m.get("showtimes", []),
            "poster": m.get("tmdb", {}).get("poster_path"),
            "overview": m.get("tmdb", {}).get("overview"),
        })

    ACTIVE_POLLS[poll_id] = poll_data
    return poll_data


# ----------------------------------------------------------------------
# Voting
# ----------------------------------------------------------------------
def submit_vote(poll_id: str, username: str, movie_title: str) -> dict:
    """
    Record a user's vote for a movie in a poll.
    """
    poll = ACTIVE_POLLS.get(poll_id)
    if not poll:
        raise ValueError("Poll not found")

    if movie_title not in [m["title"] for m in poll["movies"]]:
        raise ValueError("Invalid movie title for this poll")

    poll["votes"][username] = movie_title
    return {"message": f"Vote recorded for {username}", "poll_id": poll_id}


# ----------------------------------------------------------------------
# Get poll results
# ----------------------------------------------------------------------
def get_poll_results(poll_id: str) -> dict:
    """
    Return poll standings: number of votes per movie.
    """
    poll = ACTIVE_POLLS.get(poll_id)
    if not poll:
        raise ValueError("Poll not found")

    tally: Dict[str, int] = {m["title"]: 0 for m in poll["movies"]}
    for vote in poll["votes"].values():
        tally[vote] = tally.get(vote, 0) + 1

    results = sorted(
        [{"title": t, "votes": v} for t, v in tally.items()],
        key=lambda x: x["votes"],
        reverse=True,
    )

    return {
        "poll_id": poll_id,
        "results": results,
        "total_votes": len(poll["votes"]),
        "movies": poll["movies"],
    }
