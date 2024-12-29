import 'package:flutter/material.dart';
import 'package:animated_text_kit/animated_text_kit.dart';
import 'dart:async';
import 'dart:math';
import 'package:syncbranch/login_pages/login_page.dart';
import 'package:syncbranch/login_pages/login_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  SplashScreenState createState() => SplashScreenState();
}

class SplashScreenState extends State<SplashScreen>
    with TickerProviderStateMixin {
  final List<Widget> _notes = [];
  static const List<String> assetIcons = [
    'assets/images/icon1.png',
    'assets/images/icon2.png',
    'assets/images/icon3.png',
    'assets/images/icon7.png',
    'assets/images/icon8.png',
  ];
  final Random random = Random();
  bool _showAppName = true;
  bool _showDescription = false;

  // List to store all animation controllers for disposal
  final List<AnimationController> controllers = [];

  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _startAddingNotes();
    _startTransition();
  }

  void _startAddingNotes() {
    _timer = Timer.periodic(const Duration(milliseconds: 1000), (timer) {
      _addNote();
      if (_notes.length > 30) {
        timer.cancel();
      }
    });
  }

  @override
  void dispose() {
    // Timer'ı iptal edin
    _timer?.cancel();

    // AnimationController'ları dispose edin
    for (final controller in controllers) {
      controller.dispose();
    }
    super.dispose();
  }

  void _startTransition() {
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted) {
        setState(() {
          _showAppName = false;
        });
      }
      Future.delayed(const Duration(seconds: 3), () {
        if (mounted) {
          setState(() {
            _showDescription = true;
          });
        }
      });

      // Navigate to the login screen after a specific delay
      Future.delayed(const Duration(seconds: 2), () {
        if (mounted) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (context) => const LoginScreen()),
          );
        }
      });
    });
  }

  void _addNote() {
    if (!mounted) return;
    final AnimationController controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 10),
    );
    controller.forward();

    // Add controller to the list for later disposal
    controllers.add(controller);

    final double initialLeft =
        random.nextDouble() * MediaQuery.of(context).size.width;

    final Widget noteIcon = Image.asset(
      assetIcons[random.nextInt(assetIcons.length)],
      width: 30,
      height: 30,
      color: const Color.fromARGB(255, 202, 125, 195),
    );

    final note = AnimatedBuilder(
      animation: controller,
      builder: (context, child) {
        final opacity = 1.0 - controller.value;
        const double startBottom = 0.0;
        final double endPosition = MediaQuery.of(context).size.height * 0.7;
        final double position = startBottom + controller.value * endPosition;
        final double waveOffset = 15.0 * sin(controller.value * pi * 2);

        return Positioned(
          left: initialLeft + waveOffset,
          bottom: position,
          child: Opacity(
            opacity: opacity,
            child: noteIcon,
          ),
        );
      },
    );

    setState(() {
      _notes.add(note);
    });

    controller.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        setState(() {
          _notes.remove(note);
        });
        // Removed controller.dispose() here to avoid double disposal
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // Background gradient
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
          // "Syncbranch" title
          Positioned(
            top: 130,
            left: 0,
            right: 0,
            child: AnimatedOpacity(
              opacity: _showAppName ? 1.0 : 0.0,
              duration: const Duration(seconds: 1),
              child: const Text(
                'Syncbranch',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: 'Montserrat',
                  fontSize: 46.0,
                  color: Color.fromARGB(255, 141, 122, 148),
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
          // Descriptive text appears after "Syncbranch" fades out
          if (_showDescription)
            Positioned(
              top: 200,
              left: 0,
              right: 0,
              child: Center(
                child: DefaultTextStyle(
                  style: const TextStyle(
                      fontFamily: 'Montserrat',
                      fontSize: 28.0,
                      color: Color.fromARGB(255, 141, 122, 148),
                      fontWeight: FontWeight.w800),
                  textAlign: TextAlign.center,
                  child: AnimatedTextKit(
                    animatedTexts: [
                      TyperAnimatedText('Connect through music.'),
                      TyperAnimatedText('Let the rhythm guide you.'),
                    ],
                    repeatForever: true,
                    pause: const Duration(seconds: 3),
                  ),
                ),
              ),
            ),
          // Animated notes
          ..._notes,
        ],
      ),
    );
  }
}
