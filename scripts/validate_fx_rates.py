#!/usr/bin/env python3
"""Validate the public ECB annual-average EUR-equivalent layer."""

from __future__ import annotations

import json
import math
import re
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
SOURCE_FX = ROOT / "source" / "fx-rates.json"
PUBLIC_FX = ROOT / "site" / "data" / "fx-rates.json"
SOURCE_SCHEMA = ROOT / "source" / "schemas" / "fx-rates.schema.json"
PUBLIC_SCHEMA = ROOT / "site" / "schemas" / "fx-rates.schema.json"
MARKET_SOURCE = ROOT / "source" / "market-observations.json"
SCENARIO_SOURCE = ROOT / "source" / "country-scenarios.json"
APP = ROOT / "site" / "assets" / "app.js"
INDEX = ROOT / "site" / "index.html"

EXPECTED_RATES = {
    ("CAD", 2019): Decimal("1.485477254902"),
    ("CAD", 2020): Decimal("1.5299926070039"),
    ("CAD", 2021): Decimal("1.4825689922481"),
    ("CAD", 2022): Decimal("1.3694910505837"),
    ("CAD", 2023): Decimal("1.459468627451"),
    ("CAD", 2024): Decimal("1.482110546875"),
    ("CAD", 2025): Decimal("1.5787262745098"),
    ("NZD", 2022): Decimal("1.6582474708171"),
    ("NZD", 2023): Decimal("1.762151372549"),
    ("NZD", 2024): Decimal("1.788048828125"),
    ("PLN", 2025): Decimal("4.2396576470588"),
    ("SEK", 2024): Decimal("11.432519140625"),
    ("USD", 2015): Decimal("1.109512890625"),
    ("USD", 2016): Decimal("1.1069031128405"),
    ("USD", 2017): Decimal("1.1296811764706"),
    ("USD", 2018): Decimal("1.1809545098039"),
    ("USD", 2019): Decimal("1.1194745098039"),
    ("USD", 2020): Decimal("1.1421961089494"),
    ("USD", 2021): Decimal("1.1827403100775"),
    ("USD", 2025): Decimal("1.1299831372549"),
}

EXPECTED_EUR_CHECKS = {
    "CA-2019-STATCAN-RCS-VAPING-RETAIL-SALES": Decimal("321160757.21"),
    "CA-2020-STATCAN-RCS-VAPING-RETAIL-SALES": Decimal("340293801.17"),
    "CA-2021-STATCAN-RCS-VAPING-RETAIL-SALES": Decimal("669602565.00"),
    "CA-2022-STATCAN-RCS-VAPING-RETAIL-SALES": Decimal("932578565.92"),
    "CA-2023-STATCAN-RCS-VAPING-RETAIL-SALES": Decimal("1048846115.09"),
    "CA-2024-STATCAN-RCS-VAPING-RETAIL-SALES": Decimal("822583715.21"),
    "CA-2025-STATCAN-RCS-VAPING-RETAIL-SALES": Decimal("802271438.98"),
    "CA-2024-MANUFACTURER-IMPORTER-SHIPMENTS-VALUE": Decimal("783176261.20"),
    "NZ-2024-IDENTIFIED-VAPING-PRODUCT-SALES-RAW-SUM": Decimal("153340560.89"),
    "US-2021-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES": Decimal("2336340711.87"),
}

EXPECTED_SCENARIO_EUR = {
    "low": Decimal("298460744.07"),
    "base": Decimal("358945280.35"),
    "high": Decimal("408923839.77"),
}

