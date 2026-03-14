# ─────────────────────────────────────────────
# Plot: Distribution of normalized cost per shipment
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

# Download to device
from google.colab import files
files.download('cost_distribution.png')
