# 🔐 Environment Variables Configuration

## ✅ Vercel (Frontend)
**Project:** diversity-hires-hackathon-3x1r

Go to: **Vercel Dashboard** → **Settings** → **Environment Variables**

Add the following variable:

```
NEXT_PUBLIC_API_URL=https://diversityhireshackathon-production-4ad4.up.railway.app
```

**⚠️ Important:**
- No trailing slash!
- Apply to all environments (Production, Preview, Development)
- After adding, **redeploy** the site

---

## ✅ Railway (Backend)
**Project:** diversityhireshackathon-production-4ad4

Go to: **Railway Dashboard** → **Variables**

Add/verify these variables:

```env
# Required - Flask Configuration
FLASK_ENV=production
FLASK_SECRET_KEY=your-secret-key-minimum-20-characters
PORT=5000

# Required - AI Service
GEMINI_API_KEY=your-google-gemini-api-key

# Required - CORS (Frontend URL)
FRONTEND_URL=https://diversity-hires-hackathon-3x1r.vercel.app

# Optional - Google Calendar Integration
GOOGLE_CREDENTIALS_PATH=/app/credentials.json
GOOGLE_TOKENS_FOLDER=/app/tokens
```

**⚠️ Important:**
- No trailing slash on FRONTEND_URL!
- Railway will auto-redeploy when you change variables
- Make sure GEMINI_API_KEY is valid

---

## 🧪 Testing the Configuration

### 1. Test Backend Health
Open in browser or use curl:
```
https://diversityhireshackathon-production-4ad4.up.railway.app/
```

Expected response:
```json
{
  "status": "ok",
  "message": "Movie Matcher API is running",
  "version": "1.0.0",
  ...
}
```

### 2. Test Frontend
Open in browser:
```
https://diversity-hires-hackathon-3x1r.vercel.app
```

Should load without "Error connecting to server" message.

### 3. Test CORS
In the browser console (F12), you should NOT see errors like:
- `Access-Control-Allow-Origin`
- `CORS policy`
- `blocked by CORS`

---

## 🔍 Troubleshooting

### Issue: "Error connecting to server"
**Causes:**
1. `NEXT_PUBLIC_API_URL` not set in Vercel
2. Railway backend is down
3. CORS blocking the request

**Solutions:**
1. Check Vercel environment variables
2. Check Railway deployment logs
3. Verify FRONTEND_URL matches your Vercel URL exactly

### Issue: CORS errors in browser console
**Causes:**
1. `FRONTEND_URL` in Railway doesn't match Vercel URL
2. Missing trailing slash mismatch

**Solutions:**
1. Update `FRONTEND_URL` in Railway to: `https://diversity-hires-hackathon-3x1r.vercel.app`
2. Ensure no trailing slashes
3. Check Railway logs for CORS errors

### Issue: Backend returns 500 errors
**Causes:**
1. Missing `GEMINI_API_KEY`
2. Invalid API key
3. Python errors in backend

**Solutions:**
1. Verify all required environment variables are set
2. Check Railway deployment logs for Python errors
3. Test endpoints individually

---

## 📋 Current Configuration Summary

| Service | URL | Environment |
|---------|-----|-------------|
| **Frontend** | https://diversity-hires-hackathon-3x1r.vercel.app | Vercel |
| **Backend** | https://diversityhireshackathon-production-4ad4.up.railway.app | Railway |

### Vercel Environment Variables
- [x] `NEXT_PUBLIC_API_URL` = `https://diversityhireshackathon-production-4ad4.up.railway.app`

### Railway Environment Variables
- [x] `FLASK_ENV` = `production`
- [x] `FLASK_SECRET_KEY` = (your secret)
- [x] `PORT` = `5000`
- [x] `GEMINI_API_KEY` = (your key)
- [x] `FRONTEND_URL` = `https://diversity-hires-hackathon-3x1r.vercel.app`

---

## 🚀 Deployment Checklist

After setting environment variables:

1. **Railway:**
   - [ ] All required variables are set
   - [ ] Latest deployment is successful (check Deployments tab)
   - [ ] Backend responds at root URL

2. **Vercel:**
   - [ ] `NEXT_PUBLIC_API_URL` is set correctly
   - [ ] Redeploy if needed (Deployments → Redeploy)
   - [ ] Site loads without errors

3. **Testing:**
   - [ ] Main chat page loads
   - [ ] Can add usernames
   - [ ] Chat responds to messages
   - [ ] Movie recommendations appear
   - [ ] No CORS errors in console

---

## 💡 Quick Reference

### Test Backend
```bash
curl https://diversityhireshackathon-production-4ad4.up.railway.app/
```

### Check Railway Logs
**Railway** → **Deployments** → Click latest → **View Logs**

### Check Vercel Logs
**Vercel** → **Deployments** → Click latest → **View Function Logs**

### Redeploy Railway
Push to GitHub main branch (auto-deploys)

### Redeploy Vercel
**Vercel** → **Deployments** → Latest → **⋯** → **Redeploy**

---

**Last Updated:** November 9, 2025
**Status:** ✅ Environment variables configured and documented
