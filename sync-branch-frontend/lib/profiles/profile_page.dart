import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:syncbranch/authlib.dart';

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

  // Kullanıcı bilgileri
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

  /// Kullanıcı bilgilerini çek
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

  /// Ek profil bilgilerini çek
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

      final profileData = response.data.first; // Veriler liste olarak döner

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

  /// Kullanıcıyı giriş ekranına yönlendir
  void _redirectToLogin() {
    Navigator.pushReplacementNamed(context, '/login');
  }

  /// Logout işlemi
  Future<void> logout() async {
    await _secureStorage.delete(key: 'jwt_token');
    _redirectToLogin();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Profil fotoğrafı
                  if (profileImageUrl != null)
                    Center(
                      child: CircleAvatar(
                        radius: 50,
                        backgroundImage: NetworkImage(profileImageUrl!),
                      ),
                    ),
                  const SizedBox(height: 20),

                  // Kullanıcı bilgileri
                  buildProfileField('Username', username),
                  buildProfileField('Email', email),
                  const SizedBox(height: 20),

                  // Kişisel bilgiler
                  buildProfileField('Personal Type', personalType),
                  if (typeDescription != null)
                    Text(
                      typeDescription!,
                      style: const TextStyle(
                          fontFamily: 'Montserrat',
                          fontSize: 14,
                          color: Colors.grey),
                    ),
                  const SizedBox(height: 20),

                  // Playlist bilgileri
                  buildProfileField('Playlists', playlistCount?.toString()),
                  buildProfileField('Total Tracks', totalTracks?.toString()),
                ],
              ),
            ),
    );
  }

  /// Tekrarlanan profil alanlarını oluşturur
  Widget buildProfileField(String label, String? value) {
    return Text(
      '$label: ${value ?? "Loading..."}',
      style: const TextStyle(
        fontFamily: 'Montserrat',
        fontSize: 16,
        fontWeight: FontWeight.bold,
      ),
    );
  }
}
