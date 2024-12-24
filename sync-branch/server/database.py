from flask import Blueprint, request, jsonify
from utils import execute_query_with_logging, get_gender_icon

# Define the Blueprint for database-related routes
database_bp = Blueprint('database', __name__)

@database_bp.route('/get_all_matches', methods=['POST'])
def get_all_matches():
    """Retrieve all matches for a user based on match rates."""
    payload = request.json
    user_id = payload.get('user_id')
    db_name = payload.get('db_name', 'primary')  # Default to the primary database

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    query = """
WITH RankedMatches AS (
    SELECT 
        CASE WHEN u1.user_id = ? THEN u2.user_id ELSE u1.user_id END AS match_user_id,
        CASE WHEN u1.user_id = ? THEN u2.display_name ELSE u1.display_name END AS match_user_name,
        CASE WHEN u1.user_id = ? THEN u2.profile_image_url ELSE u1.profile_image_url END AS match_user_image,
        upmD.final_match_rate_percentage,
        CASE WHEN u1.user_id = ? THEN uaf2.personal_type ELSE uaf1.personal_type END AS match_user_type,
        CASE 
            WHEN u1.user_id = ? THEN uaf1.personal_type
            ELSE uaf2.personal_type
        END AS type1,
        CASE 
            WHEN u1.user_id = ? THEN uaf2.personal_type
            ELSE uaf1.personal_type
        END AS type2,
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
SELECT
    rm.match_user_id,
    rm.match_user_name,
    rm.match_user_image,
    rm.final_match_rate_percentage,
    rm.match_user_type,
    ptmd.description AS match_type_desc
FROM 
    RankedMatches rm
LEFT JOIN 
    personal_type_match ptmd
ON 
    (rm.type1 = ptmd.type_1 AND rm.type2 = ptmd.type_2) OR 
    (rm.type1 = ptmd.type_2 AND rm.type2 = ptmd.type_1)
WHERE 
    rm.rn = 1
ORDER BY final_match_rate_percentage DESC;
    """

    try:
        params = [user_id] * 9
        data, description = execute_query_with_logging(query, db_name, params=params, fetch=True)
        columns = [desc[0] for desc in description]
        result = [dict(zip(columns, row)) for row in data]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@database_bp.route('/user-profile', methods=['POST'])
def user_profile():
    payload = request.json
    user_id = payload.get('user_id')
    db_name = payload.get('db_name', 'primary')  # Default to the primary database
    query = """
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
        """
    try:
        params = [user_id] * 1
        data, description = execute_query_with_logging(query, db_name, params=params, fetch=True)
        user_info = data[0]
        user_info = {
            "user_id": user_info[0],
            "display_name": user_info[1],
            "profile_image_url": user_info[2] or'https://sync-branch.yggbranch.dev/assets/default_user.png' or get_gender_icon(user_info[1]) ,
            "personal_type": user_info[3],
            "type_description": user_info[4]
        }
        return user_info, 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@database_bp.route('/get_top5_matches', methods=['POST'])
def get_top5_matches():
    """Retrieve all matches for a user based on match rates."""
    payload = request.json
    user_id = payload.get('user_id')
    db_name = payload.get('db_name', 'primary')  # Default to the primary database

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    query = """
        WITH RankedMatches AS (
    SELECT 
        CASE WHEN u1.user_id = ? THEN u2.user_id ELSE u1.user_id END AS match_user_id,
        CASE WHEN u1.user_id = ? THEN u2.display_name ELSE u1.display_name END AS match_user_name,
        CASE WHEN u1.user_id = ? THEN u2.profile_image_url ELSE u1.profile_image_url END AS match_user_image,
        upmD.final_match_rate_percentage,
        CASE WHEN u1.user_id = ? THEN uaf2.personal_type ELSE uaf1.personal_type END AS match_user_type,
        CASE 
            WHEN u1.user_id = ? THEN uaf1.personal_type
            ELSE uaf2.personal_type
        END AS type1,
        CASE 
            WHEN u1.user_id = ? THEN uaf2.personal_type
            ELSE uaf1.personal_type
        END AS type2,
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
    rm.match_user_id,
    rm.match_user_name,
    rm.match_user_image,
    rm.final_match_rate_percentage,
    rm.match_user_type,
    ptmd.description AS match_type_desc
FROM 
    RankedMatches rm
LEFT JOIN 
    personal_type_match ptmd
ON 
    (rm.type1 = ptmd.type_1 AND rm.type2 = ptmd.type_2) OR 
    (rm.type1 = ptmd.type_2 AND rm.type2 = ptmd.type_1)
WHERE 
    rm.rn = 1
ORDER BY final_match_rate_percentage DESC;
    """

    username_query = "SELECT username From users where spotify_user_id = ?"

    try:
        params = [user_id] * 9
        data, description = execute_query_with_logging(query, db_name, params=params, fetch=True)
        columns = [desc[0] for desc in description]
        result = [dict(zip(columns, row)) for row in data]
        
        # 1) Gather all match_user_ids
        match_user_ids = [row["match_user_id"] for row in result]
        
        # 2) Build an 'IN' clause with placeholders
        placeholders = ",".join(["?"] * len(match_user_ids))  # "?, ?, ?"
        username_query = f"SELECT spotify_user_id, username FROM users WHERE spotify_user_id IN ({placeholders})"
        
        db_name = "flutter"
        
        # 3) Execute the query once, passing all match_user_ids as params
        data, description = execute_query_with_logging(username_query, db_name, params=match_user_ids, fetch=True)
        columns = [desc[0] for desc in description]  # e.g. ['spotify_user_id', 'username']
        rows = [dict(zip(columns, row)) for row in data]
        
        # Convert rows into a dict for quick lookup: {spotify_user_id: username, ...}
        user_dict = {row["spotify_user_id"]: row["username"] for row in rows}
        
        # 4) Loop through 'result' and enrich with username from users table
        for row in result:
            match_id = row["match_user_id"]
            row["matched_username"] = user_dict.get(match_id, None)  # or default if not found
        
        #data, description = execute_query_with_logging(username_query, db_name, params=params, fetch=True)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@database_bp.route('/get_recent', methods=['POST'])
def get_recent():
    """Retrieve recent activity for a user based on user_id."""
    payload = request.json
    user_id = payload.get('spotify_user_id')
    db_name = payload.get('db_name', 'primary')  # Default to the primary database

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    query = """
SELECT TOP 5
    ut.user_id, 
    ut.track_id, 
    t.name AS track_name, 
    a.name AS artist_name,
    ut.listened_at,
    t.images
FROM 
    User_Recent_Tracks ut
JOIN 
    Tracks t ON ut.track_id = t.track_id
JOIN 
    Track_Artists ta ON t.track_id = ta.track_id
JOIN 
    Artists a ON ta.artist_id = a.artist_id
WHERE 
    ut.user_id = ?
ORDER BY 
    ut.listened_at DESC;

    """

    try:
        params = [user_id]
        data, description = execute_query_with_logging(query, db_name, params=params, fetch=True)
        columns = [desc[0] for desc in description]
        result = [dict(zip(columns, row)) for row in data]
        if result == []:
            result = [{"Error":"User Don't have recent!"}] 
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

