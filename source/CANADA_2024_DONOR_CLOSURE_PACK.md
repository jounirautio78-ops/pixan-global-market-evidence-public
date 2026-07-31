# Canada 2024 donor-closure pack

Reviewed: 2026-07-31

## Executive conclusion

Canada provides a reproducible official 2024 consumer-retail point estimate for
NAPCS 5619122:

- quarterly RCS route: **CAD 1,219,160,000**;
- ECB 2024 annual-average equivalent: **EUR 822,583,715.21**;
- same-survey monthly RCS cross-check: **CAD 1,219,161,000**;
- monthly-versus-quarterly difference: **CAD 1,000**, or **0.000082%** of
  the quarterly annual sum.

The point estimate is useful as a national official retail anchor. It is not an
accepted donor market. A separate 2022 consumer survey shows an in-person vape
shop as a usual acquisition source for about 63% of device and liquid users
with valid answers. This supports treating the RCS-excluded specialist route as
potentially material but does not establish monetary materiality or quantify
the missing 2024 CAD value. D5 national channel coverage and D7 method and
missingness fail; D10 independent reconciliation remains open.
The public table identifies the values as current CAD. Statistics Canada
directly clarified on 2026-07-29 that table `20-10-0071-01` excludes
GST/HST/PST/QST, includes additional duties embedded in retail prices and is
intended to be annualised by summing its four quarters. This supersedes the
earlier inference that the current table excluded excise. A further written
clarification on 2026-07-30 confirms that the possible embedded components
include federal, additional and provincial vaping duties and that the same
basis applies to the reviewed monthly and archived vectors. D8 therefore
remains closed on an explicit multi-table basis. Canada remains `not_accepted` at
**7/10 passed**, and the public global-estimate gate remains **0/3**.

The Health Canada 2024 manufacturer/importer shipment value is a separate,
non-additive official route:

- shipments: **CAD 1,160,753,796.78**, or **EUR 783,176,261.20**;
- retail minus shipments: **CAD 58,406,203.22**, or
  **EUR 39,407,454.01**;
- retail / shipments: **1.0503174776**, or **+5.0317478%**;
- residual / retail: **4.7906922%**.

The residual is not labelled a retail margin. The RCS retail figure includes
additional duties embedded in retail prices, while the Health Canada shipment
measure excludes taxes and duties. The residual may also contain inventory,
timing, returns, product-scope, reporting-coverage and measurement differences.
These stage and tax-basis effects are not quantified. The two routes are not
summed and are not presented as a low-to-high market range.

## D1-D10 decision

| Criterion | Status | Evidence and decision |
|:---|:---|:---|
| D1 Complete calendar year | Passed | Four published 2024 quarters sum to CAD 1,219,160,000. |
| D2 Consumer retail transaction | Passed | RCS measures sales of commodities by retailers; the reporting period is when the commodities were sold in retail stores. |
| D3 Devices and consumables | Passed | NAPCS 5619122 includes electronic cigarettes, e-liquid refills, vaporizers and other e-liquid delivery systems. |
| D4 Adjacent products controlled | Passed | NAPCS 5619122 is separate from tobacco products and accessories other than e-cigarettes. No heated-tobacco or broad tobacco aggregate is added. |
| D5 National channel coverage | Failed | Statistics Canada confirmed that the RCS target population covers NAICS 441100–459993. Official NAICS examples place electronic-cigarette and vapour-liquid specialist retailing in 459999, outside the target range. CTNS 2022 separately reports an in-person vape shop as a usual source for about 63% of device and liquid users with valid answers, supporting potential channel materiality without quantifying the missing 2024 CAD value. |
| D6 No supply-stage double counting | Passed | The RCS retail observation stands alone. Health Canada shipments are retained only as a separate cross-check and are never added to retail. |
| D7 Method and missingness documented | Failed | Statistics Canada documents sampling, weighting, imputation, calibration, revisions and quality-indicator construction. All 12 months and all four quarters in 2024 carry `E`. The Retail Commodity Program confirmed that no exact product-class CV, imputation rate, standard error or annual covariance information exists beyond what is published, so the annual error boundary cannot be bounded. |
| D8 Currency and tax basis | Passed | Currency is CAD. Statistics Canada confirmed that the reviewed quarterly, monthly and archived vectors exclude GST, HST, PST and QST and include additional duties embedded in retail prices. Those duties can include the federal vaping duty, the additional vaping duty and provincial vaping duties. Four quarters form the intended annual value. |
| D9 Public reproducibility | Passed | The quarterly and monthly vectors, source ZIPs, formulas, status flags and file hashes are public and reproducible without licensed or company-identifiable records. |
| D10 Independent reconciliation | Open | Health Canada provides an independent supply-stage route, but the CAD 58,406,203.22 residual is not decomposed. Its published CAD 2.04 billion 2021 institutional benchmark confirms a materially different historical boundary but derives from a non-public custom study and cannot validate 2024. The monthly RCS route is a same-survey QA check, not independent evidence. |

## Reproduced 2024 retail calculation

