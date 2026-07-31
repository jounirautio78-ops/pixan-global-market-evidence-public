# Canada, Germany, New Zealand and Poland donor-closure sprint

Reviewed: 2026-07-31  
Public boundary: independent public-source research; not Pixan Oy's official position, an audit, a valuation or legal advice.

## Decision outcome

No country changed donor status. The acceptance gate remains **0/3** and the
global retail value remains **`null/not_computed`**. The new evidence improves
channel, product, fiscal and revision controls but does not supply a complete,
same-year national consumer-retail value that passes D1-D10.

| Country | New evidence | Decision impact |
|---|---|---|
| Canada | Official CTNS 2022 public-use microdata shows an in-person vape shop as the usual source for 62.9% of device users and 63.0% of liquid users with valid answers. | Supports treating the RCS-excluded specialist channel as potentially material but does not establish monetary materiality; D5 remains failed because its missing 2024 CAD value is not quantified. Canada stays 7/10. |
| Germany | Official base-2020 CPI weights separately identify devices and a mixed liquid/tobacco-stick item. Official WZ 47.26 VAT-return supplies-and-services turnover provides a broad tobacco-specialist channel envelope. | Improves product and channel mapping, but neither source is e-cigarette-only retail sales. Germany remains not accepted. |
| New Zealand | Official 2024 policy papers show more than 7,000 physical vape sellers, 1,280 specialist retailers, 146 specialist websites and an approval problem potentially affecting 117 companies and 546 stores. | Confirms that legal-entity, store and site counts cannot be divided into a coverage rate. D5 remains failed; D8 and D10 remain open. New Zealand stays 7/10. |
| Poland | Official disposable-unit sales, e-liquid excise, customs net-mass and a conflicting 2023 volume revision route; a 2015 UOKiK decision adds a historical value and channel benchmark. | Adds bounded anchors and exposes a 9.71% official volume conflict, but no full-market consumer-retail value. Poland is not scored as a donor. |

## Additional public controls admitted in v40

The following records improve triangulation without changing the fail-closed
decision. Every monetary record retains its original currency, period,
transaction stage and product scope. An analytical EUR equivalent is generated
only where the reviewed FX rules permit it.

### Canada: 2021 full-market and channel benchmark

Health Canada's first legislative review states that the 2021 Canadian vaping
market was estimated at **CAD 2.04 billion**. It separately reports gas and
convenience sales of **CAD 631 million (31%)** and online sales of approximately
**CAD 436 million (21%)**. The report attributes the figures to a 2022 custom
Euromonitor International study compiled for Health Canada.

Source: <https://www.canada.ca/en/health-canada/programs/consultation-legislative-review-tobacco-vaping-products-act/final-report.html>.

The published values are useful institutional benchmarks, not official
measurements with a public underlying workbook or method. The 2021 Statistics
Canada RCS value of CAD 992.732 million is only 48.66% of the published CAD
2.04 billion benchmark; the CAD 1.047268 billion difference confirms that the
two public boundaries are materially different. It does not identify the
missing 2024 value or prove that every difference is a channel omission.

The public 2023 Survey of Household Spending microdata was also inspected. Its
released hierarchy combines tobacco products, smokers' supplies and cannabis
in one field and does not expose a vaping-only expenditure field. It is
therefore a documented dead end for a vaping-specific donor value.

### Germany: official apparent-supply and tax/VAT sensitivity

Eurostat's annual PRODCOM/Comext dissemination API publishes Germany's 2024
sold production, imports and exports for two relevant product classes:

| Product class | Sold production | Imports | Exports | Mechanical apparent supply |
|---|---:|---:|---:|---:|
| `20595980`, nicotine and nicotine substitutes intended for inhalation | EUR 39,078,000 | EUR 400,843,037 | EUR 120,676,188 | EUR 319,244,849 |
| `27901152`, electronic cigarettes and similar personal vaporising devices | EUR 99,890,000 | EUR 490,580,247 | EUR 301,380,538 | EUR 289,089,709 |
| **Combined** |  |  |  | **EUR 608,334,558** |

Sources:

- <https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-059358/A.DE.20595980.?startPeriod=2024&endPeriod=2024>
- <https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-059358/A.DE.27901152.?startPeriod=2024&endPeriod=2024>

The sold-production values carry Eurostat flag `:E`. Adding the existing
Destatis 2024 substitutes-excise receipt of EUR 266 million and mechanically
applying Germany's 19% standard VAT rate gives:

`(EUR 608,334,558 + EUR 266,000,000) x 1.19 = EUR 1,040,458,124.02`

VAT source: <https://www.gesetze-im-internet.de/ustg_1980/__12.html>.

