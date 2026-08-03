# New Zealand 2024 donor-gap research — 2026-08-02

Status: completed public-source review; donor decision unchanged at **7/10 —
NOT ACCEPTED**. This record documents a failed closure attempt rather than
silently upgrading the evidence.

## Decision

| Criterion | Result | Evidence boundary |
| --- | --- | --- |
| D5 national channel coverage | **FAILED** | The official return design requires general retailers to report product quantities but not retail prices or sales value. No observed nationwide general-retail value or compatible legal-entity denominator was found. |
| D8 currency and tax basis | **OPEN** | NZD is clear and GST is 15%, but the published specialist-retailer sales field does not state whether GST is included or how discounts, returns, credits, timing and corrections are treated. |
| D10 independent reconciliation | **OPEN** | Customs is a different transaction stage. HES covers a different period. The new CPI weight is based mainly on the same HES source and is therefore not independent calendar-2024 sales. |

The donor gate remains 0/3 and the global market value remains
`null/not_computed`.

## D5 — structural general-retail gap

The Ministry of Health's [2024 annual-return release](https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2024)
reports 3,125 returns: 1,970 general retailer / RPS, 1,009 specialist
retailer / AVP, 83 specialist internet seller / AIS and 63 notifier returns.
It describes specialist-retailer sales of at least NZD 280 million, warns that
the dataset is incomplete and does not recommend it for in-depth research.

The official [2024 policy brief](https://www.health.govt.nz/system/files/2024-08/h2024035267_briefing_-_smokefree_environments_and_regulated_products_amendment_bill_approval_for_introduction_black_box_1.pdf)
and [2024 return-form regulations](https://www.legislation.govt.nz/regulation/public/2021/0204/34.0/096be8ed81ef10f5.pdf)
show the decisive asymmetry:

- specialist Form 4 contains recommended retail price, quantity and total
  sales value;
- general-retailer Form 5 contains product and quantity fields but no retail
  price or sales-value field.

One RPS return may cover several outlets belonging to the same legal entity.
The 1,970 return count therefore cannot be divided by an outlet estimate to
create a coverage percentage. No public 2024 legal-entity denominator or
usable/nil/late/rejected-return distribution was located.

## D8 — GST scenarios are conditional, not a range

Inland Revenue confirms the [15% GST rate](https://www.ird.govt.nz/gst/what-gst-is)
and that the GST component of a GST-inclusive price is [3/23](https://www.ird.govt.nz/gst/charging-gst).
Applied mechanically to the NZD 274,180,410.21 specialist subtotal:

- **if GST-inclusive**, the net-of-GST amount would be NZD 238,417,748.01 and
  the GST component NZD 35,762,662.20;
- **if GST-exclusive**, the grossed-up amount would be NZD 315,307,471.74 and
  added GST NZD 41,127,061.53.

These are mutually exclusive conditional illustrations. They are not a market
range and neither can be selected until the Ministry confirms the reporting
basis. The public instructions do not define whether the field is realised
transaction revenue or RRP times quantity, nor the treatment of discounts,
returns, refunds, credits, bad debts or later corrections.

## D10 — new CPI structure check

Stats NZ published [CPI expenditure weights](https://www.stats.govt.nz/methods/consumers-price-index-expenditure-weights/)
on 3 July 2026. The official [2024 workbook](https://www.stats.govt.nz/assets/Methods/Consumers-price-index-expenditure-weights/consumers-price-index-expenditure-weights-2024.xlsx)
contains:

| NZHESCO code | Scope | Weight |
| --- | --- | ---: |
| `02.2.00.4` | E-cigarettes and refills | 0.11% |
| `02.2.00.4.0.01` | E-cigarette devices | 0.01% |
| `02.2.00.4.0.02` | E-cigarette refills | 0.10% |

Control: 0.01% + 0.10% = 0.11%. Workbook SHA-256:
`ffa7610732df74b89d5aaebecd16394ed392ecee911ae7f5bdf59fca98c2e655`.

The [2024 CPI review](https://www.stats.govt.nz/methods/consumers-price-index-review-2024/)
states that the weights mainly reflect the HES year ended June 2023 and are
price-updated to December 2024. The weights are rounded percentages, not an
absolute NZD value, do not represent observed calendar-2024 sales and share
the principal source with the existing HES route. They therefore improve
structure transparency but do not close D10.

The existing 2024 customs controls remain border-stage diagnostics only:
imports NZD 189,640,890 VFD and NZD 203,340,531 CIF, exports NZD 6,270,209 FOB,
and net proxies NZD 183,370,681 and NZD 197,070,322. They cannot establish
retail sales without production, inventory, re-export, margin, channel, timing
and GST bridges.

## Next evidence

The prepared 7 August Ministry follow-up remains the correct route. It should
seek, if held:

1. an observed 2024 general-retail sales value and a compatible legal-entity
   or outlet coverage denominator;
2. the exact GST and realised-revenue basis of specialist sales fields; and
3. direct official validation or another genuinely independent same-boundary
   reconciliation.

This is independent research. It is not Pixan Oy's official position, an
audit, valuation, legal opinion, investment recommendation or lending
recommendation.
