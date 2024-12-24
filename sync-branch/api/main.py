import pyodbc
import csv
import time
from util import get_access_token_for_request
from db_operations import check_user_exists, insert_user_data
from playlist_operations import handle_playlists
import sys
from dotenv import load_dotenv
import os
from cmd_gui_kit import CmdGUI
import logging

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

gui = CmdGUI()

# Check if '--debug' is passed as a command-line argument
DEBUG_MODE = '--debug' in sys.argv
WARNING_MODE = '--warning' in sys.argv
ERROR_MODE = '--error' in sys.argv
UPDATE_MODE = '--upt' in sys.argv

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

# Function to process user data and playlists
def process_user_data(user_id, conn, cursor, debug_mode=DEBUG_MODE, warning_mode=WARNING_MODE, error_mode=ERROR_MODE, UPDATE = True):
    try:
        # Get an access token for the 'Get User Profile' request type
        access_token = get_access_token_for_request("Get User Profile")
        headers = {"Authorization": f"Bearer {access_token}"}

        # Check if user data already exists and insert if not
        if not check_user_exists(user_id, cursor):
            if debug_mode:
                gui.log(f"Inserting data for new user: {user_id}", level="info")
                logger.info(f"Inserting data for new user: {user_id}")
            try:
                insert_user_data(user_id, headers, cursor, conn, update=UPDATE)
            except AttributeError as e:
                if debug_mode or error_mode:
                    gui.status(f"AttributeError encountered for user {user_id} during data insertion: {e}", status="error")
                    logger.error(f"AttributeError encountered for user {user_id} during data insertion: {e}")
                # Continue with processing playlists even if an error occurred

        # Process playlists for the user
        if debug_mode:
            gui.log(f"Handling playlists for user: {user_id}", level="info")
            logger.info(f"Handling playlists for user: {user_id}")
        try:
            handle_playlists(user_id, cursor, conn)
            return True  # Indicate successful processing
        except AttributeError as e:
            if debug_mode or error_mode:
                gui.status(f"AttributeError encountered for user {user_id} during playlist handling: {e}", status="error")
                logger.error(f"AttributeError encountered for user {user_id} during playlist handling: {e}")
            return False

    except Exception as e:
        if debug_mode or error_mode:
            gui.status(f"General error processing user {user_id}: {e}", status="error")
            logger.error(f"General error processing user {user_id}: {e}")
        return False

# Update processed status in CSV file
def update_csv_status(CSV_path, user_id):
    with open(CSV_path, 'r') as csvfile:
        rows = list(csv.DictReader(csvfile))

    with open(CSV_path, 'w', newline='') as csvfile:
        fieldnames = rows[0].keys()
        csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
        csvwriter.writeheader()

        for row in rows:
            if row['user_id'] == user_id:
                row['processed'] = '1'
            csvwriter.writerow(row)

# Main function
def main(CSV_path, debug_mode=DEBUG_MODE, warning_mode=WARNING_MODE, error_mode=ERROR_MODE, update_mode = UPDATE_MODE):
    # Connect to SQL Server
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        if debug_mode:
            gui.status("Connected to the database successfully.", status="success")
            logger.info("Connected to the database successfully.")
    except pyodbc.Error as db_err:
        if debug_mode or error_mode:
            gui.status(f"Database connection failed: {db_err}", status="error")
            logger.error(f"Database connection failed: {db_err}")
        return

    # Read user IDs from CSV file
    try:
        with open(CSV_path, 'r') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                user_id = row['user_id']
                processed = row.get('processed', '0')

                # Process only users who have not been processed
                if processed == '0':
                    gui.log(f"Processing user: {user_id}", level="info")
                    logger.info(f"Processing user: {user_id}")
                    success = process_user_data(user_id, conn, cursor, UPDATE=update_mode)

                    # Mark user as processed if successful
                    if success:
                        update_csv_status(CSV_path, user_id)

    except FileNotFoundError:
        if debug_mode or error_mode:
            gui.status(f"CSV file {CSV_path} not found.", status="error")
            logger.error(f"CSV file {CSV_path} not found.")
    except KeyError as key_err:
        if debug_mode or warning_mode:
            gui.status(f"CSV file format error: Missing key {key_err}", status="warning")
            logger.warning(f"CSV file format error: Missing key {key_err}")
    except Exception as e:
        if debug_mode or error_mode:
            gui.status(f"An error occurred while reading the CSV file: {e}", status="error")
            logger.error(f"An error occurred while reading the CSV file: {e}")
    finally:
        cursor.close()
        conn.close()
        if debug_mode:
            gui.status("Database connection closed.", status="info")
            logger.info("Database connection closed.")

if __name__ == "__main__":
    CSV_path = "user_ids.csv"
    start_time = time.time()
    main(CSV_path)
    end_time = time.time()
    gui.status(f"Data for all users saved to the database.\nExecution time: {end_time - start_time:.2f} seconds.", status="success")
    logger.info(f"Data for all users saved to the database.\nExecution time: {end_time - start_time:.2f} seconds.")
