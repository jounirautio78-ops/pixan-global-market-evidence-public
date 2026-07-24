#!/usr/bin/env python3
"""Fail-closed validation for v18 evidence lanes, donor controls and scenarios."""

from __future__ import annotations

import json
import math
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from public_privacy_guard import contains_private_identifier


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"
SITE = ROOT / "site"
DATA = SITE / "data"
SCHEMAS = SOURCE / "schemas"
PUBLIC_SCHEMAS = SITE / "schemas"

SOURCE_LANES = SOURCE / "evidence-lanes.json"
SOURCE_DONORS = SOURCE / "donor-cockpit.json"
SOURCE_SCENARIOS = SOURCE / "country-scenarios.json"
PUBLIC_LANES = DATA / "evidence-lanes.json"
PUBLIC_DONORS = DATA / "donor-cockpit.json"
PUBLIC_SCENARIOS = DATA / "country-scenarios.json"
MARKET = DATA / "market-values.json"
INDEX = SITE / "index.html"
APP = SITE / "assets" / "app.js"

EXPECTED_LANES = [
    "public_reproducible",
    "licensed_controlled",
    "private_pending_review",
]
EXPECTED_CRITERIA = [f"D{index}" for index in range(1, 11)]
RANGE_KEYS = ["low", "base", "high"]
NZ_2024_COMPONENTS = {
    "low": (258327110.88, 275335272.80, 533662383.68),
    "base": (274180410.21, 367631277.68, 641811687.89),
    "high": (274180410.21, 456995382.29, 731175792.50),
}
STATUS_VALUES = {"passed", "failed", "open"}
SENSITIVE_KEYS = {
    "address",
    "brand",
    "businessid",
    "businessname",
    "companyname",
    "contact",
    "email",
    "filename",
    "licenceid",
    "licenseid",
    "name",
    "rawrecord",
    "rawrecords",
    "respondent",
    "respondentname",
    "sender",
    "upc",
}
REQUIRED_HTML_IDS = {
    "market-evidence-lanes",
    "market-evidence-lane-grid",
    "market-donor-ledger",
    "market-donor-matrix-head",
    "market-donor-matrix-body",
    "market-donor-control-body",
    "market-scenario-lab",
    "market-scenario-global",
    "market-scenario-cards",
}
REQUIRED_APP_TOKENS = {
    "assessEvidenceLanes",
    "assessDonorLedger",
    "assessScenarioInputs",
    "assessScenarioComponents",
    "formatScenarioComponent",
    "assessScenarioLab",
    'fetch("data/evidence-lanes.json"',
    'fetch("data/donor-cockpit.json"',
    'fetch("data/country-scenarios.json"',
    'candidate?.evidenceLaneId === "public_reproducible"',
    "acceptedDonors >= minimumDonors && coveragePassed",
    "official_table_derived:",
    '"not_computed"',
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_date(value: Any) -> date | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def is_safe_https(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and parsed.username is None
        and parsed.password is None
    )


def walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(re.sub(r"[^a-z0-9]", "", str(key).casefold()))
            keys.update(walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(walk_keys(child))
    return keys


def validate_schema_documents(errors: list[str]) -> None:
    expected = {
        "evidence-lanes.schema.json": "Pixan public evidence lanes",
        "donor-cockpit.schema.json": "Pixan public donor-conversion cockpit",
        "country-scenarios.schema.json": "Pixan public country-year scenario controls",
    }
    for filename, title in expected.items():
        path = SCHEMAS / filename
        public_path = PUBLIC_SCHEMAS / filename
        if not path.is_file():
            errors.append(f"Missing source schema {filename}")
            continue
        if not public_path.is_file():
            errors.append(f"Missing public schema {filename}")
            continue
        if path.read_bytes() != public_path.read_bytes():
            errors.append(f"{filename}: public schema differs from the reviewed source")
        schema = load_json(path)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append(f"{filename}: JSON Schema draft must remain 2020-12")
        if schema.get("title") != title or schema.get("type") != "object":
            errors.append(f"{filename}: schema identity differs from the reviewed control")


def validate_lanes(lanes: dict[str, Any], errors: list[str]) -> None:
    if set(lanes) != {"schemaVersion", "asOf", "publicBuildPolicy", "lanes"}:
        errors.append("Evidence lanes must use the exact reviewed top-level schema")
    if lanes.get("schemaVersion") != "1.0":
        errors.append("Evidence-lane schemaVersion must remain 1.0")
    if parse_date(lanes.get("asOf")) is None:
        errors.append("Evidence-lane asOf must be an ISO date")

    policy = lanes.get("publicBuildPolicy")
    if not isinstance(policy, dict):
        errors.append("Evidence lanes require a publicBuildPolicy object")
        policy = {}
    if policy.get("allowedRecordLaneIds") != ["public_reproducible"]:
        errors.append("Only public_reproducible may carry records in the public build")
    if set(policy.get("metadataOnlyLaneIds", [])) != {
        "licensed_controlled",
        "private_pending_review",
    }:
        errors.append("Licensed and private lanes must remain metadata-only")

    records = lanes.get("lanes")
    if not isinstance(records, list) or len(records) != 3:
        errors.append("Evidence lanes must contain exactly three reviewed lane records")
        return
    ids = [item.get("laneId") for item in records if isinstance(item, dict)]
    if ids != EXPECTED_LANES:
        errors.append("Evidence lanes must remain ordered public, licensed, private")
    for index, item in enumerate(records):
        path = f"lanes[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path}: lane must be an object")
            continue
        if item.get("order") != index + 1:
            errors.append(f"{path}: lane order must be deterministic")
        for key in (
            "titleEn",
            "titleFi",
            "purposeEn",
            "purposeFi",
            "publicationRuleEn",
            "publicationRuleFi",
        ):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"{path}.{key} must be a non-empty string")
        if item.get("laneId") == "public_reproducible":
            if (
                item.get("publicExposure") != "reviewed_aggregate_records"
                or item.get("dataState") != "reviewed_aggregate_records_available"
            ):
                errors.append("The public lane must remain reviewed aggregates only")
        elif (
            item.get("publicExposure") != "metadata_placeholder_only"
            or item.get("dataState") != "no_public_records"
        ):
            errors.append(f"{path}: controlled lanes must expose empty metadata placeholders only")
        if any(key in item for key in ("records", "values", "rows", "extracts", "files")):
            errors.append(f"{path}: lane metadata must not embed records or source extracts")


