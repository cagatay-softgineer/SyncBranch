import 'package:flutter/material.dart';
import 'chat_services.dart';
import 'message.dart';
import 'dart:async';
import 'package:syncbranch/services/api_service.dart';
import 'package:syncbranch/login_pages/auto_scroll_to_end.dart';
import 'spotify_embed_helper.dart';

Widget buildMessageContent(String message) {
  final regex = RegExp(
    r'https://open\.spotify\.com(/intl-[\w-]+)?/(track|artist|playlist)/([\w\d?=&]+)',
    caseSensitive: false,
  );

  if (regex.hasMatch(message)) {
    //print(message);
    return CustomSpotifyEmbed(embedUrl: message); // Use the embed widget
  } else {
    return Text(
      message,
      style: const TextStyle(fontSize: 16),
    );
  }
}

class MessagingScreen extends StatefulWidget {
  final String baseUrl;
  final String displayName;
  final ApiService apiService;

  const MessagingScreen(
      {Key? key,
      required this.baseUrl,
      required this.displayName,
      required this.apiService})
      : super(key: key);

  @override
  _MessagingScreenState createState() => _MessagingScreenState();
}

class _MessagingScreenState extends State<MessagingScreen> {
  final ChatServices _chatServices = ChatServices();
  late Future<List<Message>> _messagesFuture;
  Timer? _refreshTimer;
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController =
      ScrollController(); // Scroll Controller

  @override
  void initState() {
    super.initState();
    _messagesFuture = _loadAllMessages();
    _startAutoRefresh();

    // Sayfa açıldığında en alta kaydır
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scrollToBottom();
    });
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.jumpTo(_scrollController.position.maxScrollExtent);
    }
  }

  void _startAutoRefresh() {
    _refreshTimer = Timer.periodic(const Duration(seconds: 60), (timer) {
      setState(() {
        _messagesFuture = _loadAllMessages();
        _scrollToBottom();
      });

      WidgetsBinding.instance.addPostFrameCallback((_) {
        _scrollToBottom(); // Yenileme sonrası en alta kaydır
      });
    });
  }

Future<List<Message>> _loadAllMessages() async {
  final allMessages = await _chatServices.fetchMessages();

  // Filter messages related to the current user
  final filteredMessages = allMessages.where((message) {
    return message.sender == widget.displayName ||
        message.receiver == widget.displayName;
  }).toList();

  // Sort messages by timestamp
  filteredMessages.sort(Message.compareByTimestamp);
  //print("FILTERED MESSAGES : ${filteredMessages.map((m) => m.toJson()).toList()}");

  // Mark unread messages as read
  for (var message in filteredMessages) {
    //print("#######################################################");
    //print(message.receiver);
    //print(message.isRead);
    //print(message.messageId);
    //print(message.messageId.toString());
    //print("#######################################################");

    if (!message.isRead && message.sender == widget.displayName) {
      try {
        //print('Marking message as read: ${message.messageId}');
        await _chatServices.markMessageAsRead(message.messageId.toString());
        //message.isRead = true; // Update local state to reflect change
      } catch (e) {
        print('Failed to mark message as read: $e');
      }
    }
  }

  return filteredMessages;
}



  Future<void> _sendMessage() async {
    final messageText = _messageController.text.trim();
    //print(messageText);
    if (messageText.isNotEmpty) {
      //print("widget ${widget.displayName}");
      final success =
          await _chatServices.sendMessage(widget.displayName, messageText);
      //print(success);
      if (success) {
        setState(() {
          _messagesFuture = _loadAllMessages();
        });

        _messageController.clear();
        WidgetsBinding.instance.addPostFrameCallback((_) {
          _scrollToBottom(); // Mesaj gönderildikten sonra en alta kaydır
        });
      }
    }
  }

 @override
Widget build(BuildContext context) {
  return WillPopScope(
    onWillPop: () async {
      Navigator.pop(context, true); // Notify MainScreen of updates
      return false; // Prevent default pop behavior
    },
    child: Scaffold(
      appBar: AppBar(
        title: Text('Mesajlar (${widget.displayName})'),
      ),
      body: Column(
        children: [
          Expanded(
            child: FutureBuilder<List<Message>>(
              future: _messagesFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                } else if (snapshot.hasError) {
                  return Center(child: Text('Hata: ${snapshot.error}'));
                } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                  return const Center(
                      child: Text('Bu kullanıcıdan mesaj yok.'));
                } else {
                  final messages = snapshot.data!;
                  return ListView.builder(
                    itemCount: messages.length,
                    itemBuilder: (context, index) {
                      final message = messages[index];
                      final isSentByUser = message.sender == widget.displayName;

                      return Align(
                        alignment: isSentByUser
                            ? Alignment.centerLeft
                            : Alignment.centerRight,
                        child: Container(
                          margin: const EdgeInsets.symmetric(
                              vertical: 5, horizontal: 10),
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: isSentByUser
                                ? const Color(0xffbbc2c8)
                                : const Color(0xff6e7ccd),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              buildMessageContent(message.message),
                              const SizedBox(height: 5),
                              Text(
                                message.timestamp,
                                style: const TextStyle(
                                    fontSize: 12, color: Colors.black54),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  );
                }
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    decoration: const InputDecoration(
                      hintText: 'Mesajınızı yazın...',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: _sendMessage,
                ),
              ],
            ),
          ),
        ],
      ),
    ),
  );
}
}