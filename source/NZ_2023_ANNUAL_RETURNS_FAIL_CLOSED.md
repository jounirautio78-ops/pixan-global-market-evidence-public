# New Zealand 2023 annual returns: official boundary and fail-closed reconstruction status

Reviewed: 2026-07-24

## Official aggregate

The New Zealand Ministry of Health reports:

- at least NZD 374 million of 2023 notifiable-product revenue;
- 2,570 annual returns, comprising 516 specialist-retailer (AVP), 47 internet
  specialist-retailer (AIS), 32 manufacturer/importer (Notifier), and 1,975
  general-retailer (RPS) returns.

The official headline includes heated-tobacco products, excludes smoked tobacco,
combines several supply-chain stages, is incomplete, and carries an explicit
data-quality warning. The Ministry does not recommend the collection for
in-depth research. It therefore remains a mixed-scope lower bound rather than a
national vaping retail-market value.

Primary page:
[Vaping product annual returns 2023](https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2023)

## Reviewed public workbooks

The six official downloads were retrieved for controlled aggregate analysis.
Their rows, business identifiers, product identifiers, brands and respondent
information are not copied into this public repository.

| Workbook | Bytes | SHA-256 at retrieval |
| --- | ---: | --- |
| [AVP Returns 2023](https://www.health.govt.nz/system/files/2024-12/avp-returns-2023%20%28updated-dec24%29.xlsx) | 3,279,638 | `08e4e48246f1f2a1e219d58cd862c8fe2d8cda3534546737ce0e0a8305572d0b` |
| [AIS Returns 2023](https://www.health.govt.nz/system/files/2024-12/ais-returns-2023%20%28updated-dec24%29.xlsx) | 546,425 | `418953133448d61d6185be0b1546a8e6336dd49bbcd6efd65a03d8bc9d1466fb` |
| [Notifier Returns 2023](https://www.health.govt.nz/system/files/2024-10/notifier-returns-2023.xlsx) | 491,717 | `6276bbf9bcc8ab4d1da9116bf3c6e006185abb6a91728995dfe993f52fd740ba` |
| [RPS Returns 2023, part 1](https://www.health.govt.nz/system/files/2024-12/rps-returns-2023-part-1%20%28updated-dec24%29.xlsx) | 1,841,050 | `1f01b75b213baeb454b16dda7d34ca796873fbe006ae2ff7f9a263c82a9ba87b` |
| [RPS Returns 2023, part 2](https://www.health.govt.nz/system/files/2024-12/rps-returns-2023-part-2%20%28updated-dec24%29.xlsx) | 1,829,284 | `7507fdae5c263e1eea45306e005aabe5f830e7b2a77ee59abff155d9725ae7ce` |
| [RPS Returns 2023, part 3](https://www.health.govt.nz/system/files/2024-12/rps-returns-2023-part-3%20%28updated-dec24%29.xlsx) | 1,614,617 | `7afa1931c330e2188c465f5bcbcb09ef6dc1cd9f00d70c37fea63ba59cba852f` |

## Reconstruction status

No new 2023 retail-value reconstruction is published in this release. The
required product-scope classification, quantity-field validation, repeated-row
analysis, supply-stage de-duplication, tax-basis review and independent
reconciliation have not all been completed. Every derived 2023 category
therefore remains `not_computed`; missing or invalid inputs are not treated as
zero.

The next reproducible step is to compute privacy-safe aggregates separately for
AVP/AIS retail value, RPS quantities and Notifier supply-stage value; classify
vaping versus heated-tobacco and other adjacent products; run exact-row
duplication sensitivities; and reconcile the resulting retail layer against an
independent official, tax, import or scanner-data route. Notifier values must
not be added to retailer values without a non-overlap proof.
