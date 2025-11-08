# scripts/find_common_free_time.py
from src.calendar_agent import authenticate, get_all_busy_events
from src.utils.time_utils import merge_events, find_free_slots
from datetime import datetime, timedelta
import os

# 1. List of token filenames (one per friend)
# user_tokens = ["sanne.json", "ioana.json"]
tokens_folder = os.getenv("GOOGLE_TOKENS_FOLDER", "./tokens")
user_tokens = [f for f in os.listdir(tokens_folder) if f.endswith(".json")]

# 2. Collect busy events from all users
all_busy = []
for token_file in user_tokens:
    service = authenticate(token_filename=token_file)
    busy = get_all_busy_events(service, days_ahead=7)  # your function that fetches all calendars
    all_busy.extend(busy)

# 3. Merge overlapping events
merged_busy = merge_events(all_busy)

# 4. Define timeframe to check for free slots
start = datetime.now()
end = start + timedelta(days=7)

# 5. Find free slots of at least 2 hours
common_free = find_free_slots(merged_busy, start, end, min_duration_minutes=120)

# 6. Print results
print("Common free slots for all users (>= 2 hours):")
for s, e in common_free:
    print(f" - {s} to {e}")
