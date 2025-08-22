# twitter_client.py
import os, time, random, json, pathlib
import requests
import pandas as pd

BASE = "https://api.x.com/2"
CACHE_DIR = pathlib.Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

def _headers():
    token = os.getenv("X_BEARER_TOKEN")
    if not token:
        raise RuntimeError("Missing X_BEARER_TOKEN in environment/.env")
    return {"Authorization": f"Bearer {token}"}

def _build_url(path: str) -> str:
    if path.startswith(("http://", "https://")):
        return path
    return BASE + (path if path.startswith("/") else "/" + path)

def _cache_read(name: str):
    p = CACHE_DIR / name
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def _cache_write(name: str, data):
    p = CACHE_DIR / name
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f)

def _request(method: str, path: str, params=None, max_retries: int = 3) -> requests.Response:
    url = _build_url(path)
    for attempt in range(max_retries):
        r = requests.request(method, url, headers=_headers(), params=params, timeout=30)
        if r.status_code == 429:
            # rate limited → backoff
            retry_after = r.headers.get("retry-after")
            reset = r.headers.get("x-rate-limit-reset")
            if retry_after:
                wait = int(retry_after)
            elif reset:
                try:
                    wait = max(0, int(reset) - int(time.time()))
                except:
                    wait = 60
            else:
                wait = 60 * (2 ** attempt) + random.randint(0, 5)
            if attempt == max_retries - 1:
                raise requests.HTTPError("Rate limited by X", response=r)
            time.sleep(wait); continue
        if 500 <= r.status_code < 600:
            # transient server error → retry
            if attempt == max_retries - 1:
                r.raise_for_status()
            time.sleep(2 ** attempt + random.random()); continue
        r.raise_for_status()
        return r
    r.raise_for_status()

def get_user_by_username(username: str, cache_ttl=3600):
    cache_key = f"user_{username.lower()}.json"
    cached = _cache_read(cache_key)
    if cached and time.time() - cached.get("_ts", 0) < cache_ttl:
        return cached["data"]

    params = {"user.fields": "profile_image_url,public_metrics,description,created_at,location,verified"}
    r = _request("GET", f"/users/by/username/{username}", params=params)
    data = r.json().get("data")
    if data:
        _cache_write(cache_key, {"_ts": time.time(), "data": data})
    return data

def get_user_tweets(user_id: str, max_results: int = None, exclude_rt_replies: bool = True) -> pd.DataFrame:
    # Default to a low pull size to avoid burning the cap
    if max_results is None:
        max_results = int(os.getenv("X_MAX_RESULTS", "20"))

    cache_key = f"tweets_{user_id}.json"
    cached = _cache_read(cache_key) or {"_ts": 0, "since_id": None, "data": []}

    tweets = []
    next_token = None
    params = {
        "max_results": min(100, max_results),
        "tweet.fields": "created_at,public_metrics,lang",
    }
    if exclude_rt_replies:
        params["exclude"] = "retweets,replies"
    if cached.get("since_id"):
        params["since_id"] = cached["since_id"]

    try:
        while len(tweets) < max_results:
            if next_token:
                params["pagination_token"] = next_token
            r = _request("GET", f"/users/{user_id}/tweets", params=params)
            j = r.json()
            data = j.get("data", [])
            tweets.extend(data)
            next_token = j.get("meta", {}).get("next_token")
            if not next_token:
                break
            params["max_results"] = min(100, max_results - len(tweets))
    except requests.HTTPError as e:
        # Rate-limited → use cache if available
        if e.response is not None and e.response.status_code == 429 and cached["data"]:
            return _df_from_tweets(cached["data"])
        raise

    # Merge new + cached, dedup by id, newest first
    merged = (tweets + cached["data"])
    seen, dedup = set(), []
    for t in sorted(merged, key=lambda x: x.get("created_at",""), reverse=True):
        tid = t.get("id")
        if not tid or tid in seen: 
            continue
        seen.add(tid); dedup.append(t)

    # Update since_id to newest we have
    newest = dedup[0]["id"] if dedup else cached.get("since_id")
    _cache_write(cache_key, {"_ts": time.time(), "since_id": newest, "data": dedup[:500]})
    return _df_from_tweets(dedup)

def _df_from_tweets(items):
    rows = []
    for t in items:
        m = t.get("public_metrics", {})
        rows.append({
            "id": t.get("id",""),
            "text": t.get("text",""),
            "created_at": t.get("created_at",""),
            "likes": int(m.get("like_count", 0)),
            "retweets": int(m.get("retweet_count", 0)),
            "replies": int(m.get("reply_count", 0)),
            "quotes": int(m.get("quote_count", 0)),
        })
    return pd.DataFrame(rows)
