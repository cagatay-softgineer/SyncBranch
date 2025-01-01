import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:syncbranch/authlib.dart';
import 'playlist.dart';
import 'tracks_page.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  ProfilePageState createState() => ProfilePageState();
}

class ProfilePageState extends State<ProfilePage> {
  final Dio _dio = Dio(
    BaseOptions(
      baseUrl: 'https://api-sync-branch.yggbranch.dev/',
      connectTimeout: const Duration(milliseconds: 10000),
      receiveTimeout: const Duration(milliseconds: 10000),
    ),
  );
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  String? username;
  String? spotifyId;
  String? email;
  String? profileImageUrl;
  String? personalType;
  String? typeDescription;
  int? playlistCount;
  int? totalTracks;
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchProfileData();
  }

  Future<void> fetchProfileData() async {
    try {
      setState(() {
        isLoading = true;
      });

      final token = await _secureStorage.read(key: 'jwt_token');
      if (token == null) {
        _redirectToLogin();
        return;
      }

      final response = await _dio.get(
        '/profile/view',
        options: Options(headers: {"Authorization": "Bearer $token"}),
      );

      setState(() {
        username = response.data['username'];
        spotifyId = response.data['spotify_user_id'];
        email = response.data['email'];
      });

      if (spotifyId != null) {
        await fetchAdditionalProfileData();
      }
    } catch (e) {
      debugPrint("Error fetching profile data: $e");
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to load profile data')),
      );
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  Future<List<Playlist>> fetchPlaylists(String userId) async {
  final response = await _dio.post(
        '/database/get_user_playlists',
        data: {
          "user_id": "$spotifyId"
        }
  );

  if (response.statusCode == 200) {
    final List<dynamic> data = response.data;
    return data.map((json) => Playlist.fromJson(json)).toList();
  } else {
    throw Exception('Failed to load playlists');
  }
}

  Future<void> fetchAdditionalProfileData() async {
    try {
      final basicAuthHeader = BasicAuthService.getBasicAuthHeader();

      final response = await _dio.post(
        '/api/query',
        data: {
          "query": "SELECT * FROM dbo.GetUserProfile('$spotifyId');",
          "db_name": "primary",
        },
        options: Options(headers: {
          "Authorization": basicAuthHeader,
          "Content-Type": "application/json",
        }),
      );

      final profileData = response.data.first;

      setState(() {
        profileImageUrl = profileData['profile_image_url'];
        personalType = profileData['personal_type'];
        typeDescription = profileData['type_description'];
        playlistCount = profileData['playlist_count'];
        totalTracks = profileData['total_tracks'];
      });
    } catch (e) {
      debugPrint("Error fetching additional profile data: $e");
    }
  }

  void _redirectToLogin() {
    Navigator.pushReplacementNamed(context, '/login');
  }

  Future<void> logout() async {
    await _secureStorage.delete(key: 'jwt_token');
    _redirectToLogin();
  }

@override
Widget build(BuildContext context) {
  return Scaffold(
    body: Stack(
      children: [
        // Background with gradient
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
        // Content
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: isLoading
              ? const Center(child: CircularProgressIndicator())
              : SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 80), // Space for the top
                      // Profile Section
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Profile Picture
                          ClipRRect(
                            borderRadius: BorderRadius.circular(100),
                            child: Image.network(
                              profileImageUrl ?? '', // Default if null
                              width: 100,
                              height: 100,
                              fit: BoxFit.cover,
                            ),
                          ),
                          const SizedBox(width: 16), // Spacing
                          // Username and Personal Type
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  username ?? "Loading...",
                                  style: const TextStyle(
                                    fontFamily: 'Montserrat',
                                    fontSize: 24,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.white,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                buildProfileFieldPersonalType(
                                    "Personal Type", personalType),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 20), // Space below profile section
                      // Personal Type Description Card
                      Container(
                        width: MediaQuery.of(context).size.width,
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.9),
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.2),
                              blurRadius: 10,
                              offset: const Offset(0, 5),
                            ),
                          ],
                        ),
                        child: Text(
                          typeDescription ?? "Loading...",
                          style: const TextStyle(
                            fontFamily: 'Montserrat',
                            fontSize: 16,
                            color: Colors.black87,
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),
                      // Playlist and Tracks Section
                      const Text(
                        "Playlists",
                        style: TextStyle(
                          fontFamily: 'Montserrat',
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      // Playlist Cards
                      FutureBuilder<List<Playlist>>(
                        future: fetchPlaylists('user_id'), // Replace with actual user ID
                        builder: (context, snapshot) {
                          if (snapshot.connectionState == ConnectionState.waiting) {
                            return const Center(child: CircularProgressIndicator());
                          } else if (snapshot.hasError) {
                            return Center(
                              child: Text(
                                'Error: ${snapshot.error}',
                                style: const TextStyle(color: Colors.white),
                              ),
                            );
                          } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                            return const Center(
                              child: Text(
                                'No playlists available',
                                style: TextStyle(color: Colors.white),
                              ),
                            );
                          } else {
                            final playlists = snapshot.data!;
                            return ListView.builder(
                              shrinkWrap: true,
                              physics: const NeverScrollableScrollPhysics(),
                              itemCount: playlists.length,
                              itemBuilder: (context, index) {
                                final playlist = playlists[index];
                                return GestureDetector(
                                  onTap: () {
                                    // Navigate to Tracks Page
                                    Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (context) => TracksPage(playlist: playlist),
                                      ),
                                    );
                                  },
                                  child: Card(
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(16),
                                    ),
                                    color: Colors.white.withOpacity(0.9),
                                    child: Padding(
                                      padding: const EdgeInsets.all(16),
                                      child: Row(
                                        children: [
                                          Image.network(
                                            playlist.playlistImage,
                                            width: 50,
                                            height: 50,
                                            fit: BoxFit.cover,
                                          ),
                                          const SizedBox(width: 16),
                                          Expanded(
                                            child: Text(
                                              playlist.playlistName,
                                              style: const TextStyle(
                                                fontSize: 18,
                                                fontFamily: "Montserrat",
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                );
                              },
                            );
                          }
                        },
                      ),
                    ],
                  ),
                ),
        ),
      ],
    ),
  );
}


  Widget buildProfileField(String label, String? value,
      [Color color = const Color.fromRGBO(225, 225, 225, 1)]) {
    return Text(
      '$label: ${value ?? "Loading..."}',
      style: TextStyle(
        fontFamily: 'Montserrat',
        fontSize: 18,
        fontWeight: FontWeight.bold,
        color: color,
      ),
    );
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

  Widget buildProfileFieldPersonalType(String label, String? value) {
    final color =
        personalTypeColors[value] ?? const Color.fromRGBO(225, 225, 225, 1);
    return Text(
      '$label: ${value ?? "Loading..."}',
      style: TextStyle(
        fontFamily: 'Montserrat',
        fontSize: 18,
        fontWeight: FontWeight.bold,
        color: color,
      ),
    );
  }
}
