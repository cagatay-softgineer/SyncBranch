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
           msg.message_id,
           usr_sender.profile_picture
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
            "sender_picture": f"{message[6]}",
        }
        serialized_messages.append(serialized_message)

    # Return the response
    return jsonify(serialized_messages), 200

@messaging_bp.route('/mark', methods=['POST'])
@jwt_required()
def mark_message():
    try:
        # Parse incoming JSON data
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        message_id = data.get('message_id')
        status = data.get('is_read')  # Expecting '1' or '0'

        # Validate inputs
        if message_id is None or status is None:
            return jsonify({"error": "Missing 'message_id' or 'is_read'"}), 400

        if status not in [0, 1, "0", "1"]:
            return jsonify({"error": "'is_read' must be 0 or 1"}), 400

        # Convert status to integer (if needed)
        status = int(status)

        # Update the database
        query = "UPDATE messages SET is_read = ? WHERE message_id = ?"
        execute_query_with_logging(query, "flutter", (status, message_id))

        return jsonify({"message": f"Message {message_id} marked as {'read' if status == 1 else 'unread'}"}), 200
    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": str(e)}), 500
