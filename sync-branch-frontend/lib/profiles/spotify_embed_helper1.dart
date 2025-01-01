import 'package:flutter/material.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';

class SpotifyEmbedWidget extends StatelessWidget {
  final String spotifyUrl;

  SpotifyEmbedWidget({Key? key, required this.spotifyUrl}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Generate the Spotify embed URL
    final regex = RegExp(
      r'https://open\.spotify\.com(/intl-[\w-]+)?/(track|artist|playlist)/([\w\d]+)',
      caseSensitive: false,
    );

    final match = regex.firstMatch(spotifyUrl);
    if (match == null) {
      return Text(
        'Invalid Spotify URL',
        style: const TextStyle(color: Colors.red),
      );
    }

    final type = match.group(2); // track, artist, or playlist
    final id = match.group(3); // Extract only the ID before '?'
    final embedUrl = 'https://open.spotify.com/embed/$type/$id';
    print(embedUrl);
    return Container(
      width: double.infinity,
      height: 100,
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey),
        borderRadius: BorderRadius.circular(10),
      ),
      child: InAppWebView(
        initialUrlRequest: URLRequest(url: WebUri(embedUrl)),
        initialSettings: InAppWebViewSettings(
          javaScriptEnabled: true,
          allowsInlineMediaPlayback: true,
          mediaPlaybackRequiresUserGesture: false,
        ),
        onLoadStop: (controller, url) {
          print('WebView loaded: $url');
        },
        onLoadError: (controller, url, code, message) {
          print('WebView error: $message');
        },
      ),
    );
  }
}
