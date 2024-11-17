from flask import Flask, render_template, request
import pyodbc
import json
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import seaborn as sns
import squarify
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_CONNECTION_STRING = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_HOST},{DB_PORT};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD}"

def get_connection():
    """Establishes and returns a new database connection."""
    return pyodbc.connect(DB_CONNECTION_STRING)

@app.route('/cause-error')
def cause_error():
    # Example of causing an error for testing
    raise ValueError("This is a test error")

# 404 Error Handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_message="The page you are looking for does not exist."), 404

# 500 Error Handler
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_message="An internal server error occurred. Please try again later."), 500


# Load gender-name.json file
with open('gender_api/first_names/first_names.json', 'r', encoding='utf-8') as f:
    gender_data = json.load(f)


def get_gender_icon(display_name):
    if display_name in gender_data:
        gender_probs = gender_data[display_name].get('gender', {})
        if gender_probs:
            most_probable_gender = max(gender_probs, key=gender_probs.get)
            if most_probable_gender == 'M':
                return '/static/icons/male.png'
            elif most_probable_gender == 'F':
                return '/static/icons/female.png'
    return '/static/icons/unknown.png'

@app.route('/')
def main_page():
    try:
        # If user data is available, you can fetch personalized info here
        # Example: Fetch a sample user display name for a personalized link
        user_display_name = "bg"  # Replace with dynamic user info if available

        return render_template(
            'index.html',
            user_display_name=user_display_name  # Pass any dynamic data needed
        )
    except Exception as e:
        error_message = f"Error loading the main page: {e}"
        return render_template('error.html', error_message=error_message)

@app.route('/tracks-embeds', methods=['GET'])
def tracks_embeds():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    tracks_per_page = 100  # You can adjust this number
    offset = (page - 1) * tracks_per_page

    try:
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()

        # Count total records with search filter for pagination
        count_query = """
            SELECT COUNT(DISTINCT "Track Index")
            FROM TracksAudioFeatures
            WHERE "Track Name" LIKE ? OR "Track Artist Names" LIKE ?
        """
        cursor.execute(count_query, ('%' + search_query + '%', '%' + search_query + '%'))
        total_tracks = cursor.fetchone()[0]
        total_pages = (total_tracks + tracks_per_page - 1) // tracks_per_page

        # Fetch paginated track audio features data with search filter (only track_id)
        select_query = """
            SELECT "Track Index"
            FROM TracksAudioFeatures
            WHERE "Track Name" LIKE ? OR "Track Artist Names" LIKE ?
            ORDER BY "Track Popularity" DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        cursor.execute(select_query, ('%' + search_query + '%', '%' + search_query + '%', offset, tracks_per_page))
        
        data = cursor.fetchall()

        # Create a list of iframes for each track
        embeds = []
        for row in data:
            track_id = row[0]  # Track ID
            embed_code = f'<iframe style="border-radius:12px" src="https://open.spotify.com/embed/track/{track_id}" width="100%" height="100" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>'
            embeds.append(embed_code)

        cursor.close()
        conn.close()

        return render_template(
            'view_tracks_embeds.html',
            embeds=embeds,
            page=page,
            total_pages=total_pages,
            search_query=search_query
        )
    except pyodbc.Error as e:
        error_message = f"Database error: {e}"
        return render_template('error.html', error_message=error_message)

@app.route('/audio-features', methods=['GET'])
def show_tracks_audio_features():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    tracks_per_page = 100
    offset = (page - 1) * tracks_per_page

    try:
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()

        # Count total records with search filter for pagination
        count_query = """
            SELECT COUNT(DISTINCT "Track Index")
            FROM TracksAudioFeatures
            WHERE "Track Name" LIKE ? OR "Track Artist Names" LIKE ?
        """
        cursor.execute(count_query, ('%' + search_query + '%', '%' + search_query + '%'))
        total_tracks = cursor.fetchone()[0]
        total_pages = (total_tracks + tracks_per_page - 1) // tracks_per_page

        # Fetch paginated track audio features data with search filter
        select_query = """
            SELECT *
            FROM TracksAudioFeatures
            WHERE "Track Name" LIKE ? OR "Track Artist Names" LIKE ?
            ORDER BY "Track Popularity" DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        cursor.execute(select_query, ('%' + search_query + '%', '%' + search_query + '%', offset, tracks_per_page))
        
        data = cursor.fetchall()
        headers = [column[0] for column in cursor.description]
        headers = headers[1:]
        print(headers[4])
        headers[4] = "Duration"
        for i in range(len(data)):
            # Extract the row
            row = data[i]
            row = row[1:]
            # Convert the value at index 4 from milliseconds to seconds
            milliseconds = row[4]
            total_seconds = milliseconds / 1000  # Convert milliseconds to seconds
            total_min = total_seconds // 60
            last_sec = total_seconds % 60

            # Update the row with the converted value at index 4
            data[i][4] = f"{int(total_min)} Min {int(last_sec)} Sec"
            data[i] = data[i][1:]
        # Attach index to each row cell for easier targeting in the template
        rows = [[(index, cell) for index, cell in enumerate(row)] for row in data]


        cursor.close()
        conn.close()

        return render_template(
            'view_audio_features.html', 
            headers=headers, 
            rows=rows, 
            page=page,
            total_pages=total_pages,
            search_query=search_query
        )
    except pyodbc.Error as e:
        error_message = f"Database error: {e}"
        return render_template('error.html', error_message=error_message)

