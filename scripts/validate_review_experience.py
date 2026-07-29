#!/usr/bin/env python3
"""Fail-closed validation for the current review surface and evidence baseline."""

from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DATA = SITE / "data"

EXPECTED_OFFICIAL_COUNTRIES = {"CA", "DE", "FI", "NZ", "PL", "SE", "US"}
EXPECTED_PROCESS_STATES = {
    "DE": "registered_processing_notice_received",
    "FI": "registered_processing_notice_received",
}
EXPECTED_AVAILABILITY_STATES = {
    "DK": "official_sales_data_not_held_retailer_registry_identified",
    "IT": "official_aggregate_not_held_public_routes_identified",
}
EXPECTED_STRUCTURAL_STATES = {
    "SE": "official_structural_data_received_sales_not_available",
}
EXPECTED_TRADE_PROXY_STATES = {
    "FR": "official_customs_trade_proxy_received_scope_partial",
}
EXPECTED_MARKET_SOURCE_IDS = {
    "CA-HC-VAPING-SALES-2024",
    "CA-STATCAN-RCS-2019-2022",
    "CA-STATCAN-RCS-2023-2025",
    "DE-DESTATIS-73411-0003",
    "FI-TAX-EXCISE-VVT-010-2025",
    "PL-SEJM-I07255-O1",
    "PL-SEJM-I17526-O1",
    "PL-MF-EXCISE-RATES-2025",
    "SE-GOV-BERAKNINGSKONVENTIONER-2026",
    "SE-FHM-PUBLIC-RECORD-RESPONSE-2026-07-24",
    "NZ-MOH-ANNUAL-RETURNS-2022",
    "NZ-MOH-ANNUAL-RETURNS-2023",
    "NZ-MOH-ANNUAL-RETURNS-2024",
    "NZ-MOH-ANNUAL-RETURN-REQUIREMENTS",
    "NZ-MOH-ANNUAL-RETURNS-2024-GUIDE",
    "EU-EC-SWD-2025-560",
    "EU-EC-SWD-2026-111",
    "IMARC-GLOBAL-2025",
    "GVR-GLOBAL-2025",
    "FORTUNE-GLOBAL-2025",
    "INTASTE-GERMANFLAVOURS-2026",
    "INTASTE-SAMURAI-2026",
    "INTASTE-REVOLTAGE-2026",
    "US-FTC-E-CIGARETTE-REPORT-2021",
}
NZ_VAPING_OBSERVATION_ID = "NZ-2024-IDENTIFIED-VAPING-PRODUCT-SALES-RAW-SUM"
NZ_DONOR_CANDIDATE_ID = "NZ-2024-IDENTIFIED-VAPING-RETAIL-SUBTOTAL"
NZ_SOURCE_IDS = [
    "NZ-MOH-ANNUAL-RETURNS-2024",
    "NZ-MOH-ANNUAL-RETURN-REQUIREMENTS",
    "NZ-MOH-ANNUAL-RETURNS-2024-GUIDE",
]
GERMANY_MODEL_ID = "DE-2025-LIQUID-RETAIL-EQUIVALENT-RANGE"
GERMANY_VOLUME_ID = "DE-2025-TAXED-LIQUID-VOLUME-L"
GERMANY_PRICE_IDS = {
    "low": "DE-2026-RETAIL-PRICE-LOW-EUR-PER-ML",
    "central": "DE-2026-RETAIL-PRICE-BASE-EUR-PER-ML",
    "high": "DE-2026-RETAIL-PRICE-HIGH-EUR-PER-ML",
}
GERMANY_OUTPUTS = {
    "low": 667_920_000,
    "central": 1_199_220_000,
    "high": 1_654_620_000,
}
POLAND_RECONSTRUCTION = {
    "PL-2020-E-LIQUID-REPORTED-VOLUME-L": (
        "PL",
        2020,
        "reported_e_liquid_volume",
        1_451_529,
        "litre",
        None,
        "calendar_year",
        "official_observed",
        "official_response",
        "e_liquid_only",
        "official_reported_domestic_sales_intra_eu_acquisition_and_import_volume_not_retail_market_value",
        False,
        False,
        ["PL-SEJM-I07255-O1"],
    ),
    "PL-2021-E-LIQUID-REPORTED-VOLUME-L": (
        "PL",
        2021,
        "reported_e_liquid_volume",
        277_265,
        "litre",
        None,
        "calendar_year",
        "official_observed",
        "official_response",
        "e_liquid_only",
        "official_reported_domestic_sales_intra_eu_acquisition_and_import_volume_not_retail_market_value",
        False,
        False,
        ["PL-SEJM-I07255-O1"],
    ),
    "PL-2022-E-LIQUID-REPORTED-VOLUME-L": (
        "PL",
        2022,
        "reported_e_liquid_volume",
        416_088,
        "litre",
        None,
        "calendar_year",
        "official_observed",
        "official_response",
        "e_liquid_only",
        "official_reported_domestic_sales_intra_eu_acquisition_and_import_volume_not_retail_market_value",
        False,
        False,
        ["PL-SEJM-I07255-O1"],
    ),
    "PL-2023-E-LIQUID-REPORTED-VOLUME-L": (
        "PL",
        2023,
        "reported_e_liquid_volume",
        805_441,
        "litre",
        None,
        "calendar_year",
        "official_observed",
        "official_response",
        "e_liquid_only",
        "official_reported_domestic_sales_intra_eu_acquisition_and_import_volume_not_retail_market_value",
        False,
        False,
        ["PL-SEJM-I07255-O1"],
    ),
    "PL-2025-E-LIQUID-EXCISE-AMOUNT": (
        "PL",
        2025,
        "e_liquid_excise_amount",
        993_100_000,
        "PLN",
        "PLN",
        "calendar_year",
        "official_observed",
        "official_response",
        "e_liquid_only",
        "official_tax_amount_not_retail_market_value",
        False,
        False,
        ["PL-SEJM-I17526-O1"],
    ),
    "PL-2025-VAPING-DEVICE-EXCISE-AMOUNT": (
        "PL",
        2025,
        "vaping_device_excise_amount",
        175_300_000,
        "PLN",
        "PLN",
        "calendar_year",
        "official_observed",
        "official_response",
        "vaping_devices_only",
        "official_tax_amount_not_retail_market_value",
        False,
        False,
        ["PL-SEJM-I17526-O1"],
    ),
    "PL-2025-VAPING-COMPONENT-SETS-EXCISE-AMOUNT": (
        "PL",
        2025,
        "vaping_component_sets_excise_amount",
        2_500_000,
        "PLN",
        "PLN",
        "calendar_year",
        "official_observed",
        "official_response",
        "vaping_component_sets_only",
        "official_tax_amount_not_retail_market_value",
        False,
        False,
        ["PL-SEJM-I17526-O1"],
    ),
    "PL-2025-VAPING-DEVICE-EXCISE-BACKSOLVED-UNITS": (
        "PL",
        2025,
        "vaping_device_excise_backsolved_units",
        4_382_500,
        "unit",
        None,
        "calendar_year",
        "official_table_derived",
        "tax_receipts_divided_by_statutory_rate",
        "vaping_devices_only",
        "derived_taxed_units_not_sales_or_retail_market_value",
        False,
        False,
        ["PL-SEJM-I17526-O1", "PL-MF-EXCISE-RATES-2025"],
    ),
    "PL-2025-VAPING-COMPONENT-SETS-EXCISE-BACKSOLVED-UNITS": (
        "PL",
        2025,
        "vaping_component_sets_excise_backsolved_units",
        62_500,
        "unit",
        None,
        "calendar_year",
        "official_table_derived",
        "tax_receipts_divided_by_statutory_rate",
        "vaping_component_sets_only",
        "derived_taxed_units_not_sales_or_retail_market_value",
        False,
        False,
        ["PL-SEJM-I17526-O1", "PL-MF-EXCISE-RATES-2025"],
    ),
}
REQUIRED_REVIEW_IDS = {
    "decision-cockpit",
    "decision-cockpit-state",
    "decision-cockpit-status",
    "cockpit-meta",
    "cockpit-supported-list",
    "cockpit-not-supported-list",
    "cockpit-gates-list",
    "research-operations-overview",
    "research-operations-metrics",
    "third-donor-programme",
    "third-donor-summary",
    "third-donor-table-wrap",
    "third-donor-country-list",
    "third-donor-follow-ups",
    "third-donor-status",
    "sweden-structure-card",
    "review-calculation-audit",
    "review-calculation-audit-status",
    "review-calculation-audit-summary",
    "review-calculation-audit-steps",
    "review-source-freshness",
    "review-source-freshness-status",
    "review-source-freshness-summary",
    "review-source-freshness-table",
    "review-source-freshness-list",
    "review-donor-ledger",
    "review-donor-protocol-version",
    "review-donor-gate-rule",
    "review-donor-rule",
    "review-donor-summary",
    "review-donor-closure-body",
    "review-donor-closure-status",
    "review-donor-candidates",
    "review-donor-status",
}
REQUIRED_REVIEW_FUNCTIONS = {
    "applyReviewView",
    "assessReviewFxRates",
    "assessReviewEurEquivalent",
    "reviewEurEquivalentNode",
    "reviewFxDisclosureNode",
    "renderDecisionCockpit",
    "renderResearchOperationsOverview",
    "renderThirdDonorScreen",
    "renderThirdDonorScreenUnavailable",
    "renderReviewCalculationAudit",
    "renderReviewCalculationAuditUnavailable",
    "renderReviewSourceFreshness",
    "renderReviewSourceFreshnessUnavailable",
    "assessReviewDonorLedger",
    "renderReviewDonorLedger",
    "renderReviewDonorLedgerUnavailable",
    "renderReviewDonorClosureBoard",
    "renderReviewDonorClosureUnavailable",
}
REQUIRED_I18N_EN = {
    "Workspace views",
    "5-minute Review",
    "Evidence Center",
    "Research Operations",
    "What this release supports—and what it does not",
    "Supported in this release",
    "Not supported by this release",
    "Top 3 decision gates",
    "Calculation audit trail",
    "How current is the evidence?",
    "Market source",
    "Substantive staleness",
    "No automatic publication, spending or external action",
    "Donor-market acceptance gate",
    "The 0/3 gate changes only when a candidate passes every criterion.",
    "3 process-only responses",
    "1 official structural response",
    "1 customs-trade proxy response",
    "0 sales-data responses",
    "The Sweden response contains official registration-structure counts only.",
    "Third-country acquisition screen · not a donor assessment",
    "Where the next official-data programme should focus",
    "Poland is the practical primary programme; Russia is a source-only, high-friction lead",
    "Prepared drafts remain unsent until separately approved",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def valid_https(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc) and not parsed.username and not parsed.password


def parse_date(value: Any) -> date | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def validate_third_donor_screen(screen: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if screen.get("schemaVersion") != "1.0" or screen.get("asOf") != "2026-07-29":
        errors.append("Third-donor screen must use the reviewed v35 date")
    if screen.get("status") != "screening_only_not_donor_assessment":
        errors.append("Third-donor screen must remain screening-only")
    decision = screen.get("decision") if isinstance(screen.get("decision"), dict) else {}
    if (
        decision.get("primaryProgrammeCountryIso2") != "PL"
        or decision.get("sourceOnlyLeadCountryIso2") != "RU"
        or decision.get("secondaryProgrammeCountryIso2") != ["FI", "DK", "FR"]
    ):
        errors.append("Third-donor programme must remain PL primary, RU source-only and FI/DK/FR secondary")
    countries = screen.get("countries") if isinstance(screen.get("countries"), list) else []
    expected_iso2 = ["RU", "PL", "FI", "DK", "FR", "AE", "CN", "GB", "US", "NL", "IT", "ES", "SE", "PH", "SA"]
    if [item.get("countryIso2") for item in countries if isinstance(item, dict)] != expected_iso2:
        errors.append("Third-donor screen must retain the exact 15-country ranking")
    expected_classes = {
        "RU": "source_only_high_friction",
        "PL": "primary_programme",
        "FI": "secondary_programme",
        "DK": "secondary_programme",
        "FR": "secondary_programme",
    }
    for index, country in enumerate(countries):
        if not isinstance(country, dict):
            errors.append("Third-donor country records must be objects")
            continue
        iso2 = country.get("countryIso2")
        if country.get("rank") != index + 1:
            errors.append("Third-donor ranks must remain sequential")
        if country.get("donorStatus") != "not_assessed":
            errors.append("Third-donor countries must remain not assessed")
        if country.get("programmeClass") != expected_classes.get(iso2, "monitor"):
            errors.append("Third-donor programme classes differ from the reviewed decision")
        sources = country.get("officialSources") if isinstance(country.get("officialSources"), list) else []
        if not sources or any(not valid_https(source.get("url")) for source in sources if isinstance(source, dict)):
            errors.append("Third-donor country routes require safe official HTTPS sources")
    wave = screen.get("followUpWave") if isinstance(screen.get("followUpWave"), dict) else {}
    if wave.get("dueOn") != "2026-07-28" or wave.get("draftState") != "completed_or_superseded":
        errors.append("Third-donor follow-ups must remain completed or superseded for 2026-07-28")
    wave_items = [item for item in wave.get("items", []) if isinstance(item, dict)]
    vendors = [item.get("vendor") for item in wave_items]
    if vendors != ["ECigIntelligence", "Euromonitor", "Circana"]:
        errors.append("Third-donor follow-up vendors differ from the reviewed wave")
    if [item.get("threadStatus") for item in wave_items] != [
        "follow_up_sent",
        "superseded_by_comprehensive_request_sent",
        "qualification_response_received_clarification_sent",
    ]:
        errors.append("Third-donor follow-up completion states differ from the reviewed wave")
    if [item.get("route") for item in wave_items] != [
        "existing_thread",
        "existing_thread",
        "direct_follow_up",
    ]:
        errors.append("Third-donor follow-up routes differ from the reviewed wave")
    excluded = wave.get("excluded") if isinstance(wave.get("excluded"), list) else []
    if len(excluded) != 1 or excluded[0].get("vendor") != "NIQ":
        errors.append("NIQ must remain outside the reviewed follow-up wave")
    return errors


def validate_review_data(
    atlas: dict[str, Any],
    market: dict[str, Any],
    patent: dict[str, Any],
    requests: dict[str, Any],
    fx: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []

    countries = atlas.get("countries")
    evidence = atlas.get("evidence")
    if not isinstance(countries, list) or len(countries) != 195:
        errors.append("Decision Cockpit requires exactly 195 country records for v18")
    if not isinstance(evidence, list) or len(evidence) != 37:
        errors.append("Decision Cockpit requires exactly 37 atlas evidence records for v18")
        evidence = []
    for item in evidence:
        if any(key in item for key in ("retrievedAt", "reviewedAt", "verifiedAt", "lastVerifiedAt")):
            errors.append("Atlas item-level freshness must remain undated unless the v18 ledger and release claim are updated")
            break
    blockers = atlas.get("readiness", {}).get("blockers")
    if not isinstance(blockers, list) or len(blockers) < 3:
        errors.append("Decision Cockpit requires three explicit readiness blockers")
    if atlas.get("readiness", {}).get("lenderReady") is not False:
        errors.append("v18 Decision Cockpit must remain HOLD while lenderReady is false")

    sources = market.get("sources")
    observations = market.get("observations")
    models = market.get("models")
    if not isinstance(sources, list):
        errors.append("Freshness ledger requires a market-source array")
        sources = []
    elif len(sources) != 24:
        errors.append("Freshness ledger requires exactly 24 reviewed market sources for v27")
    if not isinstance(observations, list) or len(observations) != 84:
        errors.append("v27 market baseline must contain exactly 84 observations")
        observations = []
    if not isinstance(models, list):
        errors.append("Market models must be a list")
        models = []

    source_ids: set[str] = set()
    reference_date = parse_date(market.get("meta", {}).get("asOf"))
    if reference_date is None:
        errors.append("Market asOf must be an ISO calendar date")
    for source in sources:
        source_id = source.get("sourceId")
        if not isinstance(source_id, str) or not source_id:
            errors.append("Every market source requires a sourceId")
            continue
        if source_id in source_ids:
            errors.append(f"Duplicate market sourceId {source_id}")
        source_ids.add(source_id)
        if not valid_https(source.get("pageUrl")):
            errors.append(f"{source_id}: pageUrl must be safe HTTPS")
        retrieved = parse_date(source.get("retrievedAt"))
        if retrieved is None:
            errors.append(f"{source_id}: retrievedAt must be an ISO calendar date")
        elif reference_date and retrieved > reference_date:
            errors.append(f"{source_id}: retrievedAt cannot be later than market asOf")
    if source_ids != EXPECTED_MARKET_SOURCE_IDS:
        errors.append(
            "v27 freshness ledger must retain the exact 24-source set; "
            f"missing={sorted(EXPECTED_MARKET_SOURCE_IDS - source_ids)}, "
            f"extra={sorted(source_ids - EXPECTED_MARKET_SOURCE_IDS)}"
        )

    observation_by_id: dict[str, dict[str, Any]] = {}
    years_by_source: dict[str, list[int]] = defaultdict(list)
    for observation in observations:
        observation_id = observation.get("observationId")
        if not isinstance(observation_id, str) or not observation_id:
            errors.append("Every market observation requires an observationId")
            continue
        if observation_id in observation_by_id:
            errors.append(f"Duplicate observationId {observation_id}")
        observation_by_id[observation_id] = observation
        value = observation.get("value")
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value <= 0:
            errors.append(f"{observation_id}: numeric value must be positive and finite")
        for source_id in observation.get("sourceIds", []):
            if source_id not in source_ids:
                errors.append(f"{observation_id}: unresolved sourceId {source_id}")
            if isinstance(observation.get("year"), int):
                years_by_source[source_id].append(observation["year"])

    unused_sources = source_ids - years_by_source.keys()
    if unused_sources:
        errors.append(f"Every freshness-ledger source must support a dated observation; unused={sorted(unused_sources)}")

    nz_vaping = observation_by_id.get(NZ_VAPING_OBSERVATION_ID, {})
    nz_vaping_fact = (
        nz_vaping.get("countryIso2"),
        nz_vaping.get("year"),
        nz_vaping.get("metric"),
        nz_vaping.get("value"),
        nz_vaping.get("unit"),
        nz_vaping.get("currency"),
        nz_vaping.get("period"),
        nz_vaping.get("evidenceStatus"),
        nz_vaping.get("finality"),
        nz_vaping.get("productScope"),
        nz_vaping.get("marketValueBasis"),
        nz_vaping.get("comparableMarketValue"),
        nz_vaping.get("atlasEstimate"),
        nz_vaping.get("sourceIds"),
    )
    if nz_vaping_fact != (
        "NZ",
        2024,
        "derived_identified_vaping_product_sales_raw_sum",
        274_180_410.21,
        "NZD",
        "NZD",
        "calendar_year",
        "derived_official_files",
        "keyword_classified_raw_file_sum_with_quality_warning",
        "specialist_retail_rows_with_product_type_text_identified_as_vaping",
        "conservative_text_classification_raw_sum_not_donor",
        False,
        False,
        NZ_SOURCE_IDS,
    ):
        errors.append("v27 New Zealand identified-vaping observation differs from its reviewed fact boundary")
    nz_limitation = str(nz_vaping.get("limitationEn", ""))
    for marker in (
        "189,402,451.96",
        "84,709,409.85",
        "68,548.40",
        "274,180,410.21",
        "2,137,085.24",
        "4,367,017.37",
        "AIS/AVP",
        "Notifier and RPS observed value is not added",
        "258,327,110.88",
        "unknown GST treatment",
        "no independent reconciliation",
    ):
        if marker not in nz_limitation:
            errors.append(f"v27 New Zealand identified-vaping disclosure lacks {marker!r}")

    for observation_id, expected in POLAND_RECONSTRUCTION.items():
        item = observation_by_id.get(observation_id, {})
        actual = (
            item.get("countryIso2"),
            item.get("year"),
            item.get("metric"),
            item.get("value"),
            item.get("unit"),
            item.get("currency"),
            item.get("period"),
            item.get("evidenceStatus"),
            item.get("finality"),
            item.get("productScope"),
            item.get("marketValueBasis"),
            item.get("comparableMarketValue"),
            item.get("atlasEstimate"),
            item.get("sourceIds"),
        )
        if actual != expected:
            errors.append(
                f"v27 Poland reconstruction observation {observation_id} "
                "differs from its reviewed fact boundary"
            )
    for observation_id in (
        "PL-2025-VAPING-DEVICE-EXCISE-BACKSOLVED-UNITS",
        "PL-2025-VAPING-COMPONENT-SETS-EXCISE-BACKSOLVED-UNITS",
    ):
        limitation = str(observation_by_id.get(observation_id, {}).get("limitationEn", ""))
        if (
            "1 July 2025" not in limitation
            or "second-half tax-base bridge" not in limitation
            or "not full-year sell-through" not in limitation
            or "retail market value" not in limitation
        ):
            errors.append(
                f"v27 Poland tax-base bridge {observation_id} lacks its "
                "half-year, sell-through and retail-value boundaries"
            )

    official = [
        item for item in observations
        if str(item.get("evidenceStatus", "")).startswith("official_")
    ]
    official_countries = {item.get("countryIso2") for item in official}
    structural_official = [
        item for item in official
        if item.get("marketValueBasis") == "official_registration_structure_count_not_sales_or_market_value"
    ]
    market_measure_official = [item for item in official if item not in structural_official]
    if (
        len(official) != 75
        or official_countries != EXPECTED_OFFICIAL_COUNTRIES
        or len(structural_official) != 36
        or {item.get("countryIso2") for item in structural_official} != {"SE"}
        or len(market_measure_official) != 39
    ):
        errors.append(
            "v27 must retain 39 official market-measure observations plus 36 Sweden "
            "registration-structure observations across the seven reviewed countries"
        )
    official_retail = [
        item for item in official
        if item.get("metric") in {
            "consumer_retail_market_value",
            "official_specialist_retail_sales_lower_bound",
            "statcan_rcs_vaping_retail_sales",
        }
    ]
    if (
        len(official_retail) != 8
        or {item.get("countryIso2") for item in official_retail} != {"CA", "NZ"}
        or any(item.get("comparableMarketValue") is not False for item in official_retail)
    ):
        errors.append("v27 must retain seven Canada retail estimates, one NZ lower bound and no accepted retail donor")

    readiness = market.get("meta", {}).get("modelReadiness", {})
    declared_donors = readiness.get("comparableFullYearMarketValueDonors")
    required_donors = readiness.get("minimumRequiredDonors")
    computed_donors = [
        item for item in observations
        if item.get("comparableMarketValue") is True and item.get("period") == "calendar_year"
    ]
    if declared_donors != 0 or len(computed_donors) != 0 or required_donors != 3:
        errors.append("Global-estimate donor gate must remain blocked at 0/3 for v18")
    protocol = market.get("donorProtocol")
    candidates = market.get("donorCandidates")
    if (
        not isinstance(protocol, dict)
        or protocol.get("protocolVersion") != "1.0"
        or not isinstance(protocol.get("criteria"), list)
        or len(protocol["criteria"]) != 10
    ):
        errors.append("v18 donor protocol must expose version 1.0 and ten criteria")
    if not isinstance(candidates, list) or len(candidates) != 5:
        errors.append("v18 donor ledger must contain exactly five reviewed candidates")
        candidates = []
    if any(item.get("decision") != "not_accepted" for item in candidates):
        errors.append("v18 donor candidates must all remain not accepted")
    candidate_ids = {item.get("candidateId") for item in candidates}
    if candidate_ids != {
        NZ_DONOR_CANDIDATE_ID,
        "EU-2023-COMMISSION-BENCHMARK",
        "CA-2024-STATCAN-RCS-RETAIL-SALES",
        "DE-2025-LIQUID-RETAIL-MODEL",
        "US-2021-FTC-REPORTED-MANUFACTURER-SALES",
    }:
        errors.append("v27 donor ledger must retain the reviewed NZ, EU, Canada, Germany and US candidates")
    candidate_by_id = {
        item.get("candidateId"): item
        for item in candidates
        if isinstance(item, dict) and isinstance(item.get("candidateId"), str)
    }
    nz_candidate = candidate_by_id.get(NZ_DONOR_CANDIDATE_ID, {})
    if (
        nz_candidate.get("referenceType") != "observation"
        or nz_candidate.get("referenceId") != NZ_VAPING_OBSERVATION_ID
        or nz_candidate.get("decision") != "not_accepted"
        or set(nz_candidate.get("passedCriteria", []))
        != {"D1", "D2", "D3", "D4", "D6", "D7", "D9"}
        or set(nz_candidate.get("failedCriteria", [])) != {"D5"}
        or set(nz_candidate.get("openCriteria", [])) != {"D8", "D10"}
        or nz_candidate.get("sourceIds") != NZ_SOURCE_IDS
    ):
        errors.append("v27 New Zealand donor candidate differs from the reviewed 7/10 closure decision")

    germany_models = [item for item in models if item.get("modelId") == GERMANY_MODEL_ID]
    if len(germany_models) != 1:
        errors.append("Exactly one Germany calculation-waterfall model is required")
    else:
        model = germany_models[0]
        if model.get("formula") != "volume_litres * 1000 * retail_price_eur_per_ml":
            errors.append("Germany model formula is not the reviewed formula")
        if model.get("rangeInputMap") != GERMANY_PRICE_IDS:
            errors.append("Germany rangeInputMap does not resolve to the three reviewed prices")
        expected_inputs = {GERMANY_VOLUME_ID, *GERMANY_PRICE_IDS.values()}
        if set(model.get("inputIds", [])) != expected_inputs:
            errors.append("Germany inputIds do not match the reviewed waterfall")
        if model.get("confidence") != "low" or model.get("comparableMarketValue") is not False:
            errors.append("Germany model must remain low-confidence and donor-ineligible")
        volume = observation_by_id.get(GERMANY_VOLUME_ID)
        prices = {name: observation_by_id.get(item_id) for name, item_id in GERMANY_PRICE_IDS.items()}
        if not volume or any(item is None for item in prices.values()):
            errors.append("Germany waterfall inputs do not all resolve")
        else:
            price_years = {item.get("year") for item in prices.values() if item}
            if model.get("yearMismatch") is not True or price_years != {2026} or volume.get("year") != 2025:
                errors.append("Germany 2025-volume/2026-price mismatch must remain explicit")
            for scenario, price in prices.items():
                computed = volume["value"] * 1000 * price["value"]
                if (
                    not math.isclose(computed, GERMANY_OUTPUTS[scenario], rel_tol=0, abs_tol=0.01)
                    or model.get(scenario) != GERMANY_OUTPUTS[scenario]
                ):
                    errors.append(f"Germany {scenario} output does not reproduce exactly")

    if reference_date:
        reference_year = reference_date.year
        freshness_counts = {"latest_period": 0, "previous_full_year": 0, "historical_only": 0}
        for source_id in source_ids:
            source_years = years_by_source.get(source_id, [])
            if not source_years:
                continue
            latest_year = max(source_years)
            if latest_year >= reference_year - 1:
                freshness_counts["latest_period"] += 1
            elif latest_year == reference_year - 2:
                freshness_counts["previous_full_year"] += 1
            else:
                freshness_counts["historical_only"] += 1
        if freshness_counts != {
            "latest_period": 12,
            "previous_full_year": 5,
            "historical_only": 7,
        }:
            errors.append(f"Unexpected deterministic freshness buckets: {freshness_counts}")

    family_members = patent.get("familyMembers")
    proceedings = patent.get("proceedings")
    alerts = patent.get("diligenceAlerts")
    if not isinstance(family_members, list) or len(family_members) != 22:
        errors.append("v18 patent baseline must contain 22 family records")
        family_members = []
    national = [
        item for item in family_members
        if item.get("verificationLevel") == "official_national_record"
    ]
    if len(national) != 4:
        errors.append("Only four official_national_record rows may count as nationally verified")
    if not isinstance(proceedings, list) or len(proceedings) != 4:
        errors.append("v18 patent baseline must contain four proceedings")
    if patent.get("summary", {}).get("unresolvedProceedingCount") != 3:
        errors.append("v18 patent baseline must retain three unresolved proceedings")
    if not isinstance(alerts, list) or len(alerts) != 4:
        errors.append("v18 patent baseline must contain four diligence alerts")

    if requests.get("schemaVersion") != 3:
        errors.append("Research Operations requires request-programme schema version 3")
    evidence_stack = requests.get("evidenceStack")
    expected_layer_ids = [
        "statutory_sales",
        "excise_domestic_release",
        "customs_net_imports",
        "retail_or_shipments",
        "price_channel_bridge",
        "enforcement_signal",
    ]
    if (
        not isinstance(evidence_stack, dict)
        or evidence_stack.get("stateUniverseCount") != 195
        or [
            layer.get("layerId")
            for layer in evidence_stack.get("layers", [])
            if isinstance(layer, dict)
        ] != expected_layer_ids
    ):
        errors.append("Research Operations requires the reviewed six-layer 195-state evidence stack")
    supplements = requests.get("supplementaryRequests")
    expected_supplements = {
        "DE-BVL-TABAKERZV25-ANNUAL-SALES": {
            "countryIso2": "DE",
            "sentOn": "2026-07-24",
        },
        "PL-BUREAU-CHEMICALS-EUCEG-ANNUAL-SALES": {
            "countryIso2": "PL",
            "sentOn": "2026-07-28",
        },
    }
    supplement_items = supplements if isinstance(supplements, list) else []
    supplement_by_id = {
        item.get("requestId"): item
        for item in supplement_items
        if isinstance(item, dict)
    }
    if not isinstance(supplements, list) or set(supplement_by_id) != set(expected_supplements):
        errors.append("Research Operations requires the two non-counting German and Polish supplements")
    else:
        for request_id, expected in expected_supplements.items():
            supplement = supplement_by_id[request_id]
            if (
                supplement.get("countryIso2") != expected["countryIso2"]
                or supplement.get("countsTowardCountryQueue") is not False
                or supplement.get("status") != "sent"
                or supplement.get("dispatch") != {
                    "state": "sent",
                    "sentOn": expected["sentOn"],
                    "publicAuthorityReference": None,
                    "responseState": "not_publicly_recorded",
                }
            ):
                errors.append(
                    "Research Operations requires the exact non-counting German and Polish "
                    f"supplement contract for {request_id}"
                )

    routes = requests.get("routes")
    if not isinstance(routes, list) or len(routes) != 20:
        errors.append("Research Operations requires exactly 20 request routes")
        routes = []
    sent = [route for route in routes if route.get("status") == "sent"]
    drafts = [route for route in routes if route.get("status") == "draft_not_sent"]
    if len(sent) != 12 or len(drafts) != 8:
        errors.append("Request programme must remain 12 sent and 8 draft routes")
    recorded_responses = {
        route.get("countryIso2"): route.get("dispatch", {}).get("responseState")
        for route in routes
        if route.get("dispatch", {}).get("responseState")
        not in {"not_publicly_recorded", "not_applicable"}
    }
    process = {
        country: state
        for country, state in recorded_responses.items()
        if country in EXPECTED_PROCESS_STATES
    }
    availability = {
        country: state
        for country, state in recorded_responses.items()
        if country in EXPECTED_AVAILABILITY_STATES
    }
    structural = {
        country: state
        for country, state in recorded_responses.items()
        if country in EXPECTED_STRUCTURAL_STATES
    }
    trade_proxy = {
        country: state
        for country, state in recorded_responses.items()
        if country in EXPECTED_TRADE_PROXY_STATES
    }
    if process != EXPECTED_PROCESS_STATES:
        errors.append(f"Process-only response baseline must remain DE and FI: {process}")
    if availability != EXPECTED_AVAILABILITY_STATES:
        errors.append(f"Availability-response baseline must remain Denmark and Italy: {availability}")
    if structural != EXPECTED_STRUCTURAL_STATES:
        errors.append(f"Structural-data response baseline must remain Sweden only: {structural}")
    if trade_proxy != EXPECTED_TRADE_PROXY_STATES:
        errors.append(f"Trade-proxy response baseline must remain France only: {trade_proxy}")
    if set(recorded_responses) != (
        set(EXPECTED_PROCESS_STATES)
        | set(EXPECTED_AVAILABILITY_STATES)
        | set(EXPECTED_STRUCTURAL_STATES)
        | set(EXPECTED_TRADE_PROXY_STATES)
    ):
        errors.append(f"Unexpected authority response countries: {recorded_responses}")
    for route in routes:
        if route.get("countryIso2") in (
            set(EXPECTED_PROCESS_STATES)
            | set(EXPECTED_AVAILABILITY_STATES)
            | set(EXPECTED_STRUCTURAL_STATES)
            | set(EXPECTED_TRADE_PROXY_STATES)
        ):
            if route.get("dispatch", {}).get("publicAuthorityReference") is not None:
                errors.append(f"{route.get('countryIso2')}: authority response must not publish a private reference")

    if fx is not None:
        policy = fx.get("calculationPolicy", {})
        if (
            fx.get("schemaVersion") != "1.0"
            or fx.get("targetCurrency") != "EUR"
            or fx.get("provider", {}).get("name") != "European Central Bank"
            or policy.get("eligibleRecordPeriods") != ["calendar_year", "calendar_year_estimate"]
            or policy.get("eligibleUnitRule") != "currency_must_equal_unit"
            or policy.get("rateType") != "annual_average_reference_rate"
            or policy.get("quoteConvention") != "currency_units_per_eur"
            or policy.get("formulaMachine") != "eur_equivalent = original_amount / currency_units_per_eur"
            or policy.get("missingRateStatus") != "not_computed"
        ):
            errors.append("Review EUR layer must retain the reviewed fail-closed ECB annual-average policy")
        rates = fx.get("rates")
        if not isinstance(rates, list) or not rates:
            errors.append("Review EUR layer requires a non-empty ECB rate ledger")
            rates = []
        rate_keys: set[tuple[str, int]] = set()
        for rate in rates:
            currency = rate.get("currency")
            year = rate.get("year")
            key = (currency, year)
            source_url = rate.get("sourceUrl")
            parsed = urlparse(source_url) if isinstance(source_url, str) else None
            if (
                not isinstance(currency, str)
                or not re.fullmatch(r"[A-Z]{3}", currency)
                or not isinstance(year, int)
                or not isinstance(rate.get("currencyUnitsPerEur"), (int, float))
                or not math.isfinite(rate["currencyUnitsPerEur"])
                or rate["currencyUnitsPerEur"] <= 0
                or rate.get("seriesKey") != f"EXR.A.{currency}.EUR.SP00.A"
                or rate.get("rateId") != f"ECB-EXR-A-{currency}-EUR-SP00-A-{year}"
                or rate.get("rateType") != "annual_average_reference_rate"
                or rate.get("status") != "available"
                or not parsed
                or parsed.scheme != "https"
                or parsed.hostname != "data-api.ecb.europa.eu"
                or key in rate_keys
            ):
                errors.append(f"Review EUR layer contains an invalid or duplicate ECB rate {currency}:{year}")
                continue
            rate_keys.add(key)
        required_review_rates = {
            ("NZD", 2024),
            ("USD", 2021),
            ("USD", 2025),
            ("CAD", 2024),
        }
        missing_review_rates = required_review_rates - rate_keys
        if missing_review_rates:
            errors.append(f"Review EUR layer lacks required card rates: {sorted(missing_review_rates)}")

    return errors


def extract_ids(html: str) -> set[str]:
    return set(re.findall(r"""\bid=["']([^"']+)["']""", html))


def opening_tag_with_id(html: str, element_id: str) -> str:
    pattern = re.compile(
        rf"""<[^>]+\bid=["']{re.escape(element_id)}["'][^>]*>""",
        flags=re.IGNORECASE,
    )
    match = pattern.search(html)
    return match.group(0) if match else ""


def function_body(js: str, function_name: str) -> str:
    marker = f"function {function_name}("
    start = js.find(marker)
    if start < 0:
        return ""
    brace = js.find("{", start)
    if brace < 0:
        return ""
    depth = 0
    for index in range(brace, len(js)):
        if js[index] == "{":
            depth += 1
        elif js[index] == "}":
            depth -= 1
            if depth == 0:
                return js[brace + 1:index]
    return ""


def validate_review_structure(
    review_html: str,
    index_html: str,
    review_js: str,
    i18n_js: str | None = None,
    request_program_js: str | None = None,
    app_js: str | None = None,
    independent_controls_js: str | None = None,
) -> list[str]:
    errors: list[str] = []
    id_list = re.findall(r"""\bid=["']([^"']+)["']""", review_html)
    ids = set(id_list)
    duplicate_ids = sorted({element_id for element_id in id_list if id_list.count(element_id) > 1})
    if duplicate_ids:
        errors.append(f"review.html contains duplicate element IDs: {duplicate_ids}")
    missing_ids = REQUIRED_REVIEW_IDS - ids
    if missing_ids:
        errors.append(f"review.html lacks required v18 hooks: {sorted(missing_ids)}")
    required_index_ids = {
        "market-donor-ledger",
        "market-donor-protocol-version",
        "market-donor-gate-rule",
        "market-donor-rule",
        "market-donor-summary",
        "market-donor-candidates",
        "market-donor-status",
        "method-route-summary",
        "method-route-filter",
    }
    index_ids = set(re.findall(r"""\bid=["']([^"']+)["']""", index_html))
    missing_index_ids = required_index_ids - index_ids
    if missing_index_ids:
        errors.append(f"index.html lacks required v18 donor hooks: {sorted(missing_index_ids)}")

    body_match = re.search(r"<body\b[^>]*>", review_html, flags=re.IGNORECASE)
    body_tag = body_match.group(0) if body_match else ""
    if not re.search(r"""data-review-view=["']review["']""", body_tag):
        errors.append("review.html body must default to data-review-view=review")
    for view in ("review", "evidence", "operations"):
        if not re.search(rf"""data-review-view-link=["']{view}["']""", review_html):
            errors.append(f"review.html lacks the {view} workspace-view link")
        if not re.search(rf"""data-review-view-link=["']{view}["']""", index_html):
            errors.append(f"index.html lacks the {view} workspace-view link")

    for element_id in ("third-donor-programme", "paid-data", "vendor-response-control", "request-program", "research-priority-matrix"):
        tag = opening_tag_with_id(review_html, element_id)
        if not tag or not re.search(r"""data-review-surface=["']operations["']""", tag):
            errors.append(f"#{element_id} must be isolated on the operations surface")
    for control_hook in ("data-us-benchmark-control", "data-open-extraction-wave"):
        tag_match = re.search(
            rf"<section\b[^>]*\b{re.escape(control_hook)}\b[^>]*>",
            review_html,
            flags=re.IGNORECASE,
        )
        tag = tag_match.group(0) if tag_match else ""
        if not tag or not re.search(r"""data-review-surface=["']operations["']""", tag):
            errors.append(f"{control_hook} must be isolated on the operations surface")
    for element_id in ("decision-cockpit", "review-calculation-audit", "review-source-freshness", "bankability"):
        tag = opening_tag_with_id(review_html, element_id)
        if not tag or not re.search(r"""data-review-surface=["']review["']""", tag):
            errors.append(f"#{element_id} must be isolated on the review surface")

    for page_name, page, expected_count in (
        ("review.html", review_html, 8),
        ("index.html", index_html, 4),
    ):
        cache_tokens = re.findall(
            r"""(?:href|src)=["']assets/[^"']+\?v=([^"']+)["']""",
            page,
            flags=re.IGNORECASE,
        )
        if (
            len(cache_tokens) != expected_count
            or set(cache_tokens) != {"2026-07-29-35"}
        ):
            errors.append(
                f"{page_name} must expose exactly {expected_count} v35 asset cache-busters"
            )

    for public_control_hook in (
        'src="assets/independent-controls.js?v=2026-07-29-35"',
        'href="data/us-independent-benchmark-control.json"',
        'href="schemas/us-independent-benchmark-sample.schema.json"',
        'href="data/open-official-extraction-wave-es-kr-jp.json"',
        'href="schemas/open-official-extraction-wave.schema.json"',
    ):
        if public_control_hook not in review_html:
            errors.append(
                f"review.html lacks required v35 independent-control hook {public_control_hook!r}"
            )

    for function_name in REQUIRED_REVIEW_FUNCTIONS:
        if f"function {function_name}(" not in review_js:
            errors.append(f"review.js lacks required function {function_name}")
    freshness_body = function_body(review_js, "renderReviewSourceFreshness")
    for forbidden in ("Date.now(", "new Date(", "performance.now(", "toLocaleDateString("):
        if forbidden in freshness_body:
            errors.append(f"Source freshness must be deterministic and cannot use {forbidden}")
    if "source.retrievedAt > referenceDate" not in freshness_body:
        errors.append("Source freshness must fail closed on retrieval dates after dataset asOf")
    if "consumer_retail_market_value" not in review_js:
        errors.append("Decision Cockpit must compute official consumer-retail evidence from the canonical metric")
    review_metrics_body = function_body(review_js, "renderReviewMetrics")
    if (
        "reviewGlobalBaseData.countries.length" not in review_metrics_body
        or '"— / 195"' not in review_metrics_body
        or "`${countries.length} / 195`" in review_metrics_body
    ):
        errors.append(
            "Review open-country-base metric must fail closed when the global base is unavailable"
        )
    if "model.formula" not in review_js or "arithmeticPass" not in review_js:
        errors.append("Calculation audit must reconcile the canonical formula and outputs")
    for required_market_hook in (
        "NZ-2024-IDENTIFIED-VAPING-PRODUCT-SALES-RAW-SUM",
        "NZ-2024-RETAIL-RANGE",
        "US-2021-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES",
        "EU-2023-EC-E-CIGARETTE-MARKET-BENCHMARK",
        "source/NZ_2024_DONOR_CLOSURE_PACK.md",
        "source/NZ_2024_RPS_RETAIL_VALUE_SENSITIVITY.md",
        "source/US_FTC_2015_2021_REPORTED_SALES.md",
        "source/EU_2023_E_CIGARETTE_BENCHMARK_RECONCILIATION.md",
        'fetch("data/country-scenarios.json"',
        'fetch("data/third-donor-screen.json"',
        'fetch("data/fx-rates.json"',
        "screening_only_not_donor_assessment",
        "completed_or_superseded",
        "qualification_response_received_clarification_sent",
        "qualificationResponses",
        "function renderThirdDonorScreen(",
        "function renderThirdDonorScreenUnavailable(",
        "function reviewScenarioRange(",
        "EUR = alkuperäinen rahamäärä ÷ ECB:n vuosikeskiarvo",
        "EUR = original monetary amount ÷ ECB annual average",
        "requestData.schemaVersion !== 3",
        "DE-BVL-TABAKERZV25-ANNUAL-SALES",
        "PL-BUREAU-CHEMICALS-EUCEG-ANNUAL-SALES",
        "official_aggregate_not_held_public_routes_identified",
        "availabilityResponses",
        "enforcement_signal",
    ):
        if required_market_hook not in review_js:
            errors.append(f"review.js lacks required v27 reconciliation hook {required_market_hook}")

    lowered_public = f"{review_html}\n{index_html}\n{review_js}".lower()
    for forbidden_claim in ("fresh today", "current worldwide patent", "official global retail value"):
        if forbidden_claim in lowered_public:
            errors.append(f"Unsupported v18 public claim found: {forbidden_claim!r}")
    named_investor_pattern = re.compile(
        r"\b\x62\x6c\x61\x63\x6b\s*\x72\x6f\x63\x6b\b",
        flags=re.IGNORECASE,
    )
    if named_investor_pattern.search(lowered_public):
        errors.append("Named investor-interest claims must not appear in the public review experience")

    if i18n_js is not None:
        for text in REQUIRED_I18N_EN:
            if text not in i18n_js:
                errors.append(f"i18n.js lacks the Finnish/English pair for {text!r}")
        for release_hook in (
            "2026-07-29-mail-and-daily-package-v35",
            'version: "2026.07.29-35"',
            'publishedAt: "2026-07-29T17:55:00+03:00"',
            "Official-request replies and conditional vendor extract",
            "Germany, France, Denmark and Luxembourg",
            "six downloadable lender-package files are the reviewed v35 daily snapshot",
            "dashboard and downloads share the v35 daily release",
        ):
            if release_hook not in i18n_js:
                errors.append(f"i18n.js lacks required v35 UI release hook {release_hook!r}")
    if request_program_js is not None:
        required_rows = (
            "[2018, 226, 18356, 16264, 2092]",
            "[2019, 310, 24525, 17704, 6821]",
            "[2020, 369, 29125, 18745, 10380]",
            "[2021, 399, 31243, 19251, 11992]",
            "[2022, 431, 34163, 20256, 13907]",
            "[2023, 544, 40593, 25278, 15315]",
            "[2024, 619, 48036, 30371, 17665]",
            "[2025, 663, 52889, 32899, 19990]",
            "[2026, 687, 55273, 32889, 22384]",
        )
        for hook in (
            "SWEDEN_STRUCTURAL_RESPONSE",
            "TRADE_PROXY_RESPONSE_STATE",
            "function renderSwedenStructure(",
            "function responseCounts(",
            'includes("privacy-safe categorical process or evidence state")',
            'includes("tietosuojatun kategorisen prosessi- tai evidenssitilan")',
            "STRUCTURE ONLY · NOT SALES",
            "does not measure sales, market value, devices sold, e-liquid millilitres",
            "Official annual customs-trade extract received",
            "tradeProxy",
            "sales: 0",
            *required_rows,
        ):
            if hook not in request_program_js:
                errors.append(f"request-program.js lacks required Sweden hook {hook!r}")
        if "4 process responses" in request_program_js:
            errors.append("request-program.js still presents Sweden as a process-only response")
    if app_js is not None:
        if "function publicReleases(" not in app_js or "window.PixanUiRelease" not in app_js:
            errors.append("app.js does not expose the UI release to metadata and returning visitors")
        app_metrics_body = function_body(app_js, "renderMetrics")
        if (
            "state.globalBase.countries.length" not in app_metrics_body
            or '"— / 195"' not in app_metrics_body
            or "`${list.length} / 195`" in app_metrics_body
        ):
            errors.append(
                "Atlas open-country-base metric must fail closed when the global base is unavailable"
            )
        for hook in (
            "function renderMethodRouteSummary(",
            "function methodRouteFor(",
            "reviewed_method_plan",
            "reviewed_source_lead",
            "regional_tpd_pattern_only",
            "proxy_only_unscoped",
            "eligibleForGlobalRollup",
            "donorAccepted",
            "retailValueStatus",
            "provenanceBasisIds",
            '"nextAction"',
            '"boundary"',
        ):
            if hook not in app_js:
                errors.append(f"app.js lacks required v30 method-control hook {hook!r}")
    if independent_controls_js is not None:
        for hook in (
            'fetch("data/us-independent-benchmark-control.json"',
            'fetch("data/open-official-extraction-wave-es-kr-jp.json"',
            'raw.controlId !== "US-INDEPENDENT-BENCHMARK-CONTROL-20260728"',
            "raw.sources.length !== 7",
            "raw.observations.length !== 19",
            "raw.outputs?.unitedStatesRetailMarketValue !== null",
            "raw.outputs?.globalMarketValue !== null",
            "raw.outputs?.acceptedDonorIncrement !== 0",
            "item.retailSalesEligible !== false",
            'raw.waveId !== "ES_KR_JP_OPEN_OFFICIAL_2026_07_28"',
            'raw.countries.map((item) => item.countryIso2).join(",") !== "ES,KR,JP"',
            'country.marketValueStatus !== "not_computed"',
            "route.retailSalesEligible !== false",
            "route.globalRollupEligible !== false",
            "function renderUs(",
            "function renderWave(",
            "function renderError(",
        ):
            if hook not in independent_controls_js:
                errors.append(
                    f"independent-controls.js lacks required fail-closed hook {hook!r}"
                )
        if independent_controls_js.count("route.globalRollupEligible !== false") < 2:
            errors.append(
                "independent-controls.js must enforce globalRollupEligible !== false "
                "both per route and at the country boundary"
            )
    for hook in (
        "REVIEW_STRUCTURAL_RESPONSE_COUNTRIES",
        "REVIEW_TRADE_PROXY_RESPONSE_COUNTRIES",
        "officialStructuralResponses",
        "tradeProxyResponses",
        "salesResponses: 0",
        "function reviewPublicReleases(",
        "window.PixanUiRelease",
    ):
        if hook not in review_js:
            errors.append(f"review.js lacks required response hook {hook!r}")
    for page_name, page in (("review.html", review_html), ("index.html", index_html)):
        for language, label in (("fi", "Suomi"), ("en", "English")):
            pattern = (
                rf"""<button\b[^>]*data-language=["']{language}["'][^>]*"""
                rf"""\blang=["']{language}["'][^>]*\baria-label=["']{label}["'][^>]*>"""
            )
            if not re.search(pattern, page, flags=re.IGNORECASE):
                errors.append(f"{page_name} language control {language} lacks lang and accessible full-language label")

    return errors


def validate_all(root: Path = ROOT) -> list[str]:
    atlas = load_json(root / "site" / "data" / "atlas.json")
    market = load_json(root / "site" / "data" / "market-values.json")
    patent = load_json(root / "site" / "data" / "patent-history.json")
    requests = load_json(root / "site" / "data" / "top20-data-request-routes.json")
    fx = load_json(root / "site" / "data" / "fx-rates.json")
    third_donor = load_json(root / "site" / "data" / "third-donor-screen.json")
    review_html = (root / "site" / "review.html").read_text(encoding="utf-8")
    index_html = (root / "site" / "index.html").read_text(encoding="utf-8")
    review_js = (root / "site" / "assets" / "review.js").read_text(encoding="utf-8")
    i18n_js = (root / "site" / "assets" / "i18n.js").read_text(encoding="utf-8")
    request_program_js = (root / "site" / "assets" / "request-program.js").read_text(encoding="utf-8")
    app_js = (root / "site" / "assets" / "app.js").read_text(encoding="utf-8")
    independent_controls_js = (
        root / "site" / "assets" / "independent-controls.js"
    ).read_text(encoding="utf-8")
    return [
        *validate_review_data(atlas, market, patent, requests, fx),
        *validate_third_donor_screen(third_donor),
        *validate_review_structure(
            review_html,
            index_html,
            review_js,
            i18n_js,
            request_program_js,
            app_js,
            independent_controls_js,
        ),
    ]


def main() -> None:
    errors = validate_all()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Review-experience validation failed with {len(errors)} error(s).", file=sys.stderr)
        raise SystemExit(1)
    print(
        "Validated v35 dashboard / v35 daily-package review experience: HOLD boundary, "
        "0/3 donor gate, exact Germany "
        "waterfall, New Zealand and Canada 7/10 closures, Poland reconstruction, "
        "deterministic 24-source ledger and required UI hooks."
    )


if __name__ == "__main__":
    main()
