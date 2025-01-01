import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dio/dio.dart';
import 'dart:convert';
import 'package:syncbranch/authlib.dart';
import 'package:http/http.dart' as http;

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final Dio _dio = Dio();
  final FlutterSecureStorage secureStorage = const FlutterSecureStorage();
  bool _isLoading = true;
  String? profile_picture;
  List<Map<String, dynamic>> _recentSongs = [];

  @override
  void initState() {
    super.initState();
    AuthService.loadToken().then((_) => initUserAndFetchSongs());
  }

  Future<void> initUserAndFetchSongs() async {
  try {
    // Now call fetchRecentSongs with a real String
    await fetchRecentSongs();
  } catch (e) {
    print("Error fetching data: $e");
  } finally {
    setState(() => _isLoading = false);
  }
  }

  /// En son dinlenen şarkıları çek
  Future<void> fetchRecentSongs() async {
  const url = 'http://api-sync-branch.yggbranch.dev/database/get_recent';
  final token = await secureStorage.read(key: 'jwt_token');
  String? spotifyId;
  //print("#################################");
  //print(token);

  final response = await _dio.get(
        'https://api-sync-branch.yggbranch.dev/profile/view',
        options: Options(
          headers: {'Authorization': 'Bearer $token'},
        ),
      );
  spotifyId = response.data['spotify_user_id'];
  profile_picture = response.data['profile_picture'];
  //print(spotifyId);
  //print("#################################");
  try {
    final response = await _dio.post(
      url,
      options: Options(headers: {
        'Authorization': BasicAuthService.getBasicAuthHeader(),
      }),
      data: {
        "user_id": spotifyId, // userId is a proper String now
        "db_name": "primary",
      },
    );

    //print("data $response");
    if (response.statusCode == 200) {
      setState(() {
        _recentSongs = List<Map<String, dynamic>>.from(response.data);
      });
    } else {
      throw Exception('Failed to load recent songs');
    }
  } catch (e) {
    print('Error fetching recent songs: $e');
  }
  }
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // Gradient Background
          Container(
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
          // Page Content
          SafeArea(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                const SizedBox(height: 20),
                const Text(
                  'HOME',
                  style: TextStyle(
                    fontSize: 24,
                    fontFamily: 'Montserrat',
                    fontWeight: FontWeight.w900,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 10),
                // Profile Section
                
                CircleAvatar(
                  radius: 100,
                  backgroundColor: Colors.green,
                  child: CircleAvatar(
                    radius: 95,
                    backgroundImage: NetworkImage("$profile_picture"), // Profil resmi
                  ),
                ),
                const SizedBox(height: 10),

                const Text(
                  'Online',
                  style: TextStyle(
                    color: Colors.greenAccent,
                    fontSize: 14,
                  ),
                ),
                const SizedBox(height: 20),
                const Text(
                  'Recently Listened Songs:',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 10),
                _isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : Expanded(
                        child: ListView.builder(
                          itemCount: _recentSongs.length,
                          itemBuilder: (context, index) {
                            final song = _recentSongs[index];
                            return Card(
                              color: Colors.black54,
                              margin: const EdgeInsets.symmetric(
                                  vertical: 8, horizontal: 16),
                              child: ListTile(
                                leading: song['images'] != null && song['images'].isNotEmpty
    ? Image.network(
        song['images'],
        width: 40,
        height: 40,
        fit: BoxFit.cover,
      )
    : Icon(
        Icons.music_note, // Fallback icon or widget
        size: 40,
      ),
                                title: Text(
                                  song['track_name'] ?? 'Unknown Song',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.bold,
                                    fontFamily: 'Montserrat',
                                  ),
                                ),
                                subtitle: Text(
                                  song['artist_name'] ?? 'Unknown Artist',
                                  style: const TextStyle(
                                    color: Colors.white70,
                                    fontFamily: 'Montserrat',
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                      ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
