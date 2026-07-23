#!/usr/bin/env python3
"""Fail-closed validation for the public paid-data procurement shortlist."""

from __future__ import annotations

import csv
from datetime import date
import io
import json
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import urlparse
import zipfile

from openpyxl import load_workbook

from build_paid_data_procurement import (
    CSV_FIELDS,
    OUTPUT_CSV,
    OUTPUT_JSON,
    OUTPUT_XLSX,
    SOURCE_PATH,
    normalised,
    render_csv,
    render_json,
    score_item,
)


EXPECTED_TOP_LEVEL = {
    "schemaVersion",
    "programmeId",
    "asOf",
    "version",
    "status",
    "publicBoundaryEn",
    "publicBoundaryFi",
    "rankingBoundaryEn",
    "rankingBoundaryFi",
    "currencyNoteEn",
    "currencyNoteFi",
    "weights",
    "packageOptions",
    "items",
    "goCriteria",
    "stopCriteria",
    "avoidAsPrimary",
}
WEIGHT_IDS = {
    "annualSalesFit",
    "vapeSpecificity",
    "countryCoverage",
    "methodTransparency",
    "transactionLicenceFit",
    "costCertainty",
}
PRICE_TYPES = {"public_list_price", "vendor_quote"}
FORBIDDEN_PUBLIC_TEXT = (
    "/users/",
    "file://",
    "@gmail.com",
    "blackrock",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def valid_iso_date(value: Any) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def valid_public_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and not parsed.username
        and not parsed.password
        and not any(
            key.casefold() in {"access_token", "api_key", "key", "password", "secret", "token"}
            for key, _ in __import__("urllib.parse").parse.parse_qsl(parsed.query)
        )
    )


def text_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from text_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from text_values(item)


def validate_source(source: Any, errors: list[str]) -> None:
    if not isinstance(source, dict):
        errors.append("source must contain an object")
        return
    if set(source) != EXPECTED_TOP_LEVEL or source.get("schemaVersion") != 1:
        errors.append("source has an unsupported top-level schema")
        return
    if source.get("status") != "decision_support_only_no_purchase_authorised":
        errors.append("source must state that no purchase is authorised")
    if not valid_iso_date(source.get("asOf")) or source.get("version") != "2026.07.23-1":
        errors.append("source date or version is invalid")

    weights = source.get("weights")
    if not isinstance(weights, list) or len(weights) != 6:
        errors.append("exactly six transparent weights are required")
        return
    if {item.get("id") for item in weights if isinstance(item, dict)} != WEIGHT_IDS:
        errors.append("weight IDs differ from the reviewed score model")
    try:
        if abs(sum(float(item["weight"]) for item in weights) - 1.0) > 1e-9:
            errors.append("weights must sum to 1.0")
    except (KeyError, TypeError, ValueError):
        errors.append("weights must be numeric")

    items = source.get("items")
    if not isinstance(items, list) or len(items) != 11:
        errors.append("exactly 11 reviewed procurement items are required")
        return
    ranks = [item.get("rank") for item in items if isinstance(item, dict)]
    if sorted(ranks) != list(range(1, 12)) or len(set(ranks)) != 11:
        errors.append("procurement ranks must be unique integers 1–11")
    item_ids = [item.get("itemId") for item in items if isinstance(item, dict)]
    if any(not isinstance(value, str) or not value for value in item_ids) or len(set(item_ids)) != 11:
        errors.append("item IDs must be unique non-empty strings")

    for item in items:
        label = f'item {item.get("rank", "?")}' if isinstance(item, dict) else "item"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        if item.get("priceType") not in PRICE_TYPES:
            errors.append(f"{label}: invalid priceType")
        if item.get("priceType") == "vendor_quote":
            if item.get("priceAmount") is not None or item.get("currency") is not None:
                errors.append(f"{label}: quote-only item cannot expose a fake numeric price")
            if "quote" not in str(item.get("priceDisplay", "")).casefold():
                errors.append(f"{label}: quote-only price display must say Quote")
        else:
            if not isinstance(item.get("priceAmount"), (int, float)) or item["priceAmount"] <= 0:
                errors.append(f"{label}: public list price must be positive")
            if item.get("currency") not in {"USD", "EUR", "GBP"}:
                errors.append(f"{label}: public list price currency is invalid")
        scores = item.get("scores")
        if not isinstance(scores, dict) or set(scores) != WEIGHT_IDS:
            errors.append(f"{label}: score schema differs")
        elif any(not isinstance(value, (int, float)) or value < 1 or value > 5 for value in scores.values()):
            errors.append(f"{label}: every score must be between 1 and 5")
        else:
            computed = score_item(item, weights)
            if computed < 1 or computed > 5:
                errors.append(f"{label}: weighted score is outside 1–5")
        if not valid_iso_date(item.get("verifiedOn")) or item.get("verifiedOn") > source["asOf"]:
            errors.append(f"{label}: verification date is invalid")
        urls = item.get("sourceUrls")
        if not isinstance(urls, list) or not urls or any(not valid_public_url(url) for url in urls):
            errors.append(f"{label}: official/vendor HTTPS source links are required")
        if item.get("transactionLicenceFit", None) is not None:
            errors.append(f"{label}: transaction licence fit must stay inside the transparent score object")

    if len(source.get("goCriteria", [])) < 5 or len(source.get("stopCriteria", [])) < 5:
        errors.append("at least five go and five stop criteria are required")
    if len(source.get("packageOptions", [])) != 3:
        errors.append("exactly three procurement package options are required")
    combined = "\n".join(text_values(source)).casefold()
    for phrase in FORBIDDEN_PUBLIC_TEXT:
        if phrase in combined:
            errors.append(f"source contains forbidden public text {phrase!r}")
    if "no purchase" not in combined and "mitään ostoa" not in combined:
        errors.append("visible no-purchase boundary is missing")
    if "data-room" not in combined and "datahuone" not in combined:
        errors.append("transaction data-room licence gate is missing")


