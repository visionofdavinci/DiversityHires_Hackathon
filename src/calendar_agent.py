# src/calendar_agent.py
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from googleapiclient.discovery import build
from src.utils.config_loader import get_config
from src.utils.time_utils import find_free_slots
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
import google.auth.transport.requests
import requests
import json


# Google Calendar OAuth scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


class TimeoutHTTPRequest(google.auth.transport.requests.Request):
    """Custom Request class with timeout to prevent hanging on OAuth requests."""
    def __init__(self, timeout=10):
        """
        Args:
            timeout: Timeout in seconds for HTTP requests (default: 10)
        """
        session = requests.Session()
        # Configure session with timeout
        adapter = requests.adapters.HTTPAdapter()
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        super().__init__(session)
        self.timeout = timeout
    
    def __call__(self, url, method='GET', body=None, headers=None, **kwargs):
        """Override to add timeout to all requests."""
        kwargs['timeout'] = kwargs.get('timeout', self.timeout)
        return super().__call__(url, method=method, body=body, headers=headers, **kwargs)


def build_calendar_service(credentials, timeout=30):
    """
    Build a Google Calendar service with timeout configuration.
    
    Args:
        credentials: Google OAuth credentials
        timeout: HTTP timeout in seconds for API calls (default: 30)
    
    Returns:
        Google Calendar service object
    """
    # Build service directly with credentials
    # The timeout protection is handled at the credentials refresh level
    service = build("calendar", "v3", credentials=credentials)
    return service


def get_oauth_flow(redirect_uri='http://localhost:5000/calendar/oauth2callback'):
    """
    Create and return a Flow instance for OAuth2 authentication.
    This will be used to generate the authorization URL.
    """
    try:
        cfg = get_config()
        credentials_path = cfg.get("GOOGLE_CREDENTIALS_PATH")
        
        if not credentials_path or not os.path.exists(credentials_path):
            # Try default locations
            default_paths = ['./credentials.json', '../credentials.json', 'credentials.json']
            for path in default_paths:
                if os.path.exists(path):
                    credentials_path = path
                    break
            
            if not credentials_path or not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    "Google OAuth credentials file not found. "
                    "Please download it from Google Cloud Console and save as 'credentials.json' in project root"
                )
        
        # Create flow without scope validation to accept whatever Google grants
        from google_auth_oauthlib.flow import Flow
        flow = Flow.from_client_secrets_file(
            credentials_path,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
        # Disable strict scope checking
        flow.oauth2session.scope = SCOPES
        
        return flow
    except Exception as e:
        print(f"Error creating OAuth flow: {e}")
        raise


def get_authorization_url():
    """
    Generate the Google OAuth authorization URL that users should visit.
    Returns: (authorization_url, state)
    """
    flow = get_oauth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force consent screen to get refresh token
    )
    return authorization_url, state


def exchange_code_for_tokens(code, state):
    """
    Exchange the authorization code for access and refresh tokens.
    Returns: credentials object
    
    Note: Google may grant additional scopes beyond what we requested.
    We accept whatever scopes Google grants us.
    """
    flow = get_oauth_flow()
    
    # Bypass scope validation by setting oauth2session scope to None
    # This prevents the "Scope has changed" error
    original_scope = flow.oauth2session.scope
    flow.oauth2session.scope = None
    
    try:
        flow.fetch_token(code=code)
        return flow.credentials
    except Warning as w:
        # OAuth library can raise Warning as exception - ignore scope changes
        if 'Scope has changed' in str(w):
            print("[OAuth] Note: Google granted additional scopes, continuing anyway")
            # Try to return credentials if they were fetched
            if hasattr(flow, 'credentials') and flow.credentials:
                return flow.credentials
        raise
    finally:
        # Restore original scope (cleanup)
        flow.oauth2session.scope = original_scope


def save_credentials(credentials, username):
    """
    Save user credentials to a JSON file.
    """
    tokens_folder = os.getenv("GOOGLE_TOKENS_FOLDER", "./tokens")
    os.makedirs(tokens_folder, exist_ok=True)
    
    token_path = os.path.join(tokens_folder, f"{username}.json")
    
    # Convert credentials to dict and save
    creds_data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    with open(token_path, 'w') as token_file:
        json.dump(creds_data, token_file)
    
    return token_path


