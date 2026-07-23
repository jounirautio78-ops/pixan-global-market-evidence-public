#!/usr/bin/env python3
"""Build public paid-data procurement JSON and CSV.

This builder publishes only the reviewed procurement decision record. It does
not buy, subscribe to, contact or endorse any vendor. The reviewed XLSX is
created separately with the workspace spreadsheet runtime and validated against
the same canonical source before publication.
"""

from __future__ import annotations

import copy
import csv
from decimal import Decimal, ROUND_HALF_UP
import io
import json
import os
from pathlib import Path
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "source" / "paid-data-procurement.json"
OUTPUT_JSON = ROOT / "site" / "data" / "paid-data-procurement.json"
OUTPUT_CSV = ROOT / "site" / "data" / "paid-data-procurement.csv"
OUTPUT_XLSX = ROOT / "site" / "downloads" / "pixan-paid-data-procurement-fi-en.xlsx"

CSV_FIELDS = [
    "rank",
    "priorityCode",
    "tier",
    "vendor",
    "product",
    "category",
    "priceType",
    "priceAmount",
    "currency",
    "priceDisplay",
    "weightedScore",
    "roleEn",
    "roleFi",
    "coverageEn",
    "coverageFi",
    "decisionEn",
    "decisionFi",
    "conditionsEn",
    "conditionsFi",
    "alternativeGroup",
    "sourceUrls",
    "verifiedOn",
    "programmeVersion",
    "programmeAsOf",
    "purchaseAuthorised",
]


def load_source() -> dict[str, Any]:
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def score_item(item: dict[str, Any], weights: list[dict[str, Any]]) -> float:
    total = sum(
        Decimal(str(item["scores"][weight["id"]])) * Decimal(str(weight["weight"]))
        for weight in weights
    )
    return float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def normalised(source: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(source)
    result["items"] = sorted(result["items"], key=lambda item: item["rank"])
    for item in result["items"]:
        item["weightedScore"] = score_item(item, result["weights"])
    return result


def render_json(source: dict[str, Any]) -> bytes:
    return (
        json.dumps(normalised(source), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def render_csv(source: dict[str, Any]) -> bytes:
    programme = normalised(source)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for item in programme["items"]:
        writer.writerow(
            {
                "rank": item["rank"],
                "priorityCode": item["priorityCode"],
                "tier": item["tier"],
                "vendor": item["vendor"],
                "product": item["product"],
                "category": item["category"],
                "priceType": item["priceType"],
                "priceAmount": "" if item["priceAmount"] is None else item["priceAmount"],
                "currency": item["currency"] or "",
                "priceDisplay": item["priceDisplay"],
                "weightedScore": f'{item["weightedScore"]:.2f}',
                "roleEn": item["roleEn"],
                "roleFi": item["roleFi"],
                "coverageEn": item["coverageEn"],
                "coverageFi": item["coverageFi"],
                "decisionEn": item["decisionEn"],
                "decisionFi": item["decisionFi"],
                "conditionsEn": item["conditionsEn"],
                "conditionsFi": item["conditionsFi"],
                "alternativeGroup": item["alternativeGroup"] or "",
                "sourceUrls": " | ".join(item["sourceUrls"]),
                "verifiedOn": item["verifiedOn"],
                "programmeVersion": programme["version"],
                "programmeAsOf": programme["asOf"],
                "purchaseAuthorised": "false",
            }
        )
    return buffer.getvalue().encode("utf-8")


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        handle.write(content)
        temporary_path = Path(handle.name)
    os.replace(temporary_path, path)


def build() -> list[Path]:
    source = load_source()
    outputs = {
        OUTPUT_JSON: render_json(source),
        OUTPUT_CSV: render_csv(source),
    }
    for path, content in outputs.items():
        write_atomic(path, content)
    return list(outputs)


def main() -> None:
    outputs = build()
    print(
        "Built paid-data procurement outputs: "
        + ", ".join(str(path.relative_to(ROOT)) for path in outputs)
    )


if __name__ == "__main__":
    main()
