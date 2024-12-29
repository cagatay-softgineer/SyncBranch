import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'settingsprofile.dart';
import 'settingsnotifications.dart';
import 'settingsprivacy.dart'; // SettingsPrivacy dosyasını import edin
import '../login_pages/login_page.dart'; // LoginPage dosyasını import edin

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}


class _SettingsScreenState extends State<SettingsScreen> {
  final FlutterSecureStorage _storage = FlutterSecureStorage();

  Future<void> _showLogoutConfirmation(BuildContext context) async {
    final shouldLogout = await showDialog<bool>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Log Out'),
          content: const Text('Are you sure you want to log out?'),
          actions: [
            TextButton(
              child: const Text('Cancel'),
              onPressed: () {
                Navigator.of(context).pop(false); // Çıkış yapma
              },
            ),
            TextButton(
              child: const Text('Log Out'),
              onPressed: () {
                Navigator.of(context).pop(true); // Çıkış yapmayı onayla
              },
            ),
          ],
        );
      },
    );

    if (shouldLogout == true) {
      // Kullanıcının giriş bilgilerini temizle
      await _storage.delete(key: 'username');
      await _storage.delete(key: 'password');

      // Kullanıcıyı LoginPage'e yönlendir
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => LoginPage()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ListTile(
              leading: const Icon(Icons.account_circle),
              title: const Text('About Us'),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => SettingsProfile()),
                );
              },
            ),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.notifications),
              title: const Text('Notifications'),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                      builder: (context) => SettingsNotifications()),
                );
              },
            ),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.lock),
              title: const Text('Privacy'),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => SettingsPrivacy()),
                );
              },
            ),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.logout),
              title: const Text('Log Out'),
              onTap: () {
                _showLogoutConfirmation(context); // Çıkış onayı
              },
            ),
          ],
        ),
      ),
    );
  }
}
