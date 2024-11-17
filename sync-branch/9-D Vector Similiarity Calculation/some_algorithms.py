import pyodbc
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from math import sin
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

CONNECTION_STRING = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_HOST},{DB_PORT};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD}"

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
users = [row[0] for row in data]  # List of user IDs
vectors = [list(row[1:]) for row in data]  # List of feature vectors

# Feature Weights (Optional)
feature_weights = np.array([0.2, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])

# Function to calculate the radar chart area
def calculate_radar_area(radii, angles):
    n = len(radii)
    area = 0.0
    for i in range(n - 1):
        area += 0.5 * radii[i] * radii[i + 1] * abs(sin(angles[i + 1] - angles[i]))
    return abs(area)

# Convert polar to Cartesian coordinates for intersection calculation
def polar_to_cartesian(radii, angles):
    x = radii * np.cos(angles)
    y = radii * np.sin(angles)
    return np.column_stack((x, y))

# Initialize similarity results
similarity_results = []

# Initialize the progress bar
total_comparisons = len(users) * (len(users) - 1) // 2
with tqdm(total=total_comparisons, desc="Calculating Similarities") as pbar:
    # Iterate through all pairs of users
    for i in range(len(users)):
        for j in range(i + 1, len(users)):
            # Prepare weighted vectors
            vector_1 = np.array(vectors[i]) * feature_weights
            vector_2 = np.array(vectors[j]) * feature_weights

            # Radar Chart Angles
            angles = np.linspace(0, 360, len(vector_1), endpoint=False)
            angles = np.deg2rad(np.append(angles, angles[0]))

            # Add closing value for radar chart
            vector_1 = np.append(vector_1, vector_1[0])
            vector_2 = np.append(vector_2, vector_2[0])

            # Calculate Areas
            area_vector_1 = calculate_radar_area(vector_1, angles)
            area_vector_2 = calculate_radar_area(vector_2, angles)

            # Calculate Intersection Area
            polygon_1 = Polygon(polar_to_cartesian(vector_1, angles))
            polygon_2 = Polygon(polar_to_cartesian(vector_2, angles))
            intersection_area = polygon_1.intersection(polygon_2).area

            # Calculate Similarity
            bigger_area = max(area_vector_1, area_vector_2)
            similarity = (intersection_area / bigger_area) * 100

            # Append results
            similarity_results.append({
                "User 1": users[i],
                "User 2": users[j],
                "Similarity (%)": round(similarity, 2)
            })

            # Plot Radar Chart
            fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
            ax.plot(angles, vector_1, label=f"User {users[i]}", color="blue")
            ax.fill(angles, vector_1, color="blue", alpha=0.25)
            ax.plot(angles, vector_2, label=f"User {users[j]}", color="green")
            ax.fill(angles, vector_2, color="green", alpha=0.25)
            ax.set_title(f"Radar Chart (Similarity: {similarity:.2f}%)")
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(["danceability", "energy", "loudness", "speechiness", "acousticness",
                                "instrumentalness", "liveness", "valence", "tempo"])
            ax.legend()
            # Uncomment below line to view radar charts during the process
            # plt.show()
            plt.close(fig)  # Close the figure to avoid memory issues

            # Update progress bar
            pbar.update(1)

# Convert results to DataFrame
similarity_df = pd.DataFrame(similarity_results)

# Display similarity table
print("Similarity Results:")
print(similarity_df)

# Save similarity table to a CSV file
similarity_df.to_csv("similarity_results.csv", index=False)