def market_indexes(market: dict[str, Any]) -> tuple[set[str], set[str], dict[str, dict[str, Any]]]:
    observations = {
        item.get("observationId")
        for item in market.get("observations", [])
        if isinstance(item, dict) and isinstance(item.get("observationId"), str)
    }
    models = {
        item.get("modelId")
        for item in market.get("models", [])
        if isinstance(item, dict) and isinstance(item.get("modelId"), str)
    }
    sources = {
        item.get("sourceId"): item
        for item in market.get("sources", [])
        if isinstance(item, dict) and isinstance(item.get("sourceId"), str)
    }
    return observations, models, sources


def computed_donor_decision(
    candidate: dict[str, Any],
    expected_criteria: list[str] = EXPECTED_CRITERIA,
) -> str:
    statuses = candidate.get("criterionStatuses")
    if not isinstance(statuses, list):
        return "not_accepted"
    by_id = {
        item.get("criterionId"): item.get("status")
        for item in statuses
        if isinstance(item, dict)
    }
    complete_pass = (
        len(statuses) == len(expected_criteria)
        and set(by_id) == set(expected_criteria)
        and all(by_id.get(criterion_id) == "passed" for criterion_id in expected_criteria)
    )
    return (
        "accepted"
        if candidate.get("candidateType") == "country_year" and complete_pass
        else "not_accepted"
    )


