# Experiment 17: Histograms and Boxplots
import matplotlib.pyplot as plt

# Sample data
data = [10, 20, 15, 25, 30, 35, 40, 45, 50]
# Histogram
plt.figure(figsize=(8,4))
plt.hist(data, bins=5, color='skyblue', edgecolor='black')
plt.title('Histogram Example')
plt.xlabel('Value')
plt.ylabel('Frequency')
plt.show()
# Boxplot
plt.figure(figsize=(8,4))
plt.boxplot(data, patch_artist=True)
plt.title('Boxplot Example')
plt.show()
