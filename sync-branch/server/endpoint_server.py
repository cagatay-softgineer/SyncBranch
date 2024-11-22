import pyodbc
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import padding
import secrets
from base64 import b64encode, b64decode
from dotenv import load_dotenv
import bcrypt
import datetime
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

load_dotenv()

app.config.from_pyfile('.env')

app.config['ENDPOINT_USERNAME'] = os.getenv("ENDPOINT_USERNAME")
app.config['ENDPOINT_PASSWORD'] = os.getenv("ENDPOINT_PASSWORD")

# Database connection configurations
app.config['PRIMARY_SQL_SERVER'] = os.getenv("PRIMARY_SQL_SERVER")
app.config['PRIMARY_SQL_SERVER_PORT'] = os.getenv("PRIMARY_SQL_SERVER_PORT")
app.config['PRIMARY_SQL_DATABASE'] = os.getenv("PRIMARY_SQL_DATABASE")
app.config['PRIMARY_SQL_USER'] = os.getenv("PRIMARY_SQL_USER")
app.config['PRIMARY_SQL_PASSWORD'] = os.getenv("PRIMARY_SQL_PASSWORD")

app.config['FLUTTER_SQL_SERVER'] = os.getenv("FLUTTER_SQL_SERVER")
app.config['FLUTTER_SQL_SERVER_PORT'] = os.getenv("FLUTTER_SQL_SERVER_PORT")
app.config['FLUTTER_SQL_DATABASE'] = os.getenv("FLUTTER_SQL_DATABASE")
app.config['FLUTTER_SQL_USER'] = os.getenv("FLUTTER_SQL_USER")
app.config['FLUTTER_SQL_PASSWORD'] = os.getenv("FLUTTER_SQL_PASSWORD")

app.config['SECRET_ENCODE_KEY'] = os.getenv("SECRET_ENCODE_KEY").encode()

app.config['PRIMARY_SQL_SERVER_CONNECTION_STRING'] = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={app.config['PRIMARY_SQL_SERVER']},{app.config['PRIMARY_SQL_SERVER_PORT']};DATABASE={app.config['PRIMARY_SQL_DATABASE']};UID={app.config['PRIMARY_SQL_USER']};PWD={app.config['PRIMARY_SQL_PASSWORD']}"
app.config['FLUTTER_SQL_SERVER_CONNECTION_STRING'] = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={app.config['FLUTTER_SQL_SERVER']},{app.config['FLUTTER_SQL_SERVER_PORT']};DATABASE={app.config['FLUTTER_SQL_DATABASE']};UID={app.config['FLUTTER_SQL_USER']};PWD={app.config['FLUTTER_SQL_PASSWORD']}"

# Email configuration (use actual SMTP server details)

app.config['SMTP_SERVER '] = os.getenv("SMTP_SERVER ")
app.config['SMTP_PORT'] = os.getenv("SMTP_PORT")
app.config['SMTP_USERNAME'] = os.getenv("SMTP_USERNAME")
app.config['SMTP_PASSWORD'] = os.getenv("SMTP_PASSWORD")
app.config['FROM_EMAIL'] = os.getenv("FROM_EMAIL")

# JWT configuration
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")  # Change to a secret key of your choice
jwt = JWTManager(app)

# AES-GCM encryption/decryption utilities
def derive_key(password: str, salt: bytes) -> bytes:
    """ Derive an encryption key from a password using PBKDF2-HMAC. """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256-bit key
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def encrypt_message(message: str, password: str) -> str:
    """ Encrypt the message using AES-GCM with a derived key and random salt. """
    salt = secrets.token_bytes(16)  # Generate a random salt
    key = derive_key(password, salt)  # Derive key from password and salt
    
    # Generate a random IV (Initialization Vector)
    iv = secrets.token_bytes(12)  # AES-GCM typically uses 12 bytes for the IV
    
    # Pad the message to make it a multiple of the block size
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(message.encode()) + padder.finalize()
    
    # Encrypt the message using AES-GCM
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    tag = encryptor.tag  # Authentication tag
    
    # Combine salt, IV, tag, and ciphertext into a single string and return as base64
    encrypted_data = salt + iv + tag + ciphertext
    return b64encode(encrypted_data).decode()

