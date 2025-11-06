#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Converted from Jupyter Notebook: notebook.ipynb
Conversion Date: 2025-11-05T14:27:18.492Z
"""

# | Device | Category    | Discount | Purchased |
# | ------ | ----------- | -------- | --------- |
# | Mobile | Electronics | High     | Yes       |
# | Laptop | Books       | Low      | No        |
# | Mobile | Fashion     | Medium   | Yes       |
# | Tablet | Books       | Medium   | No        |
# | Laptop | Electronics | High     | Yes       |
# | Mobile | Fashion     | Low      | No        |
# | TV     | Electronics | High     | Yes       |
# | Tablet | Fashion     | Medium   | Yes       |
# | Laptop | Books       | Low      | No        |
# | Mobile | Electronics | High     | Yes       |
# 


import pandas as pd

data = {
    'Device': ['Mobile', 'Laptop', 'Mobile', 'Tablet', 'Laptop', 'Mobile', 'TV', 'Tablet', 'Laptop', 'Mobile'],
    'Category': ['Electronics', 'Books', 'Fashion', 'Books', 'Electronics', 'Fashion', 'Electronics', 'Fashion', 'Books', 'Electronics'],
    'Discount': ['High', 'Low', 'Medium', 'Medium', 'High', 'Low', 'High', 'Medium', 'Low', 'High'],
    'Purchased': ['Yes', 'No', 'Yes', 'No', 'Yes', 'No', 'Yes', 'Yes', 'No', 'Yes']
}

df = pd.DataFrame(data)
prior_probs = df['Purchased'].value_counts(normalize=True).to_dict()
feature_likelihoods = {}

for feature in ['Device', 'Category', 'Discount']:
    feature_likelihoods[feature] = {}
    for purchase_status in df['Purchased'].unique():
        subset = df[df['Purchased'] == purchase_status]
        value_counts = subset[feature].value_counts(normalize=True)
        feature_likelihoods[feature][purchase_status] = value_counts.to_dict()

def predict_given_category_discount(category_value, discount_value):
    posteriors = {}
    for purchase_status in prior_probs.keys():
        posterior_prob = prior_probs[purchase_status]

        for feature, feature_value in [('Category', category_value), ('Discount', discount_value)]:
            likelihood = feature_likelihoods[feature].get(purchase_status, {}).get(feature_value, 1e-6)
            posterior_prob *= likelihood

        posteriors[purchase_status] = posterior_prob

    total_prob = sum(posteriors.values())
    normalized_posteriors = {cls: prob / total_prob for cls, prob in posteriors.items()}

    predicted_class = max(normalized_posteriors, key=normalized_posteriors.get)
    return predicted_class, normalized_posteriors
predicted, probs = predict_given_category_discount('Electronics', 'High')
print(f"Given Category='Electronics' and Discount='High':")
print(f"Predicted Purchased: {predicted}")
print(f"Posterior probabilities: {probs}")


import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import CategoricalNB
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

df = pd.DataFrame(data)

print("First 10 rows of dataset:")
print(df.head(10))

print("\nDataset Summary:")
print(df.describe(include='all'))

le = LabelEncoder()
df_encoded = df.apply(le.fit_transform)

X = df_encoded.drop("Purchased", axis=1)
y = df_encoded["Purchased"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

nb_model = CategoricalNB()
nb_model.fit(X_train, y_train)

y_pred = nb_model.predict(X_test)

print("\nAccuracy of Naive Bayes Model: {:.2f}%".format(accuracy_score(y_test, y_pred) * 100))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))
