# src/calendar_agent.py
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from src.utils.config_loader import get_config
from src.utils.time_utils import find_free_slots
from datetime import datetime, timedelta
from google.auth.transport.requests import Request




def authenticate(token_filename: str = None):
    """
    Authenticate a Google Calendar user using a specific token file.
    If no token_filename is provided, fallback to default from config.
    """
    from google.auth.transport.requests import Request  # make sure this import exists
    cfg = get_config()
    tokens_folder = os.getenv("GOOGLE_TOKENS_FOLDER", "./tokens")
    os.makedirs(tokens_folder, exist_ok=True)

    # Determine which token file to use
    token_path = os.path.join(tokens_folder, token_filename) if token_filename else cfg["GOOGLE_TOKEN_PATH"]

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, cfg["GOOGLE_CALENDAR_SCOPES"])

    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                cfg["GOOGLE_CREDENTIALS_PATH"],
                cfg["GOOGLE_CALENDAR_SCOPES"]
            )
            creds = flow.run_local_server(port=0)  # opens browser for authentication

        # Save the credentials for next run
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    return service


def test_auth():
    service = authenticate()
    calendars = service.calendarList().list().execute()
    print("Available calendars:")
    for cal in calendars.get("items", []):
        print(f' - {cal["summary"]} (id: {cal["id"]})')

def list_calendars(service):
    """
    Returns a list of (calendar_id, calendar_name) for all calendars the user has access to.
    """
    calendar_list = service.calendarList().list().execute()
    return [(cal['id'], cal['summary']) for cal in calendar_list.get('items', [])]


def get_busy_events(service, calendar_id="primary", days_ahead=7):
    """
    Fetch upcoming events from Google Calendar as a list of (start, end) datetime tuples
    """
    now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    future = (datetime.utcnow() + timedelta(days=days_ahead)).replace(microsecond=0).isoformat() + "Z"
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        timeMax=future,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = []
    for event in events_result.get('items', []):
        start_str = event['start'].get('dateTime', event['start'].get('date'))
        end_str = event['end'].get('dateTime', event['end'].get('date'))

        def _parse_to_local_naive(iso_str: str):
            if not iso_str:
                return None

            # If it's a date (YYYY-MM-DD) -> treat as local midnight
            if "T" not in iso_str:
                try:
                    d = datetime.fromisoformat(iso_str)
                    return d
                except Exception:
                    pass

            # Normalize Z to +00:00 so fromisoformat can parse it
            try:
                if iso_str.endswith('Z'):
                    dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromisoformat(iso_str)
            except Exception:
                # Fallback: try removing fractional seconds or timezone noise
                try:
                    base = iso_str.split('+')[0].split('Z')[0]
                    dt = datetime.fromisoformat(base)
                except Exception:
                    return None

            # Convert to local timezone and drop tzinfo to produce naive local datetime
            try:
                local_dt = dt.astimezone().replace(tzinfo=None)
            except Exception:
                # If astimezone fails (dt naive), just strip tzinfo
                local_dt = dt.replace(tzinfo=None)
            return local_dt

        start_dt = _parse_to_local_naive(start_str)
        end_dt = _parse_to_local_naive(end_str)

        if start_dt and end_dt:
            summary = event.get('summary', 'Unnamed event')
            events.append((start_dt, end_dt, summary))


    return events

def get_all_busy_events(service, days_ahead=7):
    """
    Fetch all events from all calendars the user has access to.
    Returns a list of (start_datetime, end_datetime) tuples.
    """
    all_events = []
    calendars = list_calendars(service)
    for calendar_id, name in calendars:
        events = get_busy_events(service, calendar_id, days_ahead)
        all_events.extend(events)
    return all_events


def find_free_time(service, days_ahead=7, min_duration_minutes=120):
    """
    Return list of free slots in the next `days_ahead` days across all calendars.
    """
    busy_events = get_all_busy_events(service, days_ahead)
    start = datetime.now()
    end = start + timedelta(days=days_ahead)

    free_slots = find_free_slots(busy_events, start, end, min_duration_minutes)
    return free_slots

def get_user_events(username: str, days_ahead: int = 7):
    """
    Return a summary of the user's upcoming calendar events.
    """
    tokens_folder = os.getenv("GOOGLE_TOKENS_FOLDER", "./tokens")
    token_filename = f"{username}.json"  # or whatever naming convention you use

    token_path = os.path.join(tokens_folder, token_filename)
    if not os.path.exists(token_path):
        raise FileNotFoundError(f"No token found for {username} in {tokens_folder}")

    service = authenticate(token_filename=token_filename)
    busy_events = get_all_busy_events(service, days_ahead=days_ahead)

    # Optionally convert events to a readable dict list
    event_list = [
        {"start": s.isoformat(), "end": e.isoformat(), "title": t}
        for s, e, t in busy_events
    ]
    return event_list
