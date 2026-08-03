#!/usr/bin/env python3
"""Extract a fail-closed 2022–2025 Japan customs-import proxy series."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTROL = ROOT / "source" / "JAPAN_2022_2025_OFFICIAL_CUSTOMS_SERIES_CONTROL.json"
DEFAULT_OUTPUT = ROOT / "source" / "JAPAN_2022_2025_OFFICIAL_CUSTOMS_SERIES.json"
REQUIRED_FIELDS = {
    "Exp or Imp",
    "Year",
    "HS",
    "Country",
    "Unit1",
    "Unit2",
    "Quantity1-Year",
    "Quantity2-Year",
    "Value-Year",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downloads", type=Path, required=True)
    parser.add_argument("--control", type=Path, default=DEFAULT_CONTROL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> csv.DictReader:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "cp932", "shift_jis"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"{path.name}: unsupported CSV encoding")
    reader = csv.DictReader(text.splitlines())
    if reader.fieldnames is None or not REQUIRED_FIELDS.issubset(reader.fieldnames):
        missing = sorted(REQUIRED_FIELDS - set(reader.fieldnames or []))
        raise ValueError(f"{path.name}: missing required fields {missing}")
    return reader


def number(value: str, field: str, *, blank_allowed: bool = False) -> Decimal | None:
    cleaned = str(value or "").strip().replace(",", "")
    if not cleaned and blank_allowed:
        return None
    try:
        result = Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"{field} must be numeric") from None
    if not result.is_finite() or result < 0:
        raise ValueError(f"{field} must be a finite non-negative number")
    return result


def decimal_output(value: Decimal) -> int | float:
    integral = value.to_integral_value()
    return int(integral) if value == integral else float(value)


def validate_control(control: dict[str, Any]) -> None:
    if (
        control.get("schemaVersion") != "1.0"
        or control.get("seriesId") != "JP_MOF_ESTAT_CUSTOMS_IMPORT_2022_2025"
        or control.get("asOf") != "2026-08-02"
        or control.get("transactionStage") != "customs_import_declaration"
        or control.get("retailSalesEligible") is not False
        or control.get("globalRollupEligible") is not False
    ):
        raise ValueError("control identity or fail-closed boundary is invalid")

    codes = control.get("codes")
    if not isinstance(codes, list) or {item.get("code") for item in codes} != {
        "240412000",
        "240419100",
        "240419200",
        "854340000",
    }:
        raise ValueError("the exact reviewed four-code set is required")
    if any(not re.fullmatch(r"\d{9}", str(item.get("code", ""))) for item in codes):
        raise ValueError("every Japan code must contain exactly nine digits")

    years = control.get("years")
    if not isinstance(years, list) or [item.get("year") for item in years] != [
        2022,
        2023,
        2024,
        2025,
    ]:
        raise ValueError("the exact 2022–2025 year set is required")
    for item in years:
        if len(item.get("files", [])) != 2:
            raise ValueError(f"{item.get('year')}: exactly two chapter files required")
        if {file.get("chapterFile") for file in item["files"]} != {"04", "16"}:
            raise ValueError(f"{item.get('year')}: chapter files must be 04 and 16")
        rate = number(
            str(item.get("ecbRate", {}).get("currencyUnitsPerEur", "")),
            "currencyUnitsPerEur",
        )
        if rate is None or rate <= 0:
            raise ValueError(f"{item.get('year')}: ECB rate is missing")


def extract(downloads: Path, control_path: Path) -> dict[str, Any]:
    control_bytes = control_path.read_bytes()
    control = json.loads(control_bytes)
    validate_control(control)
    code_map = {item["code"]: item for item in control["codes"]}
    observations: list[dict[str, Any]] = []
    files_validated = 0
    bytes_validated = 0

    for year_record in control["years"]:
        year = int(year_record["year"])
        rate = Decimal(str(year_record["ecbRate"]["currencyUnitsPerEur"]))
        totals: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "value": Decimal(0),
                "q1": Decimal(0),
                "q2": Decimal(0),
                "q1Present": False,
                "q2Present": False,
                "u1": set(),
                "u2": set(),
                "partners": set(),
            }
        )

        for file_record in year_record["files"]:
            path = downloads / file_record["fileName"]
            if not path.is_file():
                raise ValueError(f"{path.name}: required source file is missing")
            if path.stat().st_size != file_record["bytes"]:
                raise ValueError(f"{path.name}: byte size differs from control")
            if sha256_file(path) != file_record["sha256"]:
                raise ValueError(f"{path.name}: SHA-256 differs from control")
            files_validated += 1
            bytes_validated += path.stat().st_size

            allowed_codes = {
                item["code"]
                for item in control["codes"]
                if item["chapterFile"] == file_record["chapterFile"]
            }
            for row in read_csv(path):
                code = row["HS"].strip().strip("'")
                if code not in allowed_codes:
                    continue
                if row["Exp or Imp"].strip() != "2" or row["Year"].strip() != str(year):
                    raise ValueError(f"{path.name}: target code has wrong flow or year")
                partner = row["Country"].strip()
                if not re.fullmatch(r"\d{3}", partner):
                    raise ValueError(f"{path.name}: invalid partner code for {code}")
                current = totals[code]
                current["partners"].add(partner)
                current["value"] += number(row["Value-Year"], "Value-Year") or Decimal(0)
                for suffix in ("1", "2"):
                    quantity = number(
                        row[f"Quantity{suffix}-Year"],
                        f"Quantity{suffix}-Year",
                        blank_allowed=True,
                    )
                    unit = row[f"Unit{suffix}"].strip()
                    if quantity is not None:
                        current[f"q{suffix}"] += quantity
                        current[f"q{suffix}Present"] = True
                    if unit:
                        current[f"u{suffix}"].add(unit)

        if set(totals) != set(code_map):
            raise ValueError(f"{year}: one or more reviewed target codes are absent")

        for code in sorted(totals):
            total = totals[code]
            if len(total["u1"]) > 1 or len(total["u2"]) > 1:
                raise ValueError(f"{year} {code}: inconsistent quantity units")
            amount_jpy = total["value"] * Decimal(1000)
            eur = (amount_jpy / rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            classification = code_map[code]
            observations.append(
                {
                    "observationId": f"JP-MOF-IMPORT-{year}-{code}",
                    "year": year,
                    "classificationCode": code,
                    "productBucket": classification["bucket"],
                    "classificationDecision": classification["decision"],
                    "classificationVersion": year_record["classificationVersion"],
                    "transactionStage": control["transactionStage"],
                    "flow": control["flow"],
                    "partnerRows": len(total["partners"]),
                    "amountJpyThousand": decimal_output(total["value"]),
                    "amountJpy": decimal_output(amount_jpy),
                    "currency": "JPY",
                    "eurEquivalent": decimal_output(eur),
                    "eurEquivalentStatus": "computed_secondary_analytical",
                    "ecbCurrencyUnitsPerEur": decimal_output(rate),
                    "ecbSourceUrl": year_record["ecbRate"]["sourceUrl"],
                    "quantity1": (
                        decimal_output(total["q1"])
                        if total["q1Present"] and total["u1"]
                        else None
                    ),
                    "quantity1Unit": next(iter(total["u1"]), None),
                    "quantity2": (
                        decimal_output(total["q2"])
                        if total["q2Present"] and total["u2"]
                        else None
                    ),
                    "quantity2Unit": next(iter(total["u2"]), None),
                    "retailSalesEligible": False,
                    "globalRollupEligible": False,
                }
            )

    return {
        "schemaVersion": "1.0",
        "seriesId": control["seriesId"],
        "asOf": control["asOf"],
        "sourceIntegrity": {
            "controlSha256": hashlib.sha256(control_bytes).hexdigest(),
            "filesValidated": files_validated,
            "bytesValidated": bytes_validated,
        },
        "primaryMeasure": "official customs import CIF value",
        "currencyPolicy": (
            "JPY is primary; EUR is a secondary same-year ECB annual-average "
            "analytical equivalent."
        ),
        "observations": observations,
        "retailMarketValueComputed": False,
        "globalRollupChanged": False,
        "limitations": [
            "Customs imports are not consumer retail sell-through.",
            "Codes 240419100 and 240419200 remain excluded from vaping scope.",
            "Code 240412000 is not an e-liquid-only category.",
            "Exports, domestic production, inventory, illicit supply, retail mark-up and channel coverage are not included.",
            "The EUR value is analytical and does not replace the official JPY observation."
        ],
    }


def main() -> None:
    args = parse_args()
    result = extract(args.downloads.resolve(), args.control.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "files": result["sourceIntegrity"]["filesValidated"],
                "observations": len(result["observations"]),
                "retailMarketValueComputed": False,
                "output": str(args.output),
            }
        )
    )


if __name__ == "__main__":
    main()
