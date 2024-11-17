from util import make_request
import pyodbc
import sys
from dateutil import parser

# Check if '--debug' is passed as a command-line argument
DEBUG_MODE = '--debug' in sys.argv
WARNING_MODE = '--warning' in sys.argv
ERROR_MODE = '--error' in sys.argv

def check_user_exists(user_id, cursor):
    """
    Checks if a user already exists in the database.

    Args:
        user_id (str): The Spotify user ID.
        cursor (pyodbc.Cursor): Database cursor for executing SQL queries.

    Returns:
        bool: True if the user exists, False otherwise.
    """
    cursor.execute("SELECT 1 FROM Users WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

def insert_user_data(user_id, headers, cursor, conn, debug_mode=DEBUG_MODE, warning_mode=WARNING_MODE, error_mode=ERROR_MODE):
    """
    Fetches user profile data from Spotify API and inserts it into the database.

    Args:
        user_id (str): The Spotify user ID.
        headers (dict): Authorization headers for Spotify API.
        cursor (pyodbc.Cursor): Database cursor for executing SQL queries.
        conn (pyodbc.Connection): Database connection to commit transactions.
    """
    user_url = f"https://api.spotify.com/v1/users/{user_id}"
    user_response = make_request(user_url, "Get User Profile")
    if user_response and user_response.status_code == 200:
        user_data = user_response.json()
        cursor.execute("""
        INSERT INTO Users (user_id, display_name, email, profile_image_url, country)
        VALUES (?, ?, ?, ?, ?)
        """, user_id, user_data.get("display_name"), user_data.get("email"),
        user_data.get("images", [{}])[0].get("url", "") if user_data.get("images") else "", user_data.get("country", ""))
        conn.commit()
        if debug_mode:
            print(f"[DEBUG] Inserted data for user {user_id}")
    else:
        if debug_mode or error_mode:
            print(f"[ERROR] Failed to fetch data for user {user_id}")
            
def check_and_insert_playlist(playlist, user_id, cursor, conn, debug_mode=DEBUG_MODE, warning_mode=WARNING_MODE, error_mode=ERROR_MODE):
    """
    Checks if a playlist exists in the database and inserts it if it doesn't.

    Args:
        playlist (dict): Playlist data from Spotify API.
        user_id (str): Spotify user ID to associate with the playlist.
        cursor (pyodbc.Cursor): Database cursor for executing SQL queries.
        conn (pyodbc.Connection): Database connection to commit transactions.
    """
    if not playlist:
        if debug_mode or warning_mode:
            print(f"[WARNING] Playlist data is None or empty for user {user_id}. Skipping.")
        return
    
    if playlist is None:
        if debug_mode or warning_mode:
            print(f"[WARNING] Playlist data is None or empty for user {user_id}. Skipping.")
        return

    try:
        
        # Check that 'id' exists and is not None before proceeding
        if playlist.get("id") is None:
            if debug_mode or warning_mode:
                print(f"[WARNING] Playlist data is missing 'id' for user {user_id}. Skipping.")
            return
        
        # Validate playlist fields
        playlist_id = playlist.get("id")
        playlist_name = playlist.get("name", "Unnamed Playlist")
        playlist_description = playlist.get("description", "")
        is_public = 1 if playlist.get("public", False) else 0
        is_collaborative = 1 if playlist.get("collaborative", False) else 0
        playlist_href = playlist.get("href", "")
        playlist_uri = playlist.get("uri", "")

        # Check if essential fields are missing
        if not playlist_id or not playlist_name:
            if debug_mode or warning_mode:
                print(f"[WARNING] Playlist data is missing essential fields for user {user_id}. Skipping.")
            return

        # Log details of the playlist for debugging
        if debug_mode:
            print(f"[DEBUG] Processing playlist: {playlist_name} (ID: {playlist_id})")

        # Insert playlist if not exists
        cursor.execute("SELECT 1 FROM Playlists WHERE playlist_id = ?", (playlist_id,))
        if cursor.fetchone() is None:
            cursor.execute("""
            INSERT INTO Playlists (playlist_id, name, description, is_public, collaborative, playlist_href, uri)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, playlist_id, playlist_name, playlist_description, is_public, is_collaborative, playlist_href, playlist_uri)
            conn.commit()
            if debug_mode:
                print(f"[DEBUG] Inserted new playlist: {playlist_name} (ID: {playlist_id})")

        # Associate user with playlist in User_Playlists table
        cursor.execute("SELECT 1 FROM User_Playlists WHERE user_id = ? AND playlist_id = ?", (user_id, playlist_id))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO User_Playlists (user_id, playlist_id) VALUES (?, ?)", user_id, playlist_id)
            conn.commit()
            if debug_mode:
                print(f"[DEBUG] Associated user {user_id} with playlist {playlist_id}")

    except (AttributeError, KeyError, TypeError) as e:
        if debug_mode or error_mode:
            print(f"[ERROR] Data issue encountered for user {user_id} while processing playlist {playlist.get('name', 'Unknown')}: {e}")
    except pyodbc.Error as db_err:
        if debug_mode or error_mode:
            print(f"[ERROR] Database error for user {user_id}: {db_err}")
                    
def fetch_and_insert_audio_features(track_ids, headers, cursor, conn, debug_mode=DEBUG_MODE, warning_mode=WARNING_MODE, error_mode=ERROR_MODE):
    """
    Fetches audio features for up to 100 track IDs in one request and inserts them into the database.

    Args:
        track_ids (list): List of track IDs to fetch audio features for.
        headers (dict): Authorization headers for Spotify API.
        cursor (pyodbc.Cursor): Database cursor for executing SQL queries.
        conn (pyodbc.Connection): Database connection to commit transactions.
        debug_mode (bool): If True, print debug information.
    """
    if not track_ids:
        if debug_mode:
            print("[DEBUG] No track IDs to process.")
        return  # No track IDs to process

    # Make a request for audio features in bulk (up to 100 track IDs)
    track_ids_string = ",".join(track_ids)
    audio_features_url = f"https://api.spotify.com/v1/audio-features?ids={track_ids_string}"

    if debug_mode:
        print(f"[DEBUG] Requesting audio features for {len(track_ids)} track IDs.")
        print(f"[DEBUG] Request URL: {audio_features_url}")

    response = make_request(audio_features_url, "Get Audio Features Batch")

    if response:
        if response.status_code == 200:
            audio_features_list = response.json().get("audio_features", [])
            if debug_mode:
                print(f"[DEBUG] Received audio features for {len(audio_features_list)} tracks.")

            for audio_features_data in audio_features_list:
                if audio_features_data:  # Ensure data is not None
                    track_id = audio_features_data.get("id")
                    if debug_mode:
                        print(f"[DEBUG] Inserting audio features for track ID: {track_id}")
                    cursor.execute("""
                    INSERT INTO Audio_Features (track_id, acousticness, danceability, energy, instrumentalness, liveness, loudness, speechiness, valence, tempo, track_key, mode, time_signature)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, track_id, audio_features_data.get("acousticness"), audio_features_data.get("danceability"),
                    audio_features_data.get("energy"), audio_features_data.get("instrumentalness"),
                    audio_features_data.get("liveness"), audio_features_data.get("loudness"),
                    audio_features_data.get("speechiness"), audio_features_data.get("valence"),
                    audio_features_data.get("tempo"), audio_features_data.get("key"),
                    audio_features_data.get("mode"), audio_features_data.get("time_signature"))
            conn.commit()
            if debug_mode:
                print(f"[DEBUG] Committed audio features for batch of {len(track_ids)} tracks.")
        else:
            if debug_mode or error_mode:
                print(f"[ERROR] Failed to fetch audio features. Status Code: {response.status_code}")
                print(f"[ERROR] Response: {response.text}")
    else:
        if debug_mode or error_mode:
            print("[ERROR] No response received for the request.")

def check_and_insert_track(track_item, playlist_id, headers, cursor, conn, track_buffer, max_buffer_size=100, debug_mode=DEBUG_MODE, warning_mode=WARNING_MODE, error_mode=ERROR_MODE):
    if not track_item or 'track' not in track_item or track_item['track'] is None:
        if debug_mode or warning_mode:
            print("[WARNING] Track data is None or unavailable, skipping this track.")
        return  # Skip if the track data is invalid

    track_info = track_item["track"]
    track_id = track_info.get("id")
    album_info = track_info.get("album", {})
    album_id = album_info.get("id")

    if not track_id:
        if debug_mode or warning_mode:
            print("[WARNING] Track ID is missing, skipping.")
        return  # Skip tracks with no valid ID

    if not album_id:
        if debug_mode or warning_mode:
            print(f"[WARNING] Skipping track {track_id} due to missing album_id.")
        return  # Skip this track if album_id is missing

    # Insert album into Albums table if not exists
    cursor.execute("SELECT 1 FROM Albums WHERE album_id = ?", (album_id,))
    if cursor.fetchone() is None:
        release_date = album_info.get("release_date", None)
        parsed_date = None
        if release_date:
            try:
                parsed_date = parser.parse(release_date).strftime('%Y-%m-%d')
            except ValueError:
                if debug_mode or warning_mode:
                    print(f"[WARNING] Invalid release date format for album {album_id}.")
        
        cursor.execute("""
        INSERT INTO Albums (album_id, name, release_date, total_tracks, album_type, album_href, uri)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, album_id, album_info.get("name"), parsed_date,
        album_info.get("total_tracks", 0), album_info.get("album_type", ""),
        album_info.get("href", ""), album_info.get("uri", ""))
        conn.commit()  # Commit the album insertion to ensure it is visible

    # Insert track into Tracks table if not exists
    cursor.execute("SELECT 1 FROM Tracks WHERE track_id = ?", (track_id,))
    if cursor.fetchone() is None:
        cursor.execute("""
        INSERT INTO Tracks (track_id, name, album_id, duration_ms, explicit, popularity, preview_url, track_href, uri)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, track_id, track_info.get("name"), album_id,
        track_info.get("duration_ms"), int(track_info.get("explicit", 0)),
        track_info.get("popularity", 0), track_info.get("preview_url"),
        track_info.get("href"), track_info.get("uri"))
        conn.commit()  # Commit the track insertion

    # Associate playlist with track in Playlist_Tracks table using provided playlist_id
    cursor.execute("SELECT 1 FROM Playlist_Tracks WHERE playlist_id = ? AND track_id = ?", (playlist_id, track_id))
    if cursor.fetchone() is None:
        cursor.execute("""
        INSERT INTO Playlist_Tracks (playlist_id, track_id, added_at)
        VALUES (?, ?, ?)
        """, playlist_id, track_id, track_item["added_at"])
        conn.commit()  # Commit the association