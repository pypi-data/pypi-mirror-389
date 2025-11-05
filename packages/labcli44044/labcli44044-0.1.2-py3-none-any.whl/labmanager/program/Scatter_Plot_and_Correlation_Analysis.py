# Experiment 18: Scatter Plot
import matplotlib.pyplot as plt
# Sample data
x = [1, 2, 3, 4, 5]
y = [2, 4, 1, 3, 5]
plt.figure(figsize=(8,4))
plt.scatter(x, y, color='red', marker='x')
plt.title('Scatter Plot Example')
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.grid(True)
plt.show()
