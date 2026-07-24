# Canada: Statistics Canada RCS retail-sales series, 2019–2025

Reviewed: 2026-07-24

## Result and use boundary

Statistics Canada's Retail Commodity Survey (RCS) publishes a national
quarterly retail-sales series for North American Product Classification System
(NAPCS) code 5619122:

> Electronic cigarettes, e-liquid refills, vaporizers and other e-liquid
> delivery systems, at retail.

The seven annual values below are deterministic sums of four published
quarters. They are official-table-derived consumer-retail estimates in current
Canadian dollars. They are not separately published annual totals and are not
accepted donor markets. The series retains material boundaries concerning
sampling error, imputation, revisions, the 2023 classification break, channel
coverage before 2023, and tax treatment.

## Canonical official sources

### 2019–2022

- Statistics Canada table 20-10-0016-01, *Retail commodity survey, retail
  sales, inactive*:
  https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010001601
- Bulk CSV and metadata:
  https://www150.statcan.gc.ca/n1/en/tbl/csv/20100016-eng.zip
- Extracted vector: `v1038567205`
- NAPCS: 5619122
- Industry aggregate: Retail trade `[44-453]`
- Unit in source: dollars, thousands
- Retrieval-date ZIP SHA-256:
  `21f2ab9d7e430acfcafcab3e87b7be67937667f04e683a2ac18635c3b1759486`

### 2023–2025

- Statistics Canada table 20-10-0071-01, *Quarterly retail commodity sales*:
  https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010007101
- Bulk CSV and metadata:
  https://www150.statcan.gc.ca/n1/en/tbl/csv/20100071-eng.zip
- Extracted vector: `v1456717514`
- NAPCS: 5619122
- Industry aggregate: Retail trade `[44-45]`
- Unit in source: dollars, thousands
- Retrieval-date ZIP SHA-256:
  `283e8ec0159c048e4cfe5050f00232bff57aa6bd9add308d20492fd6af85e4b0`

### Method, channels and questionnaire

- RCS survey record 2008, methodology and data accuracy:
  https://www23.statcan.gc.ca/imdb/p2SV.pl?Function=getSurvey&Id=1585585
- Monthly Retail Trade Survey questionnaire used by the RCS frame:
  https://www23.statcan.gc.ca/imdb/p3Instr.pl?Function=assembleInstr&Item_Id=1234971&lang=en
- Statistics Canada release explaining the pre-2023 e-commerce boundary:
  https://www150.statcan.gc.ca/n1/daily-quotidien/210708/dq210708b-eng.htm

## Reproduced quarterly values and annual sums

All source values are published in CAD thousands. Each displayed value below is
the source value multiplied by 1,000. The annual calculation is:

`annual CAD = Q1 CAD + Q2 CAD + Q3 CAD + Q4 CAD`

| Year | Q1 CAD | Q2 CAD | Q3 CAD | Q4 CAD | Annual CAD | Published quarter status |
|---:|---:|---:|---:|---:|---:|:---|
| 2019 | 107,664,000 | 137,742,000 | 131,046,000 | 100,625,000 | **477,077,000** | blank; blank; blank; blank |
| 2020 | 101,360,000 | 135,461,000 | 145,105,000 | 138,721,000 | **520,647,000** | blank; blank; blank; blank |
| 2021 | 193,631,000 | 222,318,000 | 289,054,000 | 287,729,000 | **992,732,000** | blank; blank; blank; blank |
| 2022 | 262,131,000 | 317,103,000 | 345,684,000 | 352,240,000 | **1,277,158,000** | E; D; D; D |
| 2023 | 401,909,000 | 408,484,000 | 415,294,000 | 305,071,000 | **1,530,758,000** | E; D; E; E |
| 2024 | 284,774,000 | 302,814,000 | 312,004,000 | 319,568,000 | **1,219,160,000** | E; E; E; E |
| 2025 | 314,192,000 | 306,082,000 | 323,578,000 | 322,715,000 | **1,266,567,000** | E; E; E; E |

