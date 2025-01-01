import 'package:flutter/material.dart';
import 'package:syncbranch/profiles/home_page.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'match_page.dart';
import 'messaging_inbox.dart';
import 'profile_page.dart';
import '../settings/settings.dart';
import 'chat_services.dart';

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _selectedIndex = 0; // Aktif sekmeyi tutar
  int _unreadCount = 0; // Unread message count
  final ChatServices _chatServices = ChatServices();
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  final List<Widget> _pages = [
    const HomePage(),
    const MatchPage(),
    const ProfilePage(),
    SenderListScreen(baseUrl: 'https://api-sync-branch.yggbranch.dev/'),
  ];

  @override
  void initState() {
    super.initState();
    _loadUnreadCount(); // Fetch unread messages on app start
  }

  Future<int> _getUnreadMessageCount() async {
    // Fetch all messages
    final allMessages = await _chatServices.fetchMessages();
    final userId = await _secureStorage.read(key: 'user_id');

    if (userId == null) {
      print('Error: User ID is null');
      return 0;
    }

    // Filter unread messages
    final unreadMessages = allMessages.where((message) {
      //print('Message: ${message.toJson()}'); // Debug: Ensure messages are correct
      return message.receiver == userId && !message.isRead; // Use boolean
    }).toList();

    return unreadMessages.length;
  }

  Future<void> _loadUnreadCount() async {
    try {
      final count = await _getUnreadMessageCount();
      setState(() {
        _unreadCount = count;
        //print('Unread Count Updated: $_unreadCount');
      });
    } catch (e) {
      print('Error loading unread count: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // 1. Add an AppBar with a leading IconButton
      appBar: AppBar(
        backgroundColor: Colors.transparent, // Make AppBar transparent
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.settings, color: Colors.white),
          onPressed: () {
            /// If you have a named route for Settings:
            Navigator.pushNamed(context, '/settings');
            
            /// Or, if you want to directly push a widget:
            // Navigator.push(
            //   context,
            //   MaterialPageRoute(builder: (context) => const SettingsScreen()),
            // );
          },
        ),
      ),
      // 2. Let the body go behind the AppBar so the gradient is visible
      extendBodyBehindAppBar: true,
      
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
          // Sayfa İçeriği
          IndexedStack(
            index: _selectedIndex,
            children: _pages,
          ),
        ],
      ),

      // BottomNavigationBar implementation stays the same
      bottomNavigationBar: SafeArea(
        child: Container(
          height: 100,
          color: const Color(0xFF292929),
          child: BottomNavigationBar(
            backgroundColor: Colors.transparent,
            elevation: 0,
            currentIndex: _selectedIndex,
            onTap: _onItemTapped,
            type: BottomNavigationBarType.fixed,
            selectedFontSize: 14,
            unselectedFontSize: 12,
            selectedItemColor: Colors.white,
            unselectedItemColor: Colors.white70,
            showSelectedLabels: false,
            showUnselectedLabels: false,
            items: [
              BottomNavigationBarItem(
                icon: _buildIcon(Icons.home, 0),
                label: 'Home',
              ),
              BottomNavigationBarItem(
                icon: _buildIcon(Icons.star, 1),
                label: 'Match',
              ),
              BottomNavigationBarItem(
                icon: _buildIcon(Icons.person, 2),
                label: 'Profile',
              ),
              BottomNavigationBarItem(
                icon: _buildIcon(Icons.chat, 3),
                label: 'Messages',
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _onItemTapped(int index) {
    if (index != _selectedIndex) {
      setState(() {
        _selectedIndex = index;
      });
    }
  }

Widget _buildIcon(IconData icon, int index) {
  final bool isSelected = _selectedIndex == index;

  return Stack(
    children: [
      AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        transform: isSelected
            ? Matrix4.translationValues(0, -10, 0)
            : Matrix4.translationValues(0, 0, 0),
        child: Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            color: isSelected ? Colors.black : Colors.transparent,
            borderRadius: BorderRadius.circular(30),
            border: isSelected ? Border.all(color: Colors.white, width: 2) : null,
          ),
          child: Icon(
            icon,
            size: 30,
            color: isSelected ? const Color(0xFFE040FB) : Colors.white70,
          ),
        ),
      ),
      if (index == 3 && _unreadCount > 0) // Only add badge for Messages tab
        Positioned(
          right: 0,
          top: 0,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            transform: isSelected
            ? Matrix4.translationValues(0, -10, 0)
            : Matrix4.translationValues(0, 0, 0),
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: Colors.red,
              shape: BoxShape.circle,
            ),
            child: Text(
              '$_unreadCount',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
    ],
  );
}
}
