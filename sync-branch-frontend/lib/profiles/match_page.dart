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

      print('Spotify ID: $spotifyId');

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
        '/api/query',
        data: {
          "query":
              "SELECT top 5 * FROM GetAllMatches('$spotifyId') ORDER BY final_match_rate_percentage DESC;",
          "db_name": "primary",
        },
        options: Options(headers: {
          "Authorization": basicAuthHeader,
          "Content-Type": "application/json",
        }),
      );

      setState(() {
        topMatches = response.data;
        print("topMatches $topMatches");
      });
    } catch (e) {
      print("Error fetching top matches: $e");
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
                          itemWidth: MediaQuery.of(context).size.width * 0.9,
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
                                    ),
                                  ),
                                );
                              },
                              child: Container(
                                margin: const EdgeInsets.all(8.0),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(20),
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withOpacity(0.2),
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
                                        padding: const EdgeInsets.all(20),
                                        decoration: BoxDecoration(
                                          gradient: LinearGradient(
                                            colors: [
                                              Colors.black.withOpacity(0.7),
                                              Colors.transparent,
                                            ],
                                            begin: Alignment.bottomCenter,
                                            end: Alignment.topCenter,
                                          ),
                                        ),
                                        child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Text(
                                              match['match_user_name'] ??
                                                  'Unknown',
                                              style: const TextStyle(
                                                fontFamily: 'Montserrat',
                                                color: Colors.white,
                                                fontSize: 24,
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                            const SizedBox(height: 5),
                                            Text(
                                              '${match['final_match_rate_percentage']}% Match',
                                              style: const TextStyle(
                                                fontFamily: 'Montserrat',
                                                color: Colors.white70,
                                                fontSize: 16,
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
