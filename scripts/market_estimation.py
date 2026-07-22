#!/usr/bin/env python3
"""Transparent, source-driven annual market-estimation engine.

The engine never fetches data and never supplies country values of its own. It
only transforms explicitly supplied, cited inputs. Each calculation route is an
alternative estimate of the same annual national retail market. Alternative
routes are therefore combined with a weighted median, never added together.

Input records are dictionaries with this minimum shape::

    {
      "countryIso2": "DE",
      "year": 2025,
      "currency": "EUR",
      "scope": {
        "geography": "national",
        "includedProducts": ["e_liquid", "devices"],
        "channel": "legal_retail",
        "valueBasis": "consumer_spend_including_indirect_tax"
      },
      "sources": [{...}],
      "methods": [{...}]
    }

A scalar input is treated as a point range. Uncertain inputs use
``{"low": x, "base": y, "high": z}``. A method emits low/base/high only
after all configured input and source thresholds are satisfied. The overall
record does the same after the independent-method consensus threshold is met.
"""

from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = ROOT / "source" / "model-config.json"

SUPPORTED_METHODS = {
    "direct_reported_value",
    "taxable_volume_price_basket",
    "excise_backsolve_price_basket",
    "customs_apparent_consumption_retail",
    "active_users_annual_spend",
    "usage_units_price",
    "comparable_country_scaling",
    "external_global_sanity_check",
}

DEFAULT_LIMITATIONS = (
    "The output is a modelled market estimate, not an audited market size or a company valuation.",
    "The engine does not verify sources, market definitions, exchange rates, tax allocation, illicit trade or reporting completeness.",
    "Confidence tiers are transparent model weights assigned to supplied evidence, not statistically calibrated probabilities.",
    "Alternative methods are not additive. Correlated methods sharing one evidence group contribute at most one consensus candidate.",
    "A national market estimate does not establish Pixan revenue, patent coverage, infringement, damages, licensing income or collateral value.",
)


class InputIssue(ValueError):
    """A structured reason why one estimate is not ready."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load and structurally validate the model configuration."""

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    if config.get("configSchemaVersion") != 1:
        raise ValueError("model config must use configSchemaVersion 1")
    method_definitions = config.get("methodDefinitions")
    if not isinstance(method_definitions, dict):
        raise ValueError("model config methodDefinitions must be an object")
    configured = set(method_definitions)
    if configured != SUPPORTED_METHODS:
        missing = sorted(SUPPORTED_METHODS - configured)
        unknown = sorted(configured - SUPPORTED_METHODS)
        raise ValueError(f"model config method mismatch; missing={missing}, unknown={unknown}")
    if config.get("consensus", {}).get("neverSumAlternativeMethods") is not True:
        raise ValueError("model config must prohibit summing alternative methods")
    for method_id, definition in method_definitions.items():
        if definition.get("role") not in {"primary", "sanity_check"}:
            raise ValueError(f"{method_id}: role must be primary or sanity_check")
        _decimal(definition.get("baseWeight"), f"config.{method_id}.baseWeight", positive=True)
        minimum_sources = definition.get("minimumSources")
        if isinstance(minimum_sources, bool) or not isinstance(minimum_sources, int) or minimum_sources < 1:
            raise ValueError(f"{method_id}: minimumSources must be a positive integer")
    return config


def _decimal(
    value: Any,
    path: str,
    *,
    positive: bool = False,
    maximum: Decimal | None = None,
) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise InputIssue("invalid_number", f"{path} must be a finite number")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise InputIssue("invalid_number", f"{path} must be a finite number") from None
    if not number.is_finite():
        raise InputIssue("invalid_number", f"{path} must be a finite number")
    if positive and number <= 0:
        raise InputIssue("out_of_range", f"{path} must be greater than zero")
    if not positive and number < 0:
        raise InputIssue("out_of_range", f"{path} cannot be negative")
    if maximum is not None and number > maximum:
        raise InputIssue("out_of_range", f"{path} cannot exceed {maximum}")
    return number


def _range(
    value: Any,
    path: str,
    *,
    positive: bool = False,
    maximum: Decimal | None = None,
) -> dict[str, Decimal]:
    if isinstance(value, Mapping):
        missing = [key for key in ("low", "base", "high") if key not in value]
        if missing:
            raise InputIssue("missing_range_bound", f"{path} is missing {', '.join(missing)}")
        result = {
            key: _decimal(value[key], f"{path}.{key}", positive=positive, maximum=maximum)
            for key in ("low", "base", "high")
        }
    else:
        point = _decimal(value, path, positive=positive, maximum=maximum)
        result = {"low": point, "base": point, "high": point}
    if not result["low"] <= result["base"] <= result["high"]:
        raise InputIssue("invalid_range_order", f"{path} must satisfy low <= base <= high")
    return result