def validate_donors(
    cockpit: dict[str, Any],
    market: dict[str, Any],
    errors: list[str],
) -> int:
    if set(cockpit) != {"schemaVersion", "asOf", "protocol", "gate", "candidates"}:
        errors.append("Donor cockpit must use the exact reviewed top-level schema")
    as_of = parse_date(cockpit.get("asOf"))
    if cockpit.get("schemaVersion") != "1.0" or as_of is None:
        errors.append("Donor cockpit requires schemaVersion 1.0 and an ISO asOf date")

    protocol = cockpit.get("protocol")
    if not isinstance(protocol, dict):
        errors.append("Donor cockpit requires a protocol object")
        protocol = {}
    criteria = protocol.get("criteria")
    if protocol.get("protocolVersion") != "1.0" or not isinstance(criteria, list):
        errors.append("Donor protocol must remain version 1.0 with ten criteria")
        criteria = []
    criterion_ids = [
        item.get("criterionId")
        for item in criteria
        if isinstance(item, dict)
    ]
    if criterion_ids != EXPECTED_CRITERIA:
        errors.append("Donor criteria must remain ordered D1 through D10")
    for index, item in enumerate(criteria):
        if not isinstance(item, dict):
            errors.append(f"protocol.criteria[{index}] must be an object")
            continue
        for key in ("titleEn", "titleFi", "requirementEn", "requirementFi"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"protocol.criteria[{index}].{key} must be non-empty")

    gate = cockpit.get("gate")
    if not isinstance(gate, dict):
        errors.append("Donor cockpit requires a gate object")
        gate = {}
    if gate.get("minimumAcceptedDonors") != 3:
        errors.append("Public global gate requires exactly three accepted donors")
    if gate.get("coverageGateRequired") is not True:
        errors.append("The donor coverage gate must remain mandatory")
    if gate.get("coverageGateStatus") not in {"not_met", "passed"}:
        errors.append("Donor coverageGateStatus must be not_met or passed")

    observations, models, sources = market_indexes(market)
    candidates = cockpit.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        errors.append("Donor cockpit must contain at least one candidate")
        return 0
    candidate_ids: set[str] = set()
    accepted = 0
    for index, candidate in enumerate(candidates):
        path = f"candidates[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{path}: candidate must be an object")
            continue
        candidate_id = candidate.get("candidateId")
        if not isinstance(candidate_id, str) or not candidate_id:
            errors.append(f"{path}.candidateId must be non-empty")
        elif candidate_id in candidate_ids:
            errors.append(f"Duplicate donor candidateId {candidate_id}")
        candidate_ids.add(candidate_id)
        if candidate.get("evidenceLaneId") != "public_reproducible":
            errors.append(f"{path}: public donor records must remain in public_reproducible")
        candidate_type = candidate.get("candidateType")
        country = candidate.get("countryIso2")
        if candidate_type == "country_year":
            if not isinstance(country, str) or not re.fullmatch(r"[A-Z]{2}", country):
                errors.append(f"{path}: country_year candidates require an ISO2 country")
        elif candidate_type == "regional_benchmark":
            if country is not None:
                errors.append(f"{path}: regional benchmarks must not claim a country ISO2")
        else:
            errors.append(f"{path}.candidateType is invalid")
        if not isinstance(candidate.get("year"), int):
            errors.append(f"{path}.year must be an integer")

        statuses = candidate.get("criterionStatuses")
        if not isinstance(statuses, list) or len(statuses) != 10:
            errors.append(f"{path}: each candidate requires exactly D1-D10 statuses")
            statuses = []
        status_ids = [
            item.get("criterionId")
            for item in statuses
            if isinstance(item, dict)
        ]
        if status_ids != EXPECTED_CRITERIA:
            errors.append(f"{path}: criterion statuses must remain ordered D1-D10")
        if any(
            not isinstance(item, dict) or item.get("status") not in STATUS_VALUES
            for item in statuses
        ):
            errors.append(f"{path}: criterion status must be passed, failed or open")

        computed = computed_donor_decision(candidate)
        if candidate.get("declaredDecision") != computed:
            errors.append(f"{path}: declared donor decision does not match D1-D10 computation")
        if computed == "accepted":
            accepted += 1

        reference_type = candidate.get("referenceType")
        reference_id = candidate.get("referenceId")
        if (
            reference_type == "observation"
            and reference_id not in observations
        ) or (
            reference_type == "model"
            and reference_id not in models
        ) or reference_type not in {"observation", "model"}:
            errors.append(f"{path}: referenced market observation or model does not resolve")

        source_ids = candidate.get("sourceIds")
        if not isinstance(source_ids, list) or not source_ids or len(source_ids) != len(set(source_ids)):
            errors.append(f"{path}: sourceIds must be a non-empty unique list")
            source_ids = []
        for source_id in source_ids:
            source = sources.get(source_id)
            if not source or not is_safe_https(source.get("pageUrl") or source.get("downloadUrl")):
                errors.append(f"{path}: unresolved or unsafe public source {source_id}")

        reviewed_at = parse_date(candidate.get("lastReviewedAt"))
        if reviewed_at is None or (as_of and reviewed_at > as_of):
            errors.append(f"{path}.lastReviewedAt must be an ISO date no later than asOf")
        for key in (
            "headlineEn",
            "headlineFi",
            "blockerEn",
            "blockerFi",
            "nextEvidenceEn",
            "nextEvidenceFi",
            "acquisitionRouteEn",
            "acquisitionRouteFi",
            "responseStatus",
            "licenseStatus",
        ):
            if not isinstance(candidate.get(key), str) or not candidate[key].strip():
                errors.append(f"{path}.{key} must be non-empty")
    return accepted