@app.route('/artist-genre-distribution')
def artist_genre_distribution():
    artist_name = request.args.get('artist_name', None)
    try:
        # Connect to the database
        conn = get_connection()
        cursor = conn.cursor()

        if artist_name:
            # Query for genre distribution for a specific artist
            genre_query = """
                SELECT TG."Track Genre", COUNT(*) AS TrackCount
                FROM TracksAudioFeatures TG
                JOIN Artists AR ON TG."Track Artist Name" = AR.name
                WHERE AR.name = ?
                GROUP BY TG."Track Genre"
            """
            cursor.execute(genre_query, (artist_name,))
            genre_data = cursor.fetchall()
            #title = f"Genre Distribution for {artist_name}"
        else:
            # Query for overall genre distribution
            genre_query = """
                SELECT TG."Track Genre", COUNT(*) AS TrackCount
                FROM TracksAudioFeatures TG
                GROUP BY TG."Track Genre"
            """
            cursor.execute(genre_query)
            genre_data = cursor.fetchall()
            #title = "Overall Genre Distribution"

        genres = [row[0] for row in genre_data]
        genre_counts = [row[1] for row in genre_data]

        cursor.close()
        conn.close()
        
        sorted_genre_data = sorted(zip(genre_counts, genres), reverse=True)
        sizes = [count for count, genre in sorted_genre_data]
        labels = [f"{genre}\n{count}" for count, genre in sorted_genre_data]

        # Generate treemap
        treemap = BytesIO()
        plt.figure(figsize=(12, 8))
        
        plt.gca().set_facecolor("#292929")  # Set the plot background color
        plt.gcf().patch.set_facecolor("#292929")  # Set the figure background color
        
        squarify.plot(sizes=sizes, label=labels, alpha=0.8, color=sns.color_palette('viridis', len(sizes)))
        plt.axis('off')
        #plt.title(title, fontsize=16)
        plt.tight_layout()
        plt.savefig(treemap, format='png')
        treemap.seek(0)
        treemap_url = base64.b64encode(treemap.getvalue()).decode()

        return render_template(
            'artist_genre_distribution.html', 
            genre_bar_url=treemap_url,
            total_tracks=sum(genre_counts),
            artist_name=artist_name  # Pass artist_name to the template if specified
        )
    except pyodbc.Error as e:
        error_message = f"Database error: {e}"
        return render_template('error.html', error_message=error_message)

@app.route('/artists')
def artists():
    search_query = request.args.get('search', '')

    try:
        # Connect to the database
        conn = get_connection()
        cursor = conn.cursor()

        # Query to get all unique artist names, filtered by search query if provided
        if search_query:
            artist_query = """
                SELECT DISTINCT AR.name
                FROM Artists AR
                JOIN TracksAudioFeatures TAF ON AR.name = TAF."Track Artist Name"
                WHERE AR.name LIKE ?
                ORDER BY AR.name
            """
            cursor.execute(artist_query, ('%' + search_query + '%',))
        else:
            artist_query = """
                SELECT DISTINCT AR.name
                FROM Artists AR
                JOIN TracksAudioFeatures TAF ON AR.name = TAF."Track Artist Name"
                ORDER BY AR.name
            """
            cursor.execute(artist_query)

        artists_data = cursor.fetchall()
        
        # Convert fetched data to a list of artist names
        artists = [row[0] for row in artists_data]

        cursor.close()
        conn.close()

        # Render the template with the list of artist names and search query
        return render_template('artists.html', artists=artists)
    except pyodbc.Error as e:
        error_message = f"Database error: {e}"
        return render_template('error.html', error_message=error_message)

