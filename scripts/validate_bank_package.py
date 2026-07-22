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

try:
    from bank_register_parity import validate_register_parity
except ModuleNotFoundError:  # Support importing this file as scripts.validate_bank_package.
    from scripts.bank_register_parity import validate_register_parity


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "site" / "data" / "bank-package-manifest.json"
CHANGELOG_PATH = ROOT / "site" / "data" / "changelog.json"
REGISTER_CSV_PATH = ROOT / "site" / "data" / "bank-evidence-register.csv"
EN_REGISTER_CSV_PATH = ROOT / "site" / "data" / "bank-evidence-register-en.csv"

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
EN_REGISTER_HEADERS = [
    "Claim",
    "Slide/section",
    "Evidence",
    "Source",
    "Date",
    "Calculation method",
    "Assumptions",
    "Confidence",
    "Gaps / additional evidence needed",
]
EN_ALLOWED_STATUSES = {"Confirmed", "Supported", "Assumption", "Missing"}
EXPECTED_INPUTS = {
    "site/data/atlas.json",
    "site/data/changelog.json",
    "site/data/market-values.json",
    "site/data/patent-history.json",
    "source/bank-evidence-register-en.json",
    "source/bank-deck-en-translations.json",
    "source/bank-package-en-lock.json",
}
EXPECTED_ARTIFACTS = {
    "short-deck-fi": {
        "kind": "pptx",
        "language": "fi",
        "path": "downloads/pixan-bank-deck-short-fi.pptx",
        "slideCount": 6,
    },
    "medium-deck-fi": {
        "kind": "pptx",
        "language": "fi",
        "path": "downloads/pixan-bank-deck-medium-fi.pptx",
        "slideCount": 12,
    },
    "large-deck-fi": {
        "kind": "pptx",
        "language": "fi",
        "path": "downloads/pixan-bank-deck-large-fi.pptx",
        "slideCount": 30,
    },
    "evidence-register-fi": {
        "kind": "xlsx",
        "language": "fi",
        "path": "downloads/pixan-bank-evidence-register-fi.xlsx",
    },
    "short-deck-en": {
        "kind": "pptx",
        "language": "en",
        "path": "downloads/pixan-bank-deck-short-en.pptx",
        "slideCount": 6,
    },
    "medium-deck-en": {
        "kind": "pptx",
        "language": "en",
        "path": "downloads/pixan-bank-deck-medium-en.pptx",
        "slideCount": 12,
    },
    "large-deck-en": {
        "kind": "pptx",
        "language": "en",
        "path": "downloads/pixan-bank-deck-large-en.pptx",
        "slideCount": 30,
    },
    "evidence-register-en": {
        "kind": "xlsx",
        "language": "en",
        "path": "downloads/pixan-bank-evidence-register-en.xlsx",
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
EN_MEDIUM_SECTION_TITLES = [
    "financing thesis",
    "problem",
    "patented solution",
    "patent and ip status",
    "technical differentiation",
    "market size and scope",
    "customers and purchase rationale",
    "competition and alternatives",
    "validation and current evidence",
    "commercialisation model",
    "financial model and sensitivities",
    "risks, controls and next steps",
]
FORBIDDEN_TEXT = (
    "/users/",
    "\\users\\",
    "file://",
    "tmp/pdfs",
)
PRIVATE_IDENTIFIER_FINGERPRINTS = frozenset(
    {
        (7, "46d7415f6182ece9e933e8e9f780957e449361e0dbe10e34f46c186cad3382a1"),
        (7, "f910f0bbe95037851d18ca33b91ee7fc9f334c6cfcd02deaf66af4501c8a884c"),
        (9, "7e6578c2e34b53136741c6efe7799a2dce739651c22404a7894b48d42aa88b41"),
        (13, "933536a17b00f1b39ba9d3585427bd7232d44960ab35754318c1da8e4cf6c5be"),
        (25, "40f45830e7e3e21d88245728fe87f76b2e8919543a502aad248a465487cacee3"),
    }
)
FORBIDDEN_ARCHIVE_PARTS = (
    "vbaproject",
    "/embeddings/",
    "/externalLinks/",
    "/oleObject",
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
    normalised = re.sub(r"[^a-z0-9]+", "", lowered)
    for length, expected in PRIVATE_IDENTIFIER_FINGERPRINTS:
        if any(
            hashlib.sha256(normalised[index:index + length].encode("utf-8")).hexdigest() == expected
            for index in range(max(0, len(normalised) - length + 1))
        ):
            errors.append(f"{label}: forbidden private identifier fingerprint")
            break


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


def validate_external_https_target(label: str, target: str, errors: list[str]) -> None:
    """Require the entire external relationship target to be a safe HTTPS URL."""

    if target != target.strip() or any(character.isspace() or ord(character) < 32 for character in target):
        errors.append(f"{label}: external hyperlink target contains whitespace/control characters")
        return
    if re.search(r"%(?![0-9A-Fa-f]{2})", target):
        errors.append(f"{label}: external hyperlink target contains malformed percent-encoding")
        return
    try:
        parsed = urlparse(target)
        # Accessing port forces urllib to reject malformed or out-of-range ports.
        _ = parsed.port
    except ValueError:
        errors.append(f"{label}: external hyperlink target is malformed")
        return
    if parsed.scheme.casefold() != "https" or not parsed.netloc or not parsed.hostname:
        errors.append(f"{label}: external hyperlink target must be an absolute HTTPS URL")
        return
    if parsed.username is not None or parsed.password is not None:
        errors.append(f"{label}: external hyperlink target must not contain credentials")
    if "\\" in target:
        errors.append(f"{label}: external hyperlink target must not contain backslashes or UNC syntax")
    query_keys = {key.casefold() for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
    if query_keys & SENSITIVE_QUERY_KEYS:
        errors.append(f"{label}: external hyperlink target contains a sensitive query key")
    validate_forbidden_terms(label, target, errors)


def validate_ooxml(
    path: Path,
    errors: list[str],
    *,
    require_deterministic_zip: bool,
    allow_empty_notes: bool,
) -> str:
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
            if require_deterministic_zip:
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
                    is_notes_part = "/notesslides/" in lowered_name or "/notesmasters/" in lowered_name
                    if is_notes_part:
                        if not allow_empty_notes:
                            errors.append(f"{label}: notes parts are forbidden ({info.filename})")
                        elif info.filename.endswith(".xml"):
                            try:
                                note_root = ET.fromstring(payload)
                            except ET.ParseError:
                                errors.append(f"{label}: malformed notes part {info.filename}")
                            else:
                                note_text = [
                                    str(element.text or "").strip()
                                    for element in note_root.iter()
                                    if element.tag.endswith("}t") and str(element.text or "").strip()
                                ]
                                if note_text:
                                    errors.append(f"{label}: notes part contains text ({info.filename})")
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
                            else:
                                validate_external_https_target(f"{label} relationship", target, errors)
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


def read_register_csv(
    path: Path,
    headers: list[str],
    allowed_statuses: set[str],
    errors: list[str],
) -> list[list[str]]:
    label = str(path.relative_to(ROOT))
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle))
    except OSError as error:
        errors.append(f"{label}: {error}")
        return []
    if not rows or rows[0] != headers:
        errors.append(f"{label} has incorrect headers")
        return []
    data_rows = [[str(value) for value in row] for row in rows[1:] if any(str(value).strip() for value in row)]
    for index, row in enumerate(data_rows, start=2):
        if len(row) != len(headers):
            errors.append(f"{label} row {index} has {len(row)} columns")
            continue
        if row[7] not in allowed_statuses:
            errors.append(f"{label} row {index} has invalid status {row[7]!r}")
        validate_text(f"{label} row {index}", "\n".join(row), errors)
    if not data_rows:
        errors.append(f"{label} must contain evidence rows")
    elif {row[7] for row in data_rows if len(row) == len(headers)} != allowed_statuses:
        errors.append(f"{label} must visibly use all four evidence classifications")
    return data_rows


def validate_workbook(
    path: Path,
    csv_rows: list[list[str]],
    expected_headers: list[str],
    errors: list[str],
) -> int:
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
    if headers != expected_headers:
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
        "languages",
        "publicBoundary",
        "inputs",
        "artifacts",
    }
    if not isinstance(manifest, dict) or set(manifest) != expected_keys:
        errors.append("bank-package-manifest.json has an unexpected schema")
        return
    if manifest.get("schemaVersion") != 2 or manifest.get("generatedFromPublicDataOnly") is not True:
        errors.append("manifest must declare schemaVersion 2 and public-data-only generation")
    if manifest.get("languages") != ["en", "fi"]:
        errors.append("manifest languages must be exactly en and fi")
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
        errors.append("manifest artifacts must contain exactly the eight approved downloads")

    csv_rows_by_language = {
        "fi": read_register_csv(REGISTER_CSV_PATH, REGISTER_HEADERS, ALLOWED_STATUSES, errors),
        "en": read_register_csv(EN_REGISTER_CSV_PATH, EN_REGISTER_HEADERS, EN_ALLOWED_STATUSES, errors),
    }
    errors.extend(
        validate_register_parity(
            csv_rows_by_language["fi"],
            csv_rows_by_language["en"],
        )
    )
    headers_by_language = {"fi": REGISTER_HEADERS, "en": EN_REGISTER_HEADERS}
    for artifact_id, expected in EXPECTED_ARTIFACTS.items():
        item = artifact_by_id.get(artifact_id)
        if not isinstance(item, dict):
            continue
        required = {"id", "kind", "language", "titleFi", "titleEn", "fileName", "path", "sha256", "bytes"}
        if expected["kind"] == "pptx":
            required.add("slideCount")
        else:
            required.add("rowCount")
        if set(item) != required:
            errors.append(f"manifest artifact {artifact_id} has an unexpected schema")
        if (
            item.get("kind") != expected["kind"]
            or item.get("language") != expected["language"]
            or item.get("path") != expected["path"]
        ):
            errors.append(f"manifest artifact {artifact_id} kind/language/path differs from allowlist")
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
        is_english = expected["language"] == "en"
        validate_ooxml(
            path,
            errors,
            require_deterministic_zip=not is_english,
            allow_empty_notes=is_english and expected["kind"] == "pptx",
        )
        if expected["kind"] == "pptx":
            texts = slide_texts(path, errors)
            if len(texts) != expected["slideCount"] or item.get("slideCount") != expected["slideCount"]:
                errors.append(f"{relative}: expected exactly {expected['slideCount']} slides")
            for index, text in enumerate(texts, start=1):
                if not text.strip():
                    errors.append(f"{relative}: slide {index} has no readable text")
                validate_text(f"{relative} slide {index}", text, errors)
            combined = "\n".join(texts).casefold()
            expected_boundary = "independent public evidence" if is_english else "julkinen riippumaton"
            if expected_boundary not in combined:
                errors.append(f"{relative}: public-boundary disclosure is missing")
            if artifact_id in {"medium-deck-fi", "medium-deck-en"} and len(texts) == 12:
                titles = EN_MEDIUM_SECTION_TITLES if is_english else MEDIUM_SECTION_TITLES
                for index, expected_title in enumerate(titles):
                    normalized = " ".join(texts[index].casefold().split())
                    if expected_title not in normalized:
                        errors.append(
                            f"{relative}: slide {index + 1} lacks requested section title {expected_title!r}"
                        )
        else:
            csv_rows = csv_rows_by_language[expected["language"]]
            row_count = validate_workbook(path, csv_rows, headers_by_language[expected["language"]], errors)
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
        "Validated bilingual public bank package: English and Finnish 6/12/30-slide decks, "
        "Evidence Register parity, release-lock and SHA-256 integrity, safe OOXML and public-data-only boundary."
    )


if __name__ == "__main__":
    main()
