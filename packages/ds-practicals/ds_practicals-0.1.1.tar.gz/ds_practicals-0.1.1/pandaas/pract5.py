"""
ML Practical 5 - Random Forest Classifier
"""

def print_code():
    """Prints the entire code of this practical."""
    code = '''"""
ML Practical 5 - Random Forest Classifier
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

# Define proper column names as dataset has no header row
columns = ['buying', 'maint', 'doors', 'persons', 'lug_boot', 'safety', 'class']

# Load dataset with header=None
df = pd.read_csv('car_evaluation.csv', header=None, names=columns)

# Encode categorical values into numeric
le = LabelEncoder()
for col in df.columns:
    df[col] = le.fit_transform(df[col])

# Split features and target
X = df.drop('class', axis=1)
y = df['class']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Random Forest model
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# Predict
y_pred = model.predict(X_test)

# Evaluate
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\\nClassification Report:\\n", classification_report(y_test, y_pred))

# Confusion Matrix (graphical form)
cm = confusion_matrix(y_test, y_pred)
ConfusionMatrixDisplay(cm).plot(cmap='Blues')'''
    print(code)

