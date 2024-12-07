import pyodbc
from fetch_playlist_image import fetch_and_insert_playlist_images
from cmd_gui_kit import CmdGUI
from dotenv import load_dotenv
from tqdm import tqdm
import os
import logging


# Setup logging
LOG_FILE = "logs/update_playlist_image.log"

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

# Initialize CmdGUI
gui = CmdGUI()

# Load environment variables
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

def get_playlist_ids(cursor, update_all=True):
    """
    Fetches playlist IDs from the database.

    Args:
        cursor (pyodbc.Cursor): Database cursor for executing SQL queries.
        update_all (bool): If True, fetch all playlists. If False, fetch only playlists without images.

    Returns:
        list: List of playlist IDs.
    """
    if update_all:
        query = "SELECT playlist_id FROM Playlists"
    else:
        query = "SELECT playlist_id FROM Playlists WHERE images IS NULL"
    cursor.execute(query)
    return [row[0] for row in cursor.fetchall()]

def update_all_playlist_images(update_all=True, debug_mode=False, warning_mode=False, error_mode=False):
    """
    Fetches playlist IDs from the database and updates their images.

    Args:
        update_all (bool): If True, update all playlists. If False, update only playlists without images.
        debug_mode (bool): If True, enable debug logs.
        warning_mode (bool): If True, enable warning logs.
        error_mode (bool): If True, enable error logs.
    """
    try:
        # Connect to the database
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
        gui.status("Connected to the database successfully.", status="success")
        logger.info("Connected to the database successfully.")

        # Get playlist IDs based on the update_all parameter
        playlist_ids = get_playlist_ids(cursor, update_all=update_all)
        gui.log(f"Found {len(playlist_ids)} playlists to update.", level="info")
        logger.info(f"Found {len(playlist_ids)} playlists to update.")

        # Use tqdm to add a progress bar
        for playlist_id in tqdm(playlist_ids, desc="Updating Playlists", unit="playlist"):
            gui.log(f"Processing playlist ID: {playlist_id}", level="info")
            logger.info(f"Processing playlist ID: {playlist_id}")
            fetch_and_insert_playlist_images(playlist_id, cursor, conn, debug_mode, warning_mode, error_mode)

        gui.status("Playlist images updated successfully.", status="success")
        logger.info("Playlist images updated successfully.")

    except pyodbc.Error as db_err:
        gui.status(f"Database error: {db_err}", status="error")
        logger.error(f"Database error: {db_err}")

    except Exception as e:
        gui.status(f"Unexpected error: {e}", status="error")
        logger.error(f"Unexpected error: {e}")

    finally:
        try:
            cursor.close()
            conn.close()
            gui.log("Database connection closed.", level="info")
            logger.info("Database connection closed.")
        except Exception:
            pass

if __name__ == "__main__":
    # Set update_all to True or False based on your preference
    UPDATE_ALL = False  # Change to True to update all playlists
    update_all_playlist_images(update_all=UPDATE_ALL, debug_mode=True, warning_mode=True, error_mode=True)
