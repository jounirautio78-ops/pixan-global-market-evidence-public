#!/usr/bin/env python3
"""Validate the source-only United States independent benchmark control."""

from __future__ import annotations

import json
import math
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CONTROL_PATH = ROOT / "source" / "US_INDEPENDENT_BENCHMARK_CONTROL_2026-07-28.json"
SCHEMA_PATH = ROOT / "source" / "schemas" / "us-independent-benchmark-sample.schema.json"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    control = json.loads(CONTROL_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    require(control.get("asOf") == "2026-07-28", "control asOf must be 2026-07-28", errors)
    require(control.get("verifiedOn") == "2026-07-28", "control verification date mismatch", errors)

    boundary = control.get("publicBoundary", {})
    for key in (
        "containsLicensedRawData",
        "containsPersonalData",
        "containsPrivateCorrespondence",
        "changesMarketTotals",
        "changesDonorStatus",
        "purchaseAuthorised",
    ):
        require(boundary.get(key) is False, f"public boundary {key} must be false", errors)
    require(boundary.get("officialSourcesOnly") is True, "officialSourcesOnly must be true", errors)

    sources = control.get("sources", [])
    source_ids = [item.get("sourceId") for item in sources]
    require(len(source_ids) == len(set(source_ids)), "source IDs must be unique", errors)
    required_source_ids = {
        "US-FTC-E-CIGARETTE-REPORT-2021",
        "US-FTC-E-CIGARETTE-REPORT-2015-2018",
        "US-CDC-ECIGARETTE-SALES-JUNE-2024",
        "US-WI-DOR-CIGARETTE-OTP-COLLECTIONS",
        "US-NC-DOR-STATISTICAL-ABSTRACT-2024",
        "US-CENSUS-INTERNATIONAL-TRADE-API",
        "US-USITC-HTS-854340",
    }
    require(set(source_ids) == required_source_ids, "official source set mismatch", errors)
    allowed_hosts = {
        "www.ftc.gov",
        "www.cdc.gov",
        "www.revenue.wi.gov",
        "www.ncdor.gov",
        "www.census.gov",
        "hts.usitc.gov",
    }
    for source in sources:
        require(source.get("verifiedOn") == "2026-07-28", f"{source.get('sourceId')}: verification date mismatch", errors)
        for url_key in ("pageUrl", "downloadUrl"):
            url = source.get(url_key)
            if not url:
                continue
            parsed = urlparse(url)
            require(parsed.scheme == "https", f"{source.get('sourceId')}: URL must use HTTPS", errors)
            require(parsed.netloc in allowed_hosts, f"{source.get('sourceId')}: non-official host {parsed.netloc}", errors)

    observations = control.get("observations", [])
    observation_by_id = {item.get("recordId"): item for item in observations}
    require(len(observation_by_id) == len(observations), "observation IDs must be unique", errors)

    required_schema_fields = set(schema.get("required", []))
    expected_schema_fields = {
        "recordId",
        "sourceId",
        "sourceVersion",
        "verifiedOn",
        "geography",
        "periodType",
        "periodLabel",
        "productSegment",
        "channel",
        "transactionStage",
        "metric",
        "value",
        "unit",
        "currency",
        "taxBasis",
        "recordStatus",
        "coverageStatus",
        "revisionStatus",
        "sourceUrl",
        "licenceClass",
        "retailSalesEligible",
    }
    require(required_schema_fields == expected_schema_fields, "sample schema required-field set mismatch", errors)

    for observation in observations:
        missing = sorted(required_schema_fields - set(observation))
        require(not missing, f"{observation.get('recordId')}: missing schema fields {missing}", errors)
        require(observation.get("sourceId") in required_source_ids, f"{observation.get('recordId')}: unknown source", errors)
        require(observation.get("verifiedOn") == "2026-07-28", f"{observation.get('recordId')}: verification date mismatch", errors)
        require(observation.get("retailSalesEligible") is False, f"{observation.get('recordId')}: must not be retail-rollup eligible", errors)

    expected_ftc = {
        2015: (259984551, 44185495, 304170046),
        2016: (417302598, 68404886, 485707484),
        2017: (707415500, 72420899, 779836399),
        2018: (1969019051, 74683954, 2043703005),
        2019: (2633333620, 69274687, 2702608307),
        2020: (2132503069, 261920036, 2394423105),
        2021: (2496219204, 267065134, 2763284338),
    }
    for year, (cartridge, disposable, total) in expected_ftc.items():
        record_id = f"US-FTC-{year}-CARTRIDGE-DISPOSABLE-SALES"
        row = observation_by_id.get(record_id, {})
        components = row.get("components", {})
        require(row.get("value") == total, f"{record_id}: FTC total mismatch", errors)
        require(components.get("cartridgeSystemUsd") == cartridge, f"{record_id}: cartridge component mismatch", errors)
        require(components.get("disposableUsd") == disposable, f"{record_id}: disposable component mismatch", errors)
        require(cartridge + disposable == total, f"{record_id}: FTC arithmetic failed", errors)
        require(row.get("transactionStage") == "manufacturer_reported_sales", f"{record_id}: stage mismatch", errors)

    cdc_value = observation_by_id.get("US-CDC-2024-JUNE-FOUR-WEEK-RETAIL-SALES-USD", {})
    cdc_units = observation_by_id.get("US-CDC-2024-JUNE-FOUR-WEEK-RETAIL-UNITS", {})
    require(cdc_value.get("value") == 488900000, "CDC June 2024 dollar checkpoint mismatch", errors)
    require(cdc_units.get("value") == 21100000, "CDC June 2024 unit checkpoint mismatch", errors)
    for row in (cdc_value, cdc_units):
        require(row.get("periodType") == "four_week_period", "CDC checkpoint must remain four-week", errors)
        require(row.get("coverageStatus") == "partial_brick_and_mortar", "CDC channel boundary mismatch", errors)

    expected_wi = {
        2022: 82516317,
        2023: 141245968,
        2024: 142107893,
        2025: 161408755,
    }
    for year, expected_value in expected_wi.items():
        record_id = f"US-WI-FY{year}-TAXABLE-VAPOR-ML"
        row = observation_by_id.get(record_id, {})
        require(row.get("value") == expected_value, f"{record_id}: Wisconsin value mismatch", errors)
        require(row.get("transactionStage") == "state_excise_tax_base", f"{record_id}: Wisconsin stage mismatch", errors)
        require(row.get("unit") == "millilitre", f"{record_id}: Wisconsin unit mismatch", errors)

    expected_nc = {
        2022: (6507171, 130143420),
        2023: (6676754, 133535080),
        2024: (6429692, 128593840),
    }
    for year, (receipt, volume) in expected_nc.items():
        receipt_id = f"US-NC-FY{year}-VAPOR-TAX-RECEIPTS"
        volume_id = f"US-NC-FY{year}-DERIVED-TAXABLE-VAPOR-ML"
        receipt_row = observation_by_id.get(receipt_id, {})
        volume_row = observation_by_id.get(volume_id, {})
        require(receipt_row.get("value") == receipt, f"{receipt_id}: receipt mismatch", errors)
        require(volume_row.get("value") == volume, f"{volume_id}: derived volume mismatch", errors)
        derivation = volume_row.get("derivation", {})
        require(derivation.get("sourceRecordId") == receipt_id, f"{volume_id}: source link mismatch", errors)
        rate = derivation.get("taxRateUsdPerMl")
        require(rate == 0.05, f"{volume_id}: tax rate mismatch", errors)
        if rate:
            require(math.isclose(receipt / rate, volume, rel_tol=0, abs_tol=1e-9), f"{volume_id}: receipt/rate arithmetic failed", errors)

    import_route = control.get("queuedImportRoute", {})
    require(import_route.get("status") == "queued_not_computed", "import route must remain queued", errors)
    require(import_route.get("result") is None, "import route result must remain null", errors)
    require(import_route.get("retailSalesEligible") is False, "import route must not be retail eligible", errors)
    require(len(import_route.get("blockers", [])) >= 3, "import route blockers incomplete", errors)

    policy = control.get("reconciliationPolicy", {})
    require(policy.get("mechanicalAdditionAcrossStages") is False, "mechanical addition must be blocked", errors)
    forbidden = set(policy.get("forbiddenOperations", []))
    require(
        {
            "add_manufacturer_sales_to_retail_sales",
            "add_state_tax_bases_to_national_retail_value",
            "add_import_value_to_domestic_sales",
            "annualise_single_four_week_checkpoint",
            "treat_missing_channels_as_zero",
        }.issubset(forbidden),
        "non-addition locks incomplete",
        errors,
    )

    sample_acceptance = control.get("sampleAcceptance", {})
    gate_ids = [gate.get("id") for gate in sample_acceptance.get("gates", [])]
    require(gate_ids == [f"G{number}" for number in range(1, 7)], "G1-G6 gate set mismatch", errors)
    for gate in sample_acceptance.get("gates", []):
        require(bool(gate.get("passLogic")), f"{gate.get('id')}: pass logic missing", errors)
        require(bool(gate.get("failLogic")), f"{gate.get('id')}: fail logic missing", errors)
    current_sample = sample_acceptance.get("currentEvaluation", {})
    require(current_sample.get("scorable") is False, "no sample may be marked scorable", errors)
    for gate_id in gate_ids:
        require(current_sample.get(gate_id) == "not_evaluated", f"{gate_id}: current state must be not_evaluated", errors)

    donor_acceptance = control.get("donorAcceptance", {})
    donor_ids = [criterion.get("id") for criterion in donor_acceptance.get("criteria", [])]
    require(donor_ids == [f"D{number}" for number in range(1, 11)], "D1-D10 criterion set mismatch", errors)
    current_decision = donor_acceptance.get("currentDecision", {})
    require(current_decision.get("existingDeclaredDecision") == "not_accepted", "existing US donor decision mismatch", errors)
    require(current_decision.get("decisionAfterThisPackage") == "not_accepted", "package must not accept US donor", errors)
    require(current_decision.get("decisionChanged") is False, "package must not change donor decision", errors)
    require(current_decision.get("globalRollupEligible") is False, "US must remain outside global roll-up", errors)

    outputs = control.get("outputs", {})
    require(outputs.get("unitedStatesRetailMarketValue") is None, "US retail market value must remain null", errors)
    require(outputs.get("globalMarketValue") is None, "global market value must remain null", errors)
    require(outputs.get("acceptedDonorIncrement") == 0, "accepted donor increment must remain zero", errors)

    if errors:
        print(f"FAIL: {len(errors)} error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "PASS: US independent benchmark control "
        f"({len(sources)} official sources, {len(observations)} observations, "
        "FTC arithmetic + CDC checkpoint + WI/NC tax controls + queued Census/USITC route; "
        "market totals unchanged, donor increment 0)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
