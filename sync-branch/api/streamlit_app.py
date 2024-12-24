import streamlit as st
import pyodbc
import csv
import time
from dotenv import load_dotenv
import os
import logging

# ---- IMPORT YOUR CUSTOM MODULES HERE ---- #
from util import get_access_token_for_request
from db_operations import check_user_exists, insert_user_data
from playlist_operations import handle_playlists

# ---------------- LOGGING SETUP ---------------- #
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
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.propagate = False

# ---------------- LOAD ENV VARIABLES ---------------- #
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

CONNECTION_STRING = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={DB_HOST},{DB_PORT};"
    f"DATABASE={DB_NAME};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD}"
)

# ---------------- HELPER FUNCTIONS ---------------- #
def update_csv_status(csv_path, user_id):
    """Mark user_id as processed in the CSV file."""
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        rows = list(csv.DictReader(csvfile))

    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = rows[0].keys()
        csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
        csvwriter.writeheader()

        for row in rows:
            if row['user_id'] == user_id:
                row['processed'] = '1'
            csvwriter.writerow(row)

def process_user_data(
    user_id, conn, cursor, 
    debug_mode=False, 
    warning_mode=False, 
    error_mode=False, 
    update_mode=True
):
    """Process user data and handle playlists."""
    try:
        # Get an access token for the 'Get User Profile' request type
        access_token = get_access_token_for_request("Get User Profile")
        headers = {"Authorization": f"Bearer {access_token}"}

        # Check if user data already exists and insert if not
        if not check_user_exists(user_id, cursor):
            if debug_mode:
                st.info(f"Inserting data for new user: {user_id}")
                logger.info(f"Inserting data for new user: {user_id}")
            try:
                insert_user_data(user_id, headers, cursor, conn, update=update_mode)
            except AttributeError as e:
                if debug_mode or error_mode:
                    st.error(f"AttributeError for user {user_id} during data insertion: {e}")
                    logger.error(f"AttributeError for user {user_id} during data insertion: {e}")
                # Continue with playlist processing even if user insertion had an issue

        # Process playlists for the user
        if debug_mode:
            st.info(f"Handling playlists for user: {user_id}")
            logger.info(f"Handling playlists for user: {user_id}")
        try:
            handle_playlists(user_id, cursor, conn)
            return True  # Indicate successful processing
        except AttributeError as e:
            if debug_mode or error_mode:
                st.error(f"AttributeError for user {user_id} during playlist handling: {e}")
                logger.error(f"AttributeError for user {user_id} during playlist handling: {e}")
            return False

    except Exception as e:
        if debug_mode or error_mode:
            st.error(f"General error processing user {user_id}: {e}")
            logger.error(f"General error processing user {user_id}: {e}")
        return False

def main(
    csv_path, 
    debug_mode=False, 
    warning_mode=False, 
    error_mode=False, 
    update_mode=True
):
    """Main function to connect to DB, read CSV, and process user data."""

    # Connect to SQL Server
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        if debug_mode:
            st.success("Connected to the database successfully.")
            logger.info("Connected to the database successfully.")
    except pyodbc.Error as db_err:
        if debug_mode or error_mode:
            st.error(f"Database connection failed: {db_err}")
            logger.error(f"Database connection failed: {db_err}")
        return

    # Read user IDs from CSV file
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                user_id = row['user_id']
                processed = row.get('processed', '0')

                # Process only users who have not been processed
                if processed == '0':
                    st.info(f"Processing user: {user_id}")
                    logger.info(f"Processing user: {user_id}")
                    success = process_user_data(
                        user_id, conn, cursor,
                        debug_mode=debug_mode,
                        warning_mode=warning_mode,
                        error_mode=error_mode,
                        update_mode=update_mode
                    )
                    # Mark user as processed if successful
                    if success:
                        update_csv_status(csv_path, user_id)

    except FileNotFoundError:
        if debug_mode or error_mode:
            st.error(f"CSV file {csv_path} not found.")
            logger.error(f"CSV file {csv_path} not found.")
    except KeyError as key_err:
        if debug_mode or warning_mode:
            st.warning(f"CSV format error: Missing key {key_err}")
            logger.warning(f"CSV format error: Missing key {key_err}")
    except Exception as e:
        if debug_mode or error_mode:
            st.error(f"An error occurred while reading the CSV file: {e}")
            logger.error(f"An error occurred while reading the CSV file: {e}")
    finally:
        cursor.close()
        conn.close()
        if debug_mode:
            st.info("Database connection closed.")
            logger.info("Database connection closed.")

# ---------------- STREAMLIT APP ENTRY POINT ---------------- #
def run_streamlit_app():
    st.title("User Data Processing App")

    # --- User Interface Options --- #
    st.subheader("Configuration")
    csv_path = st.text_input("Enter path to CSV file:", value="user_ids.csv")
    debug_mode = st.checkbox("Debug Mode", value=False)
    warning_mode = st.checkbox("Warning Mode", value=False)
    error_mode = st.checkbox("Error Mode", value=False)
    update_mode = st.checkbox("Update Mode (If checked, update existing user data)", value=True)

    if st.button("Run Processing"):
        start_time = time.time()
        main(csv_path, debug_mode, warning_mode, error_mode, update_mode)
        end_time = time.time()
        st.success(
            f"Processing complete!\nExecution time: {end_time - start_time:.2f} seconds."
        )
        logger.info(
            f"Data for all users saved to the database.\nExecution time: {end_time - start_time:.2f} seconds."
        )

# The code that Streamlit will actually run:
if __name__ == "__main__":
    run_streamlit_app()
