# DiversityHires_Hackathon
This is the repository for the PROSUS AI Hackathon 

Team Name: Diversity Hires

 **[Try the Live Demo](https://diversity-hires-hackathon-3x1r.vercel.app/)**

## Movie Night Orchestrator

### Short Description
An intelligent AI-powered agent that transforms movie planning from hours of group chat chaos into seconds of natural conversation. Simply tell the agent what you want, and it handles everything - from understanding your preferences to booking the perfect movie night.

### AI Methods & Technology Stack

**Natural Language Understanding:**
- **Google Gemini AI** for parsing natural language requests
  - Intent detection from conversational input
  - Entity extraction (participants, dates, mood/genre preferences)
  - Contextual understanding of temporal expressions ("this Friday", "tonight", "weekend")
- **Gemini NLG** for generating natural, context-aware responses

**Personalization Engine:**
- **Web scraping** of Letterboxd profiles to build user taste graphs
- **Collaborative filtering** for group compatibility scoring
- **TMDb API integration** for enriched movie metadata
- **Adaptive learning** from group viewing history and preferences
- **Mood-based filtering** using genre mapping and sentiment analysis

**Intelligent Scheduling:**
- **Google Calendar API** integration for automated availability detection
- **Calendar matching algorithm** to find optimal time slots across multiple users
- **Free time detection** with configurable minimum duration thresholds
- **OAuth 2.0** secure authentication flow

**Recommendation Algorithm:**
- **Hybrid recommendation system** combining:
  - Content-based filtering (genres, directors, themes)
  - Collaborative filtering (group compatibility)
  - Temporal constraints (showtime availability)
  - Preference weighting per user
- **Random Forest classifier** for mood-to-genre prediction
- **Multi-criteria scoring** (individual scores + group harmony)
- **Real-time cinema data** scraped from Cineville Amsterdam

**Full-Stack Architecture:**
- **Backend:** Python Flask with microservices architecture
  - Calendar agent, Movie matcher, Orchestrator modules
  - RESTful API design
- **Frontend:** Next.js 14 with TypeScript
  - Server-side rendering for optimal performance
  - Real-time updates via API polling
  - Responsive UI with Tailwind CSS
- **Deployment:** Railway (backend) + Vercel (frontend)
  - Production-ready with environment-based configuration
  - CORS-enabled for secure cross-origin requests

### Why It's Innovative
**Eliminates the "what do we do tonight?" paralysis** by combining multiple AI techniques:
- Natural language processing removes the friction of structured inputs
- Personalization ensures recommendations everyone will enjoy
- Automated scheduling removes the coordination overhead
- End-to-end orchestration means zero manual work

### Key Features
✅ **Natural language input** - just chat with the AI  
✅ **Multi-user preference analysis** - learns from Letterboxd viewing history  
✅ **Automated calendar integration** - finds when everyone is free  
✅ **Real-time cinema data** - actual showtimes from Cineville Amsterdam  
✅ **Smart group scoring** - balances individual preferences  
✅ **Mood-based filtering** - matches recommendations to your vibe  
✅ **Conversational AI responses** - natural, helpful interactions


## Project Structure

```text
DiversityHires_Hackathon/
│
├── README.md                               # Project documentation
├── requirements.txt                        # Python dependencies
├── .gitignore                             # Git ignore file
├── .env                                   # Environment variables (DO NOT COMMIT!)
├── .env.example                           # Example env file
├── credentials.json                       # Google OAuth credentials (DO NOT COMMIT!)
│
├── app.py                                 # Flask backend API server
├── main.py                                # Main entry point (CLI)
├── webhook.py                             # WhatsApp webhook handler
├── test_calendar_fix.py                   # Calendar testing script
├── main_test.ipynb                        # Testing notebook
│
├── Dockerfile                             # Docker configuration for Railway
├── railway.json                           # Railway deployment config
│
│
├── src/                                   # Backend source code
│   ├── ai_agent.py                        # AI agent orchestration
│   ├── api_server.py                      # API server utilities
│   ├── calendar_agent.py                  # Google Calendar integration
│   ├── calendar_matcher.py                # Calendar free time matching
│   ├── cineville_scraper.py               # Cineville cinema scraper
│   ├── gemini_nlg.py                      # Gemini natural language generation
│   ├── gemini_parser.py                   # Gemini NLP parser
│   ├── openai_parser.py                   # OpenAI parser fallback
│   ├── letterboxd_integration.py          # Letterboxd profile scraper
│   ├── movie_matcher.py                   # Movie matching algorithm + TMDb
│   ├── group_history.py                   # Group preference tracking
│   ├── mood_filter.py                     # Mood-based filtering
│   ├── orchestrator.py                    # Main orchestration logic
│   ├── poll_manager.py                    # Poll management
│   ├── test_group_history_mood_filtering.py  # Testing script
│   │
│   └── utils/                             # Utility modules
│       ├── config_loader.py               # Configuration loader
│       └── time_utils.py                  # Time/date helpers
│
├── scripts/                               # Utility scripts
│   ├── create_token_for_user.py           # Create OAuth tokens
│   ├── find_common_free_time.py           # Calendar availability finder
│   ├── generate_oauth_env.py              # Generate OAuth env variables
│   └── test_calendar_auth.py              # Test calendar authentication
│
├── data/                                  # Data files
│   ├── cineville_nextjs_data.json         # Cineville data export
│   ├── mock_letterboxd.json               # Mock Letterboxd data
│   └── groups/                            # Group preference data
│       ├── noorsterre_sannebr_visionofdavinci_history.json
│       └── noorsterre_sannebr_visionofdavinci_preferences.json
│
├── tokens/                                # Google Calendar OAuth tokens (DO NOT COMMIT!)
│   ├── ioana.json
│   ├── noor.json
│   └── sanne.json
│
├── notebooks/                             # Jupyter notebooks for testing
│   └── ai_parser_test.ipynb               # AI parser testing
│
├── old_whatsapp/                          # Legacy WhatsApp implementation
│   ├── og_whatsapp_bot.py
│   ├── whatsapp_bot.py
│   └── whatsapp_test.ipynb
│
└── frontend/                              # Next.js frontend application
    ├── package.json                       # Node dependencies
    ├── tsconfig.json                      # TypeScript config
    ├── next.config.ts                     # Next.js config
    ├── tailwind.config.js                 # Tailwind CSS config
    ├── postcss.config.js                  # PostCSS config
    ├── eslint.config.mjs                  # ESLint config
    ├── .env.local                         # Frontend env variables
    ├── README.md                          # Frontend documentation
    │
    ├── public/                            # Static assets
    │
    ├── src/                               # Frontend source code
    │   ├── app/                           # Next.js app router
    │   │   ├── layout.tsx                 # Root layout
    │   │   ├── page.tsx                   # Home page (chat interface)
    │   │   ├── globals.css                # Global styles
    │   │   │
    │   │   ├── api/                       # API route handlers
    │   │   │   ├── calendar/route.ts      # Calendar API proxy
    │   │   │   ├── chat/route.ts          # Chat API proxy
    │   │   │   ├── cineville/route.ts     # Cineville API proxy
    │   │   │   └── letterboxd/route.ts    # Letterboxd API proxy
    │   │   │
    │   │   ├── calendar/                  # Calendar page
    │   │   │   └── page.tsx
    │   │   ├── cineville/                 # Cineville page
    │   │   │   └── page.tsx
    │   │   └── letterboxd/                # Letterboxd page
    │   │       └── page.tsx
    │   │
    │   ├── components/                    # React components
    │   │   ├── CalendarView.tsx           # Calendar display
    │   │   ├── chat.tsx                   # Main chat interface
    │   │   ├── chat-message.tsx           # Chat message component
    │   │   ├── ChatHistory.tsx            # Chat history
    │   │   ├── CinevilleRecommendations.tsx  # Movie recommendations
    │   │   ├── LetterboxdProfile.tsx      # Letterboxd profile display
    │   │   ├── movie-card.tsx             # Movie card component
    │   │   ├── nav-layout.tsx             # Navigation layout
    │   │   └── ui/                        # UI components
    │   │       └── button.tsx
    │   │
    │   ├── lib/                           # Utilities
    │   │   ├── types.ts                   # TypeScript types
    │   │   └── utils.ts                   # Helper functions
    │   │
    │   ├── services/                      # API services
    │   │   └── api.ts                     # Backend API client
    │   │
    │   └── types/                         # Type definitions
    │       └── index.ts
    │
    └── data/                              # Frontend data
        └── groups/                        # Group data cache

```
