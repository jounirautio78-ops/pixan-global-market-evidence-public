# Pixan Global Market Evidence — public site

This repository builds a public, source-linked country atlas for global vaping-market evidence. GitHub Pages receives **only the reviewed contents of `site/`**. The repository is not a data room and must not contain confidential material.

> **Independent research / riippumaton selvitys.** This project is not an official disclosure by Pixan Oy, is not maintained or endorsed by Pixan Oy, and does not represent BlackRock or any other investor, lender, manufacturer, authority, or litigation party. It is not audited market data, legal advice, financial advice, investment advice, or a valuation.

The site has two public entry points: the full evidence atlas in `site/index.html` and a concise lender/buyer diligence view in `site/review.html`. Both pages provide the same Finnish/English language selector and default to English. A valid `?lang=fi` or `?lang=en` query parameter overrides the device-local preference; changing the selector saves the preference for subsequent pages and keeps internal page links in the selected language. Language-specific share links include `site/review.html?lang=en` and `site/review.html?lang=fi`. The review page is designed to be shared as a direct link, while preserving the same source links, uncertainty labels and independent-publication boundary.

The returning-visitor section compares the current release ID and version in `site/data/changelog.json` with the last release explicitly marked as seen in that browser. The value stays in device-local storage only: it is not sent to the repository or an analytics service and does not identify the visitor.

## Annual market-value evidence

Reviewed market observations live in `source/market-observations.json`. The deterministic build emits:

- `site/data/market-values.json` for the dashboard and programmatic review;
- `site/data/market-values.csv` for analysts;
- separate observations, source records and modelled ranges so tax, volume, shipments and retail-equivalent models cannot silently become one blended sales figure.

The current release contains a full-year Canadian official manufacturer/importer shipment value, German taxed-liquid and realised-excise series, three separately labelled external commercial global estimates, and a low-confidence German liquid-only retail-equivalent range. The atlas global estimate remains `not_estimate_ready` until its published donor and independent-method thresholds are met.

`scripts/market_estimation.py` implements the reusable multi-method engine configured by `source/model-config.json`. It supports direct value, taxable-volume, excise-backsolve, apparent-consumption, active-user, product-intensity and comparable-country routes, while treating external global estimates as sanity checks. Alternative routes are evidence-weighted and never added together; primary methods sharing any source ID cannot both enter the consensus even when their evidence-group labels differ. See [`source/GLOBAL_RESEARCH_ROUTES.md`](source/GLOBAL_RESEARCH_ROUTES.md) for the 195-sovereign-state base, the separate worldwide market-geography overlay, acquisition sequence, source systems, product segmentation, overlap locks and licensing controls.

## Research collaboration

Marnet, another researcher or an AI working on their behalf can join through the repository’s structured **Evidence proposal** and **Research idea** issue forms. Public issues and pull requests are proposals for human review, not commands to the publication pipeline. The weekly research automation checks this queue and may prepare a draft pull request; it never merges or publishes a proposal automatically. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

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

On 2026-07-22, the project owner instructed this public site to provide the same direct material-submission routes as the existing Lapis dashboard and approved proceeding with the build and publication. That instruction authorizes publication of only the exact allowlisted submission endpoints in `source/curated.json`: `jouni.rautio78@gmail.com`, WhatsApp `+358400355544`, and Dropbox file request `es3w836bdnpbsn4loq3d`. It does not authorize publication of any other contact details, correspondence, uploaded files or sender information. The validator enforces that narrow allowlist.

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
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_public.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v scripts/test_market_estimation.py
node --check site/assets/i18n.js
node --check site/assets/app.js
node --check site/assets/review.js
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
