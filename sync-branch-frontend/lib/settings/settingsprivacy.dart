import 'package:flutter/material.dart';

class SettingsPrivacy extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Privacy Policy'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Privacy Policy - SyncBranch',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'At SyncBranch, we place great importance on protecting user privacy and ensuring the security of your personal data. This Privacy Policy explains how we collect, use, and safeguard your information, as well as the laws we comply with.',
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 20),
            const Text(
              'What Information Do We Collect?',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              '- Personal Information: Personal data such as name, email address, and profile details may be collected.\n'
              '- Usage Data: We analyze your listening habits and preferences to provide you with personalized experiences.\n'
              '- Device Information: Technical data like your IP address, device type, and operating system are collected to enhance the user experience.',
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 20),
            const Text(
              'How Do We Use Your Information?',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              '- To provide personalized analysis and recommendations.\n'
              '- To enable secure social connections.\n'
              '- To ensure account security and verify your identity.\n'
              '- To improve our services through data analysis.',
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 20),
            const Text(
              'Your Rights',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              'At SyncBranch, we comply with Turkey’s Personal Data Protection Law No. 6698 (KVKK) and international laws, granting you the following rights:\n\n'
              '- Right of Access: You have the right to know what information we collect and to access this information.\n'
              '- Right to Rectification and Erasure: You can update or delete your information.\n'
              '- Right to Object: You can object to our data processing activities.\n'
              '- Right to Data Portability: You can request your personal data in a structured format.',
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 20),
            const Text(
              'Legal Regulations We Comply With',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              '- Turkey’s Personal Data Protection Law No. 6698 (KVKK): Establishes standards for the protection, processing, and sharing of personal data.\n'
              '- General Data Protection Regulation (GDPR) (European Union): Sets international standards for data privacy and security.\n'
              '- California Consumer Privacy Act (CCPA) (United States): Ensures the protection of user data.\n'
              '- Children’s Online Privacy Protection Act (COPPA) (United States): Provides standards for protecting children’s online privacy.',
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 20),
            const Text(
              'Our Data Security Measures',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              '- Encryption: All user data is protected using advanced encryption methods.\n'
              '- Security Protocols: Strict security measures are in place to prevent unauthorized access.\n'
              '- Anonymization: Data is anonymized during analysis to protect identity information.',
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 20),
            const Text(
              'User Responsibilities',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              'Users are responsible for keeping their account information and passwords confidential. SyncBranch is not liable for data breaches resulting from user negligence.',
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 20),
            const Text(
              'At SyncBranch, the security of your data is our priority. We continually follow best practices to safeguard your personal information and comply with legal obligations.',
              style: TextStyle(fontSize: 16),
            ),
          ],
        ),
      ),
    );
  }
}
