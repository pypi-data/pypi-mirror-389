#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Converted from Jupyter Notebook: naive_bayes.ipynb
Conversion Date: 2025-11-05T14:27:54.168Z
"""

# 
# Simple PageRank Implementation
# 
# steps:
# Read or define the adjacency matrix A of the graph.
# 
# Set an initial rank vector V₀ = [1/n, 1/n, …, 1/n], where n is the number of nodes.
# 
# Repeat:
# 
# V_i = A x V_i-1
# 
# 
# until convergence (i.e., V_i ≈ V_{i-1}).
# ---
# 
# 

import numpy as np

# Step 1: Define the adjacency matrix
# Rows = pages, Columns = incoming links
A = np.array([
    [0, 1, 1, 0],  # Page 1 gets links from Pages 2 and 3
    [1, 0, 0, 1],  # Page 2 gets links from Pages 1 and 4
    [0, 1, 0, 1],  # Page 3 gets links from Pages 2 and 4
    [0, 0, 1, 0]   # Page 4 gets link from Page 3
])

# Step 2: Normalize columns so that each column sums to 1
# (represents the probability of jumping from one page to another)
col_sum = np.sum(A, axis=0)
A = A / col_sum

# Step 3: Initialize the rank vector (equal probability for each page)
n = A.shape[0]
V = np.ones(n) / n  # e.g., for 4 pages → [0.25, 0.25, 0.25, 0.25]

# Step 4: Iteratively compute PageRank values
print("Iterations:\n")
for i in range(1, 101):  # limit to 100 iterations
    new_V = np.dot(A, V)  # Multiply matrix with current rank vector
    print(f"Iteration {i}: {new_V.round(6)}")  # Show rank values after each iteration

    # Stop if the values converge (no major changes)
    if np.allclose(V, new_V, atol=1e-6):
        print(f"\nConverged after {i} iterations.")
        break

    V = new_V  # Update rank vector

# Step 5: Display final PageRank values
print("\nFinal PageRank Values:")
print(V)

# PageRank with Damping Factor (Web Surfer Model)
# To handle spider traps and dead ends, we use a damping factor
# 
# d=0.85:
# 
# 𝑃
# 𝑅 =
# 𝑑
# (
# 𝐴
# 𝑉
# )
# +
# (
# 1
# −
# 𝑑
# ) /
# 𝑛
# 
# 	
# 

import numpy as np

# Step 1: Define the adjacency matrix
# Rows = pages, Columns = incoming links
A = np.array([
    [0, 1, 1, 0],  # Page 1 gets links from Pages 2 and 3
    [1, 0, 0, 1],  # Page 2 gets links from Pages 1 and 4
    [0, 1, 0, 1],  # Page 3 gets links from Pages 2 and 4
    [0, 0, 1, 0]   # Page 4 gets link from Page 3
])

# Step 2: Normalize columns so each column sums to 1
# (represents probability of following a link)
col_sum = np.sum(A, axis=0)
A = A / col_sum

# Step 3: Initialize rank vector (equal probability for all pages)
n = A.shape[0]
V = np.ones(n) / n  # e.g., for 4 pages → [0.25, 0.25, 0.25, 0.25]

# Step 4: Define damping factor (probability of following a link)
d = 0.85

# Step 5: Iteratively compute PageRank with damping factor
print("Iterations:\n")
for i in range(1, 101):  # Run up to 100 iterations
    # Formula: new_V = d * (A @ V) + (1 - d) / n
    new_V = d * np.dot(A, V) + (1 - d) / n

    # Show rank values at each iteration
    print(f"Iteration {i}: {new_V.round(6)}")

    # Check for convergence (if change < 0.000001)
    if np.allclose(V, new_V, atol=1e-6):
        print(f"\nConverged after {i} iterations.")
        break

    V = new_V  # Update PageRank vector

# Step 6: Display final PageRank values
print("\nFinal PageRank Values:")
print(V)


# HITS Algorithm


import numpy as np

# Step 1: Define adjacency matrix (A[i][j] = 1 if page i links to page j)
A = np.array([
    [0, 1, 1, 0],  # Page 1 links to 2 and 3
    [0, 0, 1, 0],  # Page 2 links to 3
    [1, 0, 0, 1],  # Page 3 links to 1 and 4
    [0, 0, 0, 1]   # Page 4 links to itself
])

# Number of pages
n = A.shape[0]

# Step 2: Initialize authority and hub scores (start with equal values)
authority = np.ones(n)
hub = np.ones(n)

# Step 3: Iteratively update hub and authority scores
print("Iterations:\n")
for i in range(1, 101):
    # Authority = sum of hub scores of pages linking to it → A^T * hub
    new_authority = np.dot(A.T, hub)

    # Hub = sum of authority scores of pages it links to → A * authority
    new_hub = np.dot(A, new_authority)

    # Normalize both vectors to prevent values from exploding
    new_authority = new_authority / np.linalg.norm(new_authority)
    new_hub = new_hub / np.linalg.norm(new_hub)

    print(f"Iteration {i}:")
    print(f" Authority: {new_authority.round(4)}")
    print(f" Hub:       {new_hub.round(4)}\n")

    # Check for convergence
    if np.allclose(authority, new_authority, atol=1e-6) and np.allclose(hub, new_hub, atol=1e-6):
        print(f"Converged after {i} iterations.\n")
        break

    authority = new_authority
    hub = new_hub

# Step 4: Print final scores
print("Final Authority Scores:", authority.round(4))
print("Final Hub Scores:", hub.round(4))
