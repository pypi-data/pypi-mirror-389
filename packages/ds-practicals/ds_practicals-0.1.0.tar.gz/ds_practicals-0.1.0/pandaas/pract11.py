"""
DMV Practical 11 - Air Quality Data Visualization
"""

import pandas as pd
import matplotlib.pyplot as plt

# 1. Import dataset
data = pd.read_csv("city_day.csv")
print(data.head())

# 2. Keep only useful columns
cols = ['Date', 'PM2.5', 'PM10', 'NO', 'NO2', 'NOx', 'CO', 'SO2', 'O3', 'AQI']
data = data[cols]

# 3. Handle missing data
data = data.dropna(subset=['Date', 'AQI'])

# 4. Convert data types
data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
num_cols = ['PM2.5', 'PM10', 'NO', 'NO2', 'NOx', 'CO', 'SO2', 'O3', 'AQI']
data[num_cols] = data[num_cols].apply(pd.to_numeric, errors='coerce')
data = data.sort_values('Date')

# 5. Line Plot – Overall AQI Trend Over Time
plt.figure(figsize=(10,5))
plt.plot(data['Date'], data['AQI'], color='red')
plt.title("Overall AQI Trend Over Time")
plt.xlabel("Date")
plt.ylabel("AQI")
plt.tight_layout()
plt.show()

# 6. Line Plots – Individual Pollutant Trends
plt.figure(figsize=(10,5))
plt.plot(data['Date'], data['PM2.5'], color='blue')
plt.title("PM2.5 Levels Over Time")
plt.xlabel("Date")
plt.ylabel("PM2.5 (µg/m³)")
plt.tight_layout()
plt.show()

plt.figure(figsize=(10,5))
plt.plot(data['Date'], data['PM10'], color='green')
plt.title("PM10 Levels Over Time")
plt.xlabel("Date")
plt.ylabel("PM10 (µg/m³)")
plt.tight_layout()
plt.show()

plt.figure(figsize=(10,5))
plt.plot(data['Date'], data['NO2'], color='orange')
plt.title("NO2 Levels Over Time")
plt.xlabel("Date")
plt.ylabel("NO2 (µg/m³)")
plt.tight_layout()
plt.show()

# 7. Bar Plot – Compare AQI Across Dates (without grouping)
plt.figure(figsize=(10,5))
plt.bar(data['Date'], data['AQI'])
plt.title("AQI Levels Across Dates")
plt.xlabel("Date")
plt.ylabel("AQI")
plt.tight_layout()
plt.show()

# 8. Box Plots – Distribution of AQI for Different Pollutant Categories
pollutant_cols = ['PM2.5', 'PM10', 'CO']
plt.figure(figsize=(8,5))
plt.boxplot([data['AQI'][data[p].notna()] for p in pollutant_cols], labels=pollutant_cols)
plt.title("Distribution of AQI for Different Pollutants")
plt.ylabel("AQI")
plt.tight_layout()
plt.show()

# 9. Scatter Plot – AQI vs PM2.5
plt.scatter(data['PM2.5'], data['AQI'], color='brown')
plt.title("AQI vs PM2.5 Levels")
plt.xlabel("PM2.5 (µg/m³)")
plt.ylabel("AQI")
plt.show()


def print_code():
    """Prints the entire code of this practical."""
    code = '''"""
DMV Practical 11 - Air Quality Data Visualization
"""

import pandas as pd
import matplotlib.pyplot as plt

# 1. Import dataset
data = pd.read_csv("city_day.csv")
print(data.head())

# 2. Keep only useful columns
cols = ['Date', 'PM2.5', 'PM10', 'NO', 'NO2', 'NOx', 'CO', 'SO2', 'O3', 'AQI']
data = data[cols]

# 3. Handle missing data
data = data.dropna(subset=['Date', 'AQI'])

# 4. Convert data types
data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
num_cols = ['PM2.5', 'PM10', 'NO', 'NO2', 'NOx', 'CO', 'SO2', 'O3', 'AQI']
data[num_cols] = data[num_cols].apply(pd.to_numeric, errors='coerce')
data = data.sort_values('Date')

# 5. Line Plot – Overall AQI Trend Over Time
plt.figure(figsize=(10,5))
plt.plot(data['Date'], data['AQI'], color='red')
plt.title("Overall AQI Trend Over Time")
plt.xlabel("Date")
plt.ylabel("AQI")
plt.tight_layout()
plt.show()

# 6. Line Plots – Individual Pollutant Trends
plt.figure(figsize=(10,5))
plt.plot(data['Date'], data['PM2.5'], color='blue')
plt.title("PM2.5 Levels Over Time")
plt.xlabel("Date")
plt.ylabel("PM2.5 (µg/m³)")
plt.tight_layout()
plt.show()

plt.figure(figsize=(10,5))
plt.plot(data['Date'], data['PM10'], color='green')
plt.title("PM10 Levels Over Time")
plt.xlabel("Date")
plt.ylabel("PM10 (µg/m³)")
plt.tight_layout()
plt.show()

plt.figure(figsize=(10,5))
plt.plot(data['Date'], data['NO2'], color='orange')
plt.title("NO2 Levels Over Time")
plt.xlabel("Date")
plt.ylabel("NO2 (µg/m³)")
plt.tight_layout()
plt.show()

# 7. Bar Plot – Compare AQI Across Dates (without grouping)
plt.figure(figsize=(10,5))
plt.bar(data['Date'], data['AQI'])
plt.title("AQI Levels Across Dates")
plt.xlabel("Date")
plt.ylabel("AQI")
plt.tight_layout()
plt.show()

# 8. Box Plots – Distribution of AQI for Different Pollutant Categories
pollutant_cols = ['PM2.5', 'PM10', 'CO']
plt.figure(figsize=(8,5))
plt.boxplot([data['AQI'][data[p].notna()] for p in pollutant_cols], labels=pollutant_cols)
plt.title("Distribution of AQI for Different Pollutants")
plt.ylabel("AQI")
plt.tight_layout()
plt.show()

# 9. Scatter Plot – AQI vs PM2.5
plt.scatter(data['PM2.5'], data['AQI'], color='brown')
plt.title("AQI vs PM2.5 Levels")
plt.xlabel("PM2.5 (µg/m³)")
plt.ylabel("AQI")
plt.show()'''
    print(code)

