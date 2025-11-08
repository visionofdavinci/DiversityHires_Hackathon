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

Why it's cool: Eliminates the "what do we do tonight" paralysis


Structure of project:

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


