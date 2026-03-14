# Shipment Cost Normalization — Full Analysis

> **Objective:** Build a normalized shipment cost model to enable fair comparison of shipping costs across 9 Indian logistics carriers.

**Dataset:** Parcel invoice data for a shoe company shipping 4 lb parcels across India  
**Carriers:** Delhivery, DTDC, Blue Dart, FedEx, DHL, Gati, Ecom Express, Ekart Logistics, Safe Express

---

## Section 1 — Setup & Data Loading

```python
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
# Note: Place FJ_Assignment.xlsx in the same folder as this file
# ─────────────────────────────────────────────
df = pd.read_excel('FJ_Assignment.xlsx', sheet_name='FJ Assignment - Sheet1')

print(f'Dataset loaded successfully.')
print(f'Shape: {df.shape[0]} rows x {df.shape[1]} columns')
print(f'Columns: {list(df.columns)}')
df.head(10)
```

---

## Section 2 — Data Profiling

Before any analysis, we need to understand the structure, completeness, and distributions of the dataset.

```python
# ─────────────────────────────────────────────
# Basic structure
# ─────────────────────────────────────────────
print('=== DATASET STRUCTURE ===')
print(f'Total rows         : {df.shape[0]}')
print(f'Total columns      : {df.shape[1]}')
print(f'Unique shipments   : {df["Tracking Number"].nunique()}')
print(f'Unique carriers    : {df["Carrier Name"].nunique()}')
print(f'Unique charge types: {df["Charge Type"].nunique()}')

print('\n=== MISSING VALUES ===')
print(df.isnull().sum())

print('\n=== DATA TYPES ===')
print(df.dtypes)
```

```python
# ─────────────────────────────────────────────
# Categorical column distributions
# ─────────────────────────────────────────────
print('=== CARRIERS ===')
print(df['Carrier Name'].value_counts())

print('\n=== ZONES ===')
print(df['Zones'].value_counts())

print('\n=== SERVICE LEVELS ===')
print(df['Service Level'].value_counts())

print('\n=== WEIGHT VALUES ===')
print(df['Weight (lbs)'].value_counts())
```

```python
# ─────────────────────────────────────────────
# Charge amount statistics
# Note: 75th percentile == median == 25.0
# Highly uniform distribution — consistent with synthetic/sample data
# ─────────────────────────────────────────────
print('=== CHARGE AMOUNT STATS ===')
print(df['Charge'].describe())

print(f'\n=== TOP 20 MOST COMMON CHARGE TYPES ===')
print(df['Charge Type'].value_counts().head(20))
```

```python
# ─────────────────────────────────────────────
# Rows per shipment
# Dataset is in LONG FORMAT — one row per charge line, not per shipment
# Multiple charge rows can exist for a single tracking number (1 to 5 rows)
# ─────────────────────────────────────────────
rows_per_shipment = df.groupby('Tracking Number').size()

print('=== ROWS PER SHIPMENT ===')
print(rows_per_shipment.describe())

print('\nDistribution (how many shipments have N charge rows):')
print(rows_per_shipment.value_counts().sort_index())
```

---

## Section 3 — Data Quality Issues & Cleaning

| Issue | Detail | Action |
|-------|--------|--------|
| 196 unique charge labels for 214 rows | Many duplicates with numeric suffixes (e.g. `Weekend Pickup - Special Handling 1-43`) | Consolidated via classification |
| Zone format inconsistency | Values appear as `1,2,3` AND `Zone 1, Zone 2` | Strip 'Zone ' prefix |
| Weight inconsistency | Assignment says 4 lbs; dataset has 5-12 lb entries | Clean format; flag anomaly |
| Multi-carrier tracking numbers | Same tracking number with different carriers | Treat as separate records |
| Uniform charge amounts | 75% of rows = Rs 25.00 exactly | Noted as synthetic data characteristic |

```python
# ─────────────────────────────────────────────
# Fix 1: Zone format inconsistency
# Standardize 'Zone 1', 'Zone 2'... to '1', '2'...
# ─────────────────────────────────────────────
df['Zone_clean'] = df['Zones'].astype(str).str.replace('Zone ', '', regex=False).str.strip()

print('Zone values after cleaning:')
print(df['Zone_clean'].value_counts())

# ─────────────────────────────────────────────
# Fix 2: Weight format inconsistency
# Standardize '4 lbs', '5 lbs'... to '4', '5'...
# ─────────────────────────────────────────────
df['Weight_clean'] = df['Weight (lbs)'].astype(str).str.replace(' lbs', '', regex=False).str.strip()

print('\nWeight values after cleaning:')
print(df['Weight_clean'].value_counts())

# Flag weight anomaly
anomaly_count = df[df['Weight_clean'].astype(str) != '4'].shape[0]
print(f'\nWeight anomaly: {anomaly_count} rows have weight != 4 lbs (assignment states all are 4 lbs)')
```

