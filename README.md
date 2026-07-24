# Pixan Global Market Evidence — public site

This repository builds a public, source-linked country atlas for global vaping-market evidence. GitHub Pages receives **only the reviewed contents of `site/`**. The repository is not a data room and must not contain confidential material.

> **Independent research / riippumaton selvitys.** This project is not an official disclosure by Pixan Oy, is not maintained or endorsed by Pixan Oy, and does not represent any investor, lender, manufacturer, authority, or litigation party. It is not audited market data, legal advice, financial advice, investment advice, or a valuation.

The site has three shareable public views: the five-minute decision review at `site/review.html?view=review`, the full Evidence Center in `site/index.html`, and Research Operations at `site/review.html?view=operations`. The review and operations modes are normal query-addressable links on one validated page, so public procurement, vendor-response and authority-request controls remain isolated from the external decision narrative without creating a separate publication pipeline. Every page defaults to English and provides the same Finnish/English selector. A valid `?lang=fi` or `?lang=en` query parameter overrides the device-local preference; changing the selector saves the preference for subsequent pages and preserves both the selected language and review mode in internal links.

The five-minute review opens with a fail-closed Decision Cockpit derived from the reviewed atlas, market, patent and request-programme JSON. It keeps supported facts, unsupported conclusions and the three current readiness blockers separate, and remains **HOLD — research dataset, not a valuation** while `readiness.lenderReady` is false. The same view exposes a reproducible Germany calculation waterfall, a deterministic 20-source market ledger and a five-candidate donor acceptance ledger. The Evidence Center adds three explicit publication lanes, the same source-linked D1–D10 donor cockpit and a country-year scenario lab. Missing or invalid scenario inputs return `not_computed`, never zero, and no public global total is calculated until at least three donors plus regional and regulatory-archetype coverage pass. The waterfall must reconcile the committed formula and all three outputs before displaying them. The freshness ledger keeps retrieval date and latest observation year separate, never treats a download date as proof of substantive currency, and labels the atlas's item-level source dates as undated where they are not recorded.

The returning-visitor section compares the current release ID and version in `site/data/changelog.json` with the last release explicitly marked as seen in that browser. The value stays in device-local storage only: it is not sent to the repository or an analytics service and does not identify the visitor.

The changelog's top-level `asOf` is the reviewed evidence date shared with the atlas, market and patent datasets. A release's `publishedAt` is the later publication timestamp for site or presentation changes and may therefore be later than `asOf`; the two dates must not be presented as the same concept.

## Public bankability gates

