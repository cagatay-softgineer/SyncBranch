import 'package:flutter/material.dart';

class GooglePage extends StatelessWidget {
  const GooglePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF05031C), // Rich Black arka plan
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            // Üst Kısım: Google Amblem ve Başlık
            const Spacer(flex: 2), // Yukarı boşluk
            Column(
              children: [
                Image.asset(
                  'assets/images/google_logo.png', // Google amblemi için resim
                  height: 80,
                  width: 80,
                ),
                const SizedBox(height: 16),
                ShaderMask(
                  shaderCallback: (Rect bounds) {
                    return const LinearGradient(
                      colors: [
                        Color(0xFF84FBFB),
                        Color(0xFF6A11CB),
                        Color(0xFFFF22FF),
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ).createShader(bounds);
                  },
                  child: const Text(
                    "Connect Your Google",
                    style: TextStyle(
                      fontFamily: 'Montserrat',
                      fontWeight: FontWeight.bold,
                      fontSize: 24,
                      color: Colors.white,
                    ),
                  ),
                ),
              ],
            ),
            const Spacer(flex: 1), // Form elemanlarını aşağı kaydır

            // Orta Kısım: Form Alanları
            TextField(
              decoration: InputDecoration(
                hintText: 'Google Email',
                hintStyle: const TextStyle(
                  fontFamily: 'Montserrat',
                  color: Colors.white54,
                ),
                filled: true,
                fillColor: const Color(0xFF292929), // Koyu alan rengi
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: BorderSide.none,
                ),
              ),
              style: const TextStyle(
                fontFamily: 'Montserrat',
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 20),
            TextField(
              obscureText: true,
              decoration: InputDecoration(
                hintText: 'Google Password',
                hintStyle: const TextStyle(
                  fontFamily: 'Montserrat',
                  color: Colors.white54,
                ),
                filled: true,
                fillColor: const Color(0xFF292929), // Koyu alan rengi
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: BorderSide.none,
                ),
              ),
              style: const TextStyle(
                fontFamily: 'Montserrat',
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                // Google hesabına bağlanma işlemi burada yapılacak
              },
              style: ElevatedButton.styleFrom(
                backgroundColor:
                    const Color(0xFF6A11CB), // Buton arka plan rengi
                foregroundColor: Colors.white, // Yazı rengi
                shape: RoundedRectangleBorder(
                  borderRadius:
                      BorderRadius.circular(10), // Yuvarlatılmış köşeler
                ),
                minimumSize:
                    const Size(double.infinity, 50), // Tam genişlikte buton
              ),
              child: const Text(
                'Connect',
                style: TextStyle(
                  fontFamily: 'Montserrat',
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            const Spacer(flex: 3), // Alt boşluk
          ],
        ),
      ),
    );
  }
}
