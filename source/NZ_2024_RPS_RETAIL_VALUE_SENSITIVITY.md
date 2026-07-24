# New Zealand 2024 general-retailer value sensitivity

**Status:** supported model, not an observed national market value
**Evidence lane:** `public_reproducible`
**Donor decision:** not accepted
**Observation year:** 2024
**Reviewed:** 2026-07-24

## Result

The Ministry of Health's 2024 general-retailer files report product quantities
but not retail value. A reproducible hierarchical price crosswalk values those
quantities from recommended retail prices reported separately by specialist
vape retailers.

| Component | Low (NZD) | Base (NZD) | High (NZD) |
|---|---:|---:|---:|
| Specialist-retailer identified-vaping sales, reported rows | 274,180,410.21 | 274,180,410.21 | 274,180,410.21 |
| Specialist-retailer identified-vaping sales, exact-row-deduplicated sensitivity | 258,327,110.88 | 258,327,110.88 | 258,327,110.88 |
| Modelled RPS sales, all notifiable-product rows | 315,520,194.60 | 394,767,099.14 | 490,812,604.68 |
| Modelled RPS rows identified as vaping | 294,453,772.36 | 367,631,277.68 | 456,995,382.29 |
| Modelled RPS rows identified as vaping, exact-row-deduplicated sensitivity | 275,335,272.80 | 340,383,101.34 | 421,749,582.52 |
| Combined 2024 retail-vaping sensitivity | 533,662,383.68 | 641,811,687.89 | 731,175,792.50 |

The combined range is **not** a corrected official total. Its lower case combines
the exact-row-deduplicated specialist-vaping sensitivity with
exact-row-deduplicated general-retailer quantities at lower-quartile prices.
The base case combines reported specialist-vaping sales with all positive RPS
quantities at median prices. The high case uses upper-quartile prices.

The published component arithmetic is:

- Low: 258,327,110.88 + 275,335,272.80 = **533,662,383.68 NZD**
- Base: 274,180,410.21 + 367,631,277.68 = **641,811,687.89 NZD**
- High: 274,180,410.21 + 456,995,382.29 = **731,175,792.50 NZD**

Only the low case applies the exact-row-deduplicated sensitivity to both
components. The base and high cases retain reported specialist-retailer rows
and raw positive-quantity RPS rows.

## Reproducible calculation

1. The price reference reads 22 official AVP/AIS workbooks: 718,966 product
   rows, 646,617 rows with a positive RRP and 12,447 unique priced UPCs.
2. The quantity leg reads six official RPS workbooks: 145,046 product rows,
   141,028 rows with positive quantity and 20,765,394.76 reported units.
3. Each positive RPS quantity is priced first by exact UPC. If no exact price
   exists, the calculation uses a product-type distribution with at least five
   unique priced UPCs, then a product-scope distribution with at least twenty.
4. Low, base and high prices are the 25th, 50th and 75th percentiles. Product-
   type and scope distributions use unique-UPC median prices so repeated
   retailer lines do not directly determine the fallback distribution.
5. Manufacturer/importer notifier rows are excluded. AVP/AIS and RPS are
   distinct retail-return classes under the Ministry's filing instructions.
6. No licence, company, brand, flavour or UPC value is published.

All 141,028 positive-quantity RPS rows received a price through one of the
published fallback levels. This is model coverage, not proof that the selected
price represents the actual transaction price at a general retailer.

## Why the result is not a donor market

- RPS value is modelled from quantities and specialist-retailer RRP, not
  observed general-retailer revenue.
- Filing completeness, late returns, nil returns and unresolved data-quality
  issues prevent a complete national-coverage claim.
- The official page and reviewed user guide do not state the GST basis.
- No independent tax, customs or retail-scanner reconciliation is available in
  this release.
- Exact repeated rows are shown only as a sensitivity because their business
  meaning has not been established.

## Official sources

- [New Zealand Ministry of Health: 2024 annual returns](https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2024)
- [New Zealand Ministry of Health: annual-sales-return requirements](https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return)
- [New Zealand Ministry of Health: 2025 annual-sales-return user guide](https://www.health.govt.nz/system/files/2025-11/notifiable-products-annual-sales-return-2025-user-guide.pdf)

The current guide confirms that general retailers use RPS returns, specialist
premises and internet sites use AVP/AIS returns, and manufacturers/importers use
notifier returns. It also instructs specialist retailers to report RRP,
quantity sold and total sales revenue, while the reviewed RPS publication
contains quantity but no direct value.
