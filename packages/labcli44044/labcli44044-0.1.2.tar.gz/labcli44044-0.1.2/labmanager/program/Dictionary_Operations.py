# Dictionary Operations
d = {'a':1, 'b':2}
print("Original Dictionary:", d)
d['c'] = 3
print("After adding 'c':3:", d)
d['a'] = 5
print("After updating 'a':", d)
d.pop('b')
print("After removing 'b':", d)
print("Keys:", d.keys())
print("Values:", d.values())
print("Items:", d.items())
# Iterating through dictionary
for key, value in d.items():
  print(f"Key: {key}, Value: {value}")
