import os
import sys
from datetime import datetime, timedelta

# Ensure Python can find the src folder
sys.path.append(os.path.join(os.getcwd(), "src"))

from calendar_agent import authenticate, get_all_busy_events
from utils.time_utils import merge_events, find_free_slots

def find_common_available_times(days_ahead=7, min_duration_minutes=120):
    """
    Find common available time slots for all users based on their calendar availability.
    
    Args:
        days_ahead (int): Number of days to look ahead for availability
        min_duration_minutes (int): Minimum duration of free slots in minutes
    
    Returns:
        list: List of tuples containing (start_datetime, end_datetime) for common free slots
    """
    # Get all user tokens
    tokens_folder = os.getenv("GOOGLE_TOKENS_FOLDER", "/etc/secrets")
    user_tokens = [f for f in os.listdir(tokens_folder) if f.endswith(".json")]
    
    if not user_tokens:
        raise ValueError("No user tokens found in the tokens folder")
    
    # Collect all busy times from each user's calendar
    all_busy = []
    for token_file in user_tokens:
        service = authenticate(token_filename=token_file)
        busy = get_all_busy_events(service, days_ahead=days_ahead)
        all_busy.extend(busy)
    
    # Merge overlapping busy events
    merged_busy = merge_events(all_busy)
    
    # Define time range
    start = datetime.now()
    end = start + timedelta(days=days_ahead)
    
    # Find common free slots
    common_free = find_free_slots(merged_busy, start, end, min_duration_minutes=min_duration_minutes)
    
    return common_free

def print_common_slots(common_slots):
    """
    Print the common free time slots in a readable format.
    
    Args:
        common_slots (list): List of (start_datetime, end_datetime) tuples
    """
    print(f"Common free slots for all users (>= 2 hours):")
    for start, end in common_slots:
        print(f" - {start.strftime('%A, %b %d %Y %H:%M')} to {end.strftime('%H:%M')}")

if __name__ == "__main__":
    # Example usage
    common_free_slots = find_common_available_times()
    print_common_slots(common_free_slots)