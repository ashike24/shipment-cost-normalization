# ─────────────────────────────────────────────
# Plot: Rank change after normalization
# Green = improved rank, Red = worsened rank
# ─────────────────────────────────────────────

comparison['Rank (Raw)']        = comparison['Avg Raw Cost (Rs)'].rank().astype(int)
comparison['Rank (Normalized)'] = comparison['Avg Normalized Cost (Rs)'].rank().astype(int)
comparison['Rank Change']       = comparison['Rank (Raw)'] - comparison['Rank (Normalized)']

comp_sorted = comparison.sort_values('Avg Normalized Cost (Rs)')
carriers    = comp_sorted.index

colors = ['#2ecc71' if v > 0 else '#e74c3c' if v < 0 else '#95a5a6'
          for v in comp_sorted['Rank Change']]

fig, ax = plt.subplots(figsize=(10, 5))

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

# Download to device
from google.colab import files
files.download('rank_change.png')
