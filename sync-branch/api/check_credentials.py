import requests
import base64
import time
import json
from datetime import datetime
from prettytable import PrettyTable
from dotenv import load_dotenv
import os

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

# Function to get an access token for a credential
def get_access_token(client_id, client_secret):
    client_creds_b64 = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    token_url = "https://accounts.spotify.com/api/token"
    token_data = {"grant_type": "client_credentials"}
    token_headers = {
        "Authorization": f"Basic {client_creds_b64}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(token_url, data=token_data, headers=token_headers)
    if response.status_code == 200:
        return response.json()["access_token"]
    elif response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 1))
        retry_time = datetime.utcfromtimestamp(time.time() + retry_after).strftime('%Y-%m-%d %H:%M:%S')
        return f"Rate-Limited; Retry at {retry_time}"
    else:
        return f"Error: {response.status_code}"

# Function to check the status of each API command with retry logic
def check_api_status(access_token, commands, max_retries=1):
    headers = {"Authorization": f"Bearer {access_token}"}
    status_results = {}

    for command, url in commands.items():
        retries = 0
        while retries < max_retries:
            test_url = url.replace("{track_id}", TRACK_ID) if "{track_id}" in url else url
            response = requests.get(test_url, headers=headers)

            if response.status_code == 200:
                status_results[command] = "Active"
                break  # Exit the retry loop if successful
            elif response.status_code == 429:
                # Handle rate limiting
                retry_after = int(response.headers.get("Retry-After", 1))
                retry_time = datetime.utcfromtimestamp(time.time() + retry_after).strftime('%Y-%m-%d %H:%M:%S')
                status_results[command] = f"Rate-Limited; Retry at {retry_time}"
                print(f"[WARNING] {command} is rate-limited. Retrying after {retry_after} seconds.")
                time.sleep(retry_after)
                retries += 1
            else:
                # For other errors, record the error status
                status_results[command] = f"Error: {response.status_code}"
                break  # Exit on non-429 errors

        if retries == max_retries:
            # After max retries, indicate failure
            status_results[command] = "Rate-Limited"

    return status_results

# Function to check each credential, print results in a table, and write to JSON file
def check_credentials_status(credentials=CREDENTIALS, commands=API_COMMANDS, output_file="api_status.json", silent=False):
    json_output = []
    results_dict = {}

    for credential in credentials:
        client_id = credential["client_id"]
        client_secret = credential["client_secret"]

        # Get access token and handle rate limit
        token_result = get_access_token(client_id, client_secret)
        
        if "Rate-Limited" in token_result or "Error" in token_result:
            # If rate-limited or error during token acquisition, replicate the message for each command
            status = {cmd: token_result for cmd in commands}
        else:
            # Use the access token to check API commands status with retry control
            status = check_api_status(token_result, commands)

        results_dict[client_id] = status
        json_output.append({"Client ID": client_id, "Status": status})
        continue
        
    token_result = SPOTIFY_TOKEN
    if "Rate-Limited" in token_result or "Error" in token_result:
            # If rate-limited or error during token acquisition, replicate the message for each command
        status = {cmd: token_result for cmd in commands}
    else:
        # Use the access token to check API commands status with retry control
        status = check_api_status(token_result, commands)

    results_dict["SPOTIFY"] = status
    json_output.append({"Client ID": "SPOTIFY", "Status": status})

    if not silent:
        # Print results in a table format
        table = PrettyTable()
        table.field_names = ["API Command"] + [cred["client_id"] for cred in credentials] + ["SPOTIFY"]

        for command in commands:
            row = [command] + [results_dict[cred["client_id"]].get(command, "N/A") for cred in credentials] + [results_dict["SPOTIFY"].get(command, "N/A")]
            table.add_row(row)

        print(f"[INFO]\n{table}")

    # Write the JSON output to a file
    with open(output_file, "w") as f:
        json.dump(json_output, f, indent=4)

def main():
    # Run the credential check and display status table
    check_credentials_status(silent=False)


if __name__ == "__main__":
    main()