def _number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def _public_range(value: Mapping[str, Decimal]) -> dict[str, int | float]:
    return {key: _number(value[key]) for key in ("low", "base", "high")}


def _multiply(*ranges: Mapping[str, Decimal]) -> dict[str, Decimal]:
    result = {"low": Decimal(1), "base": Decimal(1), "high": Decimal(1)}
    for current in ranges:
        for key in result:
            result[key] *= current[key]
    return result


def _divide(numerator: Mapping[str, Decimal], denominator: Mapping[str, Decimal]) -> dict[str, Decimal]:
    return {
        "low": numerator["low"] / denominator["high"],
        "base": numerator["base"] / denominator["base"],
        "high": numerator["high"] / denominator["low"],
    }


def _add(ranges: Iterable[Mapping[str, Decimal]]) -> dict[str, Decimal]:
    result = {"low": Decimal(0), "base": Decimal(0), "high": Decimal(0)}
    for current in ranges:
        for key in result:
            result[key] += current[key]
    return result


def _median(values: Sequence[Decimal]) -> Decimal:
    if not values:
        raise InputIssue("missing_comparables", "at least one comparable value is required")
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / Decimal(2)


def _weighted_quantile(
    values_and_weights: Sequence[tuple[Decimal, Decimal]],
    quantile: Decimal,
) -> Decimal:
    """Weighted quantile using interpolation between weight-centre positions."""

    if not values_and_weights:
        raise ValueError("weighted quantile requires at least one value")
    ordered = sorted(values_and_weights, key=lambda item: item[0])
    total_weight = sum((weight for _, weight in ordered), Decimal(0))
    if total_weight <= 0:
        raise ValueError("weighted quantile requires positive total weight")
    if len(ordered) == 1:
        return ordered[0][0]

    centres: list[tuple[Decimal, Decimal]] = []
    cumulative = Decimal(0)
    for value, weight in ordered:
        centres.append((value, (cumulative + weight / Decimal(2)) / total_weight))
        cumulative += weight

    if quantile <= centres[0][1]:
        return centres[0][0]
    if quantile >= centres[-1][1]:
        return centres[-1][0]
    for index in range(1, len(centres)):
        right_value, right_position = centres[index]
        left_value, left_position = centres[index - 1]
        if quantile <= right_position:
            fraction = (quantile - left_position) / (right_position - left_position)
            return left_value + (right_value - left_value) * fraction
    return centres[-1][0]


def _require_inputs(inputs: Mapping[str, Any], required: Sequence[str]) -> None:
    missing = [name for name in required if name not in inputs]
    if missing:
        raise InputIssue("missing_inputs", f"missing required inputs: {', '.join(missing)}")


def _scope_factor(inputs: Mapping[str, Any], path: str) -> dict[str, Decimal]:
    return _range(inputs["scopeAdjustmentFactor"], f"{path}.scopeAdjustmentFactor", positive=True)


def _calculate_direct(
    inputs: Mapping[str, Any], context: Mapping[str, Any]
) -> tuple[dict[str, Decimal], dict[str, Any]]:
    estimate = _range(inputs["reportedMarketValue"], "inputs.reportedMarketValue", positive=True)
    return estimate, {"reportedMarketValue": _public_range(estimate)}


def _calculate_taxable_volume(
    inputs: Mapping[str, Any], context: Mapping[str, Any]
) -> tuple[dict[str, Decimal], dict[str, Any]]:
    unit = inputs.get("unit")
    if not isinstance(unit, str) or not unit.strip():
        raise InputIssue("missing_unit", "inputs.unit must identify the common volume and price unit")
    volume = _range(inputs["taxableVolume"], "inputs.taxableVolume", positive=True)
    price = _range(inputs["retailPricePerUnit"], "inputs.retailPricePerUnit", positive=True)
    adjustment = _scope_factor(inputs, "inputs")
    estimate = _multiply(volume, price, adjustment)
    return estimate, {
        "unit": unit,
        "taxableVolume": _public_range(volume),
        "retailPricePerUnit": _public_range(price),
        "scopeAdjustmentFactor": _public_range(adjustment),
    }


def _calculate_excise_backsolve(
    inputs: Mapping[str, Any], context: Mapping[str, Any]
) -> tuple[dict[str, Decimal], dict[str, Any]]:
    unit = inputs.get("unit")
    if not isinstance(unit, str) or not unit.strip():
        raise InputIssue("missing_unit", "inputs.unit must identify the excise-rate and price unit")
    revenue = _range(inputs["realisedExciseRevenue"], "inputs.realisedExciseRevenue", positive=True)
    rate = _range(inputs["exciseRatePerUnit"], "inputs.exciseRatePerUnit", positive=True)
    price = _range(inputs["retailPricePerUnit"], "inputs.retailPricePerUnit", positive=True)
    adjustment = _scope_factor(inputs, "inputs")
    implied_volume = _divide(revenue, rate)
    estimate = _multiply(implied_volume, price, adjustment)
    return estimate, {
        "unit": unit,
        "impliedTaxableVolume": _public_range(implied_volume),
        "scopeAdjustmentFactor": _public_range(adjustment),
    }