def decrypt_message(encrypted_message: str, password: str) -> str:
    """ Decrypt the encrypted message using AES-GCM. """
    encrypted_data = b64decode(encrypted_message)
    
    # Extract salt, IV, tag, and ciphertext
    salt = encrypted_data[:16]
    iv = encrypted_data[16:28]
    tag = encrypted_data[28:44]
    ciphertext = encrypted_data[44:]
    
    # Derive the key from the password and salt
    key = derive_key(password, salt)
    
    # Decrypt the message using AES-GCM
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Unpad the message
    unpadder = padding.PKCS7(128).unpadder()
    message = unpadder.update(padded_data) + unpadder.finalize()
    
    return message.decode()

# Function to create MSSQL database connection
def get_db_connection():
    conn = pyodbc.connect(app.config['PRIMARY_SQL_SERVER_CONNECTION_STRING'])
    return conn

# Function to get a connection to the Flutter database (second database)
def get_flutter_db_connection():
    conn = pyodbc.connect(app.config['FLUTTER_SQL_SERVER_CONNECTION_STRING'])
    return conn

# Endpoint to login and create access token
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    # Get the stored hashed password for the user from the database
    conn = get_flutter_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()

    if result is None:
        return jsonify(error="User not found"), 404

    stored_hashed_password = result[0]

    # Check if the entered password matches the stored hashed password
    if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8')):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify(error="Invalid credentials"), 401

# Registration
@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')
    spotify_user_id = request.json.get('spotify_user_id')
    email = request.json.get('email')

    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

    conn = get_flutter_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (username, password, spotify_user_id, email, created_at)
        VALUES (?, ?, ?, ?, GETDATE());
    """, (username, hashed_password.decode('utf-8'), spotify_user_id, email))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(message="User registered successfully"), 201

# User Profile - Get and Update
@app.route('/profile', methods=['GET', 'PUT'])
@jwt_required()
def profile():
    username = get_jwt_identity()
    if request.method == 'GET':
        conn = get_flutter_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username, email, spotify_user_id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            return jsonify({
                "username": user[0],
                "email": user[1],
                "spotify_user_id": user[2]
            }), 200
        else:
            return jsonify(error="User not found"), 404

    if request.method == 'PUT':
        new_email = request.json.get('email')
        new_spotify_user_id = request.json.get('spotify_user_id')
        
        conn = get_flutter_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET email = ?, spotify_user_id = ?
            WHERE username = ?
        """, (new_email, new_spotify_user_id, username))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify(message="Profile updated successfully"), 200

# Send Friendship Request
@app.route('/friendship/send', methods=['POST'])
@jwt_required()
def send_friend_request():
    sender_username = get_jwt_identity()
    receiver_username = request.json.get('receiver_username')

    conn = get_flutter_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO friendship_requests (sender_username, receiver_username, status, created_at)
        VALUES (?, ?, 'pending', GETDATE())
    """, (sender_username, receiver_username))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(message="Friendship request sent"), 200

# Accept or Reject Friendship Request
@app.route('/friendship/respond', methods=['POST'])
@jwt_required()
def respond_friend_request():
    sender_username = request.json.get('sender_username')
    response = request.json.get('response')  # 'accept' or 'reject'

    receiver_username = get_jwt_identity()

    if response == 'accept':
        status = 'accepted'
    else:
        status = 'rejected'

    conn = get_flutter_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE friendship_requests
        SET status = ?
        WHERE sender_username = ? AND receiver_username = ?
    """, (status, sender_username, receiver_username))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(message=f"Friendship request {status}"), 200

