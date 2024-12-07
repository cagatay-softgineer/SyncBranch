import requests
import base64
import time
import json
from datetime import datetime
from prettytable import PrettyTable
from dotenv import load_dotenv
import os
import logging
from cmd_gui_kit import CmdGUI  # Import CmdGUI for visual feedback

# Initialize CmdGUI
gui = CmdGUI()

# Configure logging
LOG_FILE = "logs/spotify_api.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.propagate = False

load_dotenv()

SPOTIFY_TOKEN = os.getenv("SPOTIFY_TOKEN")
USER_ID = os.getenv("USER_ID")
TRACK_ID = os.getenv("TRACK_ID")
PLAYLIST_ID = os.getenv("PLAYLIST_ID")
ALBUM_ID = os.getenv("ALBUM_ID")
ARTISTS_ID = os.getenv("ARTISTS_ID")

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

formatted_api_commands = {key: value.format(
    USER_ID=USER_ID,
    TRACK_ID=TRACK_ID,
    PLAYLIST_ID=PLAYLIST_ID,
    ALBUM_ID=ALBUM_ID,
    ARTISTS_ID=ARTISTS_ID
) for key, value in API_COMMANDS.items()}

def get_access_token(client_id, client_secret, gui):
    client_creds_b64 = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    token_url = "https://accounts.spotify.com/api/token"
    token_data = {"grant_type": "client_credentials"}
    token_headers = {
        "Authorization": f"Basic {client_creds_b64}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    gui.spinner(duration=2, message="Requesting access token...")
    logger.debug("Requesting access token.")

    response = requests.post(token_url, data=token_data, headers=token_headers)
    if response.status_code == 200:
        logger.info("Access token successfully retrieved.")
        return response.json()["access_token"]
    elif response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 1))
        retry_time = datetime.utcfromtimestamp(time.time() + retry_after).strftime('%Y-%m-%d %H:%M:%S')
        logger.warning(f"Rate-limited. Retry at {retry_time}.")
        return f"Rate-Limited; Retry at {retry_time}"
    else:
        logger.error(f"Error retrieving access token: {response.status_code}")
        return f"Error: {response.status_code}"

def check_api_status(access_token, commands, max_retries=1, gui=None):
    headers = {"Authorization": f"Bearer {access_token}"}
    status_results = {}

    for command, url in commands.items():
        retries = 0
        while retries < max_retries:
            test_url = url.replace("{track_id}", TRACK_ID) if "{track_id}" in url else url
            response = requests.get(test_url, headers=headers)

            if response.status_code == 200:
                status_results[command] = "Active"
                logger.info(f"{command} is active.")
                break
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                retry_time = datetime.utcfromtimestamp(time.time() + retry_after).strftime('%Y-%m-%d %H:%M:%S')
                status_results[command] = f"Rate-Limited; Retry at {retry_time}"
                gui.log(f"{command} is rate-limited. Retrying after {retry_after} seconds.", level="warn")
                logger.warning(f"{command} is rate-limited. Retry at {retry_time}.")
                time.sleep(retry_after)
                retries += 1
            else:
                status_results[command] = f"Error: {response.status_code}"
                logger.error(f"Error with {command}: {response.status_code}")
                break

    return status_results

def check_credentials_status(credentials=CREDENTIALS, commands=formatted_api_commands, output_file="api_status.json", silent=False, gui=None):
    json_output = []
    results_dict = {}

    for credential in credentials:
        client_id = credential["client_id"]
        client_secret = credential["client_secret"]

        token_result = get_access_token(client_id, client_secret, gui)
        if "Rate-Limited" in token_result or "Error" in token_result:
            status = {cmd: token_result for cmd in commands}
        else:
            status = check_api_status(token_result, commands, gui=gui)

        results_dict[client_id] = status
        json_output.append({"Client ID": client_id, "Status": status})
        logger.debug(f"Checked API status for client_id: {client_id}.")

    if not silent:
        table = PrettyTable()
        table.field_names = ["API Command"] + [cred["client_id"] for cred in credentials]
        for command in commands:
            row = [command] + [results_dict[cred["client_id"]].get(command, "N/A") for cred in credentials]
            table.add_row(row)
        gui.log(f"\n{table}", level="info")
        logger.info(f"API status table: \n{table}")

    with open(output_file, "w") as f:
        json.dump(json_output, f, indent=4)
        logger.info(f"API status results saved to {output_file}.")

def main():
    logger.info("Starting credential check process.")
    check_credentials_status(silent=False, gui=gui)
    logger.info("Credential check process completed.")

if __name__ == "__main__":
    main()