def load_credentials(username):
    """
    Load credentials from saved token file.
    """
    tokens_folder = os.getenv("GOOGLE_TOKENS_FOLDER", "./tokens")
    token_path = os.path.join(tokens_folder, f"{username}.json")
    
    if not os.path.exists(token_path):
        return None
    
    with open(token_path, 'r') as token_file:
        creds_data = json.load(token_file)
    
    credentials = Credentials(
        token=creds_data.get('token'),
        refresh_token=creds_data.get('refresh_token'),
        token_uri=creds_data.get('token_uri'),
        client_id=creds_data.get('client_id'),
        client_secret=creds_data.get('client_secret'),
        scopes=creds_data.get('scopes')
    )
    
    return credentials


def authenticate(token_filename: str = None):
    """
    Authenticate a Google Calendar user using a specific token file.
    If no token_filename is provided, fallback to default from config.
    """
    cfg = get_config()
    tokens_folder = os.getenv("GOOGLE_TOKENS_FOLDER", "./tokens")
    os.makedirs(tokens_folder, exist_ok=True)

    # Determine which token file to use
    token_path = os.path.join(tokens_folder, token_filename) if token_filename else cfg["GOOGLE_TOKEN_PATH"]

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Use custom Request with timeout to prevent hanging
            request = TimeoutHTTPRequest(timeout=10)
            creds.refresh(request)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                cfg["GOOGLE_CREDENTIALS_PATH"],
                SCOPES
            )
            creds = flow.run_local_server(port=0)  # opens browser for authentication

        # Save the credentials for next run
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    service = build_calendar_service(creds, timeout=30)
    return service


def get_calendar_service(username):
    """
    Get authenticated Google Calendar service for a user.
    Refreshes tokens if needed.
    """
    credentials = load_credentials(username)
    
    if not credentials:
        raise ValueError(f"No credentials found for user {username}. Please authenticate first.")
    
    # Refresh token if expired
    if credentials.expired and credentials.refresh_token:
        try:
            # Use custom Request with timeout to prevent hanging
            request = TimeoutHTTPRequest(timeout=10)
            credentials.refresh(request)
            save_credentials(credentials, username)
        except Exception as e:
            print(f"Error refreshing token: {e}")
            raise ValueError(f"Token refresh failed for user {username}. Please re-authenticate.")
    
    service = build_calendar_service(credentials, timeout=30)
    return service


def get_calendar_service_simple(username):
    """
    Simplified version that works with pre-existing token files.
    This is useful when you already have valid tokens and don't need OAuth flow.
    """
    tokens_folder = os.getenv("GOOGLE_TOKENS_FOLDER", "./tokens")
    token_path = os.path.join(tokens_folder, f"{username}.json")
    
    if not os.path.exists(token_path):
        raise ValueError(f"No token file found for {username}. Please authenticate first.")
    
    # Load credentials from file
    credentials = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # Refresh if expired
    if credentials.expired and credentials.refresh_token:
        try:
            # Use custom Request with timeout to prevent hanging
            request = TimeoutHTTPRequest(timeout=10)
            credentials.refresh(request)
            # Save refreshed credentials
            with open(token_path, 'w') as token_file:
                token_file.write(credentials.to_json())
        except Exception as e:
            print(f"Error refreshing token: {e}")
            raise ValueError(f"Token refresh failed. Token may be invalid or revoked.")
    
    service = build_calendar_service(credentials, timeout=30)
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
    service = get_calendar_service(username)
    busy_events = get_all_busy_events(service, days_ahead=days_ahead)

    # Optionally convert events to a readable dict list
    event_list = [
        {"start": s.isoformat(), "end": e.isoformat(), "title": t}
        for s, e, t in busy_events
    ]
    return event_list


def get_events_for_user(service, username, days_ahead=14):
    """
    Get formatted events for a user using an existing service object.
    Returns list of event dictionaries.
    """
    busy_events = get_all_busy_events(service, days_ahead=days_ahead)
    
    # Convert to the expected format with proper datetime handling
    event_list = []
    for start_dt, end_dt, title in busy_events:
        event_list.append({
            'summary': title,
            'start': {'dateTime': start_dt.isoformat()},
            'end': {'dateTime': end_dt.isoformat()}
        })
    
    return event_list
