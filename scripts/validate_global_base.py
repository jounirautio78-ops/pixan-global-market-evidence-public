#!/usr/bin/env python3
"""Validate the fail-closed UN195 global base layer and its public outputs."""

from __future__ import annotations

import argparse
import csv
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from build_atlas import COUNTRY_CATALOG
from build_global_base import (
    CONFIG_PATH,
    CSV_FIELDS,
    CSV_OUTPUT_PATH,
    DONOR_COCKPIT_PATH,
    EXPECTED_ASSIGNMENT_COUNTS,
    FX_PATH,
    JSON_OUTPUT_PATH,
    METHOD_ROUTE_CONFIG_PATH,
    OBSERVATIONS_PATH,
    OUTPUT_SCHEMA_VERSION,
    PUBLIC_SCHEMA_PATH,
    REGIONAL_TPD_PATTERN_COUNTRIES,
    REVIEWED_METHOD_PLAN_COUNTRIES,
    REVIEWED_SOURCE_LEAD_COUNTRIES,
    SOURCE_SCHEMA_PATH,
    THIRD_DONOR_SCREEN_PATH,
    TOP20_ROUTES_PATH,
    build_layer,
    csv_rows,
    read_json,
    render_csv,
    validate_method_route_sources,
    validate_source_contract,
)