This is deliberately labelled a **zero-distribution-margin sensitivity**, not
a retail-market estimate. Production and border values are not retail
sell-through; the formula does not resolve trade and product classification,
inventory, domestic production coverage, margins, discounts, illicit trade,
tax timing or whether the excise and supply records share the same boundary.

### New Zealand: 2019 and 2023 household-expenditure control

Stats NZ's detailed Household Economic Survey publishes national household
expenditure for e-cigarettes and refills. The year-ended-June estimates are NZD
42.276 million for 2019 and NZD 186.980 million for 2023. Devices and refills
sum exactly to each total, but the 2023 total has a 22.4% relative sampling
error and the device component has a 79.1% relative sampling error. Full values,
quality flags, hashes and the reproduction path are recorded in
[`NZ_2019_2023_HES_E_CIGARETTE_EXPENDITURE_CONTROL.md`](NZ_2019_2023_HES_E_CIGARETTE_EXPENDITURE_CONTROL.md).

The source is independent and nationwide, but it is not a calendar-year retail
sell-through census and does not share the 2024 Ministry annual-return boundary.
It therefore does not close D1, D5, D8 or D10 for the 2024 candidate.

### Poland: annual producer/importer quantity series and retail segment check

The Ministry of Health's annual-report table adds six product rows for
2019-2022: disposables, reusable devices, individual parts, kits, other devices
and refill containers/cartridges. The 2022 values are explicitly preliminary
because not all obliged entities had filed. The preliminary disposable figure
of 14,663,879 later rose to 19,525,600, a 33.15% revision.

Source: <https://api.sejm.gov.pl/sejm/term9/interpellations/attachment/ATTCTNBJB/i41718-o1.pdf>.

CMR separately reports approximately **PLN 2 billion** of disposable
e-cigarette sales in 2023. It is admitted only as a commercial disposable-only
segment estimate: the public page does not disclose a reproducible national
sample frame, weights, specialist-channel treatment or VAT basis, and it does
not cover refillable devices, liquids or pods.

Source: <https://www.cmr.com.pl/2024/01/jednorazowe-e-papierosy-przeboj-sprzedazy-2023/>.

The Poland volume bridge is strong but not a value bridge. Dividing official
2022 and 2023 excise receipts by the then-applicable PLN 0.55/ml rate produces
418.0 million ml and 806.545 million ml, respectively, only 0.46% and 0.14%
above the later official reported quantities. That independently checks the
liquid volume boundary, not consumer retail value.

## Canada: channel-materiality control

Official package:

- Statistics Canada CTNS 2022 landing page: <https://www150.statcan.gc.ca/n1/pub/13-25-0001/132500012022001-eng.htm>
- CSV package: <https://www150.statcan.gc.ca/n1/pub/13-25-0001/2022001/2022/CSV.zip>
- Reviewed ZIP SHA-256: `f2bbc5c0a0ea10fa15ef480972b828731a92a1376600e8e2039394ad2cd3320e`
- Files: `pumf.csv` and `pumf_bsw.csv`; survey weight `WTPP`; bootstrap weights `WRPP1`-`WRPP1000`.

For each source item, valid answers are codes 1 and 2. The weighted share is:

`sum(WTPP for yes) / sum(WTPP for yes or no)`

| Item | Yes / valid | Weighted yes / valid | Point estimate |
|---|---:|---:|---:|
| Devices from in-person vape shop (`VAP_40AR`) | 650 / 1,099 | 1,162,671.63 / 1,847,172.44 | 62.943% |
| Liquids from in-person vape shop (`VAP_41AR`) | 644 / 1,095 | 1,156,389.89 / 1,835,669.58 | 62.996% |

Precision is not computed. The public PUMF contains 12,133 unique IDs and the
bootstrap file contains 11,526; the 607 PUMF IDs absent from the replicate file
include valid channel answers and non-zero survey weights. No reviewed source
establishes that absent replicate weights are zero. The reproduction script
therefore reports the mismatch and withholds standard errors and intervals.

The questions are multi-select. Shares must not be added to 100%. They measure
self-reported usual acquisition source among past-30-day vapers, not spending,
retail sales, monetary materiality, channel coverage or the missing 2024 CAD
channel value. The survey target excludes territories, persons living on
reserves and other Indigenous settlements in the provinces, and collective
dwellings. The point estimates and mismatch diagnostic can be reproduced with
`scripts/reproduce_canada_ctns_channel_2022.py` and the official ZIP. CTNS is
not a same-boundary D10 reconciliation.

## Germany: product weights and broad specialist-channel envelope

Destatis's base-2020 CPI weighting pattern publishes:

- SEA-CPI `1232902200`, disposable and reusable electronic-cigarette devices:
  **0.05 per mille** (PDF page 22);
- SEA-CPI `0220301200`, liquid, tobacco sticks or similar products for
  e-cigarettes: **0.16 per mille** (PDF page 7).

