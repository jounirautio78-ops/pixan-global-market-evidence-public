# Switzerland FOCBS route and official price anchor

**Reviewed:** 2026-07-31
**Public status:** method and price-input evidence only; Swiss retail value
remains `not_computed`

## Result

The Swiss Federal Office for Customs and Border Security (FOCBS/BAZG) directed
the aggregate-data request to the official SwissImpex, Tares and published
tobacco-tax routes. The response did not supply annual taxed millilitres,
category-specific excise receipts or nationwide vaping retail sales.

The official routes nevertheless establish:

- a reproducible monthly customs-data route by eight-digit tariff number and
  partner country;
- the statistical control-key structure and its 1 March 2026 classification
  change;
- tobacco-excise rates of CHF 1.00/ml for disposable contents with or without
  nicotine and CHF 0.20/ml for nicotine liquids for reusable products; and
- an official CHF 4.43/ml average-price reference for both nicotine refill
  liquids and disposable contents in the 2025 Federal Council report.

The CHF 4.43/ml figure is published as one price input. It is not a complete
calendar-year market average, taxed volume, annual sales value or nationwide
retail-market figure and is not multiplied into a market total.

## Customs classification boundary

The current import control keys, effective from 1 March 2026, include:

- `2404.1290/501`: disposable e-cigarette containing nicotine;
- `2404.1290/502`: nicotine refill liquid or a reusable product;
- `2404.1990/501`: disposable nicotine-free e-cigarette; and
- `8543.4000/502`: reusable e-cigarette with a nicotine consumable.

The public TN8-by-country file contains the tariff number, supplementary unit,
quantity, kilograms, statistical value, period, country and status. It does
not expose the statistical control key. Therefore the full four-category split
cannot be published as an exact official series from that file alone.

Customs values remain border-stage trade signals. They are not domestic
consumer sell-through and do not contain the retail-margin, tax, inventory,
domestic-production, re-export, channel or illicit-flow bridges required for a
retail value.

## Publication-rights boundary

The opendata.swiss records for the relevant foreign-trade and tariff metadata
use the `terms_by_ask` condition. Source attribution is mandatory and
commercial use requires prior permission from the data owner.

This evidence centre supports lender and buyer diligence. Derived SwissImpex
trade totals are therefore withheld from the public repository until FOCBS
confirms commercial decision-support use, attribution, derivative-output and
onward-disclosure rights in writing.

The public dashboard publishes only the official route, classification,
tax-rate context and CHF 4.43/ml price anchor. It publishes no new Swiss
customs total, national retail value, donor score or global-roll-up input.

## Official sources

- [Swiss foreign-trade statistics database and open-data route](https://www.bazg.admin.ch/en/swiss-foreign-trade-statistics-database-opendata)
- [Foreign trade by tariff number and country](https://opendata.swiss/en/dataset/waren-aussenhandel-nach-tarifnummer-land)
- [Tariff-number and statistical control-key metadata](https://opendata.swiss/en/dataset/waren-aussenhandel-stammdaten-tarifnummern)
- [Current e-cigarette import fact sheet](https://www.bazg.admin.ch/dam/en/sd-web/ONuHZU913W8U/55%20d%20Merkblatt-Einfuhr%20E-Zigaretten%20per%2001.04.2026.pdf)
- [Current tobacco-tax instruction R-120-3](https://www.bazg.admin.ch/dam/de/sd-web/LOdB10XnvqWr/R-120-3%20Tabaksteuer_01.06.2026.pdf)
- [2025 Federal Council report containing the official price reference](https://cms.news.admin.ch/fileservice/sdweb-docs-prod-nsbcch-files/files/2025/12/19/0b6e6f46-9c83-4a23-85a9-eb891a093fe8.pdf)
- [opendata.swiss terms of use](https://opendata.swiss/en/terms-of-use)

## Next evidence required

1. Written permission for the intended commercial decision-support and
   onward-disclosure use.
2. A national monthly table by statistical control key, or confirmation that
   no such existing aggregate can be supplied.
3. Category-specific taxed millilitres and net excise for 1 October–31
   December 2024, calendar year 2025 and the available 2026 period.
4. The exact assessment/release/collection stage and the treatment of refunds,
   corrections, exports and warehouse movements.
5. A same-period retail or POS reconciliation before any national retail-value
   conclusion.
