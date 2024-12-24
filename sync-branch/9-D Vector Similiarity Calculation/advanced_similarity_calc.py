import pyodbc
import numpy as np
from shapely.geometry import Polygon
import pandas as pd
from tqdm import tqdm  # For the progress bar
from dotenv import load_dotenv
import os

load_dotenv()

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

# Connect to the database
conn = pyodbc.connect(CONNECTION_STRING)

# Fetch normalized user audio features
query = """
SELECT 
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
FROM NormalizedUserAudioFeatures
"""
cursor = conn.cursor()
cursor.execute(query)

# Fetch data into Python
data = cursor.fetchall()
conn.close()

# Prepare vectors
users = [row[0] for row in data]  
raw_vectors = [list(row[1:]) for row in data]  

# Feature Weights (tweak as needed)
feature_weights = np.array([0.2, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1, 0.05, 0.05])

# Create weighted vectors (radii) upfront
weighted_vectors = []
for vec in raw_vectors:
    # Multiply each dimension by its corresponding weight
    weighted_vec = np.array(vec) * feature_weights
    weighted_vectors.append(weighted_vec)

weighted_vectors = np.array(weighted_vectors)

#####################################
# Radar Chart + Polygon Computation #
#####################################

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
    1. Spreading angles equally around 360 degrees,
    2. Converting to (x, y),
    3. Making a Polygon via Shapely.
    """
    n = len(radii)
    # Equally spaced angles from 0 to 2π
    angles = np.linspace(0, 2*np.pi, n, endpoint=False)
    
    # Close the loop by repeating the first radius/angle at the end
    radii_closed = np.append(radii, radii[0])
    angles_closed = np.append(angles, angles[0])

    # Convert to cartesian
    points = polar_to_cartesian(radii_closed, angles_closed)

    # Make a polygon
    polygon = Polygon(points)
    return polygon

def intersection_over_union_area(poly1, poly2):
    """
    Compute IoU for two polygons: intersection_area / union_area.
    If both polygons are empty, return 0.0
    """
    intersection_area = poly1.intersection(poly2).area
    union_area = poly1.union(poly2).area
    if union_area == 0.0:
        # Edge case: both polygons might be degenerate or empty
        return 0.0
    return intersection_area / union_area


###################
# Main Comparison #
###################

similarity_results = []

# Initialize the progress bar
num_users = len(users)
total_comparisons = num_users * (num_users - 1) // 2

with tqdm(total=total_comparisons, desc="Calculating Area-Based Similarities") as pbar:
    for i in range(num_users):
        # Pre-build polygon for user i
        polygon_i = calculate_polygon(weighted_vectors[i])

        for j in range(i + 1, num_users):
            # Pre-build polygon for user j
            polygon_j = calculate_polygon(weighted_vectors[j])

            # Compute Intersection over Union (IoU)
            iou = intersection_over_union_area(polygon_i, polygon_j)

            # Turn it into percentage
            similarity_percentage = iou * 100

            similarity_results.append({
                "User 1": users[i],
                "User 2": users[j],
                "Similarity (%)": round(similarity_percentage, 2)
            })

            # Optional: Plot Radar Chart
            # (comment out if you don't want plots)
            """
            fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
            
            n_features = len(weighted_vectors[i])
            angles = np.linspace(0, 2*np.pi, n_features, endpoint=False)
            angles_closed = np.append(angles, angles[0])
            
            # Close the loop for plotting
            user_i_r = np.append(weighted_vectors[i], weighted_vectors[i][0])
            user_j_r = np.append(weighted_vectors[j], weighted_vectors[j][0])

            ax.plot(angles_closed, user_i_r, label=f"User {users[i]}", color="blue")
            ax.fill(angles_closed, user_i_r, color="blue", alpha=0.25)
            ax.plot(angles_closed, user_j_r, label=f"User {users[j]}", color="green")
            ax.fill(angles_closed, user_j_r, color="green", alpha=0.25)
            
            feature_labels = [
                "dance", "energy", "loud", "speech", "acoustic",
                "instrum", "live", "valence", "tempo"
            ]
            ax.set_xticks(angles)
            ax.set_xticklabels(feature_labels)
            ax.set_title(f"IoU Similarity: {similarity_percentage:.2f}%")
            ax.legend(loc="upper right")
            
            plt.show()
            """
            
            # Update progress bar
            pbar.update(1)

# Convert results to DataFrame
similarity_df = pd.DataFrame(similarity_results)

# Display or save similarity table
print("Similarity Results (Area-Based IoU):")
print(similarity_df)

similarity_df.to_csv("similarity_results_area_iou.csv", index=False)
