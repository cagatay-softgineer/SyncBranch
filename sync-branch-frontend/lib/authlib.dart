import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthService {
  static final FlutterSecureStorage _storage = FlutterSecureStorage();
  static String? _jwtToken;
  static String? _userId;

  // Save token and user_id
  static Future<void> saveToken(String token, String userId) async {
    _jwtToken = token;
    _userId = userId;
    await _storage.write(key: "jwt_token", value: token);
    await _storage.write(key: "user_id", value: userId);
  }

  // Load the token and user_id
  static Future<void> loadToken() async {
    _jwtToken = await _storage.read(key: "jwt_token");
    _userId = await _storage.read(key: "user_id");
  }

  // Get current user ID
  static Future<String?> getUserId() async {
    _userId ??= await _storage.read(key: "user_id");
    return _userId;
  }

  // Clear token and user_id
  static Future<void> clearToken() async {
    _jwtToken = null;
    _userId = null;
    await _storage.delete(key: "jwt_token");
    await _storage.delete(key: "user_id");
  }

  // Get the current token
  static String? get token => _jwtToken;
}

class BasicAuthService {
  static const String _encodedCredentials =
      "YWRtaW46YWRtLnN5bmMuYnJhbmNoLnlnZy5kZXY=";

  // Retrieve the Authorization header
  static String getBasicAuthHeader() {
    return 'Basic $_encodedCredentials';
  }
}
