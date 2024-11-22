import json
import requests
import os
import base64
from dotenv import load_dotenv
import sys

# Check if '--debug' is passed as a command-line argument
DEBUG_MODE = '--debug' in sys.argv
WARNING_MODE = '--warning' in sys.argv
ERROR_MODE = '--error' in sys.argv

load_dotenv()

# Function to check if token entry has user_id
def has_user_id(token_entry):
    return "user_id" in token_entry and token_entry["user_id"]

# Function to check if an access token is valid
def is_token_valid(access_token):
    url = "https://api.spotify.com/v1/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    return response.status_code == 200

# Function to refresh access token using the refresh token
def refresh_access_token(refresh_token):
    url = "https://accounts.spotify.com/api/token"
    CLIENT_ID = os.getenv("AUTH_CLIENT_ID")
    CLIENT_SECRET = os.getenv("AUTH_CLIENT_SECRET")
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"], response.json().get("refresh_token", refresh_token)
    else:
        if DEBUG_MODE or WARNING_MODE:
            print(f"[WARNING] Failed to refresh token: {response.status_code} - {response.text}")
        return None, None

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
            print(f"[WARNING] Failed to fetch user profile: {response.status_code} - {response.text}")
        return None

# Function to update auth_tokens.json with user_id if missing, refresh expired tokens, and ensure one token per user_id
# Additionally, save new users' email and full name to newbie.json
def update_auth_tokens():
    try:
        with open("auth_tokens.json", "r") as f:
            tokens = json.load(f)
    except FileNotFoundError:
        print("auth_tokens.json file not found.")
        return

    # Load existing entries in newbie.json
    if os.path.exists("newbie.json"):
        with open("newbie.json", "r") as f:
            new_users = json.load(f)
    else:
        new_users = []

    updated_tokens = {}
    for token_entry in tokens:
        access_token = token_entry.get("access_token")
        refresh_token = token_entry.get("refresh_token")

        # Check if token is valid; refresh if needed
        if not is_token_valid(access_token):
            if DEBUG_MODE:
                print("[DEBUG] Access token expired. Refreshing...")
            access_token, refresh_token = refresh_access_token(refresh_token)
            if access_token:
                token_entry["access_token"] = access_token
                token_entry["refresh_token"] = refresh_token
            else:
                if DEBUG_MODE or WARNING_MODE:
                    print("[WARNING] Could not refresh access token. Skipping entry.")
                continue

        # Fetch user profile and add user_id, email, and display_name if missing
        if not has_user_id(token_entry):
            user_profile = fetch_user_profile(access_token)
            if user_profile:
                token_entry["user_id"] = user_profile["user_id"]
                print(f"[INFO] Added user_id {user_profile['user_id']} to token.")

                # Check if this user is new (not in newbie.json)
                if user_profile not in new_users:
                    new_user_info = {
                        "user_id": user_profile["user_id"],
                        "email": user_profile["email"],
                        "display_name": user_profile["display_name"]
                    }
                    new_users.append(new_user_info)
                    print(f"[INFO] Added new user to newbie.json: {new_user_info}")
            else:
                if WARNING_MODE:
                    print("[WARNING] Could not fetch user profile for an entry. Skipping...")
                continue

        # Ensure only one token per user_id, keeping the latest token if duplicates exist
        user_id = token_entry["user_id"]
        updated_tokens[user_id] = token_entry

    # Write the unique tokens list back to auth_tokens.json
    with open("auth_tokens.json", "w") as f:
        json.dump(list(updated_tokens.values()), f, indent=4)
    print("[INFO] auth_tokens.json updated successfully.")

    # Write new users' information to newbie.json
    with open("newbie.json", "w") as f:
        json.dump(new_users, f, indent=4)
    print("[INFO] newbie.json updated with new user details.")

# Main function to run the update process
if __name__ == "__main__":
    update_auth_tokens()
