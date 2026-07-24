#!/usr/bin/env python3
"""Mutation tests for v20 donor closure actions and publication gates."""

from __future__ import annotations

import copy
import unittest

from validate_donor_cockpit import (
    APP,
    INDEX,
    MARKET,
    PUBLIC_DONORS,
    PUBLIC_LANES,
    PUBLIC_SCENARIOS,
    load_json,
    validate_donor_controls,
)


class DonorCockpitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lanes = load_json(PUBLIC_LANES)
        cls.cockpit = load_json(PUBLIC_DONORS)
        cls.scenarios = load_json(PUBLIC_SCENARIOS)
        cls.market = load_json(MARKET)
        cls.index_html = INDEX.read_text(encoding="utf-8")
        cls.app_js = APP.read_text(encoding="utf-8")

    def validate(
        self,
        *,
        lanes: dict | None = None,
        cockpit: dict | None = None,
        scenarios: dict | None = None,
        index_html: str | None = None,
        app_js: str | None = None,
    ) -> list[str]:
        return validate_donor_controls(
            lanes or self.lanes,
            cockpit or self.cockpit,
            scenarios or self.scenarios,
            self.market,
            index_html or self.index_html,
            app_js or self.app_js,
        )

    def assert_rejected(self, *, needle: str, **changes: object) -> None:
        errors = self.validate(**changes)
        self.assertTrue(any(needle in error for error in errors), errors)

    def test_reviewed_baseline_passes(self) -> None:
        self.assertEqual(self.validate(), [])

    def test_rejects_records_in_licensed_lane(self) -> None:
        lanes = copy.deepcopy(self.lanes)
        lanes["lanes"][1]["records"] = [{"value": 1}]
        self.assert_rejected(
            lanes=lanes,
            needle="must not embed records",
        )

    def test_rejects_sensitive_private_field(self) -> None:
        lanes = copy.deepcopy(self.lanes)
        lanes["lanes"][2]["respondentName"] = "Example respondent"
        self.assert_rejected(
            lanes=lanes,
            needle="sensitive field names",
        )

    def test_rejects_non_public_donor_record(self) -> None:
        cockpit = copy.deepcopy(self.cockpit)
        cockpit["candidates"][0]["evidenceLaneId"] = "licensed_controlled"
        self.assert_rejected(
            cockpit=cockpit,
            needle="must remain in public_reproducible",
        )

    def test_rejects_missing_d1_d10_status(self) -> None:
        cockpit = copy.deepcopy(self.cockpit)
        cockpit["candidates"][0]["criterionStatuses"].pop()
        self.assert_rejected(
            cockpit=cockpit,
            needle="requires exactly D1-D10",
        )

    def test_rejects_declared_decision_not_computed_from_criteria(self) -> None:
        cockpit = copy.deepcopy(self.cockpit)
        candidate = cockpit["candidates"][0]
        for criterion in candidate["criterionStatuses"]:
            criterion["status"] = "passed"
        self.assert_rejected(
            cockpit=cockpit,
            needle="declared donor decision does not match",
        )

    def test_rejects_missing_blocking_criterion_closure_coverage(self) -> None:
        cockpit = copy.deepcopy(self.cockpit)
        candidate = cockpit["candidates"][0]
        candidate["closureActions"][0]["criterionIds"].remove("D3")
        self.assert_rejected(
            cockpit=cockpit,
            needle="closure actions must cover every failed/open criterion exactly once",
        )

    def test_rejects_blocking_criterion_duplicated_across_closure_actions(self) -> None:
        cockpit = copy.deepcopy(self.cockpit)
        candidate = cockpit["candidates"][0]
        candidate["closureActions"][1]["criterionIds"].append("D3")
        self.assert_rejected(
            cockpit=cockpit,
            needle="blocking criteria must not be duplicated across closure actions",
        )

    def test_rejects_closure_action_targeting_passed_criterion(self) -> None:
        cockpit = copy.deepcopy(self.cockpit)
        candidate = cockpit["candidates"][0]
        candidate["closureActions"][0]["criterionIds"].append("D1")
        self.assert_rejected(
            cockpit=cockpit,
            needle="closure action must not target passed criteria",
        )

    def test_rejects_blocked_candidate_without_closure_actions(self) -> None:
        cockpit = copy.deepcopy(self.cockpit)
        cockpit["candidates"][0]["closureActions"] = []
        self.assert_rejected(
            cockpit=cockpit,
            needle="blocked candidate requires closure actions",
        )

    def test_rejects_invalid_closure_action_enums(self) -> None:
        mutations = (
            ("ownerRole", "individual_researcher", ".ownerRole is invalid"),
            ("routeType", "general_web_search", ".routeType is invalid"),
            ("publicStatus", "completed", ".publicStatus is invalid"),
        )
        for field, value, needle in mutations:
            with self.subTest(field=field):
                cockpit = copy.deepcopy(self.cockpit)
                cockpit["candidates"][0]["closureActions"][0][field] = value
                self.assert_rejected(cockpit=cockpit, needle=needle)

    def test_rejects_invalid_closure_action_dates(self) -> None:
        mutations = (
            (
                "statusAsOf",
                "2026-07-25",
                ".statusAsOf must be no later than cockpit asOf",
            ),
            (
                "statusAsOf",
                "not-a-date",
                ".statusAsOf must be no later than cockpit asOf",
            ),
            (
                "nextFollowUpOn",
                "2026-07-23",
                ".nextFollowUpOn must be on or after statusAsOf",
            ),
            (
                "nextFollowUpOn",
                "not-a-date",
                ".nextFollowUpOn must be on or after statusAsOf",
            ),
        )
        for field, value, needle in mutations:
            with self.subTest(field=field, value=value):
                cockpit = copy.deepcopy(self.cockpit)
                cockpit["candidates"][0]["closureActions"][0][field] = value
                self.assert_rejected(cockpit=cockpit, needle=needle)

    def test_rejects_accepted_candidate_with_closure_actions(self) -> None:
        cockpit = copy.deepcopy(self.cockpit)
        candidate = cockpit["candidates"][0]
        for criterion in candidate["criterionStatuses"]:
            criterion["status"] = "passed"
        candidate["declaredDecision"] = "accepted"
        self.assert_rejected(
            cockpit=cockpit,
            needle="accepted candidate must not retain closure actions",
        )

    def test_missing_country_input_returns_not_computed(self) -> None:
        scenarios = copy.deepcopy(self.scenarios)
        scenarios["countryYearScenarios"][0]["inputs"]["base"] = {
            "value": None,
            "sourceIds": [],
        }
        self.assert_rejected(
            scenarios=scenarios,
            needle="missing or invalid inputs must return not_computed",
        )

    def test_rejects_nz_model_relabelled_as_observed_value(self) -> None:
        scenarios = copy.deepcopy(self.scenarios)
        scenarios["countryYearScenarios"][0]["evidenceStatus"] = "official_observed"
        self.assert_rejected(
            scenarios=scenarios,
            needle="supported model, not an observed national value",
        )

    def test_rejects_nz_component_arithmetic_mismatch(self) -> None:
        scenarios = copy.deepcopy(self.scenarios)
        scenarios["countryYearScenarios"][0]["componentBreakdown"]["low"][
            "generalRetailRpsNzd"
        ] += 1
        self.assert_rejected(
            scenarios=scenarios,
            needle="component arithmetic does not add to combinedNzd",
        )

    def test_blocked_global_gate_rejects_values(self) -> None:
        scenarios = copy.deepcopy(self.scenarios)
        source_id = "CA-HC-VAPING-SALES-2024"
        for key, value in (("low", 1.0), ("base", 2.0), ("high", 3.0)):
            scenarios["globalScenario"]["inputs"][key] = {
                "value": value,
                "sourceIds": [source_id],
            }
        scenarios["globalScenario"]["declaredStatus"] = "computed"
        errors = self.validate(scenarios=scenarios)
        self.assertTrue(
            any("status must be computed from donor and coverage gates" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("Global values must remain null" in error for error in errors),
            errors,
        )

    def test_three_donors_still_require_coverage_gate(self) -> None:
        cockpit = copy.deepcopy(self.cockpit)
        for candidate in cockpit["candidates"]:
            if candidate["candidateType"] != "country_year":
                continue
            for criterion in candidate["criterionStatuses"]:
                criterion["status"] = "passed"
            candidate["declaredDecision"] = "accepted"
        scenarios = copy.deepcopy(self.scenarios)
        source_id = "CA-HC-VAPING-SALES-2024"
        for key, value in (("low", 1.0), ("base", 2.0), ("high", 3.0)):
            scenarios["globalScenario"]["inputs"][key] = {
                "value": value,
                "sourceIds": [source_id],
            }
        scenarios["globalScenario"]["declaredStatus"] = "computed"
        self.assert_rejected(
            cockpit=cockpit,
            scenarios=scenarios,
            needle="status must be computed from donor and coverage gates",
        )

    def test_rejects_missing_scenario_hook(self) -> None:
        index_html = self.index_html.replace(
            'id="market-scenario-lab"',
            'id="removed-market-scenario-lab"',
            1,
        )
        self.assert_rejected(
            index_html=index_html,
            needle="Missing v18 site hook #market-scenario-lab",
        )

    def test_rejects_removed_global_gate_logic(self) -> None:
        app_js = self.app_js.replace(
            "acceptedDonors >= minimumDonors && coveragePassed",
            "acceptedDonors >= minimumDonors",
            1,
        )
        self.assert_rejected(
            app_js=app_js,
            needle="Missing v18 fail-closed app control",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
