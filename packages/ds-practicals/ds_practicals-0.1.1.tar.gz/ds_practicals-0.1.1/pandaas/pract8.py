"""
DMV Practical 8 - Weather Data API and Visualization
"""

def print_code():
    """Prints the entire code of this practical."""
    code = '''"""
DMV Practical 8 - Weather Data API and Visualization
"""

import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Setup
API_KEY = "8b67e60603e59584386aa559ec1d95b7"     
CITY = "Pune"
UNITS = "metric"              # 'metric' = Celsius
url = f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&units={UNITS}&appid={API_KEY}"

# 2. Retrieve data
response = requests.get(url).json()

# 3. Extract relevant weather attributes
weather_data = []
for item in response["list"]:
    weather_data.append({
        "datetime": datetime.fromisoformat(item["dt_txt"]),
        **item["main"],   # expands temp, pressure, humidity, etc.
        **item["wind"]    # expands speed, deg, gust (if present)
    })

# 4. Create DataFrame and basic cleaning
df = pd.DataFrame(weather_data)
print(df)

#Basic cleaning
df.fillna(method='ffill', inplace=True)

# 5. Basic stats (Data Modeling)
print("\\nAverage Temp:", df["temp"].mean(), "°C")
print("Max Temp:", df["temp"].max(), "°C")
print("Min Temp:", df["temp"].min(), "°C")
# Daily summary
daily_summary = df.groupby(df["datetime"].dt.date).agg({
    "temp": ["mean", "max", "min"],
    "humidity": "mean",
    "speed": "mean"
})
daily_summary

# 6. Visualization of temperature forecast
plt.figure(figsize=(8,4))
plt.plot(df["datetime"], df["temp"], color="coral")
plt.title("Temperature Forecast - Pune (Next 5 Days)")
plt.xlabel("Date-Time")
plt.ylabel("Temperature (°C)")
plt.show()

# Humidity and Wind Speed
plt.figure(figsize=(12,5))
plt.plot(df["datetime"], df["humidity"], color='teal')
plt.plot(df["datetime"], df["speed"], color='orange')
plt.title("Humidity and Wind Speed Trends")
plt.xlabel("Datetime")
plt.show()

# 6. Correlation Heatmap
plt.figure(figsize=(6, 4))
sns.heatmap(df.corr(), cmap="coolwarm")  # no need for annot or manually listed columns
plt.title("Correlation Heatmap of Weather Attributes")
plt.tight_layout()
plt.show()'''
    print(code)

