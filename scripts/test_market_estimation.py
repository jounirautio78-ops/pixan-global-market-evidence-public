#!/usr/bin/env python3
"""Deterministic synthetic tests for market_estimation.py.

The Canada and Germany records below are calculation fixtures only. Their
numbers and sources are deliberately labelled synthetic and must never be
interpreted as market evidence for either country.
"""

from __future__ import annotations

import unittest

try:
    from scripts.market_estimation import estimate_market, load_config
except ModuleNotFoundError:  # Allows direct execution as scripts/test_market_estimation.py.
    from market_estimation import estimate_market, load_config


def synthetic_source(source_id: str, metric: str) -> dict[str, str]:
    return {
        "sourceId": source_id,
        "title": f"Synthetic fixture for {metric}",
        "publisher": "Unit test only",
        "period": "synthetic-year",
        "metric": metric,
        "url": f"urn:synthetic:{source_id.lower()}",
        "limitations": "Synthetic arithmetic fixture; not country data or a public source.",
    }


def base_record(country_iso2: str, currency: str, source_ids: list[tuple[str, str]]) -> dict:
    return {
        "countryIso2": country_iso2,
        "year": 2025,
        "currency": currency,
        "scope": {
            "geography": "national",
            "includedProducts": ["synthetic_vaping_products"],
            "channel": "legal_retail",
            "valueBasis": "consumer_spend_including_indirect_tax",
        },
        "sources": [synthetic_source(source_id, metric) for source_id, metric in source_ids],
        "methods": [],
        "limitations": ["All values in this record are synthetic unit-test fixtures."],
    }


def canada_synthetic_record() -> dict:
    record = base_record(
        "CA",
        "CAD",
        [
            ("SYN-CA-VOLUME", "synthetic taxable volume"),
            ("SYN-CA-PRICE", "synthetic retail price"),
            ("SYN-CA-USERS", "synthetic active users"),
            ("SYN-CA-SPEND", "synthetic annual spend"),
            ("SYN-GLOBAL", "synthetic global benchmark"),
        ],
    )
    record["methods"] = [
        {
            "estimateId": "CA-SYN-VOLUME-PRICE",
            "methodId": "taxable_volume_price_basket",
            "evidenceGroup": "ca-synthetic-tax-volume",
            "confidence": "medium",
            "sourceIds": ["SYN-CA-VOLUME", "SYN-CA-PRICE"],
            "inputs": {
                "taxableVolume": 100,
                "retailPricePerUnit": {"low": 9, "base": 10, "high": 11},
                "scopeAdjustmentFactor": 1,
                "unit": "synthetic-unit",
            },
        },
        {
            "estimateId": "CA-SYN-USERS-SPEND",
            "methodId": "active_users_annual_spend",
            "evidenceGroup": "ca-synthetic-user-survey",
            "confidence": "medium",
            "sourceIds": ["SYN-CA-USERS", "SYN-CA-SPEND"],
            "inputs": {
                "activeUsers": 10,
                "annualSpendPerUser": {"low": 90, "base": 100, "high": 110},
                "scopeAdjustmentFactor": 1,
            },
        },
        {
            "estimateId": "CA-SYN-GLOBAL-CHECK",
            "methodId": "external_global_sanity_check",
            "evidenceGroup": "synthetic-global-vendor-benchmark",
            "confidence": "low",
            "sourceIds": ["SYN-GLOBAL"],
            "inputs": {
                "benchmarkMarketValue": 10000,
                "targetCountryShare": 0.1,
            },
        },
    ]
    return record


