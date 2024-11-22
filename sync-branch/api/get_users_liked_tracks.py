import requests
import json
from util import fetch_user_profile

def fetch_user_saved_tracks(access_token):
    base_url = "https://api.spotify.com/v1/me/tracks"
    
    user_data = fetch_user_profile(access_token)
    user_id = user_data["user_id"]
    headers = {"Authorization": f"Bearer {access_token}"}
    total_tracks = []
    offset = 0
    limit = 50
    has_more = True

    while has_more:
        params = {"limit": limit, "offset": offset}
        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code == 403:
            print("[WARNING] Permission Denied: Check token scopes.")
            break
        elif response.status_code != 200:
            print(f"[ERROR] {response.status_code} - {response.text}")
            break

        data = response.json()
        items = data.get("items", [])
        total_tracks.extend(items)

        offset += limit
        has_more = len(items) == limit

    with open(f"sync-branch/SavedTracks/{user_id}_saved_tracks.json", "w", encoding="utf-8") as file:
        json.dump(total_tracks, file, indent=4, ensure_ascii=False)
    print(f"[INFO] Total tracks saved : {len(total_tracks)} --> For User {user_id}")


# Execute the function
def get_users_liked_tracks():
    try:
        with open("auth_tokens.json", "r") as f:
            tokens = json.load(f)
    except FileNotFoundError:
        print("[ERROR] auth_tokens.json file not found.")
        return

    for token_entry in tokens:
        access_token = token_entry.get("access_token")
        fetch_user_saved_tracks(access_token)    

if __name__ == "__main__":
    get_users_liked_tracks()
