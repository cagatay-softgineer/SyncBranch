from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import requests
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("JWT_SECRET_KEY")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# API Base URL (the backend server running on localhost:5000)
backend_url = 'http://localhost:8080'
# Route for the homepage (user dashboard after login)
@app.route('/')
def index():
    if not session.get("logged_in"):
        return redirect(url_for('login'))
    return render_template('index.html')

# Route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        response = requests.post(f'{backend_url}/auth/login', json={'username': username, 'password': password})
        
        print(response.text)
        print(response.status_code)
        if response.status_code == 200:
            data = response.json()
            token = data['access_token']
            session['logged_in'] = True
            session['username'] = username
            session['jwt_token'] = token  # Store JWT token in session
            return redirect(url_for('index'))
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    return render_template('login.html')

# Route to view user profile
@app.route('/profile')
def profile():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    token = session.get('jwt_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(f'{backend_url}/profile/view', headers=headers)
    if response.status_code == 200:
        profile_data = response.json()
        return render_template('profile.html', profile=profile_data)
    return jsonify({"error": "Failed to load profile"}), 400

# Route to update profile
@app.route('/profile/update', methods=['POST'])
def update_profile():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    token = session.get('jwt_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    email = request.form['email']
    spotify_user_id = request.form['spotify_user_id']
    response = requests.put(f'{backend_url}/profile/update', json={'email': email, 'spotify_user_id': spotify_user_id}, headers=headers)
    if response.status_code == 200:
        return redirect(url_for('profile'))
    return jsonify({"error": "Failed to update profile"}), 400

# Route to handle messaging
@app.route('/messaging', methods=['GET', 'POST'])
def messaging():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    token = session.get('jwt_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    if request.method == 'POST':
        recipient = request.form['recipient']
        message = request.form['message']
        response = requests.post(f'{backend_url}/messaging/send', json={'recipient': recipient, 'message': message}, headers=headers)
        if response.status_code == 200:
            return redirect(url_for('messaging'))

    response = requests.get(f'{backend_url}/messaging/retrieve', headers=headers)
    if response.status_code == 200:
        messages = response.json()['messages']
        print(messages)
        return render_template('messaging.html', messages=messages)
    return jsonify({"error": "Failed to load messages"}), 400

# Route to handle friend requests
@app.route('/friendship', methods=['GET', 'POST'])
def friendship():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    token = session.get('jwt_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    if request.method == 'POST':
        receiver_username = request.form['receiver_username']
        response = requests.post(f'{backend_url}/friendship/send', json={'receiver_username': receiver_username}, headers=headers)
        if response.status_code == 200:
            return redirect(url_for('friendship'))

    response = requests.get(f'{backend_url}/friendship/list', headers=headers)
    if response.status_code == 200:
        friend_requests = response.json()['requests']
        return render_template('friendship.html', requests=friend_requests)
    return jsonify({"error": "Failed to load friend requests"}), 400

@app.route('/logout')
def logout():
    if 'logged_in' in session:
        session['logged_in'] = False
        session['username'] = None
        session['jwt_token'] = None
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)
