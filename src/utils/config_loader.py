# src/utils/config_loader.py
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

def get_config():
    return {
        "GOOGLE_CREDENTIALS_PATH": os.getenv("GOOGLE_CREDENTIALS_PATH"),
        "GOOGLE_TOKEN_PATH": os.getenv("GOOGLE_TOKEN_PATH"),
        "GOOGLE_CALENDAR_SCOPES": os.getenv("GOOGLE_CALENDAR_SCOPES").split(","),
        "TMDB_API_KEY": os.getenv("TMDB_API_KEY"),
        "LETTERBOXD_USERNAMES": os.getenv("LETTERBOXD_USERNAMES").split(","),
        "GOOGLE_TOKENS_FOLDER": os.getenv("GOOGLE_TOKENS_FOLDER"),
    }
