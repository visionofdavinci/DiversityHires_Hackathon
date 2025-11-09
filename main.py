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
