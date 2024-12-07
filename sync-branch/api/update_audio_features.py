import pyodbc
from db_operations import fetch_and_insert_audio_features
from tqdm import tqdm
import sys
import os
from dotenv import load_dotenv
from cmd_gui_kit import CmdGUI
import logging

# Setup logging
LOG_FILE = "logs/update_audio_features.log"

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

# Check if '--debug' is passed as a command-line argument
DEBUG_MODE = '--debug' in sys.argv
WARNING_MODE = '--warning' in sys.argv
ERROR_MODE = '--error' in sys.argv

load_dotenv()

DEBUG_MODE = os.getenv("DEBUG_MODE")
if DEBUG_MODE == "True":
    DEBUG_MODE = True

# Database connection settings
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_CONNECTION_STRING = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_HOST},{DB_PORT};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD}"

def fetch_tracks_missing_audio_features(cursor):
    """
    Fetches track IDs from the Tracks table that are missing in the Audio_Features table.

    Args:
        cursor (pyodbc.Cursor): Database cursor for executing SQL queries.

    Returns:
        list: List of track IDs that are missing audio features.
    """
    query = """
    SELECT t.track_id
    FROM Tracks t
    LEFT JOIN Audio_Features af ON t.track_id = af.track_id
    WHERE af.track_id IS NULL
    """
    cursor.execute(query)
    return [row[0] for row in cursor.fetchall()]

def check_and_update_audio_features(debug_mode=DEBUG_MODE, warning_mode=WARNING_MODE, error_mode=ERROR_MODE):
    """
    Checks the database for tracks that are missing audio features,
    fetches the missing audio features from the Spotify API, and updates the Audio_Features table.

    Args:
        debug_mode (bool): If True, print debug information.
    """
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()

    # Fetch track IDs that are missing audio features
    missing_audio_features_tracks = fetch_tracks_missing_audio_features(cursor)

    if debug_mode:
        gui.log(f"Found {len(missing_audio_features_tracks)} tracks missing audio features.", level="info")
        logger.info(f"Found {len(missing_audio_features_tracks)} tracks missing audio features.")

    # Process tracks in batches to avoid rate limiting
    batch_size = 100
    for i in tqdm(range(0, len(missing_audio_features_tracks), batch_size), desc="Processing missing audio features", unit="batch"):
        track_batch = missing_audio_features_tracks[i:i + batch_size]
        fetch_and_insert_audio_features(track_batch, None, cursor, conn, debug_mode)

    cursor.close()
    conn.close()
    gui.status("Finished updating missing audio features.", status="success")
    logger.info("Finished updating missing audio features.")

def main():
    # Run the audio feature check and update function
    check_and_update_audio_features()

if __name__ == "__main__":
    main()