def _calculate_customs(
    inputs: Mapping[str, Any], context: Mapping[str, Any]
) -> tuple[dict[str, Decimal], dict[str, Any]]:
    imports = _range(inputs["importsValue"], "inputs.importsValue")
    production = _range(inputs["domesticProductionValue"], "inputs.domesticProductionValue")
    exports = _range(inputs["exportsValue"], "inputs.exportsValue")
    markup = _range(inputs["retailMarkupFactor"], "inputs.retailMarkupFactor", positive=True)
    adjustment = _scope_factor(inputs, "inputs")
    apparent = {
        "low": max(Decimal(0), imports["low"] + production["low"] - exports["high"]),
        "base": max(Decimal(0), imports["base"] + production["base"] - exports["base"]),
        "high": max(Decimal(0), imports["high"] + production["high"] - exports["low"]),
    }
    estimate = _multiply(apparent, markup, adjustment)
    return estimate, {
        "apparentConsumptionAtDeclaredFlowValue": _public_range(apparent),
        "retailMarkupFactor": _public_range(markup),
        "scopeAdjustmentFactor": _public_range(adjustment),
    }


def _calculate_users_spend(
    inputs: Mapping[str, Any], context: Mapping[str, Any]
) -> tuple[dict[str, Decimal], dict[str, Any]]:
    users = _range(inputs["activeUsers"], "inputs.activeUsers", positive=True)
    spend = _range(inputs["annualSpendPerUser"], "inputs.annualSpendPerUser", positive=True)
    adjustment = _scope_factor(inputs, "inputs")
    estimate = _multiply(users, spend, adjustment)
    return estimate, {
        "activeUsers": _public_range(users),
        "annualSpendPerUser": _public_range(spend),
        "scopeAdjustmentFactor": _public_range(adjustment),
    }


def _calculate_usage_units(
    inputs: Mapping[str, Any], context: Mapping[str, Any]
) -> tuple[dict[str, Decimal], dict[str, Any]]:
    users = _range(inputs["activeUsers"], "inputs.activeUsers", positive=True)
    adjustment = _scope_factor(inputs, "inputs")
    components = inputs.get("components")
    if not isinstance(components, list) or not components:
        raise InputIssue("missing_components", "inputs.components must be a non-empty array")

    seen_ids: set[str] = set()
    seen_scopes: set[str] = set()
    component_spend: list[dict[str, Decimal]] = []
    public_components: list[dict[str, Any]] = []
    for index, component in enumerate(components):
        path = f"inputs.components[{index}]"
        if not isinstance(component, Mapping):
            raise InputIssue("invalid_component", f"{path} must be an object")
        component_id = component.get("componentId")
        revenue_scope_id = component.get("revenueScopeId")
        unit = component.get("unit")
        if not isinstance(component_id, str) or not component_id:
            raise InputIssue("invalid_component", f"{path}.componentId must be a non-empty string")
        if component_id in seen_ids:
            raise InputIssue("duplicate_component", f"duplicate componentId {component_id}")
        seen_ids.add(component_id)
        if not isinstance(revenue_scope_id, str) or not revenue_scope_id:
            raise InputIssue("missing_revenue_scope", f"{path}.revenueScopeId must be a non-empty string")
        if revenue_scope_id in seen_scopes:
            raise InputIssue(
                "overlapping_component_scope",
                f"revenueScopeId {revenue_scope_id} is repeated; overlapping components cannot be added",
            )
        seen_scopes.add(revenue_scope_id)
        if component.get("isDisjointRevenueScope") is not True:
            raise InputIssue(
                "unconfirmed_disjoint_scope",
                f"{path}.isDisjointRevenueScope must be true before components may be added",
            )
        if not isinstance(unit, str) or not unit:
            raise InputIssue("missing_unit", f"{path}.unit must be a non-empty string")
        share = _range(component.get("userShare"), f"{path}.userShare", maximum=Decimal(1))
        units = _range(component.get("annualUnitsPerUser"), f"{path}.annualUnitsPerUser", positive=True)
        price = _range(component.get("retailPricePerUnit"), f"{path}.retailPricePerUnit", positive=True)
        annual_spend = _multiply(share, units, price)
        component_spend.append(annual_spend)
        public_components.append(
            {
                "componentId": component_id,
                "revenueScopeId": revenue_scope_id,
                "unit": unit,
                "annualSpendPerActiveUser": _public_range(annual_spend),
            }
        )
    combined_spend = _add(component_spend)
    estimate = _multiply(users, combined_spend, adjustment)
    return estimate, {
        "activeUsers": _public_range(users),
        "combinedAnnualSpendPerActiveUser": _public_range(combined_spend),
        "components": public_components,
        "scopeAdjustmentFactor": _public_range(adjustment),
    }


