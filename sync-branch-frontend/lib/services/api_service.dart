import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:syncbranch/profiles/profile_page.dart'; // ProfilePage'in bulunduğu dosyayı import edin.
import 'package:syncbranch/profiles/messaging_screen.dart';

class ApiService {
  final Dio _dio = Dio(
    BaseOptions(
      baseUrl: 'https://api-sync-branch.yggbranch.dev/',
      connectTimeout: const Duration(milliseconds: 5000),
      receiveTimeout: const Duration(milliseconds: 5000),
    ),
  );

  // Secure storage instance
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  Future<Map<String, dynamic>> login(String username, String password) async {
    try {
      final response = await _dio.post(
        'auth/login',
        data: {
          'username': username,
          'password': password,
        },
        options: Options(
          headers: {
            'Content-Type': 'application/json',
          },
        ),
      );

      //print('Response Data: ${response.data}');

      if (response.data is Map<String, dynamic>) {
        // Check if the response contains access_token
        if (response.data.containsKey('access_token')) {
          // Store the token securely
          await _secureStorage.write(
            key: 'access_token',
            value: response.data['access_token'],
          );
          //print('Access token stored securely.');
        }

        return response.data;
      } else {
        throw Exception(
            'Unexpected response type: ${response.data.runtimeType}');
      }
    } on DioException catch (e) {
      if (e.type == DioExceptionType.connectionTimeout) {
        return {
          'error': true,
          'message':
              'Connection timed out. Please check your internet connection.',
        };
      } else if (e.type == DioExceptionType.receiveTimeout) {
        return {
          'error': true,
          'message': 'Server took too long to respond. Please try again later.',
        };
      } else if (e.response != null) {
        return {
          'error': true,
          'message': e.response?.data['message'] ?? 'Login failed',
        };
      } else {
        return {
          'error': true,
          'message': 'An unexpected error occurred. Please try again.',
        };
      }
    }
  }

  // Method to retrieve the stored token
  Future<String?> getAccessToken() async {
    return await _secureStorage.read(key: 'access_token');
  }

  // Method to clear the stored token
  Future<void> clearAccessToken() async {
    await _secureStorage.delete(key: 'access_token');
  }
}
