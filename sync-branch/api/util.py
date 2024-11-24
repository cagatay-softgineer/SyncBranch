import requests
import base64
import time
import json
import os
from threading import Lock
import sys
from check_credentials import check_api_status
from dotenv import load_dotenv
from cmd_gui_kit import CmdGUI

gui = CmdGUI()

load_dotenv()

# Function to fetch user profile info (user_id, email, display_name) from Spotify API
def fetch_user_profile(access_token):
    url = "https://api.spotify.com/v1/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        return {
            "user_id": user_data["id"],
            "email": user_data.get("email"),
            "display_name": user_data.get("display_name")
        }
    else:
        if DEBUG_MODE or WARNING_MODE:
            gui.log(f"Failed to fetch user profile: {response.status_code} - {response.text}", level="warn")
        return None


credentials_str = os.getenv("CREDENTIALS")
api_commands_str = os.getenv("API_COMMANDS")

# Load CREDENTIALS from JSON string
if credentials_str:
    CREDENTIALS = json.loads(credentials_str)
else:
    CREDENTIALS = []

# Load API_COMMANDS from JSON string
if api_commands_str:
    API_COMMANDS = json.loads(api_commands_str)
else:
    API_COMMANDS = {}


# Check if '--debug' is passed as a command-line argument
DEBUG_MODE = '--debug' in sys.argv
WARNING_MODE = '--warning' in sys.argv
ERROR_MODE = '--error' in sys.argv

# File to track the status of API keys
STATUS_FILE = "api_status.json"
token_cache = {}  # Correctly declare this globally
lock = Lock()

# Load existing API status from a JSON file if it exists
def load_status_file():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    return []

# Function to update the status of an API key in the status file
# Function to update the status of an API key in the status file
def update_client_status(client_id, new_status_dict, debug_mode=DEBUG_MODE, warning_mode=WARNING_MODE, error_mode=ERROR_MODE):
    """
    Updates the entire status for a specific client in the JSON file.
    
    Args:
        client_id (str): The client ID to update.
        new_status_dict (dict): A dictionary containing the new statuses for the client.
    """
    try:
        # Load existing status data from the JSON file
        with open(STATUS_FILE, 'r') as f:
            status_data = json.load(f)

        # Iterate through the status data to find the matching client_id
        for entry in status_data:
            if entry["Client ID"] == client_id:
                # Replace the entire status with the new status dictionary
                entry["Status"] = new_status_dict
                break  # Exit the loop once the client is found

        # Save the updated status data back to the JSON file
        with open(STATUS_FILE, 'w') as f:
            json.dump(status_data, f, indent=4)
        if debug_mode:
            gui.log(f"Updated all statuses for client_id {client_id}.", level="info")

    except FileNotFoundError:
        if debug_mode or error_mode:
            gui.status(f"Status file {STATUS_FILE} not found. Cannot update client status.", status="error")
    except json.JSONDecodeError:
        if debug_mode or error_mode:
            gui.status(f"Failed to decode JSON from {STATUS_FILE}.", status="error")
    except Exception as e:
        if debug_mode or error_mode:
            gui.status(f"An unexpected error occurred: {e}", status="error")

# Function to check if an API key is marked as rate-limited
def is_key_rate_limited(client_id, request_type, debug_mode=DEBUG_MODE, warning_mode=WARNING_MODE, error_mode=ERROR_MODE):
    try:
        with open(STATUS_FILE, 'r') as f:
            status_data = json.load(f)
            for entry in status_data:
                if entry["Client ID"] == client_id and entry["Status"].get(request_type) == "Rate-Limited":
                    return True
    except FileNotFoundError:
        if debug_mode or error_mode:
            gui.status(f"Status file {STATUS_FILE} not found. Cannot check API key status.", status="error")
    return False

def get_active_key_for_request(request_type):
    """
    Get a client ID that has an 'Active' status for a specific request type.
    
    Args:
        request_type (str): The type of request for which the key is needed.

    Returns:
        dict or None: The credential dictionary of an available key or None if not found.
    """
    status_data = load_status_file()
    for cred_status in status_data:
        client_id = cred_status["Client ID"]
        if cred_status["Status"].get(request_type) == "Active":
            for cred in CREDENTIALS:
                if cred["client_id"] == client_id:
                    return cred
    return None

