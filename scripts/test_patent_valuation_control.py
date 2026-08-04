#!/usr/bin/env python3
"""Mutation tests for the public patent-valuation fail-closed boundary."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

try:
    from validate_patent_valuation_control import validate_control
except ModuleNotFoundError:
    from scripts.validate_patent_valuation_control import validate_control


ROOT = Path(__file__).resolve().parents[1]


class PatentValuationControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        patent = json.loads((ROOT / "source" / "patent-history.json").read_text(encoding="utf-8"))
        cls.control = patent["monetisation"]["valuationControl"]
        cls.source_ids = {item["sourceId"] for item in patent["sources"]}

    def errors(self, control: dict) -> list[str]:
        errors: list[str] = []
        validate_control(control, errors, known_source_ids=self.source_ids)
        return errors

    def test_current_control_passes(self) -> None:
        self.assertEqual(self.errors(copy.deepcopy(self.control)), [])

    def test_rejects_zero_as_patent_value(self) -> None:
        control = copy.deepcopy(self.control)
        control["ultimatePatentValueEUR"] = 0
        self.assertTrue(any("ultimatePatentValueEUR" in error for error in self.errors(control)))

    def test_rejects_computed_status(self) -> None:
        control = copy.deepcopy(self.control)
        control["status"] = "COMPUTED"
        self.assertTrue(any("NOT_COMPUTED" in error for error in self.errors(control)))

    def test_rejects_non_null_intermediate(self) -> None:
        control = copy.deepcopy(self.control)
        control["formulaBridge"]["steps"][2]["valueEUR"] = 1
        self.assertTrue(any("valueEUR must remain null" in error for error in self.errors(control)))

    def test_rejects_missing_gate(self) -> None:
        control = copy.deepcopy(self.control)
        control["hardGates"].pop()
        self.assertTrue(any("hard-gate IDs/order" in error for error in self.errors(control)))

    def test_rejects_market_as_valuation_basis(self) -> None:
        control = copy.deepcopy(self.control)
        control["marketEvidenceRole"]["role"] = "VALUATION_BASIS"
        self.assertTrue(any("INPUT_ONLY" in error for error in self.errors(control)))

    def test_rejects_market_setting_patent_value(self) -> None:
        control = copy.deepcopy(self.control)
        control["marketEvidenceRole"]["maySetPatentValue"] = True
        self.assertTrue(any("maySetPatentValue" in error for error in self.errors(control)))

    def test_rejects_donor_gate_as_final_objective(self) -> None:
        control = copy.deepcopy(self.control)
        control["donorGateSnapshot"]["roleEn"] = "Final valuation objective."
        self.assertTrue(any("final valuation objective" in error for error in self.errors(control)))

    def test_rejects_globalised_german_judgment(self) -> None:
        control = copy.deepcopy(self.control)
        control["germanyRole"]["mayEstablishGlobalInfringement"] = True
        self.assertTrue(any("mayEstablishGlobalInfringement" in error for error in self.errors(control)))

    def test_rejects_double_counting_permission(self) -> None:
        control = copy.deepcopy(self.control)
        control["guardrails"]["noDoubleCounting"] = False
        self.assertTrue(any("noDoubleCounting" in error for error in self.errors(control)))

    def test_rejects_missing_as_zero(self) -> None:
        control = copy.deepcopy(self.control)
        control["guardrails"]["missingIsZero"] = True
        self.assertTrue(any("missingIsZero" in error for error in self.errors(control)))

    def test_rejects_additive_output(self) -> None:
        control = copy.deepcopy(self.control)
        control["outputCases"][0]["nonAdditive"] = False
        self.assertTrue(any("non-additive" in error for error in self.errors(control)))

    def test_rejects_non_null_probability_weighted_output(self) -> None:
        control = copy.deepcopy(self.control)
        control["outputCases"][2]["probabilityWeightedValueEUR"] = 1
        self.assertTrue(any("probabilityWeightedValueEUR" in error for error in self.errors(control)))

    def test_rejects_licensing_through_infringing_sales(self) -> None:
        control = copy.deepcopy(self.control)
        control["routeBranches"][1]["requiresPotentiallyInfringingSales"] = True
        self.assertTrue(any("infringement dependency" in error for error in self.errors(control)))

    def test_rejects_double_counted_time_discount(self) -> None:
        control = copy.deepcopy(self.control)
        control["presentValueConvention"]["separateTimeDiscountFactorPermitted"] = True
        self.assertTrue(any("time discount factor" in error for error in self.errors(control)))

    def test_rejects_incomplete_scenario_qa(self) -> None:
        control = copy.deepcopy(self.control)
        control["scenarioControl"]["probabilitiesMustSumToOne"] = False
        self.assertTrue(any("sum to one" in error for error in self.errors(control)))

    def test_rejects_generic_collateral_haircut(self) -> None:
        control = copy.deepcopy(self.control)
        control["collateralRecoveryCase"]["simpleValueTimesHaircutPermitted"] = True
        self.assertTrue(any("generic haircut" in error for error in self.errors(control)))

    def test_rejects_independent_review_as_model_input(self) -> None:
        control = copy.deepcopy(self.control)
        control["independentReview"]["usedAsComputationInput"] = True
        self.assertTrue(any("computation input" in error for error in self.errors(control)))

    def test_rejects_material_comparability_transfer(self) -> None:
        control = copy.deepcopy(self.control)
        control["germanyRole"]["statementEn"] = "Materially comparable products establish transfer."
        errors = self.errors(control)
        self.assertTrue(any("material comparability" in error or "adjudicated-case" in error for error in errors))

    def test_rejects_global_circular_gate(self) -> None:
        control = copy.deepcopy(self.control)
        control["dependencyControl"]["globalCircularBlock"] = True
        self.assertTrue(any("global circular" in error for error in self.errors(control)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
