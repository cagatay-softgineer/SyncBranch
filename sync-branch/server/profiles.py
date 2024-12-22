from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import execute_query_with_logging

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/view', methods=['GET'])
@jwt_required()
def view_profile():
    current_user = get_jwt_identity()
    query = """
        SELECT username, email, spotify_user_id, bio
        FROM users
        WHERE username = ?
    """
    user = execute_query_with_logging(query, "flutter", (current_user,), fetch=True)
    print(user)
    if user:
        user = user[0][0]
        return jsonify({
            "username": user[0],
            "email": user[1],
            "spotify_user_id": user[2],
            "bio" : user[3]
        }), 200
    return jsonify({"error": "User not found"}), 404

@profile_bp.route('/update', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user = get_jwt_identity()
    data = request.json
    new_email = data.get('email')
    new_spotify_user_id = data.get('spotify_user_id')

    query = """
        UPDATE users
        SET email = ?, spotify_user_id = ?
        WHERE username = ?
    """
    execute_query_with_logging(query, "flutter",(new_email, new_spotify_user_id, current_user))
    return jsonify({"message": "Profile updated successfully"}), 200
