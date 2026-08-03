#!/usr/bin/env python3
"""Validate the committed Spain AEAT 2025–2026 H1 excise series."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "source" / "SPAIN_AEAT_2025_2026_EXCISE_SERIES_CONTROL.json"
OUTPUT = ROOT / "source" / "SPAIN_AEAT_2025_2026_EXCISE_SERIES.json"
MEMO = ROOT / "source" / "SPAIN_AEAT_2025_2026_EXCISE_SERIES.md"
EXPECTED_2025 = {
    1: (None, None, None),
    2: (None, None, None),
    3: (None, None, None),
    4: (294, 0, 294),
    5: (2332, 0, 2332),
    6: (2518, 0, 2518),
    7: (5311, 0, 5311),
    8: (4296, 0, 4296),
    9: (4426, -357, 4069),
    10: (3930, -1016, 2914),
    11: (4508, -12, 4496),
    12: (4182, -844, 3338),
}
EXPECTED_2026_H1 = {
    1: (4352, -9, 4343),
    2: (3633, -232, 3401),
    3: (3563, -723, 2840),
    4: (5157, -2492, 2665),
    5: (4578, -107, 4471),
    6: (4443, -387, 4056),
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
    if (
        output.get("seriesId") != "ES_AEAT_ECIG_LIQUID_EXCISE_2025_2026H1"
        or output.get("asOf") != "2026-08-02"
        or output.get("sourceIntegrity", {}).get("filesValidated") != 2
        or output.get("sourceIntegrity", {}).get("bytesValidated") != 1_757_433
    ):
        errors.append("series identity or source-integrity vector differs")

    annual = output.get("annual2025", {})
    if annual != {
        "provisional": True,
        "accruedExciseEurMillion": 36.151,
        "accruedExciseEur": 36_151_000,
        "netCashReceiptsEurMillion": 29.568,
        "netCashReceiptsEur": 29_568_000,
    }:
        errors.append("annual 2025 vector differs")

    rows = output.get("monthlyCashSeries")
    if not isinstance(rows, list) or len(rows) != 18:
        errors.append("exactly 18 monthly rows are required")
        rows = []
    index = {
        (row.get("year"), row.get("month")): row
        for row in rows
        if isinstance(row, dict)
    }
    expected_coverage = {(2025, month) for month in range(1, 13)} | {
        (2026, month) for month in range(1, 7)
    }
    if set(index) != expected_coverage:
        errors.append("monthly coverage differs from 2025 plus 2026 H1")

    for year, expected in ((2025, EXPECTED_2025), (2026, EXPECTED_2026_H1)):
        for month, vector in expected.items():
            row = index.get((year, month), {})
            actual = tuple(
                row.get(key)
                for key in (
                    "grossEurThousand",
                    "refundsEurThousand",
                    "netEurThousand",
                )
            )
            if actual != vector:
                errors.append(f"{year}-{month:02d}: monthly vector differs")
                continue
            if vector[0] is None:
                if any(
                    row.get(key) is not None
                    for key in ("grossEur", "refundsEur", "netEur")
                ):
                    errors.append(f"{year}-{month:02d}: blank source month must remain null")
            else:
                if vector[0] + vector[1] != vector[2]:
                    errors.append(f"{year}-{month:02d}: controlled identity is invalid")
                if tuple(
                    row.get(key)
                    for key in ("grossEur", "refundsEur", "netEur")
                ) != tuple(value * 1000 for value in vector):
                    errors.append(f"{year}-{month:02d}: EUR expansion differs")

    summaries = output.get("cashSummaries", {})
    if summaries.get("2025") != {
        "grossEurThousand": 31_797,
        "refundsEurThousand": -2_229,
        "netEurThousand": 29_568,
        "grossEur": 31_797_000,
        "refundsEur": -2_229_000,
        "netEur": 29_568_000,
    }:
        errors.append("2025 cash summary differs")
    if summaries.get("2026H1") != {
        "grossEurThousand": 25_726,
        "refundsEurThousand": -3_950,
        "netEurThousand": 21_776,
        "grossEur": 25_726_000,
        "refundsEur": -3_950_000,
        "netEur": 21_776_000,
    }:
        errors.append("2026 H1 cash summary differs")

    if (
        output.get("retailMarketValueComputed") is not False
        or output.get("globalRollupChanged") is not False
        or control.get("retailSalesEligible") is not False
        or control.get("globalRollupEligible") is not False
    ):
        errors.append("retail and global-roll-up boundaries must remain false")

    for token in (
        "all four epigraphs",
        "not e-liquid-only",
        "no devices",
        "mainland Spain and the Balearic Islands",
        "not consumer retail",
        "Do not claim",
    ):
        if token.casefold() not in memo.casefold():
            errors.append(f"memo is missing boundary token: {token}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Spain AEAT 2025–2026 H1 excise series validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