The older vector begins with Q4 2018 at CAD 70,456,000. It is excluded because
the first three quarters are absent. The newer vector also contains Q1 2026,
which is excluded because 2026 is not a complete calendar year.

## Quality flags

The bulk metadata defines:

- `D`: acceptable in the symbol legend; the cube note describes code D as a
  coefficient of variation greater than 16.5% and at most 25%.
- `E`: use with caution; the cube note describes code E as a coefficient of
  variation greater than 25%.
- a blank status cell: no status symbol is attached to that published quarter.
  It is not re-labelled here as A, B or C.

The annual sums do not reduce the published quarterly uncertainty. In
particular, every quarter in 2024 and 2025 carries `E`.

RCS is a sample survey. Statistics Canada documents weighting, imputation,
calibration to the Monthly Retail Trade Survey, annual revisions, and
non-seasonally-adjusted estimates. The public annual sums should therefore be
treated as reproducible survey estimates, not exact cash-register census
totals.

## Product boundary

NAPCS 5619122 directly includes electronic cigarettes, e-liquid refills,
vaporizers and other e-liquid delivery systems. It is separate from NAPCS
5619121, tobacco products and accessories except e-cigarettes. This is a much
closer product match than a broad tobacco category, but the public table does
not publish a device-versus-liquid split.

## Channel boundary

The questionnaire instructs respondents to include brick-and-mortar sales,
Internet sales, and orders made by mail, telephone, catalogue and facsimile.
That supports inclusion of those methods within an in-scope sampled business.

For the 2019–2022 vector, the published industry aggregate is `[44-453]`.
Statistics Canada's contemporaneous release says that e-commerce sales of a
brick-and-mortar retailer are included with that retailer, while separately
managed online operations and pure-play Internet retailers were classified to
NAICS 45411. The release explicitly states that total retail sales did not
include retailers classified to 45411. The older annual values therefore
retain a potentially material pure-play Internet and mail-order channel gap.
The public data do not separately quantify vaping sales through that excluded
industry.

For the 2023–2025 vector, the aggregate is `[44-45]`. Statistics Canada states
that under NAICS 2022, Internet retail, direct selling and mail-order retail are
no longer classified separately from traditional in-store retail; businesses
are classified by the goods sold. This supports broader method-of-sale coverage
from 2023 onward. It does not provide a vaping-specific response-rate or
channel-completeness percentage, and telephone sales are not separately
quantified in the table.

## Tax boundary

The questionnaire explicitly instructs respondents to exclude GST, HST, PST
and QST from total and commodity retail sales. The questionnaire does not
explicitly state whether federal or provincial vaping excise duties embedded in
retail prices are included or excluded. The series is therefore tax-exclusive
for the named general sales taxes, but the vaping-excise basis remains
unresolved. No excise adjustment is made.

## Classification and comparability boundary

Table 20-10-0071-01 replaces table 20-10-0016-01. Starting in January 2023, RCS
figures use NAPCS 2022 and NAICS 2022 structures. Statistics Canada describes
new commodities, updated definitions and a broadened industry scope. Although
the same 5619122 label and a national retail aggregate exist on both sides, the
2019–2022 and 2023–2025 levels should not be interpreted as a perfectly
unchanged longitudinal series without a published bridge.

## Donor decision

These records remain `comparableMarketValue: false` and
`atlasEstimate: false`. They materially improve Canada's consumer-retail
evidence, but donor acceptance remains blocked at least by:

1. unresolved vaping-excise treatment;
2. the pre-2023 pure-play Internet/mail-order gap;
3. lack of a public vaping-specific response/coverage reconciliation;
4. weak published precision, especially all-`E` quarters in 2024 and 2025;
5. lack of independent reconciliation against Health Canada shipment values,
   excise, scanner data or another non-duplicative retail route.
