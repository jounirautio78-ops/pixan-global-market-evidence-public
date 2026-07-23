#!/usr/bin/env python3
"""Fail-closed validation for the public vendor-response control."""

from __future__ import annotations

import csv
from datetime import date
import io
import json
from pathlib import Path
import re
import sys
from typing import Any

from public_privacy_guard import contains_private_identifier
from build_vendor_response_control import (
    CSV_FIELDS,
    OUTPUT_CSV,
    OUTPUT_JSON,
    SOURCE_PATH,
    normalised,
    render_csv,
    render_json,
    score_vendor,
)


ROOT = Path(__file__).resolve().parents[1]
REVIEW_HTML = ROOT / "site" / "review.html"
VENDOR_SCRIPT = ROOT / "site" / "assets" / "vendor-response.js"

TOP_LEVEL_KEYS = {
    "schemaVersion",
    "controlId",
    "asOf",
    "version",
    "status",
    "publicBoundaryEn",
    "publicBoundaryFi",
    "scoreBoundaryEn",
    "scoreBoundaryFi",
    "scoreScale",
    "criteria",
    "mandatoryGates",
    "evidenceTypes",
    "vendors",
}
OUTPUT_TOP_LEVEL_KEYS = TOP_LEVEL_KEYS | {"summary"}
CRITERION_WEIGHTS = {
    "annualCountrySeriesFit": 0.20,
    "metricScopeClarity": 0.15,
    "coverage": 0.15,
    "methodTransparency": 0.15,
    "auditability": 0.10,
    "transactionLicenceFit": 0.15,
    "commercialClarity": 0.10,
}
EVIDENCE_KEYS = {
    "sample",
    "methodology",
    "coverageMatrix",
    "quote",
    "officialAnchorReconciliation",
    "transactionUseRights",
    "totalCostTerms",
}
MANDATORY_GATE_KEYS = EVIDENCE_KEYS - {"quote"}
EXPECTED_VENDORS = {
    "ecig-global-market-database": {
        "vendor": "ECigIntelligence",
        "product": "Global Market Database",
        "requestState": "request_sent",
        "responseState": "pending",
        "publicStatusEn": "Request sent; response pending",
        "publicStatusFi": "Pyyntö lähetetty; vastaus odottaa",
    },
    "euromonitor-passport-nicotine": {
        "vendor": "Euromonitor International",
        "product": "Passport Nicotine / e-vapour country series",
        "requestState": "request_sent",
        "responseState": "pending",
        "publicStatusEn": "Request sent; response pending",
        "publicStatusFi": "Pyyntö lähetetty; vastaus odottaa",
    },
    "niq-rms-pilot": {
        "vendor": "NielsenIQ",
        "product": "Retail Measurement Services pilot",
        "requestState": "not_submitted_terms_gate",
        "responseState": "not_submitted",
        "publicStatusEn": "Not submitted; terms gate",
        "publicStatusFi": "Ei lähetetty; ehtoraja",
    },
    "circana-us-tobacco-pilot": {
        "vendor": "Circana",
        "product": "US Tobacco POS pilot",
        "requestState": "submission_confirmed",
        "responseState": "pending",
        "publicStatusEn": "Submission confirmed; response pending",
        "publicStatusFi": "Vastaanotto vahvistettu; vastaus odottaa",
    },
}
VENDOR_KEYS = {
    "vendorId",
    "vendor",
    "product",
    "requestState",
    "responseState",
    "publicStatusEn",
    "publicStatusFi",
    "receivedEvidence",
    "criterionScores",
    "scoringState",
    "weightedScore",
    "purchaseAuthorised",
}
OUTPUT_VENDOR_KEYS = VENDOR_KEYS | {
    "evidenceReceivedCount",
    "mandatoryGatePassCount",
}
SUMMARY_KEYS = {
    "trackedVendors",
    "substantiveResponses",
    "scoredVendors",
    "purchaseAuthorisations",
}

