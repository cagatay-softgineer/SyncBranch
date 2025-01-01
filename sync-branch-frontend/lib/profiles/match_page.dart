import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:card_swiper/card_swiper.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'other_profile_page.dart';
import 'package:syncbranch/authlib.dart';

class MatchPage extends StatefulWidget {
  const MatchPage({super.key});

  @override
  State<MatchPage> createState() => _MatchPageState();
}

class _MatchPageState extends State<MatchPage> {
  final Dio _dio = Dio(
    BaseOptions(
      baseUrl: 'https://api-sync-branch.yggbranch.dev/',
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
    ),
  );
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  List<dynamic> topMatches = [];
  String? spotifyId;
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchUserProfile();
  }

  Future<void> fetchUserProfile() async {
    try {
      setState(() {
        isLoading = true;
      });

      final token = await _secureStorage.read(key: 'jwt_token');
      if (token == null) throw Exception('No JWT token found');

      final response = await _dio.get(
        'profile/view',
        options: Options(
          headers: {'Authorization': 'Bearer $token'},
        ),
      );

      setState(() {
        spotifyId = response.data['spotify_user_id'];
        isLoading = false;
      });

      //print('Spotify ID: $spotifyId');

      if (spotifyId != null) {
        fetchTopMatches();
      }
    } catch (e) {
      print('Error fetching profile data: $e');
      setState(() {
        isLoading = false;
      });
    }
  }

  Future<void> fetchTopMatches() async {
    try {
      final basicAuthHeader = BasicAuthService.getBasicAuthHeader();

      final response = await _dio.post(
        '/database/get_top5_matches',
        data: {
          "user_id": "$spotifyId",
          "db_name": "primary",
        },
        options: Options(headers: {
          "Authorization": basicAuthHeader,
          "Content-Type": "application/json",
        }),
      );

      setState(() {
        topMatches = response.data;
        //print("topMatches $topMatches");
      });
    } catch (e) {
      print("Error fetching top matches: $e");
    }
  }
  Color getMatchRateColor(double matchRate) {
  if (matchRate >= 80) {
    return Colors.green; // High match
  } else if (matchRate >= 50) {
    return Colors.orange; // Medium match
  } else {
    return Colors.red; // Low match
  }
}


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
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
        child: SafeArea(
          child: Column(
            children: [
              // "TOP 5 MATCHES" başlığı
              const Padding(
                padding: EdgeInsets.only(top: 20.0, bottom: 20.0),
                child: Text(
                  "TOP 5 MATCHES",
                  style: TextStyle(
                    color: Color(0xFFF6F6F6),
                    fontFamily: 'Montserrat',
                    fontSize: 24,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
              const SizedBox(height: 1), // Daha küçük bir boşluk
              // Kartlar
              Expanded(
                child: topMatches.isEmpty
                    ? const Center(
                        child: Text(
                          'No matches found.',
                          style: TextStyle(
                              fontFamily: 'Montserrat', color: Colors.white),
                        ),
                      )
                    : Align(
                        alignment: Alignment.center, // Kartların ortalanması
                        child: Swiper(
                          itemCount: topMatches.length,
                          layout: SwiperLayout.TINDER,
                          itemWidth: MediaQuery.of(context).size.width * 1.1,
                          itemHeight: MediaQuery.of(context).size.height * 0.7,
                          itemBuilder: (BuildContext context, int index) {
                            final match = topMatches[index];
                            return GestureDetector(
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (context) => OtherProfilePage(
                                      userId: match['match_user_id'],
                                      displayName: match['match_user_name'],
                                      username: match['matched_username'] ?? "Not Registered",
                                    ),
                                  ),
                                );
                              },
                              child: Container(
                                margin: const EdgeInsets.all(8.0),
                                decoration: BoxDecoration(
                                  color: Colors.transparent,
                                  borderRadius: BorderRadius.circular(20),
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withOpacity(0.3),
                                      blurRadius: 10,
                                      offset: const Offset(0, 5),
                                    ),
                                  ],
                                ),
                                child: ClipRRect(
                                  borderRadius: BorderRadius.circular(20),
                                  child: Stack(
                                    alignment: Alignment.bottomLeft,
                                    children: [
                                      // Kullanıcı görseli
                                      Image.network(
  match['match_user_image'] == "file:///"
      ? 'https://sync-branch.yggbranch.dev/assets/default_user.png'
      : match['match_user_image'],
  errorBuilder: (context, error, stackTrace) {
    // Handle errors like invalid URLs or network issues
    return Image.network('https://sync-branch.yggbranch.dev/assets/default_user.png');
  },
                                  fit: BoxFit.fitHeight,
                                  width: double.infinity,
                                  height: double.infinity,
                                      ),
                                      // Gradient arka plan ve kullanıcı bilgileri
                                      Container(
                                        padding: const EdgeInsets.all(10),
                                        alignment: Alignment.bottomCenter,
                                        decoration: BoxDecoration(
                                          gradient: LinearGradient(
                                            colors: [
                                              Colors.black.withOpacity(1),
                                              Colors.transparent,
                                            ],
                                            begin: Alignment.bottomCenter,
                                            end: Alignment.center,
                                          ),
                                          backgroundBlendMode: BlendMode.multiply,
                                          boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withOpacity(0.1),
                                      blurRadius: 10,
                                      offset: const Offset(0, 5),
                                    ),
                                  ],
                                        ),
                                        child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Align(
  alignment: Alignment.center,
  child: Text(
                                              match['match_user_name'] ??
                                                  'Unknown',
                                              style: const TextStyle(
                                                fontFamily: 'Montserrat',
                                                color: Colors.white,
                                                fontSize: 24,
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                            ),
                                            const SizedBox(height: 5),

  Align(
  alignment: Alignment.center,
  child: buildProfileFieldPersonalType(match['match_user_type']),
                                            ),

                                            const SizedBox(height: 5),
Align(
  alignment: Alignment.center,
  child: Text(
    '${match['final_match_rate_percentage']}% Match',
    textAlign: TextAlign.center,
    style: TextStyle(
      fontFamily: 'Montserrat',
      color: getMatchRateColor(match['final_match_rate_percentage']),
      fontSize: 16,
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
                            );
                          },
                        ),
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}


final Map<String, Color> personalTypeColors = {
  "Ambient Live Listener": Colors.lightBlue,
  "Ambient Minimalist": Colors.teal,
  "Balanced Pop Listener": Colors.purple,
  "Calm and Acoustic": Colors.green,
  "Cheerful Studio Enthusiast": Colors.orange,
  "Dance Enthusiast": Colors.pink,
  "Diverse Music Explorer": Colors.cyan,
  "Energetic Listener": Colors.red,
  "Engaged Podcast Listener": Colors.brown,
  "Fast-Paced Fan": Colors.amber,
  "Heavy and Intense": Colors.deepPurple,
  "High-Energy Electronic Fan": Colors.indigo,
  "High-Octane Music Lover": Colors.deepOrange,
  "Instrumental Lover": Colors.blueGrey,
  "Live Performance Enthusiast": Colors.lime,
  "Melancholic and Deep": Colors.grey,
  "Mellow and Relaxed": Colors.lightGreen,
  "Party Enthusiast": Colors.yellow,
  "Peaceful Acoustic Listener": Colors.lightBlueAccent,
  "Podcast and Rap Lover": Colors.blueAccent,
  "Quiet and Thoughtful": Colors.indigoAccent,
  "Reflective and Mellow": Colors.cyanAccent,
  "Relaxing Instrumental Lover": Colors.pinkAccent,
  "Silent and Serene": Colors.white,
  "Soft and Calm Listener": Colors.lightGreenAccent,
  "Soothing and Slow": Colors.tealAccent,
  "Speech-Oriented Listener": Colors.orangeAccent,
  "Speedy and Dance-Oriented": Colors.purpleAccent,
  "Upbeat and Loud": Colors.redAccent,
  "Upbeat Yet Relaxed": Colors.yellowAccent,
  "Uplifting and Happy": Colors.greenAccent,
};

Widget buildProfileFieldPersonalType(String? value) {
  // Get the color for the personal type, or default to white if not found
  final color = personalTypeColors[value] ?? const Color.fromRGBO(225, 225, 225, 1);

  return Text(
    '${value ?? "Loading..."}',
    style: TextStyle(
      fontFamily: 'Montserrat',
      fontSize: 18,
      fontWeight: FontWeight.bold,
      color: color,
    ),
  );
}