def _calculate_comparables(
    inputs: Mapping[str, Any], context: Mapping[str, Any]
) -> tuple[dict[str, Decimal], dict[str, Any]]:
    target_scale = _range(inputs["targetScaleBase"], "inputs.targetScaleBase", positive=True)
    scale_metric = inputs.get("scaleMetric")
    if not isinstance(scale_metric, str) or not scale_metric.strip():
        raise InputIssue("missing_scale_metric", "inputs.scaleMetric must be a non-empty string")
    comparables = inputs.get("comparables")
    minimum = int(context.get("minimumComparables", 2))
    if not isinstance(comparables, list) or len(comparables) < minimum:
        raise InputIssue("insufficient_comparables", f"at least {minimum} comparable countries are required")

    target_iso2 = context["countryIso2"]
    method_source_ids = set(context["sourceIds"])
    seen_countries: set[str] = set()
    referenced_comparable_sources: set[str] = set()
    derived: list[dict[str, Decimal]] = []
    public_comparables: list[dict[str, Any]] = []
    for index, comparable in enumerate(comparables):
        path = f"inputs.comparables[{index}]"
        if not isinstance(comparable, Mapping):
            raise InputIssue("invalid_comparable", f"{path} must be an object")
        country_iso2 = comparable.get("countryIso2")
        if not isinstance(country_iso2, str) or len(country_iso2) != 2 or not country_iso2.isalpha():
            raise InputIssue("invalid_comparable_country", f"{path}.countryIso2 must be a two-letter code")
        country_iso2 = country_iso2.upper()
        if country_iso2 == target_iso2:
            raise InputIssue("self_comparable", f"{path} cannot use the target country as a comparable")
        if country_iso2 in seen_countries:
            raise InputIssue("duplicate_comparable", f"comparable country {country_iso2} is repeated")
        seen_countries.add(country_iso2)
        if comparable.get("marketDefinitionMatch") is not True:
            raise InputIssue(
                "unconfirmed_market_definition",
                f"{path}.marketDefinitionMatch must be true before the comparable can be used",
            )
        comparable_source_ids = comparable.get("sourceIds")
        if not isinstance(comparable_source_ids, list) or not comparable_source_ids:
            raise InputIssue("missing_comparable_sources", f"{path}.sourceIds must be a non-empty array")
        if len(comparable_source_ids) != len(set(comparable_source_ids)):
            raise InputIssue("duplicate_comparable_source", f"{path}.sourceIds must be unique")
        if not set(comparable_source_ids) <= method_source_ids:
            raise InputIssue(
                "unlinked_comparable_source",
                f"{path}.sourceIds must refer to the method's cited sourceIds",
            )
        referenced_comparable_sources.update(comparable_source_ids)
        market_value = _range(comparable.get("marketValue"), f"{path}.marketValue", positive=True)
        comparable_scale = _range(comparable.get("scaleBase"), f"{path}.scaleBase", positive=True)
        adjustment = _range(
            comparable.get("comparabilityAdjustmentFactor"),
            f"{path}.comparabilityAdjustmentFactor",
            positive=True,
        )
        per_scale = _divide(market_value, comparable_scale)
        estimate = _multiply(per_scale, target_scale, adjustment)
        derived.append(estimate)
        public_comparables.append(
            {
                "countryIso2": country_iso2,
                "sourceIds": list(comparable_source_ids),
                "derivedTargetEstimate": _public_range(estimate),
            }
        )

    if len(referenced_comparable_sources) < minimum:
        raise InputIssue(
            "insufficient_comparable_sources",
            f"the comparable set must link at least {minimum} distinct sources",
        )

    estimate = {
        key: _median([candidate[key] for candidate in derived])
        for key in ("low", "base", "high")
    }
    return estimate, {
        "scaleMetric": scale_metric,
        "targetScaleBase": _public_range(target_scale),
        "comparables": public_comparables,
        "comparableAggregation": "unweighted median of individually scaled comparable-country estimates",
    }


def _calculate_global_check(
    inputs: Mapping[str, Any], context: Mapping[str, Any]
) -> tuple[dict[str, Decimal], dict[str, Any]]:
    benchmark = _range(inputs["benchmarkMarketValue"], "inputs.benchmarkMarketValue", positive=True)
    share = _range(inputs["targetCountryShare"], "inputs.targetCountryShare", maximum=Decimal(1))
    if share["base"] <= 0:
        raise InputIssue("out_of_range", "inputs.targetCountryShare.base must be greater than zero")
    estimate = _multiply(benchmark, share)
    return estimate, {
        "benchmarkMarketValue": _public_range(benchmark),
        "targetCountryShare": _public_range(share),
    }


