#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Converted from Jupyter Notebook: clustering.ipynb
Conversion Date: 2025-11-05T14:19:52.321Z
"""

# -------------------------------
# Part 1: K-Means (Manual Implementation)
# -------------------------------

# to calculate Euclidean distance in 3D
import warnings
warnings.filterwarnings("ignore")  # suppress all sklearn/pandas/numpy warnings
def euclidean_distance(p1, p2):
    return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2) ** 0.5


# checking if centroids have converged
def converged(centroids, prev_centroids, tolerance=1e-4):
    for c1, c2 in zip(centroids, prev_centroids):
        if euclidean_distance(c1, c2) > tolerance:
            return False
    return True


# assign points to nearest centroid
def assign_clusters(points, centroids):
    clusters = {0: [], 1: [], 2: []}
    for point in points:
        distances = [
            euclidean_distance(point, centroids[0]),
            euclidean_distance(point, centroids[1]),
            euclidean_distance(point, centroids[2])
        ]
        cluster = distances.index(min(distances))
        clusters[cluster].append(point)
    return clusters


# compute new centroids
def update_centroids(clusters):
    centroids = []
    for i in range(3):
        if len(clusters[i]) > 0:
            x = sum([p[0] for p in clusters[i]]) / len(clusters[i])
            y = sum([p[1] for p in clusters[i]]) / len(clusters[i])
            z = sum([p[2] for p in clusters[i]]) / len(clusters[i])
            centroid = [x, y, z]
        else:
            centroid = [float(i*10), float(i*10), float(i*10)]
        centroids.append(centroid)
    return centroids


def kmeans_3d(points, initial_centroids, max_iters=100):
    centroids = initial_centroids
    prev_centroids = [[0, 0, 0] for _ in range(3)]
    iteration = 0

    while not converged(centroids, prev_centroids) and iteration < max_iters:
        print(f"\n--- Iteration {iteration + 1} ---")

        # save previous centroids
        prev_centroids = [c[:] for c in centroids]

        # Step 1: Assign points to clusters
        clusters = assign_clusters(points, centroids)

        # Step 2: Print clusters
        for i in range(3):
            print(f"Cluster {i + 1}: {clusters[i]}")

        # Step 3: Update centroids
        centroids = update_centroids(clusters)
        print(f"Updated Centroids: {centroids}")

        iteration += 1

    print("\n✅ Clustering completed!")
    return clusters, centroids


def main():
    points = [
        [2, 4, 10], [12, 3, 20], [30, 11, 25], [23, 10, 6],
        [7, 15, 18], [5, 6, 9], [16, 19, 3], [11, 5, 8],
        [9, 12, 7], [14, 3, 16]
    ]

    print("Using initial centroids for 3 clusters:")
    m1 = [2, 4, 10]
    m2 = [12, 3, 20]
    m3 = [30, 11, 25]
    initial_centroids = [m1, m2, m3]

    clusters, final_centroids = kmeans_3d(points, initial_centroids)

    print("\nFinal Clusters and Centroids:")
    for i in range(3):
        print(f"Cluster {i + 1}: {clusters[i]}")
    print(f"Final Centroids: {final_centroids}")


if __name__ == "__main__":
    main()


# -------------------------------
# Part 2: K-Means using scikit-learn
# -------------------------------

# ✅ Correct: use subprocess to install package (since `pip install` is invalid in .py)
import subprocess
import sys

try:
    import sklearn
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn"])

from sklearn.cluster import KMeans
import numpy as np

# Input points (same as your manual version)
points = np.array([
    [2, 4, 10], [12, 3, 20], [30, 11, 25], [23, 10, 6],
    [7, 15, 18], [5, 6, 9], [16, 19, 3], [11, 5, 8],
    [9, 12, 7], [14, 3, 16]
])

# Initial centroids for 3 clusters
centroids = np.array([
    [2, 4, 10],
    [12, 3, 20],
    [30, 11, 25]
])

prev_centroids = None
iteration = 0

# Run until centroids stop changing
while True:
    iteration += 1
    print(f"\n--- Iteration {iteration} ---")

    kmeans = KMeans(n_clusters=3, init=centroids, n_init=1, max_iter=1, random_state=0)
    kmeans.fit(points)

    labels = kmeans.labels_
    centroids = kmeans.cluster_centers_

    for i in range(3):
        cluster_points = points[labels == i].tolist()
        print(f"Cluster {i + 1}: {cluster_points}")
    print("Updated Centroids:", centroids.tolist())

    if prev_centroids is not None and np.allclose(prev_centroids, centroids):
        break
    prev_centroids = centroids.copy()

print("\n✅ Clustering Completed!")
for i in range(3):
    print(f"Final Cluster {i + 1}: {points[labels == i].tolist()}")
print("Final Centroids:", centroids.tolist())
