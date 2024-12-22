from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import execute_query_with_logging

messaging_bp = Blueprint('messaging', __name__)

@messaging_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    current_user = get_jwt_identity()
    data = request.json
    recipient_username = data.get('recipient')
    message = data.get('message')

    query = """
        INSERT INTO messages (sender_id, receiver_id, content, sent_at)
        VALUES (
            (SELECT user_id FROM users WHERE username = ?),
            (SELECT user_id FROM users WHERE username = ?),
            ?, GETDATE()
        )
    """
    execute_query_with_logging(query, "flutter", (current_user, recipient_username, message))
    return jsonify({"message": "Message sent successfully"}), 200


@messaging_bp.route('/retrieve', methods=['GET'])
@jwt_required()
def retrieve_messages():
    current_user = get_jwt_identity()  # Fetch current user's identity from JWT

    query = """
    SELECT msg.content, 
           usr_sender.username AS sender, 
           usr_receiver.username AS receiver, 
           msg.sent_at, 
           msg.is_read, 
           msg.message_id
    FROM messages msg
    JOIN users usr_sender ON usr_sender.user_id = msg.sender_id
    JOIN users usr_receiver ON usr_receiver.user_id = msg.receiver_id
    WHERE msg.sender_id = (SELECT user_id FROM users WHERE username = ?)
       OR msg.receiver_id = (SELECT user_id FROM users WHERE username = ?)
    ORDER BY msg.sent_at DESC;
    """
    messages, _ = execute_query_with_logging(
        query, 
        "flutter", 
        (current_user, current_user), 
        fetch=True
    )

    serialized_messages = []
    for message in messages:
        # Convert each row to a dictionary
        serialized_message = {
            "message": f"{message[0]}",
            "sender": f"{message[1]}",
            "receiver": f"{message[2]}",
            "timestamp": message[3].isoformat() if message[3] else None,  # Convert datetime to ISO string
            "is_read": f"{message[4]}",
            "message_id": f"{message[5]}",
        }
        serialized_messages.append(serialized_message)

    # Return the response
    return jsonify(serialized_messages), 200

@messaging_bp.route('/mark', methods=['POST'])
@jwt_required()
def mark_message():
    data = request.json
    message_id = data.get('message_id')
    status = data.get('is_read')  # '1' or '0'

    query = "UPDATE messages SET is_read = ? WHERE message_id = ?"
    execute_query_with_logging(query, "flutter", (status, message_id))
    return jsonify({"message": f"Message marked as {status}"}), 200
