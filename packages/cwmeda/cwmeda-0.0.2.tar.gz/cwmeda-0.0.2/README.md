# EDAHelper

**EDAHelper** is a lightweight Python library that helps data scientists quickly visualize datasets with simple customizable plots.

## Installation
```bash
pip install cwmeda
```

## Usage
```python
from cwmeda import plot_columns
import pandas as pd

df = pd.DataFrame({'Gender':['M','F','M','F'], 'Age':[22,25,30,28]})
plot_columns(df, columns, plot_type='count', n_cols=3)
```
