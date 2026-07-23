# New Zealand 2024 annual returns — aggregate reconciliation

Status: derived from official files, not an accepted donor market
Review date: 2026-07-24
Official landing page: https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2024

## Purpose

This note records an independent arithmetic check of the 29 XLSX workbooks linked by New Zealand's Ministry of Health for the 2024 notifiable-product annual returns. It is a reproducibility and quality-control record. It does not convert the files into a complete New Zealand vaping-market value.

Only aggregate results are published. The downloaded workbooks are not copied into this repository, and no licence code, business identity, brand, flavour or UPC is reproduced.

## Input and method

- 29 official XLSX workbooks: 1 AIS, 21 AVP, 1 Notifier and 6 RPS files.
- Downloaded size: 50,355,870 bytes.
- Rows below workbook headers: 882,422.
- Numeric `Total sales` cells: 612,765.
- Rows without a numeric `Total sales` value: 269,657.
- Every numeric `Total sales` cell was parsed as a finite number and summed without imputation.
- Product scope was classified conservatively from the published product-type text. The classes were identified vaping, identified adjacent notifiable product and unresolved product type.
- Exact whole-row hashes were counted only as a sensitivity test. Repeated rows were not automatically removed because the files do not establish whether identical rows are errors or legitimate repeated reporting.

The aggregate analysis record has SHA-256 `e4243d2225caff2b3953199267d823feb40bb64cbd9b55fded2ddcabc1ad103d`.

## Results

| Check | Result |
|---|---:|
| Raw sum of numeric `Total sales` cells | NZD 280,684,512.81 |
| Ministry headline | at least NZD 280 million |
| Exact repeated row signatures beyond the first | 95,144 |
| Raw sales carried by those repeated rows | NZD 16,123,457.76 |
| Exact-row-deduplicated sensitivity | NZD 264,561,055.05 |
| Identified vaping rows, raw sum | NZD 274,180,410.21 |
| Identified adjacent notifiable-product rows, raw sum | NZD 2,137,085.24 |
| Unresolved product-type rows, raw sum | NZD 4,367,017.37 |
| Identified vaping, exact-row-deduplicated sensitivity | NZD 258,327,110.88 |

The three conservative product classes partition the raw product-row sum:

`274,180,410.21 + 2,137,085.24 + 4,367,017.37 = 280,684,512.82`

The one-cent difference from the workbook-level raw sum is a rounding artefact from aggregating the class subtotals.

## Quality boundary

The Ministry describes the published 2024 information as incomplete, limited to specialist vape retailer sales and unsuitable for in-depth research. The files also leave material interpretation issues:

- general retail is not included;
- missing or nil returns cannot be distinguished completely from the aggregate files;
- the product scope includes adjacent notifiable products;
- the meaning of exact repeated rows is unverified;
- 136,528 rows with numeric `Total sales`, RRP and quantity differ from `RRP × quantity`;
- GST inclusion or exclusion is not established consistently;
- the separate `Other products (total sales)` field cannot be added safely without resolving its scope and possible overlap.

For those reasons, neither NZD 280,684,512.81 nor the sensitivity values are labelled as a cleaned national retail-market estimate. They remain derived, non-comparable and donor-ineligible.

## Finnish summary / Suomenkielinen yhteenveto

Kaikkien 29 virallisen vuoden 2024 XLSX-tiedoston numeeristen `Total sales` -solujen raakasumma on 280 684 512,81 Uuden-Seelannin dollaria. Se täsmää ministeriön vähintään 280 miljoonan dollarin otsikkolukuun. Varovainen tekstiluokitus tunnistaa sähkötupakkatuoteriveiksi 274 180 410,21 dollaria.

Luku ei ole puhdistettu koko maan markkina-arvo: yleisvähittäiskauppa puuttuu, tuoteryhmä on osin sekoittunut, toistuvien rivien merkitystä ei tunneta, puuttuvat ilmoitukset ovat avoimia ja GST-käsittelyä ei ole vahvistettu. Täsmäytys ei siksi muuta hyväksyttyjen luovuttajamarkkinoiden määrää.
