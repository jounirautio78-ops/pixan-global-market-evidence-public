#!/usr/bin/env python3
"""Validate the generated public atlas and fail closed on unsafe output."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlparse
from zoneinfo import ZoneInfo

from public_privacy_guard import (
    PRIVATE_IDENTIFIER_FINGERPRINTS,
    contains_private_identifier as guard_contains_private_identifier,
    private_identifier_fingerprint,
)
from build_atlas import (
    ABSOLUTE_PATH_RE,
    ALLOWED_EMAIL,
    ALLOWED_PHONE_DIGITS,
    CHANGELOG_PATH,
    COUNTRY_CATALOG,
    COUNTRY_ISO2,
    DIMENSIONS,
    DIMENSION_STATUSES,
    EMAIL_RE,
    GRADE_BY_CLAIM_TYPE,
    LEGACY_COUNTRY_TO_ISO2,
    MARKET_CSV_FIELDS,
    MARKET_DONOR_CANDIDATE_KEYS,
    MARKET_DONOR_CRITERION_KEYS,
    MARKET_DONOR_PROTOCOL_KEYS,
    MARKET_MODEL_KEYS,
    MARKET_OBSERVATION_KEYS,
    MARKET_OBSERVATIONS_PATH,
    MARKET_READINESS_KEYS,
    MARKET_SOURCE_KEYS,
    MARKET_SOURCE_OPTIONAL_KEYS,
    MARKET_SOURCE_TOP_LEVEL_KEYS,
    OUTPUT_DIR,
    PATENT_FAMILY_CSV_FIELDS,
    PATENT_HISTORY_PATH,
    PATENT_SOURCE_TOP_LEVEL_KEYS,
    PLUS_PHONE_RE,
    PUBLIC_BASELINE_PATH,
    ROOT,
    SECRET_ASSIGNMENT_RE,
    UPSTREAM_METADATA_PATH,
    best_evidence,
    build_changelog,
    build_market_values,
    build_patent_history,
    coverage_percent,
    market_values_csv_rows,
    normalize_phone,
    patent_family_csv_rows,
)
from validate_data_request_program import (
    SOURCE_PATH as DATA_REQUEST_SOURCE_PATH,
    SOURCE_TEMPLATE_EN as DATA_REQUEST_TEMPLATE_EN,
    SOURCE_TEMPLATE_FI as DATA_REQUEST_TEMPLATE_FI,
    validate_outputs as validate_data_request_outputs,
    validate_program as validate_data_request_program,
)
from validate_vendor_response_control import (
    SOURCE_PATH as VENDOR_RESPONSE_SOURCE_PATH,
    validate_outputs as validate_vendor_response_outputs,
    validate_source as validate_vendor_response_source,
)
from validate_review_experience import validate_all as validate_review_experience
from validate_fx_rates import validate_all as validate_fx_rates


ATLAS_PATH = OUTPUT_DIR / "atlas.json"
COUNTRIES_CSV_PATH = OUTPUT_DIR / "countries.csv"
EVIDENCE_CSV_PATH = OUTPUT_DIR / "evidence.csv"
MARKET_VALUES_JSON_PATH = OUTPUT_DIR / "market-values.json"
MARKET_VALUES_CSV_PATH = OUTPUT_DIR / "market-values.csv"
CHANGELOG_JSON_PATH = OUTPUT_DIR / "changelog.json"
PATENT_HISTORY_JSON_PATH = OUTPUT_DIR / "patent-history.json"
PATENT_FAMILY_CSV_PATH = OUTPUT_DIR / "patent-family.csv"
CURATED_PATH = ROOT / "source" / "curated.json"
UPSTREAM_SHA_PATH = ROOT / "source" / "marnet-upstream.sha256"
PAID_DATA_SOURCE_PATH = ROOT / "source" / "paid-data-procurement.json"
FORBIDDEN_RAW_PATH = ROOT / "source" / "marnet-dashboard.json"
SOCIAL_IMAGE_PATH = OUTPUT_DIR.parent / "assets" / "og-pixan-global-market-evidence.png"
SOCIAL_IMAGE_URL = (
    "https://jounirautio78-ops.github.io/pixan-global-market-evidence-public/"
    "assets/og-pixan-global-market-evidence.png"
)
SOCIAL_IMAGE_SIZE = (1200, 628)
REPOSITORY_PRIVATE_SCAN_ROOTS = (
    ROOT / "scripts",
    ROOT / "source",
    ROOT / ".github",
)
REPOSITORY_PRIVATE_SCAN_SUFFIXES = frozenset(
    {
        ".csv",
        ".html",
        ".js",
        ".json",
        ".md",
        ".py",
        ".sha256",
        ".txt",
        ".xml",
        ".yaml",
        ".yml",
    }
)

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
JAVASCRIPT_LOCAL_PATH_RE = re.compile(
    r"(?i)(?:file:(?://|\\/\\/)|/(?:Users|home|private|tmp|var|etc)/|"
    r"[A-Z]:\\\\(?:Users|home|private|tmp|var|etc)\\\\)"
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
    "site/assets/downloads.js",
    "site/assets/i18n.js",
    "site/assets/paid-data.js",
    "site/assets/request-program.js",
    "site/assets/review.js",
    "site/assets/vendor-response.js",
    "site/assets/styles.css",
    "site/assets/favicon.svg",
    "site/assets/og-pixan-global-market-evidence.png",
    "site/data/atlas.json",
    "site/data/countries.csv",
    "site/data/evidence.csv",
    "site/data/changelog.json",
    "site/data/bank-evidence-register.csv",
    "site/data/bank-evidence-register-en.csv",
    "site/data/bank-package-manifest.json",
    "site/data/top20-data-request-routes.json",
    "site/data/top20-data-request-routes.csv",
    "site/data/paid-data-procurement.json",
    "site/data/paid-data-procurement.csv",
    "site/data/vendor-response-control.json",
    "site/data/vendor-response-control.csv",
    "site/data/market-values.json",
    "site/data/market-values.csv",
    "site/data/evidence-lanes.json",
    "site/data/donor-cockpit.json",
    "site/data/country-scenarios.json",
    "site/data/fx-rates.json",
    "site/schemas/evidence-lanes.schema.json",
    "site/schemas/donor-cockpit.schema.json",
    "site/schemas/country-scenarios.schema.json",
    "site/schemas/fx-rates.schema.json",
    "site/data/patent-history.json",
    "site/data/patent-family.csv",
    "site/downloads/pixan-bank-deck-short-fi.pptx",
    "site/downloads/pixan-bank-deck-medium-fi.pptx",
    "site/downloads/pixan-bank-deck-large-fi.pptx",
    "site/downloads/pixan-bank-evidence-register-fi.xlsx",
    "site/downloads/pixan-bank-deck-short-en.pptx",
    "site/downloads/pixan-bank-deck-medium-en.pptx",
    "site/downloads/pixan-bank-deck-large-en.pptx",
    "site/downloads/pixan-bank-evidence-register-en.xlsx",
    "site/downloads/data-request-template-en.txt",
    "site/downloads/data-request-template-fi.txt",
    "site/downloads/pixan-paid-data-procurement-fi-en.xlsx",
}

PATENT_OUTPUT_TOP_LEVEL_KEYS = {
    "meta",
    "patent",
    "summary",
    "sources",
    "timeline",
    "familyMembers",
    "proceedings",
    "diligenceAlerts",
    "monetisation",
}
PATENT_META_KEYS = {"schemaVersion", "asOf", "generatedAt", "disclaimerEn", "disclaimerFi"}
PATENT_EVIDENCE_TIERS = {"official", "secondary", "lead"}
PATENT_VERIFICATION_LEVELS = {
    "official_central_status",
    "official_family_record",
    "official_national_record",
    "secondary_record",
    "unverified_lead",
}

MARKET_OUTPUT_TOP_LEVEL_KEYS = {
    "meta",
    "donorProtocol",
    "donorCandidates",
    "sources",
    "observations",
    "models",
}
MARKET_META_KEYS = {
    "schemaVersion",
    "asOf",
    "generatedAt",
    "modelReadiness",
    "disclaimerEn",
    "disclaimerFi",
}
MARKET_EVIDENCE_STATUSES = {
    "official_observed",
    "official_provisional",
    "official_table_derived",
    "derived_official_files",
    "institutional_supported",
    "commercial_estimate",
    "published_price_input",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def contains_private_identifier(
    value: str,
    fingerprints: frozenset[tuple[int, str]] | None = None,
) -> bool:
    if fingerprints is None:
        fingerprints = PRIVATE_IDENTIFIER_FINGERPRINTS
    return guard_contains_private_identifier(value, fingerprints)


def validate_social_preview(errors: list[str]) -> None:
    try:
        image = SOCIAL_IMAGE_PATH.read_bytes()
    except FileNotFoundError:
        errors.append("Social preview image is missing")
        return
    if not image.startswith(b"\x89PNG\r\n\x1a\n") or image[12:16] != b"IHDR":
        errors.append("Social preview must be a valid PNG with an IHDR header")
        return
    size = (int.from_bytes(image[16:20], "big"), int.from_bytes(image[20:24], "big"))
    if size != SOCIAL_IMAGE_SIZE:
        errors.append(f"Social preview must be {SOCIAL_IMAGE_SIZE[0]}x{SOCIAL_IMAGE_SIZE[1]}, got {size[0]}x{size[1]}")
    if len(image) > 3_000_000:
        errors.append("Social preview PNG exceeds the 3 MB publication limit")

    for page_name in ("index.html", "review.html"):
        page = OUTPUT_DIR.parent.joinpath(page_name).read_text(encoding="utf-8")
        if page.count(SOCIAL_IMAGE_URL) != 2:
            errors.append(f"site/{page_name} must bind the reviewed social preview to both Open Graph and Twitter")
        if '<meta name="twitter:card" content="summary_large_image">' not in page:
            errors.append(f"site/{page_name} lacks summary_large_image metadata")


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
        if contains_private_identifier(text):
            errors.append(f"{label}{path}: private identifier fingerprint is forbidden")


def scan_javascript_text(label: str, text: str, errors: list[str]) -> None:
    for match in EMAIL_RE.finditer(text):
        if match.group(0).lower() != ALLOWED_EMAIL:
            errors.append(f"{label}: disallowed email {match.group(0)!r}")
    for match in PLUS_PHONE_RE.finditer(text):
        if normalize_phone(match.group(0)) != ALLOWED_PHONE_DIGITS:
            errors.append(f"{label}: disallowed phone {match.group(0)!r}")
    if JAVASCRIPT_LOCAL_PATH_RE.search(text):
        errors.append(f"{label}: absolute/local path is forbidden")
    if SECRET_ASSIGNMENT_RE.search(text) or PEM_RE.search(text):
        errors.append(f"{label}: secret-like material is forbidden")
    if contains_private_identifier(text):
        errors.append(f"{label}: private identifier fingerprint is forbidden")


def scan_repository_private_identifiers(
    errors: list[str],
    roots: Iterable[Path] | None = None,
) -> None:
    """Reject reviewed private identifiers anywhere in publishable repo text."""
    selected_roots = tuple(roots) if roots is not None else REPOSITORY_PRIVATE_SCAN_ROOTS
    for root in selected_roots:
        if not root.exists():
            continue
        paths = (root,) if root.is_file() else root.rglob("*")
        for path in sorted(candidate for candidate in paths if candidate.is_file()):
            if path.suffix.lower() not in REPOSITORY_PRIVATE_SCAN_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                errors.append(f"{path}: expected public text is not valid UTF-8")
                continue
            if contains_private_identifier(text):
                try:
                    label = str(path.relative_to(ROOT))
                except ValueError:
                    label = str(path)
                errors.append(f"{label}: private identifier fingerprint is forbidden in repository text")


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
            reviewed_business_date = datetime.fromisoformat(
                reviewed_at[:-1] + "+00:00"
            ).astimezone(ZoneInfo("Asia/Nicosia")).date()
            if date.fromisoformat(str(curated_meta.get("asOf"))) > reviewed_business_date:
                errors.append("curated meta.asOf cannot be later than the Nicosia business date of meta.reviewedAt")
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


def validate_market_values(
    source: dict[str, Any],
    market_values: dict[str, Any],
    errors: list[str],
) -> None:
    """Validate market observations, calculation semantics and source parity."""
    if set(source) != MARKET_SOURCE_TOP_LEVEL_KEYS:
        errors.append("market-observations.json must use the exact reviewed top-level schema")
    if set(market_values) != MARKET_OUTPUT_TOP_LEVEL_KEYS:
        errors.append(
            "market-values.json must contain exactly meta, donorProtocol, donorCandidates, "
            "sources, observations, and models"
        )

    meta = market_values.get("meta")
    if not isinstance(meta, dict) or set(meta) != MARKET_META_KEYS:
        errors.append("market-values.json meta must use the exact reviewed schema")
        meta = {}
    if source.get("schemaVersion") != 1 or meta.get("schemaVersion") != 1:
        errors.append("market-value source and output schemaVersion must be 1")
    if meta.get("asOf") != source.get("asOf") or meta.get("generatedAt") != source.get("reviewedAt"):
        errors.append("market-values.json dates must be deterministically derived from the source")
    for key in ("asOf",):
        try:
            date.fromisoformat(str(source.get(key)))
        except ValueError:
            errors.append(f"market-observations.json {key} must be an ISO date")
    if not isinstance(source.get("reviewedAt"), str) or not RFC3339_UTC_RE.fullmatch(source["reviewedAt"]):
        errors.append("market-observations.json reviewedAt must be an RFC 3339 UTC timestamp")
    if meta.get("disclaimerEn") != source.get("disclaimerEn") or meta.get("disclaimerFi") != source.get("disclaimerFi"):
        errors.append("market-values.json disclaimers must match the reviewed source")

    readiness = source.get("modelReadiness")
    if not isinstance(readiness, dict) or set(readiness) != MARKET_READINESS_KEYS:
        errors.append("market-observations.json modelReadiness must use the exact reviewed schema")
        readiness = {}
    if meta.get("modelReadiness") != readiness:
        errors.append("market-values.json modelReadiness must match the reviewed source")
    if (
        readiness.get("status") != "not_estimate_ready"
        or readiness.get("comparableFullYearMarketValueDonors") != 0
        or readiness.get("minimumRequiredDonors") != 3
    ):
        errors.append("market model must remain not_estimate_ready with zero of three minimum comparable retail-value donors")
    for key in ("reasonEn", "reasonFi"):
        if not isinstance(readiness.get(key), str) or not readiness[key].strip():
            errors.append(f"modelReadiness.{key} must be a non-empty string")

    donor_protocol = source.get("donorProtocol")
    if not isinstance(donor_protocol, dict) or set(donor_protocol) != MARKET_DONOR_PROTOCOL_KEYS:
        errors.append("market-observations.json donorProtocol must use the exact reviewed schema")
        donor_protocol = {}
    if market_values.get("donorProtocol") != donor_protocol:
        errors.append("market-values.json donorProtocol must match the reviewed source")
    if donor_protocol.get("protocolVersion") != "1.0":
        errors.append("donorProtocol.protocolVersion must remain 1.0")
    for key in ("acceptanceRuleEn", "acceptanceRuleFi"):
        if not isinstance(donor_protocol.get(key), str) or not donor_protocol[key].strip():
            errors.append(f"donorProtocol.{key} must be a non-empty string")
    donor_criteria = donor_protocol.get("criteria")
    if not isinstance(donor_criteria, list) or len(donor_criteria) != 10:
        errors.append("donorProtocol.criteria must contain exactly ten acceptance criteria")
        donor_criteria = []
    criterion_ids: list[str] = []
    for index, item in enumerate(donor_criteria):
        path = f"donorProtocol.criteria[{index}]"
        if not isinstance(item, dict) or set(item) != MARKET_DONOR_CRITERION_KEYS:
            errors.append(f"{path} must use the exact reviewed schema")
            continue
        criterion_id = item.get("criterionId")
        if not isinstance(criterion_id, str) or not criterion_id:
            errors.append(f"{path}.criterionId must be a non-empty string")
        else:
            criterion_ids.append(criterion_id)
        for key in ("titleEn", "titleFi", "requirementEn", "requirementFi"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"{path}.{key} must be a non-empty string")
    expected_criterion_ids = [f"D{index}" for index in range(1, 11)]
    if criterion_ids != expected_criterion_ids:
        errors.append("donorProtocol criterion IDs must remain ordered D1 through D10")

    source_rows = source.get("sources")
    output_sources = market_values.get("sources")
    if output_sources != source_rows:
        errors.append("market-values.json sources must match the reviewed source exactly")
    if not isinstance(source_rows, list) or not source_rows:
        errors.append("market-observations.json sources must be a non-empty array")
        source_rows = []
    expected_source_urls = {
        "CA-HC-VAPING-SALES-2024": (
            "official",
            "https://health-infobase.canada.ca/substance-use/vaping/sales/",
            "https://health-infobase.canada.ca/src/data/substance-use/vaping/sales/VPRR%20Data%20-%202026-01-22.zip",
        ),
        "DE-DESTATIS-73411-0003": (
            "official",
            "https://genesis.destatis.de/datenbank/online/statistic/73411/table/73411-0003",
            "https://genesis.destatis.de/genesisWS/downloads/00/tables/73411-0003_00.csv",
        ),
        "FI-TAX-EXCISE-VVT-010-2025": (
            "official",
            "https://vero2.stat.fi/PXWeb/api/v1/en/Vero/Valmistevero/vvt_010.px",
            None,
        ),
        "PL-SEJM-I07255-O1": (
            "official",
            "https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTDDEJZ5/i07255-o1.pdf",
            None,
        ),
        "PL-SEJM-I17526-O1": (
            "official",
            "https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTDVKHSJ/i17526-o1.pdf",
            None,
        ),
        "SE-GOV-BERAKNINGSKONVENTIONER-2026": (
            "official",
            "https://www.regeringen.se/contentassets/1ed01e00001b42e5ad8d47433db63ece/berakningskonventioner_2026.pdf",
            None,
        ),
        "NZ-MOH-ANNUAL-RETURNS-2022": (
            "official",
            "https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2022",
            None,
        ),
        "NZ-MOH-ANNUAL-RETURNS-2023": (
            "official",
            "https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2023",
            None,
        ),
        "NZ-MOH-ANNUAL-RETURNS-2024": (
            "official",
            "https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2024",
            None,
        ),
        "EU-EC-SWD-2025-560": (
            "official_secondary",
            "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=SWD%3A2025%3A0560%3AFIN",
            None,
        ),
        "EU-EC-SWD-2026-111": (
            "official_secondary",
            "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=SWD%3A2026%3A111%3AFIN",
            None,
        ),
        "IMARC-GLOBAL-2025": (
            "commercial_estimate",
            "https://www.imarcgroup.com/e-cigarette-market",
            None,
        ),
        "GVR-GLOBAL-2025": (
            "commercial_estimate",
            "https://www.grandviewresearch.com/industry-analysis/e-cigarette-vaping-market",
            None,
        ),
        "FORTUNE-GLOBAL-2025": (
            "commercial_estimate",
            "https://www.fortunebusinessinsights.com/e-cigarette-and-vaping-market-114882",
            None,
        ),
        "INTASTE-GERMANFLAVOURS-2026": (
            "retail_listing",
            "https://www.intaste.de/pfefferminz-liquid-germanflavours-liquid",
            None,
        ),
        "INTASTE-SAMURAI-2026": (
            "retail_listing",
            "https://www.intaste.de/anstand-liquid-samurai-liquid",
            None,
        ),
        "INTASTE-REVOLTAGE-2026": (
            "retail_listing",
            "https://www.intaste.de/tobacco-vanilla-nikotinsalz-revoltage-liquid",
            None,
        ),
        "US-FTC-E-CIGARETTE-REPORT-2021": (
            "official",
            "https://www.ftc.gov/reports/e-cigarette-report-2021",
            "https://www.ftc.gov/system/files/ftc_gov/pdf/E-CigaretteReportfor2021.pdf",
        ),
    }
    source_by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(source_rows):
        path = f"market sources[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path} must be an object")
            continue
        keys = set(item)
        if not MARKET_SOURCE_KEYS.issubset(keys) or keys - MARKET_SOURCE_KEYS - MARKET_SOURCE_OPTIONAL_KEYS:
            errors.append(f"{path} uses an unexpected schema")
        source_id = item.get("sourceId")
        if not isinstance(source_id, str) or not source_id:
            errors.append(f"{path}.sourceId must be a non-empty string")
            continue
        if source_id in source_by_id:
            errors.append(f"market sources contain duplicate sourceId {source_id}")
        source_by_id[source_id] = item
        if not is_https_url(item.get("pageUrl")):
            errors.append(f"{path}.pageUrl must be a public HTTPS URL")
        if "downloadUrl" in item and not is_https_url(item.get("downloadUrl")):
            errors.append(f"{path}.downloadUrl must be a public HTTPS URL")
        try:
            retrieved = date.fromisoformat(str(item.get("retrievedAt")))
            as_of = date.fromisoformat(str(source.get("asOf")))
            if retrieved > as_of:
                errors.append(f"{path}.retrievedAt cannot be later than asOf")
        except ValueError:
            errors.append(f"{path}.retrievedAt must be an ISO date")
    if set(source_by_id) != set(expected_source_urls):
        errors.append("market sources must match the exact reviewed source ID set")
    for source_id, (source_kind, page_url, download_url) in expected_source_urls.items():
        item = source_by_id.get(source_id, {})
        if item.get("sourceKind") != source_kind or item.get("pageUrl") != page_url:
            errors.append(f"market source {source_id} must retain its reviewed kind and page URL")
        if item.get("downloadUrl") != download_url:
            errors.append(f"market source {source_id} must retain its reviewed download URL")

    observations = source.get("observations")
    output_observations = market_values.get("observations")
    if output_observations != observations:
        errors.append("market-values.json observations must match the reviewed source exactly")
    if not isinstance(observations, list) or not observations:
        errors.append("market-observations.json observations must be a non-empty array")
        observations = []
    observations_by_id: dict[str, dict[str, Any]] = {}
    expected_observations = {
        "CA-2024-MANUFACTURER-IMPORTER-SHIPMENTS-VALUE": ("CA", 2024, "manufacturer_importer_shipments_value", 1160753796.78, "CAD", "official_observed", "published", "manufacturer_importer_shipments_value_not_retail_sales", False),
        "CA-2024-MANUFACTURER-IMPORTER-SHIPMENTS-UNITS": ("CA", 2024, "manufacturer_importer_shipments_units", 118901910, "unit", "official_observed", "published", "physical_units_not_market_value", False),
        "CA-2024-MANUFACTURER-IMPORTER-SHIPMENTS-LITRES": ("CA", 2024, "manufacturer_importer_shipments_liquid_volume", 1251843, "litre", "official_observed", "published", "physical_volume_not_market_value", False),
        "NZ-2022-NOTIFIABLE-PRODUCT-REPORTED-REVENUE": ("NZ", 2022, "official_reported_revenue_mixed_supply_stages", 404000000, "NZD", "official_provisional", "official_approximation_with_significant_quality_warning", "mixed_supply_stage_revenue_incomplete_not_retail_market_value", False),
        "NZ-2023-NOTIFIABLE-PRODUCT-REPORTED-REVENUE-LOWER-BOUND": ("NZ", 2023, "official_reported_revenue_mixed_supply_stages", 374000000, "NZD", "official_provisional", "official_lower_bound_with_quality_warning", "mixed_supply_stage_revenue_incomplete_not_retail_market_value", False),
        "NZ-2024-SPECIALIST-RETAIL-SALES-LOWER-BOUND": ("NZ", 2024, "official_specialist_retail_sales_lower_bound", 280000000, "NZD", "official_provisional", "official_lower_bound_with_quality_warning", "specialist_vape_retailer_sales_incomplete_lower_bound_mixed_notifiable_products", False),
        "NZ-2024-SPECIALIST-RETAIL-PRODUCT-SALES-RAW-FILE-SUM": ("NZ", 2024, "derived_official_workbook_sales_raw_sum", 280684512.81, "NZD", "derived_official_files", "reproduced_raw_file_sum_with_quality_warning", "raw_workbook_sum_not_cleaned_or_complete_national_market", False),
        "NZ-2024-IDENTIFIED-VAPING-PRODUCT-SALES-RAW-SUM": ("NZ", 2024, "derived_identified_vaping_product_sales_raw_sum", 274180410.21, "NZD", "derived_official_files", "keyword_classified_raw_file_sum_with_quality_warning", "conservative_text_classification_raw_sum_not_donor", False),
        "EU-2023-EC-E-CIGARETTE-MARKET-BENCHMARK": (None, 2023, "institutional_market_value_benchmark", 4990000000, "EUR", "institutional_supported", "published_secondary_benchmark", "external_study_benchmark_published_by_official_institution_not_donor", False),
        "DE-2023-TAXED-LIQUID-VOLUME-L": ("DE", 2023, "taxed_substitutes_volume", 1241000, "litre", "official_observed", "final", "taxed_physical_volume_not_retail_market_value", False),
        "DE-2023-SUBSTITUTES-EXCISE-RECEIPTS": ("DE", 2023, "substitutes_excise_receipts", 201000000, "EUR", "official_observed", "final", "excise_receipts_not_retail_market_value", False),
        "DE-2024-TAXED-LIQUID-VOLUME-L": ("DE", 2024, "taxed_substitutes_volume", 1284000, "litre", "official_observed", "final", "taxed_physical_volume_not_retail_market_value", False),
        "DE-2024-SUBSTITUTES-EXCISE-RECEIPTS": ("DE", 2024, "substitutes_excise_receipts", 266000000, "EUR", "official_observed", "final", "excise_receipts_not_retail_market_value", False),
        "DE-2025-TAXED-LIQUID-VOLUME-L": ("DE", 2025, "taxed_substitutes_volume", 1518000, "litre", "official_provisional", "provisional", "taxed_physical_volume_not_retail_market_value", False),
        "DE-2025-SUBSTITUTES-EXCISE-RECEIPTS": ("DE", 2025, "substitutes_excise_receipts", 404000000, "EUR", "official_provisional", "provisional", "excise_receipts_not_retail_market_value", False),
        "FI-2025-NICOTINE-E-LIQUID-TAXED-VOLUME-L": ("FI", 2025, "nicotine_e_liquid_taxed_volume", 11801.062, "litre", "official_observed", "published", "taxed_physical_volume_not_retail_market_value", False),
        "FI-2025-NICOTINE-E-LIQUID-EXCISE-RECEIPTS": ("FI", 2025, "nicotine_e_liquid_excise_receipts", 3540319, "EUR", "official_observed", "published", "excise_receipts_not_retail_market_value", False),
        "PL-2023-E-LIQUID-REPORTED-VOLUME-L": ("PL", 2023, "reported_e_liquid_volume", 805441, "litre", "official_observed", "official_response", "official_reported_physical_volume_not_retail_market_value", False),
        "PL-2025-E-LIQUID-EXCISE-AMOUNT": ("PL", 2025, "e_liquid_excise_amount", 993100000, "PLN", "official_observed", "official_response", "official_tax_amount_not_retail_market_value", False),
        "PL-2025-VAPING-DEVICE-EXCISE-AMOUNT": ("PL", 2025, "vaping_device_excise_amount", 175300000, "PLN", "official_observed", "official_response", "official_tax_amount_not_retail_market_value", False),
        "PL-2025-VAPING-COMPONENT-SETS-EXCISE-AMOUNT": ("PL", 2025, "vaping_component_sets_excise_amount", 2500000, "PLN", "official_observed", "official_response", "official_tax_amount_not_retail_market_value", False),
        "SE-2024-NICOTINE-E-LIQUID-TAXED-VOLUME-L": ("SE", 2024, "nicotine_e_liquid_taxed_volume", 26000, "litre", "official_observed", "official_rounded", "taxed_physical_volume_not_retail_market_value", False),
        "SE-2024-NICOTINE-E-LIQUID-EXCISE-RECEIPTS": ("SE", 2024, "nicotine_e_liquid_excise_receipts", 80000000, "SEK", "official_observed", "official_rounded", "excise_receipts_not_retail_market_value", False),
        "GLOBAL-2025-IMARC-COMMERCIAL-ESTIMATE": (None, 2025, "commercial_market_estimate", 26000000000, "USD", "commercial_estimate", "external_estimate", "external_non_comparable_reference_not_atlas_estimate", False),
        "GLOBAL-2025-GVR-COMMERCIAL-ESTIMATE": (None, 2025, "commercial_market_estimate", 45700000000, "USD", "commercial_estimate", "external_estimate", "external_non_comparable_reference_not_atlas_estimate", False),
        "GLOBAL-2025-FORTUNE-COMMERCIAL-ESTIMATE": (None, 2025, "commercial_market_estimate", 46320000000, "USD", "commercial_estimate", "external_estimate", "external_non_comparable_reference_not_atlas_estimate", False),
        "DE-2026-RETAIL-PRICE-LOW-EUR-PER-ML": ("DE", 2026, "retail_price_input", 0.44, "EUR_per_ml", "published_price_input", "current_listing", "single_retail_listing_input_not_market_value", False),
        "DE-2026-RETAIL-PRICE-BASE-EUR-PER-ML": ("DE", 2026, "retail_price_input", 0.79, "EUR_per_ml", "published_price_input", "current_listing", "single_retail_listing_input_not_market_value", False),
        "DE-2026-RETAIL-PRICE-HIGH-EUR-PER-ML": ("DE", 2026, "retail_price_input", 1.09, "EUR_per_ml", "published_price_input", "current_listing", "single_retail_listing_input_not_market_value", False),
        "US-2015-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES": ("US", 2015, "ftc_reported_cartridge_and_disposable_sales", 304170046, "USD", "official_table_derived", "sum_of_official_product_categories", "manufacturer_reported_sales_not_complete_consumer_retail_sell_through", False),
        "US-2016-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES": ("US", 2016, "ftc_reported_cartridge_and_disposable_sales", 485707484, "USD", "official_table_derived", "sum_of_official_product_categories", "manufacturer_reported_sales_not_complete_consumer_retail_sell_through", False),
        "US-2017-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES": ("US", 2017, "ftc_reported_cartridge_and_disposable_sales", 779836399, "USD", "official_table_derived", "sum_of_official_product_categories", "manufacturer_reported_sales_not_complete_consumer_retail_sell_through", False),
        "US-2018-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES": ("US", 2018, "ftc_reported_cartridge_and_disposable_sales", 2043703005, "USD", "official_table_derived", "sum_of_official_product_categories", "manufacturer_reported_sales_not_complete_consumer_retail_sell_through", False),
        "US-2019-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES": ("US", 2019, "ftc_reported_cartridge_and_disposable_sales", 2702608307, "USD", "official_table_derived", "corrected_official_table_sum", "manufacturer_reported_sales_not_complete_consumer_retail_sell_through", False),
        "US-2020-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES": ("US", 2020, "ftc_reported_cartridge_and_disposable_sales", 2394423105, "USD", "official_table_derived", "corrected_and_expanded_official_table_sum", "manufacturer_reported_sales_not_complete_consumer_retail_sell_through", False),
        "US-2021-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES": ("US", 2021, "ftc_reported_cartridge_and_disposable_sales", 2763284338, "USD", "official_table_derived", "official_table_sum", "manufacturer_reported_sales_not_complete_consumer_retail_sell_through", False),
    }
    for index, item in enumerate(observations):
        path = f"market observations[{index}]"
        if not isinstance(item, dict) or set(item) != MARKET_OBSERVATION_KEYS:
            errors.append(f"{path} must use the exact reviewed schema")
            continue
        observation_id = item.get("observationId")
        if not isinstance(observation_id, str) or not observation_id:
            errors.append(f"{path}.observationId must be a non-empty string")
            continue
        if observation_id in observations_by_id:
            errors.append(f"market observations contain duplicate ID {observation_id}")
        observations_by_id[observation_id] = item
        value = item.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            errors.append(f"{path}.value must be a positive finite number")
        if item.get("countryIso2") is not None and item.get("countryIso2") not in COUNTRY_ISO2:
            errors.append(f"{path}.countryIso2 must be null or a UN195 country")
        if item.get("evidenceStatus") not in MARKET_EVIDENCE_STATUSES:
            errors.append(f"{path}.evidenceStatus is invalid")
        for key in ("geography", "metric", "unit", "period", "finality", "productScope", "marketValueBasis", "labelEn", "labelFi", "limitationEn", "limitationFi"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"{path}.{key} must be a non-empty string")
        for key in ("comparableMarketValue", "atlasEstimate"):
            if not isinstance(item.get(key), bool):
                errors.append(f"{path}.{key} must be Boolean")
        item_source_ids = item.get("sourceIds")
        if not isinstance(item_source_ids, list) or not item_source_ids or len(item_source_ids) != len(set(item_source_ids)):
            errors.append(f"{path}.sourceIds must be a non-empty unique array")
        elif any(source_id not in source_by_id for source_id in item_source_ids):
            errors.append(f"{path}.sourceIds references an unknown source")

        if item.get("metric") in {
            "taxed_substitutes_volume",
            "substitutes_excise_receipts",
            "nicotine_e_liquid_taxed_volume",
            "nicotine_e_liquid_excise_receipts",
            "reported_e_liquid_volume",
            "e_liquid_excise_amount",
            "vaping_device_excise_amount",
            "vaping_component_sets_excise_amount",
        }:
            allowed_basis = {
                "taxed_physical_volume_not_retail_market_value",
                "excise_receipts_not_retail_market_value",
                "official_reported_physical_volume_not_retail_market_value",
                "official_tax_amount_not_retail_market_value",
            }
            if item.get("marketValueBasis") not in allowed_basis or item.get("comparableMarketValue") or item.get("atlasEstimate"):
                errors.append(f"{path}: taxed volume or excise must never be labelled retail market value")
        if item.get("metric") == "commercial_market_estimate":
            if (
                item.get("evidenceStatus") != "commercial_estimate"
                or item.get("comparableMarketValue")
                or item.get("atlasEstimate")
                or item.get("marketValueBasis") != "external_non_comparable_reference_not_atlas_estimate"
            ):
                errors.append(f"{path}: external estimates must remain non-observed, non-comparable references")
        if item.get("metric") in {
            "official_reported_revenue_mixed_supply_stages",
            "official_specialist_retail_sales_lower_bound",
        }:
            if (
                item.get("evidenceStatus") != "official_provisional"
                or item.get("comparableMarketValue")
                or item.get("atlasEstimate")
            ):
                errors.append(f"{path}: New Zealand quality-warning values must remain provisional and donor-ineligible")
        if item.get("metric") in {
            "derived_official_workbook_sales_raw_sum",
            "derived_identified_vaping_product_sales_raw_sum",
        }:
            if (
                item.get("evidenceStatus") != "derived_official_files"
                or item.get("comparableMarketValue")
                or item.get("atlasEstimate")
            ):
                errors.append(f"{path}: reproduced New Zealand file sums must remain derived, non-comparable and donor-ineligible")
        if item.get("metric") == "institutional_market_value_benchmark":
            if (
                item.get("evidenceStatus") != "institutional_supported"
                or item.get("comparableMarketValue")
                or item.get("atlasEstimate")
                or item.get("marketValueBasis")
                != "external_study_benchmark_published_by_official_institution_not_donor"
            ):
                errors.append(f"{path}: institutional secondary values must remain supported, non-observed benchmarks")
        if item.get("metric") == "retail_price_input" and item.get("evidenceStatus") != "published_price_input":
            errors.append(f"{path}: a retail listing must remain a price input, not observed market value")
        if item.get("metric") == "ftc_reported_cartridge_and_disposable_sales":
            if (
                item.get("evidenceStatus") != "official_table_derived"
                or item.get("productScope")
                != "cartridge_system_and_disposable_e_cigarette_products_excluding_open_system"
                or item.get("marketValueBasis")
                != "manufacturer_reported_sales_not_complete_consumer_retail_sell_through"
                or item.get("comparableMarketValue")
                or item.get("atlasEstimate")
                or item.get("sourceIds") != ["US-FTC-E-CIGARETTE-REPORT-2021"]
            ):
                errors.append(f"{path}: FTC series must remain a derived official-table manufacturer-sales route, not a donor")
            if observation_id == "US-2020-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES" and (
                "five prior recipients" not in str(item.get("limitationEn", ""))
                or "three of the four first-time recipients" not in str(item.get("limitationEn", ""))
            ):
                errors.append(
                    f"{path}: the 2020 FTC population must retain the five-prior plus three-of-four-new boundary"
                )
        if observation_id == "GLOBAL-2025-IMARC-COMMERCIAL-ESTIMATE":
            limitation = str(item.get("limitationEn", ""))
            if (
                item.get("productScope")
                != "publisher_defined_global_e_cigarette_market_including_next_generation_and_htp_products"
                or "heated-tobacco" not in limitation
                or "IQOS" not in limitation
                or "Glo" not in limitation
            ):
                errors.append(f"{path}: IMARC scope must explicitly disclose included HTP products")

    if set(observations_by_id) != set(expected_observations):
        errors.append("market observations must match the exact reviewed observation ID set")
    for observation_id, expected in expected_observations.items():
        item = observations_by_id.get(observation_id, {})
        actual = (
            item.get("countryIso2"),
            item.get("year"),
            item.get("metric"),
            item.get("value"),
            item.get("unit"),
            item.get("evidenceStatus"),
            item.get("finality"),
            item.get("marketValueBasis"),
            item.get("comparableMarketValue"),
        )
        if actual != expected:
            errors.append(f"market observation {observation_id} differs from its reviewed fact tuple")

    expected_scope_sources = {
        "NZ-2022-NOTIFIABLE-PRODUCT-REPORTED-REVENUE": ("all_notifiable_products_including_vaping_smokeless_tobacco_and_herbal_smoking_products", "NZ-MOH-ANNUAL-RETURNS-2022"),
        "NZ-2023-NOTIFIABLE-PRODUCT-REPORTED-REVENUE-LOWER-BOUND": ("regulated_notifiable_products_including_heated_tobacco", "NZ-MOH-ANNUAL-RETURNS-2023"),
        "NZ-2024-SPECIALIST-RETAIL-SALES-LOWER-BOUND": ("notifiable_products_including_vaping_smokeless_tobacco_and_herbal_smoking_products", "NZ-MOH-ANNUAL-RETURNS-2024"),
        "NZ-2024-SPECIALIST-RETAIL-PRODUCT-SALES-RAW-FILE-SUM": ("specialist_retail_product_rows_including_vaping_and_adjacent_notifiable_products", "NZ-MOH-ANNUAL-RETURNS-2024"),
        "NZ-2024-IDENTIFIED-VAPING-PRODUCT-SALES-RAW-SUM": ("specialist_retail_rows_with_product_type_text_identified_as_vaping", "NZ-MOH-ANNUAL-RETURNS-2024"),
        "FI-2025-NICOTINE-E-LIQUID-TAXED-VOLUME-L": ("nicotine_containing_e_liquid_only", "FI-TAX-EXCISE-VVT-010-2025"),
        "FI-2025-NICOTINE-E-LIQUID-EXCISE-RECEIPTS": ("nicotine_containing_e_liquid_only", "FI-TAX-EXCISE-VVT-010-2025"),
        "PL-2023-E-LIQUID-REPORTED-VOLUME-L": ("e_liquid_only", "PL-SEJM-I07255-O1"),
        "PL-2025-E-LIQUID-EXCISE-AMOUNT": ("e_liquid_only", "PL-SEJM-I17526-O1"),
        "PL-2025-VAPING-DEVICE-EXCISE-AMOUNT": ("vaping_devices_only", "PL-SEJM-I17526-O1"),
        "PL-2025-VAPING-COMPONENT-SETS-EXCISE-AMOUNT": ("vaping_component_sets_only", "PL-SEJM-I17526-O1"),
        "SE-2024-NICOTINE-E-LIQUID-TAXED-VOLUME-L": ("nicotine_containing_e_liquid_only", "SE-GOV-BERAKNINGSKONVENTIONER-2026"),
        "SE-2024-NICOTINE-E-LIQUID-EXCISE-RECEIPTS": ("nicotine_containing_e_liquid_only", "SE-GOV-BERAKNINGSKONVENTIONER-2026"),
        "US-2015-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES": ("cartridge_system_and_disposable_e_cigarette_products_excluding_open_system", "US-FTC-E-CIGARETTE-REPORT-2021"),
        "US-2016-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES": ("cartridge_system_and_disposable_e_cigarette_products_excluding_open_system", "US-FTC-E-CIGARETTE-REPORT-2021"),
        "US-2017-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES": ("cartridge_system_and_disposable_e_cigarette_products_excluding_open_system", "US-FTC-E-CIGARETTE-REPORT-2021"),
        "US-2018-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES": ("cartridge_system_and_disposable_e_cigarette_products_excluding_open_system", "US-FTC-E-CIGARETTE-REPORT-2021"),
        "US-2019-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES": ("cartridge_system_and_disposable_e_cigarette_products_excluding_open_system", "US-FTC-E-CIGARETTE-REPORT-2021"),
        "US-2020-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES": ("cartridge_system_and_disposable_e_cigarette_products_excluding_open_system", "US-FTC-E-CIGARETTE-REPORT-2021"),
        "US-2021-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES": ("cartridge_system_and_disposable_e_cigarette_products_excluding_open_system", "US-FTC-E-CIGARETTE-REPORT-2021"),
    }
    for observation_id, (product_scope, source_id) in expected_scope_sources.items():
        item = observations_by_id.get(observation_id, {})
        if item.get("productScope") != product_scope or item.get("sourceIds") != [source_id]:
            errors.append(f"market observation {observation_id} must retain its conservative scope and official source")
    nz_raw_sum = observations_by_id.get("NZ-2024-SPECIALIST-RETAIL-PRODUCT-SALES-RAW-FILE-SUM", {})
    if (
        "29 official XLSX files" not in str(nz_raw_sum.get("limitationEn", ""))
        or "95,144 exact repeated row signatures" not in str(nz_raw_sum.get("limitationEn", ""))
        or "264,561,055.05" not in str(nz_raw_sum.get("limitationEn", ""))
    ):
        errors.append("New Zealand raw-file reconciliation must retain its file count and repeated-row sensitivity boundary")
    nz_vaping_sum = observations_by_id.get("NZ-2024-IDENTIFIED-VAPING-PRODUCT-SALES-RAW-SUM", {})
    if (
        "274,180,410.21" not in str(nz_vaping_sum.get("limitationEn", ""))
        or "2,137,085.24" not in str(nz_vaping_sum.get("limitationEn", ""))
        or "4,367,017.37" not in str(nz_vaping_sum.get("limitationEn", ""))
        or "258,327,110.88" not in str(nz_vaping_sum.get("limitationEn", ""))
    ):
        errors.append("New Zealand vaping classification must retain its partition and repeated-row sensitivity boundary")
    eu_benchmark = observations_by_id.get("EU-2023-EC-E-CIGARETTE-MARKET-BENCHMARK", {})
    if (
        eu_benchmark.get("productScope")
        != "external_study_e_cigarettes_including_devices_closed_refills_and_open_system_liquids"
        or eu_benchmark.get("sourceIds") != ["EU-EC-SWD-2025-560", "EU-EC-SWD-2026-111"]
        or "external study" not in str(eu_benchmark.get("limitationEn", "")).lower()
        or "euromonitor international" not in str(eu_benchmark.get("limitationEn", "")).lower()
        or "cyprus, luxembourg and malta" not in str(eu_benchmark.get("limitationEn", "")).lower()
    ):
        errors.append("EU 2023 benchmark must retain its commercial source attribution, missing-country boundary and both Commission sources")
    for observation_id in (
        "FI-2025-NICOTINE-E-LIQUID-TAXED-VOLUME-L",
        "FI-2025-NICOTINE-E-LIQUID-EXCISE-RECEIPTS",
    ):
        if "nicotine-free full-year value is suppressed" not in str(observations_by_id.get(observation_id, {}).get("limitationEn", "")):
            errors.append(f"market observation {observation_id} must disclose suppressed nicotine-free full-year data")
    for observation_id in (
        "SE-2024-NICOTINE-E-LIQUID-TAXED-VOLUME-L",
        "SE-2024-NICOTINE-E-LIQUID-EXCISE-RECEIPTS",
    ):
        item = observations_by_id.get(observation_id, {})
        if item.get("finality") != "official_rounded" or "Table 7.5" not in str(item.get("limitationEn", "")):
            errors.append(f"market observation {observation_id} must remain a rounded Table 7.5 figure")

    donor_count = sum(
        1
        for item in observations
        if isinstance(item, dict)
        and item.get("comparableMarketValue") is True
        and item.get("period") == "calendar_year"
    )
    if donor_count != readiness.get("comparableFullYearMarketValueDonors"):
        errors.append("modelReadiness donor count must equal comparable full-year monetary observations")

    models = source.get("models")
    output_models = market_values.get("models")
    if output_models != models:
        errors.append("market-values.json models must match the reviewed source exactly")
    if not isinstance(models, list) or len(models) != 1:
        errors.append("market-observations.json must contain exactly one reviewed model")
        models = []
    for index, model in enumerate(models):
        path = f"market models[{index}]"
        if not isinstance(model, dict) or set(model) != MARKET_MODEL_KEYS:
            errors.append(f"{path} must use the exact reviewed schema")
            continue
        if model.get("modelId") != "DE-2025-LIQUID-RETAIL-EQUIVALENT-RANGE":
            errors.append(f"{path}.modelId is not the reviewed model")
        if (
            model.get("countryIso2") != "DE"
            or model.get("year") != 2025
            or model.get("evidenceStatus") != "modelled"
            or model.get("confidence") != "low"
            or model.get("yearMismatch") is not True
            or model.get("productScope") != "taxed_substitutes_for_tobacco_liquid_only"
            or model.get("marketValueBasis") != "retail_equivalent_plausibility_range_not_observed_sales"
            or model.get("comparableMarketValue") is not False
            or model.get("atlasEstimate") is not True
        ):
            errors.append(f"{path} must remain a low-confidence, year-mismatched, modelled liquid-only range")
        if model.get("formula") != "volume_litres * 1000 * retail_price_eur_per_ml":
            errors.append(f"{path}.formula is invalid")
        input_ids = model.get("inputIds")
        if not isinstance(input_ids, list) or len(input_ids) != 4 or len(input_ids) != len(set(input_ids)):
            errors.append(f"{path}.inputIds must retain four unique observation IDs")
            input_ids = []
        if any(identifier not in observations_by_id for identifier in input_ids):
            errors.append(f"{path}.inputIds references an unknown observation")
        range_map = model.get("rangeInputMap")
        if not isinstance(range_map, dict) or set(range_map) != {"low", "central", "high"}:
            errors.append(f"{path}.rangeInputMap must contain exactly low, central, and high")
            range_map = {}
        if any(identifier not in input_ids for identifier in range_map.values()):
            errors.append(f"{path}.rangeInputMap values must be retained in inputIds")
        required_exclusions = {"devices", "illicit_and_untaxed_sales", "nicotine_free_products_where_not_taxed"}
        exclusions = model.get("exclusions")
        if not isinstance(exclusions, list) or not required_exclusions.issubset(set(exclusions)):
            errors.append(f"{path}.exclusions must retain the material excluded categories")

        volume = observations_by_id.get("DE-2025-TAXED-LIQUID-VOLUME-L", {}).get("value")
        expected_range: dict[str, int] = {}
        if isinstance(volume, (int, float)) and not isinstance(volume, bool):
            for bound in ("low", "central", "high"):
                price = observations_by_id.get(range_map.get(bound), {}).get("value")
                if isinstance(price, (int, float)) and not isinstance(price, bool):
                    expected_range[bound] = round(volume * 1000 * price)
        if expected_range != {"low": 667920000, "central": 1199220000, "high": 1654620000}:
            errors.append(f"{path}: model inputs do not reproduce the reviewed plausibility range")
        for bound, expected_value in expected_range.items():
            if model.get(bound) != expected_value:
                errors.append(f"{path}.{bound} must equal the deterministic formula result")
        if not (model.get("low", 0) < model.get("central", 0) < model.get("high", 0)):
            errors.append(f"{path}: model range must be ordered low < central < high")
        if "not observed sales" not in str(model.get("limitationEn", "")).lower():
            errors.append(f"{path}.limitationEn must explicitly say the range is not observed sales")
        if "ei havaittua myynti" not in str(model.get("limitationFi", "")).lower():
            errors.append(f"{path}.limitationFi must explicitly say the range is not observed sales")

    donor_candidates = source.get("donorCandidates")
    if market_values.get("donorCandidates") != donor_candidates:
        errors.append("market-values.json donorCandidates must match the reviewed source")
    if not isinstance(donor_candidates, list) or not donor_candidates:
        errors.append("market-observations.json donorCandidates must be a non-empty array")
        donor_candidates = []
    candidate_ids: set[str] = set()
    candidate_by_id: dict[str, dict[str, Any]] = {}
    accepted_candidates = 0
    known_reference_ids = set(observations_by_id) | {
        item.get("modelId") for item in models if isinstance(item, dict)
    }
    all_criterion_ids = set(expected_criterion_ids)
    for index, item in enumerate(donor_candidates):
        path = f"donorCandidates[{index}]"
        if not isinstance(item, dict) or set(item) != MARKET_DONOR_CANDIDATE_KEYS:
            errors.append(f"{path} must use the exact reviewed schema")
            continue
        candidate_id = item.get("candidateId")
        if not isinstance(candidate_id, str) or not candidate_id:
            errors.append(f"{path}.candidateId must be a non-empty string")
        elif candidate_id in candidate_ids:
            errors.append(f"donorCandidates contains duplicate ID {candidate_id}")
        else:
            candidate_ids.add(candidate_id)
            candidate_by_id[candidate_id] = item
        if item.get("countryIso2") is not None and item.get("countryIso2") not in COUNTRY_ISO2:
            errors.append(f"{path}.countryIso2 must be null or a UN195 country")
        if isinstance(item.get("year"), bool) or not isinstance(item.get("year"), int):
            errors.append(f"{path}.year must be an integer")
        if item.get("referenceType") not in {"observation", "model"}:
            errors.append(f"{path}.referenceType is invalid")
        if item.get("referenceId") not in known_reference_ids:
            errors.append(f"{path}.referenceId must identify a reviewed observation or model")
        decision = item.get("decision")
        if decision not in {"accepted", "not_accepted"}:
            errors.append(f"{path}.decision is invalid")
        for key in (
            "geography",
            "headlineEn",
            "headlineFi",
            "decisionReasonEn",
            "decisionReasonFi",
            "nextEvidenceEn",
            "nextEvidenceFi",
        ):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"{path}.{key} must be a non-empty string")
        buckets: list[list[str]] = []
        for key in ("passedCriteria", "failedCriteria", "openCriteria"):
            values = item.get(key)
            if (
                not isinstance(values, list)
                or len(values) != len(set(values))
                or any(value not in all_criterion_ids for value in values)
            ):
                errors.append(f"{path}.{key} must be a unique criterion-ID array")
                values = []
            buckets.append(values)
        flattened = [value for values in buckets for value in values]
        if len(flattened) != len(set(flattened)) or set(flattened) != all_criterion_ids:
            errors.append(f"{path} criterion buckets must partition D1 through D10 exactly")
        source_ids = item.get("sourceIds")
        if (
            not isinstance(source_ids, list)
            or not source_ids
            or len(source_ids) != len(set(source_ids))
            or any(source_id not in source_by_id for source_id in source_ids)
        ):
            errors.append(f"{path}.sourceIds must reference reviewed market sources")
        if decision == "accepted":
            accepted_candidates += 1
            if item.get("failedCriteria") or item.get("openCriteria") or set(item.get("passedCriteria", [])) != all_criterion_ids:
                errors.append(f"{path}: an accepted donor must pass all ten criteria")
        elif not item.get("failedCriteria"):
            errors.append(f"{path}: a rejected donor must expose at least one failed criterion")
    if accepted_candidates != readiness.get("comparableFullYearMarketValueDonors"):
        errors.append("accepted donor-candidate count must equal modelReadiness donor count")
    expected_candidate_tests = {
        "NZ-2024-OFFICIAL-RETAIL-LOWER-BOUND": (
            "NZ-2024-SPECIALIST-RETAIL-SALES-LOWER-BOUND",
            {"D1", "D2", "D6", "D7", "D9"},
            {"D4", "D5"},
            {"D3", "D8", "D10"},
        ),
        "EU-2023-COMMISSION-BENCHMARK": (
            "EU-2023-EC-E-CIGARETTE-MARKET-BENCHMARK",
            {"D1", "D3", "D4"},
            {"D7", "D9"},
            {"D2", "D5", "D6", "D8", "D10"},
        ),
        "CA-2024-OFFICIAL-SHIPMENT-PROXY": (
            "CA-2024-MANUFACTURER-IMPORTER-SHIPMENTS-VALUE",
            {"D1", "D3", "D4", "D7", "D9"},
            {"D2"},
            {"D5", "D6", "D8", "D10"},
        ),
        "DE-2025-LIQUID-RETAIL-MODEL": (
            "DE-2025-LIQUID-RETAIL-EQUIVALENT-RANGE",
            {"D4", "D6", "D7", "D9"},
            {"D1", "D2", "D3", "D10"},
            {"D5", "D8"},
        ),
        "US-2021-FTC-REPORTED-MANUFACTURER-SALES": (
            "US-2021-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES",
            {"D1", "D4", "D6", "D7", "D9"},
            {"D2", "D3", "D5"},
            {"D8", "D10"},
        ),
    }
    if candidate_ids != set(expected_candidate_tests):
        errors.append("donorCandidates must retain the five reviewed candidate tests")
    for candidate_id, (reference_id, passed, failed, open_items) in expected_candidate_tests.items():
        candidate = candidate_by_id.get(candidate_id, {})
        actual = (
            candidate.get("referenceId"),
            candidate.get("decision"),
            set(candidate.get("passedCriteria", [])),
            set(candidate.get("failedCriteria", [])),
            set(candidate.get("openCriteria", [])),
        )
        expected = (reference_id, "not_accepted", passed, failed, open_items)
        if actual != expected:
            errors.append(f"donor candidate {candidate_id} differs from its reviewed criterion test")

    try:
        expected_output = build_market_values()
    except (KeyError, TypeError, ValueError) as error:
        errors.append(f"market-value deterministic build rejected its source: {error}")
    else:
        if market_values != expected_output:
            errors.append("market-values.json differs from the deterministic reviewed build")


def validate_market_values_csv(market_values: dict[str, Any], errors: list[str]) -> None:
    try:
        with MARKET_VALUES_CSV_PATH.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames
            actual_rows = list(reader)
    except FileNotFoundError:
        errors.append("site/data/market-values.csv is missing")
        return
    if fieldnames != MARKET_CSV_FIELDS:
        errors.append("market-values.csv columns differ from the reviewed schema")

    expected_rows = market_values_csv_rows(market_values)
    normalized_expected = [
        {
            field: "" if row.get(field) is None else str(row.get(field, ""))
            for field in MARKET_CSV_FIELDS
        }
        for row in expected_rows
    ]
    if actual_rows != normalized_expected:
        errors.append("market-values.csv differs from market-values.json deterministic parity")
    record_ids = [row.get("recordId", "") for row in actual_rows]
    if len(record_ids) != len(set(record_ids)) or any(not record_id for record_id in record_ids):
        errors.append("market-values.csv recordId values must be unique and non-empty")


def validate_patent_history(
    source: dict[str, Any],
    public: dict[str, Any],
    errors: list[str],
) -> None:
    """Validate patent chronology, evidence tiers, family scope and strategy limits."""
    if set(source) != PATENT_SOURCE_TOP_LEVEL_KEYS or source.get("schemaVersion") != 1:
        errors.append("source/patent-history.json must use schemaVersion 1 and the exact reviewed top-level schema")
    if set(public) != PATENT_OUTPUT_TOP_LEVEL_KEYS:
        errors.append("site/data/patent-history.json uses an unexpected top-level schema")

    meta = public.get("meta")
    if not isinstance(meta, dict) or set(meta) != PATENT_META_KEYS:
        errors.append("patent-history public meta must use the exact reviewed schema")
        meta = {}
    if meta.get("schemaVersion") != 1 or meta.get("asOf") != source.get("asOf") or meta.get("generatedAt") != source.get("reviewedAt"):
        errors.append("patent-history public dates and schema must be deterministically derived")
    try:
        as_of = date.fromisoformat(str(source.get("asOf")))
    except ValueError:
        errors.append("source/patent-history.json asOf must be an ISO date")
        as_of = None
    if not isinstance(source.get("reviewedAt"), str) or not RFC3339_UTC_RE.fullmatch(source["reviewedAt"]):
        errors.append("source/patent-history.json reviewedAt must be an RFC 3339 UTC timestamp")
    if meta.get("disclaimerEn") != source.get("disclaimerEn") or meta.get("disclaimerFi") != source.get("disclaimerFi"):
        errors.append("patent-history disclaimers must match the reviewed source")
    combined_disclaimer = f"{source.get('disclaimerEn', '')} {source.get('disclaimerFi', '')}".lower()
    for term in ("not legal advice", "ei ole oikeudellinen neuvonta", "national status", "kansallinen voimassaolo", "cash flow", "kassavirta"):
        if term not in combined_disclaimer:
            errors.append(f"patent-history disclaimer must contain {term!r}")

    source_keys = {
        "sourceId", "publisher", "title", "sourceKind", "evidenceTier", "url", "retrievedAt",
        "scopeEn", "scopeFi", "limitationEn", "limitationFi",
    }
    sources = source.get("sources")
    if public.get("sources") != sources:
        errors.append("patent-history public sources must match the reviewed source exactly")
    if not isinstance(sources, list) or not sources:
        errors.append("patent-history sources must be a non-empty array")
        sources = []
    sources_by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(sources):
        path = f"patent sources[{index}]"
        if not isinstance(item, dict) or set(item) != source_keys:
            errors.append(f"{path} must use the exact reviewed schema")
            continue
        source_id = item.get("sourceId")
        if not isinstance(source_id, str) or not source_id:
            errors.append(f"{path}.sourceId must be a non-empty string")
            continue
        if source_id in sources_by_id:
            errors.append(f"patent sources contain duplicate sourceId {source_id}")
        sources_by_id[source_id] = item
        if item.get("evidenceTier") not in PATENT_EVIDENCE_TIERS:
            errors.append(f"{path}.evidenceTier is invalid")
        if not is_https_url(item.get("url")):
            errors.append(f"{path}.url must be a public HTTPS URL")
        try:
            retrieved = date.fromisoformat(str(item.get("retrievedAt")))
            if as_of and retrieved > as_of:
                errors.append(f"{path}.retrievedAt cannot be later than asOf")
        except ValueError:
            errors.append(f"{path}.retrievedAt must be an ISO date")
        for key in ("publisher", "title", "sourceKind", "scopeEn", "scopeFi", "limitationEn", "limitationFi"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"{path}.{key} must be a non-empty string")

    required_source_ids = {
        "EPO-REGISTER-MAIN",
        "EPO-REGISTER-EVENT",
        "EPO-REGISTER-DOCLIST",
        "EPO-REGISTER-FAMILY",
        "EPO-B1-SPECIFICATION",
        "EPO-B2-SPECIFICATION",
        "DE-BPATG-8NI18-24",
        "DE-LGMUC-7O3341-24",
        "RPX-CN-225669",
        "CNIPA-PUBLIC-QUERY-GUIDANCE",
        "CNIPA-REEXAMINATION-GUIDANCE",
        "PRH-FI-REGISTER",
        "IPAU-PATENT-API",
        "ROSPATENT-REGISTER",
        "KIPRIS-REGISTER",
        "USPTO-PATENT-CENTER",
        "USPTO-MAINTENANCE",
        "USPTO-ASSIGNMENT",
        "WIPO-IP-VALUATION",
        "WIPO-IP-FINANCE",
    }
    missing_sources = required_source_ids - set(sources_by_id)
    if missing_sources:
        errors.append(f"patent-history is missing required source anchors {sorted(missing_sources)}")
    for source_id in required_source_ids - {"RPX-CN-225669"}:
        if sources_by_id.get(source_id, {}).get("evidenceTier") != "official":
            errors.append(f"patent source {source_id} must remain official")
    if sources_by_id.get("RPX-CN-225669", {}).get("evidenceTier") != "secondary":
        errors.append("China RPX docket must remain a secondary source")

    patent_keys = {
        "title", "familyLabel", "inventionSummaryEn", "inventionSummaryFi", "claimScopeSummaryEn",
        "claimScopeSummaryFi", "claimScopeLimitationEn", "claimScopeLimitationFi", "inventor",
        "recordedProprietor", "earliestPriorityNumber", "earliestPriorityDate", "pctApplication",
        "woPublication", "epApplication", "epPublication", "epCentralStatusEn", "epCentralStatusFi",
        "epCentralStatusDate", "sourceIds",
    }
    patent = source.get("patent")
    if public.get("patent") != patent:
        errors.append("patent summary must match the reviewed source exactly")
    if not isinstance(patent, dict) or set(patent) != patent_keys:
        errors.append("patent summary must use the exact reviewed schema")
        patent = {}
    expected_identity = {
        "inventor": "Mika Kananen",
        "recordedProprietor": "Pixan Oy",
        "earliestPriorityNumber": "FI20135829",
        "earliestPriorityDate": "2013-08-14",
        "pctApplication": "PCT/FI2014/050624",
        "woPublication": "WO2015022448A1",
        "epApplication": "EP14836345.0",
        "epPublication": "EP3032975B2",
    }
    for key, value in expected_identity.items():
        if patent.get(key) != value:
            errors.append(f"patent.{key} must retain the reviewed identity {value}")
    if patent.get("epCentralStatusDate") != "2024-04-24":
        errors.append("patent.epCentralStatusDate must record the B2 publication on 2024-04-24")

    timeline_keys = {
        "eventId", "date", "historyType", "geography", "titleEn", "titleFi", "detailEn", "detailFi",
        "evidenceTier", "sourceIds", "limitationEn", "limitationFi",
    }
    family_keys = {
        "memberId", "jurisdictionCode", "jurisdictionEn", "jurisdictionFi", "jurisdictionCategory",
        "applicationNumber", "publicationNumber", "publicationDate", "recordType", "centralRecordStatusEn",
        "centralRecordStatusFi", "currentNationalStatusEn", "currentNationalStatusFi", "verificationLevel",
        "sourceIds", "registerUrl", "limitationEn", "limitationFi",
    }
    proceeding_keys = {
        "proceedingId", "jurisdictionCode", "forum", "proceedingType", "reference", "eventDate",
        "titleEn", "titleFi", "detailEn", "detailFi", "outcomeStatus", "finalityEn", "finalityFi",
        "evidenceTier", "patentNumbers", "sourceIds", "limitationEn", "limitationFi",
    }

    def validate_references(path: str, item: dict[str, Any]) -> None:
        refs = item.get("sourceIds")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{path}.sourceIds must be a non-empty array")
            return
        unknown = set(refs) - set(sources_by_id)
        if unknown:
            errors.append(f"{path}.sourceIds contains unknown IDs {sorted(unknown)}")
        tier = item.get("evidenceTier")
        if tier not in PATENT_EVIDENCE_TIERS:
            errors.append(f"{path}.evidenceTier is invalid")
        if tier == "official" and any(sources_by_id.get(ref, {}).get("evidenceTier") != "official" for ref in refs):
            errors.append(f"{path} cannot be official when any cited source is non-official")

    timeline = source.get("timeline")
    if public.get("timeline") != timeline:
        errors.append("patent public timeline must match the reviewed source exactly")
    if not isinstance(timeline, list) or not timeline:
        errors.append("patent timeline must be a non-empty array")
        timeline = []
    timeline_ids: list[str] = []
    prior_date = ""
    for index, item in enumerate(timeline):
        path = f"patent timeline[{index}]"
        if not isinstance(item, dict) or set(item) != timeline_keys:
            errors.append(f"{path} must use the exact reviewed schema")
            continue
        timeline_ids.append(str(item.get("eventId", "")))
        event_date = str(item.get("date", ""))
        try:
            date.fromisoformat(event_date)
        except ValueError:
            errors.append(f"{path}.date must be an ISO date")
        if prior_date and event_date < prior_date:
            errors.append("patent timeline must be chronological")
        prior_date = event_date
        validate_references(path, item)
    if len(timeline_ids) != len(set(timeline_ids)) or any(not item for item in timeline_ids):
        errors.append("patent timeline eventId values must be unique and non-empty")

    family = source.get("familyMembers")
    if public.get("familyMembers") != family:
        errors.append("patent public familyMembers must match the reviewed source exactly")
    if not isinstance(family, list) or len(family) < 20:
        errors.append("patent familyMembers must contain at least the 20 official EPO-family publication records")
        family = []
    member_ids: list[str] = []
    jurisdictions: set[str] = set()
    for index, item in enumerate(family):
        path = f"patent familyMembers[{index}]"
        if not isinstance(item, dict) or set(item) != family_keys:
            errors.append(f"{path} must use the exact reviewed schema")
            continue
        member_ids.append(str(item.get("memberId", "")))
        jurisdictions.add(str(item.get("jurisdictionCode", "")))
        if item.get("verificationLevel") not in PATENT_VERIFICATION_LEVELS:
            errors.append(f"{path}.verificationLevel is invalid")
        if not is_https_url(item.get("registerUrl")):
            errors.append(f"{path}.registerUrl must be a public HTTPS URL")
        refs = item.get("sourceIds")
        if not isinstance(refs, list) or not refs or set(refs) - set(sources_by_id):
            errors.append(f"{path}.sourceIds must reference known sources")
        national_status = f"{item.get('currentNationalStatusEn', '')} {item.get('currentNationalStatusFi', '')}".lower()
        if item.get("verificationLevel") == "official_family_record" and item.get("jurisdictionCode") != "WO" and not (
            "not independently verified" in national_status and "ei ole riippumattomasti vahvistettu" in national_status
        ):
            errors.append(f"{path} must not imply current national status from a family publication record")
    if len(member_ids) != len(set(member_ids)) or any(not item for item in member_ids):
        errors.append("patent family memberId values must be unique and non-empty")
    if not {"FI", "WO", "EP", "US", "CN", "JP", "KR", "AU", "CA", "BR"}.issubset(jurisdictions):
        errors.append("patent family inventory is missing core EPO-family jurisdictions")

    proceedings = source.get("proceedings")
    if public.get("proceedings") != proceedings:
        errors.append("patent public proceedings must match the reviewed source exactly")
    if not isinstance(proceedings, list) or len(proceedings) < 4:
        errors.append("patent proceedings must contain EPO, China-lead and German records")
        proceedings = []
    proceedings_by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(proceedings):
        path = f"patent proceedings[{index}]"
        if not isinstance(item, dict) or set(item) != proceeding_keys:
            errors.append(f"{path} must use the exact reviewed schema")
            continue
        proceeding_id = str(item.get("proceedingId", ""))
        if not proceeding_id or proceeding_id in proceedings_by_id:
            errors.append(f"{path}.proceedingId must be unique and non-empty")
        proceedings_by_id[proceeding_id] = item
        validate_references(path, item)
        if not isinstance(item.get("patentNumbers"), list) or not item["patentNumbers"]:
            errors.append(f"{path}.patentNumbers must be a non-empty array")
    required_proceedings = {"EPO-OPPOSITION-APPEAL", "CN-PRB-225669", "DE-BPATG-8NI18-24", "DE-LGMUC-7O3341-24"}
    if required_proceedings - set(proceedings_by_id):
        errors.append("patent proceedings are missing required reviewed anchors")
    china = proceedings_by_id.get("CN-PRB-225669", {})
    if china.get("evidenceTier") != "secondary" or china.get("outcomeStatus") != "unverified":
        errors.append("China PRB 225669 must remain secondary with an unverified outcome")
    china_text = f"{china.get('detailEn', '')} {china.get('detailFi', '')} {china.get('limitationEn', '')} {china.get('limitationFi', '')}".lower()
    for term in ("review request", "rejected application", "not an infringement judgment", "loukkaustuomio", "later", "official decision"):
        if term not in china_text:
            errors.append(f"China PRB record must preserve the limitation {term!r}")
    german_nullity = proceedings_by_id.get("DE-BPATG-8NI18-24", {})
    if german_nullity.get("outcomeStatus") != "appeal_pending" or "X ZR 21/26" not in str(german_nullity.get("reference", "")):
        errors.append("German nullity proceeding must retain the pending BGH appeal X ZR 21/26")

    alert_keys = {
        "alertId", "jurisdictionCode", "targetDate", "dateType", "priority", "status",
        "titleEn", "titleFi", "detailEn", "detailFi", "actionEn", "actionFi", "evidenceTier",
        "sourceIds", "limitationEn", "limitationFi",
    }
    allowed_alert_date_types = {
        "statutory_due", "payment_window_end", "register_in_force_through", "internal_review_target"
    }
    allowed_alert_priorities = {"critical", "high", "medium"}
    allowed_alert_statuses = {"confirm_now", "action_required", "verify_payment", "ongoing"}
    alerts = source.get("diligenceAlerts")
    if public.get("diligenceAlerts") != alerts:
        errors.append("patent public diligenceAlerts must match the reviewed source exactly")
    if not isinstance(alerts, list) or not alerts:
        errors.append("patent diligenceAlerts must be a non-empty array")
        alerts = []
    alert_ids: list[str] = []
    for index, item in enumerate(alerts):
        path = f"patent diligenceAlerts[{index}]"
        if not isinstance(item, dict) or set(item) != alert_keys:
            errors.append(f"{path} must use the exact reviewed schema")
            continue
        alert_ids.append(str(item.get("alertId", "")))
        if item.get("dateType") not in allowed_alert_date_types:
            errors.append(f"{path}.dateType is invalid")
        if item.get("priority") not in allowed_alert_priorities:
            errors.append(f"{path}.priority is invalid")
        if item.get("status") not in allowed_alert_statuses:
            errors.append(f"{path}.status is invalid")
        try:
            target_date = date.fromisoformat(str(item.get("targetDate", "")))
            if as_of and target_date < as_of:
                errors.append(f"{path}.targetDate cannot precede the dataset asOf date")
        except ValueError:
            errors.append(f"{path}.targetDate must be an ISO date")
        validate_references(path, item)
        for key in ("titleEn", "titleFi", "detailEn", "detailFi", "actionEn", "actionFi", "limitationEn", "limitationFi"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"{path}.{key} must be a non-empty string")
    if len(alert_ids) != len(set(alert_ids)) or any(not alert_id for alert_id in alert_ids):
        errors.append("patent diligence alertId values must be unique and non-empty")
    required_alerts = {"AU-RENEWAL-CONFIRM-2026", "FI-YEAR14-FEE-2026", "EP-NATIONAL-RECONCILIATION-2026", "US-MAINTENANCE-2026"}
    if required_alerts - set(alert_ids):
        errors.append("patent diligence alerts are missing required maintenance checkpoints")

    monetisation = source.get("monetisation")
    if public.get("monetisation") != monetisation:
        errors.append("patent public monetisation must match the reviewed source exactly")
    required_monetisation_keys = {"positioning", "readinessChecks", "countryScoring", "revenueRoutes", "sequence", "guardrails"}
    if not isinstance(monetisation, dict) or set(monetisation) != required_monetisation_keys:
        errors.append("patent monetisation must use the exact reviewed schema")
        monetisation = {}
    weights = [item.get("weightPercent") for item in monetisation.get("countryScoring", []) if isinstance(item, dict)]
    if not weights or any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in weights) or sum(weights) != 100:
        errors.append("patent country-scoring weights must be positive integers summing to 100")
    guardrail_text = " ".join(
        f"{item.get('textEn', '')} {item.get('textFi', '')}" for item in monetisation.get("guardrails", []) if isinstance(item, dict)
    ).lower()
    for term in ("germany", "saksa", "product-specific", "tuotekohtai", "national status", "kansallista voimassaolo", "counsel", "asiantuntija"):
        if term not in guardrail_text:
            errors.append(f"patent monetisation guardrails must contain {term!r}")
    for section in ("readinessChecks", "countryScoring", "revenueRoutes", "sequence", "guardrails"):
        records = monetisation.get(section)
        if not isinstance(records, list) or not records:
            errors.append(f"patent monetisation.{section} must be a non-empty array")
            continue
        for index, item in enumerate(records):
            if not isinstance(item, dict):
                errors.append(f"patent monetisation.{section}[{index}] must be an object")
                continue
            refs = item.get("sourceIds")
            if not isinstance(refs, list) or not refs or set(refs) - set(sources_by_id):
                errors.append(f"patent monetisation.{section}[{index}].sourceIds must reference known sources")
    positioning = monetisation.get("positioning")
    if not isinstance(positioning, dict) or not isinstance(positioning.get("sourceIds"), list) or set(positioning.get("sourceIds", [])) - set(sources_by_id):
        errors.append("patent monetisation.positioning must reference known sources")

    summary = public.get("summary")
    expected_summary = {
        "timelineEventCount": len(timeline),
        "familyRecordCount": len(family),
        "officialSourceCount": sum(1 for item in sources if isinstance(item, dict) and item.get("evidenceTier") == "official"),
        "proceedingCount": len(proceedings),
        "diligenceAlertCount": len(alerts),
        "unresolvedProceedingCount": sum(
            1
            for item in proceedings
            if isinstance(item, dict)
            and item.get("outcomeStatus")
            in {"unverified", "pending", "appeal_pending", "official_judgment_finality_unverified"}
        ),
    }
    if summary != expected_summary:
        errors.append("patent-history summary does not match its records")

    try:
        expected_public = build_patent_history()
    except (KeyError, TypeError, ValueError) as error:
        errors.append(f"patent-history deterministic build rejected its source: {error}")
    else:
        if public != expected_public:
            errors.append("patent-history public JSON differs from the deterministic reviewed build")


def validate_patent_family_csv(patent_history: dict[str, Any], errors: list[str]) -> None:
    try:
        with PATENT_FAMILY_CSV_PATH.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames
            actual_rows = list(reader)
    except FileNotFoundError:
        errors.append("site/data/patent-family.csv is missing")
        return
    if fieldnames != PATENT_FAMILY_CSV_FIELDS:
        errors.append("patent-family.csv columns differ from the reviewed schema")
    expected_rows = patent_family_csv_rows(patent_history)
    normalized_expected = [
        {field: "" if row.get(field) is None else str(row.get(field, "")) for field in PATENT_FAMILY_CSV_FIELDS}
        for row in expected_rows
    ]
    if actual_rows != normalized_expected:
        errors.append("patent-family.csv differs from patent-history.json deterministic parity")


def validate_changelog(source: dict[str, Any], public: dict[str, Any], errors: list[str]) -> None:
    """Validate deterministic release metadata used only for device-local visit comparison."""
    if set(source) != {"schemaVersion", "asOf", "releases"} or source.get("schemaVersion") != 1:
        errors.append("source/changelog.json must use schemaVersion 1 and the exact top-level schema")
    if public != source:
        errors.append("site/data/changelog.json must match the reviewed source exactly")
    try:
        as_of = date.fromisoformat(str(source.get("asOf")))
    except ValueError:
        errors.append("source/changelog.json asOf must be an ISO date")
        as_of = None
    releases = source.get("releases")
    if not isinstance(releases, list) or not releases:
        errors.append("source/changelog.json releases must be a non-empty array")
        releases = []
    release_ids: list[str] = []
    timestamps: list[datetime] = []
    allowed_categories = {"market_data", "model", "method", "language", "usability", "patent", "legal", "diligence"}
    for index, release in enumerate(releases):
        path = f"changelog releases[{index}]"
        expected = {"id", "version", "publishedAt", "titleEn", "titleFi", "items"}
        if not isinstance(release, dict) or set(release) != expected:
            errors.append(f"{path} must use the exact reviewed schema")
            continue
        release_id = release.get("id")
        if not isinstance(release_id, str) or not release_id.strip():
            errors.append(f"{path}.id must be a non-empty string")
        else:
            release_ids.append(release_id)
        for key in ("version", "titleEn", "titleFi"):
            if not isinstance(release.get(key), str) or not release[key].strip():
                errors.append(f"{path}.{key} must be a non-empty string")
        try:
            timestamp = datetime.fromisoformat(str(release.get("publishedAt")))
            if timestamp.tzinfo is None:
                raise ValueError
            timestamps.append(timestamp)
        except ValueError:
            errors.append(f"{path}.publishedAt must be an offset-aware ISO timestamp")
        items = release.get("items")
        if not isinstance(items, list) or not items:
            errors.append(f"{path}.items must be a non-empty array")
            continue
        for item_index, item in enumerate(items):
            item_path = f"{path}.items[{item_index}]"
            if not isinstance(item, dict) or set(item) != {"category", "textEn", "textFi"}:
                errors.append(f"{item_path} must use the exact reviewed schema")
                continue
            if item.get("category") not in allowed_categories:
                errors.append(f"{item_path}.category is not allowlisted")
            for key in ("textEn", "textFi"):
                if not isinstance(item.get(key), str) or not item[key].strip():
                    errors.append(f"{item_path}.{key} must be a non-empty string")
    if len(release_ids) != len(set(release_ids)):
        errors.append("changelog release IDs must be unique")
    if timestamps != sorted(timestamps, reverse=True):
        errors.append("changelog releases must be ordered newest first")
    try:
        expected_public = build_changelog()
    except (KeyError, TypeError, ValueError) as error:
        errors.append(f"changelog deterministic build rejected its source: {error}")
    else:
        if public != expected_public:
            errors.append("site/data/changelog.json differs from the deterministic reviewed build")


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
        MARKET_VALUES_JSON_PATH,
        MARKET_VALUES_CSV_PATH,
        PATENT_HISTORY_JSON_PATH,
        PATENT_FAMILY_CSV_PATH,
        CHANGELOG_JSON_PATH,
        CURATED_PATH,
        PUBLIC_BASELINE_PATH,
        MARKET_OBSERVATIONS_PATH,
        PATENT_HISTORY_PATH,
        CHANGELOG_PATH,
        UPSTREAM_METADATA_PATH,
        UPSTREAM_SHA_PATH,
        DATA_REQUEST_SOURCE_PATH,
        PAID_DATA_SOURCE_PATH,
        VENDOR_RESPONSE_SOURCE_PATH,
        DATA_REQUEST_TEMPLATE_EN,
        DATA_REQUEST_TEMPLATE_FI,
    ):
        if not path.exists():
            errors.append(f"Missing required file: {path.relative_to(ROOT)}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)

    validate_social_preview(errors)
    atlas = load_json(ATLAS_PATH)
    curated = load_json(CURATED_PATH)
    baseline = load_json(PUBLIC_BASELINE_PATH)
    metadata = load_json(UPSTREAM_METADATA_PATH)
    market_source = load_json(MARKET_OBSERVATIONS_PATH)
    market_values = load_json(MARKET_VALUES_JSON_PATH)
    patent_source = load_json(PATENT_HISTORY_PATH)
    patent_history = load_json(PATENT_HISTORY_JSON_PATH)
    changelog_source = load_json(CHANGELOG_PATH)
    changelog_public = load_json(CHANGELOG_JSON_PATH)
    data_request_source = load_json(DATA_REQUEST_SOURCE_PATH)
    paid_data_source = load_json(PAID_DATA_SOURCE_PATH)
    vendor_response_source = load_json(VENDOR_RESPONSE_SOURCE_PATH)
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

    if not isinstance(market_source, dict):
        errors.append("market-observations.json must contain an object")
    elif not isinstance(market_values, dict):
        errors.append("market-values.json must contain an object")
    else:
        validate_market_values(market_source, market_values, errors)
        validate_market_values_csv(market_values, errors)

    if not isinstance(patent_source, dict) or not isinstance(patent_history, dict):
        errors.append("source and public patent-history files must contain objects")
    else:
        validate_patent_history(patent_source, patent_history, errors)
        validate_patent_family_csv(patent_history, errors)

    if not isinstance(changelog_source, dict) or not isinstance(changelog_public, dict):
        errors.append("source and public changelog files must contain objects")
    else:
        validate_changelog(changelog_source, changelog_public, errors)

    if not isinstance(data_request_source, dict):
        errors.append("top20-data-request-routes.json must contain an object")
    else:
        validate_data_request_program(data_request_source, errors)
        validate_data_request_outputs(data_request_source, errors)

    if not isinstance(vendor_response_source, dict):
        errors.append("vendor-response-control.json must contain an object")
    else:
        validate_vendor_response_source(vendor_response_source, errors)
        validate_vendor_response_outputs(vendor_response_source, errors)

    errors.extend(validate_review_experience(ROOT))
    errors.extend(validate_fx_rates(ROOT))

    scan_public_text("atlas", atlas, errors)
    scan_public_text("curated", curated, errors)
    scan_public_text("baseline", baseline, errors)
    scan_public_text("metadata", metadata, errors)
    scan_public_text("market source", market_source, errors)
    scan_public_text("market values", market_values, errors)
    scan_public_text("patent source", patent_source, errors)
    scan_public_text("patent history", patent_history, errors)
    scan_public_text("changelog source", changelog_source, errors)
    scan_public_text("data-request source", data_request_source, errors)
    scan_public_text("paid-data procurement source", paid_data_source, errors)
    scan_public_text("vendor-response source", vendor_response_source, errors)
    for path in (ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "source" / "SOURCE_PROVENANCE.md"):
        scan_public_text(str(path.relative_to(ROOT)), path.read_text(encoding="utf-8"), errors)
    for path in (COUNTRIES_CSV_PATH, EVIDENCE_CSV_PATH, MARKET_VALUES_CSV_PATH, PATENT_FAMILY_CSV_PATH):
        scan_public_text(str(path.relative_to(ROOT)), path.read_text(encoding="utf-8"), errors)
    for path in sorted((ROOT / "site").rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix == ".js":
            scan_javascript_text(str(path.relative_to(ROOT)), path.read_text(encoding="utf-8"), errors)
        elif suffix in {".html", ".css", ".json", ".csv", ".svg", ".txt", ".xml"}:
            scan_public_text(str(path.relative_to(ROOT)), path.read_text(encoding="utf-8"), errors)
    scan_repository_private_identifiers(errors)

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
