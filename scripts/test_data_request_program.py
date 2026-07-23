#!/usr/bin/env python3
"""Mutation tests for the privacy-safe public data-request tracking boundary."""

from __future__ import annotations

import copy
import unittest

from validate_data_request_program import SOURCE_PATH, read_json, validate_program


class DataRequestBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.program = read_json(SOURCE_PATH)

    def assert_rejected(self, mutate) -> None:
        candidate = copy.deepcopy(self.program)
        mutate(candidate)
        errors: list[str] = []
        validate_program(candidate, errors)
        self.assertTrue(errors, "mutated programme unexpectedly passed validation")

    def test_approved_public_tracking_passes(self) -> None:
        errors: list[str] = []
        validate_program(copy.deepcopy(self.program), errors)
        self.assertEqual(errors, [])

    def test_rejects_top_level_sent_flag(self) -> None:
        self.assert_rejected(lambda item: item.__setitem__("sent", True))

    def test_rejects_route_dispatched_flag(self) -> None:
        self.assert_rejected(lambda item: item["routes"][0].__setitem__("requestDispatched", True))

    def test_rejects_sent_timestamp(self) -> None:
        self.assert_rejected(lambda item: item["routes"][0].__setitem__("sent_timestamp", "2026-07-22"))

    def test_rejects_missing_bilingual_source_label(self) -> None:
        self.assert_rejected(lambda item: item["routes"][0]["officialSources"][0].pop("labelFi"))

    def test_rejects_empty_source_label(self) -> None:
        self.assert_rejected(lambda item: item["routes"][0]["officialSources"][0].__setitem__("labelEn", ""))

    def test_rejects_empty_authority_name(self) -> None:
        self.assert_rejected(lambda item: item["routes"][0]["primaryAuthority"].__setitem__("nameEn", ""))

    def test_rejects_string_instead_of_requested_records_array(self) -> None:
        self.assert_rejected(lambda item: item["routes"][0].__setitem__("recordsRequestedEn", "sales"))

    def test_rejects_string_instead_of_languages_array(self) -> None:
        self.assert_rejected(lambda item: item["routes"][0].__setitem__("languages", "en"))

    def test_rejects_wrong_sent_country_set(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "US")
            route["status"] = "sent"
            route["dispatch"] = {
                "state": "sent",
                "sentOn": "2026-07-23",
                "publicAuthorityReference": None,
                "responseState": "not_publicly_recorded",
            }

        self.assert_rejected(mutate)

    def test_rejects_status_dispatch_mismatch(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "US")
            route["status"] = "sent"

        self.assert_rejected(mutate)

    def test_rejects_future_sent_date(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "FI")
            route["dispatch"]["sentOn"] = "2026-07-24"

        self.assert_rejected(mutate)

    def test_rejects_unsafe_public_reference(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "GB")
            route["dispatch"]["publicAuthorityReference"] = "private@example.com"

        self.assert_rejected(mutate)

    def test_rejects_private_recipient_metadata(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "FI")
            route["dispatch"]["recipientEmail"] = "private@example.com"

        self.assert_rejected(mutate)

    def test_rejects_private_message_identifier(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "PL")
            route["dispatch"]["messageId"] = "private-message-id"

        self.assert_rejected(mutate)

    def test_rejects_acknowledgement_metadata(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "GB")
            route["dispatch"]["acknowledgedOn"] = "2026-07-17"

        self.assert_rejected(mutate)

    def test_rejects_unapproved_response_state(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "GB")
            route["dispatch"]["responseState"] = "acknowledged"

        self.assert_rejected(mutate)


if __name__ == "__main__":
    unittest.main()
