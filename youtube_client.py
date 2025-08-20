# youtube_client.py
from googleapiclient.discovery import build
import os
import pandas as pd

def get_youtube_client():
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing YOUTUBE_API_KEY environment variable. Create a .env file or set it in your shell.")
    return build("youtube", "v3", developerKey=api_key)

def get_channel_stats(youtube, channel_id: str):
    req = youtube.channels().list(part="snippet,contentDetails,statistics", id=channel_id)
    res = req.execute()
    items = res.get("items", [])
    if not items:
        return None
    item = items[0]
    thumbs = item["snippet"].get("thumbnails", {})
    thumb = thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}
    data = {
        "channel_title": item["snippet"]["title"],
        "channel_avatar": thumb.get("url", ""),
        "subscribers": int(item["statistics"].get("subscriberCount", 0)),
        "views": int(item["statistics"].get("viewCount", 0)),
        "total_videos": int(item["statistics"].get("videoCount", 0)),
        "uploads_playlist_id": item["contentDetails"]["relatedPlaylists"]["uploads"],
    }
    return data

def get_video_ids(youtube, playlist_id: str, max_results: int = 100):
    video_ids = []
    page_token = None
    while True and len(video_ids) < max_results:
        req = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=min(50, max_results - len(video_ids)),
            pageToken=page_token
        )
        res = req.execute()
        for it in res.get("items", []):
            vid = it["contentDetails"]["videoId"]
            video_ids.append(vid)
        page_token = res.get("nextPageToken")
        if not page_token or len(video_ids) >= max_results:
            break
    return video_ids

def get_video_details(youtube, video_ids):
    out = []
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        req = youtube.videos().list(part="snippet,statistics", id=",".join(chunk))
        res = req.execute()
        for v in res.get("items", []):
            stats = v.get("statistics", {})
            thumbs = v["snippet"].get("thumbnails", {})
            thumb = thumbs.get("medium") or thumbs.get("high") or thumbs.get("default") or {}
            out.append({
                "video_id": v["id"],
                "title": v["snippet"]["title"],
                "published_at": v["snippet"]["publishedAt"],
                "thumbnail": thumb.get("url", ""),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
            })
    return pd.DataFrame(out)
