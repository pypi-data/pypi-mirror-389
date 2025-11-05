# K-Means Clustering
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import numpy as np
# Sample dataset
X = np.array([[1,2], [1,4], [1,0], [4,2], [4,4], [4,0]])
# KMeans model
kmeans = KMeans(n_clusters=2, random_state=42)
kmeans.fit(X)
# Cluster centers
print("Cluster Centers:\n", kmeans.cluster_centers_)
# Labels
print("Cluster Labels:", kmeans.labels_)
# Plotting clusters
plt.scatter(X[:,0], X[:,1], c=kmeans.labels_, cmap='rainbow')
plt.scatter(kmeans.cluster_centers_[:,0], kmeans.cluster_centers_[:,1],
marker='x', s=200, color='black')
plt.title('K-Means Clustering')
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
