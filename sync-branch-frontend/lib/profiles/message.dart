class Message {
  final int messageId;
  final String sender;
  final String receiver;
  final String message;
  final String timestamp;
  final bool isRead;

  Message({
    required this.messageId,
    required this.sender,
    required this.receiver,
    required this.message,
    required this.timestamp,
    required this.isRead,
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
    );
  }
  static int compareByTimestamp(Message a, Message b) {
    return DateTime.parse(a.timestamp).compareTo(DateTime.parse(b.timestamp));
  }
}
