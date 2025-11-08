# src/calendar_agent.py
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from src.utils.config_loader import get_config
from src.utils.time_utils import find_free_slots
from datetime import datetime, timedelta
from google.auth.transport.requests import Request




def authenticate():
    config = get_config()
    creds = None

    # Load existing token if it exists
    if os.path.exists(config["GOOGLE_TOKEN_PATH"]):
        creds = Credentials.from_authorized_user_file(
            config["GOOGLE_TOKEN_PATH"], config["GOOGLE_CALENDAR_SCOPES"]
        )

    # If no valid creds, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config["GOOGLE_CREDENTIALS_PATH"],
                config["GOOGLE_CALENDAR_SCOPES"]
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for next run
        with open(config["GOOGLE_TOKEN_PATH"], "w") as token_file:
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

        start_dt = datetime.fromisoformat(start_str.split("+")[0])
        end_dt = datetime.fromisoformat(end_str.split("+")[0])

        events.append((start_dt, end_dt))

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


def find_free_time(service, days_ahead=7, min_duration_minutes=30):
    """
    Return list of free slots in the next `days_ahead` days across all calendars.
    """
    busy_events = get_all_busy_events(service, days_ahead)
    start = datetime.now()
    end = start + timedelta(days=days_ahead)

    free_slots = find_free_slots(busy_events, start, end, min_duration_minutes)
    return free_slots
