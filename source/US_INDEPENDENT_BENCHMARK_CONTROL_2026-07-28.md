# United States independent benchmark control

Reviewed and source-verified: 2026-07-28

This package creates an official-source-only comparison harness for a future
United States retail sample. It does **not** calculate a United States market
total, annualise a short-period checkpoint, change the existing donor decision
or authorise a data purchase.

The controlling machine-readable files are:

- `source/US_INDEPENDENT_BENCHMARK_CONTROL_2026-07-28.json`
- `source/schemas/us-independent-benchmark-sample.schema.json`
- `scripts/validate_us_independent_benchmark.py`

## Official observations retained at source stage

| Geography / period | Observation | Value | Stage | Boundary |
|---|---|---:|---|---|
| United States 2015–2021 | FTC cartridge-system plus disposable sales | USD 304,170,046 to USD 2,763,284,338 | manufacturer-reported direct and indirect sales | leading manufacturers; open systems excluded; reporting population changes |
| United States, June 2024 four-week checkpoint | CDC-published dollar sales | USD 488,900,000 | partial brick-and-mortar consumer-retail scanner | online and tobacco-specialty-store sales unavailable; not a full year |
| United States, June 2024 four-week checkpoint | CDC-published units | 21,100,000 reported units | partial brick-and-mortar consumer-retail scanner | CDC reports 12.3 million disposables, or 58.1%; not a full-year denominator |
| Wisconsin FY2022 | published taxable vapor volume | 82,516,317 mL | state excise tax base | one state; not retail value |
| Wisconsin FY2023 | published taxable vapor volume | 141,245,968 mL | state excise tax base | one state; not retail value |
| Wisconsin FY2024 | published taxable vapor volume | 142,107,893 mL | state excise tax base | one state; not retail value |
| Wisconsin FY2025 | published taxable vapor volume | 161,408,755 mL | state excise tax base | one state; not retail value |
| North Carolina FY2022 | vapor tax receipts / reconstructed base | USD 6,507,171 / 130,143,420 mL | state excise receipt / derived tax base | receipt ÷ USD 0.05/mL; rounded source dollars |
| North Carolina FY2023 | vapor tax receipts / reconstructed base | USD 6,676,754 / 133,535,080 mL | state excise receipt / derived tax base | receipt ÷ USD 0.05/mL; rounded source dollars |
| North Carolina FY2024 | vapor tax receipts / reconstructed base | USD 6,429,692 / 128,593,840 mL | state excise receipt / derived tax base | receipt ÷ USD 0.05/mL; rounded source dollars |

North Carolina's official note states that the USD 0.05 per fluid-millilitre
tax applies to consumable vapor products containing nicotine and that the
discount does not apply. The reconstructed volume is therefore:

`published whole-dollar vapor tax receipt / 0.05 USD per mL`

The result inherits the source table's whole-dollar rounding. It is a tax-base
reconstruction, not an observed retail-sale volume or market value.

## Import route

The Census international-trade API and USITC HTS route remains
`queued_not_computed`.

- Census states that all current international-trade API calls require an API
  key. No key is stored in the repository.
- HTS `85434000` is the current device starting point.
- The mutually exclusive ten-digit United States mapping for liquids,
  prefilled disposables and hardware, the `240412` mapping and the pre-2022
  break must be reviewed before retrieval.
- Border imports remain trade-stage evidence and cannot be added to domestic
  manufacturer sales, state excise bases or retail scanner sales.

## Non-addition locks

The following operations are prohibited:

1. adding FTC manufacturer sales to CDC retail sales;
2. adding Wisconsin or North Carolina state tax bases to a national value;
3. adding imports to domestic sales;
4. multiplying the CDC four-week checkpoint by 13 to create an annual value;
5. treating online, vape-shop or other missing channels as zero.

The observations may be compared only after year, product scope, geography,
channel, transaction stage, currency and tax basis are matched. Differences
must be bridged through separately sourced reporting-population, margin, tax,
inventory, return, open-system and missing-channel fields.

## Sample acceptance

A future commercial or official retail sample remains unscored until all six
gates pass:

- **G1:** at least 24 complete populated months, including a period overlapping
  an official FTC aggregate;
- **G2:** country-specific dictionary, method, projection, missingness,
  revision and record-status fields;
- **G3:** mutually mapped product segments and quantified physical and online
  channel coverage;
- **G4:** a same-year FTC matched-subset bridge, periodic-to-annual agreement
  within 0.01% and an unexplained residual no greater than the larger of 10%
  or the published sampling error;
- **G5:** written lender, buyer, adviser, auditor and controlled-data-room
  rights for permitted derived output;
- **G6:** all-in price, tax, user, export, retention, cancellation and renewal
  terms.

The 10% G4 residual is a proposed control threshold, not an observed market
fact. A raw deviation between manufacturer and retail stages is not itself a
pass or fail.

After G1–G6, D1–D10 remain separate. A private licensed sample cannot by itself
pass D9 unless a public aggregate and reproducible source chain are permitted.
The existing United States donor candidate therefore remains `not_accepted`,
and this package adds zero accepted donors.

## Official source links

- [FTC E-Cigarette Report for 2021](https://www.ftc.gov/reports/e-cigarette-report-2021)
- [FTC E-Cigarette Report for 2015–2018](https://www.ftc.gov/reports/e-cigarette-report-2015-2018)
- [CDC Electronic Cigarettes, June 2024 sales checkpoint](https://www.cdc.gov/TemplatePackage/contrib/widgets/microsite-collection-viewer/index.html?cdcCollectionid=398772)
- [Wisconsin cigarette and other tobacco product collections](https://www.revenue.wi.gov/DORReports/Cigarette-and-Other-Tobacco-Product-Collections.pdf)
- [North Carolina Statistical Abstract of Taxes 2024](https://www.ncdor.gov/documents/reports/statistical-abstract-north-carolina-taxes-2024/open)
- [Census international-trade API documentation](https://www.census.gov/data/developers/data-sets/international-trade.html)
- [USITC HTS search for 8543.40.00](https://hts.usitc.gov/search?query=8543.40.00)
