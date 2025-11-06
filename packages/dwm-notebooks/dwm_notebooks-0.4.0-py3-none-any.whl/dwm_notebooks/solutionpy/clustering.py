#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Converted from Jupyter Notebook: notebook.ipynb
Conversion Date: 2025-11-05T14:18:52.302Z
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.cluster import AgglomerativeClustering


file_path = 'Mall_Customers.csv'
df = pd.read_csv(file_path)

print("First 5 rows of dataset:")
print(df.head())

features_for_clustering = df[['Annual Income (k$)', 'Spending Score (1-100)']].copy()
print("\nSelected features for clustering:")
print(features_for_clustering.head())

linkage_matrix = linkage(features_for_clustering, method='ward')
plt.figure(figsize=(10, 6))
dendrogram(linkage_matrix)
plt.title('Dendrogram for Hierarchical Clustering')
plt.xlabel('Customers')
plt.ylabel('Euclidean Distances')
plt.show()

agglomerative_model = AgglomerativeClustering()
df['cluster_label'] = agglomerative_model.fit_predict(features_for_clustering)

print("\nData with cluster labels:")
print(df.head())
plt.figure(figsize=(10, 7))
scatter = plt.scatter(df['Annual Income (k$)'], df['Spending Score (1-100)'],
                      c=df['cluster_label'], cmap='viridis', s=50)
plt.xlabel('Annual Income (k$)')
plt.ylabel('Spending Score (1-100)')
plt.title('Hierarchical Clustering of Mall Customers')
plt.legend(*scatter.legend_elements(), title="Clusters", loc="upper left")
plt.show()



import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import kagglehub
from kagglehub import KaggleDatasetAdapter

file_path = "student_exam_scores.csv"

df = kagglehub.load_dataset(KaggleDatasetAdapter.PANDAS,"saadaliyaseen/analyzing-student-academic-trends",file_path)
print( df.head())

!ls /kaggle/input/analyzing-student-academic-trends


features_for_clustering = df[['hours_studied', 'previous_scores']].copy()
print("Selected features for clustering:")
display(features_for_clustering.head())

from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.cluster import AgglomerativeClustering

linkage_matrix = linkage(features_for_clustering, method='ward')
plt.figure(figsize=(10, 6))
dendrogram(linkage_matrix)
plt.title('Dendrogram for Hierarchical Clustering')
plt.show()


agglomerative_model = AgglomerativeClustering()
agglomerative_model.fit(features_for_clustering)
df['cluster_label'] = agglomerative_model.labels_
display(df.head())

plt.figure(figsize=(10, 7))
scatter = plt.scatter(df['hours_studied'], df['previous_scores'], c=df['cluster_label'], cmap='viridis', s=50)
plt.xlabel('Hours Studied')
plt.ylabel('Previous Scores')
plt.title('Hierarchical Clustering of Students based on Hours Studied and Previous Scores')
legend_labels = [f'Cluster {i}' for i in range(optimal_clusters)]
plt.legend(*scatter.legend_elements(), title="Clusters", loc="upper left")
plt.show()
