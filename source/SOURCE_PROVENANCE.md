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

## ECB annual-average EUR equivalents

`source/fx-rates.json` is a separate, public-only conversion layer sourced from the European Central Bank’s official `EXR` dataset. It contains 20 annual-average spot-reference observations for the exact CAD, NZD, PLN, SEK and USD currency-year pairs used by the current annual monetary records. Every rate links to a year-bounded ECB Data API CSV query and records the review date `2026-07-24`.

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
