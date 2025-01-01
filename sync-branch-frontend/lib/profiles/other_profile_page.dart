import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:syncbranch/profiles/messaging_screen.dart';
import 'package:syncbranch/services/api_service.dart';
import 'message.dart';
import 'playlist.dart';
import 'tracks_page.dart';

class OtherProfilePage extends StatefulWidget {
  final String userId;
  final String displayName;
  final String username;

  const OtherProfilePage({
    required this.userId,
    required this.displayName,
    required this.username,
    Key? key,
  }) : super(key: key);

  @override
  _OtherProfilePageState createState() => _OtherProfilePageState();
}

class _OtherProfilePageState extends State<OtherProfilePage> {
  final Dio _dio =
      Dio(BaseOptions(baseUrl: "https://api-sync-branch.yggbranch.dev/"));

  String? username;
  String? profileImageUrl;
  String? personalType;
  String? typeDescription;
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchOtherUserProfile();
  }

  Future<void> fetchOtherUserProfile() async {
    try {
      final response = await _dio.post(
        'database/user-profile',
        data: {
          "user_id": widget.userId,
          "db_name": "primary",
        },
      );

      final profileData = response.data;

      setState(() {
        username = profileData['display_name'];
        profileImageUrl = profileData['profile_image_url'];
        personalType = profileData['personal_type'];
        typeDescription = profileData['type_description'];
        isLoading = false;
      });
    } catch (e) {
      print("Error fetching other user's profile: $e");
      setState(() {
        isLoading = false;
      });
    }
  }

    Future<List<Playlist>> fetchPlaylists(String userId) async {
  final response = await _dio.post(
        '/database/get_user_playlists',
        data: {
          "user_id": widget.userId
        }
  );

  if (response.statusCode == 200) {
    final List<dynamic> data = response.data;
    return data.map((json) => Playlist.fromJson(json)).toList();
  } else {
    throw Exception('Failed to load playlists');
  }
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
          decoration: BoxDecoration(
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
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: isLoading
                ? Center(
                    child: CircularProgressIndicator(),
                  )
                : SingleChildScrollView(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        SizedBox(height: 120),
                        // Profile Image
                        if (profileImageUrl != null)
                          Center(
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(20),
                              child: Image.network(
                                profileImageUrl!,
                                width: 300,
                                height: 400,
                                fit: BoxFit.cover,
                              ),
                            ),
                          ),
                        SizedBox(height: 16),
                        // Username
                        Text(
                          username ?? "Loading...",
                          style: TextStyle(
                            fontFamily: 'Montserrat',
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        SizedBox(height: 20),
                        // Personal Type Card
                        Container(
                          width: MediaQuery.of(context).size.width * 0.85,
                          padding: EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.8),
                            borderRadius: BorderRadius.circular(16),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.7),
                                blurRadius: 10,
                                offset: Offset(0, 5),
                              ),
                            ],
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              buildProfileFieldPersonalType(
                                  "Personel Type", personalType),
                              SizedBox(height: 20),
                              Text(
                                typeDescription ?? "Loading...",
                                style: TextStyle(
                                  fontFamily: 'Montserrat',
                                  fontSize: 16,
                                  color: const Color.fromARGB(255, 0, 0, 1),
                                ),
                              ),
                            ],
                          ),
                        ),
                        SizedBox(height: 50),
                        // Send Message Button
                        ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.white,
                            foregroundColor: Colors.deepPurple,
                            padding: EdgeInsets.symmetric(
                                horizontal: 40, vertical: 12),
                          ),
                          onPressed: () {
  if (widget.username == "Not Registered") {
    // Show a message instead of navigating
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text("This user is not registered to the main app."),
        behavior: SnackBarBehavior.floating, // Optional: Floating snackbar
      ),
    );
  } else {
    // Navigate to the MessagingScreen
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => MessagingScreen(
          baseUrl: "https://api-sync-branch.yggbranch.dev/",
          displayName: widget.username,
          apiService: ApiService(),
        ),
      ),
    );
  }
},

                          child: Text(
                            "Mesaj Gönder",
                            style: TextStyle(
                                fontFamily: 'Montserrat', fontSize: 16),
                          ),
                        ),
                        SizedBox(height: 50),
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
        ),
        // Positioned back icon
        Positioned(
          top: 50,
          left: 5,
          child: IconButton(
            icon: const Icon(Icons.west, color: Colors.white),
            onPressed: () {
              Navigator.pop(context);
            },
          ),
        ),
      ],
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
  // Get the color for the personal type, or default to white if not found
  final color = personalTypeColors[value] ?? const Color.fromRGBO(225, 225, 225, 1);

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