from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import execute_query_with_logging

friendship_bp = Blueprint('friendship', __name__)

@friendship_bp.route('/send', methods=['POST'])
@jwt_required()
def send_friend_request():
    current_user = get_jwt_identity()
    data = request.json
    receiver_username = data.get('receiver_username')

    # Fetch user IDs for sender and receiver
    sender_query = "SELECT user_id FROM users WHERE username = ?"
    sender_user_id = execute_query_with_logging(sender_query, "flutter",(current_user,), fetch=True)[0][0]

    receiver_query = "SELECT user_id FROM users WHERE username = ?"
    receiver_user_id = execute_query_with_logging(receiver_query, "flutter",(receiver_username,), fetch=True)

    if not receiver_user_id:
        return jsonify({"error": "Receiver username not found"}), 404

    receiver_user_id = receiver_user_id[0][0]

    # Insert the friendship request
    query = """
        INSERT INTO friendship_requests (sender_user_id, receiver_user_id, status, created_at)
        VALUES (?, ?, 'pending', GETDATE())
    """
    execute_query_with_logging(query, "flutter", (sender_user_id, receiver_user_id))
    return jsonify({"message": "Friendship request sent"}), 200

@friendship_bp.route('/respond', methods=['POST'])
@jwt_required()
def respond_friend_request():
    data = request.json
    sender_username = data.get('sender_username')
    response = data.get('response')  # 'accept' or 'reject'
    current_user = get_jwt_identity()

    # Fetch user IDs for sender and receiver
    sender_query = "SELECT user_id FROM users WHERE username = ?"
    sender_user_id = execute_query_with_logging(sender_query, "flutter",(sender_username,), fetch=True)[0][0]

    receiver_query = "SELECT user_id FROM users WHERE username = ?"
    receiver_user_id = execute_query_with_logging(receiver_query, "flutter",(current_user,), fetch=True)[0][0]

    # Update the friendship request status
    status = 'accepted' if response == 'accept' else 'rejected'
    query = """
        UPDATE friendship_requests
        SET status = ?
        WHERE sender_user_id = ? AND receiver_user_id = ?
    """
    execute_query_with_logging(query, "flutter",(status, sender_user_id, receiver_user_id))
    if response == 'accept':
        query = """
            INSERT INTO friendships(user_id, friend_id, status, created_at)
        VALUES (?, ?, ?, GETDATE())
        """
        execute_query_with_logging(query, "flutter",(sender_user_id, receiver_user_id, status))
    
    return jsonify({"message": f"Friendship request {status}"}), 200

@friendship_bp.route('/list', methods=['GET'])
@jwt_required()
def list_friend_requests():
    current_user = get_jwt_identity()
    # Fetch the user_id of the current user
    receiver_query = "SELECT user_id FROM users WHERE username = ?"
    receiver_user_id = execute_query_with_logging(receiver_query, "flutter",(current_user,), fetch=True)[0][0]
    receiver_user_id = receiver_user_id[0]
    # Query friendship requests
    query = """
        SELECT u.username AS sender_username, f.status
        FROM friendships f
        JOIN users u ON f.friend_id = u.user_id
        WHERE f.user_id = ?
    """
    requests, _ = execute_query_with_logging(query, "flutter",(receiver_user_id,), fetch=True)
    
    # Format response
    formatted_requests = [
        {"sender_username": req[0], "status": req[1]} for req in requests
    ]
    return jsonify({"requests": formatted_requests}), 200
