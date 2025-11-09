# Hugging Face Free AI Chat Setup

I've replaced OpenAI with **Hugging Face's free Inference API**! 🎉

## What Changed

- ❌ Removed OpenAI dependency (no more quota errors!)
- ✅ Using **Mistral-7B-Instruct** - a powerful open-source model
- ✅ Completely FREE (with rate limits, but much more generous)
- ✅ Fallback responses if the API is slow or unavailable

## Quick Start (Optional - Works Without API Key!)

The chat will work **immediately** even without an API key using the public demo endpoint. However, for better performance and higher rate limits:

### Get a Free Hugging Face API Token (Recommended)

1. Go to [Hugging Face](https://huggingface.co/) and create a free account
2. Go to [Settings → Access Tokens](https://huggingface.co/settings/tokens)
3. Click **"New token"**
4. Give it a name (e.g., "Movie Chat Bot")
5. Select **"Read"** access (that's all you need)
6. Click **"Generate"**
7. Copy the token (starts with `hf_...`)

### Add to Your Frontend

Open `frontend/.env.local` and add:

```env
HUGGINGFACE_API_KEY=hf_YourTokenHere
```

**Or just leave it empty** - it will use the public demo:

```env
HUGGINGFACE_API_KEY=
```

## Restart Your Development Server

```bash
# Stop the current Next.js server (Ctrl+C)
# Then restart:
cd frontend
npm run dev
```

## Alternative Free Models

You can switch to other free models by changing the `HF_MODEL` in `frontend/src/app/api/chat/route.ts`:

```typescript
// Current model (recommended):
const HF_MODEL = 'mistralai/Mistral-7B-Instruct-v0.2'

// Alternative options:
// const HF_MODEL = 'meta-llama/Llama-2-7b-chat-hf'  // Meta's Llama 2
// const HF_MODEL = 'HuggingFaceH4/zephyr-7b-beta'   // Zephyr (fast)
// const HF_MODEL = 'microsoft/DialoGPT-large'        // Conversational
```

## How It Works

1. **User sends a message** → Frontend sends to `/api/chat`
2. **System checks for usernames** → Fetches Letterboxd + Calendar data
3. **Formats context** → Includes movie recommendations and availability
4. **Calls Hugging Face API** → Gets AI response
5. **Returns to user** → Shows chat response + movie cards

## Features

✅ Completely free (no credit card required)
✅ No quota limits (well, generous rate limits)
✅ Works offline with fallback responses
✅ Contextual - knows about movies and calendars
✅ Open source models

## Troubleshooting

### "Model is loading" error
- The model might be cold-starting (first request after being idle)
- Wait 20-30 seconds and try again
- Or switch to a different model

### Rate limit errors
- Get a free API token (see above)
- Or wait a few minutes between requests

### Chat not responding
- Check browser console for errors
- Verify Flask backend is running on port 5000
- Check that frontend dev server is running

## No Installation Needed!

The code is ready to use. Just:
1. Restart your Next.js dev server
2. Start chatting!

The chat will work immediately with the public Hugging Face endpoint. For better performance, add your free API key.
