import 'package:flutter/material.dart';
import 'package:syncbranch/login_pages/google_page.dart';
import 'package:syncbranch/login_pages/spotify_page.dart';
import 'package:syncbranch/profiles/match_page.dart';
import 'splash_screen.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'sign_up.dart';
import 'terms_and_conditions_page.dart';
import 'package:syncbranch/login_pages/login_page.dart';
import 'package:syncbranch/login_pages/login_screen.dart';
import 'package:syncbranch/profiles/profile_page.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:image_picker/image_picker.dart';
import 'settings/settings.dart'; // SettingsScreen dosyasını import edin

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SyncBranch',
      theme: ThemeData(
        primarySwatch: Colors.deepPurple,
      ),
      initialRoute: '/',
      routes: {
        '/': (context) => const SplashScreen(),
        '/login': (context) => const LoginScreen(),
        '/loginPage': (context) => LoginPage(),
        '/signup': (context) => const SignUpPage(),
        '/spotifypage': (context) => const SpotifyPage(),
        '/googlepage': (context) => const GooglePage(),
        '/profilepage': (context) => const ProfilePage(),
        '/matchpage': (context) => const MatchPage(),
        '/settings': (context) => const SettingsScreen(),
      },
    );
  }
}
