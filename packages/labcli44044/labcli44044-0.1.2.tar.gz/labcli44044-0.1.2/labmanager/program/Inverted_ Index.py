# Experiment 13: Inverted Index
from collections import defaultdict
# Sample documents
docs = {
'doc1': 'data python',
'doc2': 'python machine',
'doc3': 'data analysis'
}
# Map & Shuffle
shuffled = defaultdict(list)
for doc_id, text in docs.items():
  for word in text.split():
    shuffled[word].append(doc_id)
# Reduce phase: unique document IDs per word
inverted_index = {word: list(set(doc_ids)) for word, doc_ids in
shuffled.items()}
print("Inverted Index:", inverted_index)
