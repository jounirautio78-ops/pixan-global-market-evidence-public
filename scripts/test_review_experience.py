#!/usr/bin/env python3
"""Mutation tests for the v27 review-experience publication gates."""

from __future__ import annotations

import copy
import unittest

from validate_review_experience import (
    DATA,
    SITE,
    load_json,
    validate_review_data,
    validate_review_structure,
    validate_third_donor_screen,
)


class ReviewExperienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.atlas = load_json(DATA / "atlas.json")
        cls.market = load_json(DATA / "market-values.json")
        cls.fx = load_json(DATA / "fx-rates.json")
        cls.patent = load_json(DATA / "patent-history.json")
        cls.requests = load_json(DATA / "top20-data-request-routes.json")
        cls.third_donor = load_json(DATA / "third-donor-screen.json")
        cls.review_html = (SITE / "review.html").read_text(encoding="utf-8")
        cls.index_html = (SITE / "index.html").read_text(encoding="utf-8")
        cls.review_js = (SITE / "assets" / "review.js").read_text(encoding="utf-8")
        cls.i18n_js = (SITE / "assets" / "i18n.js").read_text(encoding="utf-8")
        cls.request_program_js = (SITE / "assets" / "request-program.js").read_text(encoding="utf-8")
        cls.app_js = (SITE / "assets" / "app.js").read_text(encoding="utf-8")
        cls.independent_controls_js = (
            SITE / "assets" / "independent-controls.js"
        ).read_text(encoding="utf-8")

    def assert_data_rejected(
        self,
        *,
        atlas: dict | None = None,
        market: dict | None = None,
        patent: dict | None = None,
        requests: dict | None = None,
        fx: dict | None = None,
        needle: str,
    ) -> None:
        errors = validate_review_data(
            atlas or self.atlas,
            market or self.market,
            patent or self.patent,
            requests or self.requests,
            fx if fx is not None else self.fx,
        )
        self.assertTrue(any(needle in error for error in errors), errors)

    def test_reviewed_baseline_passes(self) -> None:
        self.assertEqual(
            validate_review_data(self.atlas, self.market, self.patent, self.requests, self.fx),
            [],
        )
        self.assertEqual(validate_third_donor_screen(self.third_donor), [])
        self.assertEqual(
            validate_review_structure(
                self.review_html,
                self.index_html,
                self.review_js,
                self.i18n_js,
                self.request_program_js,
                self.app_js,
                self.independent_controls_js,
            ),
            [],
        )

    def test_rejects_atlas_count_substituted_for_missing_global_base(self) -> None:
        mutated = self.app_js.replace(
            'state.globalBase ? `${state.globalBase.countries.length} / 195` : "— / 195"',
            '`${list.length} / 195`',
            1,
        )
        errors = validate_review_structure(
            self.review_html,
            self.index_html,
            self.review_js,
            self.i18n_js,
            self.request_program_js,
            mutated,
        )
        self.assertTrue(any("must fail closed" in error for error in errors), errors)

    def test_rejects_missing_sweden_structure_card(self) -> None:
        mutated = self.review_html.replace(
            'id="sweden-structure-card"',
            'id="removed-sweden-structure-card"',
            1,
        )
        errors = validate_review_structure(
            mutated,
            self.index_html,
            self.review_js,
            self.i18n_js,
            self.request_program_js,
            self.app_js,
        )
        self.assertTrue(any("required v18 hooks" in error for error in errors), errors)

    def test_rejects_sweden_structure_without_sales_boundary(self) -> None:
        mutated = self.request_program_js.replace(
            "does not measure sales, market value, devices sold, e-liquid millilitres",
            "contains market information",
            1,
        )
        errors = validate_review_structure(
            self.review_html,
            self.index_html,
            self.review_js,
            self.i18n_js,
            mutated,
            self.app_js,
        )
        self.assertTrue(any("Sweden hook" in error for error in errors), errors)

    def test_rejects_relabelled_consumer_retail_value(self) -> None:
        market = copy.deepcopy(self.market)
        official = next(
            item for item in market["observations"]
            if str(item["evidenceStatus"]).startswith("official_")
        )
        official["metric"] = "consumer_retail_market_value"
        self.assert_data_rejected(
            market=market,
            needle="must retain seven Canada retail estimates",
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
        market["sources"][0]["retrievedAt"] = "2026-07-28"
        self.assert_data_rejected(
            market=market,
            needle="retrievedAt cannot be later than market asOf",
        )

    def test_rejects_changed_market_source_set(self) -> None:
        market = copy.deepcopy(self.market)
        market["sources"][0]["sourceId"] = "REMOVED-REVIEWED-SOURCE"
        self.assert_data_rejected(
            market=market,
            needle="exact 24-source set",
        )

    def test_rejects_changed_poland_tax_bridge_value(self) -> None:
        market = copy.deepcopy(self.market)
        observation = next(
            item for item in market["observations"]
            if item["observationId"]
            == "PL-2025-VAPING-DEVICE-EXCISE-BACKSOLVED-UNITS"
        )
        observation["value"] += 1
        self.assert_data_rejected(
            market=market,
            needle="Poland reconstruction observation",
        )

    def test_rejects_changed_poland_tax_bridge_sources(self) -> None:
        market = copy.deepcopy(self.market)
        observation = next(
            item for item in market["observations"]
            if item["observationId"]
            == "PL-2025-VAPING-COMPONENT-SETS-EXCISE-BACKSOLVED-UNITS"
        )
        observation["sourceIds"].pop()
        self.assert_data_rejected(
            market=market,
            needle="Poland reconstruction observation",
        )

    def test_rejects_changed_nz_observation_sources(self) -> None:
        market = copy.deepcopy(self.market)
        observation = next(
            item for item in market["observations"]
            if item["observationId"] == "NZ-2024-IDENTIFIED-VAPING-PRODUCT-SALES-RAW-SUM"
        )
        observation["sourceIds"].pop()
        self.assert_data_rejected(
            market=market,
            needle="identified-vaping observation differs",
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

    def test_rejects_changed_nz_donor_closure_status(self) -> None:
        market = copy.deepcopy(self.market)
        candidate = next(
            item for item in market["donorCandidates"]
            if item["candidateId"] == "NZ-2024-IDENTIFIED-VAPING-RETAIL-SUBTOTAL"
        )
        candidate["passedCriteria"].remove("D4")
        candidate["openCriteria"].append("D4")
        self.assert_data_rejected(
            market=market,
            needle="New Zealand donor candidate differs from the reviewed 7/10 closure decision",
        )

    def test_rejects_process_response_as_public_reference(self) -> None:
        requests = copy.deepcopy(self.requests)
        germany = next(item for item in requests["routes"] if item["countryIso2"] == "DE")
        germany["dispatch"]["publicAuthorityReference"] = "private-ticket"
        self.assert_data_rejected(
            requests=requests,
            needle="authority response must not publish a private reference",
        )

    def test_rejects_legacy_request_programme_schema(self) -> None:
        requests = copy.deepcopy(self.requests)
        requests["schemaVersion"] = 2
        self.assert_data_rejected(
            requests=requests,
            needle="schema version 3",
        )

    def test_rejects_missing_global_evidence_layer(self) -> None:
        requests = copy.deepcopy(self.requests)
        requests["evidenceStack"]["layers"].pop()
        self.assert_data_rejected(
            requests=requests,
            needle="six-layer 195-state evidence stack",
        )

    def test_rejects_supplement_counted_as_another_country(self) -> None:
        requests = copy.deepcopy(self.requests)
        requests["supplementaryRequests"][1]["countsTowardCountryQueue"] = True
        self.assert_data_rejected(
            requests=requests,
            needle="exact non-counting German and Polish supplement contract",
        )

    def test_rejects_missing_polish_supplement(self) -> None:
        requests = copy.deepcopy(self.requests)
        requests["supplementaryRequests"] = [
            item
            for item in requests["supplementaryRequests"]
            if item["countryIso2"] != "PL"
        ]
        self.assert_data_rejected(
            requests=requests,
            needle="two non-counting German and Polish supplements",
        )

    def test_rejects_false_italy_availability_response_state(self) -> None:
        requests = copy.deepcopy(self.requests)
        italy = next(item for item in requests["routes"] if item["countryIso2"] == "IT")
        italy["dispatch"]["responseState"] = "not_publicly_recorded"
        self.assert_data_rejected(
            requests=requests,
            needle="Availability-response baseline must remain Denmark and Italy",
        )

    def test_rejects_missing_cockpit_hook(self) -> None:
        mutated = self.review_html.replace('id="decision-cockpit"', 'id="removed-cockpit"', 1)
        errors = validate_review_structure(mutated, self.index_html, self.review_js, self.i18n_js)
        self.assertTrue(any("required v18 hooks" in error for error in errors), errors)

    def test_rejects_missing_donor_hook(self) -> None:
        mutated = self.index_html.replace('id="market-donor-ledger"', 'id="removed-donor-ledger"', 1)
        errors = validate_review_structure(self.review_html, mutated, self.review_js, self.i18n_js)
        self.assertTrue(any("required v18 donor hooks" in error for error in errors), errors)

    def test_rejects_missing_third_donor_hook(self) -> None:
        mutated = self.review_html.replace('id="third-donor-programme"', 'id="removed-third-donor-programme"', 1)
        errors = validate_review_structure(
            mutated,
            self.index_html,
            self.review_js,
            self.i18n_js,
            self.request_program_js,
            self.app_js,
        )
        self.assertTrue(any("required v18 hooks" in error for error in errors), errors)

    def test_rejects_missing_independent_control_surface(self) -> None:
        mutated = self.review_html.replace(
            "data-us-benchmark-control",
            "data-removed-us-benchmark-control",
            1,
        )
        errors = validate_review_structure(
            mutated,
            self.index_html,
            self.review_js,
            self.i18n_js,
            self.request_program_js,
            self.app_js,
            self.independent_controls_js,
        )
        self.assertTrue(
            any("data-us-benchmark-control" in error for error in errors),
            errors,
        )

    def test_rejects_missing_independent_control_fetch(self) -> None:
        mutated = self.independent_controls_js.replace(
            'fetch("data/us-independent-benchmark-control.json"',
            'fetch("data/removed-us-independent-benchmark-control.json"',
            1,
        )
        errors = validate_review_structure(
            self.review_html,
            self.index_html,
            self.review_js,
            self.i18n_js,
            self.request_program_js,
            self.app_js,
            mutated,
        )
        self.assertTrue(
            any("us-independent-benchmark-control.json" in error for error in errors),
            errors,
        )

    def test_rejects_removed_us_null_market_boundary(self) -> None:
        mutated = self.independent_controls_js.replace(
            "raw.outputs?.unitedStatesRetailMarketValue !== null",
            "raw.outputs?.unitedStatesRetailMarketValue === null",
            1,
        )
        errors = validate_review_structure(
            self.review_html,
            self.index_html,
            self.review_js,
            self.i18n_js,
            self.request_program_js,
            self.app_js,
            mutated,
        )
        self.assertTrue(
            any("unitedStatesRetailMarketValue" in error for error in errors),
            errors,
        )

    def test_rejects_removed_open_wave_rollup_boundary(self) -> None:
        mutated = self.independent_controls_js.replace(
            "route.globalRollupEligible !== false",
            "route.globalRollupEligible === false",
            1,
        )
        errors = validate_review_structure(
            self.review_html,
            self.index_html,
            self.review_js,
            self.i18n_js,
            self.request_program_js,
            self.app_js,
            mutated,
        )
        self.assertTrue(
            any("globalRollupEligible" in error for error in errors),
            errors,
        )

    def test_rejects_promoted_screened_country(self) -> None:
        screen = copy.deepcopy(self.third_donor)
        screen["countries"][0]["donorStatus"] = "accepted"
        errors = validate_third_donor_screen(screen)
        self.assertTrue(any("must remain not assessed" in error for error in errors), errors)

    def test_rejects_changed_third_donor_decision(self) -> None:
        screen = copy.deepcopy(self.third_donor)
        screen["decision"]["primaryProgrammeCountryIso2"] = "RU"
        errors = validate_third_donor_screen(screen)
        self.assertTrue(any("PL primary" in error for error in errors), errors)

    def test_rejects_stale_prepared_follow_up_state(self) -> None:
        screen = copy.deepcopy(self.third_donor)
        screen["followUpWave"]["draftState"] = "prepared_not_sent"
        errors = validate_third_donor_screen(screen)
        self.assertTrue(any("completed or superseded" in error for error in errors), errors)

    def test_rejects_false_follow_up_completion_state(self) -> None:
        screen = copy.deepcopy(self.third_donor)
        screen["followUpWave"]["items"][1]["threadStatus"] = "follow_up_sent"
        errors = validate_third_donor_screen(screen)
        self.assertTrue(any("completion states differ" in error for error in errors), errors)

    def test_rejects_stale_circana_follow_up_state(self) -> None:
        screen = copy.deepcopy(self.third_donor)
        screen["followUpWave"]["items"][2]["threadStatus"] = "follow_up_sent"
        errors = validate_third_donor_screen(screen)
        self.assertTrue(any("completion states differ" in error for error in errors), errors)

    def test_rejects_missing_third_donor_fetch(self) -> None:
        mutated = self.review_js.replace(
            'fetch("data/third-donor-screen.json"',
            'fetch("data/removed-third-donor-screen.json"',
            1,
        )
        errors = validate_review_structure(
            self.review_html,
            self.index_html,
            mutated,
            self.i18n_js,
            self.request_program_js,
            self.app_js,
        )
        self.assertTrue(any("third-donor-screen.json" in error for error in errors), errors)

    def test_rejects_wall_clock_freshness(self) -> None:
        mutated = self.review_js.replace(
            "function renderReviewSourceFreshness(market, atlas) {",
            "function renderReviewSourceFreshness(market, atlas) { const unsafeNow = Date.now();",
            1,
        )
        errors = validate_review_structure(self.review_html, self.index_html, mutated, self.i18n_js)
        self.assertTrue(any("Source freshness must be deterministic" in error for error in errors), errors)

    def test_rejects_missing_current_market_card_hook(self) -> None:
        mutated = self.review_js.replace(
            "NZ-2024-IDENTIFIED-VAPING-PRODUCT-SALES-RAW-SUM",
            "REMOVED-IDENTIFIED-VAPING-OBSERVATION",
            1,
        )
        errors = validate_review_structure(
            self.review_html,
            self.index_html,
            mutated,
            self.i18n_js,
        )
        self.assertTrue(any("required v27 reconciliation hook" in error for error in errors), errors)

    def test_rejects_missing_nz_closure_pack_hook(self) -> None:
        mutated = self.review_js.replace(
            "source/NZ_2024_DONOR_CLOSURE_PACK.md",
            "source/REMOVED_NZ_2024_DONOR_CLOSURE_PACK.md",
            1,
        )
        errors = validate_review_structure(
            self.review_html,
            self.index_html,
            mutated,
            self.i18n_js,
        )
        self.assertTrue(any("required v27 reconciliation hook" in error for error in errors), errors)

    def test_rejects_missing_nzd_2024_review_rate(self) -> None:
        fx = copy.deepcopy(self.fx)
        fx["rates"] = [
            item for item in fx["rates"]
            if not (item["currency"] == "NZD" and item["year"] == 2024)
        ]
        self.assert_data_rejected(
            fx=fx,
            needle="lacks required card rates",
        )

    def test_rejects_removed_review_eur_helper(self) -> None:
        mutated = self.review_js.replace(
            "function reviewEurEquivalentNode(",
            "function removedReviewEurEquivalentNode(",
            1,
        )
        errors = validate_review_structure(
            self.review_html,
            self.index_html,
            mutated,
            self.i18n_js,
        )
        self.assertTrue(any("reviewEurEquivalentNode" in error for error in errors), errors)

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
