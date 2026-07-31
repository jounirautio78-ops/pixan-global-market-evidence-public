# New Zealand 2019 and 2023 HES e-cigarette expenditure control

Reviewed: 2026-07-31
Decision boundary: official household-expenditure estimates; not calendar-year
retail sales and not donor evidence on their own.

## Result

Stats NZ's detailed Household Economic Survey expenditure file publishes
e-cigarettes and refills as a distinct national household-expenditure class.
Measure `M001` is aggregate annual household expenditure in millions of New
Zealand dollars.

| HES year ended June | NZHEC code | Scope | Estimate NZD | RSE | Quality flag |
|---:|:---|:---|---:|---:|:---|
| 2019 | `02.2.00.4` | E-cigarettes and refills | 42,276,000 | 57.1% | L |
| 2019 | `02.2.00.4.0.01` | E-cigarette devices | 18,034,000 | 106.9% | P |
| 2019 | `02.2.00.4.0.02` | E-cigarette refills | 24,242,000 | 38.4% | M |
| 2023 | `02.2.00.4` | E-cigarettes and refills | 186,980,000 | 22.4% | M |
| 2023 | `02.2.00.4.0.01` | E-cigarette devices | 22,488,000 | 79.1% | L |
| 2023 | `02.2.00.4.0.02` | E-cigarette refills | 164,492,000 | 22.6% | M |

For both years, the two published component estimates add exactly to the
published total. Stats NZ defines the flags as: R, RSE under 21%; M, 21-49.9%;
L, 50-99.9%; and P, over 100%. The estimates are therefore useful national
consumer-expenditure controls, but the total and refill estimates have
moderate sampling error, the device estimates have high or very high sampling
error, and neither year should be presented without its RSE.

## Donor-gate treatment

This source materially improves the independent evidence map but does not
convert New Zealand into an accepted donor:

- the period is the **year ended June**, not a complete calendar year, so it
  fails the locked D1 requirement for the 2024 candidate;
- the 2022/23 HES collection period and recall periods do not match the 2024
  Ministry annual-return period;
- the HES is a household sample estimate rather than a census of retailer
  sell-through, and the published device estimate has a 79.1% RSE;
- Stats NZ states that HES respondents tend to under-report some categories,
  including alcohol and tobacco, and supplements HES with other sources for
  CPI weighting;
- the detailed CSV does not explicitly establish the GST treatment needed for
  the 2024 Ministry field; and
- the HES estimate cannot reconcile the 2024 specialist-retailer subtotal
  without a same-period bridge for channels, products, tax, timing and survey
  error.

The 2023 HES total of NZD 186.98 million must not be directly subtracted from,
added to or divided into the Ministry's at-least NZD 374 million 2023
mixed-supply-stage lower bound. The periods, transaction stages, coverage and
quality controls differ. It is an independent plausibility observation, not a
validation ratio.

## Reproduction

Official source page:

<https://www.stats.govt.nz/information-releases/household-expenditure-statistics-year-ended-june-2023/>

Official detailed-data ZIP:

<https://www.stats.govt.nz/assets/Uploads/Household-expenditure-statistics/Household-expenditure-statistics-Year-ended-June-2023/Download-data/detailed-household-expenditure-year-ended-June-2023-updated.zip>

Reviewed file controls:

- ZIP: 644,031 bytes; SHA-256
  `c1b31033f5abfe2596a45fed4b90417c941c2932dd7f5511221c4fe78d8af94e`;
- detailed CSV: 3,018,298 bytes; SHA-256
  `1989b63080cd97fefd5a98fd3a660415e971e5e1963ed3eeaec201fe2f1ef55e`;
- descriptions workbook: 352,169 bytes; SHA-256
  `bff27fa5a34e578c002468afdd8425f5b8e9faf04f1d1424f14020a2faf9e85b`.

After extracting the ZIP, the six admitted rows can be reproduced with:

```bash
rg '^2019|^2023' detailed-household-expenditure-up-to-2023-csv.csv \
  | rg '"M001","02\.2\.00\.4(\.0\.(01|02))?"'
```

The source values are primary. No EUR equivalent is computed because the
current FX layer admits only calendar-year records and does not substitute a
calendar-year annual average for this July-to-June period.

This control is independent public-source research. It is not Pixan Oy's
official position, an audit, a valuation, legal advice or investment advice.
