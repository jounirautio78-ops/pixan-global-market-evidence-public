# Source provenance

This file records the origin and extraction boundary of public inputs used by the project. An upstream change is never accepted automatically; every new baseline requires human evidence, rights, and public-disclosure review.

## Full Marnet upstream snapshot — identification only

The full file was used to create the first allowlisted derivative but is **not stored in this repository**.

| Field | Recorded value |
| --- | --- |
| Upstream repository | [`marnet-collab/pixan-evidence-center`](https://github.com/marnet-collab/pixan-evidence-center) |
| Upstream path | [`data/dashboard.json`](https://github.com/marnet-collab/pixan-evidence-center/blob/main/data/dashboard.json) |
| Immutable upstream commit | [`7ab0c99c7146cac76ce01fa1e1f0a70d43092e1f`](https://github.com/marnet-collab/pixan-evidence-center/commit/7ab0c99c7146cac76ce01fa1e1f0a70d43092e1f) |
| Immutable raw URL | [`data/dashboard.json@7ab0c99c…`](https://raw.githubusercontent.com/marnet-collab/pixan-evidence-center/7ab0c99c7146cac76ce01fa1e1f0a70d43092e1f/data/dashboard.json) |
| Git blob | `a79644437a9e5ed37d1468560d5522253d05de93` |
| Snapshot metadata timestamp | `2026-07-17 16:34 UTC` |
| Byte-for-byte verification | `2026-07-22T08:24:04Z` |
| Full upstream size | `553324` bytes |
| Full upstream SHA-256 | `a394ffd3dbebdf44deb20c204a14ce2621feff4760739dd0eef6739aeff62241` |
| Machine-readable record | `source/marnet-upstream.metadata.json` and `source/marnet-upstream.sha256` |

At the recorded verification time, the fetched full file was valid JSON and matched the immutable upstream file byte for byte. It was then removed from the public project. The immutable URL and hash make that exact input independently retrievable without placing the raw file or its contact records in repository history.

## Public allowlisted derivative

| Field | Recorded value |
| --- | --- |
| Local file | `source/marnet-public-baseline.json` |
| Schema | `schemaVersion: 1` |
| Country rows | `23` |
| Country fields | `sourceName`, `sourceUrls` |
| Evidence rows | `37`, exactly matching `source/curated.json` → `marnetEvidenceWhitelist` |
| Evidence fields | `title`, `url`, `grade` |
| Public baseline size | `14242` bytes |
| Public baseline SHA-256 | `30e9f9de4f4856004fd0c337c2b3b41b474907f39a9d8dd41a14b83c38a38e7f` |

No upstream contact rows, email addresses, phone numbers, local paths, operational instructions, country narratives, evidence coverage narratives, or evidence-use narratives are retained. The builder creates `current`, `missing`, `coverage`, and `use` from local standardized rules and the curated claim type. The validator enforces exact key sets, country and evidence allowlists, HTTPS URLs, public-baseline hash and size, full-upstream metadata/sidecar consistency, and absence of the former raw path.

Two public country links were corrected during human review rather than copied verbatim:

- Belgium: the unofficial OpenJustice mirror was replaced by the official Belgian Official Gazette / eJustice record for `2023048600`.
- France: the mismatched Legifrance link was replaced by official reporting article `LEGIARTI000032549341`.

Consequently, the public derivative hash proves the reviewed derivative, while the separate full-upstream hash proves the identity of the input. They are intentionally different records.

## Sweden FHM official-response aggregate

`source/market-observations.json` contains 36 official Swedish registration-structure observations for 2018–2026: reporting entities, notified products, active products and withdrawn products. The Public Health Agency of Sweden supplied the aggregate table in an official public-record response received on 24 July 2026.

The contextual public source is FHM's canonical guidance page for [electronic cigarettes and refill containers](https://www.folkhalsomyndigheten.se/regler-och-tillsyn/tobak-och-nikotinprodukter-regler-for-tillverkning-handel-och-hantering/elektroniska-cigaretter-och-pafyllningsbehallare-sa-foljer-du-reglerna/). The exact historical aggregate was supplied in an authority workbook and is not reproduced by the current public product list. The workbook and correspondence remain outside this public repository; no sender, recipient, message identifier or other correspondence metadata is published.

The reviewed table and field mapping are documented in `source/SWEDEN_FHM_REGISTRATION_STRUCTURE_2018_2026.md`. For every year, notified products equal active plus withdrawn products. The 2018–2025 years are authority-supplied labels, not assumed calendar-year flows or year-end snapshots. The 2026 values are explicitly a current snapshot as of 24 July 2026, not a completed annual total.

These records are structural counts only. They are not annual sales, sold device units, sold liquid volume, market value, market share or donor evidence. They have no currency and are ineligible for both EUR conversion and the donor count.

## Open official-data base layer

`source/global-base-config.json` defines a reviewed five-measure snapshot for the 195-country `UN193+VA+PS` universe. `source/global-base-observations.json` contains 975 country-measure records and preserves the selected source year for every observed value.

The active World Bank World Development Indicators routes produce 578 observed values: total population for 194 countries, population ages 15–64 for 194 countries and GDP per capita in current U.S. dollars for 190 countries. The remaining World Bank records are explicitly missing. The adult e-cigarette-prevalence route to the WHO Global Health Observatory and the vaping-related trade route to UN Comtrade are route-only in v27: all 390 country-route records are missing and queued, not reported as zero. Across all measures, 397 records are missing.

Every base-layer record has `retailSalesEligible: false`. Population, working-age population and GDP are contextual signals, while eventual prevalence and trade values would be proxies. None is national annual consumer-retail vaping sales, none enters the donor count and none can be summed into a global market value. The retail-eligible observation count is zero and the global value is `null`.

- World Bank data portal: <https://data.worldbank.org/>
- World Bank API documentation: <https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures>
- WHO Global Health Observatory: <https://www.who.int/data/gho>
- UN Comtrade: <https://comtradeplus.un.org/>
- Reviewed configuration: `source/global-base-config.json`
- Reviewed observations: `source/global-base-observations.json`
- Public schema: `source/schemas/global-base-layer.schema.json`

## Poland official flow and excise bridge

`source/market-observations.json` contains four official Polish e-liquid-volume observations for 2020–2023 from the Ministry of Finance response to parliamentary interpellation 7255. The reported ZEFIR2/AIS table covers domestic sales, intra-EU acquisitions and imports: 1,451,529 litres in 2020, 277,265 litres in 2021, 416,088 litres in 2022 and 805,441 litres in 2023.

The Ministry response to interpellation 17526 provides realised 2025 excise receipts for e-liquid, vaping devices and component sets. The official PLN 40 per-device and PLN 40 per-set rates in force from 1 July 2025 support a deterministic bridge to 4,382,500 implied taxed devices and 62,500 implied taxed component sets. No e-liquid quantity is back-solved because the 2025 rate changed during the year and disposables acquired an additional charge.

The litres are physical supply or release flows and the implied units are tax-base bridges. They are not full-year consumer sell-through or observed retail value, do not make Poland an accepted donor and do not change the 0/3 donor gate.

- [Interpellation 7255 response — 2020–2023 national volumes](https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTDDEJZ5/i07255-o1.pdf)
- [Interpellation 17526 response — realised 2025 excise](https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTDVKHSJ/i17526-o1.pdf)
- [Polish Ministry of Finance — excise rates](https://www.podatki.gov.pl/akcyza/stawki-podatkowe/)
- Reviewed method and limits: `source/POLAND_2020_2025_RECONSTRUCTION.md`

## ECB annual-average EUR equivalents

`source/fx-rates.json` is a separate, public-only conversion layer sourced from the European Central Bank’s official `EXR` dataset. It contains 23 annual-average spot-reference observations for the exact CAD, NZD, PLN, SEK and USD currency-year pairs used by the current annual monetary records and the 2022–2024 World Bank GDP-per-capita base layer. Every rate links to a year-bounded ECB Data API CSV query and records the review date `2026-07-27`.

The ECB series key format is `EXR.A.<currency>.EUR.SP00.A`, and the quote is foreign-currency units per euro. The reproducible calculation is therefore `EUR equivalent = original monetary amount / currency units per EUR`. The source amount and source currency remain primary. Full published API `OBS_VALUE` precision is retained for the calculation; rounding occurs only when the browser displays the secondary EUR equivalent.

The eligibility rule is deliberately narrow: the record must be a positive annual monetary total and its unit must equal its currency. Physical litres, product counts, tax rates and per-unit prices are not converted. If the annual period, official rate or FX dataset cannot be verified, the EUR result is `not_computed`; no commercial, unofficial or current spot substitute is used.

- ECB EXR dataset metadata: <https://data.ecb.europa.eu/data/datasets/exr/data-information>
- ECB reference-rate method and quote convention: <https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html>
- Machine-readable reviewed layer: `source/fx-rates.json`
- Public schema: `source/schemas/fx-rates.schema.json`

## Attribution, licence, and limits

Marnet is credited for the upstream evidence-center source inventory. This project does not claim authorship of Marnet’s underlying work, and Marnet’s attribution does not imply approval of this project or its later transformations.

No repository licence authorizing general redistribution of the upstream work was identified during this review. The full snapshot is therefore not redistributed here. Retaining factual identifiers, short titles, grades, and official source links is a risk-minimizing review decision, not a legal conclusion or a substitute for a rights assessment.

The allowlisted derivative is an input to an independent review pipeline. Its presence does not by itself verify every market figure, source interpretation, legal conclusion, patent status, or commercial claim. Curated public output must preserve uncertainty and distinguish official statistics, derived calculations, modeled estimates, and unverified leads.

## Required record for a future baseline

When a human reviewer accepts a new snapshot, update in the same pull request:

- upstream repository, path, immutable commit, blob identifier, retrieval/verification time, byte size, and SHA-256;
- `source/marnet-upstream.metadata.json` and its exact `.sha256` sidecar;
- only the minimal allowlisted public derivative, never the full upstream file;
- the derivative schema, row counts, byte size, and SHA-256;
- all reviewed substitutions, removals, and substantive changes;
- the reviewer’s evidence, licence/rights, personal-data, and publication decision;
- the deterministic generated `site/` diff and validation result.

The weekly source monitor may report a different hash in an issue, but it has no permission or mechanism to replace either baseline.
