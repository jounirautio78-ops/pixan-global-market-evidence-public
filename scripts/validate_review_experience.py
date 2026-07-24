#!/usr/bin/env python3
"""Fail-closed validation for the v20 decision, donor, audit and freshness views."""

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
    "DE": "registered_and_processing_confirmed",
    "DK": "automated_receipt_acknowledged",
    "FI": "registered_processing_notice_received",
    "SE": "automated_route_correction_received",
}
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
    if not isinstance(sources, list) or len(sources) != 20:
        errors.append("Freshness ledger requires exactly 20 reviewed market sources for v20")
        sources = []
    if not isinstance(observations, list) or len(observations) != 43:
        errors.append("v20 market baseline must contain exactly 43 observations")
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

    official = [
        item for item in observations
        if str(item.get("evidenceStatus", "")).startswith("official_")
    ]
    official_countries = {item.get("countryIso2") for item in official}
    if len(official) != 34 or official_countries != EXPECTED_OFFICIAL_COUNTRIES:
        errors.append(
            "v20 official numeric baseline must retain 34 observations across CA, DE, FI, NZ, PL, SE and US"
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
        errors.append("v20 must retain seven Canada retail estimates, one NZ lower bound and no accepted retail donor")

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
        "NZ-2024-OFFICIAL-RETAIL-LOWER-BOUND",
        "EU-2023-COMMISSION-BENCHMARK",
        "CA-2024-STATCAN-RCS-RETAIL-SALES",
        "DE-2025-LIQUID-RETAIL-MODEL",
        "US-2021-FTC-REPORTED-MANUFACTURER-SALES",
    }:
        errors.append("v20 donor ledger must retain the reviewed NZ, EU, Canada, Germany and US candidates")

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
            latest_year = max(years_by_source[source_id])
            if latest_year >= reference_year - 1:
                freshness_counts["latest_period"] += 1
            elif latest_year == reference_year - 2:
                freshness_counts["previous_full_year"] += 1
            else:
                freshness_counts["historical_only"] += 1
        if freshness_counts != {
            "latest_period": 10,
            "previous_full_year": 3,
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
    if (
        not isinstance(supplements, list)
        or len(supplements) != 1
        or supplements[0].get("requestId") != "DE-BVL-TABAKERZV25-ANNUAL-SALES"
        or supplements[0].get("countryIso2") != "DE"
        or supplements[0].get("countsTowardCountryQueue") is not False
        or supplements[0].get("status") != "sent"
        or supplements[0].get("dispatch") != {
            "state": "sent",
            "sentOn": "2026-07-24",
            "publicAuthorityReference": None,
            "responseState": "not_publicly_recorded",
        }
    ):
        errors.append("Research Operations requires the non-counting German BVL supplement")

    routes = requests.get("routes")
    if not isinstance(routes, list) or len(routes) != 20:
        errors.append("Research Operations requires exactly 20 request routes")
        routes = []
    sent = [route for route in routes if route.get("status") == "sent"]
    drafts = [route for route in routes if route.get("status") == "draft_not_sent"]
    if len(sent) != 12 or len(drafts) != 8:
        errors.append("Request programme must remain 12 sent and 8 draft routes")
    process = {
        route.get("countryIso2"): route.get("dispatch", {}).get("responseState")
        for route in routes
        if route.get("dispatch", {}).get("responseState")
        not in {"not_publicly_recorded", "not_applicable"}
    }
    if process != EXPECTED_PROCESS_STATES:
        errors.append(f"Process-response baseline must remain the four reviewed categorical states: {process}")
    for route in routes:
        if route.get("countryIso2") in EXPECTED_PROCESS_STATES:
            if route.get("dispatch", {}).get("publicAuthorityReference") is not None:
                errors.append(f"{route.get('countryIso2')}: process response must not publish a private authority reference")

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

    for element_id in ("paid-data", "vendor-response-control", "request-program", "research-priority-matrix"):
        tag = opening_tag_with_id(review_html, element_id)
        if not tag or not re.search(r"""data-review-surface=["']operations["']""", tag):
            errors.append(f"#{element_id} must be isolated on the operations surface")
    for element_id in ("decision-cockpit", "review-calculation-audit", "review-source-freshness", "bankability"):
        tag = opening_tag_with_id(review_html, element_id)
        if not tag or not re.search(r"""data-review-surface=["']review["']""", tag):
            errors.append(f"#{element_id} must be isolated on the review surface")

    if review_html.count("2026-07-24-20") < 7:
        errors.append("review.html asset cache-busters must all use the v20 release")
    if index_html.count("2026-07-24-20") < 4:
        errors.append("index.html asset cache-busters must all use the v20 release")

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
    if "model.formula" not in review_js or "arithmeticPass" not in review_js:
        errors.append("Calculation audit must reconcile the canonical formula and outputs")
    for required_market_hook in (
        "NZ-2024-SPECIALIST-RETAIL-PRODUCT-SALES-RAW-FILE-SUM",
        "NZ-2024-RETAIL-RANGE",
        "US-2021-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES",
        "EU-2023-EC-E-CIGARETTE-MARKET-BENCHMARK",
        "source/NZ_2024_ANNUAL_RETURNS_RECONCILIATION.md",
        "source/NZ_2024_RPS_RETAIL_VALUE_SENSITIVITY.md",
        "source/US_FTC_2015_2021_REPORTED_SALES.md",
        "source/EU_2023_E_CIGARETTE_BENCHMARK_RECONCILIATION.md",
        'fetch("data/country-scenarios.json"',
        'fetch("data/fx-rates.json"',
        "function reviewScenarioRange(",
        "EUR = alkuperäinen rahamäärä ÷ ECB:n vuosikeskiarvo",
        "EUR = original monetary amount ÷ ECB annual average",
        "requestData.schemaVersion !== 3",
        "DE-BVL-TABAKERZV25-ANNUAL-SALES",
        "enforcement_signal",
    ):
        if required_market_hook not in review_js:
            errors.append(f"review.js lacks required v18 reconciliation hook {required_market_hook}")

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
    review_html = (root / "site" / "review.html").read_text(encoding="utf-8")
    index_html = (root / "site" / "index.html").read_text(encoding="utf-8")
    review_js = (root / "site" / "assets" / "review.js").read_text(encoding="utf-8")
    i18n_js = (root / "site" / "assets" / "i18n.js").read_text(encoding="utf-8")
    return [
        *validate_review_data(atlas, market, patent, requests, fx),
        *validate_review_structure(review_html, index_html, review_js, i18n_js),
    ]


def main() -> None:
    errors = validate_all()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Review-experience validation failed with {len(errors)} error(s).", file=sys.stderr)
        raise SystemExit(1)
    print(
        "Validated v20 review experience: HOLD boundary, 0/3 donor gate, exact Germany "
        "waterfall, deterministic 20-source ledger, separated operations view and required UI hooks."
    )


if __name__ == "__main__":
    main()
