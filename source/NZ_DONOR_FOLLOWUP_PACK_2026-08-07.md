# New Zealand donor follow-up pack for 7 August 2026

Prepared: 2026-07-31
Dispatch status: **not sent**

## Decision summary

New Zealand remains `not_accepted` at **7/10**:

- D5 **Failed**;
- D8 **Open**;
- D10 **Open**.

The donor gate remains **0/3** and global retail value remains
`null/not_computed`. This pack prepares exact follow-up questions and a
reproducible customs-stage control; it adds no accepted market value.

## New official-source findings

### D5 — general-retail value is structurally absent

The Ministry of Health's 2024 policy brief and current 2025 annual-return guide
retain different reporting fields for specialist retailers and registered
general retailers. RPS general retailers report product types and quantities,
not observed retail sales value. The 2025 process adds nil-return and
validation states but does not add an RPS retail-value field.

The published statutory returns therefore cannot, by themselves, reconstruct
an observed nationwide general-retail value. The existing specialist-retailer
identified-vaping subtotal remains NZD 274,180,410.21 and D5 remains failed.

### D8 — GST and adjustment treatment remain undefined

Currency is NZD and the reviewed policy material states that vaping products
do not carry excise. The applicable AIS/AVP field definition still does not
state whether sales values include GST or how discounts, refunds, returns,
rebates, credits, cancellations, delivery, bad debt, timing and corrections
are treated. D8 remains open.

### D10 — final 2024 customs control

Stats NZ's final 2024 HS10 files provide an independent import/export-stage
control. They do not provide consumer-retail sell-through and are not a market
estimate.

| Scope | Import VFD NZD | Import CIF NZD | Domestic export FOB NZD | Re-export FOB NZD | Total export FOB NZD |
|:---|---:|---:|---:|---:|---:|
| Core operational codes | 190,066,068 | 203,770,974 | 4,986,477 | 1,501,732 | 6,488,209 |
| Expanded: core + `3824994930` | 227,280,194 | 242,974,278 | 12,232,454 | 1,968,020 | 14,200,474 |
| Maximum sensitivity: expanded + `8543903920` | 276,617,041 | 296,270,346 | 16,057,927 | 2,511,826 | 18,569,753 |

Core import quantities remain separated by source unit: KGM 633,045;
LTR 161,785; NMB 5,076,910. Core total-export quantities likewise remain
separate: KGM 9,877; LTR 19,672; NMB 40,190. KGM, LTR and NMB are never added
together. CIF minus FOB is not calculated or described as a net market because
the valuation stages and bases differ.

## Reproducibility record

Retrieved and reverified: 2026-07-31

