# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from youtube_client import get_youtube_client, get_channel_stats, get_video_ids, get_video_details
import pandas as pd

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

@app.route("/")
def index():
    return render_template("index.html")

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

        # sort and prep
        df = df.sort_values("views", ascending=False).reset_index(drop=True)
        top10 = df.head(10)

        # views-over-time line chart
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

if __name__ == "__main__":
    app.run(debug=False)

