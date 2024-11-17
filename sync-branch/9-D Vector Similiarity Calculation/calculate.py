import tkinter as tk
from tkinter import messagebox
import numpy as np
import plotly.graph_objects as go
from sklearn.cluster import KMeans


# Default Vectors
default_vector_1 = [
    0.723043641032758, 0.572767559225287, 0.7740504988479,
    0.637479661742038, 0.433015589308273, 0.0902976822187196,
    0.168220142168479, 0.554631038143581, 0.606259878663072
]
default_vector_2 = [
    0.456827280068541, 0.522026493597796, 0.676255036808873,
    0.292045965551537, 0.502120130655279, 0.155771728203559,
    0.228667904754277, 0.423454946360215, 0.595914473225232
]
dimensions = [f"D{i}" for i in range(1, 10)]



data = np.array([default_vector_1, default_vector_2])  # Each row is a vector
kmeans = KMeans(n_clusters=2, random_state=42).fit(data)

print(f"Cluster Labels: {kmeans.labels_}")
print(f"Cluster Labels: {kmeans}")


# Function to Calculate Metrics
def calculate_metrics(v1, v2):
    v1, v2 = np.array(v1), np.array(v2)
    # Cosine Similarity
    dot_product = np.dot(v1, v2)
    magnitude = np.linalg.norm(v1) * np.linalg.norm(v2)
    cosine_similarity = dot_product / magnitude if magnitude != 0 else 0

    # Absolute Differences
    differences = np.abs(v1 - v2)
    avg_difference = np.mean(differences)

    # Standard Deviation of Differences
    std_dev = np.std(differences)

    return cosine_similarity, avg_difference, std_dev, differences

# Function to Show Heatmap and Radar Chart
def visualize_charts():
    try:
        # Calculate metrics
        cosine_similarity, avg_difference, std_dev, differences = calculate_metrics(
            default_vector_1, default_vector_2
        )

        # Heatmap
        heatmap = go.Figure(data=go.Heatmap(
            z=[default_vector_1, default_vector_2],
            x=dimensions,
            y=["Vector 1", "Vector 2"],
            colorscale="Viridis"
        ))
        heatmap.update_layout(title="Heatmap of Vectors")

        # Radar Chart
        angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
        angles += angles[:1]
        radar_vector_1 = default_vector_1 + [default_vector_1[0]]
        radar_vector_2 = default_vector_2 + [default_vector_2[0]]
        radar_chart = go.Figure()
        radar_chart.add_trace(go.Scatterpolar(
            r=radar_vector_1,
            theta=dimensions + [dimensions[0]],
            fill='toself',
            name='Vector 1'
        ))
        radar_chart.add_trace(go.Scatterpolar(
            r=radar_vector_2,
            theta=dimensions + [dimensions[0]],
            fill='toself',
            name='Vector 2'
        ))
        radar_chart.update_layout(title="Radar Chart of Vectors")

        # Display metrics
        metrics_text = (
            f"Cosine Similarity: {cosine_similarity:.4f}\n"
            f"Average Difference: {avg_difference:.4f}\n"
            f"Standard Deviation: {std_dev:.4f}\n"
            f"Dimension Differences: {', '.join([f'{d:.4f}' for d in differences])}"
        )
        lbl_metrics.config(text=metrics_text)

        # Show charts
        heatmap.show()
        radar_chart.show()

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# GUI Setup
root = tk.Tk()
root.title("Vector Analysis and Visualization")

# Instruction Label
tk.Label(root, text="Analyze and visualize vectors using Heatmap and Radar Chart").grid(
    row=0, column=0, columnspan=2, pady=10
)

# Visualize Button
btn_visualize = tk.Button(root, text="Visualize Charts and Metrics", command=visualize_charts)
btn_visualize.grid(row=1, column=0, columnspan=2, pady=10)

# Metrics Display
lbl_metrics = tk.Label(root, text="Metrics will be displayed here.", justify="left", anchor="w", bg="lightgray", width=60, height=10)
lbl_metrics.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

# Run the GUI
root.mainloop()
