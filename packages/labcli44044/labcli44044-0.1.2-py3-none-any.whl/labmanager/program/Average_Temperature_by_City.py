# Experiment 12: Average Temperature by City
from collections import defaultdict
# Sample data
data = [
('Chennai', 35),
('Delhi', 40),
('Chennai', 34),
('Delhi', 38)
]
# Shuffle phase
shuffled = defaultdict(list)
for city, temp in data:
  shuffled[city].append(temp)
# Reduce phase: calculate average
averages = {city: sum(temps)/len(temps) for city, temps in
shuffled.items()}
print("Average Temperatures by City:", averages)
