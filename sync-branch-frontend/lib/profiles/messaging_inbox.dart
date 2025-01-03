// sender_list_screen.dart
import 'package:flutter/material.dart';
import 'package:syncbranch/services/api_service.dart';
import 'messaging_screen.dart';
import 'package:syncbranch/authlib.dart';
import 'message.dart';
import 'chat_services.dart';
import 'dart:async';
import 'package:intl/intl.dart';

class SenderListScreen extends StatefulWidget {
  final String baseUrl;

  const SenderListScreen({Key? key, required this.baseUrl}) : super(key: key);

  @override
  _SenderListScreenState createState() => _SenderListScreenState();
}

class _SenderListScreenState extends State<SenderListScreen> {
  final ChatServices _chatServices = ChatServices();
  late Future<List<Message>> _messagesFuture;
  Timer? _refreshTimer;
  String currentUserId = ""; // Default value to avoid null issues

  @override
  void initState() {
    super.initState();
    _initialize();
    _messagesFuture = _chatServices.fetchMessages();
    _startAutoRefresh();
  }

  Future<void> _initialize() async {
    await _loadCurrentUserId();
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }
  String _formatTimestamp(String timestamp) {
    try {
      final DateTime parsedDate = DateTime.parse(timestamp);
      final DateFormat formatter = DateFormat('yyyy-MM-dd HH:mm');
      return formatter.format(parsedDate);
    } catch (e) {
      return timestamp; // Return raw value if parsing fails
    }
  }

  Future<void> _loadCurrentUserId() async {
    try {
      currentUserId = await AuthService.getUserId() ?? "";
      //print("aaa $currentUserId");
    } catch (e) {
      //print("Error loading user ID: $e");
      currentUserId = "";
    }
  }

  void _startAutoRefresh() {
    _refreshTimer = Timer.periodic(const Duration(seconds: 10), (timer) {
      setState(() {
        _messagesFuture = _chatServices.fetchMessages();
      });
    });
  }

  @override
  Widget build(BuildContext context) {

    return Scaffold(
      body: Stack(
        children: [
          // Gradient Background
          Container(
            width: double.infinity,
            height: double.infinity,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Color.fromRGBO(2, 0, 36, 1),
                  Color.fromRGBO(20, 15, 77, 1),
                  Color.fromRGBO(58, 16, 133, 1),
                  Color.fromRGBO(106, 17, 203, 1),
                  Color.fromRGBO(198, 25, 198, 1),
                ],
              ),
            ),
          ),
      FutureBuilder<List<Message>>(
        future: _messagesFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text('Hata: ${snapshot.error}'));
          } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return const Center(child: Text('Mesaj yok.'));
          } else {
            final messages = snapshot.data!;
            final Map<String, Message> latestMessages = {};

            // Her göndericinin son mesajını bul
            for (var message in messages) {
              if (message.sender != currentUserId &&
                  !latestMessages.containsKey(message.sender)) {
                latestMessages[message.sender] = message;
              } else {
                //print("-----------Mesaj-----------");
                //print(message.sender);
                //print("---------------------------");
                //print("---------------------------");
                //print(currentUserId);
                //print("---------------------------");
              }
            }

            final List<Message> sendersLastMessages =
                latestMessages.values.toList();
            //print("as $sendersLastMessages");

            return ListView.builder(
  itemCount: sendersLastMessages.length,
  itemBuilder: (context, index) {
    final message = sendersLastMessages[index];

    // Calculate the number of unread messages for this sender
    final int unreadCount = messages
        .where((msg) => msg.sender == message.sender && !msg.isRead)
        .length;

    return ListTile(
      leading: Stack(
        children: [
          CircleAvatar(
            backgroundImage: message.senderpicture.isNotEmpty
                ? NetworkImage(message.senderpicture)
                : const AssetImage(
                        'https://sync-branch.yggbranch.dev/assets/default_user.png')
                    as ImageProvider,
            radius: 24,
          ),
          if (unreadCount > 0)
            Positioned(
              right: 0,
              top: 0,
              child: Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: Colors.red,
                  shape: BoxShape.circle,
                ),
                child: Text(
                  '$unreadCount',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
        ],
      ),
      title: Text(
        'Gönderen: ${message.sender}',
        style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
      ),
      subtitle: Text(
        'Son Mesaj: ${message.message}\nZaman: ${_formatTimestamp(message.timestamp)}',
        style: const TextStyle(color: Colors.white),
      ),
      isThreeLine: true,
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => MessagingScreen(
              baseUrl: widget.baseUrl,
              displayName: message.sender,
              apiService: ApiService(),
            ),
          ),
        );
      },
    );
  },
);
          }
        },
      ),
        ]
      ),
    );
  }
}