Source: <https://www.destatis.de/EN/Themes/Economy/Prices/Consumer-Price-Index/Publications/Downloads-Consumer-Price-Indices/weighting-pattern-2020.pdf?__blob=publicationFile&v=2>  
Reviewed PDF SHA-256: `2c47d705f3c92ef20367f95567f009641841376fec9ed7685cc84427c3aa8754`.

These are expenditure-structure weights, not annual sales values. The liquid
item includes tobacco sticks. The parent `02203` weight is 3.39 per mille, of
which ordinary tobacco is 3.23 and the mixed liquid/tobacco-stick item only
0.16. Therefore the parent price index must not be labelled an e-cigarette or
e-liquid price index.

Destatis table 73311-0002 gives taxable supplies-and-services turnover for
enterprises whose main activity is WZ 47.26 retail sale of tobacco products.
Values below convert the published EUR-thousand rows to EUR:

| Year | Enterprises | Taxable supplies-and-services turnover |
|---|---:|---:|
| 2019 | 2,346 | EUR 2,247,267,035 |
| 2020 | 2,244 | EUR 2,444,948,000 |
| 2021 | 2,183 | EUR 2,325,648,577 |
| 2022 | 2,111 | EUR 2,510,888,578 |
| 2023 | 2,024 | EUR 2,581,608,198 |
| 2024 | 1,970 | EUR 2,687,776,000 |

Each historical row is bound to its official edition rather than inferred from
the current single-year Genesis download:

- 2019 workbook, `Daten 2009-2019` row 627, SHA-256
  `a93603428d3c5b3019e7b01eafc2a64b0320f682c572fc1178a343e1577e0934`:
  <https://www.destatis.de/DE/Themen/Staat/Steuern/Umsatzsteuer/Publikationen/Downloads-Umsatzsteuern/umsatzsteuerstatistik-zeitreihe-5733103197005.xlsx?__blob=publicationFile&v=5>
- 2020 report, table 2.3 on PDF page 22, SHA-256
  `e2d38ee9895dea299989a2368dafac7fef78091c3a558d33ee19858164703e19`:
  <https://www.destatis.de/DE/Themen/Staat/Steuern/Umsatzsteuer/Publikationen/Downloads-Umsatzsteuern/umsatzsteuer-2140810207004.pdf?__blob=publicationFile>
- 2021 workbook, `73311-02` row 625, SHA-256
  `e23ee1e302a8c0fb3cc61229c4a3bf8e7cf2354373e4b119266236f3b06058ed`:
  <https://www.destatis.de/DE/Themen/Staat/Steuern/Umsatzsteuer/Publikationen/Downloads-Umsatzsteuern/statistischer-bericht-umsatzsteuer-2140810217005.xlsx?__blob=publicationFile&v=3>
- 2022 workbook, `73311-03` row 625, SHA-256
  `48dbdee8fc65d1a93733bb3caa387cc5d82730564c61bd0e6703af281b8d9dc8`:
  <https://www.destatis.de/DE/Themen/Staat/Steuern/Umsatzsteuer/Publikationen/Downloads-Umsatzsteuern/statistischer-bericht-umsatzsteuer-2140810227005.xlsx?__blob=publicationFile&v=2>
- 2023 workbook, `73311-03` row 625, SHA-256
  `d4a9bf830e5174fe5a5271dd166508e1d19adbed4feb64f55b9ca89215f0fe89`:
  <https://www.destatis.de/DE/Themen/Staat/Steuern/Umsatzsteuer/Publikationen/Downloads-Umsatzsteuern/statistischer-bericht-umsatzsteuer-2140810237005.xlsx?__blob=publicationFile&v=5>
- 2024 canonical table and CSV, reviewed CSV SHA-256
  `e78bf04a7dfd0aab7a0c9b359bb4388d6c22608bfe3aee92ec9dbd598de5f9a4`:
  <https://genesis.destatis.de/datenbank/online/statistic/73311/table/73311-0002/>.

The series includes conventional tobacco and non-product enterprise revenue,
is not consumer RSP, and omits online-only WZ 47.91 and retailers classified by
another main activity. It is a deliberately broad channel envelope, never an
e-cigarette market value.

## New Zealand: store/entity denominator control

The official 11 June 2024 regulatory impact statement records at least 6,749
physical vape sellers in May 2023: 989 specialist vape retailers and at least
5,760 general vape retailers. By May 2024 it records 1,280 specialist retailers,
more than 7,000 physical vape sellers in total and 146 specialist websites.
Source: <https://www.health.govt.nz/system/files/2024-08/RIS-visibility-of-vape-products-and-proximity-of-Specialist-Vape-Retailers-Redacted.pdf>.

