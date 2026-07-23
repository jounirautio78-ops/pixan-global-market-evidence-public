#!/usr/bin/env python3
"""Mutation tests for the v17 review-experience publication gates."""

from __future__ import annotations

import copy
import unittest

from validate_review_experience import (
    DATA,
    SITE,
    load_json,
    validate_review_data,
    validate_review_structure,
)


class ReviewExperienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.atlas = load_json(DATA / "atlas.json")
        cls.market = load_json(DATA / "market-values.json")
        cls.patent = load_json(DATA / "patent-history.json")
        cls.requests = load_json(DATA / "top20-data-request-routes.json")
        cls.review_html = (SITE / "review.html").read_text(encoding="utf-8")
        cls.index_html = (SITE / "index.html").read_text(encoding="utf-8")
        cls.review_js = (SITE / "assets" / "review.js").read_text(encoding="utf-8")
        cls.i18n_js = (SITE / "assets" / "i18n.js").read_text(encoding="utf-8")

    def assert_data_rejected(
        self,
        *,
        atlas: dict | None = None,
        market: dict | None = None,
        patent: dict | None = None,
        requests: dict | None = None,
        needle: str,
    ) -> None:
        errors = validate_review_data(
            atlas or self.atlas,
            market or self.market,
            patent or self.patent,
            requests or self.requests,
        )
        self.assertTrue(any(needle in error for error in errors), errors)

    def test_reviewed_baseline_passes(self) -> None:
        self.assertEqual(
            validate_review_data(self.atlas, self.market, self.patent, self.requests),
            [],
        )
        self.assertEqual(
            validate_review_structure(self.review_html, self.index_html, self.review_js, self.i18n_js),
            [],
        )

    def test_rejects_relabelled_consumer_retail_value(self) -> None:
        market = copy.deepcopy(self.market)
        official = next(
            item for item in market["observations"]
            if str(item["evidenceStatus"]).startswith("official_")
        )
        official["metric"] = "consumer_retail_market_value"
        self.assert_data_rejected(
            market=market,
            needle="must retain one official incomplete retail lower bound",
        )

    def test_rejects_changed_germany_output(self) -> None:
        market = copy.deepcopy(self.market)
        model = next(
            item for item in market["models"]
            if item["modelId"] == "DE-2025-LIQUID-RETAIL-EQUIVALENT-RANGE"
        )
        model["central"] += 1
        self.assert_data_rejected(
            market=market,
            needle="Germany central output does not reproduce exactly",
        )

    def test_rejects_future_retrieval_date(self) -> None:
        market = copy.deepcopy(self.market)
        market["sources"][0]["retrievedAt"] = "2026-07-25"
        self.assert_data_rejected(
            market=market,
            needle="retrievedAt cannot be later than market asOf",
        )

    def test_rejects_unearned_donor(self) -> None:
        market = copy.deepcopy(self.market)
        market["meta"]["modelReadiness"]["comparableFullYearMarketValueDonors"] = 1
        self.assert_data_rejected(
            market=market,
            needle="donor gate must remain blocked at 0/3",
        )

    def test_rejects_declared_donor_candidate_acceptance(self) -> None:
        market = copy.deepcopy(self.market)
        market["donorCandidates"][0]["decision"] = "accepted"
        self.assert_data_rejected(
            market=market,
            needle="donor candidates must all remain not accepted",
        )

    def test_rejects_process_response_as_public_reference(self) -> None:
        requests = copy.deepcopy(self.requests)
        germany = next(item for item in requests["routes"] if item["countryIso2"] == "DE")
        germany["dispatch"]["publicAuthorityReference"] = "private-ticket"
        self.assert_data_rejected(
            requests=requests,
            needle="process response must not publish a private authority reference",
        )

    def test_rejects_missing_cockpit_hook(self) -> None:
        mutated = self.review_html.replace('id="decision-cockpit"', 'id="removed-cockpit"', 1)
        errors = validate_review_structure(mutated, self.index_html, self.review_js, self.i18n_js)
        self.assertTrue(any("required v17 hooks" in error for error in errors), errors)

    def test_rejects_missing_donor_hook(self) -> None:
        mutated = self.index_html.replace('id="market-donor-ledger"', 'id="removed-donor-ledger"', 1)
        errors = validate_review_structure(self.review_html, mutated, self.review_js, self.i18n_js)
        self.assertTrue(any("required v17 donor hooks" in error for error in errors), errors)

    def test_rejects_wall_clock_freshness(self) -> None:
        mutated = self.review_js.replace(
            "function renderReviewSourceFreshness(market, atlas) {",
            "function renderReviewSourceFreshness(market, atlas) { const unsafeNow = Date.now();",
            1,
        )
        errors = validate_review_structure(self.review_html, self.index_html, mutated, self.i18n_js)
        self.assertTrue(any("Source freshness must be deterministic" in error for error in errors), errors)

    def test_rejects_missing_view_translation(self) -> None:
        mutated = self.i18n_js.replace("Research Operations", "Removed operations label")
        errors = validate_review_structure(
            self.review_html,
            self.index_html,
            self.review_js,
            mutated,
        )
        self.assertTrue(any("Finnish/English pair" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
