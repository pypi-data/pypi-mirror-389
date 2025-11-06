"""
ML Practical 2 - Linear Regression Models Comparison
"""


def print_code():
    """Prints the entire code of this practical."""
    code = '''"""
ML Practical 2 - Linear Regression Models Comparison
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.metrics import r2_score, mean_squared_error

# 1. Load dataset
df = pd.read_csv('uber.csv')
print(df.head())

# Data preprocessing
df = df.dropna()

# 2. Outlier detection and removal on fare_amount
upper_limit = df['fare_amount'].quantile(0.99)
df = df[df['fare_amount'] < upper_limit]

# 3. Select numeric columns only (to avoid string/datetime issues)
df = df.select_dtypes(include=['number'])

# 4. Correlation
sns.heatmap(df.corr(), cmap='coolwarm')
plt.show()

# 5. Split data
X = df.drop('fare_amount', axis=1)
y = df['fare_amount']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 6. Models
lr = LinearRegression()
ridge = Ridge(alpha=1.0)
lasso = Lasso(alpha=0.1)

lr.fit(X_train, y_train)
ridge.fit(X_train, y_train)
lasso.fit(X_train, y_train)

# 7. Evaluation
models = {'Linear Regression': lr, 'Ridge Regression': ridge, 'Lasso Regression': lasso}
for name, model in models.items():
    preds = model.predict(X_test)
    r2 = r2_score(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    print(f"{name}: R² = {r2:.4f}, RMSE = {rmse:.4f}")'''
    print(code)