The Ministry's 23 May 2024 aide-memo reports an earlier specialist-approval
interpretation problem potentially affecting about 117 companies operating 546
stores. Source: <https://www.health.govt.nz/system/files/2024-10/H2024042044%20AM%20-%20Specialist%20Vape%20Retailer%20Approvals.pdf>.

The return instructions use different statistical units: an RPS return may
cover one legal entity with multiple stores, while AVP/AIS specialist returns
are store/site based. Consequently, ratios such as return count divided by
store count are prohibited as coverage estimates unless entity-store mapping,
dates, openings/closures and registration corrections are reconciled.

## Poland: admitted observations

### Reported disposable sales

The Ministry of Health response dated 23 February 2024 states that 2022 sales
of disposable electronic cigarettes were **19,525,600 units**. The surrounding
text links the measure to statutory annual producer/importer reports with sales
volumes by brand and type. The transaction stage and nationwide retail-channel
coverage are not stated.

Source, PDF page 2: <https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTD2VJJ5/i01345-o1.pdf>.

### E-liquid excise receipts

| Year | PLN | ECB annual-average analytical EUR equivalent |
|---|---:|---:|
| 2021 | 179,500,000 | 39,319,381.01 |
| 2022 | 229,900,000 | 49,059,916.66 |
| 2023 | 443,600,000 | 97,666,959.97 |
| 2024 | 561,400,000 | 130,382,405.18 |
| 2025 | 993,100,000 | existing reviewed dashboard conversion |

Sources: <https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTD4DHUB/i02408-o1.pdf> and <https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTDW7AZK/i18182-o1.pdf>.
These are state-budget excise receipts, not revenue or retail market value.

### Customs net-mass sensitivity

The Ministry of Finance's description-filtered AIS/e-Commerce extract for
release into free circulation reports disposable-device net mass of 2,612 kg
in 2019, 1,360 kg in 2020, 1,457 kg in 2021, 199,946 kg in 2022 and 1,075,597 kg
in 2023. The table also reports zero for 2018; zero is retained in this memo but
not inserted into the positive-value observation schema.

Source, PDF page 2: <https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTD2VJJ4/i01344-o1.pdf>.
The codes contain other products and analysts selected entries by goods
description. Net mass cannot be converted to units or retail value without a
documented weight, domestic-flow, stock and supply-stage bridge.

### Revision conflict

An April 2024 response reports **883,641,334.20 ml** for 2023 and says declared
quantities may be corrected. A January 2025 response reports **805,441 litres**
for the same year. The difference is **78,200,334.20 ml**, or **9.71%** of the
later figure. Both remain visible until the authority explains revision and
scope; neither is used as retail growth.

Sources: <https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTD4DHUB/i02408-o1.pdf> and <https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTDDEJZ5/i07255-o1.pdf>.

### Historical institutional benchmark

UOKiK decision DKK-211/2015 republishes an external May 2015 estimate of about
**PLN 500 million**. Its scope includes disposable and refillable e-cigarettes,
nicotine liquids and accessories. The same decision records an estimated 2,000
SMEs, an estimated 90% China-origin share, and an August 2014 channel split of 30%
Internet, 40% specialist shops/stands and 30% grocery/kiosk/petrol-station
sales.

Source: <https://decyzje.uokik.gov.pl/bp/dec_prez.nsf/43104c28a7a1be23c1257eac006d8dd4/7a82fa564deb307ac1257f370063717c/%24FILE/DKK1_421_48_15_MAB_BAT_CHIC_decyzja_BIP.pdf>, pages 6-9.
The value and structure figures are third-party estimates cited in an official
competition decision. Their exact annualisation, tax basis, transaction stage
and method are unavailable. They are historical institutional benchmarks, not
official observations or donor evidence. No EUR equivalent is computed because
the source does not establish a full-calendar-year reference period; the 2015
ECB annual-average rate remains a reviewed but unused reference rate.

## Excluded calculations

- No customs kilograms are converted to device units.
- No CPI weight is multiplied by an assumed national expenditure denominator.
- No WZ 47.26 turnover is labelled vaping sales.
- No Poland excise receipt is inverted into retail value.
- No New Zealand return-count/store-count ratio is treated as coverage.
- No Canada user-source share is converted to missing CAD sales.
- External Poland estimates of 32.3 million and 100 million disposables are not
  relabelled as official observations.

## Next evidence required

1. Canada: 2024 specialist-channel sell-through value and a same-boundary RCS /
   Health Canada reconciliation.
2. New Zealand: a legal-entity/store-aligned national general-retail value, GST
   definition and independent same-year reconciliation.
3. Poland: an authority explanation of the 2023 volume revision, the full
   producer/importer annual-report aggregate, channel coverage, prices and VAT.
4. Germany: e-cigarette-only WZ/EVS expenditure, same-year price basket, device
   sell-through and online/non-specialist coverage.
