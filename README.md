# Shipment Cost Normalization — Parcel Invoice Analysis

A normalized shipping cost model built for a shoe company shipping 4 lb parcels across India via 9 carriers. The goal is to enable fair, apples-to-apples cost comparison across carriers by separating base shipping costs from surcharges, taxes, and penalties.

---

## Dataset Overview

| Metric | Value |
|--------|-------|
| Total charge rows | 214 |
| Unique shipments | 106 |
| Carriers | 9 (Delhivery, DTDC, Blue Dart, FedEx, DHL, Gati, Ecom Express, Ekart Logistics, Safe Express) |
| Zones | 1–5 |
| Unique charge type labels | 196 |

**Structure:** The dataset is in long format — one row per charge line, not per shipment. Shipments have 1 to 5 charge rows each.

---

## Data Quality Issues Found

- **196 unique charge labels for 214 rows** — many are duplicates with numeric suffixes (e.g., `Future Day Pickup - Additional Handling - Weekend Pickup - Special Handling 1` through `43`). These are the same charge type and were consolidated.
- **Zone inconsistency** — values appear as both `1, 2, 3...` and `Zone 1, Zone 2, Zone 3...`. Standardized to numeric.
- **Weight inconsistency** — assignment states all parcels are 4 lbs, but dataset contains 5–12 lb entries and mixed formats (`4 lbs` vs `4`). Flagged as a data quality issue; analysis proceeds with data as-is.
- **Same tracking number appears with different carriers/zones** — treated as a data anomaly; each unique tracking + carrier + zone combination treated as one shipment record.
- **Charges are highly uniform** — 75% of individual charge rows are exactly ₹25.00, suggesting synthetic/sample data.

---

## Charge Classification

All 196 charge type labels were mapped to 15 categories:

| Category | Examples | Include in Normalized Cost? | Reason |
|----------|----------|-----------------------------|--------|
| BASE | Base Rate, Freight | ✅ Yes | Core shipping cost |
| FUEL_SURCHARGE | Fuel Surcharge | ✅ Yes | Standard operational cost, applied universally |
| AREA_SURCHARGE | DAS Comm, Extended Area, Remote Area | ✅ Yes | Reflects delivery geography — operationally relevant |
| HANDLING_SURCHARGE | Additional Handling, Oversize, AHS Weight | ✅ Yes | Weight/dimension-based, part of shipment cost |
| SIGNATURE_FEE | Adult Signature Required, Direct Signature | ✅ Yes | Service-level cost, carrier-driven |
| RESIDENTIAL_FEE | Residential, Demand Surcharge-Resi | ✅ Yes | Delivery type surcharge |
| WEEKEND_FEE | Saturday Delivery, Sunday Pickup, Weekend | ✅ Yes | Timing-based service cost |
| FUTURE_DAY_PICKUP | Future Day Pickup variants | ✅ Yes | Operational scheduling cost |
| COD | COD Fee | ✅ Yes | Payment method surcharge, carrier-applied |
| DECLARED_VALUE | Declared Value Charge | ✅ Yes | Insurance/risk cost |
| OTHER_SURCHARGE | Admin Fees, Early Surcharge | ✅ Yes | Operational costs not elsewhere classified |
| TAX | GST, VAT, Customs Duty, HST | ❌ Excluded | Tax obligations, not carrier pricing decisions |
| ADJUSTMENT | Billing Adjustment for w/e ... | ❌ Excluded | Corrections to prior invoices — distort current cost |
| PENALTY | Address Correction, Zip Code Correction | ❌ Excluded | Avoidable, shipper-side errors — not carrier cost |
| BROKERAGE | Broker Fee, Customs Clearance, Entry Prep | ❌ Excluded | International/customs costs, not domestic shipping |

---

## Normalization Results

### Overall Impact

| Metric | Value |
|--------|-------|
| Total raw spend | ₹5,197.50 |
| Total normalized spend | ₹3,590.75 |
| Reduction | ₹1,606.75 (30.9%) |
| Avg raw cost per shipment | ₹28.88 |
| Avg normalized cost per shipment | ₹19.95 |

