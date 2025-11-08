# DiversityHires_Hackathon
This is the repository for the PROSUS AI Hackathon 

Team Name: Diversity Hires

Short description: 
An AI agent that autonomously organizes movie nights by:
- Detecting free time in your calendar
- Finding personalized movies from Cineville based on your Letterboxd
- Polling your WhatsApp group
- Sending confirmations with meeting details

Idea:  Movie Night Orchestrator

An AI agent that autonomously organizes movie nights by:
- Detecting free time in your calendar
- Finding personalized movies from Cineville based on your Letterboxd
- Polling your WhatsApp group
- Sending confirmations with meeting details
+ (optionally) Books tickets
+ (GOD HELP US GET HERE) Movie recommendation based on description/vibe 

Why it's cool: Eliminates the "what do we do tonight" paralysis


Structure of project:

```text

movie-night-orchestrator/
│
├── README.md                          # Project documentation
├── requirements.txt                   # Python dependencies
├── .gitignore                        # Git ignore file
├── main.py                           # Main entry point
│
├── config/                           # Configuration files
│   ├── .env                          # API keys (DO NOT COMMIT!)
│   ├── .env.example                  # Example env file (commit this)
│   ├── google_credentials.json       # Google Calendar credentials (DO NOT COMMIT!)
│   └── config.yaml                   # App configuration (optional)
│
├── src/                              # Source code
│   ├── __init__.py                   # Makes src a package
│   │
│   ├── calendar_agent.py             # Calendar integration 
│   ├── cineville_scraper.py          # Cineville scraping
│   ├── letterboxd_integration.py     # Letterboxd integration 
│   ├── movie_matcher.py              # Movie matching logic 
│   ├── whatsapp_bot.py               # WhatsApp messaging 
│   ├── orchestrator.py               # Main orchestration brain 
│   │
│   └── utils/                        # Utility functions
│       ├── __init__.py
│       ├── time_utils.py             # Time/date helpers
│       └── config_loader.py          # Config loading utilities
│
├── notebooks/                        # Jupyter notebooks for testing
│   ├── 01_calendar_test.ipynb        # Test calendar integration
│   ├── 02_cineville_test.ipynb       # Test Cineville scraping
│   ├── 03_letterboxd_test.ipynb      # Test Letterboxd integration
│   ├── 04_whatsapp_test.ipynb        # Test WhatsApp bot
│   ├── 05_movie_matcher_test.ipynb   # Test movie matching
│   └── 06_full_demo.ipynb            # Full integration demo
│
├── data/                             # Data files
│   ├── mock_showtimes.json           # Mock Cineville data (fallback)
│   ├── mock_letterboxd.json          # Mock preferences (fallback)
│   └── user_preferences.json         # Saved user preferences
│
├── tests/                            # Unit tests (optional, if time)
│   ├── __init__.py
│   ├── test_calendar.py
│   ├── test_cineville.py
│   ├── test_letterboxd.py
│   └── test_whatsapp.py
│
│
└── deployment/                       # Deployment files (FIGURE OUT)
    ├── Dockerfile                    # Docker configuration (optional)
    ├── deploy.sh                     # Deployment script
    └── requirements-prod.txt         # Production dependencies

```

## **Sanne: Calendar + Orchestrator** 

- [ ] Setup Google Calendar API credentials
- [ ] Create `src/calendar_agent.py`
- [ ] Test calendar authentication
- [ ] Test free time detection
- [ ] Create `src/utils/time_utils.py` - time helper functions
- [ ] Create `src/utils/config_loader.py` - load .env files
- [ ] Start `src/orchestrator.py` skeleton (wait for others' APIs)
- [ ] Create `notebooks/01_calendar_test.ipynb` - document tests
- [ ] Help with integration when others are ready
- [ ] Complete `src/orchestrator.py` - wire everything together
- [ ] Add proactive checking logic (when to suggest movie night)
- [ ] Add error handling
- [ ] Help with final testing
- [ ] Work on `main.py` - command line interface

**Files:**
- `src/calendar_agent.py` 
- `src/utils/time_utils.py`
- `src/utils/config_loader.py`
- `src/orchestrator.py` (collaborate with team)
- `notebooks/01_calendar_test.ipynb`
- `main.py`

---

## **Ioana: Movies (Cineville + Letterboxd + Matching)** 

- [x] **Investigate Cineville**
  - Open https://www.cineville.nl/agenda
  - Open Browser DevTools → Network tab
  - Look for API calls (JSON responses)
  - **Decision:** API exists? → use it. No API? → scrape HTML
- [x] **Create `src/cineville_scraper.py`**
  - If API: implement API calls
  - If no API: implement BeautifulSoup scraper
  - Create mock data fallback
  - Test with real Cineville website
- [x] **Create `src/letterboxd_integration.py`**
  - Method 1: Scrape public profile
  - Method 2: Manual input fallback
  - Test with your own Letterboxd username
- [x] **Create `src/movie_matcher.py`**
  - Combine Cineville + Letterboxd
  - Scoring algorithm (rate movies by preference)
  - Get TMDb API key (free, 5 minutes)
  - Fetch movie details from TMDb
- [ ] **Create mock data files:**
  - `data/mock_showtimes.json`
  - `data/mock_letterboxd.json`
- [ ] Polish matching algorithm
- [x] Test with different Letterboxd profiles
- [ ] Handle edge cases (no movies found, etc.)
- [ ] Integration with orchestrator
- [ ] Create `notebooks/02_cineville_test.ipynb`, `03_letterboxd_test.ipynb`, `05_movie_matcher_test.ipynb`

**Files:**
- `src/cineville_scraper.py`
- `src/letterboxd_integration.py`
- `src/movie_matcher.py`
- `data/mock_showtimes.json`
- `data/mock_letterboxd.json`
- `notebooks/02_cineville_test.ipynb`
- `notebooks/03_letterboxd_test.ipynb`
- `notebooks/05_movie_matcher_test.ipynb`

---

## **Noor: WhatsApp + Integration** 

- [ ] **Setup Twilio WhatsApp**
  - Sign up: https://www.twilio.com/try-twilio
  - Get Account SID + Auth Token
  - Join WhatsApp sandbox (send "join <code>")
  - Get teammates to join sandbox too
  - Add credentials to `config/.env`
- [ ] **Create `src/whatsapp_bot.py`**
  - Implement `send_message()`
  - Implement `send_movie_poll()`
  - Implement `register_vote()`
  - Implement `send_confirmation()`
  - Test sending yourself a message
- [ ] **Test WhatsApp polling flow**
  - Send test poll to yourself
  - Manually reply with vote
  - Test vote counting
  - Test confirmation message

- [ ] **Create group testing**
  - Send poll to team WhatsApp group
  - Test multi-person voting
  - Fix any issues
- [ ] **Help with orchestrator integration**
  - Work with Person 1 to integrate WhatsApp into main flow
- [ ] Add reminder functionality
- [ ] Polish message formatting
- [ ] Add emoji and better UX
- [ ] Test edge cases (no votes, tie, etc.)
- [ ] Integration testing with full team
- [ ] Create `notebooks/04_whatsapp_test.ipynb`

**Files:**
- `src/whatsapp_bot.py`
- `notebooks/04_whatsapp_test.ipynb`
- Help with `src/orchestrator.py` (integration)

---