def range_status(
    inputs: Any,
    sources: dict[str, dict[str, Any]],
) -> tuple[str, dict[str, float | None]]:
    values: dict[str, float | None] = {key: None for key in RANGE_KEYS}
    if not isinstance(inputs, dict) or set(inputs) != set(RANGE_KEYS):
        return "not_computed", values
    for key in RANGE_KEYS:
        item = inputs.get(key)
        if not isinstance(item, dict) or set(item) != {"value", "sourceIds"}:
            return "not_computed", values
        value = item.get("value")
        source_ids = item.get("sourceIds")
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or value <= 0
            or not isinstance(source_ids, list)
            or not source_ids
            or len(source_ids) != len(set(source_ids))
        ):
            return "not_computed", values
        if any(
            source_id not in sources
            or not is_safe_https(
                sources[source_id].get("pageUrl")
                or sources[source_id].get("downloadUrl")
            )
            for source_id in source_ids
        ):
            return "not_computed", values
        values[key] = float(value)
    if not (
        values["low"] <= values["base"] <= values["high"]  # type: ignore[operator]
    ):
        return "not_computed", {key: None for key in RANGE_KEYS}
    return "computed", values


def validate_component_breakdown(
    record: dict[str, Any],
    input_values: dict[str, float | None],
    path: str,
    errors: list[str],
) -> None:
    breakdown = record.get("componentBreakdown")
    if not isinstance(breakdown, dict) or set(breakdown) != set(RANGE_KEYS):
        errors.append(f"{path}: computed scenario requires low/base/high component arithmetic")
        return

    expected_treatments = {
        "low": "exact_row_deduplicated_both_components",
        "base": "reported_specialist_and_raw_rps_rows",
        "high": "reported_specialist_and_raw_rps_rows",
    }
    for key in RANGE_KEYS:
        component = breakdown.get(key)
        component_path = f"{path}.componentBreakdown.{key}"
        if not isinstance(component, dict) or set(component) != {
            "specialistRetailNzd",
            "generalRetailRpsNzd",
            "combinedNzd",
            "rowTreatment",
        }:
            errors.append(f"{component_path}: component arithmetic must use the reviewed fields")
            continue
        values = [
            component.get("specialistRetailNzd"),
            component.get("generalRetailRpsNzd"),
            component.get("combinedNzd"),
        ]
        if any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or value <= 0
            for value in values
        ):
            errors.append(f"{component_path}: component values must be finite and positive")
            continue
        specialist, general_rps, combined = (float(value) for value in values)
        if not math.isclose(specialist + general_rps, combined, abs_tol=0.01):
            errors.append(f"{component_path}: component arithmetic does not add to combinedNzd")
        if input_values.get(key) is None or not math.isclose(
            combined,
            float(input_values[key]),
            abs_tol=0.01,
        ):
            errors.append(f"{component_path}: combinedNzd does not match the published scenario input")
        if component.get("rowTreatment") != expected_treatments[key]:
            errors.append(f"{component_path}: row treatment does not match the reviewed sensitivity")
        if record.get("scenarioId") == "NZ-2024-RETAIL-RANGE":
            expected = NZ_2024_COMPONENTS[key]
            if any(
                not math.isclose(actual, target, abs_tol=0.01)
                for actual, target in zip(
                    (specialist, general_rps, combined),
                    expected,
                )
            ):
                errors.append(f"{component_path}: values differ from the reviewed NZ 2024 release")


