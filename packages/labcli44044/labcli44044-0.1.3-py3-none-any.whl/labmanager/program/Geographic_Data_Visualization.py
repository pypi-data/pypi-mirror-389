# Experiment 20: Geographic Data Visualization
import matplotlib.pyplot as plt
# Sample coordinates (Latitude, Longitude)
lat = [12.9716, 13.0827, 13.0674]
lon = [77.5946, 80.2707, 80.2376]
cities = ['Bangalore', 'Chennai', 'Vellore']
plt.figure(figsize=(8,5))
plt.scatter(lon, lat, color='blue', s=100)
# Annotate city names
for i, city in enumerate(cities):
  plt.text(lon[i]+0.1, lat[i]+0.05, city)

  plt.title('Geographic Data Visualization')
  plt.xlabel('Longitude')
  plt.ylabel('Latitude')
  plt.grid(True)
  plt.show()
