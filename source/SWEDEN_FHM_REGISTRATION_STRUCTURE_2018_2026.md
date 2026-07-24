# Sweden FHM registration structure, 2018–2026

## Evidence status

The Public Health Agency of Sweden (Folkhälsomyndigheten, FHM) supplied the aggregate table below in an official public-record response received on 24 July 2026. The response establishes official registration-structure counts. It is **not annual sales**, sold device units, sold liquid volume, market share or an accepted donor market.

The public contextual source is FHM's canonical guidance page for [electronic cigarettes and refill containers](https://www.folkhalsomyndigheten.se/regler-och-tillsyn/tobak-och-nikotinprodukter-regler-for-tillverkning-handel-och-hantering/elektroniska-cigaretter-och-pafyllningsbehallare-sa-foljer-du-reglerna/). That page explains the notification register and links to the public product list. The historical aggregate workbook and the source correspondence are retained outside this public repository and are not republished here. Consequently, the exact historical values are official-response evidence but cannot be reconstructed solely from the current public product list.

## Reviewed aggregate

| Year | Reporting entities | Notified products | Active products | Withdrawn products |
| ---: | ---: | ---: | ---: | ---: |
| 2018 | 226 | 18,356 | 16,264 | 2,092 |
| 2019 | 310 | 24,525 | 17,704 | 6,821 |
| 2020 | 369 | 29,125 | 18,745 | 10,380 |
| 2021 | 399 | 31,243 | 19,251 | 11,992 |
| 2022 | 431 | 34,163 | 20,256 | 13,907 |
| 2023 | 544 | 40,593 | 25,278 | 15,315 |
| 2024 | 619 | 48,036 | 30,371 | 17,665 |
| 2025 | 663 | 52,889 | 32,899 | 19,990 |
| 2026 | 687 | 55,273 | 32,889 | 22,384 |

For every displayed year, the supplied values satisfy:

`notified products = active products + withdrawn products`

The 2026 values are a current-year snapshot as of 24 July 2026. They are not a completed calendar-year total and must not be compared with completed years as though finality were identical.

## Machine-readable mapping

The 36 observations in `source/market-observations.json` use four separate metrics:

- `reporting_entities_count`
- `notified_products_count`
- `active_products_count`
- `withdrawn_products_count`

All four metrics use:

- evidence status `official_observed`;
- source `SE-FHM-PUBLIC-RECORD-RESPONSE-2026-07-24`;
- product scope `notified_e_cigarettes_and_refill_containers`;
- market-value basis `official_registration_structure_count_not_sales_or_market_value`;
- `comparableMarketValue: false`; and
- `atlasEstimate: false`.

Years 2018–2025 use period `authority_supplied_year_label` and finality `official_response_year_label`. Those years are the labels supplied by the authority, not assumed calendar-year flows or year-end snapshots. Year 2026 uses period `current_snapshot_as_of_2026_07_24` and finality `official_current_snapshot`.

## Interpretation boundary

The series can evidence the scale and evolution of Sweden's regulated notification structure. It cannot by itself establish consumer demand, transaction value, quantities sold, liquid consumed, illicit-market size, product uniqueness, brand share or commercial revenue. A product can appear through more than one notifier, and the public list has visibility conditions described by FHM. No causal or sales conclusion is inferred from growth in notifications or withdrawals.

The series is therefore kept outside the donor count. The global market estimate remains `not_computed` until at least three markets independently satisfy every donor-acceptance criterion.