### Carrier Comparison: Before vs After Normalization

| Carrier | Avg Raw Cost (₹) | Rank (Raw) | Avg Normalized Cost (₹) | Rank (Normalized) | Rank Change |
|---------|-----------------|------------|--------------------------|-------------------|-------------|
| Blue Dart | 27.69 | 2 | 17.50 | 1 | +1 |
| Ekart Logistics | 27.77 | 3 | 18.45 | 2 | +1 |
| DHL | 29.29 | 6 | 18.50 | 3 | **+3** |
| Gati | 27.09 | 1 | 18.75 | 4 | **-3** |
| FedEx | 29.44 | 7 | 19.55 | 5 | +2 |
| DTDC | 28.37 | 4 | 20.10 | 6 | -2 |
| Ecom Express | 28.89 | 5 | 20.35 | 7 | -2 |
| Safe Express | 32.31 | 9 | 23.19 | 8 | +1 |
| Delhivery | 29.58 | 8 | 23.30 | 9 | -1 |

**Key insight:** Gati appeared cheapest on raw cost (rank 1) but drops to rank 4 after normalization — it carries a higher proportion of taxes and adjustments that inflate its raw cost. DHL shows the opposite: appears mid-tier raw but is 3rd cheapest normalized.

---

## Bonus: Worst 10% Shipments

**90th percentile threshold:** ₹50.00 normalized cost  
**Worst 10% shipments:** 25 out of 180 shipments (after deduplication)  
**Their total spend:** ₹1,290.00 — **35.9% of total normalized spend**

### Concentration by Carrier

| Carrier | Worst 10% Shipments |
|---------|-------------------|
| Ecom Express | 4 |
| Gati | 3 |
| FedEx | 3 |
| Delhivery | 3 |
| Safe Express | 3 |
| DTDC | 3 |
| Ekart Logistics | 3 |
| DHL | 2 |
| Blue Dart | 1 |

### Concentration by Zone

| Zone | Worst 10% Shipments |
|------|-------------------|
| Zone 2 | 7 |
| Zone 1 | 6 |
| Zone 3 | 5 |
| Zone 4 | 4 |
| Zone 5 | 3 |

**Key insights:**
- The worst shipments are **spread across all carriers** — no single carrier dominates, suggesting the driver is shipment characteristics (multiple surcharges stacking), not carrier pricing alone.
- **Zones 1 and 2 (closer zones) account for 13 of 25 worst shipments** — counterintuitive, likely because these shipments have more residential/weekend/signature surcharges stacked on top.
- The worst 10% punch well above their weight: **35.9% of total spend from ~14% of shipments** — a clear optimization target.

---

## Assumptions & Edge Cases

1. **No "Base Rate" for most shipments** — only 2 rows across 214 are classified as BASE. This means most shipments in the dataset represent individual surcharge lines, not full invoice breakdowns. The normalized cost reflects the sum of all included surcharges per shipment.
2. **Duplicate charge type labels** — `Weekend Pickup - Special Handling 1` through `43` treated as the same charge category (WEEKEND_FEE). If these are genuinely distinct charges, total WEEKEND_FEE spend would be materially higher.
3. **Multi-carrier tracking numbers** — some tracking numbers appear with different carriers across rows. Treated as separate shipment records per tracking + carrier + zone combination.
4. **Adjustments excluded entirely** — billing adjustments span specific week-ending dates (2023). Including them would require matching to original charges, which isn't possible without historical invoice data.
5. **₹ assumed as currency** — the dataset uses no currency symbol; INR assumed given India context.

---

## Repository Structure

```
shipment-cost-normalization/
│
├── README.md                  # This file — executive summary & findings
├── FJ_Assignment.xlsx         # Original dataset
├── analysis.ipynb             # Full analysis notebook with code + commentary
└── normalized_shipments.csv   # Output: one row per shipment with normalized cost
```

---

## How to Run

```bash
pip install pandas openpyxl numpy jupyter
jupyter notebook analysis.ipynb
```