CALCULATORS: dict[
    str,
    Callable[
        [Mapping[str, Any], Mapping[str, Any]],
        tuple[dict[str, Decimal], dict[str, Any]],
    ],
] = {
    "direct_reported_value": _calculate_direct,
    "taxable_volume_price_basket": _calculate_taxable_volume,
    "excise_backsolve_price_basket": _calculate_excise_backsolve,
    "customs_apparent_consumption_retail": _calculate_customs,
    "active_users_annual_spend": _calculate_users_spend,
    "usage_units_price": _calculate_usage_units,
    "comparable_country_scaling": _calculate_comparables,
    "external_global_sanity_check": _calculate_global_check,
}


def _validate_record_header(record: Mapping[str, Any]) -> list[dict[str, str]]:
    reasons: list[dict[str, str]] = []
    country_iso2 = record.get("countryIso2")
    if not isinstance(country_iso2, str) or len(country_iso2) != 2 or not country_iso2.isalpha():
        reasons.append({"code": "invalid_country", "message": "countryIso2 must be a two-letter code"})
    year = record.get("year")
    if isinstance(year, bool) or not isinstance(year, int) or not 2000 <= year <= 2100:
        reasons.append({"code": "invalid_year", "message": "year must be an integer from 2000 to 2100"})
    currency = record.get("currency")
    if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha():
        reasons.append({"code": "invalid_currency", "message": "currency must be a three-letter code"})
    scope = record.get("scope")
    required_scope = ("geography", "includedProducts", "channel", "valueBasis")
    if not isinstance(scope, Mapping):
        reasons.append({"code": "missing_scope", "message": "scope must be an object"})
    else:
        for key in required_scope:
            if key not in scope:
                reasons.append({"code": "missing_scope_field", "message": f"scope.{key} is required"})
        products = scope.get("includedProducts")
        if not isinstance(products, list) or not products or not all(isinstance(item, str) and item for item in products):
            reasons.append(
                {"code": "invalid_products", "message": "scope.includedProducts must be a non-empty string array"}
            )
        for key in ("geography", "channel", "valueBasis"):
            if key in scope and (not isinstance(scope[key], str) or not scope[key].strip()):
                reasons.append(
                    {"code": "invalid_scope_field", "message": f"scope.{key} must be a non-empty string"}
                )
    limitations = record.get("limitations", [])
    if not isinstance(limitations, list) or not all(isinstance(item, str) for item in limitations):
        reasons.append(
            {"code": "invalid_limitations", "message": "limitations must be a string array when supplied"}
        )
    return reasons


