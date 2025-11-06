"""
DMV Practical 7 - Data Loading and Analysis
"""

def print_code():
    """Prints the entire code of this practical."""
    code = '''"""
DMV Practical 7 - Data Loading and Analysis
"""

import pandas as pd
import matplotlib.pyplot as plt

# --- CSV to JSON Conversion Code (Reference) ---
# import pandas as pd
# df = pd.read_csv('sales_data.csv')
# df.to_json('sales_data.json')

# 1. Load data from different file formats
csv_data = pd.read_csv('sales_data.csv')
excel_data = pd.read_excel('sales_data.xlsx')
json_data = pd.read_json('sales_data.json')

# 2. Combine all into one DataFrame
data = pd.concat([csv_data, excel_data, json_data], ignore_index=True)

# 3. Explore structure and content
print("\\n--- Dataset Info ---")
print(data.info())
print("\\n--- First 5 Rows ---")
print(data.head())

# 4. Data cleaning
data.drop_duplicates(inplace=True)
data.fillna(method='ffill', inplace=True)  # forward-fill missing values

# 5. Data transformation
# Derive a new variable — Total Sale = Quantity_Sold * Unit_Price
data['Total_Sale'] = data['Quantity_Sold'] * data['Unit_Price']

# 6. Data analysis
print("\\n--- Descriptive Statistics ---")
print(data.describe())

# Aggregations (example by Product_Category)
category_sales = data.groupby('Product_Category')['Total_Sale'].sum().sort_values(ascending=False)
print("\\n--- Total Sales by Product Category ---")
print(category_sales)

# Calculate average order value
avg_order_value = data['Total_Sale'].mean()
print(f"\\nAverage Order Value: {avg_order_value:.2f}")

plt.figure(figsize=(8,5))
plt.bar(category_sales.index, category_sales.values, color='skyblue')  # <-- plt.bar()

plt.title('Total Sales by Product Category')
plt.xlabel('Product Category')
plt.ylabel('Total Sales')
plt.tight_layout()
plt.show()

plt.figure(figsize=(6,4))
plt.boxplot(data['Total_Sale'])  # <-- use plt.boxplot()
plt.title('Box Plot of Total Sales')
plt.ylabel('Total Sales')
plt.tight_layout()
plt.show()'''
    print(code)

