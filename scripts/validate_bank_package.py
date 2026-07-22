#!/usr/bin/env python3
"""Fail-closed validation for the public, generated lender package."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse
from xml.etree import ElementTree as ET

from openpyxl import load_workbook
from pptx import Presentation


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "site" / "data" / "bank-package-manifest.json"
CHANGELOG_PATH = ROOT / "site" / "data" / "changelog.json"
REGISTER_CSV_PATH = ROOT / "site" / "data" / "bank-evidence-register.csv"

REGISTER_HEADERS = [
    "Väite",
    "Dia/osio",
    "Todiste",
    "Lähde",
    "Päivämäärä",
    "Laskentatapa",
    "Oletukset",
    "Luottamustaso",
    "Puutteet / tarvittava lisänäyttö",
]
ALLOWED_STATUSES = {"Vahvistettu", "Tuettu", "Oletus", "Puuttuu"}
EXPECTED_INPUTS = {
    "site/data/atlas.json",
    "site/data/changelog.json",
    "site/data/market-values.json",
    "site/data/patent-history.json",
}
EXPECTED_ARTIFACTS = {
    "short-deck": {
        "kind": "pptx",
        "path": "downloads/pixan-bank-deck-short-fi.pptx",
        "slideCount": 6,
    },
    "medium-deck": {
        "kind": "pptx",
        "path": "downloads/pixan-bank-deck-medium-fi.pptx",
        "slideCount": 12,
    },
    "large-deck": {
        "kind": "pptx",
        "path": "downloads/pixan-bank-deck-large-fi.pptx",
        "slideCount": 30,
    },
    "evidence-register": {
        "kind": "xlsx",
        "path": "downloads/pixan-bank-evidence-register-fi.xlsx",
    },
}
MEDIUM_SECTION_TITLES = [
    "rahoitusteesi",
    "ongelma",
    "patentoitu ratkaisu",
    "patentti ja ip-status",
    "tekninen erottautuminen",
    "markkinan koko ja rajaus",
    "asiakkaat ja ostoperuste",
    "kilpailu ja vaihtoehdot",
    "validointi ja nykyinen näyttö",
    "kaupallistamismalli",
    "taloudellinen malli ja herkkyydet",
    "riskit, hallintatoimet ja seuraavat vaiheet",
]
FORBIDDEN_TEXT = (
    "/users/",
    "\\users\\",
    "file://",
    "jounirautio",
    "rozella",
    "ai-yield",
    "ai yield",
    "peak portfolio",
    "blackrock",
    "black rock",
    "tmp/pdfs",
    "pankkirahoituspaketti-2026",
)
FORBIDDEN_ARCHIVE_PARTS = (
    "vbaproject",
    "/embeddings/",
    "/externalLinks/",
    "/oleObject",
    "/notesMasters/",
    "/notesSlides/",
    "/comments",
    "connections.xml",
)
SENSITIVE_QUERY_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "authorization",
    "key",
    "password",
    "secret",
    "sig",
    "signature",
    "token",
    "x-amz-credential",
    "x-amz-signature",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read {path.relative_to(ROOT)}: {error}") from error


def strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def validate_forbidden_terms(label: str, text: str, errors: list[str]) -> None:
    lowered = text.casefold()
    for phrase in FORBIDDEN_TEXT:
        if phrase in lowered:
            errors.append(f"{label}: forbidden private/local term {phrase!r}")


def validate_text(label: str, text: str, errors: list[str]) -> None:
    validate_forbidden_terms(label, text, errors)
    for match in re.finditer(r"https?://[^\s<>\"']+", text):
        parsed = urlparse(match.group(0).rstrip(".,);]"))
        if parsed.scheme != "https" or not parsed.netloc:
            errors.append(f"{label}: only public HTTPS links are allowed")
            continue
        query_keys = {key.casefold() for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
        if query_keys & SENSITIVE_QUERY_KEYS:
            errors.append(f"{label}: URL contains a sensitive query key")


def validate_ooxml(path: Path, errors: list[str]) -> str:
    label = str(path.relative_to(ROOT))
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if not names or "[Content_Types].xml" not in names:
                errors.append(f"{label}: invalid OOXML package")
                return ""
            if len(names) != len(set(names)):
                errors.append(f"{label}: duplicate ZIP entries")
            if any(name.startswith("/") or ".." in Path(name).parts for name in names):
                errors.append(f"{label}: unsafe ZIP path")
            if names != sorted(names):
                errors.append(f"{label}: ZIP entries are not deterministically ordered")
            timestamps = {info.date_time for info in infos}
            if len(timestamps) != 1:
                errors.append(f"{label}: ZIP timestamps are not normalized")

            extracted_text: list[str] = []
            for info in infos:
                lowered_name = f"/{info.filename}".casefold()
                if any(part.casefold() in lowered_name for part in FORBIDDEN_ARCHIVE_PARTS):
                    errors.append(f"{label}: forbidden OOXML part {info.filename}")
                if info.file_size > 20 * 1024 * 1024:
                    errors.append(f"{label}: oversized OOXML part {info.filename}")
                if info.filename.endswith((".xml", ".rels")):
                    payload = archive.read(info).decode("utf-8", errors="replace")
                    extracted_text.append(payload)
                    if info.filename.endswith(".rels"):
                        try:
                            root = ET.fromstring(payload)
                        except ET.ParseError:
                            errors.append(f"{label}: malformed relationship part {info.filename}")
                            continue
                        for relation in root:
                            if relation.attrib.get("TargetMode") != "External":
                                continue
                            target = relation.attrib.get("Target", "")
                            relation_type = relation.attrib.get("Type", "").casefold()
                            if "hyperlink" not in relation_type:
                                errors.append(f"{label}: external non-hyperlink relationship is forbidden")
                            validate_text(f"{label} relationship", target, errors)
            combined = "\n".join(extracted_text)
            # Namespace declarations and relationship type identifiers use HTTP
            # URIs by OOXML design; URL policy applies only to visible content
            # and explicit TargetMode=External relationships.
            validate_forbidden_terms(label, combined, errors)
            return combined
    except (OSError, zipfile.BadZipFile) as error:
        errors.append(f"{label}: unreadable OOXML package: {error}")
        return ""


def slide_texts(path: Path, errors: list[str]) -> list[str]:
    try:
        presentation = Presentation(path)
    except Exception as error:  # python-pptx exposes parser-specific exceptions
        errors.append(f"{path.relative_to(ROOT)}: cannot parse presentation: {error}")
        return []
    output: list[str] = []
    for slide in presentation.slides:
        chunks: list[str] = []
        for shape in slide.shapes:
            if getattr(shape, "has_text_frame", False):
                chunks.append(shape.text)
        output.append("\n".join(chunks))
    return output


def read_register_csv(errors: list[str]) -> list[list[str]]:
    try:
        with REGISTER_CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle))
    except OSError as error:
        errors.append(f"site/data/bank-evidence-register.csv: {error}")
        return []
    if not rows or rows[0] != REGISTER_HEADERS:
        errors.append("bank-evidence-register.csv has incorrect headers")
        return []
    data_rows = [[str(value) for value in row] for row in rows[1:] if any(str(value).strip() for value in row)]
    for index, row in enumerate(data_rows, start=2):
        if len(row) != len(REGISTER_HEADERS):
            errors.append(f"bank-evidence-register.csv row {index} has {len(row)} columns")
            continue
        if row[7] not in ALLOWED_STATUSES:
            errors.append(f"bank-evidence-register.csv row {index} has invalid status {row[7]!r}")
        validate_text(f"bank-evidence-register.csv row {index}", "\n".join(row), errors)
    if not data_rows:
        errors.append("bank-evidence-register.csv must contain evidence rows")
    elif {row[7] for row in data_rows if len(row) == 9} != ALLOWED_STATUSES:
        errors.append("Evidence Register must visibly use all four evidence classifications")
    return data_rows


def validate_workbook(path: Path, csv_rows: list[list[str]], errors: list[str]) -> int:
    label = str(path.relative_to(ROOT))
    try:
        workbook = load_workbook(path, data_only=False, read_only=False)
    except Exception as error:
        errors.append(f"{label}: cannot parse workbook: {error}")
        return 0
    if "Evidence Register" not in workbook.sheetnames:
        errors.append(f"{label}: missing Evidence Register sheet")
        return 0
    for sheet in workbook.worksheets:
        if sheet.sheet_state != "visible":
            errors.append(f"{label}: hidden worksheets are forbidden ({sheet.title})")
        for row in sheet.iter_rows():
            for cell in row:
                if cell.comment is not None:
                    errors.append(f"{label}: comments are forbidden ({sheet.title}!{cell.coordinate})")
                if isinstance(cell.value, str):
                    validate_text(f"{label} {sheet.title}!{cell.coordinate}", cell.value, errors)
                    if cell.value.startswith("=") and "[" in cell.value:
                        errors.append(f"{label}: external workbook formula is forbidden")
                if cell.hyperlink is not None:
                    validate_text(f"{label} hyperlink", str(cell.hyperlink.target), errors)
    sheet = workbook["Evidence Register"]
    headers = [str(sheet.cell(1, column).value or "") for column in range(1, 10)]
    if headers != REGISTER_HEADERS:
        errors.append(f"{label}: Evidence Register headers are incorrect")
    workbook_rows: list[list[str]] = []
    for values in sheet.iter_rows(min_row=2, max_col=9, values_only=True):
        row = ["" if value is None else str(value) for value in values]
        if any(value.strip() for value in row):
            workbook_rows.append(row)
    if workbook_rows != csv_rows:
        errors.append(f"{label}: Evidence Register rows differ from the public CSV")
    return len(workbook_rows)


def validate_manifest(errors: list[str]) -> None:
    try:
        manifest = load_json(MANIFEST_PATH)
        changelog = load_json(CHANGELOG_PATH)
    except ValueError as error:
        errors.append(str(error))
        return
    expected_keys = {
        "schemaVersion",
        "generatedFromPublicDataOnly",
        "release",
        "asOf",
        "language",
        "publicBoundary",
        "inputs",
        "artifacts",
    }
    if not isinstance(manifest, dict) or set(manifest) != expected_keys:
        errors.append("bank-package-manifest.json has an unexpected schema")
        return
    if manifest.get("schemaVersion") != 1 or manifest.get("generatedFromPublicDataOnly") is not True:
        errors.append("manifest must declare schemaVersion 1 and public-data-only generation")
    if manifest.get("language") != "fi":
        errors.append("manifest language must be fi")
    latest_release = changelog.get("releases", [{}])[0]
    expected_release = {
        key: latest_release.get(key) for key in ("id", "version", "publishedAt")
    }
    if manifest.get("release") != expected_release:
        errors.append("manifest release must match the newest public changelog release")
    if manifest.get("asOf") != changelog.get("asOf"):
        errors.append("manifest asOf must match the public changelog")
    boundary = manifest.get("publicBoundary")
    if not isinstance(boundary, dict) or set(boundary) != {"en", "fi"}:
        errors.append("manifest publicBoundary must contain exactly en and fi")
    else:
        boundary_text = " ".join(str(value) for value in boundary.values())
        validate_text("manifest public boundary", boundary_text, errors)
        if "public" not in str(boundary.get("en", "")).casefold() or "julk" not in str(boundary.get("fi", "")).casefold():
            errors.append("manifest must state the public-data boundary in both languages")

    inputs = manifest.get("inputs")
    if not isinstance(inputs, list):
        errors.append("manifest inputs must be an array")
        inputs = []
    input_by_path = {
        item.get("path"): item for item in inputs if isinstance(item, dict) and set(item) == {"path", "sha256"}
    }
    if set(input_by_path) != EXPECTED_INPUTS or len(input_by_path) != len(inputs):
        errors.append("manifest inputs must be the exact reviewed public-data allowlist")
    for relative, item in input_by_path.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"manifest input is missing: {relative}")
        elif item.get("sha256") != sha256(path):
            errors.append(f"manifest input hash differs: {relative}")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("manifest artifacts must be an array")
        artifacts = []
    artifact_by_id = {
        item.get("id"): item
        for item in artifacts
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if set(artifact_by_id) != set(EXPECTED_ARTIFACTS) or len(artifact_by_id) != len(artifacts):
        errors.append("manifest artifacts must contain exactly the four approved downloads")

    csv_rows = read_register_csv(errors)
    for artifact_id, expected in EXPECTED_ARTIFACTS.items():
        item = artifact_by_id.get(artifact_id)
        if not isinstance(item, dict):
            continue
        required = {"id", "kind", "titleFi", "titleEn", "fileName", "path", "sha256", "bytes"}
        if expected["kind"] == "pptx":
            required.add("slideCount")
        else:
            required.add("rowCount")
        if set(item) != required:
            errors.append(f"manifest artifact {artifact_id} has an unexpected schema")
        if item.get("kind") != expected["kind"] or item.get("path") != expected["path"]:
            errors.append(f"manifest artifact {artifact_id} kind/path differs from allowlist")
        if item.get("fileName") != Path(expected["path"]).name:
            errors.append(f"manifest artifact {artifact_id} filename differs from path")
        if not str(item.get("titleFi", "")).strip() or not str(item.get("titleEn", "")).strip():
            errors.append(f"manifest artifact {artifact_id} requires bilingual titles")
        relative = str(item.get("path", ""))
        path = ROOT / "site" / relative
        if path.parent != ROOT / "site" / "downloads" or not path.is_file():
            errors.append(f"download missing or outside allowlist: {relative}")
            continue
        if path.stat().st_size > 12 * 1024 * 1024:
            errors.append(f"{relative}: file exceeds 12 MiB")
        if item.get("bytes") != path.stat().st_size:
            errors.append(f"{relative}: manifest byte count differs")
        if not SHA256_RE.fullmatch(str(item.get("sha256", ""))) or item.get("sha256") != sha256(path):
            errors.append(f"{relative}: manifest SHA-256 differs")
        validate_ooxml(path, errors)
        if expected["kind"] == "pptx":
            texts = slide_texts(path, errors)
            if len(texts) != expected["slideCount"] or item.get("slideCount") != expected["slideCount"]:
                errors.append(f"{relative}: expected exactly {expected['slideCount']} slides")
            for index, text in enumerate(texts, start=1):
                if not text.strip():
                    errors.append(f"{relative}: slide {index} has no readable text")
                validate_text(f"{relative} slide {index}", text, errors)
            if artifact_id == "medium-deck" and len(texts) == 12:
                for index, expected_title in enumerate(MEDIUM_SECTION_TITLES):
                    normalized = " ".join(texts[index].casefold().split())
                    if expected_title not in normalized:
                        errors.append(
                            f"{relative}: slide {index + 1} lacks requested section title {expected_title!r}"
                        )
        else:
            row_count = validate_workbook(path, csv_rows, errors)
            if item.get("rowCount") != row_count or row_count != len(csv_rows):
                errors.append(f"{relative}: manifest/workbook/CSV row counts differ")


def main() -> None:
    errors: list[str] = []
    validate_manifest(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Bank-package validation failed with {len(errors)} error(s).", file=sys.stderr)
        raise SystemExit(1)
    print(
        "Validated public bank package: 6/12/30-slide decks, Evidence Register parity, "
        "release and SHA-256 manifest integrity, deterministic OOXML and public-data-only boundary."
    )


if __name__ == "__main__":
    main()
