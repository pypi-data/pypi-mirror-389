# Tuple Operations
t = (1, 2, 3)
print("Tuple:", t)

print("Access index 1:", t[1])
print("Count of 2:", t.count(2))
print("Index of 3:", t.index(3))
# Set Operations
s = {1, 2, 3}
print("Original Set:", s)
s.add(4)
print("After adding 4:", s)
s.remove(2)
print("After removing 2:", s)
print("Set Union:", s.union({5,6}))
print("Set Intersection:", s.intersection({3,4,5}))
print("Set Difference:", s.difference({3,5}))
