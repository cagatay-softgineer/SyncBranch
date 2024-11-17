import requests
import base64
from datetime import datetime
from flask import Flask, request, redirect, session, url_for
import urllib.parse
from dotenv import load_dotenv
import os

load_dotenv()

APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")
AUTH_CLIENT_ID = os.getenv("AUTH_CLIENT_ID")
AUTH_CLIENT_SECRET = os.getenv("AUTH_CLIENT_SECRET")
AUTH_REDIRECT_URI  = os.getenv("AUTH_REDIRECT_URI")


app = Flask(__name__)
app.secret_key = APP_SECRET_KEY   # Replace with your own secret key for session management

# Spotify credentials

#REDIRECT_URI = "http://localhost:8888/callback"  # Set to the same URL in your Spotify app settings

# Spotify scopes for the app's permissions
SCOPES = [
    "user-read-private",
    "user-read-email",
    "playlist-read-private",
    "user-read-recently-played",
    "user-top-read"
]

# Function to get Spotify authorization URL
def get_spotify_auth_url():
    auth_url = "https://accounts.spotify.com/authorize"
    params = {
        "client_id": AUTH_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": AUTH_REDIRECT_URI,
        "scope": " ".join(SCOPES)
    }
    # URL encode the parameters correctly
    url_params = urllib.parse.urlencode(params)
    return f"{auth_url}?{url_params}"

# Route to initiate Spotify login
@app.route("/")
def index():
    return redirect("/login")

# Route to initiate Spotify login
@app.route("/login")
def login():
    auth_url = get_spotify_auth_url()
    return redirect(auth_url)

# Callback route to handle Spotify's redirect after authorization
@app.route("/callback")
def callback():
    auth_code = request.args.get("code")
    if auth_code:
        # Exchange the authorization code for an access token
        token_data = get_access_token(auth_code)
        if token_data:
            session['access_token'] = token_data['access_token']
            session['refresh_token'] = token_data['refresh_token']
            session['expires_at'] = datetime.utcnow().timestamp() + token_data['expires_in']
            return redirect(url_for("profile"))
    return "Authorization failed", 400

# Function to exchange authorization code for an access token
def get_access_token(auth_code):
    token_url = "https://accounts.spotify.com/api/token"
    auth_str = f"{AUTH_CLIENT_ID}:{AUTH_CLIENT_SECRET}"
    auth_bytes = base64.b64encode(auth_str.encode("utf-8"))
    auth_header = f"Basic {auth_bytes.decode('utf-8')}"

    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": AUTH_REDIRECT_URI
    }
    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to get access token:", response.json())
        return None

# Example route to fetch user's Spotify profile
@app.route("/profile")
def profile():
    access_token = session.get('access_token')
    if not access_token:
        return redirect(url_for("login"))

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.spotify.com/v1/me", headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        return f"Hello, {user_data['display_name']}! <br>Email: {user_data['email']}"
    else:
        return f"Failed to retrieve profile: {response.status_code}", response.status_code

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8888)