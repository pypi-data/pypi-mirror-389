"""
DMV Practical 10 - Data Filtering and Aggregation
"""

import pandas as pd

# 1. Import dataset and make column names simple
df = pd.read_csv("housing.csv")
print(df.head())
df.columns = ['Income', 'House_Age', 'Rooms', 'Bedrooms', 'Population', 'Price', 'Address']

# 2. Handle missing values (easy way)
df = df.dropna()   # just drop rows with any missing values

# 3. (No merging since only one dataset)

# 4. Filter df (example: only houses with population > 30000)
filtered_df = df[df['Population'] > 30000]

# 5. Handle categorical variable (Address)
# Easiest way: convert text column to category codes
filtered_df['Address_Code'] = filtered_df['Address'].astype('category').cat.codes

# 6. Round 'Bedrooms' to nearest whole number before grouping
filtered_df['Bedrooms_Rounded'] = filtered_df['Bedrooms'].round()

# Aggregate df — find average price by number of (rounded) bedrooms
avg_price = filtered_df.groupby('Bedrooms_Rounded')['Price'].mean().reset_index()

# Format output: show 4 decimal places and disable scientific notation
pd.set_option('display.float_format', '{:.4f}'.format)

print("\nAverage Price by Number of Bedrooms (rounded):")
print(avg_price)

# 3. Handle outliers in 'Price' using IQR method (do this before filtering)
Q1 = df['Price'].quantile(0.25)
Q3 = df['Price'].quantile(0.75)
IQR = Q3 - Q1
df = df[(df['Price'] >= (Q1 - 1.5 * IQR)) & (df['Price'] <= (Q3 + 1.5 * IQR))]

# Show final cleaned df
print("\nCleaned dfset shape:", filtered_df.shape)
print("\nSample cleaned df:")
print(filtered_df.head())


def print_code():
    """Prints the entire code of this practical."""
    code = '''"""
DMV Practical 10 - Data Filtering and Aggregation
"""

import pandas as pd

# 1. Import dataset and make column names simple
df = pd.read_csv("housing.csv")
print(df.head())
df.columns = ['Income', 'House_Age', 'Rooms', 'Bedrooms', 'Population', 'Price', 'Address']

# 2. Handle missing values (easy way)
df = df.dropna()   # just drop rows with any missing values

# 3. (No merging since only one dataset)

# 4. Filter df (example: only houses with population > 30000)
filtered_df = df[df['Population'] > 30000]

# 5. Handle categorical variable (Address)
# Easiest way: convert text column to category codes
filtered_df['Address_Code'] = filtered_df['Address'].astype('category').cat.codes

# 6. Round 'Bedrooms' to nearest whole number before grouping
filtered_df['Bedrooms_Rounded'] = filtered_df['Bedrooms'].round()

# Aggregate df — find average price by number of (rounded) bedrooms
avg_price = filtered_df.groupby('Bedrooms_Rounded')['Price'].mean().reset_index()

# Format output: show 4 decimal places and disable scientific notation
pd.set_option('display.float_format', '{:.4f}'.format)

print("\\nAverage Price by Number of Bedrooms (rounded):")
print(avg_price)

# 3. Handle outliers in 'Price' using IQR method (do this before filtering)
Q1 = df['Price'].quantile(0.25)
Q3 = df['Price'].quantile(0.75)
IQR = Q3 - Q1
df = df[(df['Price'] >= (Q1 - 1.5 * IQR)) & (df['Price'] <= (Q3 + 1.5 * IQR))]

# Show final cleaned df
print("\\nCleaned dfset shape:", filtered_df.shape)
print("\\nSample cleaned df:")
print(filtered_df.head())'''
    print(code)

