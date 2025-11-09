"""
Simple test script to verify calendar authentication with timeout fixes.
"""
import os
from src.calendar_agent import get_calendar_service_simple, get_all_busy_events

def test_calendar_with_timeout():
    """Test calendar access with timeout protection."""
    
    # Check for existing tokens
    tokens_folder = os.getenv("GOOGLE_TOKENS_FOLDER", "./tokens")
    
    if not os.path.exists(tokens_folder):
        print(f"❌ No tokens folder found at {tokens_folder}")
        print("Please authenticate users first using the OAuth flow.")
        return
    
    user_tokens = [f.replace('.json', '') for f in os.listdir(tokens_folder) if f.endswith(".json")]
    
    if not user_tokens:
        print(f"❌ No user tokens found in {tokens_folder}")
        print("Please authenticate users first using the OAuth flow.")
        return
    
    print(f"✓ Found {len(user_tokens)} user token(s): {', '.join(user_tokens)}")
    print()
    
    # Test each user
    for username in user_tokens:
        print(f"Testing calendar access for user: {username}")
        try:
            # This will use the timeout-protected request
            service = get_calendar_service_simple(username)
            print(f"  ✓ Successfully authenticated {username}")
            
            # Try to fetch events
            events = get_all_busy_events(service, days_ahead=7)
            print(f"  ✓ Retrieved {len(events)} event(s)")
            
            if events:
                print(f"  First few events:")
                for start, end, title in events[:3]:
                    print(f"    - {title}: {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%H:%M')}")
            
        except ValueError as e:
            print(f"  ❌ Authentication error: {e}")
        except Exception as e:
            print(f"  ❌ Error: {type(e).__name__}: {e}")
        
        print()

if __name__ == "__main__":
    print("=" * 60)
    print("Calendar Authentication Test (with timeout fix)")
    print("=" * 60)
    print()
    
    test_calendar_with_timeout()
    
    print()
    print("Test complete!")
