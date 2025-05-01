"""Streamlit web application that authenticates a user with Spotify OAuth, invokes an AWS Lambda backend to fetch processed listening data, and renders interactive analytics dashboards similar to Spotify Wrapped.

Author: Daniyal Khalid
Created: 2025
"""

import streamlit as st
import boto3
import json
import pandas as pd
import time
import matplotlib.pyplot as plt
import numpy as np
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime, timedelta
import uuid  # for generating unique cache paths

# ---------------- ENV / CONFIG ---------------- #
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
REGION = os.environ.get('REGION', 'us-east-2')
PROCESSED_BUCKET = 'spotify-processed-data-dk'

# Change BASE_URL to your actual app URL or EC2 public IP + port:
BASE_URL = "http://localhost:8501/callback"
SCOPE = 'user-read-private user-top-read user-read-recently-played'

# ------------- Helper Functions (S3 + Display) ------------- #
def fetch_processed_data(processed_key: str) -> dict:
    """Fetch processed JSON from S3."""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=REGION
        )
        response = s3_client.get_object(Bucket=PROCESSED_BUCKET, Key=processed_key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        return data
    except Exception as e:
        st.error(f"Error fetching processed data: {e}")
        return None

def display_grid(items: list[dict], item_type: str = "artist", columns_per_row: int = 3) -> None:
    """
    Lay out items (artists or tracks) in a grid (rows of columns).
    """
    if not items:
        st.info(f"No {item_type} data found.")
        return

    rows = [items[i:i+columns_per_row] for i in range(0, len(items), columns_per_row)]
    for row in rows:
        cols = st.columns(len(row))
        for col, item in zip(cols, row):
            rank = item.get('rank', '?')
            if item_type == "artist":
                name = item.get('artist_name', 'Unknown Artist')
                image_url = item.get('artist_image')
                col.markdown(f"**{rank}. {name}**")
                if image_url:
                    col.image(image_url, use_container_width=True)
            else:  # track
                name = item.get('track_name', 'Unknown Track')
                artist = item.get('artist_name', 'Unknown Artist')
                image_url = item.get('album_image')
                col.markdown(f"**{rank}. {name}**")
                col.caption(f"by {artist}")
                if image_url:
                    col.image(image_url, use_container_width=True)

# ------------- Our ETL (raw data extraction) ------------- #
def upload_to_s3(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket."""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('REGION', 'us-east-2')
    )

    if object_name is None:
        object_name = os.path.basename(file_name)
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except Exception as e:
        raise Exception(f"Error uploading file: {e}")

def authenticate_and_extract(sp):
    """
    Given a Spotipy client (with a valid token), extract user data and upload to S3.
    Returns (raw_data, upload_message, raw_key).
    """
    # 1) Current User Info
    current_user = sp.current_user()
    user_id = current_user.get("id", "unknown_user")
    display_name = current_user.get("display_name", "Unknown")

    # 2) Top Artists for all time ranges
    top_artists_short = sp.current_user_top_artists(limit=50, time_range='short_term')
    top_artists_medium = sp.current_user_top_artists(limit=50, time_range='medium_term')
    top_artists_long = sp.current_user_top_artists(limit=50, time_range='long_term')

    # 3) Top Tracks for all time ranges
    top_tracks_short = sp.current_user_top_tracks(limit=50, time_range='short_term')
    top_tracks_medium = sp.current_user_top_tracks(limit=50, time_range='medium_term')
    top_tracks_long = sp.current_user_top_tracks(limit=50, time_range='long_term')

    # 4) Recently played for the past 7 days
    seven_days_ago = datetime.now() - timedelta(days=7)
    after_timestamp_ms = int(seven_days_ago.timestamp() * 1000)
    recently_played = sp.current_user_recently_played(limit=50, after=after_timestamp_ms)

    # Combine into one JSON
    combined_data = {
        "user_id": user_id,
        "display_name": display_name,
        "top_artists_short": top_artists_short,
        "top_artists_medium": top_artists_medium,
        "top_artists_long": top_artists_long,
        "top_tracks_short": top_tracks_short,
        "top_tracks_medium": top_tracks_medium,
        "top_tracks_long": top_tracks_long,
        "recently_played": recently_played
    }

    # Save & upload raw JSON to S3
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    local_file_name = f"user_spotify_data_{timestamp}.json"
    with open(local_file_name, 'w') as f:
        json.dump(combined_data, f, indent=2)

    # Upload
    raw_key = f"raw/{local_file_name}"
    upload_message = upload_to_s3(local_file_name, 'spotify-raw-data-dk', raw_key)

    return combined_data, upload_message, raw_key

# ------------- Spotify OAuth Helper ------------- #
def get_spotipy_oauth():
    """
    Returns a SpotifyOAuth object configured for your app:
      1) Removes old .cache to avoid reusing old tokens,
      2) Uses a unique cache_path to separate each new login session.
    """
    if os.path.exists(".cache"):
        os.remove(".cache")
    cache_path = f".cache_{uuid.uuid4()}"
    return SpotifyOAuth(
        client_id=os.environ.get('SPOTIFY_CLIENT_ID'),
        client_secret=os.environ.get('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True,
        open_browser=False,
        cache_path=cache_path
    )

# ------------- The Streamlit App Entry Point ------------- #
def main():
    st.title("Spotify Dashboard – Day vs Night, Mainstream Score, and More!")
    st.markdown("""
        This dashboard lets you connect to your Spotify account and see:
        - **Genre Distribution** in a pie chart
        - **Mainstream Score**
        - **Day vs. Night** listening habits
        - **Top 10 Artists** & **Top 10 Tracks** for different time ranges
        - **Daily Listening** stats for the past 7 days
    """)

    query_params = st.query_params

    if "code" in query_params:
        code = query_params["code"]
        sp_oauth = get_spotipy_oauth()

        with st.spinner("Authenticating with Spotify..."):
            try:
                token_info = sp_oauth.get_access_token(code)
                if not token_info or "access_token" not in token_info:
                    st.error("Could not retrieve valid token info from Spotify.")
                    return

                sp = spotipy.Spotify(auth=token_info["access_token"])
                raw_data, upload_message, raw_key = authenticate_and_extract(sp)
            except Exception as e:
                st.error(f"Error during Spotify authentication/extraction: {e}")
                return

        time.sleep(15)  # wait for data processing by your Lambda/backend

        processed_key = raw_key.replace("raw/", "processed/").replace(".json", ".processed.json")
        with st.spinner("Loading processed data..."):
            processed_data = fetch_processed_data(processed_key)
            if processed_data is None:
                st.error("Failed to load processed data from S3.")
                return

        # ------------------ SECTION 1: Genre Distribution ------------------ #
        with st.expander("View Genre Distribution", expanded=False):
            genres = processed_data.get("genres", {})
            genre_labels = genres.get("labels", [])
            genre_sizes = genres.get("sizes", [])
            if genre_labels and genre_sizes:
                fig, ax = plt.subplots()
                ax.pie(genre_sizes, labels=genre_labels, autopct='%1.1f%%', startangle=140)
                ax.axis('equal')
                st.pyplot(fig)
            else:
                st.info("No genre data found.")

        # ------------------ SECTION 2: Mainstream Score ------------------ #
        with st.expander("View Mainstream Score", expanded=False):
            mainstream_score = processed_data.get("mainstream_score", {})
            # For simplicity, you can show average scores across time ranges or allow selection.
            st.write("Your mainstream scores (average track popularity) are:")
            st.json(mainstream_score)

        # ------------------ SECTION 3: Day vs. Night ------------------ #
        with st.expander("View Day vs. Night Listening", expanded=False):
            day_vs_night = processed_data.get("day_vs_night", {})
            day_percent = day_vs_night.get("day_percent", 0)
            night_percent = day_vs_night.get("night_percent", 0)
            st.write(f"**{day_percent}%** of your listening is during the day, **{night_percent}%** at night.")
            if night_percent > day_percent:
                st.write("You’re a midnight music muncher! 🌙")
            else:
                st.write("You’re more of a daytime music star! ☀️")

        # ------------------ SECTION 4: Top 10 Artists ------------------ #
        st.subheader("Top 10 Artists")
        artist_time_range = st.selectbox(
            "Select Time Range for Top Artists",
            ("Recent (Short Term)", "Last 6 Months (Medium Term)", "All Time (Long Term)")
        )
        if artist_time_range == "Recent (Short Term)":
            top_artists = processed_data.get("top_artists_short", [])
        elif artist_time_range == "Last 6 Months (Medium Term)":
            top_artists = processed_data.get("top_artists_medium", [])
        else:
            top_artists = processed_data.get("top_artists_long", [])
        display_grid(top_artists, item_type="artist", columns_per_row=3)

        # ------------------ SECTION 5: Top 10 Tracks ------------------ #
        st.subheader("Top 10 Tracks")
        track_time_range = st.selectbox(
            "Select Time Range for Top Tracks",
            ("Recent (Short Term)", "Last 6 Months (Medium Term)", "All Time (Long Term)")
        )
        if track_time_range == "Recent (Short Term)":
            top_tracks = processed_data.get("top_tracks_short", [])
        elif track_time_range == "Last 6 Months (Medium Term)":
            top_tracks = processed_data.get("top_tracks_medium", [])
        else:
            top_tracks = processed_data.get("top_tracks_long", [])
        display_grid(top_tracks, item_type="track", columns_per_row=3)

        # ------------------ SECTION 6: Daily Listening ------------------ #
        with st.expander("View Daily Listening (Past 7 Days)", expanded=False):
            listening_time = processed_data.get("listening_time", {})
            labels = listening_time.get("daily_listening_labels", [])
            values = listening_time.get("daily_listening_values", [])
            if labels and values:
                df_listen = pd.DataFrame({"Date": labels, "Minutes": values}).set_index("Date")
                st.bar_chart(df_listen)
            else:
                st.info("No daily listening data found.")

        # ------------------ VIEW RAW AND PROCESSED DATA ------------------ #
        with st.expander("View Raw Spotify Data", expanded=False):
            st.json(raw_data)
        with st.expander("View Processed Data (Full JSON)", expanded=False):
            st.json(processed_data)

    else:
        st.subheader("Step 1: Authorize Spotify")
        sp_oauth = get_spotipy_oauth()
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(f"[Click here to **Login to Spotify**]({auth_url})")

if __name__ == "__main__":
    main()
