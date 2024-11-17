import pyodbc
import csv
import time
from util import get_access_token_for_request
from db_operations import check_user_exists, insert_user_data
from playlist_operations import handle_playlists
import sys
from dotenv import load_dotenv
import os

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

# Function to process user data and playlists
def process_user_data(user_id, conn, cursor, debug_mode=DEBUG_MODE, warning_mode=WARNING_MODE, error_mode=ERROR_MODE):
    try:
        # Get an access token for the 'Get User Profile' request type
        access_token = get_access_token_for_request("Get User Profile")
        headers = {"Authorization": f"Bearer {access_token}"}

        # Check if user data already exists and insert if not
        if not check_user_exists(user_id, cursor):
            if debug_mode:
                print(f"[DEBUG] Inserting data for new user: {user_id}")
            try:
                insert_user_data(user_id, headers, cursor, conn)
            except AttributeError as e:
                if debug_mode or error_mode:
                    print(f"[ERROR] AttributeError encountered for user {user_id} during data insertion: {e}")
                # Continue with processing playlists even if an error occurred

        # Process playlists for the user
        if debug_mode:
            print(f"[DEBUG] Handling playlists for user: {user_id}")
        try:
            handle_playlists(user_id, cursor, conn)
            return True  # Indicate successful processing
        except AttributeError as e:
            if debug_mode or error_mode:
                print(f"[ERROR] AttributeError encountered for user {user_id} during playlist handling: {e}")
            # Continue to the next step even if an error occurred
            return False

    except Exception as e:
        if debug_mode or error_mode:
            print(f"[ERROR] General error processing user {user_id}: {e}")
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

    # Read user IDs from CSV file
    try:
        with open(CSV_path, 'r') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                user_id = row['user_id']
                processed = row.get('processed', '0')

                # Process only users who have not been processed
                if processed == '0':
                    print(f"[INFO] Processing user: {user_id}")
                    success = process_user_data(user_id, conn, cursor)

                    # Mark user as processed if successful
                    if success:
                        update_csv_status(CSV_path, user_id)

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
    CSV_path = "user_ids.csv"
    start_time = time.time()
    main(CSV_path)
    end_time = time.time()
    print(f"[INFO] Data for all users saved to the database.\nExecution time: {end_time - start_time:.2f} seconds.")
