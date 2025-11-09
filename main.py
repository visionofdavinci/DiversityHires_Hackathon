<<<<<<< HEAD
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
from src.movie_matcher import GroupMovieMatcher, TMDbClient
from src.cineville_scraper import CinevilleScraper
from src.calendar_agent import authenticate, find_free_time

app = FastAPI()

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
cineville = CinevilleScraper()
tmdb = TMDbClient()
matcher = GroupMovieMatcher(cineville, tmdb)

@app.get("/api/recommendations")
async def get_recommendations(
    usernames: str,
    days_ahead: int = 7,
    limit_amsterdam: bool = True,
    max_results: int = 20,
    use_calendar: bool = True,
    min_slot_minutes: int = 120,
    mood: Optional[str] = None
):
    try:
        username_list = [u.strip() for u in usernames.split(',') if u.strip()]
        if not username_list:
            raise HTTPException(status_code=400, detail="No valid usernames provided")

        results, _ = matcher.match_group(
            usernames=username_list,
            days_ahead=days_ahead,
            limit_amsterdam=limit_amsterdam,
            max_results=max_results,
            use_calendar=use_calendar,
            min_slot_minutes=min_slot_minutes,
            mood=mood
        )
        
        # Convert datetime objects to ISO strings for JSON serialization
        serialized_results = []
        for r in results:
            serialized_showtimes = [
                {"cinema": st.cinema, "start": st.start.isoformat()}
                for st in r.showtimes
            ]
            serialized_results.append({
                "title": r.title,
                "year": r.year,
                "group_score": r.group_score,
                "per_user_scores": r.per_user_scores,
                "showtimes": serialized_showtimes,
                "cineville": r.cineville,
                "tmdb": r.tmdb
            })
            
        return serialized_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/calendar/{username}/free-slots")
async def get_free_slots(username: str, days: int = 7):
    try:
        service = authenticate(f"{username}.json")
        slots = find_free_time(service, days_ahead=days)
        return [
            {"start": start.isoformat(), "end": end.isoformat()}
            for start, end in slots
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/letterboxd/{username}/profile")
async def get_letterboxd_profile(username: str):
    try:
        # This is just the basic profile info, expand as needed
        return {
            "username": username,
            "ratings": []  # You can add actual ratings here
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
=======
# main.py
import os
from src.orchestrator import get_group_recommendations

# Set these environment variables or hardcode for testing
# os.environ["LETTERBOXD_USERNAMES"] = "visionofdavinci,friend1"
# os.environ["TMDB_API_KEY"] = "your_tmdb_api_key_here"

def main():
    usernames_raw = os.getenv("LETTERBOXD_USERNAMES", "")
    usernames = [u.strip() for u in usernames_raw.split(",") if u.strip()]

    if not usernames:
        print("⚠️ Set LETTERBOXD_USERNAMES='user1,user2' in your environment to test.")
        return

    print(f"👥 Using users: {', '.join(usernames)}\n")

    rec_data = get_group_recommendations(
        usernames=usernames,
        days_ahead=3,
        max_results=10,
        use_calendar=True,   # set False to ignore calendar filtering for testing
        min_slot_minutes=120,
    )

    recommendations = rec_data["recommendations"]

    if not recommendations:
        print("No recommendations found 😢")
        return

    print("🎬 Group Movie Recommendations:\n")
    for i, r in enumerate(recommendations, start=1):
        print(f"{i:2d}. {r.title} ({r.year or '?'})  group_score={r.group_score:.3f}")
        for u, s in r.per_user_scores.items():
            print(f"    {u}: {s:.3f}")

        # Show first few showtimes
        for st in r.showtimes[:3]:
            print(f"    {st.cinema} @ {st.start.strftime('%a %d %b %H:%M')}")
        if len(r.showtimes) > 3:
            print(f"    (+ {len(r.showtimes) - 3} more showtimes)")
        print()

if __name__ == "__main__":
    main()
>>>>>>> hosttest