---

## Section 4 — Charge Classification

All 196 charge type labels are mapped to 15 categories using keyword matching.

### Inclusion / Exclusion Logic

| Decision | Categories | Reason |
|----------|------------|--------|
| ✅ Included | BASE, FUEL_SURCHARGE, AREA_SURCHARGE, HANDLING_SURCHARGE, SIGNATURE_FEE, RESIDENTIAL_FEE, WEEKEND_FEE, FUTURE_DAY_PICKUP, COD, DECLARED_VALUE, OTHER_SURCHARGE | Operational shipping costs — carrier pricing decisions |
| ❌ Excluded | TAX | Statutory obligation, not carrier pricing — distorts comparison |
| ❌ Excluded | ADJUSTMENT | References prior billing periods — cannot match to originals |
| ❌ Excluded | PENALTY | Shipper-side errors (wrong address) — avoidable, not carrier cost |
| ❌ Excluded | BROKERAGE | International/customs charges — irrelevant for domestic comparison |

```python
# ─────────────────────────────────────────────
# Charge classification function
# Uses keyword matching on lowercase charge type strings
# Order of conditions matters: specific checks come before general ones
# ─────────────────────────────────────────────
def classify_charge(ct):
    ct_lower = ct.lower()

    # Base shipping rate — core transport cost
    if any(x in ct_lower for x in ['base rate', 'freight', 'express rate']):
        return 'BASE'

    # Fuel surcharge — standard cost applied universally by all carriers
    elif 'fuel' in ct_lower:
        return 'FUEL_SURCHARGE'

    # Taxes — EXCLUDED (statutory, not carrier-driven)
    elif any(x in ct_lower for x in ['tax', 'vat', 'gst', 'hst', 'pst', 'duty', 'customs']):
        return 'TAX'

    # Billing adjustments — EXCLUDED (refer to prior invoice periods)
    elif 'adjustment' in ct_lower:
        return 'ADJUSTMENT'

    # Penalties — EXCLUDED (shipper errors, avoidable)
    elif any(x in ct_lower for x in ['address correction', 'zip code correction']):
        return 'PENALTY'

    # Delivery area surcharges — geography-based operational cost
    elif any(x in ct_lower for x in ['delivery area surcharge', 'das', 'extended area',
                                      'remote area', 'rural area', 'out of area']):
        return 'AREA_SURCHARGE'

    # Signature fees — service-level cost
    elif any(x in ct_lower for x in ['signature', 'adult signature']):
        return 'SIGNATURE_FEE'

    # Residential delivery fees — delivery type surcharge
    elif any(x in ct_lower for x in ['residential', 'resi']):
        return 'RESIDENTIAL_FEE'

    # Weekend/holiday fees — timing-based service cost
    elif any(x in ct_lower for x in ['saturday', 'sunday', 'weekend']):
        return 'WEEKEND_FEE'

    # Handling surcharges — weight/dimension-based
    elif any(x in ct_lower for x in ['oversize', 'overweight', 'large package', 'ahs',
                                      'additional handling', 'addl. handling', 'additional weight']):
        return 'HANDLING_SURCHARGE'

    # Declared value / insurance — risk-based cost
    elif 'declared value' in ct_lower:
        return 'DECLARED_VALUE'

    # Brokerage/customs clearance — EXCLUDED (international only)
    elif any(x in ct_lower for x in ['brokerage', 'broker', 'entry', 'clearance', 'disbursement']):
        return 'BROKERAGE'

    # COD fee — payment method surcharge
    elif 'cod' in ct_lower:
        return 'COD'

    # Future day pickup variants — scheduling cost
    elif 'future day pickup' in ct_lower:
        return 'FUTURE_DAY_PICKUP'

    # Everything else — included as generic operational surcharge
    else:
        return 'OTHER_SURCHARGE'


# Apply classification to all rows
df['Charge_Category'] = df['Charge Type'].apply(classify_charge)

# Build summary table
cat_summary = df.groupby('Charge_Category')['Charge'].agg(['count', 'sum', 'mean']).round(2)
cat_summary.columns = ['Count', 'Total (Rs)', 'Avg (Rs)']
cat_summary['Decision'] = cat_summary.index.map(
    lambda x: 'EXCLUDED' if x in ['TAX', 'ADJUSTMENT', 'PENALTY', 'BROKERAGE'] else 'INCLUDED'
)
print('=== CHARGE CATEGORY SUMMARY ===')
print(cat_summary.sort_values('Total (Rs)', ascending=False).to_string())
```

