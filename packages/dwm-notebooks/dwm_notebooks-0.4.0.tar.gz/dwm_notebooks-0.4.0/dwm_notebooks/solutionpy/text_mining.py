#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Converted from Jupyter Notebook: notebook.ipynb
Conversion Date: 2025-11-05T14:30:34.778Z
"""

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
# from urllib.request import urlopen # Remove urllib.request
import requests # Import the requests library
from bs4 import BeautifulSoup
import re

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')

url = "https://en.wikipedia.org/wiki/Deep_learning"

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
response = requests.get(url, headers=headers)
response.raise_for_status()
html = response.text

soup = BeautifulSoup(html, 'html.parser')

# Extract paragraphs
paragraphs = soup.find_all('p')
text = ""
for p in paragraphs:
    text += p.text

print("Original Wikipedia Text (First 500 characters):\n")
print(text[:500])

# Step 3: Preprocessing the Text
text = re.sub(r'\[[0-9]*\]', ' ', text)  # Remove citations like [1], [2]
text = re.sub(r'\s+', ' ', text)         # Remove extra spaces
# Keep punctuation needed for sentence tokenization (. ! ?)
text = re.sub('[^a-zA-Z0-9.!?]', ' ', text)
text = text.lower()                      # Convert to lowercase

print("\nPreprocessed Text (First 500 characters):\n")
print(text[:500])

# Step 4: Convert Text to Sentences
sentences = sent_tokenize(text)
print("\nNumber of Sentences:", len(sentences))

# Step 5: Weighted Frequency of Occurrence
stop_words = set(stopwords.words("english"))
words = word_tokenize(text)

word_frequencies = {}
for word in words:
    if word not in stop_words:
        if word not in word_frequencies.keys():
            word_frequencies[word] = 1
        else:
            word_frequencies[word] += 1

maximum_frequncy = max(word_frequencies.values())

for word in word_frequencies.keys():
    word_frequencies[word] = (word_frequencies[word]/maximum_frequncy)

print("\nWeighted Word Frequencies (Top 10):")
for i, (word, freq) in enumerate(sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)[:10]):
    print(f"{i+1}. {word}: {freq:.3f}")

sentence_scores = {}
for sent in sentences:
    for word in word_tokenize(sent):
        if word in word_frequencies.keys():
            if len(sent.split(' ')) < 30:
                if sent not in sentence_scores.keys():
                    sentence_scores[sent] = word_frequencies[word]
                else:
                    sentence_scores[sent] += word_frequencies[word]

from wordcloud import WordCloud
import matplotlib.pyplot as plt

wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_frequencies)

plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.title("Word Cloud of Wikipedia Article", fontsize=15)
plt.show()

import heapq
summary_sentences = heapq.nlargest(5, sentence_scores, key=sentence_scores.get)
summary = ' '.join(summary_sentences)

print("\nSummary:\n")
print(summary)
