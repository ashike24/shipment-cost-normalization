# ─────────────────────────────────────────────
# Plot: Worst 10% concentration by Carrier and Zone
# ─────────────────────────────────────────────

threshold = shipments['Normalized_Cost'].quantile(0.90)
worst     = shipments[shipments['Normalized_Cost'] >= threshold].copy()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# By carrier
carrier_worst = worst['Carrier Name'].value_counts()
axes[0].bar(carrier_worst.index, carrier_worst.values, color='#e74c3c', alpha=0.85)
axes[0].set_title('Worst 10% Shipments by Carrier', fontsize=13, fontweight='bold')
axes[0].set_xlabel('Carrier')
axes[0].set_ylabel('Number of Shipments')
axes[0].tick_params(axis='x', rotation=30)
axes[0].grid(axis='y', alpha=0.3)
for i, v in enumerate(carrier_worst.values):
    axes[0].text(i, v + 0.05, str(v), ha='center', fontweight='bold')

# By zone
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

# Download to device
from google.colab import files
files.download('worst_10pct.png')
