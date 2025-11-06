"""
DMV Practical 9 - Data Cleaning and Preprocessing
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# 1. Import the dataset
df = pd.read_csv("Telecom_Customer_Churn.csv")

# 2. Explore the dataset
print(df.info())
print(df.head())

# 3. Handle missing values
df.fillna(df.mean(numeric_only=True), inplace=True)
df.fillna("Unknown", inplace=True)

# 4. Remove duplicate records
df.drop_duplicates(inplace=True)

# 5. Standardize inconsistent data
df.columns = df.columns.str.strip()
df.replace({"yes": "Yes", "no": "No"}, inplace=True)

# 6. Convert data types
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
df["TotalCharges"].fillna(df["TotalCharges"].mean(), inplace=True)

# 7. Handle outliers in 'MonthlyCharges' using IQR method
Q1 = df['MonthlyCharges'].quantile(0.25)
Q3 = df['MonthlyCharges'].quantile(0.75)
IQR = Q3 - Q1

# Keep only data within 1.5 * IQR from Q1 and Q3
df = df[(df['MonthlyCharges'] >= (Q1 - 1.5 * IQR)) & (df['MonthlyCharges'] <= (Q3 + 1.5 * IQR))]

# 8. Feature engineering
df["TotalSpent"] = df["tenure"] * df["MonthlyCharges"]

# 9. Normalize or scale numerical columns
scaler = StandardScaler()
num_cols = ["MonthlyCharges", "TotalCharges", "tenure", "TotalSpent"]
df[num_cols] = scaler.fit_transform(df[num_cols])

# 10. Split dataset into training and testing sets
X = df.drop("Churn", axis=1)
y = df["Churn"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 11. Export cleaned dataset
df.to_csv("Cleaned_Telecom_Customer_Churn.csv", index=False)
print("✅ Cleaned dataset saved as Cleaned_Telecom_Customer_Churn.csv")


def print_code():
    """Prints the entire code of this practical."""
    code = '''"""
DMV Practical 9 - Data Cleaning and Preprocessing
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# 1. Import the dataset
df = pd.read_csv("Telecom_Customer_Churn.csv")

# 2. Explore the dataset
print(df.info())
print(df.head())

# 3. Handle missing values
df.fillna(df.mean(numeric_only=True), inplace=True)
df.fillna("Unknown", inplace=True)

# 4. Remove duplicate records
df.drop_duplicates(inplace=True)

# 5. Standardize inconsistent data
df.columns = df.columns.str.strip()
df.replace({"yes": "Yes", "no": "No"}, inplace=True)

# 6. Convert data types
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
df["TotalCharges"].fillna(df["TotalCharges"].mean(), inplace=True)

# 7. Handle outliers in 'MonthlyCharges' using IQR method
Q1 = df['MonthlyCharges'].quantile(0.25)
Q3 = df['MonthlyCharges'].quantile(0.75)
IQR = Q3 - Q1

# Keep only data within 1.5 * IQR from Q1 and Q3
df = df[(df['MonthlyCharges'] >= (Q1 - 1.5 * IQR)) & (df['MonthlyCharges'] <= (Q3 + 1.5 * IQR))]

# 8. Feature engineering
df["TotalSpent"] = df["tenure"] * df["MonthlyCharges"]

# 9. Normalize or scale numerical columns
scaler = StandardScaler()
num_cols = ["MonthlyCharges", "TotalCharges", "tenure", "TotalSpent"]
df[num_cols] = scaler.fit_transform(df[num_cols])

# 10. Split dataset into training and testing sets
X = df.drop("Churn", axis=1)
y = df["Churn"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 11. Export cleaned dataset
df.to_csv("Cleaned_Telecom_Customer_Churn.csv", index=False)
print("✅ Cleaned dataset saved as Cleaned_Telecom_Customer_Churn.csv")'''
    print(code)

