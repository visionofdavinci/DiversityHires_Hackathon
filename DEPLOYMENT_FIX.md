# 🔧 Deployment Fix - Hardcoded URLs Resolved

## Problem Fixed
Three page components were hardcoding `http://localhost:5000` instead of using the environment variable `NEXT_PUBLIC_API_URL`. This caused "Failed to fetch" errors on Vercel.

## Files Fixed
✅ `frontend/src/app/letterboxd/page.tsx`
✅ `frontend/src/app/cineville/page.tsx`
✅ `frontend/src/app/calendar/page.tsx`

All three files now use:
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
```

## Next Steps to Deploy

### 1. Commit and Push Changes
```bash
git add .
git commit -m "Fix: Use environment variable for API URL in all pages"
git push origin main
```

### 2. Verify Vercel Environment Variables
Go to **Vercel Dashboard** → Your Project → **Settings** → **Environment Variables**

Make sure you have:
```
NEXT_PUBLIC_API_URL = https://your-railway-backend.railway.app
```

**Important:** The URL should NOT have a trailing slash.

### 3. Redeploy on Vercel
After pushing to GitHub, Vercel should automatically redeploy. If not:
- Go to Vercel Dashboard → Your Project → **Deployments**
- Click **Redeploy** on the latest deployment

### 4. Verify Railway Environment Variables
Go to **Railway Dashboard** → Your Project → **Variables**

Make sure you have:
```
FLASK_ENV=production
FLASK_SECRET_KEY=your-secret-key-here
PORT=5000
GEMINI_API_KEY=your-gemini-api-key
FRONTEND_URL=https://your-app.vercel.app
GOOGLE_CREDENTIALS_PATH=/app/credentials.json
GOOGLE_TOKENS_FOLDER=/app/tokens
```

**Important:** Update `FRONTEND_URL` with your actual Vercel deployment URL.

### 5. Test the Application

Once both are deployed, test these features:
1. ✅ Chat interface - should get AI responses
2. ✅ Letterboxd page - should load user profiles
3. ✅ Cineville page - should load upcoming movies
4. ✅ Calendar page - should allow OAuth authentication
5. ✅ Movie recommendations - should appear in right panel

## Common Issues & Solutions

### Issue: "Failed to fetch" still appears
**Solution:** 
- Clear browser cache and cookies
- Check that NEXT_PUBLIC_API_URL is set correctly in Vercel
- Verify Railway backend is running (check Railway logs)

### Issue: CORS errors in browser console
**Solution:**
- Make sure `FRONTEND_URL` in Railway matches your Vercel URL exactly
- Check Railway backend logs for CORS-related errors

### Issue: "Could not load recommendations"
**Solution:**
- Check that Letterboxd username exists and is spelled correctly
- Verify Railway backend has all required environment variables
- Check Railway logs for Python errors

## Environment Variable Checklist

### Vercel (Frontend)
- [ ] `NEXT_PUBLIC_API_URL` - Railway backend URL

### Railway (Backend)
- [ ] `FLASK_ENV` - Set to `production`
- [ ] `FLASK_SECRET_KEY` - Random secret string
- [ ] `PORT` - Set to `5000`
- [ ] `GEMINI_API_KEY` - Your Google Gemini API key
- [ ] `FRONTEND_URL` - Your Vercel deployment URL
- [ ] `GOOGLE_CREDENTIALS_PATH` - `/app/credentials.json`
- [ ] `GOOGLE_TOKENS_FOLDER` - `/app/tokens`

## Testing Locally

To test these changes locally:

1. **Backend:**
   ```bash
   .venv\Scripts\Activate.ps1
   python app.py
   ```
   Should run on http://localhost:5000

2. **Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```
   Should run on http://localhost:3000

3. Test all pages to ensure they connect to the backend.

## Resources
- [Railway Deployment Guide](./RAILWAY_DEPLOYMENT.md)
- [Quick Deploy Guide](./DEPLOY_QUICKSTART.md)
- [Calendar Setup](./GOOGLE_CALENDAR_SETUP.md)

---

**Status:** ✅ Ready to deploy!
All hardcoded URLs have been replaced with environment variables.