| File | Bytes | SHA-256 |
|:---|---:|:---|
| [`2024_Imports_HS10.zip`](https://www3.stats.govt.nz/HS10_by_Country/2024_Imports_HS10.zip) | 3,169,436 | `9de45eca61ce2a48c26f3a9959d0d5e63a2640c681e11789a196f027db7b528f` |
| ZIP member `2024_Imports_HS10.csv` | 16,868,885 | `374be79b5718907e6758e17b4bfd117f358821ccc4b4a3279bb32b038ec6d21c` |
| [`2024_Exports_HS10.zip`](https://www3.stats.govt.nz/HS10_by_Country/2024_Exports_HS10.zip) | 2,365,449 | `3947a02e002bc02ca8238d27fab65a956b5577d0162d6270e00783320b6a6c82` |
| ZIP member `2024_Exports_HS10.csv` | 11,369,932 | `16fe3e0530ce306357ae5ee0b2486cfd3f40461e63456b30122af07a3d5f812a` |

The import CSV contains 100,312 data records and the export CSV 66,584 data
records.

Core filter:

```sql
status = 'Final'
AND month BETWEEN '202401' AND '202412'
AND (
  SUBSTR(hs, 1, 6) = '240412'
  OR SUBSTR(hs, 1, 8) IN ('24041901', '24041905')
  OR hs = '8543400000'
)
```

Expanded adds `3824994930`. Maximum sensitivity adds both `3824994930` and
`8543903920`.

Formulas:

```text
import_vfd = SUM(vfd)
import_cif = SUM(cif)
domestic_export_fob = SUM(Export_FOB)
re_export_fob = SUM(Re_export_FOB)
total_export_fob = SUM(total_export_FOB)
checksum: total_export_fob = domestic_export_fob + re_export_fob
```

`3824994930` is a generic chemical-products class. `8543903920` is a generic
parts class for heading 8543. Neither is vape-exclusive; both are sensitivity
limits only. Other blockers include low-value consignments, direct-to-consumer
imports, a July 2024 tariff split, classification error, domestic production,
inventory, margins, GST and missing device quantities.

## Ministry follow-up questions

Use the existing correspondence thread only after a fresh mailbox check. The
draft should ask for existing held information, not bespoke analysis:

1. Did 2024 RPS returns collect only product classes and quantities, with no
   actual retail sales value? Is any observed aggregated RPS value held
   separately?
2. For RPS, AVP, AIS and Notifier separately, what were the required or
   expected, received, nil or empty, late, validation-failed or rejected,
   usable and published return counts, with an as-of date?
3. How do the stated 3,125 received returns reconcile to 2,987 distinct
   nonblank licence identifiers in the published workbooks, including the
   differences RPS 46, AVP 90, AIS 1 and Notifier 1?
4. Does one RPS return represent one legal entity and potentially multiple
   physical or online outlets? If held, how many outlets are represented?
5. For 2024 AIS/AVP `Total sales` or `Total value of sales`, confirm NZD,
   GST-inclusive or GST-exclusive treatment, actual transaction revenue versus
   RRP multiplied by quantity, and the treatment of adjustments and timing.
6. Is it expected that 136,528 rows differ from RRP multiplied by quantity, and
   which field is authoritative?
7. Can the Ministry independently validate the reconstructed identified-vaping
   specialist value of NZD 274,180,410.21, adjacent excluded value of
   NZD 2,137,085.24 and unresolved excluded value of NZD 4,367,017.37 across
   the 29 published files?
8. Is an independent 2024 notifier, import, customs or other source-system
   cross-check held that avoids supply-stage double counting?
9. What is the publication timetable for 2025 returns, and will the publication
   expose nil or validation status and product-class quantities?

The request should state that an explicit `not held` answer is useful, no fee or
bespoke estimate is authorised without prior written approval, and attribution
and reuse permission are requested. It should not be labelled an Official
Information Act request unless applicant eligibility has first been confirmed.

## Parallel Stats NZ or Customs questions

- Confirm the complete 2024 vape HS10 mapping and code effective dates.
- Confirm whether `3824994930` or `8543903920` is vape-exclusive; if not, state
  whether a held vape-only split exists.
- Quantify or describe the treatment of consignments below NZD 1,000.
- Identify confidential or suppressed items, revisions and classification
  corrections or error estimates.
- State whether device quantities for `8543400000` or vape-only parts exist.
- Identify any held domestic-production, inventory or re-export controls.
- Confirm VFD, CIF and FOB bases and the recommended non-duplicative bridge.

## Acceptance tests

- D5 passes only with observed nationwide general-retail value plus specialist
  value, or quantitatively bounded material channel gaps, and a documented
  legal-entity or outlet denominator plus nil, late, missing and usable counts.
- D8 passes only with an official 2024 field definition covering NZD, GST,
  excise and material adjustments and timing.
- D10 passes only if the Ministry validates the exact subtotal from an
  independent internal aggregation or a genuinely independent POS, tax or
  customs bridge reconciles product, channel, timing, tax and supply-stage
  differences.
- Customs alone cannot pass D10 without vape-exclusive full-year scope,
  low-value and re-export coverage, domestic production and inventory, and a
  documented retail-stage, tax and margin bridge.

## Primary public sources

- Ministry of Health annual-return process:
  https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return
- Ministry of Health 2024 returns:
  https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2024
- Ministry of Health 2025 guide:
  https://www.health.govt.nz/system/files/2025-11/notifiable-products-annual-sales-return-2025-user-guide.pdf
- Ministry of Health 2024 policy brief:
  https://www.health.govt.nz/system/files/2024-08/h2024035267_briefing_-_smokefree_environments_and_regulated_products_amendment_bill_approval_for_introduction_black_box_1.pdf
- Stats NZ merchandise-trade downloads:
  https://www.stats.govt.nz/large-datasets/csv-files-for-download/overseas-merchandise-trade-datasets/
- Stats NZ methodology:
  https://datainfoplus.stats.govt.nz/Item/nz.govt.stats/6ed114da-3571-40d4-a89f-932068a4c753

This pack is independent research. It is not Pixan Oy's official position, an
audit, valuation, legal opinion, investment recommendation or lending
recommendation.
