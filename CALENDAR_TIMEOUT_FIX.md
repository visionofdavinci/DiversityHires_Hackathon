# Calendar Authentication Timeout Fix

## Problem
The calendar function was experiencing timeout errors when trying to authenticate with Google's OAuth2 servers:
```
Authentication error: HTTPSConnectionPool(host='oauth2.googleapis.com', port=443): Read timed out. (read timeout=None)
```

## Root Cause
The Google authentication libraries (`google-auth` and `google-api-python-client`) don't set HTTP timeouts by default, which can cause indefinite hangs when:
1. Refreshing expired OAuth tokens
2. Making API calls to Google Calendar
3. Network issues occur

## Solution Implemented

### 1. Custom Timeout Request Class (`calendar_agent.py`)
Created a `TimeoutHTTPRequest` class that wraps the standard Google Auth request with configurable timeouts:

```python
class TimeoutHTTPRequest(google.auth.transport.requests.Request):
    """Custom Request class with timeout to prevent hanging on OAuth requests."""
    def __init__(self, timeout=10):
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter()
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        super().__init__(session)
        self.timeout = timeout
    
    def __call__(self, url, method='GET', body=None, headers=None, **kwargs):
        kwargs['timeout'] = kwargs.get('timeout', self.timeout)
        return super().__call__(url, method=method, body=body, headers=headers, **kwargs)
```

### 2. Calendar Service Builder with Timeout
Added `build_calendar_service()` helper that creates Google Calendar service with timeout-protected HTTP client:

```python
def build_calendar_service(credentials, timeout=30):
    """Build a Google Calendar service with timeout configuration."""
    http = credentials.authorize(
        TimeoutHTTPRequest(timeout=timeout).session
    )
    service = build("calendar", "v3", credentials=credentials, http=http)
    return service
```

### 3. Updated All Authentication Functions
Modified these functions to use the timeout-protected requests:
- `authenticate()` - Main OAuth flow (10s timeout for token refresh, 30s for API calls)
- `get_calendar_service()` - Service with token refresh (10s timeout)
- `get_calendar_service_simple()` - Simplified service (10s timeout)

### 4. New API Endpoint (`app.py`)
Added `/api/calendar` endpoint that the frontend was calling:

```python
@app.route("/api/calendar", methods=["GET"])
def api_calendar():
    """Get calendar events for all authenticated users."""
    # Fetches events from all users with tokens
    # Returns formatted events for frontend display
```

### 5. Frontend Timeout Protection (`frontend/src/app/api/calendar/route.ts`)
Added 15-second timeout to the frontend API call:

```typescript
const controller = new AbortController()
const timeoutId = setTimeout(() => controller.abort(), 15000)

const response = await fetch('http://localhost:5000/api/calendar', {
  signal: controller.signal,
})
```

## Timeout Configuration

| Component | Operation | Timeout |
|-----------|-----------|---------|
| Token Refresh | OAuth2 token refresh | 10 seconds |
| Calendar API | Google Calendar API calls | 30 seconds |
| Frontend | Next.js → Flask API | 15 seconds |

## Testing

Run the test script to verify the fix:

```bash
python test_calendar_fix.py
```

This will:
1. Check for existing user tokens
2. Test authentication for each user with timeout protection
3. Fetch calendar events to verify full functionality
4. Display any errors with proper timeout handling

## How to Use

### For Existing Users
If you already have token files in the `tokens/` folder, they should now work with the timeout protection. Just restart your Flask server.

### For New Users
1. Start Flask server: `python app.py`
2. Call `/calendar/auth/start` with username to get OAuth URL
3. User visits URL and grants calendar access
4. Google redirects to `/calendar/oauth2callback`
5. Token is saved with timeout protection

### API Usage
```python
from src.calendar_agent import get_calendar_service_simple, get_all_busy_events

# Get service (will auto-refresh token with timeout protection)
service = get_calendar_service_simple("username")

# Fetch events (protected by timeout)
events = get_all_busy_events(service, days_ahead=7)
```

## Error Handling

The fix includes proper error messages for common scenarios:

1. **Timeout during token refresh**: "Token refresh failed for user {username}. Please re-authenticate."
2. **No token file**: "No token file found for {username}. Please authenticate first."
3. **Network timeout**: Fails gracefully after timeout period instead of hanging indefinitely

## Files Modified

1. `src/calendar_agent.py` - Added timeout classes and updated all auth functions
2. `app.py` - Added `/api/calendar` endpoint with timeout handling
3. `frontend/src/app/api/calendar/route.ts` - Added frontend timeout
4. `test_calendar_fix.py` - New test script to verify fixes

## Benefits

✅ No more indefinite hangs on authentication
✅ Predictable failure behavior with clear error messages
✅ Automatic token refresh with timeout protection
✅ Frontend protected from backend timeouts
✅ Works with existing token files
✅ Backward compatible with existing calendar agent usage

## Next Steps

If you still see timeout issues:
1. Check your internet connection
2. Verify Google API credentials are valid
3. Check if tokens have been revoked (re-authenticate)
4. Increase timeout values if needed for slow connections