---

## Section 5 — Normalization Model

Aggregate all included charges per shipment into a single normalized cost.

```
Normalized Cost = SUM of all INCLUDED charge categories per Tracking Number
Raw Cost        = SUM of ALL charges per Tracking Number
Excluded Cost   = Raw Cost - Normalized Cost
```

```python
# ─────────────────────────────────────────────
# Define included and excluded categories
# ─────────────────────────────────────────────
INCLUDED = [
    'BASE', 'FUEL_SURCHARGE', 'AREA_SURCHARGE', 'HANDLING_SURCHARGE',
    'SIGNATURE_FEE', 'RESIDENTIAL_FEE', 'WEEKEND_FEE', 'FUTURE_DAY_PICKUP',
    'COD', 'DECLARED_VALUE', 'OTHER_SURCHARGE'
]
EXCLUDED = ['TAX', 'PENALTY', 'ADJUSTMENT', 'BROKERAGE']

# Filter dataset to included charges only
df_incl = df[df['Charge_Category'].isin(INCLUDED)]

# ─────────────────────────────────────────────
# Aggregate RAW cost per shipment (ALL charges)
# ─────────────────────────────────────────────
raw = df.groupby(
    ['Tracking Number', 'Carrier Name', 'Zone_clean']
)['Charge'].sum().reset_index()
raw.columns = ['Tracking Number', 'Carrier Name', 'Zone', 'Raw_Cost']

# ─────────────────────────────────────────────
# Aggregate NORMALIZED cost per shipment (INCLUDED only)
# ─────────────────────────────────────────────
norm = df_incl.groupby(
    ['Tracking Number', 'Carrier Name', 'Zone_clean']
)['Charge'].sum().reset_index()
norm.columns = ['Tracking Number', 'Carrier Name', 'Zone', 'Normalized_Cost']

# Merge into one shipment-level dataframe
shipments = raw.merge(norm, on=['Tracking Number', 'Carrier Name', 'Zone'], how='left')
shipments['Normalized_Cost'] = shipments['Normalized_Cost'].fillna(0)
shipments['Excluded_Cost']   = shipments['Raw_Cost'] - shipments['Normalized_Cost']

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print('=== NORMALIZATION SUMMARY ===')
print(f'Total shipments            : {len(shipments)}')
print(f'Total raw spend            : Rs {shipments["Raw_Cost"].sum():.2f}')
print(f'Total normalized spend     : Rs {shipments["Normalized_Cost"].sum():.2f}')
print(f'Total excluded             : Rs {shipments["Excluded_Cost"].sum():.2f} '
      f'({shipments["Excluded_Cost"].sum() / shipments["Raw_Cost"].sum() * 100:.1f}% of raw)')
print(f'\nAvg raw cost per shipment  : Rs {shipments["Raw_Cost"].mean():.2f}')
print(f'Avg normalized cost        : Rs {shipments["Normalized_Cost"].mean():.2f}')

print('\n=== SHIPMENT-LEVEL DATA (first 10) ===')
shipments.head(10)
```

---

## Section 6 — Carrier Comparison: Before vs After Normalization

```python
# ─────────────────────────────────────────────
# Build carrier-level comparison table
# Rank 1 = cheapest carrier
# ─────────────────────────────────────────────
carrier_raw  = shipments.groupby('Carrier Name')['Raw_Cost'].mean().round(2)
carrier_norm = shipments.groupby('Carrier Name')['Normalized_Cost'].mean().round(2)

comparison = pd.DataFrame({
    'Avg Raw Cost (Rs)':        carrier_raw,
    'Avg Normalized Cost (Rs)': carrier_norm
})

comparison['Rank (Raw)']        = comparison['Avg Raw Cost (Rs)'].rank().astype(int)
comparison['Rank (Normalized)'] = comparison['Avg Normalized Cost (Rs)'].rank().astype(int)

# Positive = improved rank (became cheaper) after normalization
comparison['Rank Change'] = comparison['Rank (Raw)'] - comparison['Rank (Normalized)']

print('=== CARRIER COMPARISON TABLE (sorted by normalized cost) ===')
print(comparison.sort_values('Avg Normalized Cost (Rs)').to_string())
```

