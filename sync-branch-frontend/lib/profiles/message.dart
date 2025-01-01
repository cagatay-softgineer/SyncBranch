class Message {
  final int messageId;
  final String sender;
  final String receiver;
  final String message;
  final String timestamp;
  final bool isRead;
  final String senderpicture;

  Message({
    required this.messageId,
    required this.sender,
    required this.receiver,
    required this.message,
    required this.timestamp,
    required this.isRead,
    required this.senderpicture
  });

  // JSON'dan Message nesnesine dönüştürme
  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      messageId: int.tryParse(json['message_id'].toString()) ?? 0,
      sender: json['sender'] ?? '',
      receiver: json['receiver'] ?? '',
      message: json['message'] ?? '',
      timestamp: json['timestamp'] ?? '',
      isRead: json['is_read'].toString().toLowerCase() == 'true',
      senderpicture: json['sender_picture'] ?? '',
    );
  }
  static int compareByTimestamp(Message a, Message b) {
    return DateTime.parse(a.timestamp).compareTo(DateTime.parse(b.timestamp));
  }
  Map<String, dynamic> toJson() {
    return {
      'message_id': messageId,
      'sender': sender,
      'receiver': receiver,
      'message': message,
      'timestamp': timestamp,
      'is_read': isRead,
      'sender_picture': senderpicture,
    };
  }
}
