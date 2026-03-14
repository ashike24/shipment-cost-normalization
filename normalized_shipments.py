shipments['Is_Worst_10pct'] = shipments['Normalized_Cost'] >= threshold
shipments.to_csv('normalized_shipments.csv', index=False)
print('Saved: normalized_shipments.csv')
