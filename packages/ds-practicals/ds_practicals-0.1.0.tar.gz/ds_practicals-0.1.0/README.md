# Pandaas

A comprehensive collection of practical examples for data mining, visualization, and machine learning. This package contains 13 practical examples covering various topics in data science and machine learning.

## Installation

```bash
pip install pandaas
```

## Features

- **13 Practical Examples**: Covering data analysis, visualization, and machine learning
- **Easy Access**: Each practical has a `print_code()` function to view the complete code
- **Educational**: Perfect for learning data science concepts

## Usage

```python
from pandaas import pract1, pract2, pract7

# Run a practical
pract1.print_code()  # Prints the entire code

# Or import and use directly
import pandaas.pract1 as p1
p1.print_code()
```

## Available Practicals

### Machine Learning (ML)
- `pract1`: Principal Component Analysis (PCA)
- `pract2`: Linear Regression Models Comparison
- `pract3`: Support Vector Machine (SVM) for Digit Classification
- `pract4`: K-Means Clustering
- `pract5`: Random Forest Classifier
- `pract6`: Q-Learning Reinforcement Learning

### Data Mining and Visualization (DMV)
- `pract7`: Data Loading and Analysis
- `pract8`: Weather Data API and Visualization
- `pract9`: Data Cleaning and Preprocessing
- `pract10`: Data Filtering and Aggregation
- `pract11`: Air Quality Data Visualization
- `pract12`: Retail Sales Analysis by Region
- `pract13`: Time Series Analysis and Forecasting

## Requirements

- Python >= 3.7
- pandas >= 1.3.0
- numpy >= 1.21.0
- matplotlib >= 3.4.0
- seaborn >= 0.11.0
- scikit-learn >= 1.0.0
- statsmodels >= 0.13.0
- requests >= 2.26.0

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

