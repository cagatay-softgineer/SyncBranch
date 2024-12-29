import 'package:flutter/material.dart';
import 'package:syncbranch/login_pages/google_page.dart';
import 'package:syncbranch/sign_up.dart';
import 'package:syncbranch/login_pages/login_page.dart';
import 'package:syncbranch/login_pages/spotify_page.dart';

class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF05031C),
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Spacer(flex: 2),
            Center(
              child: Stack(
                children: [
                  Text(
                    'Welcome to SyncBranch',
                    style: TextStyle(
                      fontFamily: 'Skranji',
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      foreground: Paint()
                        ..style = PaintingStyle.stroke
                        ..strokeWidth = 6
                        ..shader = const LinearGradient(
                          colors: [
                            Color(0xFFFF22FF),
                            Color(0xFF6A11CB),
                          ],
                        ).createShader(
                          const Rect.fromLTWH(0.0, 0.0, 200.0, 70.0),
                        ),
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const Text(
                    'Welcome to SyncBranch',
                    style: TextStyle(
                      fontFamily: 'Skranji',
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFFF6F6F6),
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 80),
            ElevatedButton(
              onPressed: () {
                Navigator.pushNamed(context, '/signup');
              },
              child: const Text(
                "Sign up free",
                style: TextStyle(
                  fontFamily: 'Montserrat',
                  fontWeight: FontWeight.w600,
                ),
              ),
              style: ButtonStyle(
                backgroundColor:
                    WidgetStateProperty.resolveWith<Color?>((states) {
                  if (states.contains(WidgetState.hovered) ||
                      states.contains(WidgetState.pressed)) {
                    return const Color.fromRGBO(106, 17, 203, 0.8);
                  }
                  return const Color(0xFF6A11CB);
                }),
                foregroundColor: WidgetStateProperty.all(Colors.black),
                shape: WidgetStateProperty.all(
                  RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                ),
                minimumSize: WidgetStateProperty.all(
                  const Size(double.infinity, 50),
                ),
              ),
            ),
            const SizedBox(height: 20),
            OutlinedButton.icon(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const SpotifyPage()),
                );
              },
              icon: Image.asset(
                'assets/images/spotify.png',
                height: 24,
                width: 24,
              ),
              label: const Text(
                "Continue with Spotify",
                style: TextStyle(
                  fontFamily: 'Montserrat',
                  fontWeight: FontWeight.w400,
                ),
              ),
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.white,
                side: const BorderSide(color: Colors.white),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(30),
                ),
                minimumSize: const Size(double.infinity, 50),
              ),
            ),
            const SizedBox(height: 15),
            OutlinedButton.icon(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const GooglePage()),
                );
              },
              icon: Image.asset(
                'assets/images/google_logo.png',
                height: 32,
                width: 32,
              ),
              label: const Text(
                "Continue with Google",
                style: TextStyle(
                  fontFamily: 'Montserrat',
                  fontWeight: FontWeight.w400,
                ),
              ),
              style: OutlinedButton.styleFrom(
                foregroundColor: const Color(0xFFFFFFFF),
                side: const BorderSide(color: Colors.white),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(30),
                ),
                minimumSize: const Size(double.infinity, 50),
              ),
            ),
            const SizedBox(height: 40),
            TextButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => LoginPage(),
                  ),
                );
              },
              child: const Text(
                "Log in",
                style: TextStyle(
                  fontFamily: 'Montserrat',
                  fontWeight: FontWeight.bold,
                  color: Color(0xFFF6F6F6),
                ),
              ),
            ),
            const Spacer(flex: 2),
          ],
        ),
      ),
    );
  }
}
