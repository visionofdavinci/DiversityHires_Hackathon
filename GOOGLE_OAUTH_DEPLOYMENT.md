# 🔐 Google Calendar OAuth Setup for Deployment

## Problem Solved
The error "Google OAuth credentials file not found" occurs because Railway can't access your local `credentials.json` file. This guide shows you how to configure OAuth credentials as environment variables for deployment.

---

## ✅ Solution: Environment Variables

Instead of uploading the credentials file, we'll store it as an environment variable on Railway.

### Step 1: Prepare Your Credentials JSON

Your `credentials.json` file should look like this:

```json
{
  "web": {
    "client_id": "YOUR-CLIENT-ID.apps.googleusercontent.com",
    "project_id": "your-project",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR-CLIENT-SECRET",
    "redirect_uris": ["http://localhost:5000/calendar/oauth2callback"]
  }
}
```

### Step 2: Update Google Cloud Console

**IMPORTANT:** You need to add your Railway URL to the authorized redirect URIs:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **APIs & Services** → **Credentials**
4. Click on your OAuth 2.0 Client ID
5. Under **Authorized redirect URIs**, add:
   ```
   https://diversityhireshackathon-production-4ad4.up.railway.app/calendar/oauth2callback
   ```
6. Click **Save**

### Step 3: Set Environment Variables on Railway

Go to **Railway** → Your Project → **Variables** and add:

#### Required for Google Calendar OAuth:

```env
GOOGLE_OAUTH_CREDENTIALS={"web":{"client_id":"YOUR-CLIENT-ID.apps.googleusercontent.com","project_id":"your-project","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"YOUR-CLIENT-SECRET","redirect_uris":["https://diversityhireshackathon-production-4ad4.up.railway.app/calendar/oauth2callback"]}}
```

**Note:** 
- This is a single-line JSON string (no newlines or formatting)
- Replace `YOUR-CLIENT-ID` and `YOUR-CLIENT-SECRET` with your actual credentials
- Get these from your local `credentials.json` file

#### Backend URL (for dynamic OAuth redirects):

```env
BACKEND_URL=https://diversityhireshackathon-production-4ad4.up.railway.app
```

---

## 📋 Complete Railway Environment Variables

Here's your complete list of environment variables for Railway:

```env
# Flask Configuration
FLASK_ENV=production
FLASK_SECRET_KEY=your-secret-key-minimum-20-characters
PORT=5000

# AI Service
GEMINI_API_KEY=your-google-gemini-api-key

# CORS (Frontend URL)
FRONTEND_URL=https://diversity-hires-hackathon-3x1r.vercel.app

# Backend URL (for OAuth redirects)
BACKEND_URL=https://diversityhireshackathon-production-4ad4.up.railway.app

# Google Calendar OAuth (single line, no spaces or newlines)
# Replace YOUR-CLIENT-ID and YOUR-CLIENT-SECRET with your actual values from credentials.json
GOOGLE_OAUTH_CREDENTIALS={"web":{"client_id":"YOUR-CLIENT-ID.apps.googleusercontent.com","project_id":"your-project","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"YOUR-CLIENT-SECRET","redirect_uris":["https://diversityhireshackathon-production-4ad4.up.railway.app/calendar/oauth2callback"]}}

# Google Calendar Storage (optional)
GOOGLE_CREDENTIALS_PATH=/app/credentials.json
GOOGLE_TOKENS_FOLDER=/app/tokens
```

**⚠️ Important:** Copy your actual `client_id` and `client_secret` from your local `credentials.json` file!

---

## 🧪 How It Works

1. **Local Development:**
   - Uses `credentials.json` file from your project directory
   - OAuth redirects to `http://localhost:5000/calendar/oauth2callback`

2. **Production (Railway):**
   - Uses `GOOGLE_OAUTH_CREDENTIALS` environment variable
   - Uses `BACKEND_URL` environment variable for dynamic redirect URI
   - OAuth redirects to `https://your-railway-app.railway.app/calendar/oauth2callback`

---

## 🔍 Testing

### Test OAuth Flow on Production:

1. Deploy to Railway with all environment variables set
2. Visit your Vercel app: `https://diversity-hires-hackathon-3x1r.vercel.app`
3. Go to **Calendar** page
4. Enter a username (e.g., "ioana")
5. Click **Connect Google Calendar**
6. Should redirect to Google OAuth consent screen
7. After authorization, should redirect back to your app

### Check Railway Logs:

Look for these messages in Railway logs:
```
[OAuth] Using credentials from environment variable
[OAuth] Using redirect URI: https://diversityhireshackathon-production-4ad4.up.railway.app/calendar/oauth2callback
[OAuth] Callback received - state: xxx, code: present
[OAuth] Success! Redirecting to frontend
```

---

## ⚠️ Important Notes

### Security:
- ✅ Never commit `credentials.json` to git (already in `.gitignore`)
- ✅ Use environment variables for production
- ✅ Keep `client_secret` secure

### Google Cloud Console:
- ✅ Add Railway redirect URI to authorized list
- ✅ Keep the same credentials in both local file and env variable
- ⚠️ If you change credentials in Google Console, update both local file AND Railway env var

### OAuth Callback:
- ✅ The redirect URI in `GOOGLE_OAUTH_CREDENTIALS` must match your Railway URL
- ✅ The redirect URI in Google Cloud Console must match exactly
- ⚠️ No trailing slashes!

---

## 🆘 Troubleshooting

### Error: "redirect_uri_mismatch"
**Cause:** The redirect URI doesn't match what's registered in Google Cloud Console

**Fix:**
1. Check Railway logs for the redirect URI being used
2. Go to Google Cloud Console and add that exact URI
3. Make sure there are no trailing slashes
4. Wait a few minutes for changes to propagate

### Error: "Google OAuth credentials not found"
**Cause:** `GOOGLE_OAUTH_CREDENTIALS` environment variable not set or invalid JSON

**Fix:**
1. Check Railway variables - make sure `GOOGLE_OAUTH_CREDENTIALS` exists
2. Verify it's valid JSON (use a JSON validator)
3. Make sure it's on a single line with no newlines

### Error: "invalid_client"
**Cause:** Client ID or secret is incorrect

**Fix:**
1. Double-check credentials in Google Cloud Console
2. Update both local `credentials.json` and Railway env variable
3. Redeploy Railway

---

## 📚 Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Railway Environment Variables](https://docs.railway.app/develop/variables)
- [Google Calendar API Setup](./GOOGLE_CALENDAR_SETUP.md)

---

**Status:** ✅ OAuth configured for both local and production deployment!
