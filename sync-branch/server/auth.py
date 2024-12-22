from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required  # noqa: F401
from flask_limiter import Limiter
from flask_cors import CORS
from flask_limiter.util import get_remote_address
import bcrypt
from utils import execute_query_with_logging

auth_bp = Blueprint('auth', __name__)
limiter = Limiter(key_func=get_remote_address)

# Enable CORS for all routes in this blueprint
CORS(auth_bp, resources={r"/*": {"origins": "*"}})

@auth_bp.route('/register', methods=['POST', 'GET'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    spotify_user_id = data.get('spotify_id')

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    query = """
        INSERT INTO users (username, email, password_hash, spotify_user_id, created_at)
        VALUES (?, ?, ? , ?, GETDATE())
    """
    execute_query_with_logging(query, "flutter", (username, email, hashed_password.decode('utf-8'), spotify_user_id))
    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'OPTIONS':
        # Handle CORS preflight request
        return jsonify({"message": "CORS preflight successful"}), 200

    # Handle POST login logic
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        # Verify credentials
        query = "SELECT password_hash,username FROM users WHERE username = ?"
        rows = execute_query_with_logging(query, "flutter", params=(username,), fetch=True)

        if rows:
            stored_hashed_password = rows[0][0][0]
            user_id = rows[0][0][1]
            if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8')):
                access_token = create_access_token(identity=username)
                return jsonify({"access_token": access_token, "user_id": user_id}), 200

        return jsonify({"error": "Invalid username or password"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500