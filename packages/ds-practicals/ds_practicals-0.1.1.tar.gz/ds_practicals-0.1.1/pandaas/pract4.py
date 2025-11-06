"""
ML Practical 4 - K-Means Clustering
"""

def print_code():
    """Prints the entire code of this practical."""
    code = '''"""
ML Practical 4 - K-Means Clustering
"""

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

# Load the dataset
df = pd.read_csv('Iris.csv')

# Prepare the data (drop ID and species columns)
X = df.drop(['Id', 'Species'], axis=1)

# Elbow method to find optimal number of clusters
wcss = []
for k in range(1, 11):
    kmeans = KMeans(n_clusters=k)
    kmeans.fit(X)
    wcss.append(kmeans.inertia_)

# Plot the Elbow curve
plt.plot(range(1, 11), wcss, marker='o')
plt.title('Elbow Method for Optimal k')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('WCSS')
plt.show()

# Apply K-Means with optimal k = 3
kmeans = KMeans(n_clusters=3)
y_kmeans = kmeans.fit_predict(X)

# Visualize the clusters
plt.scatter(X.iloc[y_kmeans == 0, 2], X.iloc[y_kmeans == 0, 3], s=100, c='red', label='Cluster 1')
plt.scatter(X.iloc[y_kmeans == 1, 2], X.iloc[y_kmeans == 1, 3], s=100, c='blue', label='Cluster 2')
plt.scatter(X.iloc[y_kmeans == 2, 2], X.iloc[y_kmeans == 2, 3], s=100, c='green', label='Cluster 3')

# Plot cluster centroids
plt.scatter(kmeans.cluster_centers_[:, 2], kmeans.cluster_centers_[:, 3], s=200, c='yellow', marker='*', label='Centroids')

plt.title('K-Means Clustering on Iris Dataset')
plt.xlabel('Petal Length (cm)')
plt.ylabel('Petal Width (cm)')
plt.legend()
plt.show()'''
    print(code)

