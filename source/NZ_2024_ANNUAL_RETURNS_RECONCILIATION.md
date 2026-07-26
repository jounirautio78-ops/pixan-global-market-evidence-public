# New Zealand 2024 annual returns — aggregate reconciliation

Status: derived from official files, not an accepted donor market
Review date: 2026-07-26
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
- Product scope was classified deterministically from the published
  product-type text. Vaping consumables, devices/hardware and mixed systems
  are separately quantified. Herbal-smoking and smokeless-tobacco terms are
  classified first and excluded; all unmatched text is unresolved and
  excluded.
- Exact whole-row hashes were counted only as a sensitivity test. Repeated rows were not automatically removed because the files do not establish whether identical rows are errors or legitimate repeated reporting.

The public reproduction chain consists of:

- `source/NZ_2024_WORKBOOK_MANIFEST.json`, SHA-256
  `95b1c97e57b82b81b220ff3295b067c347474aacb1f8cb4d3d6244f454391343`;
- `scripts/analyze_nz_2024_returns.py`;
- `source/NZ_2024_PRODUCT_SCOPE_AUDIT.json`, SHA-256
  `4f6bb08650eb03716b114536c9bc08bcb4a80deb87c326527c891ad05187bb9b`.

The script validates the file set, sizes and SHA-256 hashes before reading any
workbook. Currency cells are summed with decimal arithmetic before half-up
rounding to two decimals.

## Results

| Check | Result |
|---|---:|
| Raw sum of numeric `Total sales` cells | NZD 280,684,512.81 |
| Ministry headline | at least NZD 280 million |
| Exact repeated row signatures beyond the first | 95,144 |
| Raw sales carried by those repeated rows | NZD 16,123,457.76 |
| Exact-row-deduplicated sensitivity | NZD 264,561,055.05 |
| Identified vaping rows, raw sum | NZD 274,180,410.21 |
| — vaping consumables | NZD 189,402,451.96 |
| — vaping devices or hardware | NZD 84,709,409.85 |
| — vaping mixed systems | NZD 68,548.40 |
| Identified adjacent notifiable-product rows, raw sum | NZD 2,137,085.24 |
| Unresolved product-type rows, raw sum | NZD 4,367,017.37 |
| Identified vaping, exact-row-deduplicated sensitivity | NZD 258,327,110.88 |

The identified-vaping total is the sum of the independently rounded vaping
subclasses:

`189,402,451.96 + 84,709,409.85 + 68,548.40 + 0.00 = 274,180,410.21`

The three top-level product classes partition the raw product-row sum:

`274,180,410.21 + 2,137,085.24 + 4,367,017.37 = 280,684,512.82`

The one-cent difference from the workbook-level raw sum is a rounding artefact
from independently rounding the class subtotals.

## Return-class boundary

| Return class | Role | Rows | Numeric `Total sales` cells | Reported sales |
|---|---|---:|---:|---:|
| AIS | specialist internet retailer | 29,689 | 29,086 | NZD 20,959,634.48 |
| AVP | specialist physical retailer | 689,277 | 583,679 | NZD 259,724,878.33 |
| Notifier | manufacturer or importer | 18,410 | 0 | NZD 0.00 |
| RPS | general retailer | 145,046 | 0 | NZD 0.00 |

All observed `Total sales` value comes from AIS and AVP specialist-retailer
files. Notifier quantities are not added. RPS quantities are valued only in
the separate sensitivity model and are not part of the observed
NZD 274,180,410.21 subtotal.

The Ministry reports 3,125 received returns: 1,970 RPS, 1,009 AVP, 83 AIS and
63 Notifier. The prior aggregate parser found 2,987 distinct non-blank licence
codes in the published product rows. The 138-return difference is unresolved
and is not assigned to nil, missing or late returns without official
confirmation.

## Quality boundary

The Ministry describes the published 2024 information as incomplete, limited to specialist vape retailer sales and unsuitable for in-depth research. The files also leave material interpretation issues:

- general retail is not included;
- missing or nil returns cannot be distinguished completely from the aggregate files;
- the product scope includes adjacent notifiable products;
- the meaning of exact repeated rows is unverified;
- 136,528 rows with numeric `Total sales`, RRP and quantity differ from `RRP × quantity`;
- GST inclusion or exclusion is not established consistently;
- the separate `Other products (total sales)` field cannot be added safely without resolving its scope and possible overlap.

For those reasons, neither NZD 280,684,512.81 nor the sensitivity values are
labelled as a cleaned national retail-market estimate. The deterministic
vaping-only subtotal closes the D3 device/consumable split and D4 adjacent
scope controls, but D5 national coverage fails and D8 GST basis and D10
independent reconciliation remain open. New Zealand is therefore
`not_accepted` at 7/10 criteria and remains donor-ineligible.

## Finnish summary / Suomenkielinen yhteenveto

Kaikkien 29 virallisen vuoden 2024 XLSX-tiedoston numeeristen `Total sales`
-solujen raakasumma on 280 684 512,81 Uuden-Seelannin dollaria. Se täsmää
ministeriön vähintään 280 miljoonan dollarin otsikkolukuun. Julkinen ja
toistettava tekstiluokitus tunnistaa sähkötupakkatuoteriveiksi
274 180 410,21 dollaria: kulutustarvikkeet 189 402 451,96, laitteet ja
hardware 84 709 409,85 sekä sekajärjestelmät 68 548,40 dollaria.

Viereiset tuoteryhmät 2 137 085,24 ja ratkaisematon tuotetyyppi
4 367 017,37 dollaria rajataan pois. Luku ei silti ole puhdistettu koko maan
markkina-arvo: yleisvähittäiskaupan havaittu arvo puuttuu, toistuvien rivien
merkitystä ei tunneta, ilmoitusten täydellisyys on avoin eikä GST-käsittelyä
ole vahvistettu. Uusi-Seelanti läpäisee nyt 7/10 ehtoa mutta ei ole hyväksytty
luovuttajamarkkina; hyväksyttyjen luovuttajien määrä pysyy 0/3:ssa.
