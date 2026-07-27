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
    FX_PATH,
    JSON_OUTPUT_PATH,
    OBSERVATIONS_PATH,
    PUBLIC_SCHEMA_PATH,
    SOURCE_SCHEMA_PATH,
    eur_equivalent,
    read_json,
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
