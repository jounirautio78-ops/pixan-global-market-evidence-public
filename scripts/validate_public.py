#!/usr/bin/env python3
"""Validate the generated public atlas and fail closed on unsafe output."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlparse

from build_atlas import (
    ABSOLUTE_PATH_RE,
    ALLOWED_EMAIL,
    ALLOWED_PHONE_DIGITS,
    COUNTRY_CATALOG,
    COUNTRY_ISO2,
    DIMENSIONS,
    DIMENSION_STATUSES,
    EMAIL_RE,
    GRADE_BY_CLAIM_TYPE,
    LEGACY_COUNTRY_TO_ISO2,
    OUTPUT_DIR,
    PLUS_PHONE_RE,
    PUBLIC_BASELINE_PATH,
    ROOT,
    SECRET_ASSIGNMENT_RE,
    UPSTREAM_METADATA_PATH,
    best_evidence,
    coverage_percent,
    normalize_phone,
)


ATLAS_PATH = OUTPUT_DIR / "atlas.json"
COUNTRIES_CSV_PATH = OUTPUT_DIR / "countries.csv"
EVIDENCE_CSV_PATH = OUTPUT_DIR / "evidence.csv"
CURATED_PATH = ROOT / "source" / "curated.json"
UPSTREAM_SHA_PATH = ROOT / "source" / "marnet-upstream.sha256"
FORBIDDEN_RAW_PATH = ROOT / "source" / "marnet-dashboard.json"

REQUIRED_TOP_LEVEL_KEYS = {
    "meta",
    "summary",
    "countries",
    "evidence",
    "legal",
    "methodology",
    "submission",
    "readiness",
    "sourceAttribution",
}
ALLOWED_REGIONS = {"Africa", "Americas", "Asia", "Europe", "Oceania"}
PHONE_URI_RE = re.compile(r"(?i)(?:wa\.me/|tel:)(\+?[0-9][0-9 .()\-/]{6,}[0-9])")
PHONE_CONTEXT_RE = re.compile(
    r"(?i)\b(?:phone|mobile|whatsapp|puhelin|matkapuhelin|tel)\b[^\n]{0,20}?"
    r"(\+?[0-9][0-9 .()\-/]{6,}[0-9])"
)
PEM_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*(?:PRIVATE KEY|CERTIFICATE)-----")
FORBIDDEN_OPERATIONAL_PHRASES = (
    "complete private attachment package",
    "private attachment",
    "send the complete",
    "action-time confirmation",
)
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
BASELINE_TOP_LEVEL_KEYS = {"schemaVersion", "countries", "evidence"}
BASELINE_COUNTRY_KEYS = {"sourceName", "sourceUrls"}
BASELINE_EVIDENCE_KEYS = {"title", "url", "grade"}
METADATA_KEYS = {
    "schemaVersion",
    "repository",
    "branch",
    "path",
    "commit",
    "blob",
    "sha256",
    "size",
    "immutableUrl",
    "snapshotMetadataTimestamp",
    "verifiedAt",
    "publicBaseline",
}
PUBLIC_BASELINE_METADATA_KEYS = {"path", "sha256", "size", "countries", "evidence", "policy"}
SENSITIVE_QUERY_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "auth",
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
EXPECTED_SITE_FILES = {
    "site/index.html",
    "site/review.html",
    "site/assets/app.js",
    "site/assets/review.js",
    "site/assets/styles.css",
    "site/assets/favicon.svg",
    "site/data/atlas.json",
    "site/data/countries.csv",
    "site/data/evidence.csv",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def walk_strings(value: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield from walk_strings(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from walk_strings(nested, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def is_https_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        return False
    query_keys = {key.lower() for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
    return not (query_keys & SENSITIVE_QUERY_KEYS)


def scan_public_text(label: str, value: Any, errors: list[str]) -> None:
    for path, text in walk_strings(value):
        for match in EMAIL_RE.finditer(text):
            if match.group(0).lower() != ALLOWED_EMAIL:
                errors.append(f"{label}{path}: disallowed email {match.group(0)!r}")

        for match in PLUS_PHONE_RE.finditer(text):
            if normalize_phone(match.group(0)) != ALLOWED_PHONE_DIGITS:
                errors.append(f"{label}{path}: disallowed phone {match.group(0)!r}")
        for pattern in (PHONE_URI_RE, PHONE_CONTEXT_RE):
            for match in pattern.finditer(text):
                if normalize_phone(match.group(1)) != ALLOWED_PHONE_DIGITS:
                    errors.append(f"{label}{path}: disallowed phone {match.group(1)!r}")

        if ABSOLUTE_PATH_RE.search(text):
            errors.append(f"{label}{path}: absolute/local path is forbidden")
        if SECRET_ASSIGNMENT_RE.search(text) or PEM_RE.search(text):
            errors.append(f"{label}{path}: secret-like material is forbidden")
        lowered = text.lower()
        for phrase in FORBIDDEN_OPERATIONAL_PHRASES:
            if phrase in lowered:
                errors.append(f"{label}{path}: private operational instruction is forbidden")


def validate_meta(atlas: dict[str, Any], curated: dict[str, Any], errors: list[str]) -> None:
    meta = atlas.get("meta", {})
    disclaimer = str(meta.get("disclaimer", "")).lower()
    independence = str(meta.get("independenceStatement", "")).lower()
    if "ei ole" not in disclaimer or "oikeudellinen" not in disclaimer or "arvio" not in disclaimer:
        errors.append("meta.disclaimer must independently disclaim legal and valuation conclusions")
    if "ei edusta pixan oy:n virallista kantaa" not in disclaimer:
        errors.append("meta.disclaimer must state that the atlas is not Pixan Oy's official position")
    if "riippum" not in disclaimer + independence or "migraatio" not in independence:
        errors.append("meta.independenceStatement must distinguish migration from independent verification")
    curated_meta = curated.get("meta", {})
    expected_commit = curated_meta.get("legacySourceCommit")
    if not isinstance(expected_commit, str) or not SHA1_RE.fullmatch(expected_commit):
        errors.append("curated meta.legacySourceCommit must be a full lowercase commit SHA")
    if meta.get("legacySourceCommit") != expected_commit:
        errors.append("atlas meta.legacySourceCommit must match curated metadata")
    reviewed_at = curated_meta.get("reviewedAt")
    if not isinstance(reviewed_at, str) or not RFC3339_UTC_RE.fullmatch(reviewed_at):
        errors.append("curated meta.reviewedAt must be an RFC 3339 UTC timestamp")
    elif meta.get("generatedAt") != reviewed_at:
        errors.append("atlas meta.generatedAt must equal curated meta.reviewedAt for a deterministic build")
    else:
        try:
            if date.fromisoformat(str(curated_meta.get("asOf"))) > datetime.fromisoformat(reviewed_at[:-1] + "+00:00").date():
                errors.append("curated meta.asOf cannot be later than meta.reviewedAt")
        except ValueError:
            errors.append("curated meta.asOf must be an ISO date")


def validate_source_inputs(
    curated: dict[str, Any],
    baseline: dict[str, Any],
    metadata: dict[str, Any],
    errors: list[str],
) -> None:
    if FORBIDDEN_RAW_PATH.exists():
        errors.append("source/marnet-dashboard.json must not be stored in the public repository")

    if set(baseline) != BASELINE_TOP_LEVEL_KEYS or baseline.get("schemaVersion") != 1:
        errors.append("Marnet public baseline must use exactly the approved schemaVersion 1 top-level keys")

    countries = baseline.get("countries")
    if not isinstance(countries, list):
        errors.append("Marnet public baseline countries must be an array")
        countries = []
    country_names: list[str] = []
    for index, row in enumerate(countries):
        path = f"baseline.countries[{index}]"
        if not isinstance(row, dict) or set(row) != BASELINE_COUNTRY_KEYS:
            errors.append(f"{path} must contain exactly sourceName and sourceUrls")
            continue
        source_name = row.get("sourceName")
        if not isinstance(source_name, str) or not source_name:
            errors.append(f"{path}.sourceName must be a non-empty string")
        else:
            country_names.append(source_name)
        source_urls = row.get("sourceUrls")
        if not isinstance(source_urls, list):
            errors.append(f"{path}.sourceUrls must be an array")
            continue
        if source_urls != sorted(set(source_urls)):
            errors.append(f"{path}.sourceUrls must be sorted and unique")
        for source_url in source_urls:
            if not is_https_url(source_url):
                errors.append(f"{path}.sourceUrls contains a non-public HTTPS URL")
    expected_country_names = set(LEGACY_COUNTRY_TO_ISO2)
    if len(country_names) != len(set(country_names)) or set(country_names) != expected_country_names:
        errors.append("Marnet public baseline country identifiers must match the exact 23-country allowlist")

    evidence = baseline.get("evidence")
    if not isinstance(evidence, list):
        errors.append("Marnet public baseline evidence must be an array")
        evidence = []
    evidence_titles: list[str] = []
    for index, row in enumerate(evidence):
        path = f"baseline.evidence[{index}]"
        if not isinstance(row, dict) or set(row) != BASELINE_EVIDENCE_KEYS:
            errors.append(f"{path} must contain exactly title, url, and grade")
            continue
        title = row.get("title")
        if not isinstance(title, str) or not title:
            errors.append(f"{path}.title must be a non-empty string")
        else:
            evidence_titles.append(title)
        if not is_https_url(row.get("url")):
            errors.append(f"{path}.url must be a public HTTPS URL")
        if row.get("grade") not in {"A", "B", "C", "D"}:
            errors.append(f"{path}.grade must be A, B, C, or D")
    expected_titles = {row.get("title") for row in curated.get("marnetEvidenceWhitelist", [])}
    if len(evidence_titles) != len(set(evidence_titles)) or set(evidence_titles) != expected_titles:
        errors.append("Marnet public baseline evidence titles must match the exact curated allowlist")

    if set(metadata) != METADATA_KEYS or metadata.get("schemaVersion") != 1:
        errors.append("Marnet upstream metadata must use exactly the approved schemaVersion 1 keys")
    if metadata.get("repository") != "marnet-collab/pixan-evidence-center":
        errors.append("Marnet upstream repository metadata is invalid")
    if metadata.get("branch") != "main" or metadata.get("path") != "data/dashboard.json":
        errors.append("Marnet upstream branch/path metadata is invalid")
    for key in ("commit", "blob"):
        if not isinstance(metadata.get(key), str) or not SHA1_RE.fullmatch(metadata[key]):
            errors.append(f"Marnet upstream metadata {key} must be a full lowercase SHA")
    if not isinstance(metadata.get("sha256"), str) or not SHA256_RE.fullmatch(metadata["sha256"]):
        errors.append("Marnet upstream metadata sha256 is invalid")
    if not isinstance(metadata.get("size"), int) or metadata["size"] <= 0:
        errors.append("Marnet upstream metadata size must be a positive integer")
    expected_url = (
        f"https://raw.githubusercontent.com/{metadata.get('repository')}/"
        f"{metadata.get('commit')}/{metadata.get('path')}"
    )
    if metadata.get("immutableUrl") != expected_url:
        errors.append("Marnet upstream immutableUrl must be derived from repository, commit, and path")
    if metadata.get("commit") != curated.get("meta", {}).get("legacySourceCommit"):
        errors.append("Marnet upstream metadata commit must match curated metadata")
    verified_at = metadata.get("verifiedAt")
    if not isinstance(verified_at, str) or not RFC3339_UTC_RE.fullmatch(verified_at):
        errors.append("Marnet upstream metadata verifiedAt must be an RFC 3339 UTC timestamp")

    public_metadata = metadata.get("publicBaseline")
    if not isinstance(public_metadata, dict) or set(public_metadata) != PUBLIC_BASELINE_METADATA_KEYS:
        errors.append("Marnet public baseline metadata must use exactly the approved keys")
        public_metadata = {}
    baseline_bytes = PUBLIC_BASELINE_PATH.read_bytes()
    baseline_sha = hashlib.sha256(baseline_bytes).hexdigest()
    if public_metadata.get("path") != "source/marnet-public-baseline.json":
        errors.append("Marnet public baseline metadata path is invalid")
    if public_metadata.get("sha256") != baseline_sha or public_metadata.get("size") != len(baseline_bytes):
        errors.append("Marnet public baseline does not match its recorded SHA-256 and byte size")
    if public_metadata.get("countries") != len(countries) or public_metadata.get("evidence") != len(evidence):
        errors.append("Marnet public baseline metadata counts do not match the baseline")
    sidecar = UPSTREAM_SHA_PATH.read_text(encoding="utf-8")
    expected_sidecar = f"{metadata.get('sha256')}  {metadata.get('path')}\n"
    if sidecar != expected_sidecar:
        errors.append("source/marnet-upstream.sha256 does not match the upstream metadata")

    for path, text in walk_strings(baseline):
        if EMAIL_RE.search(text) or PLUS_PHONE_RE.search(text):
            errors.append(f"baseline{path}: contact details are forbidden in the redacted source baseline")


def validate_submission(atlas: dict[str, Any], errors: list[str]) -> None:
    submission = atlas.get("submission", {})
    expected = {
        "dropboxRequestUrl": "https://www.dropbox.com/request/es3w836bdnpbsn4loq3d",
        "whatsapp": "+358400355544",
        "whatsappUrl": "https://wa.me/358400355544",
        "email": ALLOWED_EMAIL,
    }
    for key, value in expected.items():
        if submission.get(key) != value:
            errors.append(f"submission.{key} must equal the approved public contact value")
    for key in ("dropboxRequestUrl", "whatsappUrl"):
        if not is_https_url(submission.get(key)):
            errors.append(f"submission.{key} must be a public HTTPS URL")
    instruction = str(submission.get("instruction", "")).lower()
    if not all(term in instruction for term in ("alkuperä", "yksityisesti", "automaattisesti")):
        errors.append("submission.instruction must allow original material and promise private, non-automatic handling")
    if "vain julkaistavaksi hyväksyttyä" in instruction or "henkilötiedoista puhdistettua" in instruction:
        errors.append("submission.instruction must not require pre-cleaned or pre-approved material")


def validate_countries(atlas: dict[str, Any], errors: list[str]) -> None:
    countries = atlas.get("countries")
    if not isinstance(countries, list):
        errors.append("countries must be an array")
        return
    if len(countries) != 195:
        errors.append(f"countries must contain exactly 195 rows, found {len(countries)}")
    ids = [country.get("iso2") for country in countries if isinstance(country, dict)]
    if len(ids) != len(set(ids)):
        errors.append("countries contain duplicate iso2 values")
    if set(ids) != COUNTRY_ISO2:
        missing = sorted(COUNTRY_ISO2 - set(ids))
        extra = sorted(set(ids) - COUNTRY_ISO2)
        errors.append(f"countries do not match UN193+VA+PS; missing={missing}, extra={extra}")

    catalog = {country["iso2"]: country for country in COUNTRY_CATALOG}
    for index, country in enumerate(countries):
        path = f"countries[{index}]"
        if not isinstance(country, dict):
            errors.append(f"{path} must be an object")
            continue
        iso2 = country.get("iso2")
        if iso2 not in catalog:
            continue
        for key in ("name", "nameFi", "region", "current", "missing", "legacyStatus"):
            if not isinstance(country.get(key), str) or not country[key].strip():
                errors.append(f"{path}.{key} must be a non-empty string")
        if country.get("region") not in ALLOWED_REGIONS:
            errors.append(f"{path}.region is invalid")
        if country.get("name") != catalog[iso2]["name"] or country.get("nameFi") != catalog[iso2]["nameFi"]:
            errors.append(f"{path}: canonical country names were changed")

        dimensions = country.get("dimensions")
        if not isinstance(dimensions, dict) or set(dimensions) != set(DIMENSIONS):
            errors.append(f"{path}.dimensions must contain exactly {list(DIMENSIONS)}")
            continue
        invalid_statuses = {value for value in dimensions.values() if value not in DIMENSION_STATUSES}
        if invalid_statuses:
            errors.append(f"{path}.dimensions contains invalid statuses {sorted(invalid_statuses)}")
            continue
        expected_grade = best_evidence(dimensions)
        if country.get("bestEvidence") != expected_grade:
            errors.append(f"{path}.bestEvidence must be {expected_grade}")
        expected_coverage = coverage_percent(dimensions)
        if country.get("coveragePercent") != expected_coverage:
            errors.append(f"{path}.coveragePercent must be {expected_coverage}")
        source_links = country.get("sourceLinks")
        if not isinstance(source_links, list):
            errors.append(f"{path}.sourceLinks must be an array")
            source_links = []
        if len(source_links) != len(set(source_links)):
            errors.append(f"{path}.sourceLinks contains duplicates")
        for source_url in source_links:
            if not is_https_url(source_url):
                errors.append(f"{path}.sourceLinks contains a non-HTTPS source")
        if any(value != "missing" for value in dimensions.values()) and not source_links:
            errors.append(f"{path}: a non-missing dimension requires at least one source URL")
        if country.get("bestEvidence") == "A" and not any(
            dimensions[key] == "verified" for key in ("officialSales", "officialVolume", "taxRevenue")
        ):
            errors.append(f"{path}: grade A requires a verified direct official dimension")
        if country.get("bestEvidence") == "D" and any(value != "missing" for value in dimensions.values()):
            errors.append(f"{path}: grade D cannot contain non-missing dimensions")


def validate_evidence(atlas: dict[str, Any], errors: list[str]) -> None:
    evidence = atlas.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("evidence must be a non-empty array")
        return
    ids: list[str] = []
    for index, item in enumerate(evidence):
        path = f"evidence[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path} must be an object")
            continue
        ids.append(str(item.get("evidenceId", "")))
        claim_type = item.get("claimType")
        expected_grade = GRADE_BY_CLAIM_TYPE.get(claim_type)
        if expected_grade is None:
            errors.append(f"{path}.claimType is not allowlisted")
        elif item.get("grade") != expected_grade:
            errors.append(f"{path}.grade must be {expected_grade} for {claim_type}")
        if not is_https_url(item.get("sourceUrl")):
            errors.append(f"{path}.sourceUrl must be a public HTTPS URL")
        markets = item.get("countries")
        if not isinstance(markets, list) or not markets or not set(markets).issubset(COUNTRY_ISO2):
            errors.append(f"{path}.countries must be a non-empty UN195 subset")
        for key in ("title", "coverage", "use", "origin"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"{path}.{key} must be a non-empty string")
        if claim_type == "customs" and item.get("grade") != "B":
            errors.append(f"{path}: customs evidence cannot be presented as direct sales")
        if claim_type in {"model", "official_forecast", "prevalence", "enforcement_sample", "coverage_audit"} and item.get("grade") != "C":
            errors.append(f"{path}: model/forecast/supporting evidence must remain grade C")
    if len(ids) != len(set(ids)) or any(not identifier for identifier in ids):
        errors.append("evidenceId values must be unique and non-empty")


def validate_legal_and_attribution(atlas: dict[str, Any], errors: list[str]) -> None:
    legal = atlas.get("legal")
    if not isinstance(legal, list) or len(legal) < 3:
        errors.append("legal must contain the three curated German official anchors")
        return
    legal_by_id = {item.get("legalId"): item for item in legal if isinstance(item, dict)}
    required_anchors = {
        "EP-3032975-B2": "https://data.epo.org/publication-server/rest/v1.2/patents/EP3032975NWB2/document.pdf",
        "DE-BPATG-8NI18-24-JUDGMENT": "https://www.rechtsprechung-im-internet.de/jportal/?quelle=jlink&docid=JURE269032275&psml=bsjrsprod.psml",
        "DE-LGMUC-7O3341-24-JUDGMENT": "https://www.gesetze-bayern.de/Content/Document/Y-300-Z-BECKRS-B-2026-N-14206",
    }
    missing_ids = set(required_anchors) - set(legal_by_id)
    if missing_ids:
        errors.append(f"legal is missing required German anchors {sorted(missing_ids)}")
    for legal_id, source_url in required_anchors.items():
        if legal_id in legal_by_id and legal_by_id[legal_id].get("sourceUrl") != source_url:
            errors.append(f"legal anchor {legal_id} must retain its curated official source URL")
    bpatg = legal_by_id.get("DE-BPATG-8NI18-24-JUDGMENT", {})
    if bpatg.get("eventDate") != "2026-01-14" or bpatg.get("status") != "appeal_lodged":
        errors.append("BPatG anchor must record the 2026-01-14 judgment and lodged appeal")
    if "X ZR 21/26" not in str(bpatg.get("reference", "")) + str(bpatg.get("statement", "")):
        errors.append("BPatG anchor must record appeal docket X ZR 21/26")
    lg_munich = legal_by_id.get("DE-LGMUC-7O3341-24-JUDGMENT", {})
    if lg_munich.get("eventDate") != "2026-04-02" or lg_munich.get("reference") != "LG München I, 7 O 3341/24":
        errors.append("LG München I anchor must record the 2026-04-02 judgment 7 O 3341/24")
    for index, item in enumerate(legal):
        path = f"legal[{index}]"
        if item.get("countryIso2") != "DE":
            errors.append(f"{path}.countryIso2 must be DE")
        if not is_https_url(item.get("sourceUrl")):
            errors.append(f"{path}.sourceUrl must be a public HTTPS URL")
        if not item.get("limitation"):
            errors.append(f"{path}.limitation is required")

    attribution = atlas.get("sourceAttribution")
    if not isinstance(attribution, list) or not attribution:
        errors.append("sourceAttribution must be a non-empty array")
        return
    for index, item in enumerate(attribution):
        if not isinstance(item, dict) or not is_https_url(item.get("sourceUrl")):
            errors.append(f"sourceAttribution[{index}].sourceUrl must be a public HTTPS URL")


def validate_summary(atlas: dict[str, Any], errors: list[str]) -> None:
    summary = atlas.get("summary", {})
    countries = atlas.get("countries", [])
    if summary.get("countryCount") != 195 or summary.get("universe") != "UN193+VA+PS":
        errors.append("summary must declare exactly the UN193+VA+PS universe")
    grade_counts = Counter(country.get("bestEvidence") for country in countries if isinstance(country, dict))
    expected_grades = {grade: grade_counts.get(grade, 0) for grade in ("A", "B", "C", "D")}
    if summary.get("gradeCounts") != expected_grades:
        errors.append("summary.gradeCounts does not match countries")
    expected_dimensions = {
        dimension: {
            status: sum(
                1
                for country in countries
                if isinstance(country, dict) and country.get("dimensions", {}).get(dimension) == status
            )
            for status in sorted(DIMENSION_STATUSES)
        }
        for dimension in DIMENSIONS
    }
    if summary.get("dimensionCounts") != expected_dimensions:
        errors.append("summary.dimensionCounts does not match countries")
    if summary.get("evidenceCount") != len(atlas.get("evidence", [])):
        errors.append("summary.evidenceCount does not match evidence")
    if summary.get("legalAnchorCount") != len(atlas.get("legal", [])):
        errors.append("summary.legalAnchorCount does not match legal")


def validate_csv_parity(atlas: dict[str, Any], errors: list[str]) -> None:
    try:
        with COUNTRIES_CSV_PATH.open("r", encoding="utf-8", newline="") as handle:
            country_rows = list(csv.DictReader(handle))
    except FileNotFoundError:
        errors.append("site/data/countries.csv is missing")
        country_rows = []
    if len(country_rows) != 195:
        errors.append(f"countries.csv must contain 195 data rows, found {len(country_rows)}")
    json_by_iso = {country["iso2"]: country for country in atlas.get("countries", [])}
    for row in country_rows:
        country = json_by_iso.get(row.get("iso2"))
        if not country:
            errors.append(f"countries.csv contains an unknown iso2 {row.get('iso2')!r}")
            continue
        for key in ("name", "nameFi", "region", "bestEvidence", "legacyStatus"):
            if row.get(key) != str(country.get(key)):
                errors.append(f"countries.csv {row['iso2']}.{key} differs from atlas.json")
        if row.get("coveragePercent") != str(country.get("coveragePercent")):
            errors.append(f"countries.csv {row['iso2']}.coveragePercent differs from atlas.json")
        for dimension in DIMENSIONS:
            if row.get(dimension) != country["dimensions"][dimension]:
                errors.append(f"countries.csv {row['iso2']}.{dimension} differs from atlas.json")

    try:
        with EVIDENCE_CSV_PATH.open("r", encoding="utf-8", newline="") as handle:
            evidence_rows = list(csv.DictReader(handle))
    except FileNotFoundError:
        errors.append("site/data/evidence.csv is missing")
        evidence_rows = []
    if len(evidence_rows) != len(atlas.get("evidence", [])):
        errors.append("evidence.csv row count differs from atlas.json")
    json_by_id = {item["evidenceId"]: item for item in atlas.get("evidence", [])}
    for row in evidence_rows:
        item = json_by_id.get(row.get("evidenceId"))
        if not item:
            errors.append(f"evidence.csv contains unknown ID {row.get('evidenceId')!r}")
            continue
        if row.get("grade") != item["grade"] or row.get("claimType") != item["claimType"]:
            errors.append(f"evidence.csv {row['evidenceId']} semantics differ from atlas.json")
        if row.get("sourceUrl") != item["sourceUrl"] or not is_https_url(row.get("sourceUrl")):
            errors.append(f"evidence.csv {row['evidenceId']} lacks the expected HTTPS source")


def main() -> None:
    errors: list[str] = []
    actual_site_files = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "site").rglob("*")
        if path.is_file()
    }
    if actual_site_files != EXPECTED_SITE_FILES:
        errors.append(
            "site/ file manifest differs from the reviewed public allowlist; "
            f"missing={sorted(EXPECTED_SITE_FILES - actual_site_files)}, "
            f"extra={sorted(actual_site_files - EXPECTED_SITE_FILES)}"
        )
    for path in (
        ATLAS_PATH,
        COUNTRIES_CSV_PATH,
        EVIDENCE_CSV_PATH,
        CURATED_PATH,
        PUBLIC_BASELINE_PATH,
        UPSTREAM_METADATA_PATH,
        UPSTREAM_SHA_PATH,
    ):
        if not path.exists():
            errors.append(f"Missing required file: {path.relative_to(ROOT)}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)

    atlas = load_json(ATLAS_PATH)
    curated = load_json(CURATED_PATH)
    baseline = load_json(PUBLIC_BASELINE_PATH)
    metadata = load_json(UPSTREAM_METADATA_PATH)
    validate_source_inputs(curated, baseline, metadata, errors)
    if not isinstance(atlas, dict):
        errors.append("atlas.json must contain an object")
    else:
        missing_top = REQUIRED_TOP_LEVEL_KEYS - set(atlas)
        if missing_top:
            errors.append(f"atlas.json is missing top-level keys {sorted(missing_top)}")
        validate_meta(atlas, curated, errors)
        validate_submission(atlas, errors)
        validate_countries(atlas, errors)
        validate_evidence(atlas, errors)
        validate_legal_and_attribution(atlas, errors)
        validate_summary(atlas, errors)
        validate_csv_parity(atlas, errors)

    scan_public_text("atlas", atlas, errors)
    scan_public_text("curated", curated, errors)
    scan_public_text("baseline", baseline, errors)
    scan_public_text("metadata", metadata, errors)
    for path in (COUNTRIES_CSV_PATH, EVIDENCE_CSV_PATH):
        scan_public_text(str(path.relative_to(ROOT)), path.read_text(encoding="utf-8"), errors)
    for path in sorted((ROOT / "site").rglob("*")):
        # JavaScript source contains escaped URL/regex literals such as
        # `https:\\/\\/`, which resemble Windows drive paths to the data scanner.
        # Generated JSON/CSV plus rendered text assets remain fully scanned.
        if path.is_file() and path.suffix.lower() in {".html", ".css", ".json", ".csv", ".svg", ".txt", ".xml"}:
            scan_public_text(str(path.relative_to(ROOT)), path.read_text(encoding="utf-8"), errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Validation failed with {len(errors)} error(s).", file=sys.stderr)
        raise SystemExit(1)

    print(
        "Validated public atlas: 195 UN countries, redacted Marnet baseline and provenance hashes, "
        "approved contacts only, source URLs present, semantic grades consistent, and no local paths or secrets detected."
    )


if __name__ == "__main__":
    main()
