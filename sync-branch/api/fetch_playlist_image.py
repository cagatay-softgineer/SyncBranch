from util import make_request
from cmd_gui_kit import CmdGUI
import logging
from dotenv import load_dotenv
import os
import sys

load_dotenv()

# Setup logging
LOG_FILE = "logs/fetch_playlist_image.log"

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

# Initialize CmdGUI for logging and status updates
gui = CmdGUI()

# Check if '--debug' is passed as a command-line argument
DEBUG_MODE = '--debug' in sys.argv
WARNING_MODE = '--warning' in sys.argv
ERROR_MODE = '--error' in sys.argv

DEBUG_MODE = os.getenv("DEBUG_MODE")
if DEBUG_MODE == "True":
    DEBUG_MODE = True

def fetch_and_insert_playlist_images(playlist_id, cursor, conn, debug_mode=DEBUG_MODE, warning_mode=WARNING_MODE, error_mode=ERROR_MODE):
    """
    Fetches the first image URL for a playlist from Spotify API and inserts it into the database.

    Args:
        playlist_id (str): The Spotify playlist ID.
        cursor (pyodbc.Cursor): Database cursor for executing SQL queries.
        conn (pyodbc.Connection): Database connection to commit transactions.
        debug_mode (bool): If True, enable debug logs.
        warning_mode (bool): If True, enable warning logs.
        error_mode (bool): If True, enable error logs.
    """
    try:
        # Fetch playlist details
        playlist_url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
        gui.spinner(duration=1, message=f"Fetching image for playlist ID: {playlist_id}")
        response = make_request(playlist_url, "Get Playlist")

        if response and response.status_code == 200:
            playlist_data = response.json()
            images = playlist_data.get("images", [])

            # Extract the first URL or set to None if no images are available
            first_image_url = images[0]["url"] if images else None

            if debug_mode:
                if first_image_url:
                    gui.log(f"Fetched image URL for playlist {playlist_id}: {first_image_url}", level="info")
                    logger.info(f"Fetched image URL for playlist {playlist_id}: {first_image_url}")
                else:
                    gui.log(f"No image found for playlist {playlist_id}.", level="warn")
                    logger.info(f"No image found for playlist {playlist_id}.")

            # Store the first image URL in the database
            cursor.execute("UPDATE Playlists SET images = ? WHERE playlist_id = ?", first_image_url, playlist_id)
            conn.commit()
            gui.status(f"Image for playlist {playlist_id} successfully updated in the database.", status="success")
            logger.info(f"Image for playlist {playlist_id} successfully updated in the database.")
        else:
            if error_mode:
                gui.status(
                logger.info(
                    f"Failed to fetch images for playlist {playlist_id}. "
                    f"Status: {response.status_code if response else 'No response'}"
                ))

    except Exception as e:
        if error_mode:
            gui.status(f"An unexpected error occurred while processing playlist {playlist_id}: {e}", status="error")
            logger.error(f"An unexpected error occurred while processing playlist {playlist_id}: {e}")
