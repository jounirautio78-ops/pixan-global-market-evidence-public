# New Zealand, Canada and Germany donor-control sprint

**Review date:** 2026-08-02

**Publication boundary:** Independent public-source research. This is not Pixan Oy's official position, an audit, a valuation, legal advice or an investment recommendation.

## Decision lock

This sprint adds transparent controls but no accepted donor market and no
global market value. The primary donor gate remains **0/3** and the global
retail value remains **`NOT COMPUTED`**.

| Country | Public control added or clarified | Decision effect |
|---|---|---|
| New Zealand | Exact 2024 Stats NZ import and export controls, two arithmetic net-border proxies and two ratios to the existing public specialist-return subtotal. | Diagnostic only. No retail uplift, range, margin or D10 reconciliation is inferred. |
| Canada | D5, D7 and D10 evidence boundaries are stated against the current official sources. | No new Canadian value. D5 and D7 remain failed; D10 remains open. |
| Germany | Prospective benchmark `DE-BLIND-1.0.0` is recorded against final official 2023 and 2024 taxed-liquid controls. | **NOT SCORED.** No donor, market-value, purchasing or other commercial effect. |

## New Zealand: exact Stats NZ border controls

The final Stats NZ calendar-2024 HS10 import and export files were filtered
under one locked selection rule. The selection includes HS10 `8543400000` for
the full year; broad pre-1 July liquid codes `2404120000`, `2404190100` and
`2404190500`; and, from 1 July, only identified disposable, cartridge and
vaping-liquid keys. Residual “other” keys are excluded. The rule is a vaping-
targeted proxy, not a claim that the selected customs codes are pure or
exhaustive.

### Reproduced controls

| Control | 2024 value (NZD) | Calculation or source field |
|---|---:|---|
| Selected imports, VFD | 189,640,890 | Sum of selected Stats NZ import VFD rows |
| Selected imports, CIF | 203,340,531 | Sum of selected Stats NZ import CIF rows |
| Selected total exports, FOB | 6,270,209 | Domestic exports 4,835,939 + re-exports 1,434,270 |
| Arithmetic net-border proxy, VFD basis | 183,370,681 | 189,640,890 − 6,270,209 |
| Arithmetic net-border proxy, CIF basis | 197,070,322 | 203,340,531 − 6,270,209 |

The existing public 2024 identified-vaping specialist-return subtotal is NZD
274,180,410.21. Its diagnostic ratios to the two net-border proxies are:

- `274,180,410.21 / 183,370,681 = 1.495224911`
- `274,180,410.21 / 197,070,322 = 1.391282094`

The arithmetic is reproducible, but the interpretation is deliberately
fail-closed. VFD, CIF and FOB are border-stage values and do not share a common
consumer-retail valuation basis. Subtracting exports does not create an
apparent-consumption identity because domestic production, inventory changes,
low-value and direct-to-consumer imports, product-classification error,
wholesale and retail margins, GST, returns and timing are unresolved. The
ratios are therefore not mark-ups, coverage rates, error bounds or market-size
uplifts.

The control does not close nationwide-channel coverage or independent
same-boundary reconciliation. It remains separate from the specialist-return
subtotal and contributes no eligible donor value.

Official sources:

