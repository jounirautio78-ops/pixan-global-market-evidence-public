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
        self.assertEqual(len(self.program["supplementaryRequests"]), 2)
        supplement = next(
            request
            for request in self.program["supplementaryRequests"]
            if request["requestId"] == "DE-BVL-TABAKERZV25-ANNUAL-SALES"
        )
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

    def test_poland_euceg_supplement_is_sent_without_changing_country_queue(self) -> None:
        supplement = next(
            request
            for request in self.program["supplementaryRequests"]
            if request["requestId"] == "PL-BUREAU-CHEMICALS-EUCEG-ANNUAL-SALES"
        )
        self.assertEqual(supplement["countryIso2"], "PL")
        self.assertIs(supplement["countsTowardCountryQueue"], False)
        self.assertEqual(supplement["dispatch"], {
            "state": "sent",
            "sentOn": "2026-07-28",
            "publicAuthorityReference": None,
            "responseState": "not_publicly_recorded",
        })
        self.assertEqual(
            supplement["requestChannel"]["url"],
            "https://www.gov.pl/web/chemical/access-to-public-information",
        )
        self.assertEqual(
            {source["url"] for source in supplement["officialSources"]},
            {
                "https://www.gov.pl/web/chemical/"
                "notification-of-electronic-cigarettes-and-refill-containers",
                "https://www.gov.pl/web/chemikalia/"
                "przekazywanie-sprawozdan-rocznych-dotyczacych-papierosow-"
                "elektronicznych-i-pojemnikow-zapasowych2",
                "https://www.gov.pl/web/chemikalia/monitorowanie-rynku-e-papierosow",
            },
        )
        self.assertIn("adds no country", supplement["queueBoundaryEn"])
        self.assertIn("does not replace", supplement["queueBoundaryEn"])

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
            "IT": "official_aggregate_not_held_public_routes_identified",
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

    def test_italy_response_is_negative_and_tax_anchor_is_not_market_data(self) -> None:
        italy = next(
            route for route in self.program["routes"] if route["countryIso2"] == "IT"
        )
        self.assertEqual(italy["dispatch"], {
            "state": "sent",
            "sentOn": "2026-07-23",
            "publicAuthorityReference": None,
            "responseState": "official_aggregate_not_held_public_routes_identified",
        })
        source_urls = {source["url"] for source in italy["officialSources"]}
        self.assertEqual(source_urls, {
            "https://www.adm.gov.it/portale/-/"
            "libro-blu-organizzazione-statistiche-e-attivita-anno-2024",
            "https://www.adm.gov.it/portale/-/"
            "portale-prodotti-liquidi-da-inalazione-pli-e-prodotti-accessori-dei-tabacchi-pat-1",
            "https://www.adm.gov.it/portale/prodotti-succedanei-tabacco-liquidi-inalazione",
            "https://www.adm.gov.it/portale/bollettino-statistico",
        })
        self.assertIn("EUR 55,910,871.89", italy["rationaleEn"])
        self.assertIn("EUR 84,309,841.41", italy["rationaleEn"])
        self.assertIn("+50.79%", italy["rationaleEn"])
        self.assertIn("tax revenue only", italy["rationaleEn"])
        self.assertIn("not retail value, physical volume, market growth or donor evidence", italy["rationaleEn"])
        self.assertIn("no requested volume, retail value or annual market data", italy["rationaleEn"])

    def test_sweden_response_is_structural_data_with_sales_unavailable(self) -> None:
        sweden = next(
            route for route in self.program["routes"] if route["countryIso2"] == "SE"
        )
        self.assertEqual(sweden["dispatch"], {
            "state": "sent",
            "sentOn": "2026-07-23",
            "publicAuthorityReference": None,
            "responseState": "official_structural_data_received_sales_not_available",
        })
        self.assertIn(
            "official aggregate registration-structure counts",
            self.program["independenceNoticeEn"],
        )
        self.assertIn("not annual sales", self.program["independenceNoticeEn"])
        self.assertIn("donor evidence", self.program["independenceNoticeEn"])
        self.assertIn("ei vuosimyynnistä", self.program["independenceNoticeFi"])
        self.assertIn("luovuttajaevidenssistä", self.program["independenceNoticeFi"])

    def test_france_response_is_a_partial_customs_trade_proxy_not_retail_sales(self) -> None:
        france = next(
            route for route in self.program["routes"] if route["countryIso2"] == "FR"
        )
        self.assertEqual(france["dispatch"], {
            "state": "sent",
            "sentOn": "2026-07-23",
            "publicAuthorityReference": None,
            "responseState": "official_customs_trade_proxy_received_scope_partial",
        })
        self.assertIn("supply-stage proxy", france["rationaleEn"])
        self.assertIn("not retail market size", france["rationaleEn"])
        self.assertIn(
            "official annual partner-level customs trade extracts",
            self.program["independenceNoticeEn"],
        )
        self.assertIn("not consumer-retail sales", self.program["independenceNoticeEn"])

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

    def test_rejects_changed_poland_supplement_channel(self) -> None:
        def mutate(item) -> None:
            supplement = next(
                request
                for request in item["supplementaryRequests"]
                if request["requestId"] == "PL-BUREAU-CHEMICALS-EUCEG-ANNUAL-SALES"
            )
            supplement["requestChannel"]["url"] = "https://www.gov.pl/web/finanse"

        self.assert_rejected(mutate)

    def test_rejects_unapproved_third_supplement(self) -> None:
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

    def test_rejects_structural_response_reference_even_if_format_looks_public(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "SE")
            route["dispatch"]["publicAuthorityReference"] = "DIARY 67890"

        self.assert_rejected(mutate)

    def test_rejects_sweden_response_relabelled_as_sales_data(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "SE")
            route["dispatch"]["responseState"] = "official_annual_sales_data_received"

        self.assert_rejected(mutate)

    def test_rejects_italy_tax_revenue_relabelled_as_market_value(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "IT")
            route["rationaleEn"] = route["rationaleEn"].replace(
                "This is tax revenue only",
                "This is retail market value",
            )

        self.assert_rejected(mutate)

    def test_rejects_missing_sweden_sales_boundary(self) -> None:
        self.assert_rejected(
            lambda item: item.__setitem__(
                "independenceNoticeEn",
                item["independenceNoticeEn"].replace("not annual sales", "annual sales"),
            )
        )

    def test_rejects_missing_sweden_public_context_source(self) -> None:
        def mutate(item) -> None:
            route = next(route for route in item["routes"] if route["countryIso2"] == "SE")
            route["officialSources"].pop()

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