def germany_synthetic_record() -> dict:
    record = base_record(
        "DE",
        "EUR",
        [
            ("SYN-DE-EXCISE", "synthetic realised excise"),
            ("SYN-DE-RATE-PRICE", "synthetic excise rate and retail price"),
            ("SYN-DE-IMPORT", "synthetic import value"),
            ("SYN-DE-PRODUCTION-EXPORT", "synthetic production and export values"),
            ("SYN-COMP-CA", "synthetic Canada comparable"),
            ("SYN-COMP-FI", "synthetic Finland comparable"),
        ],
    )
    record["methods"] = [
        {
            "estimateId": "DE-SYN-EXCISE",
            "methodId": "excise_backsolve_price_basket",
            "evidenceGroup": "de-synthetic-excise-ledger",
            "confidence": "high",
            "sourceIds": ["SYN-DE-EXCISE", "SYN-DE-RATE-PRICE"],
            "inputs": {
                "realisedExciseRevenue": 200,
                "exciseRatePerUnit": 2,
                "retailPricePerUnit": 10,
                "scopeAdjustmentFactor": 1,
                "unit": "synthetic-unit",
            },
        },
        {
            "estimateId": "DE-SYN-CUSTOMS",
            "methodId": "customs_apparent_consumption_retail",
            "evidenceGroup": "de-synthetic-trade-flows",
            "confidence": "medium",
            "sourceIds": ["SYN-DE-IMPORT", "SYN-DE-PRODUCTION-EXPORT"],
            "inputs": {
                "importsValue": 500,
                "domesticProductionValue": 100,
                "exportsValue": 100,
                "retailMarkupFactor": 2,
                "scopeAdjustmentFactor": 1,
            },
        },
        {
            "estimateId": "DE-SYN-COMPARABLES",
            "methodId": "comparable_country_scaling",
            "evidenceGroup": "de-synthetic-comparable-countries",
            "confidence": "low",
            "sourceIds": ["SYN-COMP-CA", "SYN-COMP-FI"],
            "inputs": {
                "targetScaleBase": 100,
                "scaleMetric": "synthetic active-user scale",
                "comparables": [
                    {
                        "countryIso2": "CA",
                        "marketValue": 900,
                        "scaleBase": 90,
                        "comparabilityAdjustmentFactor": 1,
                        "marketDefinitionMatch": True,
                        "sourceIds": ["SYN-COMP-CA"],
                    },
                    {
                        "countryIso2": "FI",
                        "marketValue": 1200,
                        "scaleBase": 120,
                        "comparabilityAdjustmentFactor": 1,
                        "marketDefinitionMatch": True,
                        "sourceIds": ["SYN-COMP-FI"],
                    },
                ],
            },
        },
    ]
    return record


class MarketEstimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_config()

    def test_canada_fixture_uses_alternative_consensus_and_global_check(self) -> None:
        output = estimate_market(canada_synthetic_record(), self.config)
        self.assertEqual(output["status"], "estimate_ready")
        self.assertEqual(output["estimate"]["low"], 900)
        self.assertEqual(output["estimate"]["base"], 1000)
        self.assertEqual(output["estimate"]["high"], 1100)
        self.assertFalse(output["alternativeMethodsAreAdditive"])
        self.assertFalse(output["consensus"]["alternativeMethodsWereSummed"])
        self.assertEqual(output["consensus"]["selectedEstimateIds"], [
            "CA-SYN-VOLUME-PRICE",
            "CA-SYN-USERS-SPEND",
        ])
        self.assertEqual(len(output["sanityChecks"]), 1)
        self.assertEqual(output["sanityChecks"][0]["ratioToConsensusBase"], 1)
        self.assertFalse(output["sanityChecks"][0]["includedInConsensus"])

    def test_germany_fixture_exposes_excise_customs_and_comparables(self) -> None:
        output = estimate_market(germany_synthetic_record(), self.config)
        self.assertEqual(output["status"], "estimate_ready")
        self.assertEqual(output["estimate"]["base"], 1000)
        self.assertEqual(len(output["consensus"]["selectedEstimateIds"]), 3)
        comparable = next(
            item for item in output["methodResults"] if item["methodId"] == "comparable_country_scaling"
        )
        self.assertEqual(comparable["status"], "estimate_ready")
        self.assertEqual(comparable["estimate"]["base"], 1000)
        self.assertEqual([item["countryIso2"] for item in comparable["derivation"]["comparables"]], ["CA", "FI"])
        self.assertIn("formula", comparable)
        self.assertIn("inputs", comparable)
        self.assertEqual(comparable["confidence"]["tier"], "low")

    def test_high_confidence_direct_value_can_stand_alone(self) -> None:
        record = base_record("CA", "CAD", [("SYN-DIRECT", "synthetic direct market value")])
        record["methods"] = [
            {
                "estimateId": "CA-SYN-DIRECT",
                "methodId": "direct_reported_value",
                "evidenceGroup": "ca-synthetic-direct-report",
                "confidence": "high",
                "sourceIds": ["SYN-DIRECT"],
                "inputs": {"reportedMarketValue": 1234},
            }
        ]
        output = estimate_market(record, self.config)
        self.assertEqual(output["status"], "estimate_ready")
        self.assertEqual(output["estimate"], {
            "currency": "CAD",
            "year": 2025,
            "low": 1234,
            "base": 1234,
            "high": 1234,
            "confidence": {"score": 0.9, "label": "high"},
        })
        self.assertTrue(output["consensus"]["standaloneDirectValueUsed"])

    def test_one_non_direct_method_is_not_estimate_ready_and_has_no_range(self) -> None:
        record = canada_synthetic_record()
        record["methods"] = record["methods"][:1]
        output = estimate_market(record, self.config)
        self.assertEqual(output["status"], "not_estimate_ready")
        self.assertNotIn("estimate", output)
        self.assertEqual(output["reasonCodes"][0]["code"], "insufficient_independent_methods")
        self.assertIn("estimate", output["methodResults"][0])

    def test_same_evidence_group_contributes_only_one_candidate(self) -> None:
        record = canada_synthetic_record()
        record["methods"] = record["methods"][:2]
        record["methods"][1]["evidenceGroup"] = record["methods"][0]["evidenceGroup"]
        output = estimate_market(record, self.config)
        self.assertEqual(output["status"], "not_estimate_ready")
        included = [item for item in output["methodResults"] if item["includedInConsensus"]]
        excluded = [item for item in output["methodResults"] if not item["includedInConsensus"]]
        self.assertEqual(len(included), 1)
        self.assertEqual(excluded[0]["consensusExclusionReason"], "correlated_evidence_group_lower_weight")

    def test_same_source_cannot_be_disguised_as_two_independent_groups(self) -> None:
        record = canada_synthetic_record()
        record["methods"] = record["methods"][:2]
        record["methods"][1]["sourceIds"] = list(record["methods"][0]["sourceIds"])
        output = estimate_market(record, self.config)
        self.assertEqual(output["status"], "not_estimate_ready")
        self.assertEqual(output["consensus"]["independentEvidenceGroups"], 1)
        excluded = next(
            item for item in output["methodResults"] if not item["includedInConsensus"]
        )
        self.assertEqual(excluded["estimateId"], "CA-SYN-USERS-SPEND")
        self.assertEqual(excluded["consensusExclusionReason"], "overlapping_source_ids")
        self.assertEqual(excluded["overlappingSourceIds"], ["SYN-CA-PRICE", "SYN-CA-VOLUME"])
        self.assertEqual(excluded["overlapsSelectedEstimateIds"], ["CA-SYN-VOLUME-PRICE"])

    def test_excise_range_uses_inverse_rate_bounds(self) -> None:
        record = germany_synthetic_record()
        method = record["methods"][0]
        method["inputs"].update(
            {
                "realisedExciseRevenue": {"low": 180, "base": 200, "high": 220},
                "exciseRatePerUnit": {"low": 1.8, "base": 2, "high": 2.2},
                "retailPricePerUnit": {"low": 9, "base": 10, "high": 11},
            }
        )
        record["methods"] = [method]
        # A high-confidence non-direct method is intentionally insufficient for
        # the overall estimate, while its fully supported method result is visible.
        output = estimate_market(record, self.config)
        result = output["methodResults"][0]
        self.assertEqual(result["status"], "estimate_ready")
        self.assertAlmostEqual(result["estimate"]["low"], 180 / 2.2 * 9)
        self.assertEqual(result["estimate"]["base"], 1000)
        self.assertAlmostEqual(result["estimate"]["high"], 220 / 1.8 * 11)

    def test_customs_apparent_consumption_is_clamped_at_zero(self) -> None:
        record = germany_synthetic_record()
        method = record["methods"][1]
        method["inputs"].update(
            {
                "importsValue": {"low": 10, "base": 20, "high": 30},
                "domesticProductionValue": 0,
                "exportsValue": {"low": 40, "base": 40, "high": 40},
            }
        )
        record["methods"] = [method]
        result = estimate_market(record, self.config)["methodResults"][0]
        self.assertEqual(result["status"], "not_estimate_ready")
        self.assertEqual(result["reasonCodes"][0]["code"], "zero_estimate")
        self.assertNotIn("estimate", result)

    def test_usage_components_require_disjoint_revenue_scopes(self) -> None:
        record = base_record(
            "CA",
            "CAD",
            [("SYN-USERS", "synthetic users"), ("SYN-USAGE", "synthetic usage and prices")],
        )
        record["methods"] = [
            {
                "estimateId": "CA-SYN-USAGE",
                "methodId": "usage_units_price",
                "evidenceGroup": "ca-synthetic-usage",
                "confidence": "medium",
                "sourceIds": ["SYN-USERS", "SYN-USAGE"],
                "inputs": {
                    "activeUsers": 10,
                    "scopeAdjustmentFactor": 1,
                    "components": [
                        {
                            "componentId": "pods",
                            "revenueScopeId": "consumables",
                            "isDisjointRevenueScope": True,
                            "unit": "pod",
                            "userShare": 1,
                            "annualUnitsPerUser": 10,
                            "retailPricePerUnit": 5,
                        },
                        {
                            "componentId": "liquid-inside-pods",
                            "revenueScopeId": "consumables",
                            "isDisjointRevenueScope": True,
                            "unit": "ml",
                            "userShare": 1,
                            "annualUnitsPerUser": 20,
                            "retailPricePerUnit": 2,
                        },
                    ],
                },
            }
        ]
        result = estimate_market(record, self.config)["methodResults"][0]
        self.assertEqual(result["status"], "not_estimate_ready")
        self.assertEqual(result["reasonCodes"][0]["code"], "overlapping_component_scope")

    def test_usage_components_calculate_disjoint_product_revenue(self) -> None:
        record = base_record(
            "DE",
            "EUR",
            [("SYN-USERS", "synthetic users"), ("SYN-USAGE", "synthetic usage and prices")],
        )
        record["methods"] = [
            {
                "estimateId": "DE-SYN-USAGE",
                "methodId": "usage_units_price",
                "evidenceGroup": "de-synthetic-usage",
                "confidence": "medium",
                "sourceIds": ["SYN-USERS", "SYN-USAGE"],
                "inputs": {
                    "activeUsers": 10,
                    "scopeAdjustmentFactor": 1,
                    "components": [
                        {
                            "componentId": "consumables",
                            "revenueScopeId": "consumable-skus",
                            "isDisjointRevenueScope": True,
                            "unit": "synthetic-consumable",
                            "userShare": 1,
                            "annualUnitsPerUser": 10,
                            "retailPricePerUnit": 5,
                        },
                        {
                            "componentId": "devices",
                            "revenueScopeId": "device-skus",
                            "isDisjointRevenueScope": True,
                            "unit": "device",
                            "userShare": 0.5,
                            "annualUnitsPerUser": 2,
                            "retailPricePerUnit": 25,
                        },
                    ],
                },
            }
        ]
        result = estimate_market(record, self.config)["methodResults"][0]
        self.assertEqual(result["status"], "estimate_ready")
        self.assertEqual(result["estimate"]["base"], 750)
        self.assertEqual(result["derivation"]["combinedAnnualSpendPerActiveUser"]["base"], 75)

    def test_method_without_required_sources_has_no_estimate_range(self) -> None:
        record = canada_synthetic_record()
        record["methods"] = [record["methods"][0]]
        record["methods"][0]["sourceIds"] = ["SYN-CA-VOLUME"]
        output = estimate_market(record, self.config)
        result = output["methodResults"][0]
        self.assertEqual(result["status"], "not_estimate_ready")
        self.assertEqual(result["reasonCodes"][0]["code"], "insufficient_sources")
        self.assertNotIn("estimate", result)
        self.assertNotIn("estimate", output)

    def test_comparables_require_two_distinct_non_target_countries(self) -> None:
        record = germany_synthetic_record()
        method = record["methods"][2]
        method["inputs"]["comparables"] = method["inputs"]["comparables"][:1]
        record["methods"] = [method]
        result = estimate_market(record, self.config)["methodResults"][0]
        self.assertEqual(result["status"], "not_estimate_ready")
        self.assertEqual(result["reasonCodes"][0]["code"], "insufficient_comparables")

    def test_missing_record_header_returns_not_ready_without_methods(self) -> None:
        output = estimate_market({}, self.config)
        self.assertEqual(output["status"], "not_estimate_ready")
        self.assertNotIn("estimate", output)
        self.assertTrue(output["reasonCodes"])


if __name__ == "__main__":
    unittest.main()
