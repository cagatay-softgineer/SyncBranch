import 'package:dio/dio.dart';
import 'package:syncbranch/authlib.dart'; // AuthService'i içe aktarın.
import 'message.dart';

class ChatServices {
  final Dio _dio = Dio();
  final String baseUrl =
      "https://api-sync-branch.yggbranch.dev"; // API'nin temel adresi

  // Mesajları Al
  Future<List<Message>> fetchMessages() async {
    await AuthService.loadToken();
    final jwtToken = AuthService.token;

    if (jwtToken == null) {
      throw Exception('JWT token bulunamadı. Lütfen giriş yapın.');
    }

    final response = await _dio.get(
      '$baseUrl/messaging/retrieve',
      options: Options(
        headers: {
          'Authorization': 'Bearer $jwtToken',
        },
      ),
    );
    //print('Fetched messages: ${response.data}');
    if (response.statusCode == 200) {
      //print('Fetched messages: ${response.data}');
      final List data = response.data;
     
      return data.map((json) => Message.fromJson(json)).toList();
    } else {
      throw Exception('Mesajlar alınamadı: ${response.statusMessage}');
    }
  }

  // Mesajı Okundu Olarak İşaretle
Future<void> markMessageAsRead(String messageId) async {
  await AuthService.loadToken();
  final jwtToken = AuthService.token;

  if (jwtToken == null) {
    throw Exception('JWT token not found. Please log in.');
  }

  try {
    //print('Sending request to mark message as read. Message ID: $messageId');
    
    final response = await _dio.post(
      '$baseUrl/messaging/mark',
      data: {
        'message_id': messageId, // Ensure the message ID is correct
        'is_read': 1,           // Mark as read
      },
      options: Options(
        headers: {
          'Authorization': 'Bearer $jwtToken',
        },
      ),
    );

    // Debug response
    //print('Response status: ${response.statusCode}');
    //print('Response data: ${response.data}');

    if (response.statusCode != 200) {
      throw Exception('Failed to mark message as read. Status: ${response.statusCode}');
    }
  } catch (e) {
    print('Error in markMessageAsRead: $e');
    rethrow;
  }
}

  // Mesaj Gönder
  Future<bool> sendMessage(String recipient, String message) async {
    try {
      // JWT token'ı secure storage'dan yükle
      await AuthService.loadToken();
      final jwtToken = AuthService.token;

      if (jwtToken == null) {
        throw Exception('JWT token bulunamadı. Lütfen giriş yapın.');
      }
      //print("recipient $recipient, message $message, jwtToken $jwtToken");

      // API çağrısı yap
      final response = await _dio.post(
        'https://api-sync-branch.yggbranch.dev/messaging/send',
        data: {'recipient': recipient, 'message': message},
        options: Options(
          headers: {
            'Authorization': 'Bearer $jwtToken', // JWT token ekle
          },
        ),
      );

      if (response.statusCode == 200) {
        return true; // Mesaj başarılı
      } else {
        return false; // Mesaj gönderimi başarısız
      }
    } catch (e) {
      print('Mesaj gönderimi hatası: $e');
      return false; // Hata durumunda başarısız döner
    }
  }
}
