import 'package:http/http.dart' as http;
import 'package:html/parser.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

Future<Map<String, String>> fetchSpotifyMetadata(String embedUrl) async {
  final response = await http.get(Uri.parse(embedUrl));
  if (response.statusCode == 200) {
    var document = parse(response.body);
    Map<String, String> metadata = {};

    // Extract Open Graph tags
    metadata['title'] = document.querySelector('meta[property="og:title"]')?.attributes['content'] ?? '';
    metadata['artist'] = document.querySelector('meta[property="og:description"]')?.attributes['content'] ?? '';
    metadata['image'] = document.querySelector('meta[property="og:image"]')?.attributes['content'] ?? '';
    metadata['url'] = document.querySelector('meta[property="og:url"]')?.attributes['content'] ?? '';

    return metadata;
  } else {
    throw Exception('Failed to load Spotify metadata');
  }
}

class CustomSpotifyEmbed extends StatefulWidget {
  final String embedUrl;

  const CustomSpotifyEmbed({Key? key, required this.embedUrl}) : super(key: key);

  @override
  _CustomSpotifyEmbedState createState() => _CustomSpotifyEmbedState();
}

class _CustomSpotifyEmbedState extends State<CustomSpotifyEmbed> {
  Map<String, String>? metadata;
  bool isLoading = true;
  bool hasError = false;

  @override
  void initState() {
    super.initState();
    _loadMetadata();
  }

  Future<void> _loadMetadata() async {
    try {
      final data = await fetchSpotifyMetadata(widget.embedUrl);
      setState(() {
        metadata = data;
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        hasError = true;
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (hasError || metadata == null) {
      return const Center(child: Text('Failed to load Spotify embed'));
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.black,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.green),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (metadata!['image'] != null)
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.network(
                metadata!['image']!,
                width: double.infinity,
                height: 150,
                fit: BoxFit.cover,
              ),
            ),
          const SizedBox(height: 8),
          if (metadata!['title'] != null)
            Text(
              metadata!['title']!,
              style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
            ),
          if (metadata!['artist'] != null)
            Text(
              metadata!['artist']!,
              style: const TextStyle(color: Colors.white70, fontSize: 14),
            ),
          const SizedBox(height: 8),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color.fromARGB(255, 30, 90, 37),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            onPressed: () async {
              final url = metadata!['url'] ?? widget.embedUrl;
              if (await canLaunch(url)) {
                await launch(url);
              } else {
                throw 'Could not launch $url';
              }
            },
            child: Row(
    mainAxisSize: MainAxisSize.min, // To keep the button's size compact
    children: [
      Image.asset(
        "assets/images/Spotify_Green.png", // Specify the correct path to your image
        height: 24, // Adjust the size as needed
        width: 24,
      ),
      SizedBox(width: 8), // Add spacing between the image and the text
      Text(
  'Play on Spotify',
  style: TextStyle(
    color: Colors.white, // Sets the text color to white
  ),
)
    ],
  ),
          ),
        ],
      ),
    );
  }
}
