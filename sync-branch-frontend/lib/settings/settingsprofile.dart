import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:url_launcher/url_launcher.dart';

class SettingsProfile extends StatelessWidget {
  void _launchWebsite() async {
    final Uri url = Uri.parse('http://sync-branch.yggbranch.dev');
    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    } else {
      throw 'Could not launch $url';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('About Us - SyncBranch'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'About Us - SyncBranch',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'SyncBranch is an innovative application designed to connect people through music. By leveraging Spotify\'s rich data, SyncBranch deeply analyzes users\' listening habits and preferences, creating a bridge between music and self-discovery. Our goal is to enhance social interactions by harnessing the power of music and technology.',
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 20),
            const Text(
              'What Do We Offer?',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              '- Personalized Analysis: SyncBranch analyzes musical attributes like danceability, energy, tempo, and more to create a unique personality profile based on your listening habits.\n\n- Social Connections: Discover people with similar musical tastes and personality traits, engage in conversations, and share recommendations.\n\n- Simple Notifications: Stay updated with notifications about new messages or connections.\n\n- Data Security: We prioritize your privacy and ensure the safety of your data with advanced encryption techniques.',
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 20),
            const Text(
              'Our Vision',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              'Music is more than just sound; it\'s a reflection of emotions, memories, and identity. SyncBranch is committed to celebrating individuality through music and building meaningful connections. By focusing on community, creativity, and innovation, we aim to redefine how music shapes our daily lives.',
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 20),
            RichText(
              text: TextSpan(
                style: const TextStyle(fontSize: 16, color: Colors.black),
                children: [
                  const TextSpan(
                    text: 'For more information, ',
                    style: TextStyle(fontStyle: FontStyle.italic),
                  ),
                  TextSpan(
                    text: 'visit our website',
                    style: const TextStyle(
                      color: Colors.blue,
                      fontStyle: FontStyle.italic,
                      decoration: TextDecoration.underline,
                    ),
                    recognizer: TapGestureRecognizer()
                      ..onTap = () => _launchWebsite(),
                  ),
                  const TextSpan(
                    text: '. Let\'s make music a bond that unites us!',
                    style: TextStyle(fontStyle: FontStyle.italic),
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