```python
# ─────────────────────────────────────────────
# Chart 1: Grouped bar — Raw vs Normalized cost by carrier
# ─────────────────────────────────────────────
comp_sorted = comparison.sort_values('Avg Normalized Cost (Rs)')
carriers    = comp_sorted.index
x           = np.arange(len(carriers))
width       = 0.35

fig, ax = plt.subplots(figsize=(13, 6))

bars1 = ax.bar(x - width/2, comp_sorted['Avg Raw Cost (Rs)'],
               width, label='Raw Cost', color='#4C72B0', alpha=0.85)
bars2 = ax.bar(x + width/2, comp_sorted['Avg Normalized Cost (Rs)'],
               width, label='Normalized Cost', color='#DD8452', alpha=0.85)

ax.set_xlabel('Carrier', fontsize=12)
ax.set_ylabel('Avg Cost per Shipment (Rs)', fontsize=12)
ax.set_title('Carrier Cost Comparison: Raw vs Normalized', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(carriers, rotation=20, ha='right')
ax.legend(fontsize=11)
ax.grid(axis='y', alpha=0.3)

for bar in bars1:
    ax.annotate(f'Rs{bar.get_height():.0f}',
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 3), textcoords='offset points',
                ha='center', va='bottom', fontsize=8, color='#4C72B0')
for bar in bars2:
    ax.annotate(f'Rs{bar.get_height():.0f}',
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 3), textcoords='offset points',
                ha='center', va='bottom', fontsize=8, color='#DD8452')

plt.tight_layout()
plt.savefig('carrier_comparison.png', dpi=150, bbox_inches='tight')
plt.show()
print('Saved: carrier_comparison.png')
```

```python
# ─────────────────────────────────────────────
# Chart 2: Rank change after normalization
# Green = carrier improved (cheaper after normalization)
# Red   = carrier worsened (more expensive after normalization)
# ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))

colors = ['#2ecc71' if v > 0 else '#e74c3c' if v < 0 else '#95a5a6'
          for v in comp_sorted['Rank Change']]

bars = ax.bar(carriers, comp_sorted['Rank Change'], color=colors, alpha=0.85)
ax.axhline(0, color='black', linewidth=0.8)

ax.set_title('Rank Change After Normalization\n(positive = improved rank / became cheaper)',
             fontsize=13, fontweight='bold')
ax.set_ylabel('Rank Change')
ax.set_xlabel('Carrier')
plt.xticks(rotation=20, ha='right')
ax.grid(axis='y', alpha=0.3)

for bar, val in zip(bars, comp_sorted['Rank Change']):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + (0.05 if val >= 0 else -0.2),
            f'{val:+d}', ha='center', va='bottom', fontweight='bold', fontsize=11)

plt.tight_layout()
plt.savefig('rank_change.png', dpi=150, bbox_inches='tight')
plt.show()
print('Saved: rank_change.png')

print('\nKey Insights:')
print('- Gati: cheapest on raw (rank 1) but drops to rank 4 after normalization')
print('- DHL: improves from rank 6 to rank 3 — raw cost was inflated by taxes/adjustments')
print('- Delhivery & Safe Express remain expensive — their cost is genuinely high')
```

---

## Section 7 — Worst 10% Shipments Analysis

```python
# ─────────────────────────────────────────────
# Identify worst 10% threshold and filter shipments
# ─────────────────────────────────────────────
threshold        = shipments['Normalized_Cost'].quantile(0.90)
worst            = shipments[shipments['Normalized_Cost'] >= threshold].copy()
total_norm_spend = shipments['Normalized_Cost'].sum()
worst_spend      = worst['Normalized_Cost'].sum()

print('=== WORST 10% SUMMARY ===')
print(f'90th percentile threshold  : Rs {threshold:.2f}')
print(f'Worst 10% shipments        : {len(worst)} out of {len(shipments)}')
print(f'Their total spend          : Rs {worst_spend:.2f}')
print(f'% of total normalized spend: {worst_spend / total_norm_spend * 100:.1f}%')

print('\n--- By Carrier ---')
print(worst['Carrier Name'].value_counts())

print('\n--- By Zone ---')
print(worst['Zone'].value_counts().sort_index())
```

