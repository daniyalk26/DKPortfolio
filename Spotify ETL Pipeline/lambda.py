"""AWS Lambda handler utilities for processing Spotify listening data and storing aggregated metrics into an Amazon RDS (MySQL) instance.

Author: Daniyal Khalid
Created: 2025
"""

import os
import json
import boto3
import pymysql    # PyMySQL: pure-Python MySQL driver
from collections import Counter
from datetime import datetime

def store_in_rds(processed_data: dict) -> None:
    """
    Connects to the MySQL DB using pymysql, inserts user, daily listening,
    genre distribution, and top tracks into your MySQL RDS.
    """
    # Connect to your MySQL DB using environment variables (set these in Lambda)
    conn = pymysql.connect(
        host=os.environ["DB_HOST"],            # e.g., "dk.ct8kksg2ijto.us-east-2.rds.amazonaws.com"
        user=os.environ["DB_USER"],            # e.g., "dk"
        password=os.environ["DB_PASS"],        # e.g., "Hello123."
        database=os.environ["DB_NAME"],        # e.g., "dk"
        port=int(os.environ.get("DB_PORT", 3306)),
        connect_timeout=5
    )

    try:
        with conn.cursor() as cur:
            # Insert or update the user row
            user_id = processed_data.get("user_id", "unknown_user")
            display_name = processed_data.get("display_name", "Unknown Name")
            cur.execute("""
                INSERT INTO users (user_id, display_name)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE display_name = VALUES(display_name)
            """, (user_id, display_name))

            # Use today's UTC date as the record_date for snapshot data.
            record_date = datetime.utcnow().date()

            # Insert daily listening data
            listening_time = processed_data.get("listening_time", {})
            daily_labels = listening_time.get("daily_listening_labels", [])
            daily_values = listening_time.get("daily_listening_values", [])
            for date_str, minutes_listened in zip(daily_labels, daily_values):
                cur.execute("""
                    INSERT INTO user_daily_listening (user_id, listen_date, minutes_listened)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE minutes_listened = VALUES(minutes_listened)
                """, (user_id, date_str, minutes_listened))

            # Insert genre distribution snapshot
            genres = processed_data.get("genres", {})
            genre_labels = genres.get("labels", [])
            genre_sizes = genres.get("sizes", [])
            for g_label, g_count in zip(genre_labels, genre_sizes):
                cur.execute("""
                    INSERT INTO user_genres (user_id, genre, play_count, record_date)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE play_count = VALUES(play_count)
                """, (user_id, g_label, g_count, record_date))

            # Insert top tracks snapshot
            top_tracks = processed_data.get("top_tracks", [])
            for track in top_tracks:
                track_id = track.get("track_id", "")
                track_name = track.get("track_name", "")
                artist_name = track.get("artist_name", "")
                popularity = track.get("popularity", 0)
                track_rank = track.get("rank", 0)  # using key "rank" from processed_data
                cur.execute("""
                    INSERT INTO user_top_tracks
                      (user_id, track_id, track_name, artist_name, popularity, track_rank, record_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                      track_name = VALUES(track_name),
                      artist_name = VALUES(artist_name),
                      popularity = VALUES(popularity),
                      track_rank = VALUES(track_rank)
                """, (user_id, track_id, track_name, artist_name, popularity, track_rank, record_date))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error inserting into RDS: {e}")
        raise
    finally:
        conn.close()