EMAIL_RE = re.compile(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", re.IGNORECASE)
UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
ABSOLUTE_PATH_RE = re.compile(
    r"(?i)(?:file:(?://|\\/\\/)|/(?:Users|home|private|tmp|var|etc)/|"
    r"[A-Z]:\\\\(?:Users|home|private|tmp|var|etc)\\\\)"
)
EXACT_TIME_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?")
FORBIDDEN_METADATA_TEXT = (
    "submissionguid",
    "submission guid",
    "formguid",
    "form guid",
    "message-id",
    "message id",
    "thread id",
    "private path",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def text_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from text_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from text_values(item)


def valid_date(value: Any) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def scan_privacy(label: str, value: Any, errors: list[str]) -> None:
    for text in text_values(value):
        folded = text.casefold()
        if EMAIL_RE.search(text):
            errors.append(f"{label} contains an email address")
        if UUID_RE.search(text):
            errors.append(f"{label} contains a UUID")
        if ABSOLUTE_PATH_RE.search(text):
            errors.append(f"{label} contains a local or private path")
        if EXACT_TIME_RE.search(text):
            errors.append(f"{label} contains an exact timestamp")
        if contains_private_identifier(text):
            errors.append(f"{label} contains a private identifier fingerprint")
        if any(marker in folded for marker in FORBIDDEN_METADATA_TEXT):
            errors.append(f"{label} contains a forbidden private metadata field")


def validate_source(source: Any, errors: list[str]) -> None:
    if not isinstance(source, dict):
        errors.append("source must contain an object")
        return
    if set(source) != TOP_LEVEL_KEYS:
        errors.append("source top-level schema differs")
        return
    if source.get("schemaVersion") != 1:
        errors.append("unsupported schema version")
    if source.get("controlId") != "vendor-response-control-public":
        errors.append("unexpected control ID")
    if source.get("status") != "public_status_only_no_purchase_authorised":
        errors.append("control must state that no purchase is authorised")
    if source.get("version") != "2026.07.23-13" or not valid_date(source.get("asOf")):
        errors.append("control version or date differs")
    if source.get("scoreScale") != {
        "minimum": 0,
        "maximum": 5,
        "missingValue": "not_scored",
    }:
        errors.append("score scale must preserve missing values as not_scored")

    criteria = source.get("criteria")
    if not isinstance(criteria, list) or len(criteria) != len(CRITERION_WEIGHTS):
        errors.append("exactly seven scoring criteria are required")
        return
    criterion_ids: set[str] = set()
    for criterion in criteria:
        if not isinstance(criterion, dict) or set(criterion) != {
            "id",
            "weight",
            "labelEn",
            "labelFi",
            "descriptionEn",
            "descriptionFi",
        }:
            errors.append("criterion schema differs")
            continue
        criterion_id = criterion["id"]
        criterion_ids.add(criterion_id)
        if criterion_id not in CRITERION_WEIGHTS:
            errors.append(f"unknown criterion {criterion_id!r}")
        elif abs(float(criterion["weight"]) - CRITERION_WEIGHTS[criterion_id]) > 1e-9:
            errors.append(f"criterion weight differs for {criterion_id!r}")
    if criterion_ids != set(CRITERION_WEIGHTS):
        errors.append("criterion IDs differ")
    if abs(sum(float(item["weight"]) for item in criteria) - 1.0) > 1e-9:
        errors.append("criterion weights must sum to 1.0")

    gates = source.get("mandatoryGates")
    if not isinstance(gates, list) or len(gates) != len(MANDATORY_GATE_KEYS):
        errors.append("exactly six mandatory gates are required")
        gates = []
    gate_evidence_keys: set[str] = set()
    gate_ids: set[str] = set()
    for gate in gates:
        if not isinstance(gate, dict) or set(gate) != {
            "id",
            "evidenceKey",
            "labelEn",
            "labelFi",
            "descriptionEn",
            "descriptionFi",
        }:
            errors.append("mandatory gate schema differs")
            continue
        gate_ids.add(gate["id"])
        gate_evidence_keys.add(gate["evidenceKey"])
        if gate["id"] != gate["evidenceKey"]:
            errors.append(f"mandatory gate ID and evidence key differ for {gate['id']!r}")
    if gate_ids != MANDATORY_GATE_KEYS or gate_evidence_keys != MANDATORY_GATE_KEYS:
        errors.append("mandatory gate set differs")

    evidence_types = source.get("evidenceTypes")
    if not isinstance(evidence_types, list) or len(evidence_types) != len(EVIDENCE_KEYS):
        errors.append("exactly seven public evidence indicators are required")
    elif (
        {item.get("key") for item in evidence_types if isinstance(item, dict)} != EVIDENCE_KEYS
        or any(
            not isinstance(item, dict)
            or set(item) != {"key", "labelEn", "labelFi"}
            for item in evidence_types
        )
    ):
        errors.append("evidence indicator schema or keys differ")

    vendors = source.get("vendors")
    if not isinstance(vendors, list) or len(vendors) != len(EXPECTED_VENDORS):
        errors.append("exactly four public vendor records are required")
        return
    seen: set[str] = set()
    for vendor in vendors:
        if not isinstance(vendor, dict) or set(vendor) != VENDOR_KEYS:
            errors.append("vendor record schema differs")
            continue
        vendor_id = vendor["vendorId"]
        if vendor_id in seen or vendor_id not in EXPECTED_VENDORS:
            errors.append(f"unknown or duplicate vendor ID {vendor_id!r}")
            continue
        seen.add(vendor_id)
        expected = EXPECTED_VENDORS[vendor_id]
        for field in (
            "vendor",
            "product",
            "requestState",
            "responseState",
            "publicStatusEn",
            "publicStatusFi",
        ):
            if vendor[field] != expected[field]:
                errors.append(f"{vendor_id}: {field} differs from the reviewed public state")
        evidence = vendor.get("receivedEvidence")
        if not isinstance(evidence, dict) or set(evidence) != EVIDENCE_KEYS:
            errors.append(f"{vendor_id}: evidence schema differs")
        elif any(value is not False for value in evidence.values()):
            errors.append(f"{vendor_id}: no received evidence is established in this release")
        scores = vendor.get("criterionScores")
        if not isinstance(scores, dict) or set(scores) != set(CRITERION_WEIGHTS):
            errors.append(f"{vendor_id}: criterion score schema differs")
        elif any(value is not None for value in scores.values()):
            errors.append(f"{vendor_id}: missing evidence must not be converted into scores")
        if vendor.get("scoringState") != "not_scored" or vendor.get("weightedScore") is not None:
            errors.append(f"{vendor_id}: missing response must remain NOT SCORED")
        if vendor.get("purchaseAuthorised") is not False:
            errors.append(f"{vendor_id}: purchase authorisation must remain false")
        if isinstance(evidence, dict) and isinstance(scores, dict):
            if score_vendor(vendor, criteria, gates) is not None:
                errors.append(f"{vendor_id}: vendor cannot be scored before the mandatory gates pass")
    if seen != set(EXPECTED_VENDORS):
        errors.append("vendor set differs from the reviewed four-vendor control")

    scan_privacy("vendor-response source", source, errors)


def validate_outputs(source: dict[str, Any], errors: list[str]) -> None:
    try:
        output_json_bytes = OUTPUT_JSON.read_bytes()
    except FileNotFoundError:
        errors.append("public vendor-response JSON is missing")
        output_json_bytes = b""
    if output_json_bytes and output_json_bytes != render_json(source):
        errors.append("public vendor-response JSON is stale or differs from the canonical source")
    try:
        output_csv_bytes = OUTPUT_CSV.read_bytes()
    except FileNotFoundError:
        errors.append("public vendor-response CSV is missing")
        output_csv_bytes = b""
    if output_csv_bytes and output_csv_bytes != render_csv(source):
        errors.append("public vendor-response CSV is stale or differs from the canonical source")

    if output_json_bytes:
        output = json.loads(output_json_bytes)
        if set(output) != OUTPUT_TOP_LEVEL_KEYS:
            errors.append("public JSON top-level schema differs")
        if set(output.get("summary", {})) != SUMMARY_KEYS:
            errors.append("public JSON summary schema differs")
        elif output["summary"] != {
            "trackedVendors": 4,
            "substantiveResponses": 0,
            "scoredVendors": 0,
            "purchaseAuthorisations": 0,
        }:
            errors.append("public JSON summary differs from the reviewed current state")
        for vendor in output.get("vendors", []):
            if set(vendor) != OUTPUT_VENDOR_KEYS:
                errors.append("public JSON vendor output schema differs")
            if vendor.get("weightedScore") is not None:
                errors.append("public JSON cannot expose a score before evidence is complete")
        scan_privacy("public vendor-response JSON", output, errors)

    if output_csv_bytes:
        text = output_csv_bytes.decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(text)))
        if not rows or list(rows[0]) != CSV_FIELDS:
            errors.append("public vendor-response CSV columns differ")
        if len(rows) != 4:
            errors.append("public vendor-response CSV must contain exactly four rows")
        for row in rows:
            if row.get("scoringState") != "not_scored" or row.get("weightedScore") != "":
                errors.append("public CSV missing evidence must remain not_scored with a blank score")
            if row.get("purchaseAuthorised") != "false":
                errors.append("public CSV purchaseAuthorised must remain false")
        scan_privacy("public vendor-response CSV", text, errors)