def get_access_token_for_request(request_type, debug_mode=DEBUG_MODE, warning_mode=WARNING_MODE, error_mode=ERROR_MODE):
    global token_cache

    # Initialize token cache for the request type if it doesn't exist
    if request_type not in token_cache:
        token_cache[request_type] = {'current_credential': None, 'tokens': {}}

    current_credential = token_cache[request_type]['current_credential']

    # Check if the current credential is still active
    if current_credential and not is_key_rate_limited(current_credential, request_type):
        if debug_mode:
            gui.log(f"Using cached token for client_id {current_credential} for request type: {request_type}", level="info")
        return token_cache[request_type]['tokens'][current_credential]

    # If no valid current credential, find a new one
    for credential in CREDENTIALS:
        client_id = credential["client_id"]
        client_secret = credential["client_secret"]

        # Skip if this client ID is marked as rate-limited
        if is_key_rate_limited(client_id, request_type):
            if debug_mode:
                gui.log(f"Skipping client_id {client_id} as it is marked 'Rate-Limited' for {request_type}.", level="info")
            continue

        # If token is already cached for this client ID, use it
        if client_id in token_cache[request_type]['tokens']:
            token_cache[request_type]['current_credential'] = client_id
            if debug_mode:
                gui.log(f"Using cached token for client_id {client_id} for request type: {request_type}", level="info")
            return token_cache[request_type]['tokens'][client_id]

        # Request a new access token for this client ID
        client_creds_b64 = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        token_url = "https://accounts.spotify.com/api/token"
        token_data = {"grant_type": "client_credentials"}
        token_headers = {
            "Authorization": f"Basic {client_creds_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        response = requests.post(token_url, data=token_data, headers=token_headers)
        
        if response.status_code == 200:
            response_data = response.json()
            access_token = response_data["access_token"]

            # Cache the token and set this credential as the current active one
            with lock:
                token_cache[request_type]['tokens'][client_id] = access_token
                token_cache[request_type]['current_credential'] = client_id

            # Update status to Active
            status_results = check_api_status(access_token, API_COMMANDS)
            update_client_status(client_id,status_results)
            if debug_mode:
                gui.log(f"New access token obtained using client_id {client_id} for request type: {request_type}", level="info")
            return access_token
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 1))
            status_results = check_api_status(access_token, API_COMMANDS)
            update_client_status(client_id,status_results)
            if debug_mode or warning_mode:
                gui.log(f"Rate limit exceeded for client_id {client_id}. Marked as 'Rate-Limited'. Retrying after {retry_after} seconds.", level="warn")
            time.sleep(retry_after)
        else:
            status_results = check_api_status(access_token, API_COMMANDS)
            update_client_status(client_id,status_results)
            if debug_mode or error_mode:
                gui.status(f"Failed to obtain token for client_id {client_id}. Status code: {response.status_code}", status="error")
                
    # If all credentials are exhausted, log and raise an exception
    if debug_mode or error_mode:
        gui.status(f"No valid tokens could be obtained for request type: {request_type}", status="error")
    raise Exception()

def make_request(url, request_type, max_retries=5, debug_mode=DEBUG_MODE, warning_mode=WARNING_MODE, error_mode=ERROR_MODE):
    """
    Makes a GET request to a specified URL with retry logic to handle rate limiting.

    Args:
        url (str): The API endpoint to request data from.
        request_type (str): The type of request being made.
        max_retries (int): The maximum number of retries if rate limiting occurs.

    Returns:
        requests.Response or None: The API response if successful, or None if not found.
    """
    access_token = get_access_token_for_request(request_type)
    headers = {"Authorization": f"Bearer {access_token}"}

    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response
        elif response.status_code == 404:
            if debug_mode or warning_mode:
                gui.log(f"Resource not found: {url}", level="info")
            return None  # Log and skip if resource is not found
        elif response.status_code == 429:
            # Rate limit exceeded, check `Retry-After` header
            retry_after = int(response.headers.get("Retry-After", 1))
            if debug_mode or warning_mode:
                gui.log(f"Rate limit exceeded. Waiting for {retry_after} seconds before retrying.", level="info")
            time.sleep(retry_after)

            # Get a new access token in case of rate limit
            access_token = get_access_token_for_request(request_type)
            headers["Authorization"] = f"Bearer {access_token}"
        else:
            response.raise_for_status()
    if debug_mode or error_mode:
        gui.status("Failed to fetch data after retries.", status="error")
    return None

# Example usage
# Replace 'API_COMMANDS' with your actual API command dictionary
# make_request(API_COMMANDS["Get Playlists"], "Get Playlists")
