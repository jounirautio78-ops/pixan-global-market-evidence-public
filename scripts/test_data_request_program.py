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

    def test_global_evidence_stack_is_six_layers_for_195_states(self) -> None:
        stack = self.program["evidenceStack"]
        self.assertEqual(self.program["schemaVersion"], 3)
        self.assertEqual(stack["stateUniverseCount"], 195)
        self.assertEqual(
            [layer["layerId"] for layer in stack["layers"]],
            [
                "statutory_sales",
                "excise_domestic_release",
                "customs_net_imports",
                "retail_or_shipments",
                "price_channel_bridge",
                "enforcement_signal",
            ],
        )
        self.assertIn("never mechanically added", stack["methodBoundaryEn"])
        self.assertIn("confidence sit above all six layers", stack["methodBoundaryEn"])
        self.assertIn("eikä muutu nollaksi", stack["methodBoundaryFi"])
        self.assertIn("ei koskaan laillista myyntiä", stack["layers"][5]["outputFi"])

    def test_german_bvl_supplement_is_sent_without_changing_country_queue(self) -> None:
        self.assertEqual(len(self.program["supplementaryRequests"]), 1)
        supplement = self.program["supplementaryRequests"][0]
        self.assertEqual(supplement["requestId"], "DE-BVL-TABAKERZV25-ANNUAL-SALES")
        self.assertEqual(supplement["countryIso2"], "DE")
        self.assertIs(supplement["countsTowardCountryQueue"], False)
        self.assertEqual(supplement["dispatch"], {
            "state": "sent",
            "sentOn": "2026-07-24",
            "publicAuthorityReference": None,
            "responseState": "not_publicly_recorded",
        })
        source_urls = {source["url"] for source in supplement["officialSources"]}
        self.assertIn("https://www.gesetze-im-internet.de/tabakerzv/__25.html", source_urls)
        self.assertIn(
            "https://www.bvl.bund.de/DE/Arbeitsbereiche/03_Verbraucherprodukte/"
            "03_AntragstellerUnternehmen/04_Tabakerzeugnisse_E-Zigaretten/"
            "01_Mitteilungspflicht/bgs_tabakerzeugnisse_mitteilungspflicht_node.html"
            "?thema=Mitteilungspflicht",
            source_urls,
        )
        self.assertEqual(
            supplement["requestChannel"]["url"],
            "https://www.bvl.bund.de/DE/Service/07_Kontakt/einleitung.html",
        )
        self.assertEqual(
            sum(route["status"] == "sent" for route in self.program["routes"]),
            12,
        )
        self.assertEqual(
            sum(route["status"] == "draft_not_sent" for route in self.program["routes"]),
            8,
        )

    def test_german_primary_customs_destatis_process_state_is_preserved(self) -> None:
        germany = next(
            route for route in self.program["routes"] if route["countryIso2"] == "DE"
        )
        self.assertEqual(germany["primaryAuthority"]["nameEn"], "German Customs and Federal Statistical Office")
        self.assertIn("GENESIS table family 73411", germany["fallbackAuthority"]["nameEn"])
        self.assertEqual(germany["dispatch"], {
            "state": "sent",
            "sentOn": "2026-07-23",
            "publicAuthorityReference": None,
            "responseState": "registered_and_processing_confirmed",
        })

    def test_exact_process_response_states_are_public_and_non_substantive(self) -> None:
        expected = {
            "DE": "registered_and_processing_confirmed",
            "FI": "registered_processing_notice_received",
            "DK": "automated_receipt_acknowledged",
            "SE": "automated_route_correction_received",
        }
        actual = {
            route["countryIso2"]: route["dispatch"]["responseState"]
            for route in self.program["routes"]
            if route["countryIso2"] in expected
        }
        self.assertEqual(actual, expected)
        self.assertTrue(all(
            route["dispatch"]["publicAuthorityReference"] is None
            for route in self.program["routes"]
            if route["countryIso2"] in expected
        ))
        self.assertIn("substantive data", self.program["independenceNoticeEn"])
        self.assertIn("sisällöllisenä datana", self.program["independenceNoticeFi"])

    def test_rejects_top_level_sent_flag(self) -> None:
        self.assert_rejected(lambda item: item.__setitem__("sent", True))

    def test_rejects_wrong_state_universe_count(self) -> None:
        self.assert_rejected(
            lambda item: item["evidenceStack"].__setitem__("stateUniverseCount", 249)
        )

    def test_rejects_missing_evidence_layer(self) -> None:
        self.assert_rejected(lambda item: item["evidenceStack"]["layers"].pop())

    def test_rejects_reordered_evidence_layers(self) -> None:
        def mutate(item) -> None:
            layers = item["evidenceStack"]["layers"]
            layers[0], layers[1] = layers[1], layers[0]

        self.assert_rejected(mutate)

    def test_rejects_missing_to_zero_method_boundary(self) -> None:
        self.assert_rejected(
            lambda item: item["evidenceStack"].__setitem__(
                "methodBoundaryEn",
                "The six layers can be combined into a single total.",
            )
        )

    def test_rejects_supplement_counted_as_another_country(self) -> None:
        self.assert_rejected(
            lambda item: item["supplementaryRequests"][0].__setitem__(
                "countsTowardCountryQueue", True
            )
        )

    def test_rejects_changed_bvl_dispatch_date(self) -> None:
        self.assert_rejected(
            lambda item: item["supplementaryRequests"][0]["dispatch"].__setitem__(
                "sentOn", "2026-07-23"
            )
        )

    def test_rejects_supplement_without_section_25_source(self) -> None:
        self.assert_rejected(
            lambda item: item["supplementaryRequests"][0]["officialSources"].pop(0)
        )

    def test_rejects_unapproved_second_supplement(self) -> None:
        def mutate(item) -> None:
            extra = copy.deepcopy(item["supplementaryRequests"][0])
            extra["requestId"] = "CA-UNAPPROVED"
            extra["countryIso2"] = "CA"
            item["supplementaryRequests"].append(extra)

        self.assert_rejected(mutate)

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
            route = next(route for route in item["routes"] if route["countryIso2"] == "CN")
            route["status"] = "sent"
            route["dispatch"] = {
                "state": "sent",
                "sentOn": "2026-07-24",
                "publicAuthorityReference": None,
                "responseState": "not_publicly_recorded",
            }

        self.assert_rejected(mutate)

    def test_rejects_status_dispatch_mismatch(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "US")
            route["status"] = "draft_not_sent"

        self.assert_rejected(mutate)

    def test_rejects_future_sent_date(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "FI")
            route["dispatch"]["sentOn"] = "2026-07-25"

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

    def test_rejects_process_ticket_identifier(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "DE")
            route["dispatch"]["ticketId"] = "PRIVATE-TICKET-123"

        self.assert_rejected(mutate)

    def test_rejects_process_reference_even_if_format_looks_public(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "FI")
            route["dispatch"]["publicAuthorityReference"] = "DIARY 12345"

        self.assert_rejected(mutate)

    def test_rejects_email_address_inside_public_route_text(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "SE")
            route["requesterEligibility"]["caveatEn"] += " Contact records@example.gov."

        self.assert_rejected(mutate)

    def test_rejects_process_response_overstatement_as_market_data(self) -> None:
        self.assert_rejected(
            lambda item: item.__setitem__(
                "independenceNoticeEn",
                item["independenceNoticeEn"] + " Market data received.",
            )
        )

    def test_rejects_process_response_overstatement_as_fee_acceptance(self) -> None:
        self.assert_rejected(
            lambda item: item.__setitem__(
                "independenceNoticeEn",
                item["independenceNoticeEn"] + " A fee was accepted.",
            )
        )

    def test_rejects_weakened_process_response_boundary(self) -> None:
        self.assert_rejected(
            lambda item: item.__setitem__(
                "independenceNoticeEn",
                "Independent project. Four authority responses were received.",
            )
        )

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