def validate_outputs(source: dict[str, Any], errors: list[str]) -> None:
    if not OUTPUT_JSON.exists() or OUTPUT_JSON.read_bytes() != render_json(source):
        errors.append("public paid-data JSON is missing or stale")
    elif read_json(OUTPUT_JSON) != normalised(source):
        errors.append("public paid-data JSON differs semantically")
    if not OUTPUT_CSV.exists() or OUTPUT_CSV.read_bytes() != render_csv(source):
        errors.append("public paid-data CSV is missing or stale")
    else:
        rows = list(csv.DictReader(io.StringIO(OUTPUT_CSV.read_text(encoding="utf-8"))))
        if len(rows) != 11 or (rows and list(rows[0]) != CSV_FIELDS):
            errors.append("public paid-data CSV schema or row count differs")
        if any(row["purchaseAuthorised"] != "false" for row in rows):
            errors.append("public paid-data CSV must state purchaseAuthorised=false")


def validate_workbook(source: dict[str, Any], errors: list[str]) -> None:
    if not OUTPUT_XLSX.is_file():
        errors.append("reviewed public paid-data XLSX is missing")
        return
    try:
        workbook = load_workbook(OUTPUT_XLSX, read_only=False, data_only=False)
    except Exception as error:  # pragma: no cover - defensive parse boundary
        errors.append(f"cannot parse paid-data XLSX: {error}")
        return
    expected_sheets = ["Decision", "Priorities", "RFP Gate", "Avoid", "Sources"]
    if workbook.sheetnames != expected_sheets:
        errors.append("paid-data XLSX sheet list differs")
        return
    if any(sheet.sheet_state != "visible" for sheet in workbook.worksheets):
        errors.append("paid-data XLSX cannot contain hidden sheets")
    priority = workbook["Priorities"]
    expected_headers = [
        "Rank",
        "Priority",
        "Vendor",
        "Product",
        "Tier",
        "Price",
        "Decision / Päätös",
        "Annual series",
        "Vape",
        "Countries",
        "Method",
        "Licence",
        "Cost",
        "Weighted score",
        "Alternative group",
        "Source",
    ]
    headers = [priority.cell(5, column).value for column in range(1, 17)]
    if headers != expected_headers:
        errors.append("paid-data XLSX priority headers differ")
    ordered = sorted(source["items"], key=lambda item: item["rank"])
    for index, item in enumerate(ordered, start=6):
        if priority.cell(index, 1).value != item["rank"]:
            errors.append(f"paid-data XLSX rank differs at row {index}")
        if priority.cell(index, 3).value != item["vendor"] or priority.cell(index, 4).value != item["product"]:
            errors.append(f"paid-data XLSX vendor/product differs at row {index}")
        expected_formula = (
            f"=ROUND(H{index}*Decision!$B$17+I{index}*Decision!$B$18+"
            f"J{index}*Decision!$B$19+K{index}*Decision!$B$20+"
            f"L{index}*Decision!$B$21+M{index}*Decision!$B$22,2)"
        )
        if priority.cell(index, 14).value != expected_formula:
            errors.append(f"paid-data XLSX weighted-score formula differs at row {index}")
    formula_errors = {"#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A", "#NUM!"}
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.comment is not None:
                    errors.append("paid-data XLSX cannot contain comments")
                if isinstance(cell.value, str) and cell.value in formula_errors:
                    errors.append(f"paid-data XLSX contains formula error {cell.value}")
                if isinstance(cell.value, str) and cell.value.startswith("=") and "[" in cell.value:
                    errors.append("paid-data XLSX cannot contain external workbook formulas")
    workbook.close()

    with zipfile.ZipFile(OUTPUT_XLSX) as package:
        lowered = [name.casefold() for name in package.namelist()]
        forbidden = ("vbaproject", "externallink", "connections", "comments", "embedding", "oleobject")
        for name in lowered:
            if any(part in name for part in forbidden):
                errors.append(f"paid-data XLSX contains forbidden OOXML part {name}")


def main() -> int:
    errors: list[str] = []
    try:
        source = read_json(SOURCE_PATH)
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL: cannot read paid-data source: {error}", file=sys.stderr)
        return 1
    validate_source(source, errors)
    if not errors:
        validate_outputs(source, errors)
        validate_workbook(source, errors)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(
        "PASS: 11-item paid-data shortlist, transparent scores, 3 package options, "
        "go/stop gates, JSON/CSV/XLSX parity and no-purchase boundary verified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
