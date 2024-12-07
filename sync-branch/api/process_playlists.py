import pyodbc
import csv
import time
from util import get_access_token_for_request
from playlist_operations import handle_playlist
import sys
import os
from dotenv import load_dotenv
from cmd_gui_kit import CmdGUI
import logging


# Setup logging
LOG_FILE = "logs/process_playlists.log"

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

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

CONNECTION_STRING = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_HOST},{DB_PORT};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD}"

# Function to process playlist data
def process_playlist_data(playlist_id, conn, cursor, debug_mode=DEBUG_MODE, warning_mode=WARNING_MODE, error_mode=ERROR_MODE):
    try:
        # Get an access token for the 'Get Playlist' request type
        access_token = get_access_token_for_request("Get Playlist")
        headers = {"Authorization": f"Bearer {access_token}"}  # noqa: F841

        if debug_mode:
            gui.log(f"Handling playlist: {playlist_id}", level="info")
            logger.info(f"Handling playlist: {playlist_id}")
        try:
            handle_playlist(playlist_id, cursor, conn)
        except AttributeError as e:
            if debug_mode or error_mode:
                gui.status(f"AttributeError encountered for playlist {playlist_id} during processing: {e}", status="error")
                logger.error(f"AttributeError encountered for playlist {playlist_id} during processing: {e}")
            # Continue to the next playlist even if an error occurred

    except Exception as e:
        if debug_mode or error_mode:
            gui.status(f"General error processing playlist {playlist_id}: {e}", status="error")
            logger.error(f"General error processing playlist {playlist_id}: {e}")

# Main function
def main(CSV_path, debug_mode=DEBUG_MODE, warning_mode=WARNING_MODE, error_mode=ERROR_MODE):
    # Connect to SQL Server
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        if debug_mode:
            gui.log("Connected to the database successfully.", level="info")
            logger.info("Connected to the database successfully.")
    except pyodbc.Error as db_err:
        if debug_mode or error_mode:
            gui.status(f"Database connection failed: {db_err}", status="error")
            logger.error(f"Database connection failed: {db_err}")
        return

    # Read playlist IDs from CSV file
    try:
        with open(CSV_path, 'r') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                playlist_id = row['playlist_id']
                gui.log(f"Processing playlist: {playlist_id}", level="info")
                logger.info(f"Processing playlist: {playlist_id}")
                process_playlist_data(playlist_id, conn, cursor)
    except FileNotFoundError:
        if debug_mode or error_mode:
            gui.status(f"CSV file {CSV_path} not found.", status="error")
            logger.error(f"CSV file {CSV_path} not found.")
    except KeyError as key_err:
        if debug_mode or warning_mode:
            gui.log(f"CSV file format error: Missing key {key_err}", level="warn")
            logger.info(f"CSV file format error: Missing key {key_err}")
    except Exception as e:
        if debug_mode or error_mode:
            gui.status(f"An error occurred while reading the CSV file: {e}", status="error")
            logger.error(f"An error occurred while reading the CSV file: {e}")
    finally:
        # Close the database connection
        cursor.close()
        conn.close()
        if debug_mode:
            gui.log("Database connection closed.", level="info")
            logger.info("Database connection closed.")

if __name__ == "__main__":
    CSV_path = "playlist_ids.csv"
    start_time = time.time()
    main(CSV_path)
    end_time = time.time()
    gui.log(f"Data for all playlists saved to the database.\nExecution time: {end_time - start_time:.2f} seconds.", level="info")
    logger.info(f"Data for all playlists saved to the database.\nExecution time: {end_time - start_time:.2f} seconds.")
