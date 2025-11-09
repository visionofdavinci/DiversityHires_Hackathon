"""
Helper script to generate GOOGLE_OAUTH_CREDENTIALS environment variable for Railway deployment.

This script reads your local credentials.json file and outputs the properly formatted
environment variable value that you can copy/paste into Railway.
"""

import json
import os

def generate_oauth_env_variable():
    # Read credentials.json
    credentials_path = 'credentials.json'
    
    if not os.path.exists(credentials_path):
        print(f"❌ Error: {credentials_path} not found in current directory")
        print("Please make sure you're running this script from the project root")
        return
    
    try:
        with open(credentials_path, 'r') as f:
            credentials = json.load(f)
        
        # Update redirect_uris to include Railway URL
        railway_url = "https://diversityhireshackathon-production-4ad4.up.railway.app"
        
        if 'web' in credentials:
            credentials['web']['redirect_uris'] = [
                f"{railway_url}/calendar/oauth2callback",
                "http://localhost:5000/calendar/oauth2callback"  # Keep localhost for local dev
            ]
        elif 'installed' in credentials:
            # Convert installed to web type
            print("⚠️  Warning: Your credentials.json appears to be for 'installed' app type.")
            print("   For web deployment, you should create OAuth credentials for 'Web application' type.")
            return
        
        # Convert to single-line JSON string
        env_value = json.dumps(credentials, separators=(',', ':'))
        
        print("=" * 80)
        print("✅ SUCCESS! Copy the environment variable below:")
        print("=" * 80)
        print()
        print("GOOGLE_OAUTH_CREDENTIALS=" + env_value)
        print()
        print("=" * 80)
        print("📋 Instructions:")
        print("=" * 80)
        print("1. Copy the entire line above (including GOOGLE_OAUTH_CREDENTIALS=)")
        print("2. Go to Railway Dashboard → Your Project → Variables")
        print("3. Click 'New Variable'")
        print("4. Paste the line and Railway will split it into name=value")
        print("5. Click 'Add'")
        print()
        print("⚠️  IMPORTANT: Also update Google Cloud Console")
        print("=" * 80)
        print(f"Add this redirect URI to your OAuth client in Google Cloud Console:")
        print(f"   {railway_url}/calendar/oauth2callback")
        print()
        print("Steps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Select your project")
        print("3. Go to APIs & Services → Credentials")
        print("4. Click on your OAuth 2.0 Client ID")
        print("5. Under 'Authorized redirect URIs', add the URL above")
        print("6. Click Save")
        print()
        
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {credentials_path}")
        print(f"   {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    generate_oauth_env_variable()