@app.route('/user-personal-type/<display_name>')
def show_user_personal_type(display_name):
    try:
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            u.user_id,
            u.display_name,
            CAST(u.profile_image_url AS NVARCHAR(MAX)) AS profile_image_url,
            uc.personal_type,
            CAST(pt.type_description AS NVARCHAR(MAX)) AS type_description,
            CAST(pt.feature_profile_high AS NVARCHAR(MAX)) AS feature_profile_high,
            CAST(pt.feature_profile_medium AS NVARCHAR(MAX)) AS feature_profile_medium,
            CAST(pt.feature_profile_low AS NVARCHAR(MAX)) AS feature_profile_low,
            COUNT(DISTINCT up.playlist_id) AS playlist_count,
            ISNULL(ut.total_tracks, 0) AS total_tracks
        FROM 
            Users u
        JOIN 
            UserClusters uc ON u.user_id = uc.user_id
        JOIN 
            Personal_Types pt ON uc.personal_type = pt.personal_type
        LEFT JOIN 
            User_Playlists up ON u.user_id = up.user_id
        LEFT JOIN 
            UserTotalTracks ut ON u.user_id = ut.user_id
        WHERE 
            u.display_name = ?
        GROUP BY 
            u.user_id, 
            u.display_name, 
            CAST(u.profile_image_url AS NVARCHAR(MAX)), 
            uc.personal_type, 
            CAST(pt.type_description AS NVARCHAR(MAX)), 
            CAST(pt.feature_profile_high AS NVARCHAR(MAX)), 
            CAST(pt.feature_profile_medium AS NVARCHAR(MAX)), 
            CAST(pt.feature_profile_low AS NVARCHAR(MAX)), 
            ut.total_tracks;
        """, (display_name,))
        data = cursor.fetchone()
        if not data:
            return render_template('error.html', error_message=f"No personal type information found for user: {display_name}")
        headers = [column[0] for column in cursor.description]
        user_personal_type_info = dict(zip(headers, data))
        cursor.close()
        conn.close()
        return render_template('user_personal_type.html', user_info=user_personal_type_info)
    except pyodbc.Error as e:
        error_message = f"Database error: {e}"
        return render_template('error.html', error_message=error_message)


@app.route('/all-users')
def all_users():
    try:
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            u.user_id, 
            u.display_name, 
            u.profile_image_url, 
            uc.personal_type
        FROM 
            Users u
        LEFT JOIN 
            UserClusters uc ON u.user_id = uc.user_id
        """)
        users = cursor.fetchall()
        users = [
            {
                "user_id": user[0],  # Pass user_id
                "display_name": user[1],
                "profile_image_url": user[2] or '/static/icons/default_user.png',
                "personal_type": user[3] or "Unknown"
            }
            for user in users
        ]
        cursor.close()
        conn.close()
        return render_template('all_users.html', users=users)
    except pyodbc.Error as e:
        error_message = f"Database error: {e}"
        return render_template('error.html', error_message=error_message)


