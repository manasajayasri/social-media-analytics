# app.py
import os
import time
import pandas as pd
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv

from youtube_client import (
    get_youtube_client, get_channel_stats, get_video_ids, get_video_details
)

from twitter_client import get_user_by_username, get_user_tweets

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

@app.route("/")
def index():
    return render_template("index.html")

# ---------------- YouTube ----------------
@app.route("/youtube/form")
def youtube_form():
    return render_template("youtube_form.html")

@app.route("/youtube/process", methods=["POST"])
def youtube_process():
    channel_id = request.form.get("channel_id", "").strip()
    if not channel_id:
        flash("Please enter a channel ID")
        return redirect(url_for("youtube_form"))
    try:
        yt = get_youtube_client()
        ch = get_channel_stats(yt, channel_id)
        if not ch:
            flash("Channel not found. Double-check the channel ID.")
            return redirect(url_for("youtube_form"))

        video_ids = get_video_ids(yt, ch["uploads_playlist_id"], max_results=150)
        df = get_video_details(yt, video_ids)

        df = df.sort_values("views", ascending=False).reset_index(drop=True)
        top10 = df.head(10)

        df_time = df.copy()
        df_time["published_at"] = pd.to_datetime(df_time["published_at"], errors="coerce")
        df_time = df_time.dropna(subset=["published_at"]).sort_values("published_at")
        chart2_dates = df_time["published_at"].dt.strftime("%Y-%m-%d").tolist()
        chart2_views = df_time["views"].tolist()

        return render_template(
            "youtube_dashboard.html",
            channel=ch,
            table=df.head(50).to_dict(orient="records"),
            chart_labels=top10["title"].tolist(),
            chart_values=top10["views"].tolist(),
            chart2_dates=chart2_dates,
            chart2_views=chart2_views
        )
    except Exception as e:
        flash(f"Error: {e}")
        return redirect(url_for("youtube_form"))

# ---------------- X (Twitter) ----------------
@app.route("/x/form")
def x_form():
    return render_template("x_form.html")

@app.route("/x/process", methods=["POST"])
def x_process():
    username = request.form.get("username", "").strip().lstrip("@")
    if not username:
        flash("Please enter a username")
        return redirect(url_for("x_form"))
    try:
        u = get_user_by_username(username)
        if not u:
            flash("User not found")
            return redirect(url_for("x_form"))

        user = {
            "id": u["id"],
            "name": u.get("name", username),
            "username": u.get("username", username),
            "avatar": u.get("profile_image_url", ""),
            "desc": u.get("description", ""),
            "followers": u.get("public_metrics", {}).get("followers_count", 0),
            "following": u.get("public_metrics", {}).get("following_count", 0),
            "tweet_count": u.get("public_metrics", {}).get("tweet_count", 0),
            "listed_count": u.get("public_metrics", {}).get("listed_count", 0),
        }

        df = get_user_tweets(user["id"], max_results=50)
        if df.empty:
            flash("No tweets available or rate-limited. Try again later.")
            return redirect(url_for("x_form"))

        df = df.sort_values("likes", ascending=False).reset_index(drop=True)

        top10 = df.head(10)
        chart_labels = top10["text"].str.slice(0, 80).tolist()
        chart_values = top10["likes"].tolist()

        df_time = df.copy()
        df_time["created_at"] = pd.to_datetime(df_time["created_at"], errors="coerce")
        df_time = df_time.dropna(subset=["created_at"]).sort_values("created_at")
        chart2_dates = df_time["created_at"].dt.strftime("%Y-%m-%d").tolist()
        chart2_values = df_time["likes"].tolist()

        return render_template(
            "x_dashboard.html",
            user=user,
            table=df.head(50).to_dict(orient="records"),
            chart_labels=chart_labels,
            chart_values=chart_values,
            chart2_dates=chart2_dates,
            chart2_values=chart2_values
        )

    except requests.HTTPError as e:
        msg = "Rate limited by X. Please try again in a few minutes."
        try:
            reset = e.response.headers.get("x-rate-limit-reset") if e.response else None
            if reset:
                eta = max(0, int(reset) - int(time.time()))
                if eta > 0:
                    mins = eta // 60
                    msg += f" (~{mins} min)" if mins else f" (~{eta} sec)"
        except Exception:
            pass
        flash(msg)
        return redirect(url_for("x_form"))
    except Exception as e:
        flash(f"Error: {e}")
        return redirect(url_for("x_form"))
    except requests.HTTPError as e:
        msg = "Rate limited by X. Showing cached data if available."
        flash(msg)
        return redirect(url_for("x_form"))



if __name__ == "__main__":
    app.run(debug=False)

