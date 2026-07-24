#!/usr/bin/env python3
"""Mutation tests for the fail-closed ECB EUR-equivalent layer."""

from __future__ import annotations

import copy
import unittest
from decimal import Decimal

from validate_fx_rates import (
    APP,
    INDEX,
    MARKET_SOURCE,
    PUBLIC_FX,
    SCENARIO_SOURCE,
    SOURCE_FX,
    assess_conversion,
    load_json,
    rate_index,
    validate_documents,
)


class FxRateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = load_json(SOURCE_FX)
        cls.public = load_json(PUBLIC_FX)
        cls.market = load_json(MARKET_SOURCE)
        cls.scenarios = load_json(SCENARIO_SOURCE)
        cls.app_js = APP.read_text(encoding="utf-8")
        cls.index_html = INDEX.read_text(encoding="utf-8")

    def validate(
        self,
        *,
        source: dict | None = None,
        public: dict | None = None,
        market: dict | None = None,
        scenarios: dict | None = None,
        app_js: str | None = None,
        index_html: str | None = None,
    ) -> list[str]:
        chosen_source = source or self.source
        return validate_documents(
            chosen_source,
            public or (chosen_source if source is not None else self.public),
            market or self.market,
            scenarios or self.scenarios,
            app_js or self.app_js,
            index_html or self.index_html,
        )

    def assert_rejected(self, *, needle: str, **changes: object) -> None:
        errors = self.validate(**changes)
        self.assertTrue(any(needle in error for error in errors), errors)

    def test_reviewed_baseline_passes(self) -> None:
        self.assertEqual(self.validate(), [])

    def test_rejects_changed_ecb_observation(self) -> None:
        source = copy.deepcopy(self.source)
        source["rates"][0]["currencyUnitsPerEur"] += 0.01
        self.assert_rejected(
            source=source,
            needle="differs from the reviewed ECB OBS_VALUE",
        )

    def test_rejects_missing_compatible_rate(self) -> None:
        source = copy.deepcopy(self.source)
        source["rates"] = [
            item
            for item in source["rates"]
            if not (item["currency"] == "NZD" and item["year"] == 2024)
        ]
        errors = self.validate(source=source)
        self.assertTrue(
            any("currency-year coverage differs" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("has no compatible reviewed ECB annual-average EUR conversion" in error for error in errors),
            errors,
        )

    def test_rejects_non_ecb_rate_url(self) -> None:
        source = copy.deepcopy(self.source)
        source["rates"][0]["sourceUrl"] = "https://example.com/rate.csv"
        self.assert_rejected(
            source=source,
            needle="exact official ECB API observation",
        )

    def test_physical_volume_is_ineligible(self) -> None:
        result = assess_conversion(
            {
                "value": 100,
                "currency": "CAD",
                "unit": "litre",
                "year": 2024,
                "period": "calendar_year",
            },
            rate_index(self.source),
            {"calendar_year", "calendar_year_estimate"},
        )
        self.assertEqual(result["status"], "ineligible")

    def test_unit_price_is_ineligible(self) -> None:
        result = assess_conversion(
            {
                "value": 1.09,
                "currency": "EUR",
                "unit": "EUR_per_ml",
                "year": 2026,
                "period": "current_listing",
            },
            rate_index(self.source),
            {"calendar_year", "calendar_year_estimate"},
        )
        self.assertEqual(result["status"], "ineligible")

    def test_missing_period_is_not_computed(self) -> None:
        result = assess_conversion(
            {
                "value": 100,
                "currency": "CAD",
                "unit": "CAD",
                "year": 2024,
                "period": "snapshot",
            },
            rate_index(self.source),
            {"calendar_year", "calendar_year_estimate"},
        )
        self.assertEqual(result["status"], "not_computed")

    def test_nz_scenario_uses_full_ecb_rate(self) -> None:
        nz = self.scenarios["countryYearScenarios"][0]
        result = assess_conversion(
            {
                "value": nz["inputs"]["base"]["value"],
                "currency": nz["currency"],
                "unit": nz["currency"],
                "year": nz["year"],
                "period": "calendar_year",
            },
            rate_index(self.source),
            {"calendar_year", "calendar_year_estimate"},
        )
        self.assertEqual(result["status"], "computed")
        self.assertEqual(
            result["eurValue"].quantize(Decimal("0.01")),
            Decimal("358945280.35"),
        )

    def test_rejects_missing_method_hook(self) -> None:
        index_html = self.index_html.replace('id="market-fx-method"', 'id="removed-fx-method"', 1)
        self.assert_rejected(
            index_html=index_html,
            needle="Missing EUR-equivalent method disclosure hook",
        )

    def test_rejects_removed_fail_closed_app_token(self) -> None:
        app_js = self.app_js.replace("assessEurEquivalent", "removedEurEquivalent")
        self.assert_rejected(
            app_js=app_js,
            needle="Missing fail-closed EUR-equivalent app control",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
