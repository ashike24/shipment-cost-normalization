# ─────────────────────────────────────────────
# Import all required libraries
# ─────────────────────────────────────────────
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings

warnings.filterwarnings('ignore')

# Display settings
pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', '{:.2f}'.format)

# ─────────────────────────────────────────────
# Load the dataset
# Note: Place FJ_Assignment.xlsx in the same folder as this notebook
# ─────────────────────────────────────────────
df = pd.read_excel('FJ_Assignment.xlsx', sheet_name='FJ Assignment - Sheet1')

print(f'Dataset loaded successfully.')
print(f'Shape: {df.shape[0]} rows x {df.shape[1]} columns')
print(f'Columns: {list(df.columns)}')
df.head(10)
