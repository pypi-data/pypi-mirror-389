# Experiment 19: Time Series Plot
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
# Sample dates and values
dates = ['2025-10-01', '2025-10-02', '2025-10-03', '2025-10-04']
values = [100, 110, 105, 115]
# Convert string dates to datetime objects
dates = [datetime.strptime(date, "%Y-%m-%d") for date in dates]
plt.figure(figsize=(8,4))
plt.plot(dates, values, marker='o', color='purple')
plt.title('Time Series Plot Example')
plt.xlabel('Date')
plt.ylabel('Value')
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.gcf().autofmt_xdate() # Rotate date labels
plt.grid(True)
plt.show()
