#!/usr/bin/env python3
"""Build the public UN195 global base layer from reviewed source snapshots."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from build_atlas import COUNTRY_CATALOG


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "source" / "global-base-config.json"
OBSERVATIONS_PATH = ROOT / "source" / "global-base-observations.json"
FX_PATH = ROOT / "source" / "fx-rates.json"
METHOD_ROUTE_CONFIG_PATH = ROOT / "source" / "country-method-route-config.json"
TOP20_ROUTES_PATH = ROOT / "source" / "top20-data-request-routes.json"
THIRD_DONOR_SCREEN_PATH = ROOT / "source" / "third-donor-screen.json"
DONOR_COCKPIT_PATH = ROOT / "source" / "donor-cockpit.json"
SOURCE_SCHEMA_PATH = ROOT / "source" / "schemas" / "global-base-layer.schema.json"
JSON_OUTPUT_PATH = ROOT / "site" / "data" / "global-base-layer.json"
CSV_OUTPUT_PATH = ROOT / "site" / "data" / "global-base-layer.csv"
PUBLIC_SCHEMA_PATH = ROOT / "site" / "schemas" / "global-base-layer.schema.json"
OUTPUT_SCHEMA_VERSION = "1.1"

REVIEWED_METHOD_PLAN_COUNTRIES = {
    "AE",
    "AT",
    "AU",
    "BE",
    "BR",
    "CA",
    "CH",
    "CN",
    "DE",
    "DK",
    "ES",
    "FI",
    "FR",
    "GB",
    "ID",
    "IT",
    "JP",
    "KR",
    "LU",
    "NL",
    "NO",
    "NZ",
    "PH",
    "PL",
    "RU",
    "SA",
    "SE",
    "US",
}
REVIEWED_SOURCE_LEAD_COUNTRIES: set[str] = set()
FIVE_COUNTRY_REQUEST_COUNTRIES = {"AT", "BE", "CH", "LU", "NO"}
REGIONAL_TPD_PATTERN_COUNTRIES = {
    "BG",
    "CY",
    "CZ",
    "EE",
    "GR",
    "HR",
    "HU",
    "IE",
    "LT",
    "LV",
    "MT",
    "PT",
    "RO",
    "SI",
    "SK",
}
EU_TPD_EXPLICIT_PLAN_COUNTRIES = {
    "AT",
    "BE",
    "DE",
    "DK",
    "ES",
    "FI",
    "FR",
    "IT",
    "LU",
    "NL",
    "PL",
    "SE",
}
EU_TPD_SOURCE_LEAD_COUNTRIES: set[str] = set()
EXPECTED_ASSIGNMENT_COUNTS = {
    "reviewed_method_plan": 28,
    "reviewed_source_lead": 0,
    "regional_tpd_pattern_only": 15,
    "proxy_only_unscoped": 152,
}
NEXT_ACTION_BY_PRIMARY_METHOD = {
    "official_retail_survey": "close_retail_d5_d7_d10",
    "specialist_retail_annual_returns": "close_partial_channel_tax_reconciliation",
    "excise_plus_statutory_sales": "reconcile_excise_sales_price_pos",
    "manufacturer_reporting_plus_pos": "bridge_manufacturer_to_retail_pos",
    "excise_to_volume_reconstruction": "reconstruct_tax_base_then_retail_bridge",
    "statutory_annual_sales_reporting": "request_statutory_sales_aggregate",
    "product_registry_plus_sales_request": "registry_to_sales_aggregate",
    "production_survey_plus_customs": "production_trade_to_domestic_sellthrough",
    "customs_trade_proxy": "classify_customs_scope_then_domestic_bridge",
    "regulated_supply_plus_enforcement": "separate_lawful_supply_enforcement_retail",
    "marking_system_retail_plus_excise": "reproduce_marked_retail_and_illicit_boundary",
    "enforcement_trade_only": "establish_lawful_market_scope",
    "excise_designated_retail_price": "obtain_designated_price_tax_totals",
}

MEASURE_KEYS = {
    "population_total": ("worldBank", "populationTotal"),
    "population_ages_15_64": ("worldBank", "populationAges15To64"),
    "gdp_per_capita_current_usd": ("worldBank", "gdpPerCapitaCurrentUsd"),
    "who_adult_current_ecig_prevalence": (
        "routes",
        "whoAdultCurrentEcigPrevalence",
    ),
    "un_comtrade_vaping_trade": ("routes", "unComtradeVapingTrade"),
}

CSV_FIELDS = [
    "country_iso2",
    "country_name",
    "country_name_fi",
    "region",
    "population_total_value",
    "population_total_source_period",
    "population_total_status",
    "population_ages_15_64_value",
    "population_ages_15_64_source_period",
    "population_ages_15_64_status",
    "gdp_per_capita_usd_value",
    "gdp_per_capita_usd_source_period",
    "gdp_per_capita_usd_status",
    "gdp_per_capita_eur_value",
    "gdp_per_capita_eur_status",
    "gdp_per_capita_eur_rate_id",
    "who_ecig_prevalence_value",
    "who_ecig_prevalence_data_status",
    "who_ecig_prevalence_acquisition_status",
    "un_comtrade_value",
    "un_comtrade_data_status",
    "un_comtrade_acquisition_status",
    "method_assignment_class",
    "method_primary_id",
    "method_transaction_stage",
    "method_retail_value_status",
    "method_request_state",
    "method_donor_assessment_state",
    "method_provenance_basis_ids",
    "method_next_action_id",
    "eligible_for_global_rollup",
    "donor_accepted",
    "retail_sales_eligible",
]


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def validate_source_contract(
    config: dict[str, Any],
    snapshot: dict[str, Any],
) -> dict[tuple[str, str], dict[str, Any]]:
    countries = [country["iso2"] for country in COUNTRY_CATALOG]
    country_set = set(countries)
    measure_map = {item["measureId"]: item for item in config["measures"]}
    expected_measures = set(MEASURE_KEYS)

    if len(countries) != 195 or len(country_set) != 195:
        raise ValueError("COUNTRY_CATALOG is not an exact UN195 ISO2 universe")
    if set(measure_map) != expected_measures:
        raise ValueError("global base config must define exactly the five v27 measures")
    if config["universe"]["countryCount"] != 195:
        raise ValueError("configured country count must be 195")
    if snapshot.get("countryCount") != 195:
        raise ValueError("snapshot country count must be 195")
    if snapshot.get("universe") != config["universe"]["id"]:
        raise ValueError("snapshot universe does not match config")
    if snapshot.get("sourceWindow", {}).get("selection") != "latest_non_null":
        raise ValueError("snapshot must use latest_non_null selection")

    observations = snapshot.get("observations")
    if not isinstance(observations, list) or len(observations) != 195 * 5:
        raise ValueError("snapshot must contain exactly 975 observations")

    indexed: dict[tuple[str, str], dict[str, Any]] = {}
    for record in observations:
        if not isinstance(record, dict):
            raise ValueError("every observation must be a JSON object")
        iso2 = record.get("countryIso2")
        measure_id = record.get("measureId")
        key = (iso2, measure_id)
        if iso2 not in country_set:
            raise ValueError(f"observation has out-of-universe ISO2: {iso2}")
        if measure_id not in expected_measures:
            raise ValueError(f"observation has unknown measure: {measure_id}")
        if key in indexed:
            raise ValueError(f"duplicate observation: {iso2}/{measure_id}")
        indexed[key] = record

        definition = measure_map[measure_id]
        if record.get("sourceId") != definition["sourceId"]:
            raise ValueError(f"{iso2}/{measure_id} sourceId mismatch")
        if record.get("sourceSeries") != definition["sourceSeries"]:
            raise ValueError(f"{iso2}/{measure_id} sourceSeries mismatch")
        if record.get("unit") != definition["unit"]:
            raise ValueError(f"{iso2}/{measure_id} unit mismatch")
        if record.get("currency") != definition["currency"]:
            raise ValueError(f"{iso2}/{measure_id} currency mismatch")
        if record.get("retailSalesEligible") is not False:
            raise ValueError(f"{iso2}/{measure_id} must not be retail-sales eligible")

        value = record.get("value")
        period = record.get("sourcePeriod")
        data_status = record.get("dataStatus")
        acquisition_status = record.get("acquisitionStatus")
        if definition["retrievalMode"] == "queued":
            if (
                value is not None
                or period is not None
                or data_status != "missing"
                or acquisition_status != "queued"
            ):
                raise ValueError(
                    f"{iso2}/{measure_id} must remain queued, missing and null in v27"
                )
        elif data_status == "observed":
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value < 0
            ):
                raise ValueError(f"{iso2}/{measure_id} observed value is invalid")
            if not isinstance(period, int) or not 2020 <= period <= 2024:
                raise ValueError(f"{iso2}/{measure_id} sourcePeriod is invalid")
            if acquisition_status != "validated":
                raise ValueError(f"{iso2}/{measure_id} must be acquisition-validated")
        elif data_status == "missing":
            if value is not None or period is not None:
                raise ValueError(f"{iso2}/{measure_id} missing values must be null")
            if acquisition_status != "validated":
                raise ValueError(f"{iso2}/{measure_id} must be acquisition-validated")
        else:
            raise ValueError(f"{iso2}/{measure_id} has invalid data status")

    expected_keys = {
        (iso2, measure_id)
        for iso2 in countries
        for measure_id in expected_measures
    }
    if set(indexed) != expected_keys:
        raise ValueError("snapshot does not provide every measure for every UN195 country")
    return indexed


def available_usd_rates(fx: dict[str, Any]) -> dict[int, dict[str, Any]]:
    rates: dict[int, dict[str, Any]] = {}
    for rate in fx.get("rates", []):
        if (
            rate.get("currency") == "USD"
            and rate.get("rateType") == "annual_average_reference_rate"
            and rate.get("status") == "available"
            and isinstance(rate.get("year"), int)
            and isinstance(rate.get("currencyUnitsPerEur"), (int, float))
            and not isinstance(rate.get("currencyUnitsPerEur"), bool)
            and rate["currencyUnitsPerEur"] > 0
        ):
            rates[rate["year"]] = rate
    return rates


def eur_equivalent(
    gdp_observation: dict[str, Any],
    usd_rates: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    period = gdp_observation["sourcePeriod"]
    value = gdp_observation["value"]
    base = {
        "currency": "EUR",
        "sourcePeriod": period,
        "periodRule": "same_source_year_only",
        "formula": "usd_value / currency_units_per_eur",
    }
    if gdp_observation["dataStatus"] != "observed" or value is None or period is None:
        return {
            **base,
            "status": "not_computed",
            "value": None,
            "rateId": None,
            "rateYear": None,
            "currencyUnitsPerEur": None,
            "reason": "source_value_missing",
        }
    rate = usd_rates.get(period)
    if rate is None:
        return {
            **base,
            "status": "not_computed",
            "value": None,
            "rateId": None,
            "rateYear": None,
            "currencyUnitsPerEur": None,
            "reason": "same_year_ecb_rate_missing",
        }
    return {
        **base,
        "status": "computed",
        "value": round(value / rate["currencyUnitsPerEur"], 2),
        "rateId": rate["rateId"],
        "rateYear": rate["year"],
        "currencyUnitsPerEur": rate["currencyUnitsPerEur"],
        "reason": None,
    }


def public_observation(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "measureId": record["measureId"],
        "sourceId": record["sourceId"],
        "sourceSeries": record["sourceSeries"],
        "sourcePeriod": record["sourcePeriod"],
        "value": record["value"],
        "unit": record["unit"],
        "currency": record["currency"],
        "dataStatus": record["dataStatus"],
        "acquisitionStatus": record["acquisitionStatus"],
        "missingReason": record["missingReason"],
        "retailSalesEligible": False,
        "sourceUrl": record["sourceUrl"],
    }


def validate_method_route_sources(
    route_config: dict[str, Any],
    top20_routes: dict[str, Any],
    third_donor_screen: dict[str, Any],
    donor_cockpit: dict[str, Any],
) -> dict[str, Any]:
    """Validate the reviewed route-map inputs and return indexed controls."""

    country_set = {country["iso2"] for country in COUNTRY_CATALOG}
    if route_config.get("schemaVersion") != "1.0":
        raise ValueError("method-route config schemaVersion must be 1.0")
    if route_config.get("status") != "research_route_map_not_market_values":
        raise ValueError("method-route config must remain a research route map")
    if not isinstance(route_config.get("asOf"), str):
        raise ValueError("method-route config asOf date is missing")

    methods = route_config.get("methods")
    if not isinstance(methods, list):
        raise ValueError("method-route config methods must be a list")
    method_map = {method.get("methodId"): method for method in methods}
    if len(method_map) != len(methods) or None in method_map:
        raise ValueError("method-route config method IDs must be unique and non-null")
    for method_id, method in method_map.items():
        if method.get("canEstablishRetailValueAlone") is not False:
            raise ValueError(f"{method_id} must not establish retail value alone")
        for field in (
            "labelEn",
            "labelFi",
            "transactionStage",
            "boundaryEn",
            "boundaryFi",
        ):
            if not isinstance(method.get(field), str) or not method[field]:
                raise ValueError(f"{method_id} is missing {field}")

    actions = route_config.get("nextActions")
    if not isinstance(actions, list):
        raise ValueError("method-route config nextActions must be a list")
    action_map = {action.get("nextActionId"): action for action in actions}
    if len(action_map) != len(actions) or None in action_map:
        raise ValueError("method-route next-action IDs must be unique and non-null")
    required_action_ids = {
        *NEXT_ACTION_BY_PRIMARY_METHOD.values(),
        "validate_country_source_lead",
        "identify_national_tpd_holder_and_request_aggregate",
        "scope_country_specific_official_route",
    }
    if not required_action_ids.issubset(action_map):
        missing = sorted(required_action_ids - set(action_map))
        raise ValueError(f"method-route config is missing next actions: {missing}")
    for action_id, action in action_map.items():
        for field in ("labelEn", "labelFi"):
            if not isinstance(action.get(field), str) or not action[field]:
                raise ValueError(f"{action_id} is missing {field}")

    provenance = route_config.get("provenanceSources")
    if not isinstance(provenance, list):
        raise ValueError("method-route provenanceSources must be a list")
    provenance_map = {item.get("basisId"): item for item in provenance}
    required_provenance_ids = {
        "UN195",
        "OPEN_BASE",
        "TOP20",
        "THIRD_DONOR",
        "MARNET_PUBLIC",
        "EU_TPD_20_7",
        "DONOR_CONTROL",
        "FIVE_COUNTRY_SPRINT",
    }
    if set(provenance_map) != required_provenance_ids:
        raise ValueError("method-route provenance basis set differs from v31 contract")

    country_plans = route_config.get("countryPlans")
    if not isinstance(country_plans, list):
        raise ValueError("method-route countryPlans must be a list")
    country_plan_map = {
        plan.get("countryIso2"): plan
        for plan in country_plans
    }
    if len(country_plan_map) != len(country_plans) or None in country_plan_map:
        raise ValueError("method-route country plan ISO2 values must be unique and non-null")
    if set(country_plan_map) != REVIEWED_METHOD_PLAN_COUNTRIES:
        raise ValueError("reviewed method-plan country set differs from v31 contract")

    for iso2, plan in country_plan_map.items():
        if iso2 not in country_set:
            raise ValueError(f"method-route country plan is outside UN195: {iso2}")
        primary_method_id = plan.get("primaryMethodId")
        secondary_method_ids = plan.get("secondaryMethodIds")
        if primary_method_id not in method_map:
            raise ValueError(f"{iso2} has an unknown primary method")
        if (
            not isinstance(secondary_method_ids, list)
            or len(secondary_method_ids) != len(set(secondary_method_ids))
            or any(method_id not in method_map for method_id in secondary_method_ids)
            or primary_method_id in secondary_method_ids
        ):
            raise ValueError(f"{iso2} has invalid secondary methods")
        expected_status = {
            "CA": "official_point_estimate_quality_limited",
            "NZ": "observed_partial_channel_only",
        }.get(iso2, "not_computed")
        if plan.get("retailValueStatus") != expected_status:
            raise ValueError(f"{iso2} retail-value status differs from v31 contract")

    source_leads = set(route_config.get("reviewedSourceLeads", []))
    regional_tpd = set(route_config.get("regionalTpdPatternCountries", []))
    if source_leads != REVIEWED_SOURCE_LEAD_COUNTRIES:
        raise ValueError("reviewed source-lead country set differs from v31 contract")
    if regional_tpd != REGIONAL_TPD_PATTERN_COUNTRIES:
        raise ValueError("regional TPD-pattern country set differs from v31 contract")
    if (
        set(country_plan_map) & source_leads
        or set(country_plan_map) & regional_tpd
        or source_leads & regional_tpd
    ):
        raise ValueError("method-route assignment classes must be disjoint")

    default_plan = route_config.get("defaultPlan")
    if (
        not isinstance(default_plan, dict)
        or default_plan.get("primaryMethodId") != "official_route_not_scoped"
        or default_plan.get("secondaryMethodIds") != []
        or default_plan.get("retailValueStatus") != "not_computed"
    ):
        raise ValueError("method-route default plan must remain unscoped and not computed")

    top20_items = top20_routes.get("routes")
    if not isinstance(top20_items, list):
        raise ValueError("top20 route programme routes must be a list")
    top20_map = {route.get("countryIso2"): route for route in top20_items}
    expected_top20 = REVIEWED_METHOD_PLAN_COUNTRIES - {
        "AE",
        "AT",
        "BE",
        "CH",
        "LU",
        "NO",
        "NZ",
        "SA",
    }
    if len(top20_map) != 20 or set(top20_map) != expected_top20:
        raise ValueError("top20 programme country set differs from v31 method map")
    for iso2, route in top20_map.items():
        request_state = route.get("status")
        if request_state not in {"sent", "draft_not_sent"}:
            raise ValueError(f"{iso2} has an unexpected top20 request state")
        if route.get("dispatch", {}).get("state") != request_state:
            raise ValueError(f"{iso2} top20 request and dispatch states differ")

    country_request_items = route_config.get("countryRequests")
    if not isinstance(country_request_items, list):
        raise ValueError("method-route countryRequests must be a list")
    country_request_map = {
        item.get("countryIso2"): item
        for item in country_request_items
        if isinstance(item, dict)
    }
    if (
        len(country_request_map) != len(country_request_items)
        or set(country_request_map) != FIVE_COUNTRY_REQUEST_COUNTRIES
    ):
        raise ValueError("five-country request set differs from v31 contract")
    for iso2, item in country_request_map.items():
        if (
            item.get("status") != "sent"
            or item.get("sentOn") != route_config.get("asOf")
            or item.get("programme") != "five_country_method_sprint"
            or not isinstance(item.get("publicNoteEn"), str)
            or not item["publicNoteEn"]
            or not isinstance(item.get("publicNoteFi"), str)
            or not item["publicNoteFi"]
        ):
            raise ValueError(f"{iso2} has an invalid five-country request record")

    third_donor_items = third_donor_screen.get("countries")
    if not isinstance(third_donor_items, list):
        raise ValueError("third-donor screen countries must be a list")
    third_donor_countries = {
        country.get("countryIso2")
        for country in third_donor_items
    }
    if (
        len(third_donor_items) != 15
        or None in third_donor_countries
        or len(third_donor_countries) != 15
        or not third_donor_countries.issubset(country_set)
        or not {"AE", "SA"}.issubset(third_donor_countries)
    ):
        raise ValueError("third-donor screen country set is invalid")

    donor_candidates = donor_cockpit.get("candidates")
    if not isinstance(donor_candidates, list):
        raise ValueError("donor cockpit candidates must be a list")
    donor_country_candidates = {
        candidate.get("countryIso2"): candidate
        for candidate in donor_candidates
        if candidate.get("candidateType") == "country_year"
    }
    if set(donor_country_candidates) != {"CA", "DE", "NZ", "US"}:
        raise ValueError("donor country-assessment set differs from v31 contract")
    if any(
        candidate.get("declaredDecision") != "not_accepted"
        for candidate in donor_country_candidates.values()
    ):
        raise ValueError("no donor country may be accepted in the v31 method map")

    return {
        "methodMap": method_map,
        "actionMap": action_map,
        "provenanceMap": provenance_map,
        "countryPlanMap": country_plan_map,
        "sourceLeadCountries": source_leads,
        "regionalTpdCountries": regional_tpd,
        "top20Map": top20_map,
        "countryRequestMap": country_request_map,
        "thirdDonorCountries": third_donor_countries,
        "donorCountryCandidates": donor_country_candidates,
    }


def country_method_route(
    iso2: str,
    route_config: dict[str, Any],
    controls: dict[str, Any],
) -> dict[str, Any]:
    """Return the fail-closed reviewed method-control record for one country."""

    country_plans = controls["countryPlanMap"]
    source_leads = controls["sourceLeadCountries"]
    regional_tpd = controls["regionalTpdCountries"]
    method_map = controls["methodMap"]
    action_map = controls["actionMap"]

    if iso2 in country_plans:
        assignment_class = "reviewed_method_plan"
        review_level = "country_method_reviewed"
        plan = country_plans[iso2]
        primary_method_id = plan["primaryMethodId"]
        secondary_method_ids = list(plan["secondaryMethodIds"])
        if (
            iso2 in EU_TPD_EXPLICIT_PLAN_COUNTRIES
            and "eu_tpd_annual_reporting_pattern" not in secondary_method_ids
        ):
            secondary_method_ids.append("eu_tpd_annual_reporting_pattern")
        retail_value_status = plan["retailValueStatus"]
        next_action_id = NEXT_ACTION_BY_PRIMARY_METHOD[primary_method_id]
    elif iso2 in source_leads:
        assignment_class = "reviewed_source_lead"
        review_level = "source_lead_reviewed_method_unassigned"
        primary_method_id = "official_route_not_scoped"
        secondary_method_ids = (
            ["eu_tpd_annual_reporting_pattern"]
            if iso2 in EU_TPD_SOURCE_LEAD_COUNTRIES
            else []
        )
        retail_value_status = "not_computed"
        next_action_id = "validate_country_source_lead"
    elif iso2 in regional_tpd:
        assignment_class = "regional_tpd_pattern_only"
        review_level = "regional_pattern_reviewed_national_route_unverified"
        primary_method_id = "eu_tpd_annual_reporting_pattern"
        secondary_method_ids = []
        retail_value_status = "not_computed"
        next_action_id = "identify_national_tpd_holder_and_request_aggregate"
    else:
        assignment_class = "proxy_only_unscoped"
        review_level = "country_specific_route_not_reviewed"
        plan = route_config["defaultPlan"]
        primary_method_id = plan["primaryMethodId"]
        secondary_method_ids = list(plan["secondaryMethodIds"])
        retail_value_status = plan["retailValueStatus"]
        next_action_id = "scope_country_specific_official_route"

    method = method_map[primary_method_id]
    next_action = action_map[next_action_id]
    provenance_basis_ids = ["UN195", "OPEN_BASE"]
    if iso2 in controls["top20Map"]:
        provenance_basis_ids.append("TOP20")
    if iso2 in controls["thirdDonorCountries"]:
        provenance_basis_ids.append("THIRD_DONOR")
    if iso2 in source_leads:
        provenance_basis_ids.append("MARNET_PUBLIC")
    if iso2 in controls["countryRequestMap"]:
        provenance_basis_ids.append("FIVE_COUNTRY_SPRINT")
    if (
        iso2 in EU_TPD_EXPLICIT_PLAN_COUNTRIES
        or iso2 in EU_TPD_SOURCE_LEAD_COUNTRIES
        or iso2 in regional_tpd
    ):
        provenance_basis_ids.append("EU_TPD_20_7")
    if iso2 in controls["donorCountryCandidates"]:
        provenance_basis_ids.append("DONOR_CONTROL")

    return {
        "assignmentClass": assignment_class,
        "reviewLevel": review_level,
        "primaryMethodId": primary_method_id,
        "secondaryMethodIds": secondary_method_ids,
        "primaryMethodLabelEn": method["labelEn"],
        "primaryMethodLabelFi": method["labelFi"],
        "transactionStage": method["transactionStage"],
        "nextActionId": next_action_id,
        "nextActionEn": next_action["labelEn"],
        "nextActionFi": next_action["labelFi"],
        "provenanceBasisIds": provenance_basis_ids,
        "retailValueStatus": retail_value_status,
        "eligibleForGlobalRollup": False,
        "donorAssessmentState": (
            "assessed_not_accepted"
            if iso2 in controls["donorCountryCandidates"]
            else "not_assessed"
        ),
        "donorAccepted": False,
        "requestState": (
            controls["top20Map"][iso2]["status"]
            if iso2 in controls["top20Map"]
            else (
                controls["countryRequestMap"][iso2]["status"]
                if iso2 in controls["countryRequestMap"]
                else "not_in_top20_program"
            )
        ),
        "lastReviewedOn": route_config["asOf"],
        "boundaryEn": method["boundaryEn"],
        "boundaryFi": method["boundaryFi"],
    }


def build_layer(
    config: dict[str, Any],
    snapshot: dict[str, Any],
    fx: dict[str, Any],
    method_route_config: dict[str, Any] | None = None,
    top20_routes: dict[str, Any] | None = None,
    third_donor_screen: dict[str, Any] | None = None,
    donor_cockpit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    indexed = validate_source_contract(config, snapshot)
    usd_rates = available_usd_rates(fx)
    method_route_config = method_route_config or read_json(METHOD_ROUTE_CONFIG_PATH)
    top20_routes = top20_routes or read_json(TOP20_ROUTES_PATH)
    third_donor_screen = third_donor_screen or read_json(THIRD_DONOR_SCREEN_PATH)
    donor_cockpit = donor_cockpit or read_json(DONOR_COCKPIT_PATH)
    route_controls = validate_method_route_sources(
        method_route_config,
        top20_routes,
        third_donor_screen,
        donor_cockpit,
    )
    countries: list[dict[str, Any]] = []

    for catalogue_country in COUNTRY_CATALOG:
        iso2 = catalogue_country["iso2"]
        country: dict[str, Any] = {
            "iso2": iso2,
            "name": catalogue_country["name"],
            "nameFi": catalogue_country["nameFi"],
            "region": catalogue_country["region"],
            "worldBank": {},
            "routes": {},
            "methodRoute": country_method_route(
                iso2,
                method_route_config,
                route_controls,
            ),
            "retailSalesEligible": False,
        }
        for measure_id, (section, key) in MEASURE_KEYS.items():
            country[section][key] = public_observation(indexed[(iso2, measure_id)])
        gdp = country["worldBank"]["gdpPerCapitaCurrentUsd"]
        gdp["eurEquivalent"] = eur_equivalent(gdp, usd_rates)
        countries.append(country)

    observations = snapshot["observations"]
    measure_summary: list[dict[str, Any]] = []
    for measure in config["measures"]:
        records = [
            record
            for record in observations
            if record["measureId"] == measure["measureId"]
        ]
        periods = Counter(
            record["sourcePeriod"]
            for record in records
            if record["sourcePeriod"] is not None
        )
        measure_summary.append(
            {
                "measureId": measure["measureId"],
                "sourceId": measure["sourceId"],
                "observedCount": sum(
                    record["dataStatus"] == "observed" for record in records
                ),
                "missingCount": sum(
                    record["dataStatus"] == "missing" for record in records
                ),
                "queuedCount": sum(
                    record["acquisitionStatus"] == "queued" for record in records
                ),
                "sourcePeriods": [
                    {"sourcePeriod": year, "count": periods[year]}
                    for year in sorted(periods)
                ],
                "retailSalesEligible": False,
            }
        )

    eur_statuses = Counter(
        country["worldBank"]["gdpPerCapitaCurrentUsd"]["eurEquivalent"]["status"]
        for country in countries
    )
    assignment_counts = Counter(
        country["methodRoute"]["assignmentClass"]
        for country in countries
    )
    retail_value_status_counts = Counter(
        country["methodRoute"]["retailValueStatus"]
        for country in countries
    )
    normalized_assignment_counts = {
        assignment_class: assignment_counts[assignment_class]
        for assignment_class in EXPECTED_ASSIGNMENT_COUNTS
    }
    if normalized_assignment_counts != EXPECTED_ASSIGNMENT_COUNTS:
        raise ValueError(
            "generated method-route assignment counts differ from "
            f"v31 contract: {normalized_assignment_counts}"
        )
    if retail_value_status_counts != {
        "official_point_estimate_quality_limited": 1,
        "observed_partial_channel_only": 1,
        "not_computed": 193,
    }:
        raise ValueError("generated retail-value status counts differ from v31 contract")

    return {
        "schemaVersion": OUTPUT_SCHEMA_VERSION,
        "asOf": config["asOf"],
        "meta": {
            "universe": config["universe"]["id"],
            "countryCount": len(countries),
            "observationCount": len(observations),
            "generatedAt": snapshot["snapshot"]["retrievedAt"],
            "snapshotWindow": snapshot["sourceWindow"],
            "selectionRuleEn": config["snapshotPolicy"]["sourcePeriodRuleEn"],
            "selectionRuleFi": config["snapshotPolicy"]["sourcePeriodRuleFi"],
            "publicationClass": "official_open_derived_snapshot",
        },
        "sources": config["sources"],
        "summary": {
            "observedCount": sum(
                record["dataStatus"] == "observed" for record in observations
            ),
            "missingCount": sum(
                record["dataStatus"] == "missing" for record in observations
            ),
            "queuedCount": sum(
                record["acquisitionStatus"] == "queued" for record in observations
            ),
            "measures": measure_summary,
            "gdpEurEquivalent": {
                "computedCount": eur_statuses["computed"],
                "notComputedCount": eur_statuses["not_computed"],
                "periodRule": "same_source_year_only",
            },
        },
        "methodRouteControl": {
            "version": method_route_config["version"],
            "asOf": method_route_config["asOf"],
            "status": method_route_config["status"],
            "boundaryEn": method_route_config["boundaryEn"],
            "boundaryFi": method_route_config["boundaryFi"],
            "summary": {
                "countryCount": 195,
                "reviewedMethodPlanCount": assignment_counts["reviewed_method_plan"],
                "reviewedSourceLeadCount": assignment_counts["reviewed_source_lead"],
                "regionalTpdPatternOnlyCount": assignment_counts[
                    "regional_tpd_pattern_only"
                ],
                "proxyOnlyUnscopedCount": assignment_counts[
                    "proxy_only_unscoped"
                ],
                "reviewedNationalRouteOrLeadCount": (
                    assignment_counts["reviewed_method_plan"]
                    + assignment_counts["reviewed_source_lead"]
                ),
                "nonDefaultRouteCount": (
                    assignment_counts["reviewed_method_plan"]
                    + assignment_counts["reviewed_source_lead"]
                    + assignment_counts["regional_tpd_pattern_only"]
                ),
                "retailValueStatusCounts": {
                    "officialPointEstimateQualityLimited": retail_value_status_counts[
                        "official_point_estimate_quality_limited"
                    ],
                    "observedPartialChannelOnly": retail_value_status_counts[
                        "observed_partial_channel_only"
                    ],
                    "notComputed": retail_value_status_counts["not_computed"],
                },
                "eligibleForGlobalRollupCount": 0,
                "donorAcceptedCount": 0,
            },
            "methods": method_route_config["methods"],
            "nextActions": method_route_config["nextActions"],
            "provenanceSources": method_route_config["provenanceSources"],
        },
        "countries": countries,
        "globalRetailSales": {
            "status": "blocked",
            "value": None,
            "currency": None,
            "eligibleObservationCount": 0,
            "ruleEn": config["globalRollup"]["ruleEn"],
            "ruleFi": config["globalRollup"]["ruleFi"],
        },
    }


def csv_rows(layer: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for country in layer["countries"]:
        population = country["worldBank"]["populationTotal"]
        working_age = country["worldBank"]["populationAges15To64"]
        gdp = country["worldBank"]["gdpPerCapitaCurrentUsd"]
        eur = gdp["eurEquivalent"]
        who = country["routes"]["whoAdultCurrentEcigPrevalence"]
        trade = country["routes"]["unComtradeVapingTrade"]
        method_route = country["methodRoute"]
        rows.append(
            {
                "country_iso2": country["iso2"],
                "country_name": country["name"],
                "country_name_fi": country["nameFi"],
                "region": country["region"],
                "population_total_value": population["value"],
                "population_total_source_period": population["sourcePeriod"],
                "population_total_status": population["dataStatus"],
                "population_ages_15_64_value": working_age["value"],
                "population_ages_15_64_source_period": working_age["sourcePeriod"],
                "population_ages_15_64_status": working_age["dataStatus"],
                "gdp_per_capita_usd_value": gdp["value"],
                "gdp_per_capita_usd_source_period": gdp["sourcePeriod"],
                "gdp_per_capita_usd_status": gdp["dataStatus"],
                "gdp_per_capita_eur_value": eur["value"],
                "gdp_per_capita_eur_status": eur["status"],
                "gdp_per_capita_eur_rate_id": eur["rateId"],
                "who_ecig_prevalence_value": who["value"],
                "who_ecig_prevalence_data_status": who["dataStatus"],
                "who_ecig_prevalence_acquisition_status": who["acquisitionStatus"],
                "un_comtrade_value": trade["value"],
                "un_comtrade_data_status": trade["dataStatus"],
                "un_comtrade_acquisition_status": trade["acquisitionStatus"],
                "method_assignment_class": method_route["assignmentClass"],
                "method_primary_id": method_route["primaryMethodId"],
                "method_transaction_stage": method_route["transactionStage"],
                "method_retail_value_status": method_route["retailValueStatus"],
                "method_request_state": method_route["requestState"],
                "method_donor_assessment_state": method_route[
                    "donorAssessmentState"
                ],
                "method_provenance_basis_ids": "|".join(
                    method_route["provenanceBasisIds"]
                ),
                "method_next_action_id": method_route["nextActionId"],
                "eligible_for_global_rollup": "false",
                "donor_accepted": "false",
                "retail_sales_eligible": "false",
            }
        )
    return rows


def render_csv(rows: list[dict[str, Any]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--observations", type=Path, default=OBSERVATIONS_PATH)
    parser.add_argument("--fx", type=Path, default=FX_PATH)
    parser.add_argument(
        "--method-route-config",
        type=Path,
        default=METHOD_ROUTE_CONFIG_PATH,
    )
    parser.add_argument("--top20-routes", type=Path, default=TOP20_ROUTES_PATH)
    parser.add_argument(
        "--third-donor-screen",
        type=Path,
        default=THIRD_DONOR_SCREEN_PATH,
    )
    parser.add_argument("--donor-cockpit", type=Path, default=DONOR_COCKPIT_PATH)
    parser.add_argument("--json-output", type=Path, default=JSON_OUTPUT_PATH)
    parser.add_argument("--csv-output", type=Path, default=CSV_OUTPUT_PATH)
    parser.add_argument("--source-schema", type=Path, default=SOURCE_SCHEMA_PATH)
    parser.add_argument("--public-schema", type=Path, default=PUBLIC_SCHEMA_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    layer = build_layer(
        read_json(args.config),
        read_json(args.observations),
        read_json(args.fx),
        read_json(args.method_route_config),
        read_json(args.top20_routes),
        read_json(args.third_donor_screen),
        read_json(args.donor_cockpit),
    )
    atomic_write_text(
        args.json_output,
        json.dumps(layer, ensure_ascii=False, indent=2) + "\n",
    )
    atomic_write_text(args.csv_output, render_csv(csv_rows(layer)))
    args.public_schema.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.source_schema, args.public_schema)
    print(
        f"Wrote {len(layer['countries'])} countries to {args.json_output} "
        f"and {args.csv_output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
