import 'package:flutter/material.dart';
import 'chat_services.dart';
import 'message.dart';
import 'dart:async';
import 'package:syncbranch/services/api_service.dart';
import 'package:syncbranch/login_pages/auto_scroll_to_end.dart';

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
    _refreshTimer = Timer.periodic(const Duration(seconds: 10), (timer) {
      setState(() {
        _messagesFuture = _loadAllMessages();
      });

      WidgetsBinding.instance.addPostFrameCallback((_) {
        _scrollToBottom(); // Yenileme sonrası en alta kaydır
      });
    });
  }

  Future<List<Message>> _loadAllMessages() async {
    final allMessages = await _chatServices.fetchMessages();

    // Sadece current user ile ilgili mesajları filtrele
    final filteredMessages = allMessages.where((message) {
      return message.sender == widget.displayName ||
          message.receiver == widget.displayName;
    }).toList();

    // Mesajları zaman damgasına göre sırala
    filteredMessages.sort(Message.compareByTimestamp);
    return filteredMessages;
  }

  Future<void> _sendMessage() async {
    final messageText = _messageController.text.trim();
    print(messageText);
    if (messageText.isNotEmpty) {
      print("widget ${widget.displayName}");
      final success =
          await _chatServices.sendMessage(widget.displayName, messageText);
      print(success);
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
    return Scaffold(
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
                    controller: _scrollController, // Controller ekledik
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
                                ? Color(0xffbbc2c8)
                                : Color(0xff6e7ccd),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                message.message,
                                style: const TextStyle(fontSize: 16),
                              ),
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
    );
  }
}