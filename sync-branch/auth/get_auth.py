from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import requests
import os
import json
import base64
from dotenv import load_dotenv
import secrets
from fastapi.middleware.cors import CORSMiddleware


# Load environment variables from .env file
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Spotify credentials
CLIENT_ID = os.getenv("AUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv("AUTH_CLIENT_SECRET")
#REDIRECT_URI = os.getenv("REDIRECT_URI")

#server_ip = socket.gethostbyname(socket.gethostname())
#REDIRECT_URI = os.getenv("REDIRECT_URI", f"http://{server_ip}:8888/callback")
REDIRECT_URI = os.getenv("AUTH_REDIRECT_URI")

def generate_random_state(length=16):
    return secrets.token_hex(length)

# /login endpoint to initiate Spotify authorization
@app.get("/login")
def login():
    state = generate_random_state()
    scope = "user-read-recently-played user-read-private user-read-email playlist-read-private playlist-read-collaborative user-library-read user-top-read user-read-playback-state user-modify-playback-state user-read-currently-playing"
    
    auth_url = (
        f"https://accounts.spotify.com/authorize?"
        f"response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&scope={scope}&state={state}"
    )
    
    return RedirectResponse(url=auth_url)

# Helper function to get Spotify user profile
def get_user_profile(access_token):
    url = "https://api.spotify.com/v1/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Only attempt to parse JSON if content is present
        if response.content:
            try:
                return response.json()  # Parse JSON response if possible
            except json.JSONDecodeError:
                print("Error: Expected JSON response but received non-JSON content.")
                print(f"Response content (possibly empty or malformed): {response.text}")
                return None
        else:
            print("Error: Received empty response content with status 200.")
            return None
    else:
        # Handle non-200 responses with explicit checks for JSON content
        if response.content:
            try:
                # Try to parse the error response as JSON
                error_info = response.json()
                print(f"Error fetching user profile: {response.status_code} - {error_info}")
            except json.JSONDecodeError:
                # If parsing fails, log as plain text
                print(f"Error fetching user profile: {response.status_code}")
                print(f"Raw response content: {response.text}")
        else:
            # Log explicitly if there's no content at all
            print(f"Error fetching user profile: {response.status_code} - No content returned")
        
        return None

    
# Helper function to check if token is valid
def is_token_valid(access_token):
    url = "https://api.spotify.com/v1/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    return response.status_code == 200

# Function to refresh the access token
def refresh_access_token(refresh_token):
    url = "https://accounts.spotify.com/api/token"
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
        new_token_data = response.json()
        return new_token_data.get("access_token")
    else:
        print(f"Failed to refresh access token: {response.status_code} - {response.json()}")
        return None

# /callback endpoint to handle Spotify's response with the authorization code
@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "Authorization code not found"}

    # Prepare parameters for the token request
    token_url = "https://accounts.spotify.com/api/token"
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,  # Must match Spotify Developer Dashboard
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    response = requests.post(token_url, data=token_data, headers=token_headers)
    
    if response.status_code == 200:
        # Parse and return the token data
        token_info = response.json()
        access_token = token_info["access_token"]
        refresh_token = token_info.get("refresh_token")
        expires_in = token_info.get("expires_in")
        scope = token_info.get("scope")
        token_type = token_info.get("token_type")
        
        new_token = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "scope": scope,
        "token_type": token_type
        }

        # Load existing tokens if the file exists and is not empty
        if os.path.exists("auth_tokens.json") and os.path.getsize("auth_tokens.json") > 0:
            with open("auth_tokens.json", "r") as f:
                try:
                    tokens = json.load(f)
                    if not isinstance(tokens, list):
                        tokens = []  # Reset if file content is not a list
                except json.JSONDecodeError:
                    tokens = []  # Initialize an empty list if the file is not valid JSON
        else:
            tokens = []

        # Append the new token entry
        tokens.append(new_token)

        # Write the updated list back to the file as a JSON array
        with open("auth_tokens.json", "w") as f:
            json.dump(tokens, f, indent=4)

        print("Successfully obtained access token.")
        return {
        "success": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "scope": scope,
        "token_type": token_type
        }
    else:
        # Log the entire error response for debugging
        print(f"Failed to obtain access token, Status Code: {response.status_code}")
        try:
            error_info = response.json()
            print("Error response from Spotify:", json.dumps(error_info, indent=4))
        except json.JSONDecodeError:
            print("Error response content is not JSON:", response.text)

        return {"error": "Failed to obtain access token", "status_code": response.status_code}

    
# Enhanced function to get user profile with refresh functionality
def get_user_profile_with_refresh(access_token, refresh_token):
    # Try to get the user profile with the current access token
    profile = get_user_profile(access_token)
    if profile is not None:
        return profile
    
    # If the token was invalid, refresh it
    print("Access token may be expired, attempting to refresh...")
    new_access_token = refresh_access_token(refresh_token)
    
    if new_access_token:
        # Retry getting the user profile with the new access token
        profile = get_user_profile(new_access_token)
        if profile:
            return profile
        else:
            print("Failed to retrieve user profile even after refreshing the token.")
    else:
        print("Failed to refresh the access token.")
    
    return None

# Run the FastAPI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
