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
    current_user = get_jwt_identity()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    query = """
SELECT msg.content, usr.username, msg.sent_at, msg.is_read
FROM messages msg
JOIN users usr ON usr.user_id = msg.sender_id
WHERE msg.receiver_id = (SELECT user_id FROM users WHERE username = ?)
ORDER BY msg.sent_at DESC
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY;
    """
    messages,_ = execute_query_with_logging(query,"flutter", (current_user, (page - 1) * per_page, per_page), fetch=True)
    serialized_messages = []
    for message in messages:
        # Convert each Row to a dictionary or list
        serialized_message = {
            "message": message[0],
            "user_id": message[1],
            "timestamp": message[2],  # Convert datetime to ISO string
            "is_read" : message[3]
        }
        serialized_messages.append(serialized_message)
    # Return the response
    return jsonify({"messages": serialized_messages}), 200

@messaging_bp.route('/mark', methods=['POST'])
@jwt_required()
def mark_message():
    data = request.json
    message_id = data.get('message_id')
    status = data.get('is_read')  # '1' or '0'

    query = "UPDATE messages SET is_read = ? WHERE message_id = ?"
    execute_query_with_logging(query, "flutter", (status, message_id))
    return jsonify({"message": f"Message marked as {status}"}), 200
