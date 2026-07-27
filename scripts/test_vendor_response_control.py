#!/usr/bin/env python3
"""Regression tests for the fail-closed public vendor-response control."""

from __future__ import annotations

import copy
from decimal import Decimal
import unittest
from unittest.mock import patch

from build_vendor_response_control import load_source, normalised, score_vendor
from public_privacy_guard import private_identifier_fingerprint
from validate_vendor_response_control import (
    validate_source,
    validate_vendor_script_text,
)


class VendorResponseControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = load_source()

    def test_reviewed_current_source_is_valid(self) -> None:
        errors: list[str] = []
        validate_source(copy.deepcopy(self.source), errors)
        self.assertEqual(errors, [])

    def test_germany_sample_and_quote_are_received_but_not_scoreable(self) -> None:
        candidate = normalised(copy.deepcopy(self.source))
        vendor = next(
            item
            for item in candidate["vendors"]
            if item["vendorId"] == "euromonitor-passport-nicotine"
        )
        self.assertEqual(
            vendor["responseState"],
            "substantive_response_received",
        )
        self.assertIn("expanded Germany workbook sample", vendor["publicStatusEn"])
        self.assertIn("indicative annual package quotes", vendor["publicStatusEn"])
        self.assertIn("78-market e-vapour value-coverage list", vendor["publicStatusEn"])
        self.assertIn("private 2023–2024 numerical liquid-volume comparison", vendor["publicStatusEn"])
        self.assertIn("retail-stage, tax-basis and product-scope bridge", vendor["publicStatusEn"])
        self.assertIn("data-room use", vendor["publicStatusEn"])
        self.assertIn("NOT SCORED", vendor["publicStatusEn"])
        self.assertNotIn("CEO", vendor["publicStatusEn"])
        self.assertNotIn("single-consultant", vendor["publicStatusEn"])
        self.assertNotIn("single-user", vendor["publicStatusEn"])
        self.assertNotIn("consultant", vendor["publicStatusEn"])
        self.assertNotIn("account history", vendor["publicStatusEn"])
        self.assertTrue(vendor["receivedEvidence"]["sample"])
        self.assertTrue(vendor["receivedEvidence"]["quote"])
        self.assertTrue(vendor["receivedEvidence"]["methodology"])
        self.assertTrue(vendor["receivedEvidence"]["coverageMatrix"])
        self.assertFalse(vendor["receivedEvidence"]["officialAnchorReconciliation"])
        self.assertTrue(vendor["receivedEvidence"]["transactionUseRights"])
        self.assertTrue(vendor["receivedEvidence"]["totalCostTerms"])
        self.assertEqual(
            {
                gate_id: result["status"]
                for gate_id, result in vendor["gateResults"].items()
            },
            {
                "G1": "not_testable",
                "G2": "fail",
                "G3": "fail",
                "G4": "not_testable",
                "G5": "fail",
                "G6": "fail",
            },
        )
        self.assertTrue(vendor["quoteReceived"])
        self.assertEqual(vendor["evidenceReceivedCount"], 6)
        self.assertEqual(vendor["evaluatedGateCount"], 6)
        self.assertEqual(vendor["mandatoryGatePassCount"], 0)
        self.assertTrue(all(value is None for value in vendor["criterionScores"].values()))
        self.assertEqual(vendor["scoringState"], "not_scored")
        self.assertIsNone(vendor["weightedScore"])
        self.assertFalse(vendor["purchaseAuthorised"])
        self.assertEqual(candidate["summary"]["substantiveResponses"], 1)

    def test_germany_benchmark_is_not_testable_and_uses_reviewed_anchors(self) -> None:
        benchmark = self.source["germanyBenchmark"]
        self.assertEqual(benchmark["status"], "not_testable")
        self.assertEqual(
            [
                (
                    item["year"],
                    item["value"],
                    item["finality"],
                    item["role"],
                )
                for item in benchmark["officialAnchors"]
            ],
            [
                (2023, 1_241_000, "final", "pass_test"),
                (2024, 1_284_000, "final", "pass_test"),
                (2025, 1_518_000, "provisional", "context_only"),
            ],
        )
        self.assertEqual(
            benchmark["thresholds"]["annualDeviation"]["maximumPct"],
            15,
        )
        self.assertEqual(
            benchmark["thresholds"]["twoYearCumulativeDeviation"]["maximumPct"],
            10,
        )
        self.assertTrue(benchmark["vendorPassDoesNotEstablishDonorPass"])
        self.assertEqual(benchmark["donorGateEffect"], "none")
        self.assertIn("0/3", benchmark["donorBoundaryEn"])

    def test_germany_benchmark_rejects_changed_anchor_or_threshold(self) -> None:
        for field, mutation, expected_error in (
            (
                "anchor",
                lambda candidate: candidate["germanyBenchmark"]["officialAnchors"][0].update(
                    {"value": 1_240_999}
                ),
                "Germany 2023 official anchor differs",
            ),
            (
                "annual threshold",
                lambda candidate: candidate["germanyBenchmark"]["thresholds"][
                    "annualDeviation"
                ].update({"maximumPct": 16}),
                "Germany annualDeviation threshold differs",
            ),
        ):
            with self.subTest(field=field):
                candidate = copy.deepcopy(self.source)
                mutation(candidate)
                errors: list[str] = []
                validate_source(candidate, errors)
                self.assertIn(expected_error, errors)

    def test_germany_vendor_gate_cannot_claim_donor_acceptance(self) -> None:
        candidate = copy.deepcopy(self.source)
        candidate["germanyBenchmark"]["vendorPassDoesNotEstablishDonorPass"] = False
        candidate["germanyBenchmark"]["donorGateEffect"] = "accepted_donor"
        errors: list[str] = []
        validate_source(candidate, errors)
        self.assertTrue(
            any("must not establish donor-market acceptance" in error for error in errors),
            errors,
        )

    def test_ecig_unanswered_state_retains_follow_up_without_evidence(self) -> None:
        candidate = normalised(copy.deepcopy(self.source))
        vendor = next(
            item
            for item in candidate["vendors"]
            if item["vendorId"] == "ecig-global-market-database"
        )
        self.assertEqual(vendor["responseState"], "pending_no_acknowledgement")
        self.assertIn("2026-07-28", vendor["publicStatusEn"])
        self.assertTrue(all(value is False for value in vendor["receivedEvidence"].values()))
        self.assertTrue(
            all(
                result == {
                    "status": "missing",
                    "reasonCodes": ["EVIDENCE_NOT_RECEIVED"],
                }
                for result in vendor["gateResults"].values()
            )
        )
        self.assertTrue(all(value is None for value in vendor["criterionScores"].values()))
        self.assertEqual(vendor["scoringState"], "not_scored")
        self.assertIsNone(vendor["weightedScore"])
        self.assertFalse(vendor["purchaseAuthorised"])

    def test_missing_mandatory_evidence_is_not_scored(self) -> None:
        candidate = copy.deepcopy(self.source)
        vendor = candidate["vendors"][0]
        vendor["criterionScores"] = {
            criterion["id"]: 4 for criterion in candidate["criteria"]
        }
        self.assertIsNone(
            score_vendor(vendor, candidate["criteria"], candidate["mandatoryGates"])
        )

    def test_complete_gates_and_scores_calculate_weighted_result(self) -> None:
        candidate = copy.deepcopy(self.source)
        vendor = candidate["vendors"][0]
        for gate in candidate["mandatoryGates"]:
            vendor["gateResults"][gate["gateCode"]] = {
                "status": "pass",
                "reasonCodes": [],
            }
        vendor["criterionScores"] = {
            criterion["id"]: 4 for criterion in candidate["criteria"]
        }
        self.assertEqual(
            score_vendor(vendor, candidate["criteria"], candidate["mandatoryGates"]),
            Decimal("4.00"),
        )

    def test_out_of_range_or_non_finite_scores_are_not_scored(self) -> None:
        for invalid in (-1, 6, float("nan"), float("inf"), True):
            with self.subTest(invalid=invalid):
                candidate = copy.deepcopy(self.source)
                vendor = candidate["vendors"][0]
                for gate in candidate["mandatoryGates"]:
                    vendor["gateResults"][gate["gateCode"]] = {
                        "status": "pass",
                        "reasonCodes": [],
                    }
                vendor["criterionScores"] = {
                    criterion["id"]: invalid for criterion in candidate["criteria"]
                }
                self.assertIsNone(
                    score_vendor(
                        vendor,
                        candidate["criteria"],
                        candidate["mandatoryGates"],
                    )
                )

    def test_gate_status_must_be_one_of_four_reviewed_states(self) -> None:
        candidate = copy.deepcopy(self.source)
        candidate["vendors"][0]["gateResults"]["G1"]["status"] = "partial"
        errors: list[str] = []
        validate_source(candidate, errors)
        self.assertTrue(
            any("invalid gate status" in error for error in errors),
            errors,
        )

    def test_non_pass_gate_requires_a_reviewed_reason_code(self) -> None:
        candidate = copy.deepcopy(self.source)
        candidate["vendors"][0]["gateResults"]["G1"]["reasonCodes"] = []
        errors: list[str] = []
        validate_source(candidate, errors)
        self.assertTrue(
            any("non-PASS status requires a reason code" in error for error in errors),
            errors,
        )

    def test_gate_rejects_reason_code_from_another_gate(self) -> None:
        candidate = copy.deepcopy(self.source)
        candidate["vendors"][0]["gateResults"]["G1"] = {
            "status": "fail",
            "reasonCodes": ["RIGHTS_DATA_ROOM_UNCONFIRMED"],
        }
        errors: list[str] = []
        validate_source(candidate, errors)
        self.assertTrue(
            any("unreviewed reason code" in error for error in errors),
            errors,
        )

    def test_gate_rejects_reason_status_mismatch(self) -> None:
        candidate = copy.deepcopy(self.source)
        candidate["vendors"][0]["gateResults"]["G1"] = {
            "status": "fail",
            "reasonCodes": ["SAMPLE_REQUIRED_YEARS_MISSING"],
        }
        errors: list[str] = []
        validate_source(candidate, errors)
        self.assertTrue(
            any("inconsistent with status" in error for error in errors),
            errors,
        )

    def test_pass_gate_cannot_carry_failure_reasons(self) -> None:
        candidate = copy.deepcopy(self.source)
        candidate["vendors"][0]["gateResults"]["G1"] = {
            "status": "pass",
            "reasonCodes": ["EVIDENCE_NOT_RECEIVED"],
        }
        errors: list[str] = []
        validate_source(candidate, errors)
        self.assertTrue(
            any("PASS cannot carry failure reasons" in error for error in errors),
            errors,
        )

    def test_quote_does_not_count_as_a_mandatory_gate_pass(self) -> None:
        candidate = normalised(copy.deepcopy(self.source))
        vendor = next(
            item
            for item in candidate["vendors"]
            if item["vendorId"] == "euromonitor-passport-nicotine"
        )
        self.assertTrue(vendor["quoteReceived"])
        self.assertTrue(vendor["receivedEvidence"]["quote"])
        self.assertEqual(vendor["mandatoryGatePassCount"], 0)
        self.assertEqual(vendor["scoringState"], "not_scored")
        self.assertIsNone(vendor["weightedScore"])

    def test_public_source_rejects_premature_scores(self) -> None:
        candidate = copy.deepcopy(self.source)
        candidate["vendors"][0]["criterionScores"]["coverage"] = 0
        errors: list[str] = []
        validate_source(candidate, errors)
        self.assertTrue(
            any("must not be converted into scores" in error for error in errors),
            errors,
        )

    def test_public_source_rejects_private_contact_data(self) -> None:
        candidate = copy.deepcopy(self.source)
        candidate["vendors"][0]["publicStatusEn"] = "Reply from analyst@example.test"
        errors: list[str] = []
        validate_source(candidate, errors)
        self.assertTrue(
            any("email address" in error for error in errors),
            errors,
        )

    def test_public_source_rejects_unreviewed_status_claim(self) -> None:
        candidate = copy.deepcopy(self.source)
        candidate["vendors"][0]["publicStatusEn"] = (
            "Substantive response received; ready for purchase"
        )
        errors: list[str] = []
        validate_source(candidate, errors)
        self.assertTrue(
            any("publicStatusEn differs" in error for error in errors),
            errors,
        )

    def test_public_source_rejects_unreviewed_product_claim(self) -> None:
        candidate = copy.deepcopy(self.source)
        candidate["vendors"][0]["product"] = "Unsupported global coverage claim"
        errors: list[str] = []
        validate_source(candidate, errors)
        self.assertTrue(
            any("product differs" in error for error in errors),
            errors,
        )

    def test_public_source_rejects_fingerprinted_private_identifier(self) -> None:
        marker = "Example Confidential Counterparty"
        candidate = copy.deepcopy(self.source)
        candidate["vendors"][0]["publicStatusEn"] = marker
        fingerprints = frozenset({private_identifier_fingerprint(marker)})
        errors: list[str] = []
        with patch("public_privacy_guard.PRIVATE_IDENTIFIER_FINGERPRINTS", fingerprints):
            validate_source(candidate, errors)
        self.assertTrue(
            any("private identifier fingerprint" in error for error in errors),
            errors,
        )

    def test_visible_receipt_ledger_hooks_are_fail_closed(self) -> None:
        script = (
            "function renderReceiptLedger() { "
            "return [vendor.receivedEvidence, vendor.evidenceReceivedCount, "
            "control.evidenceTypes, 'vendor-response-receipts', "
            "'vendor-response-receipt-list', "
            "'Receipt does not mean the gate passed.', "
            "'Vastaanotto ei tarkoita portin läpäisyä.']; }"
        )
        errors: list[str] = []
        validate_vendor_script_text(script, errors)
        self.assertEqual(errors, [])

        errors = []
        validate_vendor_script_text(
            script.replace("vendor.receivedEvidence", "vendor.gateResults"),
            errors,
        )
        self.assertTrue(
            any("visible receipt-ledger hooks" in error for error in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
