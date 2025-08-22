# Social Media Analytics (Python 3.12+)

A minimal Flask app to analyze **YouTube** channels (YouTube Data API v3) and **X (Twitter)** accounts (X API v2).  

## What’s inside
- **YouTube**
  - Channel avatar + stat cards (subs, total views, total videos)
  - **Top-10 by views** (horizontal bar)
  - **Views over time** (line chart)
  - Clickable titles + thumbnails

- **X (Twitter)**
  - User avatar + follower stats
  - **Top-10 tweets by likes** (bar)
  - **Likes over time** (line)
  - Table with likes / RTs / replies / quotes
  - Rate-limit-aware (backoff + small pulls) and **local cache**
  - Modern, Py3.12-friendly deps; secrets via `.env`

## Youtube Analytics:
<img width="1000" height="892" alt="image" src="https://github.com/user-attachments/assets/6498550d-ce4f-44fa-8184-61edb90869bf" />

## X Analytics:
<img width="1000" height="892" alt="image" src="https://github.com/user-attachments/assets/8cd70e7a-458e-40bf-8dde-46dc8fed9667" />

## Quickstart

```bash
# 1) Open project
cd social-media-analytics

# 2) Create & activate venv
python -m venv venv
# PowerShell:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
#   .\venv\Scripts\Activate.ps1
# cmd:
#   venv\Scripts\activate.bat
# macOS/Linux:
#   source venv/bin/activate

# 3) Install deps
pip install -r requirements.txt
# (Ensure 'requests' is included; if not: pip install requests)

# 4) Configure env

# Windows:
copy .env.example .env
# macOS/Linux:
# cp .env.example .env

# Required:
#   YOUTUBE_API_KEY=YOUR_KEY
# Optional (for X):
#   X_BEARER_TOKEN=YOUR_X_BEARER_TOKEN
#   X_MAX_RESULTS=20         # lower = fewer API calls

# 5) Run (debug OFF for safety)
python app.py
# open http://127.0.0.1:5000
```


