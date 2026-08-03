#!/usr/bin/env python3
"""Validate the committed privacy-safe Japan 2022–2025 customs series."""

from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "source" / "JAPAN_2022_2025_OFFICIAL_CUSTOMS_SERIES_CONTROL.json"
OUTPUT = ROOT / "source" / "JAPAN_2022_2025_OFFICIAL_CUSTOMS_SERIES.json"
MEMO = ROOT / "source" / "JAPAN_2022_2025_OFFICIAL_CUSTOMS_SERIES.md"
YEARS = (2022, 2023, 2024, 2025)
CODES = ("240412000", "240419100", "240419200", "854340000")
EXPECTED_DEVICE = {
    2022: (70_257_202_000, 19_099_172, Decimal("509009121.12")),
    2023: (70_496_284_000, 18_058_688, Decimal("463821018.99")),
    2024: (74_526_020_000, 17_657_457, Decimal("454837652.81")),
    2025: (84_361_341_000, 20_529_032, Decimal("499051223.28")),
}


def main() -> int:
    errors: list[str] = []
    control_bytes = CONTROL.read_bytes()
    control = json.loads(control_bytes)
    output = json.loads(OUTPUT.read_text(encoding="utf-8"))
    memo = MEMO.read_text(encoding="utf-8")

    if output.get("sourceIntegrity", {}).get("controlSha256") != hashlib.sha256(
        control_bytes
    ).hexdigest():
        errors.append("output control hash differs")
    observations = output.get("observations")
    if not isinstance(observations, list) or len(observations) != 16:
        errors.append("exactly 16 observations are required")
        observations = []
    index = {
        (item.get("year"), item.get("classificationCode")): item
        for item in observations
        if isinstance(item, dict)
    }
    if set(index) != {(year, code) for year in YEARS for code in CODES}:
        errors.append("year-code coverage differs from the exact 4x4 matrix")

    for item in observations:
        if (
            item.get("transactionStage") != "customs_import_declaration"
            or item.get("flow") != "imports_cif"
            or item.get("retailSalesEligible") is not False
            or item.get("globalRollupEligible") is not False
        ):
            errors.append(f"{item.get('observationId')}: fail-closed boundary differs")
        amount = Decimal(str(item.get("amountJpy")))
        rate = Decimal(str(item.get("ecbCurrencyUnitsPerEur")))
        expected_eur = (amount / rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if Decimal(str(item.get("eurEquivalent"))) != expected_eur:
            errors.append(f"{item.get('observationId')}: EUR conversion differs")

    for year, (value, quantity, eur) in EXPECTED_DEVICE.items():
        item = index.get((year, "854340000"), {})
        if (
            item.get("amountJpy") != value
            or item.get("quantity2") != quantity
            or item.get("quantity2Unit") != "NO"
            or Decimal(str(item.get("eurEquivalent"))) != eur
            or item.get("classificationDecision") != "included_as_device_customs_proxy"
        ):
            errors.append(f"{year}: device proxy vector differs")

    for year in YEARS:
        for code in ("240419100", "240419200"):
            if index.get((year, code), {}).get("classificationDecision") != (
                "excluded_until_scope_review"
            ):
                errors.append(f"{year} {code}: broad code must remain excluded")

    if (
        output.get("retailMarketValueComputed") is not False
        or output.get("globalRollupChanged") is not False
    ):
        errors.append("output must not compute retail or change global roll-up")
    for token in (
        "customs-import device proxy",
        "not consumer",
        "JPY is the primary",
        "Do not claim",
    ):
        if token.casefold() not in memo.casefold():
            errors.append(f"memo is missing boundary token: {token}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Japan 2022–2025 customs series validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