OBSERVATION_KEYS = {
    "observationId",
    "countryIso2",
    "measureId",
    "sourceId",
    "sourceSeries",
    "sourcePeriod",
    "value",
    "unit",
    "currency",
    "dataStatus",
    "acquisitionStatus",
    "missingReason",
    "retailSalesEligible",
    "sourceUrl",
}
EXPECTED_SCHEMA_ID = (
    "https://jounirautio78-ops.github.io/"
    "pixan-global-market-evidence-public/schemas/global-base-layer.schema.json"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_url(value: Any, label: str, allowed_hosts: set[str] | None = None) -> None:
    require(isinstance(value, str), f"{label} must be a string URL")
    parsed = urlparse(value)
    require(parsed.scheme == "https" and bool(parsed.netloc), f"{label} must be HTTPS")
    if allowed_hosts is not None:
        require(parsed.netloc in allowed_hosts, f"{label} has an unexpected host")


def validate_config(config: dict[str, Any]) -> None:
    require(config.get("schemaVersion") == "1.0", "config schemaVersion must be 1.0")
    require(config.get("universe", {}).get("id") == "UN193+VA+PS", "wrong universe")
    require(config["universe"].get("countryCount") == 195, "wrong country count")
    policy = config.get("snapshotPolicy", {})
    require(policy.get("startYear") == 2020, "snapshot must start in 2020")
    require(policy.get("endYear") == 2024, "snapshot must end in 2024")
    require(
        policy.get("selection") == "latest_non_null",
        "snapshot selection must be latest_non_null",
    )
    require("never relabelled" in policy.get("sourcePeriodRuleEn", ""), "missing EN year rule")
    require("ei nimetä" in policy.get("sourcePeriodRuleFi", ""), "missing FI year rule")

    measures = config.get("measures")
    require(isinstance(measures, list) and len(measures) == 5, "config needs 5 measures")
    require(
        all(measure.get("retailSalesEligible") is False for measure in measures),
        "every config measure must be retailSalesEligible=false",
    )
    require(
        config.get("globalRollup", {}).get("status") == "blocked",
        "global retail rollup must be blocked",
    )
    require(
        config["globalRollup"].get("retailSalesEligibleObservationCount") == 0,
        "global retail eligible count must be zero",
    )
    eur = config.get("eurPolicy", {})
    require(eur.get("periodRule") == "same_source_year_only", "EUR period rule mismatch")
    require(eur.get("missingRateStatus") == "not_computed", "EUR missing-rate rule mismatch")


def validate_snapshot_details(
    config: dict[str, Any],
    snapshot: dict[str, Any],
) -> dict[tuple[str, str], dict[str, Any]]:
    indexed = validate_source_contract(config, snapshot)
    require(
        all(set(record) == OBSERVATION_KEYS for record in snapshot["observations"]),
        "source observation fields must match the v27 allowlist",
    )
    queries = snapshot.get("snapshot", {}).get("queries")
    require(isinstance(queries, list) and len(queries) == 3, "snapshot needs 3 queries")
    expected_series = {
        "SP.POP.TOTL",
        "SP.POP.1564.TO",
        "NY.GDP.PCAP.CD",
    }
    require(
        {query.get("sourceSeries") for query in queries} == expected_series,
        "World Bank query series mismatch",
    )
    for query in queries:
        validate_url(
            query.get("sourceUrl"),
            f"query {query.get('sourceSeries')}",
            {"api.worldbank.org"},
        )
        require(
            isinstance(query.get("returnedRowCount"), int)
            and query["returnedRowCount"] >= query.get("matchedCountryCount", 0),
            "query row counts are invalid",
        )

    for record in snapshot["observations"]:
        if record["sourceId"] == "WB-WDI":
            validate_url(record["sourceUrl"], record["observationId"], {"api.worldbank.org"})
        elif record["sourceId"] == "WHO-GHO":
            validate_url(record["sourceUrl"], record["observationId"], {"www.who.int"})
        elif record["sourceId"] == "UN-COMTRADE":
            validate_url(
                record["sourceUrl"],
                record["observationId"],
                {"comtradeplus.un.org"},
            )

    queued_counts = Counter(
        record["measureId"]
        for record in snapshot["observations"]
        if record["acquisitionStatus"] == "queued"
    )
    require(
        queued_counts["who_adult_current_ecig_prevalence"] == 195,
        "WHO route must be queued for all 195 countries",
    )
    require(
        queued_counts["un_comtrade_vaping_trade"] == 195,
        "UN Comtrade route must be queued for all 195 countries",
    )
    return indexed


def validate_layer_details(
    config: dict[str, Any],
    snapshot: dict[str, Any],
    fx: dict[str, Any],
    method_route_config: dict[str, Any],
    top20_routes: dict[str, Any],
    third_donor_screen: dict[str, Any],
    donor_cockpit: dict[str, Any],
    layer: dict[str, Any],
) -> None:
    route_controls = validate_method_route_sources(
        method_route_config,
        top20_routes,
        third_donor_screen,
        donor_cockpit,
    )
    expected = build_layer(
        config,
        snapshot,
        fx,
        method_route_config,
        top20_routes,
        third_donor_screen,
        donor_cockpit,
    )
    require(layer == expected, "public JSON is stale or differs from the deterministic build")
    require(
        layer.get("schemaVersion") == OUTPUT_SCHEMA_VERSION,
        "public global-base schemaVersion must be 1.1",
    )
    require(len(layer["countries"]) == 195, "public JSON must have 195 countries")
    require(
        {country["iso2"] for country in layer["countries"]}
        == {country["iso2"] for country in COUNTRY_CATALOG},
        "public JSON country universe differs from COUNTRY_CATALOG",
    )
    require(
        layer["globalRetailSales"]
        == {
            "status": "blocked",
            "value": None,
            "currency": None,
            "eligibleObservationCount": 0,
            "ruleEn": config["globalRollup"]["ruleEn"],
            "ruleFi": config["globalRollup"]["ruleFi"],
        },
        "global retail result must remain blocked and null",
    )

    method_control = layer.get("methodRouteControl")
    require(isinstance(method_control, dict), "methodRouteControl is missing")
    require(
        {
            "version": method_route_config["version"],
            "asOf": method_route_config["asOf"],
            "status": "research_route_map_not_market_values",
        }
        == {
            "version": method_control.get("version"),
            "asOf": method_control.get("asOf"),
            "status": method_control.get("status"),
        },
        "method-route control identity differs from its reviewed config",
    )
    summary = method_control.get("summary", {})
    expected_summary = {
        "countryCount": 195,
        "reviewedMethodPlanCount": 23,
        "reviewedSourceLeadCount": 5,
        "regionalTpdPatternOnlyCount": 15,
        "proxyOnlyUnscopedCount": 152,
        "reviewedNationalRouteOrLeadCount": 28,
        "nonDefaultRouteCount": 43,
        "retailValueStatusCounts": {
            "officialPointEstimateQualityLimited": 1,
            "observedPartialChannelOnly": 1,
            "notComputed": 193,
        },
        "eligibleForGlobalRollupCount": 0,
        "donorAcceptedCount": 0,
    }
    require(summary == expected_summary, "method-route summary differs from v30 contract")
    require(
        method_control.get("methods") == method_route_config["methods"],
        "published method definitions differ from route config",
    )
    require(
        method_control.get("nextActions") == method_route_config["nextActions"],
        "published next actions differ from route config",
    )
    require(
        method_control.get("provenanceSources")
        == method_route_config["provenanceSources"],
        "published provenance sources differ from route config",
    )

    assignment_counts: Counter[str] = Counter()
    retail_status_counts: Counter[str] = Counter()
    donor_assessed_countries: set[str] = set()
    for country in layer["countries"]:
        require(country["retailSalesEligible"] is False, "country retail flag must be false")
        route_control = country.get("methodRoute")
        require(isinstance(route_control, dict), f"{country['iso2']} methodRoute is missing")
        assignment_counts[route_control["assignmentClass"]] += 1
        retail_status_counts[route_control["retailValueStatus"]] += 1
        require(
            route_control["eligibleForGlobalRollup"] is False,
            f"{country['iso2']} must not enter the global rollup",
        )
        require(
            route_control["donorAccepted"] is False,
            f"{country['iso2']} must not be marked as an accepted donor",
        )
        require(
            route_control["lastReviewedOn"] == method_route_config["asOf"],
            f"{country['iso2']} route review date differs",
        )
        primary_method = route_controls["methodMap"][
            route_control["primaryMethodId"]
        ]
        next_action = route_controls["actionMap"][route_control["nextActionId"]]
        require(
            route_control["primaryMethodLabelEn"] == primary_method["labelEn"]
            and route_control["primaryMethodLabelFi"] == primary_method["labelFi"]
            and route_control["transactionStage"] == primary_method["transactionStage"]
            and route_control["boundaryEn"] == primary_method["boundaryEn"]
            and route_control["boundaryFi"] == primary_method["boundaryFi"],
            f"{country['iso2']} primary-method metadata differs",
        )
        require(
            route_control["nextActionEn"] == next_action["labelEn"]
            and route_control["nextActionFi"] == next_action["labelFi"],
            f"{country['iso2']} next-action metadata differs",
        )
        require(
            len(route_control["provenanceBasisIds"])
            == len(set(route_control["provenanceBasisIds"]))
            and {"UN195", "OPEN_BASE"}.issubset(
                route_control["provenanceBasisIds"]
            ),
            f"{country['iso2']} method provenance is incomplete or duplicated",
        )
        if route_control["donorAssessmentState"] == "assessed_not_accepted":
            donor_assessed_countries.add(country["iso2"])
        who = country["routes"]["whoAdultCurrentEcigPrevalence"]
        trade = country["routes"]["unComtradeVapingTrade"]
        for route in (who, trade):
            require(
                route["value"] is None
                and route["sourcePeriod"] is None
                and route["dataStatus"] == "missing"
                and route["acquisitionStatus"] == "queued"
                and route["retailSalesEligible"] is False,
                f"{country['iso2']} queued route contains asserted data",
            )
        gdp = country["worldBank"]["gdpPerCapitaCurrentUsd"]
        eur = gdp["eurEquivalent"]
        require(eur["sourcePeriod"] == gdp["sourcePeriod"], "EUR source period changed")
        if eur["status"] == "computed":
            require(eur["rateYear"] == gdp["sourcePeriod"], "EUR rate year mismatch")
            require(
                eur["value"]
                == round(gdp["value"] / eur["currencyUnitsPerEur"], 2),
                "EUR calculation mismatch",
            )
        else:
            require(eur["value"] is None, "not_computed EUR value must be null")

    require(
        dict(assignment_counts) == EXPECTED_ASSIGNMENT_COUNTS,
        "per-country method assignment counts differ from 23/5/15/152",
    )
    require(
        retail_status_counts
        == {
            "official_point_estimate_quality_limited": 1,
            "observed_partial_channel_only": 1,
            "not_computed": 193,
        },
        "per-country retail-value statuses differ from 1/1/193",
    )
    require(
        donor_assessed_countries == {"CA", "DE", "NZ", "US"},
        "donor-assessment countries differ from donor cockpit",
    )
    by_iso = {country["iso2"]: country["methodRoute"] for country in layer["countries"]}
    require(
        {
            iso2
            for iso2, route in by_iso.items()
            if route["assignmentClass"] == "reviewed_method_plan"
        }
        == REVIEWED_METHOD_PLAN_COUNTRIES,
        "reviewed method-plan country membership differs",
    )
    require(
        {
            iso2
            for iso2, route in by_iso.items()
            if route["assignmentClass"] == "reviewed_source_lead"
        }
        == REVIEWED_SOURCE_LEAD_COUNTRIES,
        "reviewed source-lead country membership differs",
    )
    require(
        {
            iso2
            for iso2, route in by_iso.items()
            if route["assignmentClass"] == "regional_tpd_pattern_only"
        }
        == REGIONAL_TPD_PATTERN_COUNTRIES,
        "regional TPD-pattern country membership differs",
    )
    require(
        by_iso["CA"]["retailValueStatus"]
        == "official_point_estimate_quality_limited"
        and by_iso["NZ"]["retailValueStatus"] == "observed_partial_channel_only"
        and all(
            route["retailValueStatus"] == "not_computed"
            for iso2, route in by_iso.items()
            if iso2 not in {"CA", "NZ"}
        ),
        "retail-value status boundary differs for CA, NZ or the other 193 countries",
    )

    require(
        layer["summary"]["gdpEurEquivalent"]["computedCount"]
        + layer["summary"]["gdpEurEquivalent"]["notComputedCount"]
        == 195,
        "GDP EUR summary must cover 195 countries",
    )


def validate_csv(layer: dict[str, Any], csv_text: str) -> None:
    reader = csv.DictReader(io.StringIO(csv_text))
    require(reader.fieldnames == CSV_FIELDS, "public CSV headers differ from contract")
    actual_rows = list(reader)
    expected_rows = csv_rows(layer)
    require(len(actual_rows) == 195, "public CSV must have 195 rows")
    require(
        csv_text == render_csv(expected_rows),
        "public CSV is stale or differs from the deterministic build",
    )
    require(
        all(row["retail_sales_eligible"] == "false" for row in actual_rows),
        "public CSV retail-sales flag must always be false",
    )
    require(
        all(row["eligible_for_global_rollup"] == "false" for row in actual_rows),
        "public CSV global-rollup eligibility must always be false",
    )
    require(
        all(row["donor_accepted"] == "false" for row in actual_rows),
        "public CSV donor-acceptance flag must always be false",
    )
    require(
        Counter(row["method_assignment_class"] for row in actual_rows)
        == EXPECTED_ASSIGNMENT_COUNTS,
        "public CSV method-assignment counts differ from 23/5/15/152",
    )
    require(
        Counter(row["method_retail_value_status"] for row in actual_rows)
        == {
            "official_point_estimate_quality_limited": 1,
            "observed_partial_channel_only": 1,
            "not_computed": 193,
        },
        "public CSV retail-value statuses differ from 1/1/193",
    )
    require(
        all(row["who_ecig_prevalence_value"] == "" for row in actual_rows),
        "WHO missing values must be empty, not zero, in CSV",
    )
    require(
        all(row["un_comtrade_value"] == "" for row in actual_rows),
        "Comtrade missing values must be empty, not zero, in CSV",
    )


def validate_files(
    *,
    config_path: Path,
    observations_path: Path,
    fx_path: Path,
    json_path: Path,
    csv_path: Path,
    source_schema_path: Path,
    public_schema_path: Path,
    method_route_config_path: Path = METHOD_ROUTE_CONFIG_PATH,
    top20_routes_path: Path = TOP20_ROUTES_PATH,
    third_donor_screen_path: Path = THIRD_DONOR_SCREEN_PATH,
    donor_cockpit_path: Path = DONOR_COCKPIT_PATH,
) -> dict[str, Any]:
    config = read_json(config_path)
    snapshot = read_json(observations_path)
    fx = read_json(fx_path)
    method_route_config = read_json(method_route_config_path)
    top20_routes = read_json(top20_routes_path)
    third_donor_screen = read_json(third_donor_screen_path)
    donor_cockpit = read_json(donor_cockpit_path)
    layer = read_json(json_path)
    source_schema = read_json(source_schema_path)
    public_schema = read_json(public_schema_path)

    validate_config(config)
    validate_snapshot_details(config, snapshot)
    validate_layer_details(
        config,
        snapshot,
        fx,
        method_route_config,
        top20_routes,
        third_donor_screen,
        donor_cockpit,
        layer,
    )
    validate_csv(layer, csv_path.read_text(encoding="utf-8"))
    require(source_schema == public_schema, "source and public schemas differ")
    require(
        source_schema.get("$schema")
        == "https://json-schema.org/draft/2020-12/schema",
        "schema draft identifier is missing",
    )
    require(
        source_schema.get("$id") == EXPECTED_SCHEMA_ID,
        "schema publication identifier differs",
    )
    require(
        source_schema.get("properties", {})
        .get("schemaVersion", {})
        .get("const")
        == OUTPUT_SCHEMA_VERSION,
        "schema must declare the 1.1 public contract",
    )
    return layer


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
    parser.add_argument("--json", type=Path, default=JSON_OUTPUT_PATH)
    parser.add_argument("--csv", type=Path, default=CSV_OUTPUT_PATH)
    parser.add_argument("--source-schema", type=Path, default=SOURCE_SCHEMA_PATH)
    parser.add_argument("--public-schema", type=Path, default=PUBLIC_SCHEMA_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    layer = validate_files(
        config_path=args.config,
        observations_path=args.observations,
        fx_path=args.fx,
        json_path=args.json,
        csv_path=args.csv,
        source_schema_path=args.source_schema,
        public_schema_path=args.public_schema,
        method_route_config_path=args.method_route_config,
        top20_routes_path=args.top20_routes,
        third_donor_screen_path=args.third_donor_screen,
        donor_cockpit_path=args.donor_cockpit,
    )
    print(
        "Global base validation passed: "
        f"{len(layer['countries'])} countries, "
        f"{layer['summary']['observedCount']} observed, "
        f"{layer['summary']['queuedCount']} queued, "
        "23/5/15/152 method-control assignments, global retail sales blocked."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
