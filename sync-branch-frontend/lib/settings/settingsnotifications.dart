import 'package:flutter/material.dart';
import '../profiles/chat_services.dart';
import '../profiles/message.dart';
import '../authlib.dart';
import 'dart:async';

class SettingsNotifications extends StatefulWidget {
  @override
  _SettingsNotificationsState createState() => _SettingsNotificationsState();
}

class _SettingsNotificationsState extends State<SettingsNotifications> {
  final ChatServices _chatServices = ChatServices();
  Timer? _refreshTimer;
  List<Map<String, String>> _newMessageSenders =
      []; // Gönderen ve zaman bilgisi
  String currentUserId = ""; // Mevcut kullanıcı ID'si

  @override
  void initState() {
    super.initState();
    _initialize();
    _startAutoRefresh();
  }

  Future<void> _initialize() async {
    try {
      currentUserId = await AuthService.getUserId() ?? "";
    } catch (e) {
      print("Error loading user ID: $e");
      currentUserId = "";
    }
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  void _startAutoRefresh() {
    _refreshTimer = Timer.periodic(const Duration(seconds: 3), (timer) async {
      await _checkNewMessages();
    });
  }

  Future<void> _checkNewMessages() async {
    try {
      final messages = await _chatServices.fetchMessages();
      final newSenders = messages
          .where((message) =>
              !message.isRead &&
              message.sender !=
                  currentUserId) // Gönderen mevcut kullanıcı değilse
          .map((message) => {
                "sender": message.sender,
                "timestamp": message.timestamp,
              })
          .toSet()
          .toList();

      if (newSenders.isNotEmpty &&
          !_listEquals(newSenders, _newMessageSenders)) {
        setState(() {
          _newMessageSenders = newSenders;
        });
      }
    } catch (e) {
      print('Hata: $e');
    }
  }

  bool _listEquals(
      List<Map<String, String>> list1, List<Map<String, String>> list2) {
    if (list1.length != list2.length) return false;
    for (int i = 0; i < list1.length; i++) {
      if (list1[i]["sender"] != list2[i]["sender"] ||
          list1[i]["timestamp"] != list2[i]["timestamp"]) return false;
    }
    return true;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Yeni Mesaj Bildirimleri:',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 10),
              if (_newMessageSenders.isEmpty)
                const Text('Yeni mesaj yok.', style: TextStyle(fontSize: 16)),
              if (_newMessageSenders.isNotEmpty)
                ..._newMessageSenders.map((entry) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 5.0),
                      child: Text(
                        '${entry["sender"]} adlı kullanıcıdan yeni mesajınız var.\nTarih: ${entry["timestamp"]}',
                        style: const TextStyle(fontSize: 16),
                      ),
                    )),
            ],
          ),
        ),
      ),
    );
  }
}
