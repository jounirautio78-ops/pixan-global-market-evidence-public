# Pixan Global Market Evidence — public site

This repository builds a public, source-linked country atlas for global vaping-market evidence. GitHub Pages receives **only the reviewed contents of `site/`**. The repository is not a data room and must not contain confidential material.

> **Independent research / riippumaton selvitys.** This project is not an official disclosure by Pixan Oy, is not maintained or endorsed by Pixan Oy, and does not represent BlackRock or any other investor, lender, manufacturer, authority, or litigation party. It is not audited market data, legal advice, financial advice, investment advice, or a valuation.

The site has two public entry points: the full Finnish evidence atlas in `site/index.html` and a concise English lender/buyer diligence view in `site/review.html`. The review page is designed to be shared as a direct link, while preserving the same source links, uncertainty labels and independent-publication boundary.

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
