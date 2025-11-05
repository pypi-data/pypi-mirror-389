# Experiment 15: Sorting by Key
from collections import defaultdict
# Sample data
data = [('b', 2), ('a', 5), ('b', 1), ('c', 3)]
# Shuffle phase
shuffled = defaultdict(list)
for k, v in data:
  shuffled[k].append(v)
# Sort keys and reduce
  sorted_keys = sorted(shuffled.keys())
  reduced = {k: sum(shuffled[k]) for k in sorted_keys}
print("Sorted and Aggregated by Key:", reduced)