- [New Zealand Ministry of Health — annual returns 2024](https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2024)
- [Stats NZ — Overseas merchandise trade datasets](https://www.stats.govt.nz/large-datasets/csv-files-for-download/overseas-merchandise-trade-datasets/)
- [Stats NZ — 2024 imports by HS10 and country](https://www3.stats.govt.nz/HS10_by_Country/2024_Imports_HS10.zip)
- [Stats NZ — 2024 exports by HS10 and country](https://www3.stats.govt.nz/HS10_by_Country/2024_Exports_HS10.zip)
- [Stats NZ — Overseas merchandise trade metadata](https://datainfoplus.stats.govt.nz/Item/nz.govt.stats/6ed114da-3571-40d4-a89f-932068a4c753/119)
- [New Zealand Gazette — Tariff (Statistical Requirements) Amendment Notice (No. 1) 2024](https://gazette.govt.nz/notice/id/2024-go2532)

## Canada: D5, D7 and D10 boundaries

This sprint creates **no new Canadian market value**. It only states what the
reviewed official sources can and cannot establish.

### D5 — nationwide channel coverage: FAILED

Statistics Canada's Retail Commodity Survey target population ends at NAICS
`459993`, while Statistics Canada's NAICS examples place electronic-cigarette
and vaping-product retail in `459999`. Online sales made by an in-scope
merchant follow the goods classification, but that rule does not bring an
excluded specialist `459999` merchant into the survey frame. Specialist,
foreign and direct-to-consumer values and the overlaps among channels remain
unquantified. Missing channel value is not zero.

D5 can close only with a rights-usable calendar-2024 national vaping-only
consumer-retail value or a de-duplicated channel bridge covering specialist,
general retail, convenience/fuel, domestic online, direct-to-consumer and
material cross-border routes.

### D7 — method, missingness and precision: FAILED

The public Retail Commodity Survey material documents the survey population,
sample design, imputation sequence, calibration, quarterly construction and
revision process. However, the reviewed public release does not provide exact
NAPCS `5619122` response counts, response rate, imputation rate, coefficient of
variation, standard error, confidence interval or the covariance needed for an
annual precision calculation. The published `E` quality flags cannot be
converted into an exact uncertainty interval.

D7 can close only with the commodity-specific missingness and precision
metrics, or with a replacement source that publishes an equivalent auditable
uncertainty boundary.

### D10 — independent same-boundary reconciliation: OPEN

The monthly and quarterly Retail Commodity Survey series are two releases from
the same survey and are not independent reconciliation routes. Health Canada's
public vaping-sales records are an independent manufacturer/importer shipment-
stage source, not consumer retail sell-through. They do not supply a matching
retail-channel, tax and transaction-stage bridge. No de-duplicated,
same-boundary calendar-2024 reconciliation was established.

D10 can close only with an independent national consumer-retail estimate or
direct official validation on matching year, products, channels, transaction
stage and tax basis, with method, precision and reuse rights documented.

Official sources:

- [Statistics Canada — Retail Commodity Survey methodology](https://www23.statcan.gc.ca/imdb/p2SV.pl?Function=getSurvey&Id=1539382)
- [Statistics Canada — NAICS 459999 examples](https://www23.statcan.gc.ca/imdb/p3VD.pl?CLV=5&CPV=459999&CST=27012022&CVD=1370970&Function=getAllExample&MLV=5&TVD=1369825&V=438494&VST=27012022)
- [Statistics Canada — quarterly Retail Commodity Survey data](https://www150.statcan.gc.ca/n1/en/tbl/csv/20100071-eng.zip)
- [Statistics Canada — monthly Retail Commodity Survey data](https://www150.statcan.gc.ca/n1/en/tbl/csv/20100080-eng.zip)
- [Health Canada — vaping product sales in Canada](https://health-infobase.canada.ca/substance-use/vaping/sales/)
- [Canada — Vaping Products Reporting Regulations](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2023-123/FullText.html)

## Germany: prospective blind benchmark `DE-BLIND-1.0.0`

The benchmark is preregistered for a future, independently received dataset.
It is not a current score and must not be tuned after a submission is opened.
The official numeric controls are tax-stage liquid volumes, not retail sales:

| Control | Official value | Reproduction | Governance tolerance |
|---|---:|---|---:|
| 2023 taxed net substitutes/liquids | 1,241,000 L | 1,260,000 L gross − 19,000 L refunds | 15% annual |
| 2024 taxed net substitutes/liquids | 1,284,000 L | 1,312,000 L gross − 28,000 L refunds | 15% annual |
| 2023–2024 combined | 2,525,000 L | 1,241,000 + 1,284,000 | 10% combined |

The 15% annual and 10% combined caps are fixed governance tolerances, not
sampling errors or Destatis publication precision. Numeric proximity may be
tested only after product, unit, period, channel, tax, transaction-stage,
observed-versus-modelled, revision and de-duplication boundaries are checked.
Passing a numeric cap cannot prove that a retail dataset and the official
tax-stamp/release proxy measure the same event.

Current status: **NOT SCORED**. No future input has been admitted to this public
record, no result is inferred, and the benchmark has no automatic effect on
Germany's donor status, a global value, disclosure, purchasing or any other
commercial decision. Germany's national all-channel consumer-retail value
therefore remains **`NOT COMPUTED`**.

Official source:

- [Destatis GENESIS — table 73411-0003, tobacco-tax statistics](https://genesis.destatis.de/datenbank/online/statistic/73411/table/73411-0003)

## Finnish summary / suomenkielinen yhteenveto

Tämä on riippumaton julkisiin lähteisiin perustuva tutkimusmuistio, ei Pixan
Oy:n virallinen kanta, tilintarkastus, arvonmääritys tai oikeudellinen lausunto.

- Uuden-Seelannin tarkat tullikontrollit ovat 189 640 890 NZD VFD,
  203 340 531 NZD CIF ja 6 270 209 NZD FOB-vientiä. Vähennyslaskelmat tuottavat
  183 370 681 ja 197 070 322 NZD:n rajavaiheen proxyt. Suhteet olemassa olevaan
  specialist-subtotaliin ovat 1,495224911 ja 1,391282094. Ne eivät ole
  markkina-arvioita, katteita tai uplift-kertoimia.
- Kanadaan ei lisätä uutta arvoa. D5 jää hylätyksi puuttuvan specialist- ja
  muun kanavapeiton vuoksi, D7 puuttuvien commodity-kohtaisten tarkkuuslukujen
  vuoksi ja D10 avoimeksi, koska riippumaton saman rajauksen retail-täsmäytys
  puuttuu.
- Saksan `DE-BLIND-1.0.0` käyttää ennakkoon lukittuina kontrolleina 1 241 000
  litraa vuodelta 2023, 1 284 000 litraa vuodelta 2024 ja yhteensä 2 525 000
  litraa. Vuosiraja on 15 % ja kahden vuoden raja 10 %. Testi on **NOT SCORED**
  eikä sillä ole donor-, markkina-arvo- tai kaupallista vaikutusta.
- Hyväksyttyjen donor-markkinoiden määrä pysyy 0/3 ja globaali retail-arvo
  tilassa **NOT COMPUTED**.
