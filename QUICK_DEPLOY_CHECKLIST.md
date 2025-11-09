# 🚀 Quick Deployment Checklist

## Your URLs
- **Railway Backend:** https://diversityhireshackathon-production-4ad4.up.railway.app/
- **Vercel Frontend:** (You'll get this after deploying to Vercel)

---

## ✅ Step-by-Step Deployment

### 1. Push the Fixed Code to GitHub
```bash
git add .
git commit -m "Fix: Use environment variable for API URL in all pages"
git push origin main
```

### 2. Configure Railway Backend

Go to **Railway** → Your Project → **Variables** and set:

```env
FLASK_ENV=production
FLASK_SECRET_KEY=generate-a-random-string-here
PORT=5000
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_CREDENTIALS_PATH=/app/credentials.json
GOOGLE_TOKENS_FOLDER=/app/tokens
```

**⚠️ Important:** Add this AFTER deploying frontend:
```env
FRONTEND_URL=https://your-app.vercel.app
```

Railway should auto-deploy from your GitHub push.

### 3. Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository: `visionofdavinci/DiversityHires_Hackathon`
4. **Configure Project:**
   - **Framework Preset:** Next.js
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build` (default)
   - **Output Directory:** `.next` (default)

5. **Add Environment Variable:**
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: `https://diversityhireshackathon-production-4ad4.up.railway.app`
   - **⚠️ NO trailing slash!**

6. Click **Deploy**

### 4. Update Railway with Frontend URL

Once Vercel deployment finishes:

1. Copy your Vercel deployment URL (e.g., `https://diversity-hires-hackathon.vercel.app`)
2. Go back to **Railway** → **Variables**
3. Add/Update:
   ```env
   FRONTEND_URL=https://your-app.vercel.app
   ```
4. Railway will automatically redeploy

### 5. Test Your Deployment

Visit your Vercel URL and test:

- [ ] Main chat page loads
- [ ] Can add a username (try `visionofdavinci`)
- [ ] Chat responds to messages
- [ ] Movie recommendations appear in right panel
- [ ] Letterboxd page works
- [ ] Cineville page shows movies
- [ ] Calendar page allows authentication

---

## 🔍 Troubleshooting

### "Failed to fetch" errors
1. Check browser console (F12) for the actual error
2. Verify `NEXT_PUBLIC_API_URL` in Vercel settings
3. Test Railway backend directly: visit `https://diversityhireshackathon-production-4ad4.up.railway.app/`
   - Should return: `{"status":"ok","message":"Movie Matcher API is running",...}`

### CORS errors
1. Make sure `FRONTEND_URL` in Railway exactly matches your Vercel URL
2. Check Railway logs for CORS-related errors
3. Ensure there's no trailing slash in URLs

### Backend errors
1. Check **Railway** → **Deployments** → Click latest → **View Logs**
2. Look for Python errors or missing environment variables
3. Make sure `GEMINI_API_KEY` is set correctly

### Vercel build errors
1. Check **Vercel** → **Deployments** → Click latest → **View Function Logs**
2. Common issue: Missing environment variables
3. Try redeploying: **Deployments** → **⋯** → **Redeploy**

---

## 📝 Environment Variables Summary

### Vercel (Frontend)
| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://diversityhireshackathon-production-4ad4.up.railway.app` |

### Railway (Backend)
| Variable | Value | Required |
|----------|-------|----------|
| `FLASK_ENV` | `production` | ✅ |
| `FLASK_SECRET_KEY` | Random string (20+ chars) | ✅ |
| `PORT` | `5000` | ✅ |
| `GEMINI_API_KEY` | Your Google Gemini API key | ✅ |
| `FRONTEND_URL` | Your Vercel URL | ✅ |
| `GOOGLE_CREDENTIALS_PATH` | `/app/credentials.json` | For calendar |
| `GOOGLE_TOKENS_FOLDER` | `/app/tokens` | For calendar |

---

## 🎯 Quick Commands

### Check Railway Backend is Running
```bash
curl https://diversityhireshackathon-production-4ad4.up.railway.app/
```

Should return:
```json
{"status":"ok","message":"Movie Matcher API is running",...}
```

### Test Locally Before Deploying
```bash
# Backend
.venv\Scripts\Activate.ps1
python app.py

# Frontend (new terminal)
cd frontend
npm run dev
```

---

## ✨ You're Ready!

Once you complete these steps, your app will be live! 🎉

Remember to:
1. ✅ Push code to GitHub
2. ✅ Set `NEXT_PUBLIC_API_URL` in Vercel
3. ✅ Deploy to Vercel
4. ✅ Set `FRONTEND_URL` in Railway
5. ✅ Test the live app

Good luck! 🚀
