# Experiment 16: Line and Bar Charts
import matplotlib.pyplot as plt
# Sample data
x = [1, 2, 3, 4]
y = [10, 20, 15, 25]
# Line Chart
plt.figure(figsize=(8,4))
plt.plot(x, y, marker='o', color='b', label='Line Chart')
plt.title('Line Chart Example')
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.legend()
plt.grid(True)
plt.show()
# Bar Chart
plt.figure(figsize=(8,4))
plt.bar(x, y, color='g', label='Bar Chart')
plt.title('Bar Chart Example')
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.legend()
plt.show()
