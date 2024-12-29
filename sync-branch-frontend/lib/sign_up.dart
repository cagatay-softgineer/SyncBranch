import 'package:flutter/material.dart';
import 'package:syncbranch/login_pages/login_page.dart';

class SignUpPage extends StatefulWidget {
  const SignUpPage({super.key});

  @override
  SignUpPageState createState() => SignUpPageState();
}

class SignUpPageState extends State<SignUpPage> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF05031C),
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24.0),
        child: Column(
          children: [
            const SizedBox(height: 140), // Yukarıda boşluk bırakılır
            // Logo ve Metin
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Image.asset(
                  'assets/images/pink_logo.png', // Logonuzun yolu
                  width: 80,
                  height: 80,
                ),
                const SizedBox(width: 10), // Logo ile metin arası boşluk
                Stack(
                  children: [
                    // Dış çizgi (stroke) efekti
                    Text(
                      'Join to\nSyncBranch',
                      style: TextStyle(
                        fontFamily: 'Montserrat',
                        fontSize: 24,
                        fontWeight: FontWeight.w700,
                        foreground: Paint()
                          ..style = PaintingStyle.stroke
                          ..strokeWidth = 6 // Dış çizginin kalınlığı
                          ..shader = const LinearGradient(
                            colors: [
                              Color(0xFFFF22FF), // Pembe
                              Color(0xFF6A11CB),
                              Color(
                                0xFF52164F,
                              ) // Mor
                            ],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ).createShader(const Rect.fromLTWH(0, 50, 200, 50)),
                      ),
                    ),
                    // İç kısım beyaz
                    const Text(
                      'Join to\nSyncBranch',
                      style: TextStyle(
                        fontFamily: 'Montserrat',
                        fontSize: 24,
                        fontWeight: FontWeight.w700,
                        color: Colors.white, // İç kısım rengi
                      ),
                    ),
                  ],
                ),
              ],
            ),

            const SizedBox(height: 50), // Logo ve form arasında boşluk
            Expanded(
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    TextField(
                      decoration: InputDecoration(
                        hintText: 'Full Name',
                        hintStyle: const TextStyle(
                          fontFamily: 'Montserrat',
                          color: Colors.white54,
                        ),
                        filled: true,
                        fillColor: const Color(0xFF292929),
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
                      decoration: InputDecoration(
                        hintText: 'Email',
                        hintStyle: const TextStyle(
                          fontFamily: 'Montserrat',
                          color: Colors.white54,
                        ),
                        filled: true,
                        fillColor: const Color(0xFF292929),
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
                        hintText: 'Password',
                        hintStyle: const TextStyle(
                          fontFamily: 'Montserrat',
                          color: Colors.white54,
                        ),
                        filled: true,
                        fillColor: const Color(0xFF292929),
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
                        hintText: 'Confirm Password',
                        hintStyle: const TextStyle(
                          fontFamily: 'Montserrat',
                          color: Colors.white54,
                        ),
                        filled: true,
                        fillColor: const Color(0xFF292929),
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
                        // Sign up button action
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF6A11CB),
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                        minimumSize: const Size(double.infinity, 50),
                      ),
                      child: const Text(
                        'Sign Up',
                        style: TextStyle(
                          fontFamily: 'Montserrat',
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const SizedBox(height: 10),
                    Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Text(
                            'Already have an account?',
                            style: TextStyle(
                              fontFamily: 'Montserrat',
                              color: Color(0xFFF6F6F6),
                            ),
                          ),
                          const SizedBox(height: 5),
                          TextButton(
                            onPressed: () {
                              Navigator.pushReplacement(
                                context,
                                MaterialPageRoute(
                                    builder: (context) =>
                                        const LoginPage()), // LoginPage'e yönlendirme
                              );
                            },
                            child: const Text(
                              'Log in',
                              style: TextStyle(
                                fontFamily: 'Montserrat',
                                color: Color(0xFFF6F6F6),
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
