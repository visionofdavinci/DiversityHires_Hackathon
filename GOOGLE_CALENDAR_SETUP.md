# Google Calendar OAuth Setup Guide

This guide will help you set up Google Calendar OAuth authentication so users can connect their personal Google Calendars.

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Name it something like "Movie Matcher" or "DiversityHires Calendar"

## Step 2: Enable Google Calendar API

1. In your Google Cloud project, go to **APIs & Services** → **Library**
2. Search for "Google Calendar API"
3. Click on it and press **Enable**

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** (unless you have a Google Workspace)
3. Fill in the required information:
   - **App name**: Movie Matcher (or your app name)
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Click **Save and Continue**
5. On the **Scopes** page, click **Add or Remove Scopes**
6. Add the following scope:
   - `https://www.googleapis.com/auth/calendar.readonly`
7. Click **Save and Continue**
8. On **Test users**, add the email addresses of people who will test the app (including yourself)
9. Click **Save and Continue**

## Step 4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Choose **Web application**
4. Configure:
   - **Name**: Movie Matcher Web Client
   - **Authorized JavaScript origins**: 
     - `http://localhost:5000`
     - `http://localhost:3000`
   - **Authorized redirect URIs**:
     - `http://localhost:5000/calendar/oauth2callback`
5. Click **Create**
6. Download the JSON file (click the download icon)
7. Rename it to `credentials.json` and place it in your project root

## Step 5: Configure Environment Variables

Create or update your `.env` file in the project root:

```env
GOOGLE_CREDENTIALS_PATH=./credentials.json
GOOGLE_TOKENS_FOLDER=./tokens
GOOGLE_CALENDAR_SCOPES=https://www.googleapis.com/auth/calendar.readonly
```

## Step 6: Create Tokens Folder

```bash
mkdir tokens
```

This folder will store user authentication tokens after they complete the OAuth flow.

## How It Works

### OAuth Flow:

1. **User enters username** → Frontend sends username to backend
2. **Backend generates OAuth URL** → Returns Google authorization URL
3. **User visits Google** → Grants calendar permissions
4. **Google redirects back** → Backend receives authorization code
5. **Backend exchanges code for tokens** → Saves tokens to `tokens/{username}.json`
6. **Frontend shows calendar** → Uses stored tokens to fetch events

### API Endpoints:

- `POST /calendar/auth/start` - Start OAuth flow (get authorization URL)
- `GET /calendar/oauth2callback` - OAuth callback (Google redirects here)
- `GET /calendar/{username}/events` - Get calendar events for authenticated user
- `GET /calendar/{username}/check-auth` - Check if user is already authenticated

## Testing the Flow

1. Start your Flask backend:
   ```bash
   python app.py
   ```

2. Start your Next.js frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Navigate to `http://localhost:3000/calendar`

4. Enter a username (e.g., "sanne", "noor", "ioana")

5. You'll be redirected to Google to grant permissions

6. After granting access, you'll be redirected back and see your calendar events

## Troubleshooting

### "Error 400: redirect_uri_mismatch"
- Make sure `http://localhost:5000/calendar/oauth2callback` is added to your OAuth client's authorized redirect URIs in Google Cloud Console

### "Access blocked: This app's request is invalid"
- Ensure you've added test users in the OAuth consent screen
- Check that the Google Calendar API is enabled

### "credentials.json not found"
- Make sure you downloaded the OAuth client JSON from Google Cloud Console
- Place it in the project root and name it `credentials.json`
- Update `GOOGLE_CREDENTIALS_PATH` in `.env` if you placed it elsewhere

### "No credentials found for user"
- User needs to complete the OAuth flow first
- Delete the token file and re-authenticate: `rm tokens/{username}.json`

## Security Notes

- **Never commit** `credentials.json` or `tokens/*.json` to version control
- Add to `.gitignore`:
  ```
  credentials.json
  tokens/*.json
  .env
  ```
- In production, use HTTPS and proper session management
- Store tokens securely (consider encryption)
- Use a proper secret key for Flask sessions (not `os.urandom(24)`)

## Production Deployment

For production:
1. Update redirect URIs to your production domain
2. Publish the OAuth consent screen (move from Testing to Production)
3. Use environment variables for all secrets
4. Implement proper token encryption
5. Add token refresh logic for expired access tokens (already implemented)
