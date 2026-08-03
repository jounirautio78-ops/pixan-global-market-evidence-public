#!/usr/bin/env python3
"""Extract a fail-closed Spain AEAT 2025–2026 H1 excise series."""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTROL = ROOT / "source" / "SPAIN_AEAT_2025_2026_EXCISE_SERIES_CONTROL.json"
DEFAULT_OUTPUT = ROOT / "source" / "SPAIN_AEAT_2025_2026_EXCISE_SERIES.json"
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CELL_RE = re.compile(r"^[A-Z]+[1-9][0-9]*$")


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


def normalize_text(value: object) -> str:
    return " ".join(str(value).split())


def decimal_value(value: object, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f"{field}: expected a numeric value") from None
    if not result.is_finite():
        raise ValueError(f"{field}: expected a finite numeric value")
    return result


def json_number(value: Decimal) -> int | float:
    integral = value.to_integral_value()
    return int(integral) if value == integral else float(value)


class XlsxBook:
    """Minimal read-only OOXML reader for named worksheets and cached values."""

    def __init__(self, path: Path):
        self.path = path
        try:
            self.archive = ZipFile(path)
        except BadZipFile:
            raise ValueError(f"{path.name}: source is not a valid XLSX file") from None
        self.shared_strings = self._read_shared_strings()
        self.sheet_paths = self._read_sheet_paths()
        self._cell_cache: dict[str, dict[str, str | None]] = {}

    def close(self) -> None:
        self.archive.close()

    def __enter__(self) -> "XlsxBook":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def _read_shared_strings(self) -> list[str]:
        if "xl/sharedStrings.xml" not in self.archive.namelist():
            return []
        root = ET.fromstring(self.archive.read("xl/sharedStrings.xml"))
        return [
            "".join(node.text or "" for node in item.iter(f"{{{MAIN_NS}}}t"))
            for item in root.findall(f"{{{MAIN_NS}}}si")
        ]

    def _read_sheet_paths(self) -> dict[str, str]:
        workbook = ET.fromstring(self.archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(
            self.archive.read("xl/_rels/workbook.xml.rels")
        )
        targets = {
            item.attrib["Id"]: item.attrib["Target"]
            for item in relationships.findall(f"{{{PACKAGE_REL_NS}}}Relationship")
        }
        result: dict[str, str] = {}
        for sheet in workbook.findall(f".//{{{MAIN_NS}}}sheet"):
            relation_id = sheet.attrib[f"{{{OFFICE_REL_NS}}}id"]
            target = targets.get(relation_id)
            if not target:
                raise ValueError(f"{self.path.name}: worksheet relationship is missing")
            if target.startswith("/"):
                archive_path = target.lstrip("/")
            else:
                archive_path = posixpath.normpath(posixpath.join("xl", target))
            result[sheet.attrib["name"]] = archive_path
        return result

    def _cells(self, sheet_name: str) -> dict[str, str | None]:
        if sheet_name not in self.sheet_paths:
            raise ValueError(f"{self.path.name}: worksheet {sheet_name!r} is missing")
        if sheet_name in self._cell_cache:
            return self._cell_cache[sheet_name]
        root = ET.fromstring(self.archive.read(self.sheet_paths[sheet_name]))
        cells: dict[str, str | None] = {}
        for cell in root.findall(f".//{{{MAIN_NS}}}c"):
            reference = cell.attrib.get("r", "")
            if not CELL_RE.fullmatch(reference):
                continue
            cell_type = cell.attrib.get("t")
            if cell_type == "inlineStr":
                value: str | None = "".join(
                    node.text or "" for node in cell.iter(f"{{{MAIN_NS}}}t")
                )
            else:
                value_node = cell.find(f"{{{MAIN_NS}}}v")
                value = value_node.text if value_node is not None else None
                if cell_type == "s" and value is not None:
                    try:
                        value = self.shared_strings[int(value)]
                    except (IndexError, ValueError):
                        raise ValueError(
                            f"{self.path.name}: invalid shared-string index in {reference}"
                        ) from None
            cells[reference] = value
        self._cell_cache[sheet_name] = cells
        return cells

    def cell(self, sheet_name: str, reference: str) -> str | None:
        if not CELL_RE.fullmatch(reference):
            raise ValueError(f"invalid cell reference {reference!r}")
        return self._cells(sheet_name).get(reference)


def validate_control(control: dict[str, Any]) -> None:
    if (
        control.get("schemaVersion") != "1.0"
        or control.get("seriesId") != "ES_AEAT_ECIG_LIQUID_EXCISE_2025_2026H1"
        or control.get("asOf") != "2026-08-02"
        or control.get("retailSalesEligible") is not False
        or control.get("globalRollupEligible") is not False
        or control.get("currency") != "EUR"
    ):
        raise ValueError("control identity or fail-closed boundary is invalid")
    sources = control.get("sources")
    if not isinstance(sources, list) or len(sources) != 2:
        raise ValueError("exactly two controlled AEAT sources are required")
    roles = {source.get("role") for source in sources}
    if roles != {"annual_2025_reconciliation", "monthly_cash_series_2025_2026H1"}:
        raise ValueError("annual and monthly source roles are required")
    monthly = next(source for source in sources if source["role"].startswith("monthly"))
    rows = monthly.get("rows")
    if not isinstance(rows, list) or len(rows) != 18:
        raise ValueError("the exact 18-month controlled series is required")
    coverage = [(row.get("year"), row.get("month")) for row in rows]
    if coverage != [(2025, month) for month in range(1, 13)] + [
        (2026, month) for month in range(1, 7)
    ]:
        raise ValueError("monthly coverage must be 2025 plus 2026 H1")
    for row in rows[:3]:
        if any(row.get(field) is not None for field in ("gross", "refunds", "net")):
            raise ValueError("January through March 2025 must remain null")


def verify_text(actual: str | None, expected: object, context: str) -> None:
    if actual is None or normalize_text(actual) != normalize_text(expected):
        raise ValueError(f"{context}: text differs from control")


def verify_number(
    actual: str | None,
    expected: object,
    context: str,
    *,
    decimal_places: int | None = None,
) -> None:
    if actual is None:
        raise ValueError(f"{context}: numeric value differs from control")
    actual_number = decimal_value(actual, context)
    expected_number = decimal_value(expected, context)
    if decimal_places is not None:
        quantum = Decimal(1).scaleb(-decimal_places)
        actual_number = actual_number.quantize(quantum)
        expected_number = expected_number.quantize(quantum)
    if actual_number != expected_number:
        raise ValueError(f"{context}: numeric value differs from control")


def verify_source_file(downloads: Path, source: dict[str, Any]) -> Path:
    path = downloads / source["fileName"]
    if not path.is_file():
        raise ValueError(f"{path.name}: required official workbook is missing")
    if path.stat().st_size != source["bytes"]:
        raise ValueError(f"{path.name}: byte size differs from control")
    if sha256_file(path) != source["sha256"]:
        raise ValueError(f"{path.name}: SHA-256 differs from control")
    return path


def add_eur_amount(value_thousand: int | None) -> int | None:
    return None if value_thousand is None else value_thousand * 1000


def extract(downloads: Path, control_path: Path) -> dict[str, Any]:
    control_bytes = control_path.read_bytes()
    control = json.loads(control_bytes)
    validate_control(control)
    sources = {source["role"]: source for source in control["sources"]}
    files_validated = 0
    bytes_validated = 0

    annual_source = sources["annual_2025_reconciliation"]
    annual_path = verify_source_file(downloads, annual_source)
    files_validated += 1
    bytes_validated += annual_path.stat().st_size
    annual_values: dict[str, Decimal] = {}
    with XlsxBook(annual_path) as book:
        for reference, expectation in annual_source["expectedCells"].items():
            actual = book.cell(annual_source["sheet"], reference)
            context = f"{annual_path.name} {annual_source['sheet']}!{reference}"
            if expectation["type"] == "text":
                verify_text(actual, expectation["value"], context)
            elif expectation["type"] == "number":
                decimal_places = expectation.get("decimalPlaces")
                verify_number(
                    actual,
                    expectation["value"],
                    context,
                    decimal_places=decimal_places,
                )
                value = decimal_value(actual, context)
                if decimal_places is not None:
                    value = value.quantize(Decimal(1).scaleb(-decimal_places))
                annual_values[reference] = value
            else:
                raise ValueError(f"{context}: unsupported expectation type")

    monthly_source = sources["monthly_cash_series_2025_2026H1"]
    monthly_path = verify_source_file(downloads, monthly_source)
    files_validated += 1
    bytes_validated += monthly_path.stat().st_size
    monthly_rows: list[dict[str, Any]] = []
    columns = monthly_source["columns"]
    with XlsxBook(monthly_path) as book:
        sheet = monthly_source["sheet"]
        for reference, expected in monthly_source["headerCells"].items():
            verify_text(
                book.cell(sheet, reference),
                expected,
                f"{monthly_path.name} {sheet}!{reference}",
            )
        for expected in monthly_source["rows"]:
            row_number = expected["row"]
            for key, expected_value in (
                ("year", expected["year"]),
                ("month", expected["month"]),
            ):
                reference = f"{columns[key]}{row_number}"
                verify_number(
                    book.cell(sheet, reference),
                    expected_value,
                    f"{monthly_path.name} {sheet}!{reference}",
                )
            label_reference = f"{columns['monthLabel']}{row_number}"
            verify_text(
                book.cell(sheet, label_reference),
                expected["monthLabel"],
                f"{monthly_path.name} {sheet}!{label_reference}",
            )
            extracted: dict[str, int | None] = {}
            for key, source_key in (
                ("grossEurThousand", "gross"),
                ("refundsEurThousand", "refunds"),
                ("netEurThousand", "net"),
            ):
                reference = f"{columns[key]}{row_number}"
                actual = book.cell(sheet, reference)
                expected_value = expected[source_key]
                if expected_value is None:
                    if actual not in (None, ""):
                        raise ValueError(f"{monthly_path.name} {sheet}!{reference}: expected blank")
                    extracted[key] = None
                else:
                    verify_number(
                        actual,
                        expected_value,
                        f"{monthly_path.name} {sheet}!{reference}",
                    )
                    numeric = decimal_value(actual, reference)
                    if numeric != numeric.to_integral_value():
                        raise ValueError(f"{reference}: expected an integer EUR-thousand value")
                    extracted[key] = int(numeric)
            if extracted["grossEurThousand"] is not None:
                if (
                    extracted["grossEurThousand"] + extracted["refundsEurThousand"]
                    != extracted["netEurThousand"]
                ):
                    raise ValueError(f"row {row_number}: gross plus refunds does not equal net")
            monthly_rows.append(
                {
                    "observationId": f"ES-AEAT-CASH-{expected['year']}-{expected['month']:02d}",
                    "year": expected["year"],
                    "month": expected["month"],
                    "monthLabel": expected["monthLabel"],
                    **extracted,
                    "grossEur": add_eur_amount(extracted["grossEurThousand"]),
                    "refundsEur": add_eur_amount(extracted["refundsEurThousand"]),
                    "netEur": add_eur_amount(extracted["netEurThousand"]),
                }
            )

    summaries: dict[str, dict[str, int]] = {}
    for period, selected_rows in (
        ("2025", [row for row in monthly_rows if row["year"] == 2025]),
        ("2026H1", [row for row in monthly_rows if row["year"] == 2026]),
    ):
        total = {
            "grossEurThousand": sum(row["grossEurThousand"] or 0 for row in selected_rows),
            "refundsEurThousand": sum(row["refundsEurThousand"] or 0 for row in selected_rows),
            "netEurThousand": sum(row["netEurThousand"] or 0 for row in selected_rows),
        }
        expected_total = monthly_source["expectedTotalsEurThousand"][period]
        for output_key, control_key in (
            ("grossEurThousand", "gross"),
            ("refundsEurThousand", "refunds"),
            ("netEurThousand", "net"),
        ):
            if total[output_key] != expected_total[control_key]:
                raise ValueError(f"{period}: {output_key} differs from controlled total")
        if total["grossEurThousand"] + total["refundsEurThousand"] != total["netEurThousand"]:
            raise ValueError(f"{period}: gross plus refunds does not equal net")
        summaries[period] = {
            **total,
            "grossEur": total["grossEurThousand"] * 1000,
            "refundsEur": total["refundsEurThousand"] * 1000,
            "netEur": total["netEurThousand"] * 1000,
        }

    accrued_million = annual_values["AG29"]
    net_cash_million = annual_values["AG45"]
    if net_cash_million * Decimal(1000) != Decimal(summaries["2025"]["netEurThousand"]):
        raise ValueError("2025 annual cash value does not reconcile to monthly net total")

    return {
        "schemaVersion": "1.0",
        "seriesId": control["seriesId"],
        "asOf": control["asOf"],
        "sourceIntegrity": {
            "controlSha256": hashlib.sha256(control_bytes).hexdigest(),
            "filesValidated": files_validated,
            "bytesValidated": bytes_validated,
        },
        "geography": control["geography"],
        "taxScope": control["taxScope"],
        "annual2025": {
            "provisional": True,
            "accruedExciseEurMillion": json_number(accrued_million),
            "accruedExciseEur": json_number(accrued_million * Decimal(1_000_000)),
            "netCashReceiptsEurMillion": json_number(net_cash_million),
            "netCashReceiptsEur": json_number(net_cash_million * Decimal(1_000_000)),
        },
        "monthlyCashSeries": monthly_rows,
        "cashSummaries": summaries,
        "retailMarketValueComputed": False,
        "globalRollupChanged": False,
        "limitations": [
            "The tax aggregate combines all four epigraphs and is not e-liquid-only.",
            "The series contains no device sales, device quantities or device revenue.",
            "Accrued excise and cash receipts are tax-stage measures, not consumer retail sell-through.",
            "January through March 2025 are blank in the official monthly workbook and remain null, not zero.",
            "The controlled geography is mainland Spain and the Balearic Islands, excluding Canary Islands, Ceuta and Melilla.",
            "No taxable volume, retail price, tax-exclusive sales, illicit supply or channel coverage is inferred."
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
                "monthlyObservations": len(result["monthlyCashSeries"]),
                "retailMarketValueComputed": False,
                "output": str(args.output),
            }
        )
    )


if __name__ == "__main__":
    main()
