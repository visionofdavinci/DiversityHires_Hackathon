# Quick Deploy to Railway - Checklist

## 🚀 Quick Start (5 minutes)

### 1. Push to GitHub
```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 2. Deploy Backend to Railway

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select `DiversityHires_Hackathon`
4. Railway auto-detects Dockerfile ✅

### 3. Add Environment Variables

Click Variables tab, add these:

```env
FLASK_SECRET_KEY=generate-a-random-string-here
FLASK_ENV=production
GEMINI_API_KEY=your-gemini-api-key-here
FRONTEND_URL=https://your-frontend-will-go-here.vercel.app
```

### 4. Get Your Backend URL

Click "Settings" → "Generate Domain"

Copy URL: `https://your-app-xxxxx.up.railway.app`

### 5. Deploy Frontend to Vercel

1. Go to https://vercel.com
2. "New Project" → Import from GitHub
3. **Root Directory**: `frontend`
4. Add environment variable:
   ```env
   NEXT_PUBLIC_API_URL=https://your-app-xxxxx.up.railway.app
   ```
5. Deploy ✅

### 6. Update Backend with Frontend URL

Go back to Railway → Variables → Update:
```env
FRONTEND_URL=https://your-app.vercel.app
```

### 7. Update Google OAuth

Google Cloud Console → Credentials → OAuth 2.0 → Add redirect:
```
https://your-app-xxxxx.up.railway.app/calendar/oauth2callback
```

## ✅ Done!

Your app is live at:
- Frontend: `https://your-app.vercel.app`
- Backend: `https://your-app-xxxxx.up.railway.app`

## 📝 Important Files Created

- ✅ `Dockerfile` - Backend container configuration
- ✅ `.dockerignore` - Exclude unnecessary files
- ✅ `railway.json` - Railway deployment config
- ✅ `.env.example` - Environment variables template
- ✅ `RAILWAY_DEPLOYMENT.md` - Full deployment guide

## 🔧 Local Testing

Before deploying, test locally:

```bash
# Test backend
python app.py

# Test frontend
cd frontend
npm run dev
```

## 🆘 Need Help?

See `RAILWAY_DEPLOYMENT.md` for detailed instructions and troubleshooting.