def _source_index(record: Mapping[str, Any]) -> tuple[dict[str, Mapping[str, Any]], list[dict[str, str]]]:
    sources = record.get("sources")
    if not isinstance(sources, list):
        return {}, [{"code": "missing_sources", "message": "sources must be an array"}]
    index: dict[str, Mapping[str, Any]] = {}
    reasons: list[dict[str, str]] = []
    required = ("sourceId", "title", "publisher", "period", "metric", "url", "limitations")
    for position, source in enumerate(sources):
        if not isinstance(source, Mapping):
            reasons.append({"code": "invalid_source", "message": f"sources[{position}] must be an object"})
            continue
        missing = [key for key in required if key not in source]
        if missing:
            reasons.append(
                {
                    "code": "incomplete_source",
                    "message": f"sources[{position}] is missing {', '.join(missing)}",
                }
            )
            continue
        source_id = source.get("sourceId")
        if not isinstance(source_id, str) or not source_id:
            reasons.append({"code": "invalid_source_id", "message": f"sources[{position}].sourceId is invalid"})
            continue
        if source_id in index:
            reasons.append({"code": "duplicate_source_id", "message": f"duplicate sourceId {source_id}"})
            continue
        for key in ("title", "publisher", "period", "metric", "url", "limitations"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                reasons.append(
                    {
                        "code": "invalid_source_field",
                        "message": f"sources[{position}].{key} must be a non-empty string",
                    }
                )
        if any(
            not isinstance(source.get(key), str) or not source[key].strip()
            for key in ("title", "publisher", "period", "metric", "url", "limitations")
        ):
            continue
        index[source_id] = source
    return index, reasons


def _method_not_ready(
    method: Mapping[str, Any],
    definition: Mapping[str, Any] | None,
    reason: InputIssue,
) -> dict[str, Any]:
    method_id = method.get("methodId")
    return {
        "estimateId": method.get("estimateId"),
        "methodId": method_id,
        "label": definition.get("label") if definition else None,
        "role": definition.get("role") if definition else None,
        "status": "not_estimate_ready",
        "formula": definition.get("formula") if definition else None,
        "inputs": method.get("inputs"),
        "sourceIds": method.get("sourceIds", []),
        "evidenceGroup": method.get("evidenceGroup"),
        "confidence": {"tier": method.get("confidence"), "score": None},
        "reasonCodes": [{"code": reason.code, "message": reason.message}],
        "includedInConsensus": False,
        "consensusExclusionReason": "method_not_ready",
    }


def _calculate_method(
    method: Mapping[str, Any],
    record: Mapping[str, Any],
    source_index: Mapping[str, Mapping[str, Any]],
    config: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Decimal] | None, Decimal | None]:
    method_id = method.get("methodId")
    definition = config["methodDefinitions"].get(method_id)
    if definition is None:
        reason = InputIssue("unknown_method", f"unsupported methodId {method_id!r}")
        return _method_not_ready(method, None, reason), None, None
    try:
        estimate_id = method.get("estimateId")
        if not isinstance(estimate_id, str) or not estimate_id:
            raise InputIssue("missing_estimate_id", "estimateId must be a non-empty string")
        evidence_group = method.get("evidenceGroup")
        if not isinstance(evidence_group, str) or not evidence_group:
            raise InputIssue("missing_evidence_group", "evidenceGroup must be a non-empty string")
        confidence_tier = method.get("confidence")
        confidence_scores = config["confidenceTiers"]
        if confidence_tier not in confidence_scores:
            raise InputIssue(
                "invalid_confidence",
                f"confidence must be one of {', '.join(sorted(confidence_scores))}",
            )
        source_ids = method.get("sourceIds")
        if not isinstance(source_ids, list) or any(not isinstance(item, str) for item in source_ids):
            raise InputIssue("invalid_source_refs", "sourceIds must be a string array")
        if len(source_ids) != len(set(source_ids)):
            raise InputIssue("duplicate_source_ref", "sourceIds must be unique")
        missing_sources = [source_id for source_id in source_ids if source_id not in source_index]
        if missing_sources:
            raise InputIssue("unknown_source_ref", f"unknown sourceIds: {', '.join(missing_sources)}")
        if len(source_ids) < int(definition["minimumSources"]):
            raise InputIssue(
                "insufficient_sources",
                f"{method_id} requires at least {definition['minimumSources']} distinct sources",
            )
        inputs = method.get("inputs")
        if not isinstance(inputs, Mapping):
            raise InputIssue("missing_inputs", "inputs must be an object")
        _require_inputs(inputs, definition["requiredInputs"])
        context = {
            "countryIso2": str(record["countryIso2"]).upper(),
            "sourceIds": source_ids,
            "minimumComparables": definition.get("minimumComparables", 0),
        }
        estimate, derivation = CALCULATORS[method_id](inputs, context)
        if not estimate["low"] <= estimate["base"] <= estimate["high"]:
            raise InputIssue("invalid_derived_range", "derived estimate does not satisfy low <= base <= high")
        if estimate["base"] <= 0:
            raise InputIssue("zero_estimate", "derived base estimate must be greater than zero")
        confidence_score = _decimal(confidence_scores[confidence_tier], "confidence score", positive=True)
        method_weight = _decimal(definition["baseWeight"], f"{method_id}.baseWeight", positive=True)
        effective_weight = confidence_score * method_weight
        result = {
            "estimateId": estimate_id,
            "methodId": method_id,
            "label": definition["label"],
            "role": definition["role"],
            "status": "estimate_ready",
            "formula": definition["formula"],
            "inputs": inputs,
            "derivation": derivation,
            "estimate": {
                "currency": str(record["currency"]).upper(),
                **_public_range(estimate),
            },
            "sourceIds": source_ids,
            "sources": [dict(source_index[source_id]) for source_id in source_ids],
            "evidenceGroup": evidence_group,
            "confidence": {
                "tier": confidence_tier,
                "score": _number(confidence_score),
                "methodBaseWeight": _number(method_weight),
                "effectiveWeight": _number(effective_weight),
            },
            "limitations": method.get("limitations", []),
            "includedInConsensus": False,
            "consensusExclusionReason": None,
        }
        return result, estimate, effective_weight
    except InputIssue as issue:
        return _method_not_ready(method, definition, issue), None, None


def _confidence_label(score: Decimal, config: Mapping[str, Any]) -> str:
    thresholds = config["confidenceLabels"]
    if score >= Decimal(str(thresholds["highAtOrAbove"])):
        return "high"
    if score >= Decimal(str(thresholds["mediumAtOrAbove"])):
        return "medium"
    return "low"


