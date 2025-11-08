# scripts/create_token_for_user.py
import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from src.utils.config_loader import get_config

def create_token_for_user(username: str):
    """
    Runs local server OAuth flow. Opens browser for login and consent.
    Saves tokens/{username}.json
    """
    cfg = get_config()
    scopes = cfg["GOOGLE_CALENDAR_SCOPES"]
    tokens_folder = os.getenv("GOOGLE_TOKENS_FOLDER", "./tokens")
    os.makedirs(tokens_folder, exist_ok=True)
    token_path = Path(tokens_folder) / f"{username}.json"

    flow = InstalledAppFlow.from_client_secrets_file(
        cfg["GOOGLE_CREDENTIALS_PATH"],
        scopes
    )

    # Hackathon-friendly: local server opens browser for authentication
    creds = flow.run_local_server(port=0)

    # Save credentials JSON
    with open(token_path, "w") as f:
        f.write(creds.to_json())
    print(f"Saved token to {token_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="Short name to store token as (e.g. alice)")
    args = parser.parse_args()
    create_token_for_user(args.username)
