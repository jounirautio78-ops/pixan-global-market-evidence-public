# New Zealand 2024 donor-closure pack

Reviewed: 2026-07-26

## Executive conclusion

New Zealand's 29 official 2024 annual-return workbooks support a reproducible,
privacy-safe **specialist-retailer identified-vaping subtotal of
NZD 274,180,410.21**:

- vaping consumables: **NZD 189,402,451.96**;
- vaping devices or hardware: **NZD 84,709,409.85**;
- mixed vaping systems: **NZD 68,548.40**;
- other explicitly identified vaping rows: **NZD 0.00**.

The deterministic scope rules also identify and exclude
**NZD 2,137,085.24** of herbal-smoking and smokeless-tobacco rows and
**NZD 4,367,017.37** of unresolved product-type rows. The aggregate is formed
only from the `Total sales` fields in AIS and AVP specialist-retailer returns.
The Notifier and RPS files contain no `Total sales` field in the published
workbooks, so no manufacturer/importer value or modelled general-retailer value
is added to this observed subtotal.

This closes the product-scope evidence work for D3 and D4 and strengthens the
supply-stage control for D6. New Zealand now passes **7/10** criteria. It is
still `not_accepted`: D5 fails because national general-retail coverage is
absent, while D8 and D10 remain open because the GST basis is unstated and
there is no independent reconciliation. The global-estimate gate therefore
remains **0/3**.

The separate NZD 533,662,383.68 / 641,811,687.89 / 731,175,792.50 RPS retail
sensitivity remains a model. It is not an observed national market value and
does not replace the identified-vaping specialist-retail subtotal.

## D1-D10 decision

| Criterion | Status | Evidence and decision |
|:---|:---|:---|
| D1 Complete calendar year | Passed | The workbooks and official page cover sales from 1 January to 31 December 2024. |
| D2 Consumer retail transaction | Passed | The candidate uses only AIS and AVP specialist-retailer `Total sales` values. |
| D3 Devices and consumables | Passed | The public deterministic taxonomy separately quantifies consumables at NZD 189,402,451.96, devices/hardware at NZD 84,709,409.85 and mixed systems at NZD 68,548.40; all three are included in the NZD 274,180,410.21 vaping subtotal. |
| D4 Adjacent products controlled | Passed | Herbal-smoking and smokeless-tobacco rows are classified first and excluded at NZD 2,137,085.24. A further NZD 4,367,017.37 of unresolved product type is disclosed and excluded rather than guessed into vaping. |
| D5 National channel coverage | Failed | The Ministry says its at-least NZD 280 million estimate is based only on incomplete specialist-vape-retailer data. RPS general-retailer files publish quantity but no observed sales value. |
| D6 No supply-stage double counting | Passed | AIS and AVP contribute all NZD 280,684,512.81 of observed `Total sales`; the published Notifier and RPS workbooks contribute NZD 0.00 because no numeric `Total sales` cells are present. Notifier quantities and modelled RPS values are not added. |
| D7 Method and missingness documented | Passed | The public page's quality warning, file manifest and hashes, parser, row counts, unresolved scope, repeated-row sensitivity and return-class totals are all disclosed. |
| D8 Currency and tax basis | Open | Currency is NZD, but neither the official page nor the reviewed annual-return guide defines whether `total net sales revenue` includes or excludes GST. No 15% adjustment is made. |
| D9 Public reproducibility | Passed | The 29 source URLs and hashes, deterministic parser and privacy-safe aggregate output are public. A reviewer with the official downloads can reproduce the result without receiving a private or licensed dataset. |
| D10 Independent reconciliation | Open | The calculation matches the Ministry's at-least NZD 280 million mixed-product headline, but that is the same source chain. No independent tax, customs, POS or direct Ministry validation reconciles the vaping-only subtotal. |

## Reproduced product-scope calculation

| Scope bucket | Rows | Numeric `Total sales` cells | Reported sales NZD | Exact-row-deduplicated sensitivity NZD |
|:---|---:|---:|---:|---:|
| Vaping consumable | 570,514 | 396,041 | **189,402,451.96** | 178,468,519.31 |
| Vaping device or hardware | 284,841 | 204,370 | **84,709,409.85** | 79,804,162.88 |
| Vaping mixed system | 846 | 370 | **68,548.40** | 54,428.69 |
| Other explicit vaping | 2 | 0 | **0.00** | 0.00 |
| **Identified vaping** | **856,203** | **600,781** | **274,180,410.21** | **258,327,110.88** |
| Adjacent notifiable product | 5,964 | 2,384 | 2,137,085.24 | 2,135,965.24 |
| Unresolved product type | 20,255 | 9,600 | 4,367,017.37 | 4,097,978.93 |
| **All product rows** | **882,422** | **612,765** | **280,684,512.81** | **264,561,055.05** |

The independently summed scope buckets differ from the workbook total by one
cent after each bucket is rounded to two decimals. Currency values are summed
before half-up rounding; no row-level value is rounded before aggregation.

