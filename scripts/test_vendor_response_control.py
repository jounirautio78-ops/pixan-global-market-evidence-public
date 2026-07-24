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
            "Written response and an 8-page brochure received; the brochure's 100-country "
            "list is the overall Passport Tobacco scope, not confirmed e-vapour "
            "country-product coverage; a non-binding multi-option quote request and "
            "numerical-sample resend request were sent 2026-07-24; the reviewable "
            "numerical sample, quote and licence terms remain pending",
        )
        self.assertEqual(
            vendor["publicStatusFi"],
            "Kirjallinen vastaus ja 8-sivuinen esite vastaanotettu; esitteen 100 maan "
            "lista kuvaa Passport Tobaccon kokonaispeittoa, ei vahvistettua sähkötupakan "
            "maa–tuote-peittoa; ei-sitova monivaihtoehtoinen tarjouspyyntö ja numeerisen "
            "näytteen uudelleenlähetyspyyntö lähetettiin 24.7.2026; tarkistettava "
            "numeerinen näyte, tarjous ja lisenssiehdot odottavat",
        )
        self.assertIn("not confirmed e-vapour country-product coverage", vendor["publicStatusEn"])
        self.assertIn("multi-option quote request", vendor["publicStatusEn"])
        self.assertTrue(all(value is False for value in vendor["receivedEvidence"].values()))
        self.assertTrue(all(value is None for value in vendor["criterionScores"].values()))
        self.assertEqual(vendor["scoringState"], "not_scored")
        self.assertIsNone(vendor["weightedScore"])
        self.assertFalse(vendor["purchaseAuthorised"])
        self.assertEqual(candidate["summary"]["substantiveResponses"], 1)

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