def validate_site_integration(errors: list[str]) -> None:
    try:
        html = REVIEW_HTML.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append("site/review.html is missing")
        return
    if 'data-vendor-response' not in html:
        errors.append("review page lacks the vendor-response control section")
    if 'src="assets/vendor-response.js' not in html:
        errors.append("review page does not load vendor-response.js")
    if 'href="data/vendor-response-control.csv"' not in html:
        errors.append("review page lacks the public vendor-response CSV download")
    if 'href="data/vendor-response-control.json"' not in html:
        errors.append("review page lacks the public vendor-response JSON download")
    if not VENDOR_SCRIPT.is_file():
        errors.append("site/assets/vendor-response.js is missing")


def main() -> None:
    errors: list[str] = []
    try:
        source = read_json(SOURCE_PATH)
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: cannot load canonical vendor-response source: {error}", file=sys.stderr)
        raise SystemExit(1)

    validate_source(source, errors)
    if not errors:
        validate_outputs(source, errors)
    validate_site_integration(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Validation failed with {len(errors)} error(s).", file=sys.stderr)
        raise SystemExit(1)

    output = normalised(source)
    print(
        "Validated privacy-safe vendor-response control: "
        f'{output["summary"]["trackedVendors"]} tracked, '
        f'{output["summary"]["substantiveResponses"]} substantive responses, '
        f'{output["summary"]["scoredVendors"]} scored, '
        f'{output["summary"]["purchaseAuthorisations"]} purchase authorisations.'
    )


if __name__ == "__main__":
    main()