The exact-row-deduplicated figures are sensitivities, not corrected estimates.
The workbooks do not establish whether identical rows are duplicate errors or
legitimate repeated reporting.

## Deterministic taxonomy

Product-type text is case-folded, hyphens are converted to spaces and repeated
whitespace is collapsed. Rules are applied in this order:

1. `smokeless tobacco` and `herbal smoking` → adjacent, excluded;
2. `vaping substance`, `e liquid`, `freebase`, `nicotine salt` → consumable;
3. `disposable`, `prefilled`, `pod`, `cartridge` → mixed system;
4. `vaping device`, `vape device`, `vapin device`, `device`, `kit`, `tank`
   → device or hardware;
5. remaining explicit `vaping` or `vape` text → other explicit vaping;
6. every unmatched value → unresolved, excluded.

The adjacent rule runs first. Unresolved text is never forced into a vaping
class. The code is in `scripts/analyze_nz_2024_returns.py`, the exact source
inputs are in `source/NZ_2024_WORKBOOK_MANIFEST.json`, and the reviewed
aggregate output is in `source/NZ_2024_PRODUCT_SCOPE_AUDIT.json`.

## Return-class and supply-stage boundary

| Return class | Official role | Files | Product rows | Numeric `Total sales` cells | Reported sales NZD used |
|:---|:---|---:|---:|---:|---:|
| AIS | Specialist internet retailer | 1 | 29,689 | 29,086 | 20,959,634.48 |
| AVP | Specialist physical retailer | 21 | 689,277 | 583,679 | 259,724,878.33 |
| Notifier | Manufacturer or importer | 1 | 18,410 | 0 | 0.00 |
| RPS | General retailer | 6 | 145,046 | 0 | 0.00 |

The Ministry reports 3,125 received returns: 1,970 RPS, 1,009 AVP, 83 AIS and
63 Notifier. The published workbooks contain 2,987 distinct non-blank licence
codes in the prior aggregate check: 1,924 RPS, 919 AVP, 82 AIS and 62 Notifier.
The **138-return difference is unresolved**. It may not be interpreted as a
specific kind of nil or missing return without Ministry confirmation.

## Reproduction

Download the 29 official workbooks listed in the manifest into one local
directory, then run:

```bash
python scripts/analyze_nz_2024_returns.py --downloads /path/to/nz-2024-workbooks
```

The script fails closed if a file is missing, extra, has a different byte size
or does not match its SHA-256 hash. It emits only aggregates.

Reviewed integrity controls:

- input manifest SHA-256:
  `95b1c97e57b82b81b220ff3295b067c347474aacb1f8cb4d3d6244f454391343`;
- aggregate output SHA-256:
  `4f6bb08650eb03716b114536c9bc08bcb4a80deb87c326527c891ad05187bb9b`;
- 29 workbooks, 50,355,870 bytes;
- 882,422 product rows;
- 612,765 numeric `Total sales` cells.

## Permitted and prohibited claims

Supported wording:

> A deterministic reconstruction of New Zealand's 29 official 2024
> annual-return workbooks identifies NZD 274.18 million of vaping-product sales
> reported by specialist retailers. Consumables, devices/hardware, adjacent
> products and unresolved rows are separately quantified. The result remains
> an incomplete specialist-retail subtotal, not a complete national market
> value or accepted donor.

Do not claim:

- that NZD 274,180,410.21 is total New Zealand vaping consumer spending;
- that the Ministry itself published the vaping-only subtotal or taxonomy;
- that the RPS sensitivity is observed cash-register revenue;
- that exact repeated rows are proven duplicate errors;
- that GST is included or excluded;
- that the 138-return reconciliation difference has a known cause;
- that New Zealand supports a public global market total.

## Exact evidence needed to close the remaining gates

1. **D5 — national channel coverage:** an official national general-retail
   value or rights-cleared POS aggregate, plus expected-filer, received-return,
   nil-return, late-return and usable-return counts by class.
2. **D8 — tax basis:** Ministry confirmation whether AIS/AVP `total net sales
   revenue` is GST-inclusive or GST-exclusive and how discounts, refunds and
   returns are treated.
3. **D10 — independent reconciliation:** a non-duplicative tax, customs or POS
   bridge aligned to the same 2024 consumer-retail, product, channel and tax
   boundary, or direct Ministry validation of the reproduced subtotal.

## Canonical official sources

- 2024 annual-return publication and 29 downloads:
  https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2024
- Annual-return requirements and return-class definitions:
  https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return
- Annual-return user guide used for return-role definitions:
  https://www.health.govt.nz/system/files/2024-12/2024-annual-returns-user-guide.pdf
- Smokefree Environments and Regulated Products Regulations, version as at
  18 December 2024:
  https://legislation.govt.nz/secondary-legislation/pco-drafted/2021/204/en/2024-12-18.pdf

This pack is independent research. It is not Pixan Oy's official position, an
audit, valuation, legal opinion, investment recommendation or lending
recommendation.
