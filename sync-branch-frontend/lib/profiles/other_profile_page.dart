import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:syncbranch/profiles/messaging_screen.dart';
import 'package:syncbranch/services/api_service.dart';
import 'message.dart';

class OtherProfilePage extends StatefulWidget {
  final String userId;
  final String displayName;

  const OtherProfilePage({
    required this.userId,
    required this.displayName,
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
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
                      // Profil Resmi
                      if (profileImageUrl != null)
                        Center(
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(100),
                            child: Image.network(
                              profileImageUrl!,
                              width: 200,
                              height: 200,
                              fit: BoxFit.cover,
                            ),
                          ),
                        ),
                      SizedBox(height: 16),
                      // Kullanıcı Adı
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
                      // Personal Type Kartı
                      Container(
                        width: MediaQuery.of(context).size.width *
                            0.85, // Enini azalttık
                        padding: EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.2),
                              blurRadius: 10,
                              offset: Offset(0, 5),
                            ),
                          ],
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '${personalType ?? "Loading..."}',
                              style: TextStyle(
                                fontFamily: 'Montserrat',
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                            SizedBox(height: 20),
                            Text(
                              typeDescription ?? "Loading...",
                              style: TextStyle(
                                fontFamily: 'Montserrat',
                                fontSize: 16,
                                color: Colors.white70,
                              ),
                            ),
                          ],
                        ),
                      ),
                      SizedBox(height: 50),
                      // Mesaj Gönder Butonu
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.white,
                          foregroundColor: Colors.deepPurple,
                          padding: EdgeInsets.symmetric(
                              horizontal: 40, vertical: 12),
                        ),
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => MessagingScreen(
                                baseUrl:
                                    "https://api-sync-branch.yggbranch.dev/", // Doğru base URL
                                displayName: widget
                                    .displayName, // Diğer kullanıcının userId'si
                                apiService: ApiService(), // ApiService örneği
                              ),
                            ),
                          );
                        },
                        child: Text(
                          "Mesaj Gönder",
                          style:
                              TextStyle(fontFamily: 'Montserrat', fontSize: 16),
                        ),
                      ),
                    ],
                  ),
                ),
        ),
      ),
    );
  }
}