# Get Friendship Requests (Sent and Received)
@app.route('/friendship/requests', methods=['GET'])
@jwt_required()
def get_friendship_requests():
    username = get_jwt_identity()

    conn = get_flutter_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sender_username, status FROM friendship_requests WHERE receiver_username = ?
    """, (username,))
    requests = cursor.fetchall()
    cursor.close()
    conn.close()

    requests_list = [{"sender_username": req[0], "status": req[1]} for req in requests]

    return jsonify(requests=requests_list), 200

# Mark Message as Read/Unread
@app.route('/messages/status', methods=['POST'])
@jwt_required()
def message_status():
    message_id = request.json.get('message_id')
    status = request.json.get('status')  # 'read' or 'unread'

    conn = get_flutter_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE messages
        SET status = ?
        WHERE message_id = ?
    """, (status, message_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(message=f"Message marked as {status}"), 200

# Get User Notifications
@app.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    username = get_jwt_identity()

    conn = get_flutter_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT notification_text, notification_date, us.user_id FROM notifications nt, users us WHERE us.username = ? and us.user_id = nt.user_id ORDER BY notification_date DESC
    """, (username,))
    notifications = cursor.fetchall()
    cursor.close()
    conn.close()

    notification_list = [{
        "notification_text": notification[0],
        "notification_date": notification[1].strftime('%Y-%m-%d %H:%M:%S')
    } for notification in notifications]

    return jsonify(notifications=notification_list), 200

# Function to send the reset email
def send_email(to_email, email_type, dynamic_content=None):
    subject = ""
    
    # Email types with their corresponding subject and body templates
    if email_type == "reset_password":
        subject = "Sync Branch Password Reset"
        body = "Reset"

    elif email_type == "after_login":
        subject = "Welcome Back to Sync Branch!"
        body = "After Login"
        
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = app.config['FROM_EMAIL']
    msg['To'] = to_email

    try:
        with smtplib.SMTP(app.config['SMTP_SERVER'], app.config['SMTP_PORT']) as server:
            server.starttls()
            server.login(app.config['SMTP_USERNAME'], app.config['SMTP_PASSWORD'])
            server.sendmail(app.config['FROM_EMAIL'], app.config['to_email'], msg.as_string())
        print("Password reset email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Password Reset Request Endpoint
@app.route('/password/reset/request', methods=['POST'])
def reset_password_request():
    email = request.json.get('email')

    # Check if the email exists in the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    # If the user with the given email does not exist
    if user is None:
        return jsonify(error="User not found with that email address"), 404

    # Generate a JWT token for password reset (expires in 1 hour)
    reset_token = create_access_token(identity=email, expires_delta=datetime.timedelta(hours=1))

    # Send the reset email with the token
    send_email(email, "reset_password",reset_token)

    cursor.close()
    conn.close()

    return jsonify(message="Password reset link sent to email"), 200

@app.route('/password/reset', methods=['POST'])
def reset_password():
    token = request.json.get('token')
    new_password = request.json.get('new_password')

    # Try to decode the token
    try:
        # Decode the JWT token (validates and extracts the user identity)
        decoded_token = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        user_id = decoded_token['sub']  # Assuming the user_id is stored in 'sub' field

        # Hash the new password using bcrypt (for security)
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        # Connect to the database and update the user's password
        conn = get_flutter_db_connection()
        cursor = conn.cursor()

        # Update the password in the database using the user_id (not message_id)
        cursor.execute("""
            UPDATE users 
            SET password = ?
            WHERE user_id = ?
        """, (hashed_password.decode('utf-8'), user_id))
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify(message="Password updated successfully"), 200

    except jwt.ExpiredSignatureError:
        return jsonify(error="Token has expired"), 400
    except jwt.InvalidTokenError:
        return jsonify(error="Invalid token"), 400
    except Exception as e:
        return jsonify(error=f"Failed to reset password: {e}"), 400
    
    
if __name__ == '__main__':
    app.run(debug=True)