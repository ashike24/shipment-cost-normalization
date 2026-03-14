import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────
# Load and prepare data
# ─────────────────────────────────────────────
df = pd.read_excel('FJ_Assignment.xlsx', sheet_name='FJ Assignment - Sheet1')

# Clean zone column
df['Zone_clean'] = df['Zones'].astype(str).str.replace('Zone ', '', regex=False).str.strip()

# Classify charges
def classify_charge(ct):
    ct_lower = ct.lower()
    if any(x in ct_lower for x in ['base rate', 'freight', 'express rate']):
        return 'BASE'
    elif 'fuel' in ct_lower:
        return 'FUEL_SURCHARGE'
    elif any(x in ct_lower for x in ['tax', 'vat', 'gst', 'hst', 'pst', 'duty', 'customs']):
        return 'TAX'
    elif 'adjustment' in ct_lower:
        return 'ADJUSTMENT'
    elif any(x in ct_lower for x in ['address correction', 'zip code correction']):
        return 'PENALTY'
    elif any(x in ct_lower for x in ['delivery area surcharge', 'das', 'extended area',
                                      'remote area', 'rural area', 'out of area']):
        return 'AREA_SURCHARGE'
    elif any(x in ct_lower for x in ['signature', 'adult signature']):
        return 'SIGNATURE_FEE'
    elif any(x in ct_lower for x in ['residential', 'resi']):
        return 'RESIDENTIAL_FEE'
    elif any(x in ct_lower for x in ['saturday', 'sunday', 'weekend']):
        return 'WEEKEND_FEE'
    elif any(x in ct_lower for x in ['oversize', 'overweight', 'large package', 'ahs',
                                      'additional handling', 'addl. handling', 'additional weight']):
        return 'HANDLING_SURCHARGE'
    elif 'declared value' in ct_lower:
        return 'DECLARED_VALUE'
    elif any(x in ct_lower for x in ['brokerage', 'broker', 'entry', 'clearance', 'disbursement']):
        return 'BROKERAGE'
    elif 'cod' in ct_lower:
        return 'COD'
    elif 'future day pickup' in ct_lower:
        return 'FUTURE_DAY_PICKUP'
    else:
        return 'OTHER_SURCHARGE'

df['Charge_Category'] = df['Charge Type'].apply(classify_charge)

# ─────────────────────────────────────────────
# Build raw and normalized cost per shipment
# ─────────────────────────────────────────────
INCLUDED = [
    'BASE', 'FUEL_SURCHARGE', 'AREA_SURCHARGE', 'HANDLING_SURCHARGE',
    'SIGNATURE_FEE', 'RESIDENTIAL_FEE', 'WEEKEND_FEE', 'FUTURE_DAY_PICKUP',
    'COD', 'DECLARED_VALUE', 'OTHER_SURCHARGE'
]

df_incl = df[df['Charge_Category'].isin(INCLUDED)]

raw = df.groupby(['Tracking Number', 'Carrier Name', 'Zone_clean'])['Charge'].sum().reset_index()
raw.columns = ['Tracking Number', 'Carrier Name', 'Zone', 'Raw_Cost']

norm = df_incl.groupby(['Tracking Number', 'Carrier Name', 'Zone_clean'])['Charge'].sum().reset_index()
norm.columns = ['Tracking Number', 'Carrier Name', 'Zone', 'Normalized_Cost']

shipments = raw.merge(norm, on=['Tracking Number', 'Carrier Name', 'Zone'], how='left')
shipments['Normalized_Cost'] = shipments['Normalized_Cost'].fillna(0)

# ─────────────────────────────────────────────
# Build carrier comparison table
# ─────────────────────────────────────────────
carrier_raw  = shipments.groupby('Carrier Name')['Raw_Cost'].mean().round(2)
carrier_norm = shipments.groupby('Carrier Name')['Normalized_Cost'].mean().round(2)

comparison = pd.DataFrame({
    'Avg Raw Cost (Rs)':        carrier_raw,
    'Avg Normalized Cost (Rs)': carrier_norm
})

# Sort by normalized cost (cheapest to most expensive)
comp_sorted = comparison.sort_values('Avg Normalized Cost (Rs)')

# ─────────────────────────────────────────────
# Plot: Grouped bar chart — Raw vs Normalized
# ─────────────────────────────────────────────
carriers = comp_sorted.index
x        = np.arange(len(carriers))
width    = 0.35

fig, ax = plt.subplots(figsize=(13, 6))

bars1 = ax.bar(x - width/2, comp_sorted['Avg Raw Cost (Rs)'],
               width, label='Raw Cost', color='#4C72B0', alpha=0.85)
bars2 = ax.bar(x + width/2, comp_sorted['Avg Normalized Cost (Rs)'],
               width, label='Normalized Cost', color='#DD8452', alpha=0.85)

# Axis labels and title
ax.set_xlabel('Carrier', fontsize=12)
ax.set_ylabel('Avg Cost per Shipment (Rs)', fontsize=12)
ax.set_title('Carrier Cost Comparison: Raw vs Normalized', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(carriers, rotation=20, ha='right')
ax.legend(fontsize=11)
ax.grid(axis='y', alpha=0.3)

# Annotate bar values
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
