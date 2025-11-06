"""
DMV Practical 13 - Time Series Analysis and Forecasting
"""

def print_code():
    """Prints the entire code of this practical."""
    code = '''"""
DMV Practical 13 - Time Series Analysis and Forecasting
"""

import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA

# 1. Import the dataset
data = pd.read_csv("ADANIPORTS.csv")

# 2. Explore the dataset
print("\\nFirst few rows of data:")
print(data.head())

# 3. Convert 'Date' column to datetime format and sort
data['Date'] = pd.to_datetime(data['Date'])
data = data.sort_values('Date')

# 4. Plot time series of Closing Price
plt.figure(figsize=(10,5))
plt.plot(data['Date'], data['Close'], color='blue')
plt.title("Stock Closing Price Over Time (ADANIPORTS)")
plt.xlabel("Date")
plt.ylabel("Closing Price")
plt.tight_layout()
plt.show()

# 5. Calculate and plot 7-day moving average
data['SMA_7'] = data['Close'].rolling(window=7).mean()
plt.figure(figsize=(10,5))
plt.plot(data['Date'], data['Close'], label='Closing Price', color='blue')
plt.plot(data['Date'], data['SMA_7'], label='7-Day Moving Average', color='red')
plt.title("Stock Price and 7-Day Moving Average (ADANIPORTS)")
plt.xlabel("Date")
plt.ylabel("Price")
plt.legend()
plt.tight_layout()
plt.show()

# 6. Perform seasonality analysis (monthly average)
# Since we have daily data, resample to monthly frequency
monthly = data.resample('M', on='Date').mean(numeric_only=True)
plt.figure(figsize=(10,5))
plt.plot(monthly.index, monthly['Close'], color='green')
plt.title("Monthly Average Closing Price (Seasonality) - ADANIPORTS")
plt.xlabel("Month")
plt.ylabel("Average Closing Price")
plt.tight_layout()
plt.show()

# 7. Analyze and plot correlation between Closing Price and Volume
corr = data['Close'].corr(data['Volume'])
print(f"\\nCorrelation between Closing Price and Volume: {corr:.2f}")

plt.figure(figsize=(6,5))
plt.scatter(data['Volume'], data['Close'], color='skyblue')
plt.title("Closing Price vs Volume (ADANIPORTS)")
plt.xlabel("Volume")
plt.ylabel("Closing Price")
plt.tight_layout()
plt.show()

# 8. Forecast future stock prices using ARIMA model
# Fill missing values if any
data['Close'].fillna(method='ffill', inplace=True)

# Build and fit ARIMA model
model = ARIMA(data['Close'], order=(1,1,1))
model = model.fit()

# Forecast next 10 days
forecast = model.forecast(steps=10)
print("\\nForecasted Stock Prices for Next 10 Days:")
print(forecast)'''
    print(code)