All published RCS values are in thousands of current Canadian dollars. The
displayed values below multiply the source values by 1,000.

| Route | Q1 CAD | Q2 CAD | Q3 CAD | Q4 CAD | Annual CAD | Quality |
|:---|---:|---:|---:|---:|---:|:---|
| Quarterly vector `v1456717514` | 284,774,000 | 302,814,000 | 312,004,000 | 319,568,000 | **1,219,160,000** | E / E / E / E |
| Monthly vector `v1456717223`, summed into quarters | 284,775,000 | 302,814,000 | 312,004,000 | 319,568,000 | **1,219,161,000** | all 12 months E |
| Difference | 1,000 | 0 | 0 | 0 | **1,000** | same-survey QA only |

Formula:

`annual CAD = Q1 CAD + Q2 CAD + Q3 CAD + Q4 CAD`

The CAD 1,000 difference is compatible with source-level rounding or separate
aggregation, but its cause is not asserted without Statistics Canada
confirmation. The quarterly route remains the canonical published point
estimate because it is the route already used by the public donor candidate.

The 2023 monthly annual sum is CAD 2,000 above the quarterly annual sum. The
2025 monthly route is not used as a full-year cross-check because December 2025
is quality `F`, meaning too unreliable to publish. No missing month is treated
as zero.

## Health Canada shipment decomposition

Health Canada defines these sales as manufacturer/importer shipments to a
wholesaler or retailer, not individual consumer purchases. The reporting
regulation defines net sales as sales less returns and requires values in CAD
excluding taxes and duties.

| Official 2024 product category | Shipment value CAD | Share of shipment value |
|:---|---:|---:|
| Vaping part or device without a vaping substance | 30,207,822.87 | 2.602% |
| Vaping device containing a vaping substance | 558,947,200.26 | 48.154% |
| Vaping part containing a vaping substance | 316,329,158.83 | 27.252% |
| Vaping substance | 255,269,614.82 | 21.992% |
| **Total** | **1,160,753,796.78** | **100.000%** |

The same four national rows sum to **118,901,910 reported units** and
**1,251,843 litres**. Province/territory values and unit counts reproduce the
national aggregates. Two opposite one-litre category rounding differences
cancel in the total.

This decomposition cannot be converted into a retail device-versus-liquid
split. A device or part containing liquid combines hardware and liquid value,
and shipment-stage shares cannot be applied mechanically to the RCS retail
total.

## EUR equivalents

Reviewed ECB 2024 annual-average rate:

`1 EUR = 1.482110546875 CAD`

Formula:

`EUR equivalent = original CAD amount / 1.482110546875`

| Measure | Original CAD | EUR equivalent |
|:---|---:|---:|
| RCS quarterly annual sum | 1,219,160,000.00 | **822,583,715.21** |
| RCS monthly annual sum | 1,219,161,000.00 | **822,584,389.92** |
| Health Canada shipment value | 1,160,753,796.78 | **783,176,261.20** |
| Retail-minus-shipment residual | 58,406,203.22 | **39,407,454.01** |

CAD remains the primary observation currency. EUR is a secondary comparison
using the source-year annual-average reference rate.

## Why no low/base/high range is published

A defensible fail-closed representation is:

- `low: not_computed`;
- `base: CAD 1,219,160,000`;
- `high: not_computed`;
- `base_eur: EUR 822,583,715.21`;
- `range_reason: exact annual standard error and covariance unavailable`.

Quality `E` does not justify applying a mechanical plus/minus 25% range. The
exact CV, imputation rate and covariance of the component periods are not
published. Health Canada's shipment value is a different transaction stage and
cannot be relabelled as a retail lower bound.

## Consumer-side specialist-channel control

Statistics Canada's 2022 Canadian Tobacco and Nicotine Survey public-use
microdata gives a separate official consumer-side check on the channel excluded
from the RCS target population. Its population excludes territories, persons
living on reserves and other Indigenous settlements in the provinces, and
residents of collective dwellings. Among past-30-day vapers with a valid yes/no
answer, an in-person vape shop was reported as a usual acquisition source by:

| Item | Unweighted yes / valid | Weighted yes / valid | Survey-weighted point estimate |
|:---|---:|---:|---:|
| Devices (`VAP_40AR`) | 650 / 1,099 | 1,162,671.63 / 1,847,172.44 | **62.943%** |
| Liquids (`VAP_41AR`) | 644 / 1,095 | 1,156,389.89 / 1,835,669.58 | **62.996%** |

The point estimates use the survey weight `WTPP`. Precision is deliberately
withheld: `pumf.csv` contains 12,133 unique IDs while `pumf_bsw.csv` contains
11,526, and there is no reviewed basis for treating the 607 absent replicate-
weight rows as zero. The acquisition-source questions are multi-select, so
their channel shares must not be added to 100%.

