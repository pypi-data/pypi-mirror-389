# Experiment 11: Word Count
from collections import defaultdict
# Sample text

lines = [
'data science python',
'python is powerful',
'data analysis'
]
# Map phase
mapped = [(word, 1) for line in lines for word in line.split()]
# Shuffle phase
shuffled = defaultdict(list)
for k, v in mapped:
  shuffled[k].append(v)
# Reduce phase
reduced = {k: sum(v) for k, v in shuffled.items()}
print("Word Count:", reduced)
