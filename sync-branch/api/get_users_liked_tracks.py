import requests
import json
import pyodbc
from util import fetch_user_profile
from cmd_gui_kit import CmdGUI
import logging
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

# Setup logging
LOG_FILE = "logs/get_users_liked_tracks.log"

# Create a logger
logger = logging.getLogger("SyncBranchLogger")
logger.setLevel(logging.DEBUG)

# Create file handler
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.propagate = False

gui = CmdGUI()

# Database connection details
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_CONNECTION_STRING = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_HOST},{DB_PORT};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD}"



def format_date(date_string):
    """Convert date string to SQL Server compatible format (YYYY-MM-DD)."""
    try:
        if date_string:
            # Parse and format the date
            return datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        logger.warning(f"Invalid date format: {date_string}. Using default date.")
    # Return a default date if parsing fails
    return None  # Or return a placeholder like '1900-01-01'

def insert_album_if_not_exists(track):
    """Ensure the album exists in the Albums table."""
    try:
        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            cursor = conn.cursor()
            
            # Extract album details
            album = track["track"]["album"]
            album_id = album["id"]
            name = album["name"]
            release_date_raw = album.get("release_date", None)
            release_date = format_date(release_date_raw)
            total_tracks = album.get("total_tracks", 0)  # Default to 0 if missing
            album_type = album.get("album_type", None)  # Allow NULL if missing
            album_href = album["href"]
            uri = album["uri"]

            # Check if the album exists in the Albums table
            cursor.execute("SELECT COUNT(*) FROM Albums WHERE album_id = ?", album_id)
            if cursor.fetchone()[0] == 0:
                # Insert the album into Albums table
                cursor.execute(
                    """
                    INSERT INTO Albums (album_id, name, release_date, total_tracks, album_type, album_href, uri)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    album_id, name, release_date, total_tracks, album_type, album_href, uri
                )
                conn.commit()
                logger.info(f"Inserted album {album_id} into Albums table.")
    except Exception as e:
        logger.error(f"Error inserting album {album_id}: {e}")
        gui.status(f"Error inserting album {album_id}: {e}", status="error")
        
        
def insert_track_if_not_exists(track):
    """Ensure the track exists in the Tracks table."""
    try:
        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            cursor = conn.cursor()
            
            # Insert album if not exists
            insert_album_if_not_exists(track)

            # Extract track details
            track_id = track["track"]["id"]
            name = track["track"]["name"]
            album_id = track["track"]["album"]["id"]
            duration_ms = track["track"]["duration_ms"]
            explicit = 1 if track["track"]["explicit"] else 0  # Convert boolean to bit
            popularity = track["track"].get("popularity", 0)  # Default to 0 if missing
            preview_url = track["track"].get("preview_url", None)  # Allow NULL
            track_href = track["track"]["href"]
            uri = track["track"]["uri"]

            # Check if the track exists in the Tracks table
            cursor.execute("SELECT COUNT(*) FROM Tracks WHERE track_id = ?", track_id)
            if cursor.fetchone()[0] == 0:
                # Insert the track into Tracks table
                cursor.execute(
                    """
                    INSERT INTO Tracks (track_id, name, album_id, duration_ms, explicit, popularity, preview_url, track_href, uri)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    track_id, name, album_id, duration_ms, explicit, popularity, preview_url, track_href, uri
                )
                conn.commit()
                logger.info(f"Inserted track {track_id} into Tracks table.")
    except Exception as e:
        logger.error(f"Error inserting track {track_id}: {e}")
        gui.status(f"Error inserting track {track_id}: {e}", status="error")

def insert_tracks_to_db(user_id, tracks):
    """Insert liked tracks into Users_Liked_Tracks table."""
    try:
        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            cursor = conn.cursor()
            
            for track in tracks:
                # Ensure the track and album exist
                insert_track_if_not_exists(track)

                # Extract relevant fields
                track_id = track["track"]["id"]
                liked_date = track["added_at"]

                # Insert into Users_Liked_Tracks
                cursor.execute(
                    """
                    INSERT INTO Users_Liked_Tracks (user_id, track_id, liked_date)
                    VALUES (?, ?, ?)
                    """,
                    user_id, track_id, liked_date
                )
            conn.commit()
        logger.info(f"Inserted {len(tracks)} tracks for user {user_id} into the database.")
        gui.log(f"Inserted {len(tracks)} tracks for user {user_id} into the database.", level="info")
    except Exception as e:
        logger.error(f"Error inserting tracks for user {user_id}: {e}")
        gui.status(f"Error inserting tracks for user {user_id}: {e}", status="error")

def fetch_user_saved_tracks(access_token):
    base_url = "https://api.spotify.com/v1/me/tracks"
    
    user_data = fetch_user_profile(access_token)
    user_id = user_data["user_id"]
    headers = {"Authorization": f"Bearer {access_token}"}
    total_tracks = []
    offset = 0
    limit = 50
    has_more = True

    while has_more:
        params = {"limit": limit, "offset": offset}
        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code == 403:
            gui.log("Permission Denied: Check token scopes.", level="warn")
            logger.info("Permission Denied: Check token scopes.")
            break
        elif response.status_code != 200:
            gui.status(f"{response.status_code} - {response.text}", status="error")
            logger.error(f"{response.status_code} - {response.text}")
            break

        data = response.json()
        items = data.get("items", [])
        total_tracks.extend(items)

        offset += limit
        has_more = len(items) == limit

    # Insert tracks into the database
    insert_tracks_to_db(user_id, total_tracks)

# Execute the function
def get_users_liked_tracks():
    try:
        with open("auth_tokens.json", "r") as f:
            tokens = json.load(f)
    except FileNotFoundError:
        gui.status("auth_tokens.json file not found.", status="error")
        logger.error("auth_tokens.json file not found.")
        return

    for token_entry in tokens:
        access_token = token_entry.get("access_token")
        fetch_user_saved_tracks(access_token)    

if __name__ == "__main__":
    get_users_liked_tracks()