def validate_scenarios(
    scenarios: dict[str, Any],
    cockpit: dict[str, Any],
    market: dict[str, Any],
    accepted_donors: int,
    errors: list[str],
) -> None:
    if set(scenarios) != {
        "schemaVersion",
        "asOf",
        "calculationPolicy",
        "globalGate",
        "countryYearScenarios",
        "globalScenario",
    }:
        errors.append("Country scenarios must use the exact reviewed top-level schema")
    if scenarios.get("schemaVersion") != "1.0" or parse_date(scenarios.get("asOf")) is None:
        errors.append("Country scenarios require schemaVersion 1.0 and an ISO asOf date")

    policy = scenarios.get("calculationPolicy")
    if not isinstance(policy, dict):
        errors.append("Country scenarios require a calculationPolicy object")
        policy = {}
    if policy.get("requiredRangeInputs") != RANGE_KEYS:
        errors.append("Country scenarios must require low, base and high in order")
    if (
        policy.get("missingInputStatus") != "not_computed"
        or policy.get("computedStatus") != "computed"
    ):
        errors.append("Missing scenario inputs must remain not_computed")

    global_gate = scenarios.get("globalGate")
    if not isinstance(global_gate, dict):
        errors.append("Country scenarios require a globalGate object")
        global_gate = {}
    if global_gate.get("minimumAcceptedDonors") != 3:
        errors.append("Scenario global gate must require three accepted donors")
    if global_gate.get("coverageGateStatus") not in {"not_met", "passed"}:
        errors.append("Scenario coverageGateStatus must be not_met or passed")
    cockpit_gate = cockpit.get("gate", {})
    if global_gate.get("coverageGateStatus") != cockpit_gate.get("coverageGateStatus"):
        errors.append("Scenario and donor coverage-gate states must match")
    requirements = global_gate.get("coverageRequirements")
    if not isinstance(requirements, list) or not requirements:
        errors.append("Global coverage gate requires explicit coverage requirements")
        requirements = []
    coverage_passed = (
        global_gate.get("coverageGateStatus") == "passed"
        and cockpit_gate.get("coverageGateStatus") == "passed"
        and bool(requirements)
        and all(
            isinstance(item, dict) and item.get("status") == "passed"
            for item in requirements
        )
    )

    _, _, sources = market_indexes(market)
    records = scenarios.get("countryYearScenarios")
    if not isinstance(records, list) or not records:
        errors.append("Country scenario lab requires at least one country-year record")
        records = []
    scenario_ids: set[str] = set()
    for index, record in enumerate(records):
        path = f"countryYearScenarios[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{path}: scenario must be an object")
            continue
        scenario_id = record.get("scenarioId")
        if not isinstance(scenario_id, str) or not scenario_id:
            errors.append(f"{path}.scenarioId must be non-empty")
        elif scenario_id in scenario_ids:
            errors.append(f"Duplicate scenarioId {scenario_id}")
        scenario_ids.add(scenario_id)
        if record.get("evidenceLaneId") != "public_reproducible":
            errors.append(f"{path}: public scenarios must remain in public_reproducible")
        if not isinstance(record.get("countryIso2"), str) or not re.fullmatch(
            r"[A-Z]{2}", record["countryIso2"]
        ):
            errors.append(f"{path}: scenario requires an ISO2 country")
        if not isinstance(record.get("year"), int):
            errors.append(f"{path}.year must be an integer")
        if not isinstance(record.get("currency"), str) or not re.fullmatch(
            r"[A-Z]{3}", record["currency"]
        ):
            errors.append(f"{path}.currency must be ISO 4217-like")
        computed, input_values = range_status(record.get("inputs"), sources)
        if record.get("declaredStatus") != computed:
            errors.append(f"{path}: missing or invalid inputs must return not_computed")
        if computed == "computed":
            if record.get("evidenceStatus") != "supported_model_not_observed_national_value":
                errors.append(f"{path}: computed sensitivity must remain labelled as a supported model, not an observed national value")
            if record.get("accepted") is not False:
                errors.append(f"{path}: a computed scenario must not become an accepted donor implicitly")
            for key in ("scenarioScope", "taxBasis", "coverageStatus", "independentReconciliationStatus", "methodEn", "methodFi"):
                if not isinstance(record.get(key), str) or not record[key].strip():
                    errors.append(f"{path}.{key} must document a computed scenario")
            if record.get("scenarioId") == "NZ-2024-RETAIL-RANGE" and (
                record.get("taxBasis") != "GST_unknown"
                or record.get("coverageStatus") != "incomplete"
                or record.get("independentReconciliationStatus") != "not_met"
            ):
                errors.append(
                    "NZ-2024 scenario must retain GST unknown, incomplete coverage and no independent reconciliation"
                )
            validate_component_breakdown(record, input_values, path, errors)
        if not isinstance(record.get("blockerEn"), str) or not isinstance(
            record.get("blockerFi"), str
        ):
            errors.append(f"{path}: blockers must be bilingual")

    global_record = scenarios.get("globalScenario")
    if not isinstance(global_record, dict):
        errors.append("globalScenario must be an object")
        return
    input_status, global_values = range_status(global_record.get("inputs"), sources)
    gates_passed = (
        accepted_donors >= global_gate.get("minimumAcceptedDonors", 3)
        and coverage_passed
    )
    expected_status = "computed" if gates_passed and input_status == "computed" else "not_computed"
    if global_record.get("declaredStatus") != expected_status:
        errors.append("Global scenario status must be computed from donor and coverage gates")
    if not gates_passed and any(value is not None for value in global_values.values()):
        errors.append("A blocked global gate must not carry a public global total")
    if not gates_passed:
        raw_inputs = global_record.get("inputs", {})
        if any(
            isinstance(raw_inputs.get(key), dict)
            and raw_inputs[key].get("value") is not None
            for key in RANGE_KEYS
        ):
            errors.append("Global values must remain null until both global gates pass")


