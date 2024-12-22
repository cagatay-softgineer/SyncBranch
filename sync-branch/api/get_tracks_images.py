import requests
import pyodbc
from util import get_access_token_for_request
from tqdm import tqdm
from dotenv import load_dotenv
import os
import logging

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

CONNECTION_STRING = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_HOST},{DB_PORT};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD}"

# Setup logging
LOG_FILE = "logs/main.log"

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

def fetch_missing_track_images(cursor):
    """
    Fetch track IDs missing images from the database.
    """
    query = "SELECT track_id FROM Tracks WHERE images IS NULL"
    cursor.execute(query)
    return [row[0] for row in cursor.fetchall()]

def fetch_track_images_from_spotify(track_ids, access_token):
    """
    Fetch track images from Spotify API for a list of track IDs.
    """
    url = f"https://api.spotify.com/v1/tracks?ids={','.join(track_ids)}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        tracks_data = response.json().get("tracks", [])
        logger.info(f"Fetched {len(tracks_data)} track images from Spotify.")
        return {track["id"]: track["album"]["images"][0]["url"] if track["album"]["images"] else None for track in tracks_data}
    else:
        logger.error(f"Spotify API error: {response.status_code} - {response.text}")
        raise Exception(f"Spotify API error: {response.status_code} - {response.text}")

def update_track_images_in_db(track_images, cursor, conn):
    """
    Update the `Tracks` table with the retrieved track images.
    """
    for track_id, image_url in track_images.items():
        cursor.execute("UPDATE Tracks SET images = ? WHERE track_id = ?", image_url, track_id)
    conn.commit()
    logger.info(f"Updated images for {len(track_images)} tracks in the database.")

def update_missing_track_images():
    """
    Main function to fetch and update missing track images in the database.
    """
    logger.info("Starting the process to update missing track images...")
    conn = pyodbc.connect(CONNECTION_STRING)
    cursor = conn.cursor()

    try:
        missing_tracks = fetch_missing_track_images(cursor)
        if not missing_tracks:
            logger.info("No tracks are missing images.")
            return

        access_token = get_access_token_for_request("Get Tracks")
        batch_size = 50

        for i in tqdm(range(0, len(missing_tracks), batch_size), desc="Updating Track Images"):
            batch = missing_tracks[i:i + batch_size]
            try:
                track_images = fetch_track_images_from_spotify(batch, access_token)
                update_track_images_in_db(track_images, cursor, conn)
            except Exception as e:
                logger.error(f"Error processing batch {i // batch_size + 1}: {e}")

        logger.info("Track images updated successfully.")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        cursor.close()
        conn.close()
        logger.info("Database connection closed.")

if __name__ == "__main__":
    update_missing_track_images()