# Experiment 14: Matrix-Vector Multiplication
from collections import defaultdict

# Matrix as dictionary {(row,col): value}
A = {(0,0): 1, (0,1): 2, (1,0): 3, (1,1): 4}
# Vector as dictionary {col: value}
B = {0: 5, 1: 6}
# Map phase
mapped = [(i, A[i,j]*B[j]) for (i,j) in A]
# Shuffle phase
shuffled = defaultdict(list)
for i, val in mapped:
  shuffled[i].append(val)
# Reduce phase
  result = {i: sum(vals) for i, vals in shuffled.items()}
print("Matrix-Vector Multiplication Result:", result)