def validate_structure(index_html: str, app_js: str, errors: list[str]) -> None:
    for element_id in sorted(REQUIRED_HTML_IDS):
        if f'id="{element_id}"' not in index_html:
            errors.append(f"Missing v18 site hook #{element_id}")
    for token in sorted(REQUIRED_APP_TOKENS):
        if token not in app_js:
            errors.append(f"Missing v18 fail-closed app control: {token}")


def validate_privacy(
    lanes: dict[str, Any],
    cockpit: dict[str, Any],
    scenarios: dict[str, Any],
    errors: list[str],
) -> None:
    combined = {"lanes": lanes, "cockpit": cockpit, "scenarios": scenarios}
    sensitive = walk_keys(combined) & SENSITIVE_KEYS
    if sensitive:
        errors.append(f"Public control files contain sensitive field names: {sorted(sensitive)}")
    serialised = json.dumps(combined, ensure_ascii=False, sort_keys=True)
    if contains_private_identifier(serialised):
        errors.append("Public control files contain a blocked private identifier")
    if re.search(r"/Users/|[A-Za-z]:\\\\|file://|dropbox\\.com/(?:home|scl)/", serialised, re.I):
        errors.append("Public control files contain a local or private storage path")
    for candidate in cockpit.get("candidates", []):
        if isinstance(candidate, dict) and candidate.get("evidenceLaneId") != "public_reproducible":
            errors.append("Non-public donor data leaked into the public cockpit")
    for scenario in scenarios.get("countryYearScenarios", []):
        if isinstance(scenario, dict) and scenario.get("evidenceLaneId") != "public_reproducible":
            errors.append("Non-public scenario data leaked into the public scenario lab")


def validate_donor_controls(
    lanes: dict[str, Any],
    cockpit: dict[str, Any],
    scenarios: dict[str, Any],
    market: dict[str, Any],
    index_html: str,
    app_js: str,
) -> list[str]:
    errors: list[str] = []
    validate_lanes(lanes, errors)
    accepted = validate_donors(cockpit, market, errors)
    validate_scenarios(scenarios, cockpit, market, accepted, errors)
    validate_structure(index_html, app_js, errors)
    validate_privacy(lanes, cockpit, scenarios, errors)
    return errors


def main() -> int:
    errors: list[str] = []
    validate_schema_documents(errors)
    paths = [
        SOURCE_LANES,
        SOURCE_DONORS,
        SOURCE_SCENARIOS,
        PUBLIC_LANES,
        PUBLIC_DONORS,
        PUBLIC_SCENARIOS,
        MARKET,
        INDEX,
        APP,
    ]
    for path in paths:
        if not path.is_file():
            errors.append(f"Missing required v18 control file: {path.relative_to(ROOT)}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    source_lanes = load_json(SOURCE_LANES)
    source_donors = load_json(SOURCE_DONORS)
    source_scenarios = load_json(SOURCE_SCENARIOS)
    public_lanes = load_json(PUBLIC_LANES)
    public_donors = load_json(PUBLIC_DONORS)
    public_scenarios = load_json(PUBLIC_SCENARIOS)
    if source_lanes != public_lanes:
        errors.append("Public evidence-lane data must match its reviewed source")
    if source_donors != public_donors:
        errors.append("Public donor-cockpit data must match its reviewed source")
    if source_scenarios != public_scenarios:
        errors.append("Public country-scenario data must match its reviewed source")

    errors.extend(
        validate_donor_controls(
            public_lanes,
            public_donors,
            public_scenarios,
            load_json(MARKET),
            INDEX.read_text(encoding="utf-8"),
            APP.read_text(encoding="utf-8"),
        )
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        "Validated v18 evidence lanes, D1-D10 donor computation, "
        "scenario gates and public-data privacy."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
