import os
import pyodbc
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from dotenv import load_dotenv
import streamlit as st
from io import BytesIO

############################
# 1. LOAD ENV & SETUP DB   #
############################

load_dotenv()  # Load .env file if present

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

CONNECTION_STRING = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={DB_HOST},{DB_PORT};DATABASE={DB_NAME};"
    f"UID={DB_USER};PWD={DB_PASSWORD}"
)


##################################
# 2. DATA FETCH & PREPROCESSING  #
##################################

def get_user_data():
    """
    Connect to the DB and retrieve normalized user audio features.
    The table columns are assumed as:
      [0: display_name, 1: user_id, 2..10: norm_* features]
    """
    conn = pyodbc.connect(CONNECTION_STRING)

    query = """
    SELECT 
        display_name,
        user_id,
        norm_danceability,
        norm_energy,
        norm_loudness,
        norm_speechiness,
        norm_acousticness,
        norm_instrumentalness,
        norm_liveness,
        norm_valence,
        norm_tempo
    FROM NormalizedUserAudioFeaturesWithNames
    """
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    # Parse results
    # 'display_names' will be used in the UI (the front end)
    # 'vectors' will hold the 9 audio features only
    display_names = []
    vectors = []

    for row in data:
        display_name = row[0]
        # user_id   = row[1]  # if you need the user_id for anything else, store it separately
        features   = list(row[2:])  # the 9 feature columns from index 2 to 10

        display_names.append(display_name)
        vectors.append(features)

    return display_names, vectors


#########################
# 3. AREA-BASED LOGIC   #
#########################

# Example feature weights
feature_weights = np.array([0.2, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1, 0.05, 0.05])

def polar_to_cartesian(radii, angles):
    """
    Convert polar coordinates (r, θ) to Cartesian (x, y).
    radii: array of radial lengths
    angles: array of angles in radians
    """
    x = radii * np.cos(angles)
    y = radii * np.sin(angles)
    return np.column_stack((x, y))

def calculate_polygon(radii):
    """
    Create a closed polygon from the given radii by:
    1. Spreading angles equally around 2π
    2. Converting to (x, y)
    3. Building a Shapely Polygon
    """
    n = len(radii)
    angles = np.linspace(0, 2*np.pi, n, endpoint=False)

    # Close the loop by repeating the first radius
    radii_closed = np.append(radii, radii[0])
    angles_closed = np.append(angles, angles[0])

    points = polar_to_cartesian(radii_closed, angles_closed)
    polygon = Polygon(points)
    return polygon

def intersection_over_union_area(poly1, poly2):
    """
    Compute IoU = intersection_area / union_area for two polygons.
    """
    intersection_area = poly1.intersection(poly2).area
    union_area = poly1.union(poly2).area
    if union_area == 0.0:  # Degenerate case
        return 0.0
    return intersection_area / union_area

def compute_area_similarity_table(display_names, raw_vectors):
    """
    Given display_names and raw feature vectors, compute the IoU-based
    similarity for all pairs. Returns a DataFrame with columns:
      "User 1", "User 2", "Similarity (%)"
    """
    weighted_vectors = [np.array(v) * feature_weights for v in raw_vectors]
    n = len(display_names)
    results = []

    for i in range(n):
        poly_i = calculate_polygon(weighted_vectors[i])
        for j in range(i+1, n):
            poly_j = calculate_polygon(weighted_vectors[j])
            iou = intersection_over_union_area(poly_i, poly_j)
            similarity_pct = iou * 100.0

            results.append({
                "User 1": display_names[i],
                "User 2": display_names[j],
                "Similarity (%)": round(similarity_pct, 2)
            })

    df = pd.DataFrame(results)
    return df


##################################
# 4. RADAR CHART PLOTTING LOGIC  #
##################################

def plot_radar_chart(display_name, user_vector, ax, color="blue"):
    """
    Plots a single user's radar polygon on the given polar Axes.
    'display_name' is shown in the legend label.
    """
    n = len(user_vector)
    angles = np.linspace(0, 2*np.pi, n, endpoint=False)
    angles = np.append(angles, angles[0])  # close the loop
    r = np.append(user_vector, user_vector[0])

    ax.plot(angles, r, color=color, label=f"{display_name}")
    ax.fill(angles, r, color=color, alpha=0.25)

    ax.set_xticks(angles[:-1])
    feature_labels = [
        "dance", "energy", "loud", "speech", "acoustic",
        "instrum", "live", "valence", "tempo"
    ]
    ax.set_xticklabels(feature_labels)

def generate_radar_plot(name1, name2, vec1, vec2):
    """
    Generate a radar chart for two users side by side.
    Returns a BytesIO object containing the PNG image data.
    """
    # Weighted vectors
    w_vec1 = np.array(vec1) * feature_weights
    w_vec2 = np.array(vec2) * feature_weights

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

    # Plot each user's polygon
    plot_radar_chart(name1, w_vec1, ax, color="blue")
    plot_radar_chart(name2, w_vec2, ax, color="green")

    ax.legend(loc="upper right")

    # Convert to BytesIO
    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)
    return buf


#########################
# 5. STREAMLIT FRONTEND #
#########################

def main():
    st.title("Music Taste Similarity - Area-Based Radar App")

    # 1. Load data from DB
    try:
        with st.spinner("Loading user data from database..."):
            display_names, raw_vectors = get_user_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    st.success("Data loaded successfully!")

    # 2. Compute IoU similarities
    st.write("Computing area-based similarities (IoU)...")
    similarity_df = compute_area_similarity_table(display_names, raw_vectors)
    st.write("Done!")
    
    # 3. Show table of results
    st.subheader("Overall Similarity Table")
    st.dataframe(similarity_df.sort_values("Similarity (%)", ascending=False))

    # 4. Interactive user selection for radar chart
    st.subheader("Compare Two Users Visually")

    user_choices = list(display_names)  # front-end uses display_names
    user1 = st.selectbox("Select User 1", user_choices, index=0)
    user2 = st.selectbox("Select User 2", user_choices, index=1)

    # Make sure two different names are chosen
    if user1 == user2:
        st.warning("Please select two different users.")
    else:
        # Get the feature vectors for the chosen users
        idx1 = display_names.index(user1)
        idx2 = display_names.index(user2)
        buf = generate_radar_plot(user1, user2, raw_vectors[idx1], raw_vectors[idx2])
        st.image(buf, caption=f"Radar Comparison: {user1} vs. {user2}")

        # Show the numeric similarity
        sub_df = similarity_df[
            ((similarity_df["User 1"] == user1) & (similarity_df["User 2"] == user2)) |
            ((similarity_df["User 1"] == user2) & (similarity_df["User 2"] == user1))
        ]
        if not sub_df.empty:
            sim_val = sub_df["Similarity (%)"].values[0]
            st.info(f"Similarity between {user1} and {user2}: **{sim_val}%**")
        else:
            st.info("No direct pair found in the table. (Possibly an unexpected case.)")

if __name__ == "__main__":
    main()
