#!/usr/bin/env python3
"""Regression tests for the fail-closed public vendor-response control."""

from __future__ import annotations

import copy
from decimal import Decimal
import unittest
from unittest.mock import patch

from build_vendor_response_control import load_source, normalised, score_vendor
from public_privacy_guard import private_identifier_fingerprint
from validate_vendor_response_control import validate_source


class VendorResponseControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = load_source()

    def test_reviewed_current_source_is_valid(self) -> None:
        errors: list[str] = []
        validate_source(copy.deepcopy(self.source), errors)
        self.assertEqual(errors, [])

    def test_written_brochure_response_is_substantive_but_not_scoreable(self) -> None:
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
        self.assertEqual(
            vendor["publicStatusEn"],
            "Two written responses and an 8-page brochure received. Quote, numerical-sample, "
            "Germany-evaluation and brand-field requests were sent on 2026-07-24. "
            "Euromonitor says it can provide samples, detailed answers and pricing after the "
            "role/access model is clarified; a role/access clarification was sent on 2026-07-24. "
            "Pending: numerical Germany sample, written brand-field confirmation, itemised "
            "price, method, country-product coverage matrix, licence and written derived-output rights. "
            "The brochure's 100-country list is not confirmed e-vapour "
            "country-product coverage. No score, purchase, fee or commitment is established.",
        )
        self.assertEqual(
            vendor["publicStatusFi"],
            "Kaksi kirjallista vastausta ja 8-sivuinen esite on saatu. Tarjous-, numeerinen "
            "näyte-, Saksa-arviointi- ja brändikenttäpyynnöt lähetettiin 24.7.2026. "
            "Euromonitor ilmoittaa voivansa toimittaa näytteitä, yksityiskohtaisia vastauksia "
            "ja hinnoittelua, kun rooli- ja käyttömalli on täsmennetty; rooli- ja käyttömallin "
            "täsmennys lähetettiin 24.7.2026. Odottavat: numeerinen Saksa-näyte, kirjallinen "
            "brändikenttävahvistus, eritelty hinta, menetelmä, maa–tuote-peittomatriisi, "
            "lisenssi ja kirjalliset johdettujen tuotosten oikeudet. Esitteen 100 maan lista "
            "ei ole vahvistettu sähkötupakan maa–tuote-peitto. Pistemäärää, ostoa, maksua tai "
            "sitoumusta ei ole osoitettu.",
        )
        self.assertIn("not confirmed e-vapour country-product coverage", vendor["publicStatusEn"])
        self.assertIn("Germany-evaluation", vendor["publicStatusEn"])
        self.assertIn("written brand-field confirmation", vendor["publicStatusEn"])
        self.assertIn("role/access clarification was sent on 2026-07-24", vendor["publicStatusEn"])
        self.assertNotIn("pending and has not been sent", vendor["publicStatusEn"])
        self.assertIn("written derived-output rights", vendor["publicStatusEn"])
        self.assertNotIn("CEO", vendor["publicStatusEn"])
        self.assertNotIn("single-consultant", vendor["publicStatusEn"])
        self.assertNotIn("single-user", vendor["publicStatusEn"])
        self.assertNotIn("consultant", vendor["publicStatusEn"])
        self.assertNotIn("account history", vendor["publicStatusEn"])
        self.assertTrue(all(value is False for value in vendor["receivedEvidence"].values()))
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
            vendor["receivedEvidence"][gate["evidenceKey"]] = True
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
                    vendor["receivedEvidence"][gate["evidenceKey"]] = True
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


if __name__ == "__main__":
    unittest.main()