The shareable review page includes a public-safe [bankability section](site/review.html#bankability) with three analytical transaction paths: share-backed financing, IP-backed corporate financing, and strategic sale or licensing. Every path is visibly marked **HOLD**. The cards describe only the evidence gates that a controlled private professional review would need to close; they do not report private diligence outcomes, active negotiations, financing availability, buyer or lender interest, transaction authority, terms, value, or a recommendation.

The same section builds a Top 10 market/right matrix in the browser from the already reviewed `site/data/atlas.json`, `site/data/patent-history.json` and `site/data/top20-data-request-routes.json`. It keeps evidence-readiness grades, official market-measure routes, request status, family publications, current national status, product claim charts and enforcement evidence in separate fields. A family publication is never presented as current national status, a missing family row is not evidence that no right exists, and German court records retain their product, territory, procedure and finality limits. The matrix cannot send or approve a data request.

## Downloadable bank-research package

The full atlas and lender/buyer review page expose eight release-locked downloads: English and Finnish versions of a 6-slide brief, the requested 12-slide lender deck, an extended 30-slide diligence deck and a 53-row Evidence Register workbook. `scripts/artifact-build/build_bank_package_artifacts.mjs` authors both languages in the controlled `@oai/artifact-tool` runtime, adds a non-empty `[Sources]` speaker-note block to every slide, renders every slide and workbook sheet, and writes the reviewed release lock and manifest. The six presentation templates and two workbook source-sheet seeds are immutable v17 inputs under `scripts/artifact-build/seeds/v17/`; the builder never treats the current public downloads as its hidden seed. Their SHA-256 digests are recorded separately as `templateInputs` and also included in the reviewed input lineage. No private workspace file is an input. `site/data/bank-package-manifest.json` records the release, source date, language, exact reviewed-input and artifact SHA-256 digests, file sizes and slide or row counts. CI does not silently regenerate stale presentations: it fails closed if any reviewed input, seed, download or lock differs. Before displaying a download link, the browser fetches the file and verifies both its exact byte length and full SHA-256 digest against that manifest.

The generated package is deliberately evidence-conservative. It distinguishes **Vahvistettu**, **Tuettu**, **Oletus** and **Puuttuu**, and treats unverified financials, customers, licensing cash flow, title/encumbrance records and financing terms as missing evidence. Both language versions share one canonical release context; `scripts/bank_register_parity.py` requires the English and Finnish registers to preserve dates, sources, confidence classes, identifiers, currencies, units and numerically equivalent values. It is independent research, not an official Pixan disclosure, a valuation, investment advice or a recommendation to lend.

## ECB EUR-equivalent layer

The public site retains every source monetary value in its original currency and shows an EUR equivalent only as a secondary comparison. `source/fx-rates.json` contains 14 reviewed ECB EXR annual-average observations for the exact currency-year pairs used by the current CAD, NZD, PLN, SEK and USD records. The ECB quotes each rate as foreign-currency units per euro, so the deterministic formula is `EUR equivalent = original amount / currency units per EUR`. The full published `OBS_VALUE` is used for calculation and only the displayed result is rounded.

Only positive monetary totals whose unit equals their currency are eligible. Physical volumes, unit counts, tax rates and unit prices are never converted as market values. A missing rate, incompatible period or invalid FX dataset produces a visible `not_computed` state; no unofficial or current spot rate is substituted. `scripts/validate_fx_rates.py` verifies ECB-only URLs, exact rates, source/public parity, current observation and scenario coverage, and UI controls. `scripts/test_fx_rates.py` mutation-tests the fail-closed boundary.

To rebuild from a clean clone after the atlas has been rebuilt, first obtain the bundled Node executable and `node_modules` directory from `codex_app.load_workspace_dependencies`. Set the two task-specific variables below to those returned absolute paths and expose that read-only bundled module directory through the repository-local ignored symlink. The builder reads the active `@oai/artifact-tool` package version dynamically and records it in the release lock; no version is hard-coded.

```bash
PIXAN_NODE=/absolute/path/returned/by/load_workspace_dependencies/node
PIXAN_NODE_MODULES=/absolute/path/returned/by/load_workspace_dependencies/node_modules
test -e node_modules || ln -s "$PIXAN_NODE_MODULES" node_modules
python -m pip install -r requirements-bank-package.txt
python scripts/build_atlas.py
"$PIXAN_NODE" scripts/artifact-build/build_bank_package_artifacts.mjs
python scripts/validate_bank_package.py
```

## Official-data request programme

The shareable review page exposes a reusable six-layer evidence stack for the 195-sovereign-state research base: statutory sales or product reporting, excise and domestic release, customs and net imports, retail or manufacturer/importer evidence, price and channel bridges, and separately labelled enforcement or seizure signals. Reconciliation and confidence controls sit above the layers; they are never mechanically added and missing evidence never becomes zero.

Within that global architecture, the page retains a verified 20-country planned-route queue for existing aggregate records. The ranking is an operational evidence-acquisition order, not a ranking of market size. Its privacy-safe public ledger marks exactly 12 country routes `sent` and 8 `draft_not_sent`: Australia, Canada, Denmark, Finland, France, Germany, Italy, the Netherlands, Poland, Sweden, the United Kingdom and the United States are the recorded sent routes. A supplementary German BVL annual-sales route was sent on 2026-07-24 under section 25 of the Tobacco Products Ordinance; it is part of Germany and does not change the 12/8 country count. The German Customs request is recorded as formally registered and under processing, but no substantive authority data has been received. A sent marker or process state does not establish a market value. The repository itself does not send requests, and the downloadable templates remain visibly `DRAFT — NOT SENT`.

`source/top20-data-request-routes.json` records each planned official request channel, legal basis, language, requester-eligibility caveat, fallback, verification date, exact schema-v3 dispatch object, the six-layer stack and the non-counting German supplement. `scripts/build_data_request_program.py` creates the public JSON, privacy-safe tracking CSV and neutral English/Finnish request templates. `scripts/validate_data_request_program.py` enforces exactly 20 unique countries, the reviewed 12-country sent set, approved dates and public references, the 195-state method boundary, the German BVL route, official HTTPS host allowlists, rejection of private correspondence metadata and deterministic output.

```bash
python scripts/build_data_request_program.py
python scripts/validate_data_request_program.py
```

## Paid-data procurement shortlist

The review page includes a bilingual, prioritised shortlist of commercial data that could close identified evidence gaps. It is a procurement decision aid, not market data, a purchase recommendation, a vendor endorsement or evidence of Pixan Oy approval. No spend is authorised.

The recommended sequence is to request samples and transaction-use quotes from ECigIntelligence and Euromonitor in parallel, buy at most one global master unless material non-overlap is demonstrated, and then use a tightly scoped NIQ/Circana POS pilot to validate selected countries. Public list prices are dated page observations; `Quote` means no reliable project price was identified. Every option remains subject to the sample, methodology, official-anchor reconciliation and written lender/M&A data-room licence gates in the downloadable workbook.

The same table now exposes a privacy-safe outreach record for four shortlisted products. It records only the vendor item, a controlled state, the calendar date and a bilingual boundary note. Sender identities, addresses, form identifiers, exact timestamps, correspondence and vendor-supplied files remain private. `sent` or `submission confirmed` means only that the request action was recorded; it does not establish a substantive response, data quality, a usable licence or a market figure.

`source/paid-data-procurement.json` is the canonical public decision and outreach record. `scripts/build_paid_data_procurement.py` regenerates the public JSON and CSV. The reviewed bilingual XLSX remains the procurement-decision workbook; the live outreach ledger is published in the JSON/CSV and dashboard. `scripts/validate_paid_data_procurement.py` checks scoring formulas, no-purchase boundaries, privacy-safe outreach states, safe HTTPS sources and OOXML safety before publication.

```bash
python scripts/build_paid_data_procurement.py
python scripts/validate_paid_data_procurement.py
```

### Vendor-response control

The review page also contains a privacy-safe response-control view for the four recorded commercial routes. It keeps outreach status, received evidence, mandatory gates and scoring readiness separate. The current checkpoint contains four tracked routes, one vendor route with substantive written responses, zero vendor samples scored and zero purchase authorisations. Euromonitor's responses and brochure establish a preliminary product-fit signal only. The brochure's 100-country list is the overall Passport Tobacco scope, not verified product-by-country e-vapour coverage, and the vendor's statement that granularity has expanded is not numerical evidence. Euromonitor says it can provide samples, detailed answers and pricing after the role/access model is clarified. That clarification is pending and has not been sent. The Germany numerical sample, itemised price, detailed method, coverage matrix, licence and written rights for derived client outputs remain pending.

`source/vendor-response-control.json` is the canonical public control record. `scripts/build_vendor_response_control.py` deterministically emits the public JSON and CSV, and `scripts/validate_vendor_response_control.py` enforces the exact current states, seven criteria whose weights total 100%, six mandatory evidence gates and the privacy boundary. Missing evidence is always `not_scored`, never a numeric zero. Correspondence, personal data, private identifiers, licensed vendor files and confidential commercial terms remain outside the repository.

The bilingual procurement workbook now includes a response scorecard, a flat evidence-intake template and visible integrity checks. Its score remains blank until all mandatory gates pass and all seven 0–5 inputs are present. It grants no purchase, subscription, NDA, auto-renewal or other commercial authority.

```bash
python scripts/build_vendor_response_control.py
python scripts/validate_vendor_response_control.py
```

## Annual market-value evidence

Reviewed market observations live in `source/market-observations.json`. The deterministic build emits:

- `site/data/market-values.json` for the dashboard and programmatic review;
- `site/data/market-values.csv` for analysts;
- separate observations, source records and modelled ranges so tax, volume, shipments and retail-equivalent models cannot silently become one blended sales figure.

The current release contains a full-year Canadian official manufacturer/importer shipment value, German taxed-liquid and realised-excise series, official New Zealand annual-return headline observations for 2022–2024, a 29-workbook New Zealand 2024 reconciliation, a transparent 2024 New Zealand retail-vaping sensitivity, a European Commission-published 2023 EU market benchmark, an official-table-derived U.S. FTC reported-sales route for 2015–2021, three separately labelled external commercial global estimates, and a low-confidence German liquid-only retail-equivalent range. The New Zealand raw specialist-workbook sum is NZD 280,684,512.81 and the conservatively identified-vaping subset is NZD 274,180,410.21. The separate retail sensitivity is NZD 533,662,383.68 / 641,811,687.89 / 731,175,792.50, combining that specialist anchor with a general-retailer quantity-and-price model and excluding notifier supply-stage values. It remains a supported model because GST, coverage and independent reconciliation are unresolved. The six official 2023 New Zealand workbooks and their hashes are logged, but every new 2023 reconstruction remains `not_computed` until product-scope, quantity-field, duplication, supply-stage, tax and independent-reconciliation checks are complete. The U.S. series ends at USD 2,763,284,338 in 2021 and remains outside the donor count because it is leading-manufacturer reporting, the reporting population changes after 2019, open-system products are excluded and the tax basis is unstated. The EU value remains an institutionally supported benchmark because it originates in Euromonitor/external-study data, the reusable country dataset and full method are not public, and the supporting annex notes unavailable information for three Member States. See [`source/NZ_2023_ANNUAL_RETURNS_FAIL_CLOSED.md`](source/NZ_2023_ANNUAL_RETURNS_FAIL_CLOSED.md), [`source/NZ_2024_ANNUAL_RETURNS_RECONCILIATION.md`](source/NZ_2024_ANNUAL_RETURNS_RECONCILIATION.md), [`source/NZ_2024_RPS_RETAIL_VALUE_SENSITIVITY.md`](source/NZ_2024_RPS_RETAIL_VALUE_SENSITIVITY.md), [`source/US_FTC_2015_2021_REPORTED_SALES.md`](source/US_FTC_2015_2021_REPORTED_SALES.md) and [`source/EU_2023_E_CIGARETTE_BENCHMARK_RECONCILIATION.md`](source/EU_2023_E_CIGARETTE_BENCHMARK_RECONCILIATION.md). [`source/DONOR_ACCEPTANCE_PROTOCOL.md`](source/DONOR_ACCEPTANCE_PROTOCOL.md) defines the ten pass/fail/open tests now applied to New Zealand, the EU, Canada, Germany and the United States. The atlas global estimate remains `not_estimate_ready` at 0/3 accepted donors.

`scripts/market_estimation.py` implements the reusable multi-method engine configured by `source/model-config.json`. It supports direct value, taxable-volume, excise-backsolve, apparent-consumption, active-user, product-intensity and comparable-country routes, while treating external global estimates as sanity checks. Alternative routes are evidence-weighted and never added together; primary methods sharing any source ID cannot both enter the consensus even when their evidence-group labels differ. See [`source/GLOBAL_RESEARCH_ROUTES.md`](source/GLOBAL_RESEARCH_ROUTES.md) for the 195-sovereign-state base, the separate worldwide market-geography overlay, acquisition sequence, source systems, product segmentation, overlap locks and licensing controls.

## Research collaboration

Marnet, another researcher or an AI working on their behalf can join through the repository’s structured **Evidence proposal** and **Research idea** issue forms or, where explicitly granted, through a branch with repository write access. Every contribution remains a proposal for human review: the protected `main` branch requires a pull request and the mandatory quality check, and the weekly research automation never merges or publishes a proposal automatically. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Relationship to Marnet’s work

The initial source inventory is attributed to Marnet’s [`marnet-collab/pixan-evidence-center`](https://github.com/marnet-collab/pixan-evidence-center) and its [public evidence center](https://marnet-collab.github.io/pixan-evidence-center/). This is a separate review and publication pipeline, not an automatic mirror, and attribution does not imply endorsement.

The full Marnet dashboard snapshot is **not stored in this repository**. [`source/marnet-public-baseline.json`](source/marnet-public-baseline.json) retains only 23 country identifiers with reviewed public source URLs and 37 allowlisted evidence identifiers, URLs, and source grades. Narrative country and evidence text is generated from local curated rules rather than copied from upstream. The full upstream file is identified without redistribution by its immutable commit, Git blob, byte size, and SHA-256 in [`source/marnet-upstream.metadata.json`](source/marnet-upstream.metadata.json) and [`source/marnet-upstream.sha256`](source/marnet-upstream.sha256). See [`source/SOURCE_PROVENANCE.md`](source/SOURCE_PROVENANCE.md) for the extraction boundary and reviewed source-link corrections.

No upstream repository licence authorizing general redistribution was identified during this review. The minimal baseline and source links reduce copying but do not themselves create a licence or settle third-party rights. Every future update still requires a human rights and publication review.

## Public/private boundary

Everything committed to this repository must be suitable for immediate public disclosure. A `.gitignore` rule is only an accident guard, not an access-control mechanism.

Allowed public material:

- curated public-source facts with a source URL, retrieval date, period, geography, unit, methodology, and confidence classification;
- public authority publications and short, necessary factual identifiers that can lawfully be linked or redistributed;
- reviewed static HTML, CSS, JavaScript, charts, and machine-readable public extracts in `site/`;
- provenance and methodology documentation.

Never commit or publish:

- emails, chat exports, internal messages, contracts, loan or share negotiations, data-room files, or unpublished investor interest;
- personal data, contact lists, privileged legal material, credentials, tokens, cookies, or private URLs;
- third-party raw files without a verified right to redistribute them;
- unsupported claims presented as confirmed sales, damages, recoveries, negotiations, patent status, or market size.

Private inputs must stay in the separately controlled private workspace. Only a human-reviewed, publication-safe derivative may enter this repository.

### Public submission-contact decision

On 2026-07-22, the project owner instructed this public site to provide the previously approved direct material-submission routes and approved proceeding with the build and publication. That instruction authorizes publication of only the exact allowlisted submission endpoints in `source/curated.json`: `jouni.rautio78@gmail.com`, WhatsApp `+358400355544`, and Dropbox file request `es3w836bdnpbsn4loq3d`. It does not authorize publication of any other contact details, correspondence, uploaded files or sender information. The validator enforces that narrow allowlist.

## Automated workflows

| Workflow | Purpose | Write capability |
| --- | --- | --- |
| `quality.yml` | Runs `scripts/build_atlas.py` and `scripts/validate_public.py`, then requires a byte-for-byte clean deterministic rebuild. | None; `contents: read`. |
| `pages.yml` | Rebuilds and validates, then uploads only `site/` as the Pages artifact. | Only the deploy job has `pages: write` and OIDC permission. |
| `source-monitor.yml` | Weekly comparison of the current public upstream file against the recorded full-upstream hash and size. | May open or update one review issue; cannot write repository contents or deploy Pages. |

The source monitor resolves the current upstream commit and downloads its immutable commit URL only to temporary runner storage. It does **not** copy the snapshot into the repository, create commits, open pull requests, update the public baseline, run the site builder, or publish anything. A network, metadata, hash, size, or JSON-validation failure fails the monitor rather than accepting partial data.

## Human-controlled update process

1. The weekly monitor reports a changed upstream SHA-256 or byte size in an issue.
2. A reviewer fetches the immutable upstream commit outside the repository and compares content, sources, methodology, licence status, personal-data boundary, and public-disclosure rights.
3. If accepted, regenerate only the minimal allowlisted `source/marnet-public-baseline.json`. Do **not** copy or commit the full dashboard snapshot, contacts, narrative text, private paths, or non-allowlisted records.
4. Update `source/marnet-upstream.metadata.json`, `source/marnet-upstream.sha256`, `source/SOURCE_PROVENANCE.md`, and the curated `meta.legacySourceCommit` / `meta.reviewedAt` values in the same branch.
5. Run the builder and validator locally.
6. Review the complete generated `site/` diff, including links, labels, uncertainty language, personal data, and mobile rendering.
7. Open a pull request. Merge only after evidence, rights, and public-disclosure review passes.
8. The merge to `main` triggers a fresh deterministic build. Only the `site/` artifact is sent to GitHub Pages.
9. Verify the actual public URL and navigation after deployment; a green build alone is not publication verification.

The monitor does not automatically close its issue after a baseline update. A human reviewer closes it after confirming the accepted baseline and public result.

## Local quality check

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_atlas.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_data_request_program.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_paid_data_procurement.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_vendor_response_control.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_public.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_data_request_program.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_paid_data_procurement.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_vendor_response_control.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_donor_cockpit.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_fx_rates.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_bank_package.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v scripts/test_market_estimation.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_review_experience.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_review_experience.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_data_request_program.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_vendor_response_control.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_paid_data_procurement_privacy.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_donor_cockpit.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_fx_rates.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_public_privacy.py
node --check site/assets/i18n.js
node --check site/assets/app.js
node --check site/assets/review.js
node --check site/assets/downloads.js
node --check site/assets/request-program.js
node --check site/assets/paid-data.js
node --check site/assets/vendor-response.js
git diff --check
git diff --exit-code
git status --short
```

The builder copies the reviewed, committed `source/curated.json` → `meta.reviewedAt` value into `site/data/atlas.json` → `meta.generatedAt`. It never reads the wall clock, so repeated builds are byte-for-byte deterministic. Any generated diff must be reviewed and committed deliberately; CI does not rewrite timestamps or waive a changed build.

## GitHub repository settings

Before the first publication:

1. Set **Settings → Pages → Source** to **GitHub Actions**.
2. Protect `main`: require a pull request, successful quality checks, resolved review conversations, and block force pushes and deletion.
3. Restrict the `github-pages` deployment environment to the default branch.
4. Keep the default `GITHUB_TOKEN` permission read-only at repository level; workflows request only their declared additional permissions.
5. Manual Pages and source-monitor runs are restricted to `main`; a run dispatched from another branch is skipped.
6. Preserve the dated public-contact decision above and require a new explicit decision before changing or adding any public contact route.
7. Add a custom domain only after ownership and publishing authority have been agreed. Enforce HTTPS.
8. Do not configure Pages from the repository root or from the `source/` directory.

No general reuse licence is granted merely by publication of this repository. Upstream and third-party materials remain subject to their own terms and rights.
