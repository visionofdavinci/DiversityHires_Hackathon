# Railway Deployment Guide

This guide will help you deploy your Movie Matcher application to Railway.

## Prerequisites

1. A [Railway](https://railway.com/) account (sign up with GitHub)
2. Your code pushed to a GitHub repository
3. Google Calendar API credentials (credentials.json)
4. Required API keys (OpenAI, TMDb, etc.)

## Architecture

Your app has two parts that need to be deployed:
1. **Backend (Flask API)** - Python Flask server
2. **Frontend (Next.js)** - React/Next.js web app

## Part 1: Deploy Backend to Railway

### Step 1: Create a New Railway Project

1. Go to [Railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Select your `DiversityHires_Hackathon` repository
5. Railway will detect the Dockerfile automatically

### Step 2: Configure Environment Variables

In your Railway project dashboard:

1. Click on your service
2. Go to "Variables" tab
3. Add the following environment variables:

```bash
# Required
FLASK_SECRET_KEY=your-secure-random-string-here
FLASK_ENV=production
PORT=5000

# Google Calendar (Important!)
GOOGLE_CREDENTIALS_PATH=/app/credentials.json
GOOGLE_TOKENS_FOLDER=/app/tokens

# Frontend URL (update after deploying frontend)
FRONTEND_URL=https://your-frontend.vercel.app

# Optional - AI Features
OPENAI_API_KEY=your-openai-api-key

# Optional - TMDb (for movie metadata)
TMDB_API_KEY=your-tmdb-api-key
```

### Step 3: Upload Google Credentials

Since `credentials.json` is in `.gitignore`, you need to add it manually:

**Option A: Use Railway CLI**
```bash
railway login
railway link
railway variables set GOOGLE_CREDENTIALS=$(cat credentials.json)
```

**Option B: Base64 encode and set as env var**
1. In PowerShell:
   ```powershell
   $credentials = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes("credentials.json"))
   echo $credentials
   ```
2. Add to Railway as `GOOGLE_CREDENTIALS_BASE64`
3. Modify Dockerfile to decode it on startup

**Option C: Use Railway Volumes (Recommended)**
1. In Railway dashboard, go to your service
2. Click "Settings" → "Volumes"
3. Mount a volume at `/app/tokens` for persistent storage
4. Manually upload credentials.json via Railway CLI

### Step 4: Deploy

1. Railway will automatically deploy when you push to GitHub
2. Wait for build to complete (check "Deployments" tab)
3. Once deployed, click "Generate Domain" to get your backend URL
4. Your backend will be available at: `https://your-app.up.railway.app`

### Step 5: Test Backend

Test your deployed backend:
```bash
curl https://your-app.up.railway.app/cineville/upcoming
```

## Part 2: Deploy Frontend to Vercel (Recommended)

Next.js works best on Vercel, but you can also deploy to Railway.

### Option A: Deploy Frontend to Vercel

1. Go to [Vercel.com](https://vercel.com)
2. Sign in with GitHub
3. Click "Add New" → "Project"
4. Import your `DiversityHires_Hackathon` repository
5. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

6. Add Environment Variables:
   ```bash
   NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
   OPENAI_API_KEY=your-openai-api-key
   HUGGINGFACE_API_KEY=your-huggingface-api-key
   ```

7. Click "Deploy"
8. Copy your Vercel URL (e.g., `https://your-app.vercel.app`)

9. **Update Backend CORS**: Go back to Railway and update `FRONTEND_URL` to your Vercel URL

### Option B: Deploy Frontend to Railway

1. In Railway, click "New Service"
2. Select "Deploy from GitHub repo"
3. Choose the same repository
4. Configure:
   - **Root Directory**: `/frontend`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`

5. Add Environment Variable:
   ```bash
   NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
   ```

6. Generate domain for frontend

## Part 3: Configure OAuth Redirect URIs

Since your Google Calendar OAuth uses redirects, you need to update Google Cloud Console:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to "APIs & Services" → "Credentials"
4. Edit your OAuth 2.0 Client ID
5. Add Authorized Redirect URIs:
   ```
   https://your-backend.up.railway.app/calendar/oauth2callback
   https://your-backend.up.railway.app/calendar/auth/start
   ```
6. Save changes

## Part 4: Update Calendar Agent

You may need to update the OAuth redirect URI in your code:

```python
# In src/calendar_agent.py
def get_oauth_flow(redirect_uri=None):
    if not redirect_uri:
        # Use environment variable or default
        redirect_uri = os.getenv('OAUTH_REDIRECT_URI', 
                                 'http://localhost:5000/calendar/oauth2callback')
    # ... rest of code
```

Then add to Railway environment variables:
```bash
OAUTH_REDIRECT_URI=https://your-backend.up.railway.app/calendar/oauth2callback
```

## Troubleshooting

### Build Fails
- Check Railway build logs
- Ensure all dependencies are in `requirements.txt`
- Verify Dockerfile syntax

### Calendar Authentication Fails
- Verify Google credentials are uploaded correctly
- Check OAuth redirect URIs in Google Cloud Console
- Ensure CORS is configured for your frontend URL

### Frontend Can't Connect to Backend
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check backend CORS settings include frontend URL
- Test backend endpoint directly

### Port Issues
- Railway automatically sets `PORT` environment variable
- Your app should use `os.getenv("PORT", 5000)`
- Gunicorn uses `${PORT:-5000}` syntax

## Monitoring & Logs

- **Railway Logs**: Click on your service → "Logs" tab
- **Metrics**: "Metrics" tab shows CPU, Memory, Network usage
- **Alerts**: Set up in "Settings" → "Alerts"

## Cost Optimization

Railway offers:
- **$5 free credits/month** for hobby plan
- **Pay-as-you-go** after free credits
- **Sleep mode** for inactive services (frontend won't sleep on Vercel)

Tips:
- Use Vercel for frontend (free tier is generous)
- Railway for backend only
- Keep tokens in persistent volume to avoid re-authentication

## Environment Variables Checklist

### Backend (Railway)
- [x] `FLASK_SECRET_KEY`
- [x] `FLASK_ENV=production`
- [x] `PORT=5000`
- [x] `GOOGLE_CREDENTIALS_PATH`
- [x] `GOOGLE_TOKENS_FOLDER`
- [x] `FRONTEND_URL`
- [ ] `OPENAI_API_KEY` (optional)
- [ ] `TMDB_API_KEY` (optional)

### Frontend (Vercel)
- [x] `NEXT_PUBLIC_API_URL`
- [ ] `OPENAI_API_KEY` (optional)
- [ ] `HUGGINGFACE_API_KEY` (optional)

## Final Steps

1. ✅ Backend deployed to Railway
2. ✅ Frontend deployed to Vercel
3. ✅ Environment variables configured
4. ✅ Google OAuth redirect URIs updated
5. ✅ Test the live application
6. ✅ Authenticate calendar for each user
7. ✅ Test movie recommendations with calendar integration

## Your Live URLs

- **Frontend**: https://your-app.vercel.app
- **Backend API**: https://your-app.up.railway.app
- **Calendar Auth**: https://your-app.up.railway.app/calendar/auth/start

Congratulations! 🎉 Your Movie Matcher is now live!