```python
# ─────────────────────────────────────────────
# Chart 3: Worst 10% concentration by Carrier and Zone
# ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

carrier_worst = worst['Carrier Name'].value_counts()
axes[0].bar(carrier_worst.index, carrier_worst.values, color='#e74c3c', alpha=0.85)
axes[0].set_title('Worst 10% Shipments by Carrier', fontsize=13, fontweight='bold')
axes[0].set_xlabel('Carrier')
axes[0].set_ylabel('Number of Shipments')
axes[0].tick_params(axis='x', rotation=30)
axes[0].grid(axis='y', alpha=0.3)
for i, v in enumerate(carrier_worst.values):
    axes[0].text(i, v + 0.05, str(v), ha='center', fontweight='bold')

zone_worst = worst['Zone'].value_counts().sort_index()
axes[1].bar(zone_worst.index.astype(str), zone_worst.values, color='#e67e22', alpha=0.85)
axes[1].set_title('Worst 10% Shipments by Zone', fontsize=13, fontweight='bold')
axes[1].set_xlabel('Zone')
axes[1].set_ylabel('Number of Shipments')
axes[1].grid(axis='y', alpha=0.3)
for i, v in enumerate(zone_worst.values):
    axes[1].text(i, v + 0.05, str(v), ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig('worst_10pct.png', dpi=150, bbox_inches='tight')
plt.show()
print('Saved: worst_10pct.png')
```

```python
# ─────────────────────────────────────────────
# Chart 4: Distribution of normalized cost per shipment
# Shows where mean and 90th percentile threshold fall
# ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))

ax.hist(shipments['Normalized_Cost'], bins=20,
        color='#4C72B0', alpha=0.8, edgecolor='white')

ax.axvline(threshold, color='red', linestyle='--', linewidth=2,
           label=f'90th percentile (Rs {threshold:.0f})')
ax.axvline(shipments['Normalized_Cost'].mean(), color='green', linestyle='--', linewidth=2,
           label=f'Mean (Rs {shipments["Normalized_Cost"].mean():.0f})')

ax.set_title('Distribution of Normalized Cost per Shipment', fontsize=13, fontweight='bold')
ax.set_xlabel('Normalized Cost (Rs)')
ax.set_ylabel('Number of Shipments')
ax.legend(fontsize=11)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('cost_distribution.png', dpi=150, bbox_inches='tight')
plt.show()
print('Saved: cost_distribution.png')
```

```python
# ─────────────────────────────────────────────
# Charge category breakdown: Worst 10% vs Rest
# Understand WHAT charge types are driving cost in worst shipments
# ─────────────────────────────────────────────
worst_ids = worst['Tracking Number'].tolist()

df['Shipment_Group'] = df['Tracking Number'].apply(
    lambda x: 'Worst 10%' if x in worst_ids else 'Rest'
)

category_split = (
    df.groupby(['Shipment_Group', 'Charge_Category'])['Charge']
    .sum()
    .unstack(fill_value=0)
)

print('=== CHARGE CATEGORY BREAKDOWN: Worst 10% vs Rest ===')
print(category_split.T.to_string())

print('\nKey Findings:')
print('- Worst 10% (25 shipments) contribute 35.9% of total normalized spend')
print('- No single carrier dominates — surcharge stacking is the primary driver')
print('- Zones 1 & 2 account for 13 of 25 worst shipments')
print('  Likely because urban deliveries attract more residential/signature/weekend surcharges')
```

---

## Section 8 — Export Output

```python
# ─────────────────────────────────────────────
# Add worst 10% flag and export final normalized dataset
# Output: normalized_shipments.csv — one row per shipment
# ─────────────────────────────────────────────
shipments['Is_Worst_10pct'] = shipments['Normalized_Cost'] >= threshold

shipments.to_csv('normalized_shipments.csv', index=False)
print('Exported: normalized_shipments.csv')
print(f'Shape: {shipments.shape}')

print('\n=== TOP 10 MOST EXPENSIVE SHIPMENTS (by normalized cost) ===')
shipments.sort_values('Normalized_Cost', ascending=False).head(10)
```

---

## Final Summary

| Metric | Finding |
|--------|---------|
| Charge types excluded | TAX, ADJUSTMENT, PENALTY, BROKERAGE |
| Normalization impact | Reduces spend basis by 30.9% (Rs 1,606.75) |
| Cheapest carrier (normalized) | Blue Dart — Rs 17.50 avg |
| Most expensive carrier (normalized) | Delhivery — Rs 23.30 avg |
| Biggest rank change | DHL improves +3 ranks after normalization |
| Worst 10% spend share | 35.9% of total normalized spend |
| Worst 10% driver | Surcharge stacking across all carriers, concentrated in Zones 1 and 2 |

---
*Analysis by: ASHIK E | Fischer Jordan Data Analytics Assignment 2026*
