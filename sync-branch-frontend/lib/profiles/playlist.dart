class Playlist {
  final String playlistName;
  final String playlistId;
  final String playlistImage;
  final List<Track> tracks;

  Playlist({
    required this.playlistName,
    required this.playlistId,
    required this.playlistImage,
    required this.tracks,
  });

  factory Playlist.fromJson(Map<String, dynamic> json) {
    return Playlist(
      playlistName: json['playlist_name'] ?? '',
      playlistId: json['playlist_id'] ?? '',
      playlistImage: json['playlist_image'] ?? '',
      tracks: (json['tracks'] as List<dynamic>)
          .map((trackJson) => Track.fromJson(trackJson))
          .toList(),
    );
  }
}

class Track {
  final String trackName;
  final String artistName;
  final String trackId;
  final String trackImage;

  Track({
    required this.trackName,
    required this.artistName,
    required this.trackId,
    required this.trackImage,
  });

  factory Track.fromJson(Map<String, dynamic> json) {
    return Track(
      trackName: json['track_name'] ?? '',
      artistName: json['artist_name'] ?? '',
      trackId: json['track_id'] ?? '',
      trackImage: json['track_images'] ?? '',
    );
  }
}