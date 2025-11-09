# src/utils/config_loader.py
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

def get_config():
    # Get scopes with default value to prevent None.split() errors
    scopes = os.getenv("GOOGLE_CALENDAR_SCOPES", "https://www.googleapis.com/auth/calendar.readonly")
    usernames = os.getenv("LETTERBOXD_USERNAMES", "")
    
    return {
        "GOOGLE_CREDENTIALS_PATH": os.getenv("GOOGLE_CREDENTIALS_PATH"),
        "GOOGLE_TOKEN_PATH": os.getenv("GOOGLE_TOKEN_PATH"),
        "GOOGLE_CALENDAR_SCOPES": scopes.split(",") if scopes else ["https://www.googleapis.com/auth/calendar.readonly"],
        "TMDB_API_KEY": os.getenv("TMDB_API_KEY"),
        "LETTERBOXD_USERNAMES": usernames.split(",") if usernames else [],
        "GOOGLE_TOKENS_FOLDER": os.getenv("GOOGLE_TOKENS_FOLDER"),
        "SHOWTIME_DEBUG": os.getenv("SHOWTIME_DEBUG", "0") == "1",
        "USE_CALENDAR": os.getenv("USE_CALENDAR", "0") == "1",
        "SHOWTIME_ALLOW_START_INSIDE": os.getenv("SHOWTIME_ALLOW_START_INSIDE", "0") == "1"
    }
