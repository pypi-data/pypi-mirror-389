# 🧠 smart-preprocess-asif  
> **A lightweight, one-line data preprocessing toolkit for machine learning workflows.**

[![PyPI version](https://img.shields.io/pypi/v/smart-preprocess-asif.svg)](https://pypi.org/project/smart-preprocess-asif/)
[![Python versions](https://img.shields.io/pypi/pyversions/smart-preprocess-asif.svg)](https://pypi.org/project/smart-preprocess-asif/)
[![License](https://img.shields.io/pypi/l/smart-preprocess-asif.svg)](https://github.com/asifpinjari/smart-preprocess-asif/blob/main/LICENSE)
[![Downloads](https://static.pepy.tech/badge/smart-preprocess-asif)](https://pepy.tech/project/smart-preprocess-asif)

---

### 🚀 Install

```bash
pip install smart-preprocess-asif

💡 Quick Start

import pandas as pd
from smart_preprocess import SmartCleaner

df = pd.DataFrame({
    "age": [20, None, 1000],
    "city": ["NY", "LA", None]
})

cleaner = SmartCleaner(outlier_clip=True)
X = cleaner.fit_transform(df)

print("✅ Cleaned DataFrame:")
print(X.head())
print("\nReport:")
print(cleaner.report_)

Output:

✅ Cleaned DataFrame:
   age__scaled  city_LA  city_NY  city_None
0    -1.224745      0.0      1.0        0.0
1     0.000000      1.0      0.0        0.0
2     1.224745      0.0      0.0        1.0

Report:
{'numeric_cols': ['age'], 'categorical_cols': ['city'], ...}

🔍 Features

✅ Automatic missing value imputation
✅ Outlier clipping (IQR method)
✅ Feature scaling using StandardScaler
✅ One-hot encoding for categorical variables
✅ Compact report dictionary summarizing transformations

🧩 Why use smart-preprocess-asif?

In ML projects, preprocessing pipelines often require 10–15 lines of repetitive boilerplate.
smart-preprocess-asif condenses those steps into one reusable, customizable class —
built with pandas + scikit-learn for performance and reliability.

🧪 Example Use Case

Integrate it into a scikit-learn pipeline:

from sklearn.pipeline import Pipeline
from smart_preprocess import SmartCleaner
from sklearn.linear_model import LogisticRegression

pipe = Pipeline([
    ("prep", SmartCleaner(outlier_clip=True)),
    ("model", LogisticRegression())
])

pipe.fit(X_train, y_train)

🛠 Requirements

Python ≥ 3.9

pandas ≥ 2.0

scikit-learn ≥ 1.3

numpy ≥ 1.24

1.24

🤝 Contributing

Pull requests are welcome!

Issues

📜 License

Licensed under the MIT License © 2025 Asif Pinjari

🌟 Support

If you find this project useful, please share it:

🔗 PyPI:
https://pypi.org/project/smart-preprocess-asif/