This evidence supports treating the RCS-excluded specialist route as
potentially material. It does **not** establish monetary materiality, quantify
the missing 2024 CAD sales value, convert user incidence to expenditure,
measure channel coverage, repair RCS coverage or change the donor decision. It
is not a same-boundary independent reconciliation; D5 remains failed and D10
remains open. The point estimates and bootstrap mismatch are reproducible with
`scripts/reproduce_canada_ctns_channel_2022.py`; the full cross-country control
is documented in
[`DONOR_CLOSURE_SPRINT_CA_DE_NZ_PL_2026-07-31.md`](DONOR_CLOSURE_SPRINT_CA_DE_NZ_PL_2026-07-31.md).

## Permitted and prohibited claims

Supported wording:

> Statistics Canada's 2024 RCS quarterly observations imply a national
> consumer-retail point estimate of CAD 1.219160 billion for NAPCS 5619122,
> equivalent to EUR 822.58 million at the ECB 2024 annual-average rate. A
> same-survey monthly reconstruction differs by only CAD 1,000. The estimate
> remains quality E and is not an accepted donor market.

Do not claim:

- that CAD 1.219160 billion is an exact cash-register census total;
- that EUR 783.18-822.58 million is a market uncertainty range;
- that CAD 58.41 million is retailer margin;
- that the shipment mix is a retail device/liquid split;
- that CTNS user-source shares can be converted into sales value or channel
  coverage;
- that CTNS supplies a D10 same-boundary independent reconciliation;
- that D5 or D7 is merely unresolved, or that D10 has passed;
- that Canada supports a public global market total.

## Exact evidence needed to close the remaining gates

1. **D5/D7 — replacement independent route:** a rights-cleared national POS or
   retailer series with the specialist and general-retail channel denominator,
   method, missingness, revisions, precision and tax basis documented. This
   may validate a separate Canada candidate; it cannot create unavailable RCS
   product-class precision.
2. **D10 — independent bridge:** a source-linked reconciliation of retail and
   shipment stages covering inventory, timing, returns, product scope, the
   now-confirmed retail-versus-shipment tax-basis difference, reporting
   coverage and any retailer value added, or an independent rights-cleared POS
   route covering the same national product-year boundary.

## Canonical official sources and integrity controls

- Statistics Canada quarterly table 20-10-0071-01:
  https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010007101
- Quarterly bulk ZIP:
  https://www150.statcan.gc.ca/n1/en/tbl/csv/20100071-eng.zip
- Quarterly ZIP SHA-256:
  `283e8ec0159c048e4cfe5050f00232bff57aa6bd9add308d20492fd6af85e4b0`
- Statistics Canada monthly table 20-10-0080-01:
  https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010008001
- Monthly bulk ZIP:
  https://www150.statcan.gc.ca/n1/en/tbl/csv/20100080-eng.zip
- Monthly ZIP SHA-256:
  `7751fb46dc1bc77de6e5579f8f4e2456dbf1f8860dbf9275a089d5609fce6be3`
- RCS methodology:
  https://www23.statcan.gc.ca/imdb/p2SV.pl?Function=getSurvey&Id=1544050
- Privacy-safe record of the 2026-07-29 table-specific clarification:
  [`CANADA_RCS_TAX_BASIS_CLARIFICATION_2026-07-29.md`](CANADA_RCS_TAX_BASIS_CLARIFICATION_2026-07-29.md)
- Privacy-safe record of the 2026-07-30 scope and quality clarification:
  [`CANADA_RCS_SCOPE_QUALITY_CLARIFICATION_2026-07-30.md`](CANADA_RCS_SCOPE_QUALITY_CLARIFICATION_2026-07-30.md)
- NAICS 2022 retail definition and vaping-specialist classification:
  https://www23.statcan.gc.ca/imdb/p3VD.pl?CLV=4&CPV=45999&CST=27012022&CVD=1370274&D=1&Function=getVD&MLV=5&TVD=1369825&wbdisable=true
- Statistics Canada 2025 tax-treatment discussion:
  https://www150.statcan.gc.ca/n1/pub/36-28-0001/2025004/article/00001-eng.pdf
- Health Canada vaping sales:
  https://health-infobase.canada.ca/substance-use/vaping/sales/
- Statistics Canada 2022 Canadian Tobacco and Nicotine Survey public-use
  microdata landing page:
  https://www150.statcan.gc.ca/n1/pub/13-25-0001/132500012022001-eng.htm
- CTNS 2022 CSV package:
  https://www150.statcan.gc.ca/n1/pub/13-25-0001/2022001/2022/CSV.zip
- CTNS 2022 CSV ZIP SHA-256:
  `f2bbc5c0a0ea10fa15ef480972b828731a92a1376600e8e2039394ad2cd3320e`
- Vaping Products Reporting Regulations:
  https://laws-lois.justice.gc.ca/eng/regulations/SOR-2023-123/FullText.html
- ECB EXR annual-average CAD/EUR query:
  https://data-api.ecb.europa.eu/service/data/EXR/A.CAD.EUR.SP00.A?startPeriod=2024&endPeriod=2024&format=csvdata

This pack is independent research. It is not Pixan Oy's official position, an
audit, valuation, legal opinion, investment recommendation or lending
recommendation.