def lambda_handler(event, context):
    print("Lambda function started")
    s3_client = boto3.client('s3')
    
    # Retrieve raw file details from the event
    raw_bucket = event['Records'][0]['s3']['bucket']['name']
    raw_key = event['Records'][0]['s3']['object']['key']
    print(f"Triggered by bucket: {raw_bucket}, key: {raw_key}")

    # Read the raw JSON file from S3
    try:
        response = s3_client.get_object(Bucket=raw_bucket, Key=raw_key)
        raw_data = json.loads(response['Body'].read())
        print("Successfully read raw data")
    except Exception as e:
        print(f"Error reading raw file: {e}")
        return {'statusCode': 500, 'body': str(e)}

    # Extract user_id and display_name (provided by authenticate_and_extract)
    user_id = raw_data.get("user_id", "unknown_user")
    display_name = raw_data.get("display_name", "Unknown")

    # ---------------- 1) Genre Distribution + Top 10 Artists ----------------
    top_artists_long = raw_data.get("top_artists_long", {})
    artist_items = top_artists_long.get("items", [])

    all_genres = []
    for artist_obj in artist_items:
        all_genres.extend(artist_obj.get("genres", []))
    if not all_genres:
        genre_part = {"message": "No genres found in the data."}
    else:
        genre_counts = Counter(all_genres)
        top_n = 10
        most_common = genre_counts.most_common(top_n)
        other_count = sum(count for genre, count in genre_counts.items() if genre not in dict(most_common))
        labels = [genre for genre, _ in most_common]
        sizes = [count for _, count in most_common]
        if other_count:
            labels.append("Other")
            sizes.append(other_count)
        genre_part = {"labels": labels, "sizes": sizes}

    top_10_artists = []
    for i, artist_obj in enumerate(artist_items[:10], start=1):
        artist_id_sp = artist_obj.get("id")
        artist_name_sp = artist_obj.get("name")
        images = artist_obj.get("images", [])
        artist_image = images[0]["url"] if images else None
        top_10_artists.append({
            "rank": i,
            "artist_id": artist_id_sp,
            "artist_name": artist_name_sp,
            "artist_image": artist_image
        })

    # ---------------- 2) Top 10 Tracks + Mainstream Score ----------------
    top_tracks_long = raw_data.get("top_tracks_long", {})
    track_items = top_tracks_long.get("items", [])
    top_10_tracks = []
    popularity_sum = 0
    popularity_count = 0
    for i, track_obj in enumerate(track_items[:10], start=1):
        track_id_sp = track_obj.get("id")
        track_name_sp = track_obj.get("name")
        popularity = track_obj.get("popularity", 0)
        popularity_sum += popularity
        popularity_count += 1
        artist_list = track_obj.get("artists", [])
        first_artist = artist_list[0]["name"] if artist_list else "Unknown"
        album_data = track_obj.get("album", {})
        album_imgs = album_data.get("images", [])
        album_image = album_imgs[0]["url"] if album_imgs else None
        top_10_tracks.append({
            "rank": i,
            "track_id": track_id_sp,
            "track_name": track_name_sp,
            "artist_name": first_artist,
            "album_image": album_image,
            "popularity": popularity
        })
    mainstream_score = popularity_sum / popularity_count if popularity_count > 0 else 0

    # ---------------- 3) Daily Listening + Day vs. Night ----------------
    recently_played = raw_data.get("recently_played", {})
    play_items = recently_played.get("items", [])
    daily_minutes = {}
    total_day_minutes = 0.0
    total_night_minutes = 0.0
    for item in play_items:
        played_at = item.get("played_at")
        track_info = item.get("track", {})
        duration_ms = track_info.get("duration_ms", 0)
        if played_at:
            try:
                dt = datetime.fromisoformat(played_at.replace("Z", "+00:00"))
                day_str = dt.strftime("%Y-%m-%d")
                daily_minutes[day_str] = daily_minutes.get(day_str, 0.0) + (duration_ms / 60000.0)
                hour = dt.hour
                mins_played = duration_ms / 60000.0
                if hour >= 22 or hour < 6:
                    total_night_minutes += mins_played
                else:
                    total_day_minutes += mins_played
            except:
                pass
    sorted_days = sorted(daily_minutes.keys())
    daily_listening_labels = sorted_days
    daily_listening_values = [round(daily_minutes[d], 1) for d in sorted_days]
    total_minutes = total_day_minutes + total_night_minutes
    if total_minutes > 0:
        day_percent = round((total_day_minutes / total_minutes) * 100, 1)
        night_percent = round((total_night_minutes / total_minutes) * 100, 1)
    else:
        day_percent = 0
        night_percent = 0

    processed_data = {
        "user_id": user_id,
        "display_name": display_name,
        "genres": genre_part,
        "top_artists": top_10_artists,
        "top_tracks": top_10_tracks,
        "listening_time": {
            "daily_listening_labels": daily_listening_labels,
            "daily_listening_values": daily_listening_values
        },
        "mainstream_score": mainstream_score,
        "day_vs_night": {
            "day_percent": day_percent,
            "night_percent": night_percent
        }
    }

    # (A) Insert data into MySQL RDS
    store_in_rds(processed_data)

    # (B) Upload processed JSON to S3
    processed_bucket = 'spotify-processed-data-dk'
    processed_key = raw_key.replace("raw/", "processed/").replace(".json", ".processed.json")
    try:
        s3_client.put_object(
            Bucket=processed_bucket,
            Key=processed_key,
            Body=json.dumps(processed_data),
            ContentType='application/json'
        )
        print("Successfully uploaded processed data")
    except Exception as e:
        print(f"Error uploading processed data: {e}")
        return {'statusCode': 500, 'body': str(e)}

    return {'statusCode': 200, 'body': "Transformation complete"}