@app.route('/user-profile/<user_id>')
def user_profile(user_id):
    try:
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Fetch user information based on user_id
        cursor.execute("""
        SELECT 
            u.user_id, u.display_name, u.profile_image_url,
            uc.personal_type, pt.type_description
        FROM 
            Users u
        JOIN 
            UserClusters uc ON u.user_id = uc.user_id
        JOIN 
            Personal_Types pt ON uc.personal_type = pt.personal_type
        WHERE 
            u.user_id = ?
        """, user_id)
        user_info = cursor.fetchone()
        
        if not user_info:
            return render_template('error.html', error_message=f"No personal type information found for user ID: {user_id}")
        
        user_info = {
            "user_id": user_info[0],
            "display_name": user_info[1],
            "profile_image_url": user_info[2] or '/static/icons/default_user.png',
            "personal_type": user_info[3],
            "type_description": user_info[4]
        }


        # Fetch top 5 matches
        cursor.execute("""
        WITH RankedMatches AS (
    SELECT 
        CASE WHEN u1.user_id = ? THEN u2.user_id ELSE u1.user_id END AS match_user_id,
        CASE WHEN u1.user_id = ? THEN u2.display_name ELSE u1.display_name END AS match_user_name,
        CASE WHEN u1.user_id = ? THEN u2.profile_image_url ELSE u1.profile_image_url END AS match_user_image,
        upmD.final_match_rate_percentage,
        CASE WHEN u1.user_id = ? THEN uaf2.personal_type ELSE uaf1.personal_type END AS match_user_type,
        ROW_NUMBER() OVER (
            PARTITION BY 
                CASE WHEN u1.user_id = ? THEN u2.user_id ELSE u1.user_id END
            ORDER BY 
                upmD.final_match_rate_percentage DESC
        ) AS rn
    FROM 
        UserPairMatchRateWithDisplayNamesTable upmD
    JOIN 
        Users u1 ON upmD.user_id1 = u1.user_id
    JOIN 
        Users u2 ON upmD.user_id2 = u2.user_id
    JOIN 
        UserClusters uaf1 ON u1.user_id = uaf1.user_id
    JOIN 
        UserClusters uaf2 ON u2.user_id = uaf2.user_id
    WHERE 
        u1.user_id = ? OR u2.user_id = ?
)
SELECT TOP 5
    match_user_id,
    match_user_name,
    match_user_image,
    final_match_rate_percentage,
    match_user_type
FROM 
    RankedMatches
WHERE 
    rn = 1
ORDER BY 
    final_match_rate_percentage DESC;
""", (user_id, user_id, user_id, user_id, user_id, user_id, user_id))
        top_matches = cursor.fetchall()
        top_matches = [
            {
            "match_user_id": match[0],  # Added match_user_id
            "match_user_name": match[1],
            "match_user_image": match[2] or '/static/icons/default_user.png',
            "final_match_rate_percentage": match[3],
            "match_user_type": match[4]
            } for match in top_matches
        ]

        # Fetch top 50 matches
        cursor.execute("""
        WITH RankedMatches AS (
    SELECT 
        CASE WHEN u1.user_id = ? THEN u2.user_id ELSE u1.user_id END AS match_user_id,
        CASE WHEN u1.user_id = ? THEN u2.display_name ELSE u1.display_name END AS match_user_name,
        CASE WHEN u1.user_id = ? THEN u2.profile_image_url ELSE u1.profile_image_url END AS match_user_image,
        upmD.final_match_rate_percentage,
        CASE WHEN u1.user_id = ? THEN uaf2.personal_type ELSE uaf1.personal_type END AS match_user_type,
        ROW_NUMBER() OVER (
            PARTITION BY 
                CASE WHEN u1.user_id = ? THEN u2.user_id ELSE u1.user_id END
            ORDER BY 
                upmD.final_match_rate_percentage DESC
        ) AS rn
    FROM 
        UserPairMatchRateWithDisplayNamesTable upmD
    JOIN 
        Users u1 ON upmD.user_id1 = u1.user_id
    JOIN 
        Users u2 ON upmD.user_id2 = u2.user_id
    JOIN 
        UserClusters uaf1 ON u1.user_id = uaf1.user_id
    JOIN 
        UserClusters uaf2 ON u2.user_id = uaf2.user_id
    WHERE 
        u1.user_id = ? OR u2.user_id = ?
)
SELECT TOP 50
    match_user_id,
    match_user_name,
    match_user_image,
    final_match_rate_percentage,
    match_user_type
FROM 
    RankedMatches
WHERE 
    rn = 1
ORDER BY 
    final_match_rate_percentage DESC;
""", (user_id, user_id, user_id, user_id, user_id, user_id, user_id))
        all_matches = cursor.fetchall()
        all_matches = [
            {
                "match_user_id": match[0],  # Ensure index 0 corresponds to match_user_id
                "match_user_name": match[1],  # Ensure index 1 corresponds to match_user_name
                "match_user_image": match[2] or '/static/icons/default_user.png',  # Ensure index 2 corresponds to match_user_image
                "final_match_rate_percentage": match[3],  # Ensure index 3 corresponds to final_match_rate_percentage
                "match_user_type": match[4]  # Ensure index 4 corresponds to match_user_type
            } for match in all_matches
        ]

        cursor.close()
        conn.close()
        return render_template('user_profile.html', user_info=user_info, top_matches=top_matches, all_matches=all_matches)
    except pyodbc.Error as e:
        error_message = f"Database error: {e}"
        return render_template('error.html', error_message=error_message)


