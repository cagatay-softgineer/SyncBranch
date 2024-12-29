import 'package:flutter/material.dart';
import 'package:syncbranch/profiles/main_screen.dart';
import 'package:syncbranch/services/api_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({Key? key}) : super(key: key);

  @override
  _LoginPageState createState() => _LoginPageState();
}


class _LoginPageState extends State<LoginPage> {
  final ApiService apiService = ApiService();
  final TextEditingController emailController = TextEditingController();
  final TextEditingController passwordController = TextEditingController();
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  bool _rememberMe = false;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _checkAutoLogin();
  }

  Future<void> _checkAutoLogin() async {
    // Kullanıcı daha önce "Beni Hatırla" seçtiyse bilgileri doldur ve giriş yap
    String? savedUsername = await _secureStorage.read(key: 'username');
    String? savedPassword = await _secureStorage.read(key: 'password');
    if (savedUsername != null && savedPassword != null) {
      emailController.text = savedUsername;
      passwordController.text = savedPassword;
      setState(() {
        _rememberMe = true;
      });
      // Otomatik giriş yap
      final isLoggedIn = await login(context);
      if (isLoggedIn && mounted) {
                        Navigator.pushReplacement(
                          context,
                          MaterialPageRoute(
                              builder: (context) => const MainScreen()),
                        );
                      }
    }
  }

  Future<bool> login(BuildContext context) async {
    final username = emailController.text.trim();
    final password = passwordController.text.trim();

    if (username.isEmpty || password.isEmpty) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please fill in all fields')),
        );
      }
      return false;
    }

    setState(() => _isLoading = true);

    try {
      final response = await apiService.login(username, password);

      if (response['error'] == true) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(response['message'] ?? 'Login failed')),
          );
        }
        return false;
      } else {
        final token = response['access_token'];
        final user_id = response['user_id'];
        if (token != null) {
          await _secureStorage.write(key: 'jwt_token', value: token);
          await _secureStorage.write(key: 'user_id', value: user_id);
          if (_rememberMe) {
          await _secureStorage.write(
              key: 'username', value: emailController.text);
          await _secureStorage.write(
              key: 'password', value: passwordController.text);
        } else {
          await _secureStorage.delete(key: 'username');
          await _secureStorage.delete(key: 'password');
        }
        }
        return true;
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('An error occurred during login')),
        );
      }
      return false;
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF05031C),
      body: Stack(
        children: [
          SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 200),
                  // Welcome Back Title
                  Center(
                    child: ShaderMask(
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
                        'Welcome Back ',
                        style: TextStyle(
                            fontFamily: 'Montserrat',
                            fontSize: 28,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFFF6F6F6)),
                      ),
                    ),
                  ),
                  const SizedBox(height: 80),
                  // Username Input

                  const SizedBox(height: 5),
                  TextField(
                    controller: emailController,
                    decoration: InputDecoration(
                      prefixIcon:
                          const Icon(Icons.person, color: Color(0x89FFFFFF)),
                      hintText: 'Enter your username',
                      hintStyle: const TextStyle(
                          fontFamily: 'Montserrat', color: Color(0x89FFFFFF)),
                      filled: true,
                      fillColor: const Color(0xFF292929),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                    style: const TextStyle(
                        fontFamily: 'Montserrat', color: Color(0xFFF6F6F6)),
                  ),
                  const SizedBox(height: 30),
                  // Password Input

                  const SizedBox(height: 5),
                  TextField(
                    controller: passwordController,
                    obscureText: true,
                    decoration: InputDecoration(
                      prefixIcon: const Icon(Icons.lock, color: Colors.white54),
                      hintText: 'Enter your password',
                      hintStyle: const TextStyle(
                          fontFamily: 'Montserrat', color: Colors.white54),
                      filled: true,
                      fillColor: const Color(0xFF292929),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                    style: const TextStyle(
                        fontFamily: 'Montserrat', color: Colors.white),
                  ),
                  const SizedBox(height: 20),

                  // Remember Me Toggle
                  Row(
                    mainAxisAlignment: MainAxisAlignment.end, // Sola hizalama
                    children: [
                      const Text(
                        'Remember Me',
                        style: TextStyle(
                            fontFamily: 'Montserrat',
                            fontWeight: FontWeight.w600,
                            color: Colors.white54,
                            fontSize: 14),
                      ),
                      const SizedBox(
                          width: 10), // Yazı ve buton arasında boşluk
                      GestureDetector(
                        onTap: () {
                          setState(() {
                            _rememberMe = !_rememberMe;
                          });
                        },
                        child: Container(
                          width: 60,
                          height: 30,
                          decoration: BoxDecoration(
                            color: _rememberMe
                                ? Colors.green
                                : Colors.grey.shade800, // Renk değişimi
                            borderRadius: BorderRadius.circular(15),
                          ),
                          child: Stack(
                            children: [
                              AnimatedPositioned(
                                duration: const Duration(milliseconds: 300),
                                left: _rememberMe ? 30 : 0,
                                child: Container(
                                  width: 30,
                                  height: 30,
                                  decoration: BoxDecoration(
                                    color: Colors.white,
                                    borderRadius: BorderRadius.circular(15),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 20),

                  // Log In Button
                  ElevatedButton(
                    onPressed: () async {
                      final isLoggedIn = await login(context);
                      if (isLoggedIn && mounted) {
                        Navigator.pushReplacement(
                          context,
                          MaterialPageRoute(
                              builder: (context) => const MainScreen()),
                        );
                      }
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
                      'Log in',
                      style: TextStyle(
                        fontFamily: 'Montserrat',
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                  const SizedBox(height: 10),
                  // Forgot Password (Login butonunun altında)
                  Center(
                    child: TextButton(
                      onPressed: () {
                        // Forgot Password Logic
                      },
                      child: const Text(
                        'Forgot Password?',
                        style: TextStyle(
                            fontFamily: 'Montserrat',
                            fontWeight: FontWeight.w800,
                            color: Colors.white54),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            ),
          ),
          if (_isLoading) const LoadingScreen(), // Loading Ekranı eklendi
        ],
      ),
    );
  }
}

// LoadingScreen ve CustomLoadingIndicator burada entegre edildi
class CustomLoadingIndicator extends StatefulWidget {
  const CustomLoadingIndicator({super.key});

  @override
  State<CustomLoadingIndicator> createState() => _CustomLoadingIndicatorState();
}

class _CustomLoadingIndicatorState extends State<CustomLoadingIndicator>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      // Daha kısa bir süre animasyonun hızlanmasını sağlar
      duration: const Duration(milliseconds: 800),
      vsync: this,
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 60,
      height: 60,
      child: RotationTransition(
        turns: _controller,
        child: Image.asset(
          'assets/images/grey_logo.png', // Logonuzun yolu
          width: 40,
          height: 40,
        ),
      ),
    );
  }
}

class LoadingScreen extends StatelessWidget {
  const LoadingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Container(
          color: Colors.black.withOpacity(0.5),
        ),
        const Center(
          child: CustomLoadingIndicator(),
        ),
      ],
    );
  }
}