TOP_LEVEL_KEYS = {
    "schemaVersion",
    "asOf",
    "targetCurrency",
    "provider",
    "calculationPolicy",
    "rates",
}
PROVIDER_KEYS = {"name", "dataset", "datasetUrl", "methodologyUrl"}
POLICY_KEYS = {
    "eligibleRecordPeriods",
    "eligibleUnitRule",
    "rateType",
    "quoteConvention",
    "formulaMachine",
    "formulaEn",
    "formulaFi",
    "originalValueRuleEn",
    "originalValueRuleFi",
    "missingRateStatus",
    "roundingRule",
}
RATE_KEYS = {
    "rateId",
    "seriesKey",
    "currency",
    "year",
    "rateType",
    "currencyUnitsPerEur",
    "sourceUrl",
    "reviewedAt",
    "status",
}
REQUIRED_APP_TOKENS = {
    "assessFxRates",
    "assessEurEquivalent",
    "appendEurEquivalent",
    "appendScenarioComponentEur",
    "renderFxMethod",
    'fetch("data/fx-rates.json"',
    "currency_units_per_eur",
    '"not_computed"',
    "record?.unit",
    "ECB annual average",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def decimal_value(value: Any) -> Decimal | None:
    if isinstance(value, bool):
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() else None


def rate_index(data: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    index: dict[tuple[str, int], dict[str, Any]] = {}
    for item in data.get("rates", []):
        if not isinstance(item, dict):
            continue
        currency = item.get("currency")
        year = item.get("year")
        if isinstance(currency, str) and isinstance(year, int) and not isinstance(year, bool):
            index[(currency, year)] = item
    return index


def assess_conversion(
    record: dict[str, Any],
    rates: dict[tuple[str, int], dict[str, Any]],
    eligible_periods: set[str],
) -> dict[str, Any]:
    value = decimal_value(record.get("value"))
    currency = record.get("currency")
    unit = record.get("unit")
    year = record.get("year")
    period = record.get("period")
    monetary_total = (
        isinstance(currency, str)
        and re.fullmatch(r"[A-Z]{3}", currency) is not None
        and unit == currency
    )
    if value is None or value <= 0 or not monetary_total:
        return {"status": "ineligible", "reason": "not_a_positive_monetary_total"}
    if currency == "EUR":
        return {"status": "already_eur", "eurValue": value}
    if (
        not isinstance(year, int)
        or isinstance(year, bool)
        or period not in eligible_periods
    ):
        return {
            "status": "not_computed",
            "reason": "period_not_compatible_with_annual_average",
        }
    rate = rates.get((currency, year))
    rate_value = decimal_value(rate.get("currencyUnitsPerEur")) if rate else None
    if rate_value is None or rate_value <= 0:
        return {"status": "not_computed", "reason": "compatible_ecb_rate_missing"}
    return {
        "status": "computed",
        "eurValue": value / rate_value,
        "rate": rate,
    }


def validate_rate_document(
    source: dict[str, Any],
    public: dict[str, Any],
    errors: list[str],
) -> None:
    if source != public:
        errors.append("site/data/fx-rates.json differs from the reviewed source")
    if set(source) != TOP_LEVEL_KEYS:
        errors.append("fx-rates.json must use the exact reviewed top-level schema")
        return
    if (
        source.get("schemaVersion") != "1.0"
        or source.get("asOf") != "2026-07-24"
        or source.get("targetCurrency") != "EUR"
    ):
        errors.append("fx-rates.json identity, review date or target currency is invalid")

    provider = source.get("provider")
    if not isinstance(provider, dict) or set(provider) != PROVIDER_KEYS:
        errors.append("fx-rates.json provider must use the exact reviewed schema")
        provider = {}
    if (
        provider.get("name") != "European Central Bank"
        or provider.get("dataset") != "EXR - Exchange Rates"
        or urlparse(str(provider.get("datasetUrl", ""))).hostname != "data.ecb.europa.eu"
        or urlparse(str(provider.get("methodologyUrl", ""))).hostname
        != "www.ecb.europa.eu"
    ):
        errors.append("FX provider and methodology links must remain official ECB sources")

    policy = source.get("calculationPolicy")
    if not isinstance(policy, dict) or set(policy) != POLICY_KEYS:
        errors.append("fx-rates.json calculationPolicy must use the exact reviewed schema")
        policy = {}
    if (
        policy.get("eligibleRecordPeriods")
        != ["calendar_year", "calendar_year_estimate"]
        or policy.get("eligibleUnitRule") != "currency_must_equal_unit"
        or policy.get("rateType") != "annual_average_reference_rate"
        or policy.get("quoteConvention") != "currency_units_per_eur"
        or policy.get("formulaMachine")
        != "eur_equivalent = original_amount / currency_units_per_eur"
        or policy.get("missingRateStatus") != "not_computed"
        or policy.get("roundingRule")
        != "calculate_with_full_published_obs_value_round_display_only"
    ):
        errors.append("FX calculation policy must retain the fail-closed ECB annual-average method")
    for key in ("formulaEn", "formulaFi", "originalValueRuleEn", "originalValueRuleFi"):
        if not isinstance(policy.get(key), str) or not policy[key].strip():
            errors.append(f"fx-rates.json calculationPolicy.{key} must be bilingual non-empty text")

    rates = source.get("rates")
    if not isinstance(rates, list):
        errors.append("fx-rates.json rates must be an array")
        return
    seen_ids: set[str] = set()
    seen_keys: set[tuple[str, int]] = set()
    for position, item in enumerate(rates):
        path = f"fx-rates.json rates[{position}]"
        if not isinstance(item, dict) or set(item) != RATE_KEYS:
            errors.append(f"{path} must use the exact reviewed schema")
            continue
        currency = item.get("currency")
        year = item.get("year")
        key = (currency, year)
        expected_rate = EXPECTED_RATES.get(key)
        expected_series = f"EXR.A.{currency}.EUR.SP00.A"
        expected_id = f"ECB-EXR-A-{currency}-EUR-SP00-A-{year}"
        expected_source = (
            "https://data-api.ecb.europa.eu/service/data/EXR/"
            f"A.{currency}.EUR.SP00.A?startPeriod={year}&endPeriod={year}&format=csvdata"
        )
        if item.get("rateId") in seen_ids or key in seen_keys:
            errors.append(f"{path} duplicates a rate ID or currency-year")
        seen_ids.add(item.get("rateId"))
        seen_keys.add(key)
        if item.get("rateId") != expected_id or item.get("seriesKey") != expected_series:
            errors.append(f"{path} series identity does not match its currency-year")
        if expected_rate is None:
            errors.append(f"{path} is outside the reviewed ECB rate allowlist")
        elif decimal_value(item.get("currencyUnitsPerEur")) != expected_rate:
            errors.append(f"{path} differs from the reviewed ECB OBS_VALUE")
        if (
            item.get("rateType") != "annual_average_reference_rate"
            or item.get("status") != "available"
            or item.get("reviewedAt") != source.get("asOf")
        ):
            errors.append(f"{path} rate type, status or review date is invalid")
        if item.get("sourceUrl") != expected_source:
            errors.append(f"{path} must link to the exact official ECB API observation")
        parsed = urlparse(str(item.get("sourceUrl", "")))
        query = parse_qs(parsed.query)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "data-api.ecb.europa.eu"
            or query.get("startPeriod") != [str(year)]
            or query.get("endPeriod") != [str(year)]
            or query.get("format") != ["csvdata"]
        ):
            errors.append(f"{path} source URL is not a bounded official ECB CSV query")
    if seen_keys != set(EXPECTED_RATES):
        errors.append("fx-rates.json currency-year coverage differs from the reviewed allowlist")


def validate_schema_files(errors: list[str]) -> None:
    if not SOURCE_SCHEMA.is_file() or not PUBLIC_SCHEMA.is_file():
        errors.append("FX JSON Schema source and public copy are both required")
        return
    if SOURCE_SCHEMA.read_bytes() != PUBLIC_SCHEMA.read_bytes():
        errors.append("site/schemas/fx-rates.schema.json differs from the reviewed source")
    schema = load_json(SOURCE_SCHEMA)
    if (
        schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
        or schema.get("title") != "Pixan public ECB EUR-equivalent controls"
        or schema.get("type") != "object"
    ):
        errors.append("FX JSON Schema identity is invalid")


def validate_market_coverage(
    fx: dict[str, Any],
    market: dict[str, Any],
    scenarios: dict[str, Any],
    errors: list[str],
) -> None:
    rates = rate_index(fx)
    policy = fx.get("calculationPolicy", {})
    eligible_periods = set(policy.get("eligibleRecordPeriods", []))
    observations = market.get("observations", [])
    if not isinstance(observations, list):
        errors.append("market-observations.json observations must be an array for FX coverage")
        return
    by_id: dict[str, dict[str, Any]] = {}
    for item in observations:
        if not isinstance(item, dict):
            continue
        observation_id = item.get("observationId")
        if isinstance(observation_id, str):
            by_id[observation_id] = item
        result = assess_conversion(item, rates, eligible_periods)
        is_non_eur_money = (
            item.get("currency") not in (None, "EUR")
            and item.get("unit") == item.get("currency")
        )
        if is_non_eur_money and result.get("status") != "computed":
            errors.append(
                f"{observation_id} has no compatible reviewed ECB annual-average EUR conversion"
            )
        if item.get("unit") in {"litre", "unit", "EUR_per_ml"} and result.get("status") == "computed":
            errors.append(
                f"{observation_id} converts a physical volume, count or unit price as a monetary total"
            )

    cent = Decimal("0.01")
    for observation_id, expected in EXPECTED_EUR_CHECKS.items():
        result = assess_conversion(by_id.get(observation_id, {}), rates, eligible_periods)
        actual = result.get("eurValue")
        if (
            result.get("status") != "computed"
            or not isinstance(actual, Decimal)
            or actual.quantize(cent, rounding=ROUND_HALF_UP) != expected
        ):
            errors.append(f"{observation_id} EUR conversion differs from the reviewed parity check")

    models = market.get("models", [])
    if isinstance(models, list):
        for model in models:
            if not isinstance(model, dict):
                continue
            for bound in ("low", "central", "high"):
                result = assess_conversion(
                    {
                        "value": model.get(bound),
                        "currency": model.get("currency"),
                        "unit": model.get("currency"),
                        "year": model.get("year"),
                        "period": "calendar_year",
                    },
                    rates,
                    eligible_periods,
                )
                if model.get("currency") != "EUR" and result.get("status") != "computed":
                    errors.append(
                        f"{model.get('modelId')}.{bound} lacks a compatible ECB EUR conversion"
                    )

    scenario_records = scenarios.get("countryYearScenarios", [])
    if not isinstance(scenario_records, list):
        errors.append("country-scenarios.json records must be an array for FX coverage")
        return
    nz = next(
        (
            item
            for item in scenario_records
            if isinstance(item, dict) and item.get("scenarioId") == "NZ-2024-RETAIL-RANGE"
        ),
        None,
    )
    if not isinstance(nz, dict):
        errors.append("NZ 2024 scenario is required for EUR parity validation")
        return
    for key, expected in EXPECTED_SCENARIO_EUR.items():
        result = assess_conversion(
            {
                "value": nz.get("inputs", {}).get(key, {}).get("value"),
                "currency": nz.get("currency"),
                "unit": nz.get("currency"),
                "year": nz.get("year"),
                "period": "calendar_year",
            },
            rates,
            eligible_periods,
        )
        actual = result.get("eurValue")
        if (
            result.get("status") != "computed"
            or not isinstance(actual, Decimal)
            or actual.quantize(cent, rounding=ROUND_HALF_UP) != expected
        ):
            errors.append(f"NZ-2024-RETAIL-RANGE.{key} EUR conversion parity failed")

    global_scenario = scenarios.get("globalScenario")
    if isinstance(global_scenario, dict) and global_scenario.get("declaredStatus") == "not_computed":
        values = [
            global_scenario.get("inputs", {}).get(key, {}).get("value")
            for key in ("low", "base", "high")
        ]
        if any(value is not None for value in values):
            errors.append("A blocked global scenario must not acquire EUR-equivalent values")


def validate_site_hooks(app_js: str, index_html: str, errors: list[str]) -> None:
    if 'id="market-fx-method"' not in index_html:
        errors.append("Missing EUR-equivalent method disclosure hook #market-fx-method")
    for token in REQUIRED_APP_TOKENS:
        if token not in app_js:
            errors.append(f"Missing fail-closed EUR-equivalent app control: {token}")
    if "original_amount / currency_units_per_eur" not in app_js:
        errors.append("The UI must expose the original-amount divided-by-rate formula")


def validate_documents(
    source: dict[str, Any],
    public: dict[str, Any],
    market: dict[str, Any],
    scenarios: dict[str, Any],
    app_js: str,
    index_html: str,
) -> list[str]:
    errors: list[str] = []
    validate_rate_document(source, public, errors)
    validate_market_coverage(source, market, scenarios, errors)
    validate_site_hooks(app_js, index_html, errors)
    return errors


def validate_all(root: Path = ROOT) -> list[str]:
    paths = (
        root / "source" / "fx-rates.json",
        root / "site" / "data" / "fx-rates.json",
        root / "source" / "schemas" / "fx-rates.schema.json",
        root / "site" / "schemas" / "fx-rates.schema.json",
        root / "source" / "market-observations.json",
        root / "source" / "country-scenarios.json",
        root / "site" / "assets" / "app.js",
        root / "site" / "index.html",
    )
    missing = [path for path in paths if not path.is_file()]
    if missing:
        return [f"Missing required FX-layer file: {path.relative_to(root)}" for path in missing]
    errors: list[str] = []
    source = load_json(paths[0])
    public = load_json(paths[1])
    validate_schema_files(errors)
    errors.extend(
        validate_documents(
            source,
            public,
            load_json(paths[4]),
            load_json(paths[5]),
            paths[6].read_text(encoding="utf-8"),
            paths[7].read_text(encoding="utf-8"),
        )
    )
    return errors


def main() -> None:
    errors = validate_all()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FX validation failed with {len(errors)} error(s).", file=sys.stderr)
        raise SystemExit(1)
    print(
        "Validated ECB EUR-equivalent layer: 20 official annual-average rates, "
        "original currencies retained, compatible monetary totals converted, "
        "and physical volumes, unit prices and missing scenarios kept fail closed."
    )


if __name__ == "__main__":
    main()
