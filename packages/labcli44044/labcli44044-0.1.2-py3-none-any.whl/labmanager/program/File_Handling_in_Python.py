# File Handling
filename = 'data.txt'
# Writing to file
with open(filename, 'w') as f:
  f.write("Hello Data Praveenkumar\n")
  f.write("Python File Handling Example\n")
# Reading file content
with open(filename, 'r') as f:
  content = f.read()
print("File Content:\n", content)
# Appending to file
with open(filename, 'a') as f:
  f.write("Appending new line\n")
# Reading updated file
with open(filename, 'r') as f:
  updated_content = f.read()
print("Updated File Content:\n", updated_content)
