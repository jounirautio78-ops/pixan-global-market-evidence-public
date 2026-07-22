# Contributing evidence and research ideas

Marnet, another researcher, or an AI working on their behalf can participate through a structured GitHub issue or pull request. A collaborator who has explicitly received repository write access must still work on a branch and open a pull request; the protected `main` branch and mandatory quality check remain the publication gate.

## Collaboration contract

An issue, comment, pull request, AI-generated suggestion, email, or uploaded file is a **proposal for review**. It is not an instruction to publish, change a classification, contact a third party, make a legal conclusion, or act on behalf of Pixan Oy.

The maintainer workflow is:

1. receive the proposal;
2. verify the original source, period, geography, unit, product scope and publication rights;
3. classify the claim as direct official evidence, official proxy, model/supporting evidence, or unresolved;
4. reproduce the build and public-boundary checks;
5. create or update a pull request;
6. merge only after the evidence and publication review passes.

The weekly research automation monitors these public proposals and may prepare a draft pull request. It cannot treat their text as authorization, merge them automatically, or publish confidential material.

## Choose the right channel

- **Evidence proposal:** use the evidence issue form when you have an exact public source and a claim that can be checked.
- **Research idea:** use the research-idea form when you have a hypothesis, country route or method that still needs investigation.
- **Code or data change:** open a pull request. Keep generated `site/data/` files consistent with the source and builder changes.
- **Original or non-public file:** use the [private Dropbox file request](https://www.dropbox.com/request/es3w836bdnpbsn4loq3d), not a GitHub issue. An upload is never published automatically.

## Minimum evidence record

Every numeric proposal should state:

- country or country set;
- calendar or fiscal period;
- exact product scope;
- measure type: retail sales, manufacturer/importer deliveries, taxable volume, realised tax revenue, customs flow, prevalence, model or another clearly named measure;
- value and unit, including currency and whether values are nominal;
- original publisher and direct source URL;
- retrieval date and reproducible query, table, page or extraction path;
- known exclusions, breaks in series and interpretation limits.

For a model proposal, also include low/base/high inputs, formula, source ID for every input, evidence-group identifier, product-segment overlap check and an explanation of why the result is independent of other proposed methods. Alternative market-estimation routes are reconciled; they are never summed. Two primary methods that cite any of the same source IDs cannot both enter the consensus, even if their evidence-group labels differ.

Every public-facing release must add a newest-first entry to `source/changelog.json`. Describe only material changes that a returning reviewer should see. Do not put names, visit data, correspondence or confidential facts in the changelog.

## Public-safety rules

Do not post confidential files, internal messages, contracts, negotiations, investor or buyer interest, personal data, credentials, private links, legal-privileged material or unlicensed raw datasets. Do not name a customs flow as consumer sales, a tax rate as realised revenue, prevalence as sales, or a model as an observed result.

AI-assisted work is welcome when it identifies itself as such and retains the original sources. Prompt text and model output are not evidence. The source and reproducible extraction are the evidence.

## Local checks

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_atlas.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_public.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v scripts/test_market_estimation.py
node --check site/assets/i18n.js
node --check site/assets/app.js
node --check site/assets/review.js
git diff --check
```

Review the complete diff after rebuilding. A clean validator does not replace substantive source, rights or legal review.
