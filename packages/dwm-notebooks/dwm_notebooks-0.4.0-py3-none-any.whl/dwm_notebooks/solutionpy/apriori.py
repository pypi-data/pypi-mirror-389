#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Converted from Jupyter Notebook: notebook.ipynb
Conversion Date: 2025-11-05T14:16:37.680Z
"""

from itertools import combinations  # Used to generate item combinations

# 🧩 Step 1: Input Dataset
transactions = [
    ['A', 'B', 'C'],
    ['A', 'C'],
    ['A', 'D'],
    ['B', 'E'],
    ['A', 'B', 'C', 'E']
]

# Minimum thresholds for support and confidence
min_support = 0.4      # 40%
min_confidence = 0.7   # 70%

# 📊 Step 2: Function to calculate support of an itemset
def get_support(itemset, transactions):
    count = sum(1 for t in transactions if itemset.issubset(t))  # Count transactions containing the itemset
    return count / len(transactions)  # Support = count / total transactions

# ⚙️ Step 3: Function to generate candidate itemsets of size k
def generate_candidates(freq_sets, k):
    # Combine itemsets to create larger ones of size k
    return {i | j for i in freq_sets for j in freq_sets if len(i | j) == k}

# 🔍 Step 4: Filter itemsets that meet minimum support
def get_frequent_itemsets(candidates, transactions, min_support):
    freq_sets, support_data = set(), {}  # Store frequent sets and their supports
    for itemset in candidates:
        support = get_support(itemset, transactions)  # Calculate support
        if support >= min_support:  # Keep only those above threshold
            freq_sets.add(itemset)
        support_data[itemset] = support  # Store all supports
    return freq_sets, support_data

# 🚀 Step 5: Main Apriori function
def apriori(transactions, min_support):
    # Start with all single items
    single_items = {frozenset([i]) for t in transactions for i in t}

    # Get frequent 1-itemsets
    freq_sets, support_data = get_frequent_itemsets(single_items, transactions, min_support)

    all_freq_sets, all_support = set(freq_sets), dict(support_data)  # To store all frequent sets
    k = 2  # Start combining into 2-itemsets

    # Generate higher-order frequent itemsets
    while freq_sets:
        candidates = generate_candidates(freq_sets, k)  # Make new candidates
        freq_sets, item_support = get_frequent_itemsets(candidates, transactions, min_support)
        all_freq_sets |= freq_sets  # Add to global frequent sets
        all_support.update(item_support)  # Update support data
        k += 1

    return all_freq_sets, all_support

# 🔗 Step 6: Generate strong association rules
def generate_rules(freq_sets, support_data, min_confidence):
    rules = []
    for itemset in freq_sets:
        if len(itemset) > 1:  # Only for sets with 2+ items
            for consequent in map(frozenset, combinations(itemset, 1)):  # Try all possible consequents
                antecedent = itemset - consequent
                confidence = support_data[itemset] / support_data[antecedent]  # Calculate confidence
                if confidence >= min_confidence:
                    rules.append((set(antecedent), set(consequent), confidence))  # Store rule
    return rules

# ▶️ Step 7: Execute Apriori
freq_sets, support_data = apriori(transactions, min_support)
rules = generate_rules(freq_sets, support_data, min_confidence)

# 🖨️ Step 8: Output results
print("=== Frequent Itemsets ===")
for item, sup in support_data.items():
    if sup >= min_support:
        print(f"{set(item)} : Support = {round(sup, 2)}")

print("\n=== Strong Association Rules (Confidence ≥ 0.7) ===")
for ant, con, conf in rules:
    print(f"{ant} → {con} (Confidence = {round(conf, 2)})")


import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

# Step 1: Dataset
dataset = [
    ['Milk', 'Bread', 'Butter'],
    ['Bread', 'Eggs'],
    ['Milk', 'Bread', 'Eggs', 'Butter'],
    ['Bread', 'Butter'],
    ['Milk', 'Eggs']
]

# Step 2: Convert transactions into a DataFrame
items = sorted(list(set([item for t in dataset for item in t])))  # Unique list of all items
encoded_vals = []

for transaction in dataset:
    encoded = {item: (item in transaction) for item in items}  # Encode each transaction as True/False
    encoded_vals.append(encoded)

df = pd.DataFrame(encoded_vals)

# Step 3: Apply Apriori Algorithm
frequent_itemsets = apriori(df, min_support=0.4, use_colnames=True)

# Step 4: Generate Association Rules
rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.7)

# Step 5: Display Results
print("=== Frequent Itemsets ===")
print(frequent_itemsets)

print("\n=== Association Rules ===")
print(rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']])
