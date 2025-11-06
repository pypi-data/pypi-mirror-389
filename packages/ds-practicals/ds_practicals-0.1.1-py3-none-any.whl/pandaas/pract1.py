"""
ML Practical 1 - Principal Component Analysis (PCA)
"""

def print_code():
    """Prints the entire code of this practical."""
    code = '''"""
ML Practical 1 - Principal Component Analysis (PCA)
"""

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns

# Load dataset
df = pd.read_csv('Wine.csv')
print(df.head())

# Separate features and target
X = df.drop('Customer_Segment', axis=1)
y = df['Customer_Segment']

# Standardize features
X_scaled = StandardScaler().fit_transform(X)

# Apply PCA (2 components for visualization)
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

# Create DataFrame with PCA results
pca_df = pd.DataFrame(data=X_pca, columns=['PC1', 'PC2'])
pca_df['Customer_Segment'] = y

# Plot the PCA result
plt.figure(figsize=(8,6))
sns.scatterplot(data=pca_df, x='PC1', y='PC2', hue='Customer_Segment', palette='viridis', s=60)
plt.title('PCA on Wine Dataset')
plt.xlabel('Principal Component 1')
plt.ylabel('Principal Component 2')
plt.show()'''
    print(code)

