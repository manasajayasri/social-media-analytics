# Social Media Analytics (Python 3.12+)

A minimal Flask app to analyze **YouTube** channels with the YouTube Data API v3.

## What’s inside

- Channel **avatar** + stat cards (subs, total views, total videos)
- **Top-10 by views** (horizontal bar chart)
- **Views over time** (line chart)
- Clickable **video titles** + **thumbnails** (opens on YouTube)
- Modern, Py3.12-friendly deps; secrets via `.env`

## Quickstart

```bash
# 1) Unzip this folder
cd social-media-analytics-starter

# 2) Create & activate venv
python -m venv venv
# Windows PowerShell (recommended)
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
#   .\venv\Scripts\Activate.ps1
# Windows cmd:
#   venv\Scripts\activate.bat
# macOS/Linux:
#   source venv/bin/activate

# 3) Install deps
pip install -r requirements.txt

# 4) Configure env
# Windows:
copy .env.example .env
# macOS/Linux:
# cp .env.example .env
# Put your YouTube API key into .env:
# YOUTUBE_API_KEY=YOUR_KEY_HERE

# 5) Run (debug OFF for safety)
python app.py
# open http://127.0.0.1:5000
```