def estimate_market(
    record: Mapping[str, Any],
    config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Estimate one annual national market from a fully explicit input record.

    Invalid or insufficient country inputs return ``not_estimate_ready`` rather
    than raising. A structurally invalid model configuration raises ValueError,
    because that is a deployment error rather than a missing-country-data state.
    """

    if config is None:
        config = load_config()
    else:
        # Validate caller-supplied config by checking the same invariants without
        # requiring it to be written to disk.
        if config.get("configSchemaVersion") != 1:
            raise ValueError("model config must use configSchemaVersion 1")
        if set(config.get("methodDefinitions", {})) != SUPPORTED_METHODS:
            raise ValueError("caller-supplied model config has unsupported method definitions")
        if config.get("consensus", {}).get("neverSumAlternativeMethods") is not True:
            raise ValueError("model config must prohibit summing alternative methods")

    if not isinstance(record, Mapping):
        return {
            "outputSchemaVersion": 1,
            "modelId": config["modelId"],
            "countryIso2": None,
            "year": None,
            "currency": None,
            "scope": None,
            "status": "not_estimate_ready",
            "alternativeMethodsAreAdditive": False,
            "methodResults": [],
            "sanityChecks": [],
            "limitations": list(DEFAULT_LIMITATIONS),
            "reasonCodes": [
                {"code": "invalid_record", "message": "input record must be a JSON object"}
            ],
        }

    header_reasons = _validate_record_header(record)
    source_index, source_reasons = _source_index(record)
    top_level_reasons = header_reasons + source_reasons
    record_limitations = record.get("limitations", [])
    if not isinstance(record_limitations, list):
        record_limitations = []
    base_output: dict[str, Any] = {
        "outputSchemaVersion": 1,
        "modelId": config["modelId"],
        "countryIso2": str(record.get("countryIso2", "")).upper() or None,
        "year": record.get("year"),
        "currency": str(record.get("currency", "")).upper() or None,
        "scope": record.get("scope"),
        "status": "not_estimate_ready",
        "alternativeMethodsAreAdditive": False,
        "methodResults": [],
        "sanityChecks": [],
        "limitations": list(DEFAULT_LIMITATIONS) + list(record_limitations),
    }
    if top_level_reasons:
        base_output["reasonCodes"] = top_level_reasons
        return base_output

    methods = record.get("methods")
    if not isinstance(methods, list) or not methods:
        base_output["reasonCodes"] = [
            {"code": "missing_methods", "message": "methods must be a non-empty array"}
        ]
        return base_output

    seen_estimate_ids: set[str] = set()
    internal: list[tuple[dict[str, Any], dict[str, Decimal] | None, Decimal | None]] = []
    for position, method in enumerate(methods):
        if not isinstance(method, Mapping):
            placeholder = {"estimateId": None, "methodId": None, "inputs": None, "sourceIds": []}
            issue = InputIssue("invalid_method", f"methods[{position}] must be an object")
            internal.append((_method_not_ready(placeholder, None, issue), None, None))
            continue
        estimate_id = method.get("estimateId")
        if isinstance(estimate_id, str) and estimate_id in seen_estimate_ids:
            issue = InputIssue("duplicate_estimate_id", f"duplicate estimateId {estimate_id}")
            definition = config["methodDefinitions"].get(method.get("methodId"))
            internal.append((_method_not_ready(method, definition, issue), None, None))
            continue
        if isinstance(estimate_id, str):
            seen_estimate_ids.add(estimate_id)
        internal.append(_calculate_method(method, record, source_index, config))

    primary_by_group: dict[str, list[tuple[dict[str, Any], dict[str, Decimal], Decimal]]] = {}
    sanity_internal: list[tuple[dict[str, Any], dict[str, Decimal]]] = []
    for result, estimate, weight in internal:
        if result["status"] != "estimate_ready" or estimate is None or weight is None:
            continue
        if result["role"] == "sanity_check":
            result["consensusExclusionReason"] = "sanity_check_only"
            sanity_internal.append((result, estimate))
            continue
        primary_by_group.setdefault(result["evidenceGroup"], []).append((result, estimate, weight))

    group_winners: list[tuple[dict[str, Any], dict[str, Decimal], Decimal]] = []
    for evidence_group in sorted(primary_by_group):
        candidates = sorted(
            primary_by_group[evidence_group],
            key=lambda item: (-item[2], item[0]["estimateId"]),
        )
        winner = candidates[0]
        group_winners.append(winner)
        for excluded, _, _ in candidates[1:]:
            excluded["consensusExclusionReason"] = "correlated_evidence_group_lower_weight"

    # A free-form evidence-group label is not enough to establish independence.
    # Conservatively retain only methods whose cited source IDs do not overlap
    # with a higher-weight selected method, regardless of how groups are named.
    selected: list[tuple[dict[str, Any], dict[str, Decimal], Decimal]] = []
    selected_source_ids: dict[str, str] = {}
    for candidate in sorted(
        group_winners,
        key=lambda item: (-item[2], item[0]["estimateId"]),
    ):
        result = candidate[0]
        source_ids = set(result.get("sourceIds", []))
        overlapping_source_ids = sorted(source_ids.intersection(selected_source_ids))
        if overlapping_source_ids:
            result["consensusExclusionReason"] = "overlapping_source_ids"
            result["overlappingSourceIds"] = overlapping_source_ids
            result["overlapsSelectedEstimateIds"] = sorted(
                {selected_source_ids[source_id] for source_id in overlapping_source_ids}
            )
            continue
        result["includedInConsensus"] = True
        selected.append(candidate)
        for source_id in source_ids:
            selected_source_ids[source_id] = result["estimateId"]

    base_output["methodResults"] = [result for result, _, _ in internal]
    consensus_config = config["consensus"]
    minimum_methods = int(consensus_config["minimumPrimaryMethods"])
    minimum_groups = int(consensus_config["minimumIndependentEvidenceGroups"])
    standalone_methods = set(consensus_config["standaloneEligibleMethods"])
    standalone_tier = consensus_config["standaloneMinimumConfidenceTier"]
    confidence_scores = config["confidenceTiers"]
    standalone_threshold = Decimal(str(confidence_scores[standalone_tier]))

    threshold_met = len(selected) >= minimum_methods and len(selected) >= minimum_groups
    standalone_used = False
    if not threshold_met and len(selected) == 1:
        selected_result = selected[0][0]
        selected_confidence = Decimal(str(selected_result["confidence"]["score"]))
        standalone_used = (
            selected_result["methodId"] in standalone_methods
            and selected_confidence >= standalone_threshold
        )
        threshold_met = standalone_used

    if not threshold_met:
        base_output["reasonCodes"] = [
            {
                "code": "insufficient_independent_methods",
                "message": (
                    f"consensus requires at least {minimum_methods} ready primary methods from "
                    f"{minimum_groups} independent evidence groups, or an eligible high-confidence "
                    "direct reported value"
                ),
            }
        ]
        base_output["consensus"] = {
            "readyPrimaryMethods": len(selected),
            "independentEvidenceGroups": len(selected),
            "selectedEstimateIds": [item[0]["estimateId"] for item in selected],
            "aggregation": consensus_config["aggregation"],
            "alternativeMethodsWereSummed": False,
        }
        return base_output

    low_quantile = Decimal(str(consensus_config["lowQuantile"]))
    base_quantile = Decimal(str(consensus_config["baseQuantile"]))
    high_quantile = Decimal(str(consensus_config["highQuantile"]))
    low = _weighted_quantile([(estimate["low"], weight) for _, estimate, weight in selected], low_quantile)
    base = _weighted_quantile([(estimate["base"], weight) for _, estimate, weight in selected], base_quantile)
    high = _weighted_quantile([(estimate["high"], weight) for _, estimate, weight in selected], high_quantile)
    low = min(low, base)
    high = max(high, base)
    total_weight = sum((weight for _, _, weight in selected), Decimal(0))
    confidence_score = sum(
        (Decimal(str(result["confidence"]["score"])) * weight for result, _, weight in selected),
        Decimal(0),
    ) / total_weight

    base_output["status"] = "estimate_ready"
    base_output["estimate"] = {
        "currency": str(record["currency"]).upper(),
        "year": record["year"],
        "low": _number(low),
        "base": _number(base),
        "high": _number(high),
        "confidence": {
            "score": _number(confidence_score),
            "label": _confidence_label(confidence_score, config),
        },
    }
    base_output["consensus"] = {
        "aggregation": consensus_config["aggregation"],
        "selectedEstimateIds": [item[0]["estimateId"] for item in selected],
        "independentEvidenceGroups": len(selected),
        "standaloneDirectValueUsed": standalone_used,
        "alternativeMethodsWereSummed": False,
        "quantiles": {
            "low": float(low_quantile),
            "base": float(base_quantile),
            "high": float(high_quantile),
        },
    }

    sanity_checks: list[dict[str, Any]] = []
    for result, estimate in sanity_internal:
        ratio = estimate["base"] / base
        check = {
            "estimateId": result["estimateId"],
            "methodId": result["methodId"],
            "estimate": result["estimate"],
            "ratioToConsensusBase": _number(ratio),
            "consensusBaseFallsInsideCheckRange": estimate["low"] <= base <= estimate["high"],
            "includedInConsensus": False,
        }
        result["comparisonToConsensus"] = {
            "ratioToConsensusBase": _number(ratio),
            "consensusBaseFallsInsideCheckRange": check["consensusBaseFallsInsideCheckRange"],
        }
        sanity_checks.append(check)
    base_output["sanityChecks"] = sanity_checks
    return base_output


def estimate_file(
    record_path: Path | str,
    config_path: Path | str = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    """Load a JSON input record and return its estimation output."""

    with Path(record_path).open("r", encoding="utf-8") as handle:
        record = json.load(handle)
    return estimate_market(record, load_config(config_path))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="JSON country-year input record")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"model configuration (default: {DEFAULT_CONFIG_PATH})",
    )
    args = parser.parse_args(argv)
    output = estimate_file(args.record, args.config)
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
