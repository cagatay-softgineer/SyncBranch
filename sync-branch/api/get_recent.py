import requests
import pyodbc
from datetime import datetime
import json
import base64
from dotenv import load_dotenv
import os
import sys

# Check if '--debug' is passed as a command-line argument
DEBUG_MODE = '--debug' in sys.argv
WARNING_MODE = '--warning' in sys.argv
ERROR_MODE = '--error' in sys.argv

#####
# 50 is Limit of Get Recent API.
# AVG Tracks time * (30-40) Minute is most accurate way to repeat this.
# AVG Tracks Time ~= 3 minute 47 sec. which is calculated from all fetched tracks data from database.
######

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_CONNECTION_STRING = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_HOST},{DB_PORT};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD}"

# Function to read the latest access token from auth_tokens.json
def get_all_tokens_with_user_ids():
    try:
        with open("auth_tokens.json", "r") as f:
            tokens = json.load(f)
            if tokens:
                # Return a list of dictionaries with user_id and access_token
                return [{"user_id": token["user_id"], "access_token": token["access_token"]} for token in tokens]
            else:
                raise Exception("[ERROR] No tokens found in auth_tokens.json.")
    except Exception as e:
        raise Exception(f"[ERROR] Error reading auth token: {e}")

# Function to check if the access token is valid
def is_token_valid(access_token):
    url = "https://api.spotify.com/v1/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    # If the token is valid, the status code should be 200
    if response.status_code == 200:
        return True
    elif response.status_code == 401:  # Unauthorized indicates expired/invalid token
        return False
    else:
        raise Exception(f"[ERROR] Unexpected error checking token validity: {response.status_code} - {response.text}")

# Function to refresh the access token
def refresh_access_token(refresh_token):
    url = "https://accounts.spotify.com/api/token"
    CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        new_token_data = response.json()
        new_access_token = new_token_data["access_token"]

        # Optionally update refresh token if Spotify provides a new one
        if "refresh_token" in new_token_data:
            refresh_token = new_token_data["refresh_token"]

        # Save the new access token to auth_tokens.json
        new_token_entry = {"access_token": new_access_token, "refresh_token": refresh_token}
        with open("auth_tokens.json", "w") as f:
            json.dump([new_token_entry], f, indent=4)  # Save as a list with the latest token
        if DEBUG_MODE:
            print("[DEBUG] Access token refreshed successfully.")
        return new_access_token
    else:
        raise Exception(f"[ERROR] Failed to refresh token: {response.status_code} - {response.text}")
    
# Function to check and insert user data
def check_and_insert_user(user_id, access_token):
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM Users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        url = "https://api.spotify.com/v1/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            display_name = user_data.get("display_name", "")
            email = user_data.get("email", "")
            profile_image_url = user_data["images"][0]["url"] if user_data.get("images") else ""
            country = user_data.get("country", "")

            cursor.execute("""
                INSERT INTO Users (user_id, display_name, email, profile_image_url, country)
                VALUES (?, ?, ?, ?, ?)
            """, user_id, display_name, email, profile_image_url, country)
            conn.commit()
        else:
            if DEBUG_MODE or ERROR_MODE:
                print(f"[WARNING] Failed to fetch user profile: {response.status_code} - {response.text}")
            return False
    cursor.close()
    conn.close()
    return True

# Function to check and insert album data
def check_and_insert_album(album_id, access_token):
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM Albums WHERE album_id = ?", (album_id,))
    if cursor.fetchone() is None:
        url = f"https://api.spotify.com/v1/albums/{album_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            album_data = response.json()
            release_date = album_data.get("release_date", None)

            cursor.execute("""
                INSERT INTO Albums (album_id, name, release_date, total_tracks, album_type, album_href, uri)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, album_id, album_data["name"], release_date, album_data.get("total_tracks", 0),
            album_data.get("album_type", ""), album_data.get("href", ""), album_data.get("uri", ""))
            conn.commit()
        else:
            if DEBUG_MODE or ERROR_MODE:
                print(f"[WARNING] Failed to fetch album data for album_id {album_id}: {response.status_code} - {response.text}")
            return False
    cursor.close()
    conn.close()
    return True

# Function to check and insert track data
def check_and_insert_track(track_id, album_id, access_token):
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM Tracks WHERE track_id = ?", (track_id,))
    if cursor.fetchone() is None:
        # Ensure album exists in Albums table before inserting the track
        if not check_and_insert_album(album_id, access_token):
            if DEBUG_MODE or ERROR_MODE:
                print(f"[WARNING] Failed to insert album for track {track_id}. Aborting track insertion.")
            return False

        url = f"https://api.spotify.com/v1/tracks/{track_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            track_data = response.json()

            cursor.execute("""
                INSERT INTO Tracks (track_id, name, album_id, duration_ms, explicit, popularity, preview_url, track_href, uri)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, track_id, track_data["name"], album_id, track_data["duration_ms"],
            int(track_data["explicit"]), track_data["popularity"], track_data["preview_url"],
            track_data["href"], track_data["uri"])
            conn.commit()
        else:
            if DEBUG_MODE or ERROR_MODE:
                print(f"[WARNING] Failed to fetch track data for track_id {track_id}: {response.status_code} - {response.text}")
            return False
    cursor.close()
    conn.close()
    return True

# Function to fetch recently played tracks
def get_recently_played_tracks(access_token):
    url = "https://api.spotify.com/v1/me/player/recently-played?limit=50"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()["items"]
    else:
        raise Exception(f"[ERROR] Error fetching recently played tracks: {response.status_code} - {response.text}")

# Function to insert recently played tracks
def insert_recently_played_tracks():
    user_tokens = get_all_tokens_with_user_ids()
    for user_token in user_tokens:
        user_id = user_token["user_id"]
        access_token = user_token["access_token"]
        
        # Check if the token is valid; refresh if necessary
        if not is_token_valid(access_token):
            if DEBUG_MODE or WARNING_MODE:
                print(f"[WARNING] Access token for user {user_id} is invalid or expired.")
            continue
        
        print(f"[INFO] Processing recently played tracks for user {user_id}.")
        
        if not check_and_insert_user(user_id, access_token):
            if DEBUG_MODE or WARNING_MODE:
                print(f"[WARNING] Failed to insert user {user_id}. Aborting.")
            continue
    
        tracks = get_recently_played_tracks(access_token)
    
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
    
        for item in tracks:
            track_id = item["track"]["id"]
            album_id = item["track"]["album"]["id"]
            played_at = datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
    
            # Ensure track and album exist before inserting into user_recent_tracks
            if check_and_insert_track(track_id, album_id, access_token):
                try:
                    cursor.execute("""
                        INSERT INTO user_recent_tracks (user_id, track_id, listened_at)
                        VALUES (?, ?, ?)
                    """, user_id, track_id, played_at)
                    conn.commit()
                except pyodbc.IntegrityError as e:  # noqa: F841
                    # Handle duplicate entry case
                    if DEBUG_MODE:
                        print(f"[DEBUG] Duplicate entry for user {user_id}, track {track_id} at {played_at}. Skipping.")
                    conn.rollback()  # Rollback if insertion fails

        cursor.close()
        conn.close()
        print(f"[INFO] Recently played tracks stored successfully for user {user_id}.")


# Main function
def main():
    try:
        insert_recently_played_tracks()
    except Exception as e:
        print(f"[ERROR] Error: {e}")

if __name__ == "__main__":
    main()
