#!/usr/bin/env python3
"""Regression tests for the UN195 global base layer."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_global_base import (  # noqa: E402
    CONFIG_PATH,
    CSV_OUTPUT_PATH,
    DONOR_COCKPIT_PATH,
    FX_PATH,
    JSON_OUTPUT_PATH,
    METHOD_ROUTE_CONFIG_PATH,
    OBSERVATIONS_PATH,
    OUTPUT_SCHEMA_VERSION,
    PUBLIC_SCHEMA_PATH,
    SOURCE_SCHEMA_PATH,
    THIRD_DONOR_SCREEN_PATH,
    TOP20_ROUTES_PATH,
    build_layer,
    eur_equivalent,
    read_json,
    validate_method_route_sources,
    validate_source_contract,
)
from refresh_global_base import latest_non_null_by_country  # noqa: E402
from validate_global_base import validate_files  # noqa: E402


class LatestNonNullTests(unittest.TestCase):
    def test_selects_latest_non_null_and_preserves_real_source_period(self) -> None:
        rows = [
            {"country": {"id": "FI"}, "date": "2024", "value": None},
            {"country": {"id": "FI"}, "date": "2023", "value": 5},
            {"country": {"id": "FI"}, "date": "2022", "value": 4},
            {"country": {"id": "SE"}, "date": "2024", "value": 0},
            {"country": {"id": "ZZ"}, "date": "2024", "value": 999},
        ]
        selected = latest_non_null_by_country(rows, {"FI", "SE"})
        self.assertEqual(selected["FI"]["date"], "2023")
        self.assertEqual(selected["FI"]["value"], 5)
        self.assertEqual(selected["SE"]["date"], "2024")
        self.assertEqual(selected["SE"]["value"], 0)
        self.assertNotIn("ZZ", selected)


class SourceFailClosedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = read_json(CONFIG_PATH)
        cls.snapshot = read_json(OBSERVATIONS_PATH)

    def test_actual_snapshot_contract(self) -> None:
        indexed = validate_source_contract(self.config, self.snapshot)
        self.assertEqual(len(indexed), 975)

    def test_rejects_zero_as_who_missing_substitute(self) -> None:
        mutated = copy.deepcopy(self.snapshot)
        record = next(
            item
            for item in mutated["observations"]
            if item["measureId"] == "who_adult_current_ecig_prevalence"
        )
        record["value"] = 0
        with self.assertRaisesRegex(ValueError, "queued, missing and null"):
            validate_source_contract(self.config, mutated)

    def test_rejects_any_retail_sales_eligibility(self) -> None:
        mutated = copy.deepcopy(self.snapshot)
        mutated["observations"][0]["retailSalesEligible"] = True
        with self.assertRaisesRegex(ValueError, "must not be retail-sales eligible"):
            validate_source_contract(self.config, mutated)

    def test_rejects_latest_value_relabelled_outside_window(self) -> None:
        mutated = copy.deepcopy(self.snapshot)
        record = next(
            item
            for item in mutated["observations"]
            if item["dataStatus"] == "observed"
        )
        record["sourcePeriod"] = 2025
        with self.assertRaisesRegex(ValueError, "sourcePeriod is invalid"):
            validate_source_contract(self.config, mutated)


class EurConversionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gdp = {
            "sourcePeriod": 2023,
            "value": 10812.68627451,
            "dataStatus": "observed",
        }

    def test_missing_same_year_rate_is_not_computed(self) -> None:
        result = eur_equivalent(self.gdp, {})
        self.assertEqual(result["status"], "not_computed")
        self.assertIsNone(result["value"])
        self.assertEqual(result["reason"], "same_year_ecb_rate_missing")

    def test_same_year_fixture_rate_computes_eur(self) -> None:
        rates = {
            2023: {
                "rateId": "TEST-USD-2023",
                "year": 2023,
                "currencyUnitsPerEur": 1.081268627451,
            }
        }
        result = eur_equivalent(self.gdp, rates)
        self.assertEqual(result["status"], "computed")
        self.assertEqual(result["rateYear"], 2023)
        self.assertEqual(result["value"], 10000.00)

    def test_never_uses_adjacent_year_rate(self) -> None:
        rates = {
            2024: {
                "rateId": "TEST-USD-2024",
                "year": 2024,
                "currencyUnitsPerEur": 1.08,
            }
        }
        result = eur_equivalent(self.gdp, rates)
        self.assertEqual(result["status"], "not_computed")
        self.assertIsNone(result["rateId"])


class MethodRouteControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = read_json(CONFIG_PATH)
        cls.snapshot = read_json(OBSERVATIONS_PATH)
        cls.fx = read_json(FX_PATH)
        cls.method_routes = read_json(METHOD_ROUTE_CONFIG_PATH)
        cls.top20 = read_json(TOP20_ROUTES_PATH)
        cls.third_donor = read_json(THIRD_DONOR_SCREEN_PATH)
        cls.donor_cockpit = read_json(DONOR_COCKPIT_PATH)

    def build(self) -> dict:
        return build_layer(
            self.config,
            self.snapshot,
            self.fx,
            self.method_routes,
            self.top20,
            self.third_donor,
            self.donor_cockpit,
        )

    def test_exact_195_country_assignment_contract(self) -> None:
        layer = self.build()
        self.assertEqual(layer["schemaVersion"], OUTPUT_SCHEMA_VERSION)
        self.assertEqual(
            layer["methodRouteControl"]["summary"],
            {
                "countryCount": 195,
                "reviewedMethodPlanCount": 28,
                "reviewedSourceLeadCount": 0,
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
            },
        )

    def test_all_country_routes_remain_fail_closed(self) -> None:
        layer = self.build()
        routes = {
            country["iso2"]: country["methodRoute"]
            for country in layer["countries"]
        }
        self.assertTrue(
            all(route["eligibleForGlobalRollup"] is False for route in routes.values())
        )
        self.assertTrue(all(route["donorAccepted"] is False for route in routes.values()))
        self.assertEqual(
            routes["CA"]["retailValueStatus"],
            "official_point_estimate_quality_limited",
        )
        self.assertEqual(
            routes["NZ"]["retailValueStatus"],
            "observed_partial_channel_only",
        )
        self.assertTrue(
            all(
                route["retailValueStatus"] == "not_computed"
                for iso2, route in routes.items()
                if iso2 not in {"CA", "NZ"}
            )
        )

    def test_regional_tpd_pattern_is_not_a_national_value_claim(self) -> None:
        layer = self.build()
        cyprus = next(country for country in layer["countries"] if country["iso2"] == "CY")
        route = cyprus["methodRoute"]
        self.assertEqual(route["assignmentClass"], "regional_tpd_pattern_only")
        self.assertEqual(
            route["primaryMethodId"],
            "eu_tpd_annual_reporting_pattern",
        )
        self.assertEqual(route["retailValueStatus"], "not_computed")
        self.assertEqual(route["donorAssessmentState"], "not_assessed")

    def test_five_country_sprint_has_reviewed_sent_fail_closed_routes(self) -> None:
        layer = self.build()
        routes = {
            country["iso2"]: country["methodRoute"]
            for country in layer["countries"]
        }
        expected_primary = {
            "AT": "statutory_annual_sales_reporting",
            "BE": "statutory_annual_sales_reporting",
            "CH": "excise_to_volume_reconstruction",
            "LU": "excise_to_volume_reconstruction",
            "NO": "regulated_supply_plus_enforcement",
        }
        for iso2, primary_method in expected_primary.items():
            route = routes[iso2]
            self.assertEqual(route["assignmentClass"], "reviewed_method_plan")
            self.assertEqual(route["primaryMethodId"], primary_method)
            self.assertEqual(route["requestState"], "sent")
            self.assertEqual(route["retailValueStatus"], "not_computed")
            self.assertFalse(route["eligibleForGlobalRollup"])
            self.assertFalse(route["donorAccepted"])
            self.assertIn("FIVE_COUNTRY_SPRINT", route["provenanceBasisIds"])

    def test_rejects_method_that_claims_standalone_retail_value(self) -> None:
        mutated = copy.deepcopy(self.method_routes)
        mutated["methods"][0]["canEstablishRetailValueAlone"] = True
        with self.assertRaisesRegex(ValueError, "must not establish retail value alone"):
            validate_method_route_sources(
                mutated,
                self.top20,
                self.third_donor,
                self.donor_cockpit,
            )

    def test_rejects_assignment_membership_drift(self) -> None:
        mutated = copy.deepcopy(self.method_routes)
        mutated["reviewedSourceLeads"] = ["CA"]
        with self.assertRaisesRegex(ValueError, "source-lead country set differs"):
            validate_method_route_sources(
                mutated,
                self.top20,
                self.third_donor,
                self.donor_cockpit,
            )

    def test_rejects_accepted_donor_claim(self) -> None:
        mutated = copy.deepcopy(self.donor_cockpit)
        candidate = next(
            item
            for item in mutated["candidates"]
            if item.get("candidateType") == "country_year"
        )
        candidate["declaredDecision"] = "accepted"
        with self.assertRaisesRegex(ValueError, "no donor country may be accepted"):
            validate_method_route_sources(
                self.method_routes,
                self.top20,
                self.third_donor,
                mutated,
            )


class GeneratedArtifactTests(unittest.TestCase):
    def test_full_generated_artifact_validation(self) -> None:
        layer = validate_files(
            config_path=CONFIG_PATH,
            observations_path=OBSERVATIONS_PATH,
            fx_path=FX_PATH,
            json_path=JSON_OUTPUT_PATH,
            csv_path=CSV_OUTPUT_PATH,
            source_schema_path=SOURCE_SCHEMA_PATH,
            public_schema_path=PUBLIC_SCHEMA_PATH,
        )
        self.assertEqual(len(layer["countries"]), 195)
        self.assertEqual(layer["schemaVersion"], "1.1")
        self.assertEqual(
            layer["methodRouteControl"]["summary"]["reviewedMethodPlanCount"],
            28,
        )
        self.assertEqual(layer["globalRetailSales"]["status"], "blocked")
        self.assertIsNone(layer["globalRetailSales"]["value"])

    def test_generated_json_contains_no_numeric_queued_routes(self) -> None:
        layer = json.loads(JSON_OUTPUT_PATH.read_text(encoding="utf-8"))
        for country in layer["countries"]:
            self.assertIsNone(
                country["routes"]["whoAdultCurrentEcigPrevalence"]["value"]
            )
            self.assertIsNone(country["routes"]["unComtradeVapingTrade"]["value"])

    def test_schema_id_points_to_the_current_publication(self) -> None:
        schema = json.loads(SOURCE_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            schema["$id"],
            "https://jounirautio78-ops.github.io/"
            "pixan-global-market-evidence-public/schemas/global-base-layer.schema.json",
        )
        self.assertEqual(schema["properties"]["schemaVersion"]["const"], "1.1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
