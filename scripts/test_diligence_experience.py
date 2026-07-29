#!/usr/bin/env python3
"""Regression checks for the public diligence-access experience."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "site" / "index.html"
REVIEW_PATH = ROOT / "site" / "review.html"
DILIGENCE_PATH = ROOT / "site" / "diligence.html"
I18N_PATH = ROOT / "site" / "assets" / "i18n.js"
STYLES_PATH = ROOT / "site" / "assets" / "styles.css"


def main() -> int:
    errors: list[str] = []
    index = INDEX_PATH.read_text(encoding="utf-8")
    review = REVIEW_PATH.read_text(encoding="utf-8")
    diligence = DILIGENCE_PATH.read_text(encoding="utf-8")
    i18n = I18N_PATH.read_text(encoding="utf-8")
    styles = STYLES_PATH.read_text(encoding="utf-8")

    for path, content in ((INDEX_PATH, index), (REVIEW_PATH, review)):
        if 'href="diligence.html"' not in content:
            errors.append(f"{path.name}: missing diligence access link")
    for token in (
        "2026-07-29-35",
        'data-copy-en="Show every material fact—without giving away protected strategy."',
        'data-copy-fi="Näytä jokainen olennainen fakta — luovuttamatta suojattua strategiaa."',
        'href="data/investor-disclosure-control.json"',
        'href="schemas/investor-disclosure-control.schema.json"',
        "This page documents a process. It is not an NDA, access grant, offer, valuation or legal opinion.",
    ):
        if token not in diligence:
            errors.append(f"diligence.html: missing {token}")
    for token in (
        '["Due diligence -pääsy", "Diligence Access"]',
        'const UI_RELEASE_V35',
        'window.PixanUiRelease = UI_RELEASE_V35',
    ):
        if token not in i18n:
            errors.append(f"i18n.js: missing {token}")
    for selector in (
        ".diligence-hero",
        ".diligence-tier-grid",
        ".diligence-tier-card",
        ".diligence-audience-grid",
        ".diligence-reuse-grid",
        ".diligence-request-panel",
    ):
        if selector not in styles:
            errors.append(f"styles.css: missing {selector}")

    if errors:
        print(f"FAIL: {len(errors)} diligence-experience error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("OK: diligence access is linked, bilingual, versioned and visually supported.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
