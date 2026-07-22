#!/usr/bin/env python3
"""Mutation tests for the draft-only data-request publication boundary."""

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

    def test_rejects_sent_status(self) -> None:
        self.assert_rejected(lambda item: item["routes"][0].__setitem__("status", "sent"))


if __name__ == "__main__":
    unittest.main()
