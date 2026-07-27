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
SOURCE_SCHEMA_PATH = ROOT / "source" / "schemas" / "global-base-layer.schema.json"
JSON_OUTPUT_PATH = ROOT / "site" / "data" / "global-base-layer.json"
CSV_OUTPUT_PATH = ROOT / "site" / "data" / "global-base-layer.csv"
PUBLIC_SCHEMA_PATH = ROOT / "site" / "schemas" / "global-base-layer.schema.json"

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


def build_layer(
    config: dict[str, Any],
    snapshot: dict[str, Any],
    fx: dict[str, Any],
) -> dict[str, Any]:
    indexed = validate_source_contract(config, snapshot)
    usd_rates = available_usd_rates(fx)
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
    return {
        "schemaVersion": config["schemaVersion"],
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
