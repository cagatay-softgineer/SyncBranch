import pyodbc
import csv
import time
from util import get_access_token_for_request
from playlist_operations import handle_playlist
import sys
import os
from dotenv import load_dotenv

# Check if '--debug' is passed as a command-line argument
DEBUG_MODE = '--debug' in sys.argv
WARNING_MODE = '--warning' in sys.argv
ERROR_MODE = '--error' in sys.argv

load_dotenv()

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
            print(f"[DEBUG] Handling playlist: {playlist_id}")
        try:
            handle_playlist(playlist_id, cursor, conn)
        except AttributeError as e:
            if debug_mode or error_mode:
                print(f"[ERROR] AttributeError encountered for playlist {playlist_id} during processing: {e}")
            # Continue to the next playlist even if an error occurred

    except Exception as e:
        if debug_mode or error_mode:
            print(f"[ERROR] General error processing playlist {playlist_id}: {e}")

# Main function
def main(CSV_path, debug_mode=DEBUG_MODE, warning_mode=WARNING_MODE, error_mode=ERROR_MODE):
    # Connect to SQL Server
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        if debug_mode:
            print("[DEBUG] Connected to the database successfully.")
    except pyodbc.Error as db_err:
        if debug_mode or error_mode:
            print(f"[ERROR] Database connection failed: {db_err}")
        return

    # Read playlist IDs from CSV file
    try:
        with open(CSV_path, 'r') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                playlist_id = row['playlist_id']
                print(f"[INFO] Processing playlist: {playlist_id}")
                process_playlist_data(playlist_id, conn, cursor)
    except FileNotFoundError:
        if debug_mode or error_mode:
            print(f"[ERROR] CSV file {CSV_path} not found.")
    except KeyError as key_err:
        if debug_mode or warning_mode:
            print(f"[WARNING] CSV file format error: Missing key {key_err}")
    except Exception as e:
        if debug_mode or error_mode:
            print(f"[ERROR] An error occurred while reading the CSV file: {e}")
    finally:
        # Close the database connection
        cursor.close()
        conn.close()
        if debug_mode:
            print("[DEBUG] Database connection closed.")

if __name__ == "__main__":
    CSV_path = "playlist_ids.csv"
    start_time = time.time()
    main(CSV_path)
    end_time = time.time()
    print(f"[INFO] Data for all playlists saved to the database.\nExecution time: {end_time - start_time:.2f} seconds.")
