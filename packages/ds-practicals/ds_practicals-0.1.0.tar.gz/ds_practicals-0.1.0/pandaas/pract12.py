"""
DMV Practical 12 - Retail Sales Analysis by Region
"""

import pandas as pd
import matplotlib.pyplot as plt

# 1. Import dataset
data = pd.read_csv("retail_sales_dataset_with_region.csv")

# 2. Display first few rows
print("\nFirst few rows of the dataset:")
print(data.head())

# 3. Select relevant columns
cols = ['Region', 'Product Category', 'Total Amount']
data = data[cols]

# 4. Group by Region – Total Sales
region_sales = data.groupby('Region')['Total Amount'].sum().sort_values(ascending=False)
print("\nTotal Sales by Region:")
print(region_sales)

# 5. Bar Plot – Sales by Region
plt.figure(figsize=(8,5))
plt.bar(region_sales.index, region_sales.values, color='skyblue')
plt.title("Total Sales by Region")
plt.ylabel("Total Sales Amount")
plt.xlabel("Region")
plt.tight_layout()
plt.show()

# 6. Identify Top Performing Regions
top_regions = region_sales.head(3)
print("\nTop Performing Regions:")
print(top_regions)

# 7. Group by Region and Product Category – Total Sales
region_category_sales = data.groupby(['Region', 'Product Category'])['Total Amount'].sum().unstack()
print("\nTotal Sales by Region and Product Category:")
print(region_category_sales)

# 8. Stacked Bar Plot – Sales by Region and Product Category
region_category_sales.plot(kind='bar', stacked=True, figsize=(8,5))
plt.title("Sales by Region and Product Category")
plt.ylabel("Total Sales Amount")
plt.xlabel("Region")
plt.tight_layout()
plt.show()


def print_code():
    """Prints the entire code of this practical."""
    code = '''"""
DMV Practical 12 - Retail Sales Analysis by Region
"""

import pandas as pd
import matplotlib.pyplot as plt

# 1. Import dataset
data = pd.read_csv("retail_sales_dataset_with_region.csv")

# 2. Display first few rows
print("\\nFirst few rows of the dataset:")
print(data.head())

# 3. Select relevant columns
cols = ['Region', 'Product Category', 'Total Amount']
data = data[cols]

# 4. Group by Region – Total Sales
region_sales = data.groupby('Region')['Total Amount'].sum().sort_values(ascending=False)
print("\\nTotal Sales by Region:")
print(region_sales)

# 5. Bar Plot – Sales by Region
plt.figure(figsize=(8,5))
plt.bar(region_sales.index, region_sales.values, color='skyblue')
plt.title("Total Sales by Region")
plt.ylabel("Total Sales Amount")
plt.xlabel("Region")
plt.tight_layout()
plt.show()

# 6. Identify Top Performing Regions
top_regions = region_sales.head(3)
print("\\nTop Performing Regions:")
print(top_regions)

# 7. Group by Region and Product Category – Total Sales
region_category_sales = data.groupby(['Region', 'Product Category'])['Total Amount'].sum().unstack()
print("\\nTotal Sales by Region and Product Category:")
print(region_category_sales)

# 8. Stacked Bar Plot – Sales by Region and Product Category
region_category_sales.plot(kind='bar', stacked=True, figsize=(8,5))
plt.title("Sales by Region and Product Category")
plt.ylabel("Total Sales Amount")
plt.xlabel("Region")
plt.tight_layout()
plt.show()'''
    print(code)

