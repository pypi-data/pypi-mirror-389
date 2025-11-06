"""
ML Practical 3 - Support Vector Machine (SVM) for Digit Classification
"""

import numpy as np
from sklearn import datasets
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt

# 1. Load data
digits = datasets.load_digits()
X, y = digits.data, digits.target

# 2. Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Train SVM (RBF kernel)
svm_model = SVC(kernel='rbf', gamma=0.001, C=10)
svm_model.fit(X_train, y_train)

# 4. Evaluate (single metric)
y_pred = svm_model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"Accuracy: {acc:.4f}")

# 5. Test and display one sample (change test_index as needed)
test_index = 10
test_image = X_test[test_index]
true_label = y_test[test_index]
predicted_label = svm_model.predict([test_image])[0]

# Reshape and show
image_to_show = test_image.reshape(8, 8)
plt.imshow(image_to_show, cmap=plt.cm.gray_r)
plt.title(f'Pred: {predicted_label} | True: {true_label}')
plt.axis('off')
plt.show()


def print_code():
    """Prints the entire code of this practical."""
    code = '''"""
ML Practical 3 - Support Vector Machine (SVM) for Digit Classification
"""

import numpy as np
from sklearn import datasets
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt

# 1. Load data
digits = datasets.load_digits()
X, y = digits.data, digits.target

# 2. Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Train SVM (RBF kernel)
svm_model = SVC(kernel='rbf', gamma=0.001, C=10)
svm_model.fit(X_train, y_train)

# 4. Evaluate (single metric)
y_pred = svm_model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"Accuracy: {acc:.4f}")

# 5. Test and display one sample (change test_index as needed)
test_index = 10
test_image = X_test[test_index]
true_label = y_test[test_index]
predicted_label = svm_model.predict([test_image])[0]

# Reshape and show
image_to_show = test_image.reshape(8, 8)
plt.imshow(image_to_show, cmap=plt.cm.gray_r)
plt.title(f'Pred: {predicted_label} | True: {true_label}')
plt.axis('off')
plt.show()'''
    print(code)

