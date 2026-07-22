# Global market-data route plan

Reviewed 2026-07-22. This is a public research plan, not observed sales data, an audited market study or a Pixan Oy statement.

## Publication target

For every country-year, publish two different concepts when evidence permits:

1. **Observed or estimated legal retail market**: tax-paid and officially reported products placed on the lawful market.
2. **Estimated total consumption**: a separate scenario that may include illicit and cross-border consumption.

Every monetary result must retain the year, currency, product segments, low/base/high range, source links, input years, method IDs, evidence grade, coverage ratio, last verification date and known reconciliation gap. A ban is not evidence of zero consumption, and missing evidence is never converted to zero.

## Common 195-country base layer

### WHO Global Health Observatory

- [GHO OData API](https://www.who.int/data/gho/info/gho-odata-api) and [API endpoint](https://ghoapi.azureedge.net/api/)
- Adult current e-cigarette prevalence route: `TOBACCO_MPOWER_M2_PREVALENCE`, with adult e-cigarette indicator and both-sex filtering.
- Survey title, survey year, age group and national coverage must come from the companion survey metadata dataset. A reporting dimension must not be substituted for the true survey year.
- Youth prevalence is retained as a risk and demand signal, never as a replacement for adult prevalence.
- WHO price data supplies cheapest observed standardised open-liquid, closed-system and disposable-product prices. It is a price floor/input, not a weighted national average.
- WHO product-tax data is a price and tax-structure check. Aggregate tobacco-tax revenue must not be allocated to vaping without product-specific evidence.
- [WHO 2025 country profiles](https://www.who.int/teams/health-promotion/tobacco-control/global-tobacco-report-2025) are the legal and policy route for ENDS/ENNDS restrictions, product presence and source metadata.

### World Bank

- [Indicator API documentation](https://datahelpdesk.worldbank.org/knowledgebase/articles/898599-indicator-api-queries)
- Core inputs: total and relevant age-band population, market exchange rate, private-consumption PPP, GDP per capita PPP and CPI.
- Prevalence is multiplied by the population matching the source survey's actual age range. The 15–64 population must not be used automatically.
- Nominal currency conversion and purchasing-power adjustment remain separate transformations.

## Customs and supply route

- [UN Comtrade API documentation](https://uncomtrade.org/docs/un-comtrade-api/) and [data availability](https://uncomtrade.org/docs/data-availability/)
- HS 2022 starting points: `854340` for electronic cigarettes/personal vaporising devices, `240412` for nicotine-containing non-combustion inhalation products, and a carefully narrowed route under `240419` where national tariff detail permits.
- The dedicated HS 2022 codes do not create a clean pre-2022 time series. Older broad electrical codes require national tariff detail and an explicit comparability break.
- Required flow fields include reporter, partner, flow, classification, year, primary/customs value, CIF/FOB value, net weight, quantity, unit and estimated/reported flags.
- Apparent consumption is `domestic production + imports − exports ± inventory change`. It is a supply proxy, not retail sales.
- Reporter imports and mirror exports are alternatives. Mirror data may replace a missing route but is never added to reporter imports.
- A mutually exclusive customs bucket is mandatory: the same prefilled disposable cannot be counted as both hardware and liquid.
- Comtrade's licence and commercial-use restrictions require a rights review before raw tables or automated extracts are redistributed. The public site should publish only approved derived aggregates with attribution.

## EU-27 priority batch

- [Eurostat Comext](https://ec.europa.eu/eurostat/web/international-trade-in-goods/database) and [Comext API guidance](https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started/comext-database)
- CN starting points: `85434000`, `24041200` and annually reviewed `240419` subdivisions.
- [European Commission 2025 tobacco-excise impact assessment](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex:52025SC0560) provides an EU-level market and segment anchor. Underlying licensed third-party country tables must not be republished without permission.
- National specific excise systems are prioritised because realised receipts and rates can reproduce taxable millilitres or units when refunds, exports, destruction, rate changes and stockpiling are reconciled.
- First direct national routes: Germany, Spain, Italy, Portugal, Poland, the Baltic states, Denmark, Finland and Hungary, followed by the remaining EU countries.

## G20 and major-market direct routes

- United States: mandatory manufacturer reporting and FTC e-cigarette reports provide a leading-manufacturer floor, not necessarily the whole market.
- Canada: Health Canada's manufacturer/importer shipment series is a direct official monetary and physical anchor; shipment value remains separate from consumer retail sales.
- United Kingdom: policy impact assessments are consultation models unless a realised tax or sales series is available. The Vaping Products Duty starts only in October 2026.
- Indonesia and Korea: excise stamps/returns combined with specific rates can support direct quantity routes.
- Australia: lawful pharmacy supply and illicit consumption require separate scenarios.
- Brazil and India: prohibition can reduce the legal market without proving zero total consumption.
- China: exports indicate global supply, not domestic demand.
- Japan: heated-tobacco products remain outside the vaping/e-liquid result unless separately reported.
- Public company filings are market floors or cross-checks. Company revenue must not be added to tax, trade or demand estimates that may cover the same products.

## Estimation routes and reconciliation locks

The executable definitions are in [`model-config.json`](model-config.json), with implementation in [`../scripts/market_estimation.py`](../scripts/market_estimation.py).

Primary alternative routes:

1. direct reported annual retail value;
2. taxable quantity × retail price basket;
3. realised excise receipts ÷ specific rate × retail price basket;
4. apparent consumption × retail mark-up;
5. active users × annual spend;
6. active users × disjoint liquid, pod and device consumption × prices;
7. comparable-country scaling.

External global or regional estimates are sanity checks only. Alternative methods are reconciled through evidence-weighted consensus and never summed. From one evidence group, only its strongest eligible method contributes to the consensus.

Required product segments remain mutually exclusive:

- bare/refillable hardware;
- open-system liquid;
- closed rechargeable pods/refills;
- prefilled disposable products;
- nicotine-free products.

Heated-tobacco products and nicotine pouches remain separate markets.

## Lower-grade routes

These may guide prioritisation or widen uncertainty, but do not independently establish a finance-grade market value:

- product-notification SKU counts calibrated for duplicates and heavy-tailed sales per SKU;
- retailer licences × audited sales per outlet plus an online adjustment;
- WEEE/EPR, battery or waste-collection units as a consumption floor;
- recalls and safety alerts as product-presence signals;
- seizures combined with enforcement intensity as an illicit-risk modifier;
- broad nicotine/PG/VG material flows as an upper-bound signal;
- search, social and website-stock signals as directional indicators only.

## Delivery sequence

1. **EU-27:** Commission aggregate anchor, WHO base layer, Comext 2022+, and national excise routes, starting with Germany and Spain.
2. **G20:** direct government sources, WHO base layer and compatible company-reporting floors.
3. **Next 30 markets:** rank by the maximum of estimated users, HS 2022 imports and population × regional prevalence.
4. **Remaining countries:** WHO–World Bank–trade–legal-profile model with deliberately wider ranges and C/D evidence grades.

A global figure is released only as a harmonised country sum with an uncertainty model. It is not a mechanical sum of every country's extreme low or high case.
