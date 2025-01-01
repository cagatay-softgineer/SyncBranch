import 'package:flutter/material.dart';
import 'playlist.dart';
import 'package:url_launcher/url_launcher.dart';

class TracksPage extends StatelessWidget {
  final Playlist playlist;

  const TracksPage({Key? key, required this.playlist}) : super(key: key);

  Future<void> _openSpotifyLink(String trackId) async {
    final url = 'https://open.spotify.com/track/$trackId';
    if (await canLaunch(url)) {
      await launch(url);
    } else {
      throw 'Could not launch $url';
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
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // AppBar
                  Row(
                    children: [
                      IconButton(
                        icon: const Icon(Icons.arrow_back, color: Colors.white),
                        onPressed: () {
                          Navigator.pop(context);
                        },
                      ),
                      Expanded(
                        child: Text(
                          playlist.playlistName,
                          style: const TextStyle(
                            fontFamily: 'Montserrat',
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  // Tracks List
                  Expanded(
                    child: ListView.builder(
                      itemCount: playlist.tracks.length,
                      itemBuilder: (context, index) {
                        final track = playlist.tracks[index];
                        return Card(
                          color: Colors.white.withOpacity(0.9),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                          margin: const EdgeInsets.symmetric(vertical: 8),
                          child: Padding(
                            padding: const EdgeInsets.all(12.0),
                            child: Row(
                              children: [
                                // Track Image with Fallback
                                ClipRRect(
                                  borderRadius: BorderRadius.circular(8),
                                  child: track.trackImage != "" &&
                                          track.trackImage.isNotEmpty
                                      ? Image.network(
                                          track.trackImage,
                                          width: 50,
                                          height: 50,
                                          fit: BoxFit.cover,
                                        )
                                      : Icon(
        Icons.music_note, // Fallback icon or widget
        size: 40,
      ),
                                ),
                                const SizedBox(width: 16),
                                // Track Details
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        track.trackName,
                                        style: const TextStyle(
                                          fontFamily: 'Montserrat',
                                          fontSize: 16,
                                          fontWeight: FontWeight.bold,
                                          color: Colors.black,
                                        ),
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        track.artistName,
                                        style: const TextStyle(
                                          fontFamily: 'Montserrat',
                                          fontSize: 14,
                                          color: Colors.grey,
                                        ),
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ],
                                  ),
                                ),
                                // Open in Spotify Icon
                                IconButton(
                                  icon: const Icon(Icons.open_in_new,
                                      color: Colors.black),
                                  onPressed: () {
                                    _openSpotifyLink(track.trackId);
                                  },
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}