@app.route('/user-personal-type-with-id/<user_id>')
def show_user_personal_type_with_id(user_id):
    try:
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            u.user_id,
            u.display_name,
            CAST(u.profile_image_url AS NVARCHAR(MAX)) AS profile_image_url,
            uc.personal_type,
            CAST(pt.type_description AS NVARCHAR(MAX)) AS type_description,
            CAST(pt.feature_profile_high AS NVARCHAR(MAX)) AS feature_profile_high,
            CAST(pt.feature_profile_medium AS NVARCHAR(MAX)) AS feature_profile_medium,
            CAST(pt.feature_profile_low AS NVARCHAR(MAX)) AS feature_profile_low,
            COUNT(DISTINCT up.playlist_id) AS playlist_count,
            ISNULL(ut.total_tracks, 0) AS total_tracks
        FROM 
            Users u
        JOIN 
            UserClusters uc ON u.user_id = uc.user_id
        JOIN 
            Personal_Types pt ON uc.personal_type = pt.personal_type
        LEFT JOIN 
            User_Playlists up ON u.user_id = up.user_id
        LEFT JOIN 
            UserTotalTracks ut ON u.user_id = ut.user_id
        WHERE 
            u.user_id = ?
        GROUP BY 
            u.user_id, 
            u.display_name, 
            CAST(u.profile_image_url AS NVARCHAR(MAX)), 
            uc.personal_type, 
            CAST(pt.type_description AS NVARCHAR(MAX)), 
            CAST(pt.feature_profile_high AS NVARCHAR(MAX)), 
            CAST(pt.feature_profile_medium AS NVARCHAR(MAX)), 
            CAST(pt.feature_profile_low AS NVARCHAR(MAX)), 
            ut.total_tracks;
        """, (user_id,))
        data = cursor.fetchone()
        if not data:
            return render_template('error.html', error_message=f"No personal type information found for user: {user_id}")
        headers = [column[0] for column in cursor.description]
        user_personal_type_info = dict(zip(headers, data))
        cursor.close()
        conn.close()
        return render_template('user_personal_type.html', user_info=user_personal_type_info)
    except pyodbc.Error as e:
        error_message = f"Database error: {e}"
        return render_template('error.html', error_message=error_message)


@app.route('/user-match/<display_name>')
def show_user_match_rates(display_name):
    try:
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            CASE 
                WHEN u1.display_name = ? THEN u1.display_name 
                ELSE u2.display_name 
            END AS user_name_1,
            CASE 
                WHEN u1.display_name = ? THEN u1.profile_image_url 
                ELSE u2.profile_image_url 
            END AS user_image_1,
            CASE 
                WHEN u1.display_name = ? THEN u2.display_name 
                ELSE u1.display_name 
            END AS user_name_2,
            CASE 
                WHEN u1.display_name = ? THEN u2.profile_image_url 
                ELSE u1.profile_image_url 
            END AS user_image_2,
            upmD.final_match_rate_percentage,
            CASE 
                WHEN u1.display_name = ? THEN uaf1.personal_type 
                ELSE uaf2.personal_type 
            END AS user1_personal_type,
            CASE 
                WHEN u1.display_name = ? THEN uaf2.personal_type 
                ELSE uaf1.personal_type 
            END AS user2_personal_type
        FROM 
            UserPairMatchRateWithDisplayNamesTable upmD
        JOIN 
            Users u1 ON upmD.user_display_name_1 = u1.display_name
        JOIN 
            Users u2 ON upmD.user_display_name_2 = u2.display_name
        JOIN 
            UserClusters uaf1 ON u1.user_id = uaf1.user_id
        JOIN 
            UserClusters uaf2 ON u2.user_id = uaf2.user_id
        WHERE 
            u1.display_name = ? OR u2.display_name = ?
        ORDER BY 
            upmD.final_match_rate_percentage DESC
        """, (display_name, display_name, display_name, display_name, display_name, display_name, display_name, display_name))
        data = cursor.fetchall()
        headers = [column[0] for column in cursor.description]
        rows = []
        for row in data:
            row = list(row)
            if not row[1] or not row[1].strip():
                row[1] = get_gender_icon(row[0])
            if not row[3] or not row[3].strip():
                row[3] = get_gender_icon(row[2])
            rows.append(row)
        cursor.close()
        conn.close()
        return render_template('user_match.html', headers=headers, rows=rows, display_name=display_name)
    except pyodbc.Error as e:
        error_message = f"Database error: {e}"
        return render_template('error.html', error_message=error_message)


if __name__ == "__main__":
    app.run(debug=True)
