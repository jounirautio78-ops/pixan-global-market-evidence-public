#!/usr/bin/env python3
"""Deterministic tests for the ES/KR/JP official extraction scaffold."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse


SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from extract_es_kr_jp_open_data import (  # noqa: E402
    build_korea_url,
    load_manifest,
    parse_japan_import_csv,
    parse_korea_xml,
    parse_spain_annual_html,
    validate_manifest,
)


RETRIEVED_AT = "2026-07-28T10:00:00+00:00"


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = load_manifest()

    def test_exact_country_and_access_state_contract(self) -> None:
        self.assertEqual(
            [country["countryIso2"] for country in self.manifest["countries"]],
            ["ES", "KR", "JP"],
        )
        statuses = {
            route["status"]
            for country in self.manifest["countries"]
            for route in country["routes"]
        }
        self.assertTrue({"ready", "blocked", "auth_required"}.issubset(statuses))

    def test_every_route_is_fail_closed_for_retail_and_global_rollup(self) -> None:
        routes = [
            route
            for country in self.manifest["countries"]
            for route in country["routes"]
        ]
        self.assertTrue(all(route["retailSalesEligible"] is False for route in routes))
        self.assertTrue(all(route["globalRollupEligible"] is False for route in routes))
        self.assertTrue(all(route["transactionStage"] for route in routes))

    def test_rejects_retail_eligibility_drift(self) -> None:
        mutated = copy.deepcopy(self.manifest)
        mutated["countries"][0]["routes"][0]["retailSalesEligible"] = True
        with self.assertRaisesRegex(ValueError, "retailSalesEligible must be false"):
            validate_manifest(mutated)

    def test_spain_retains_four_epigraphs_and_prospective_boundary(self) -> None:
        route = self.manifest["countries"][0]["routes"][0]
        self.assertEqual(len(route["classification"]["epigraphs"]), 4)
        self.assertTrue(route["coverage"]["prospectiveOnly"])
        self.assertEqual(route["coverage"]["taxEffectiveFrom"], "2025-04-01")

    def test_korea_historical_gate_and_japan_nicotine_separation_are_explicit(self) -> None:
        korea = self.manifest["countries"][1]["routes"][0]
        self.assertEqual(
            korea["classification"]["historicalVersionState"],
            "blocked_pending_year_specific_validation_for_2022_2025",
        )
        japan = self.manifest["countries"][2]["routes"][0]
        nicotine = next(
            item for item in japan["classification"]["codes"] if item["code"] == "240412000"
        )
        self.assertEqual(nicotine["permissionBoundary"], "nicotine_containing")
        self.assertIn("Never combine", japan["permissionBoundary"]["separationRule"])


class SpainParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = load_manifest()

    def test_extracts_only_the_official_aggregate_receipt(self) -> None:
        html = """
        <html><title>Ejercicio 2025</title><body>
        El Impuesto sobre los Líquidos para Cigarrillos Electrónicos
        recaudó en su primer año 30 millones.
        </body></html>
        """
        result = parse_spain_annual_html(html, self.manifest, RETRIEVED_AT)
        self.assertEqual(len(result), 1)
        observation = result[0]
        self.assertEqual(observation["amount"], 30000000)
        self.assertEqual(observation["classificationCode"], "ALL_EPIGRAPHS")
        self.assertEqual(observation["transactionStage"], "realised_excise_cash_receipts")
        self.assertFalse(observation["retailSalesEligible"])
        self.assertFalse(observation["globalRollupEligible"])

    def test_rejects_changed_or_missing_aggregate(self) -> None:
        html = """
        <html><title>Ejercicio 2025</title><body>
        El Impuesto sobre los Líquidos para Cigarrillos Electrónicos
        recaudó en su primer año 31 millones.
        </body></html>
        """
        with self.assertRaisesRegex(ValueError, "resolve uniquely to 30 million"):
            parse_spain_annual_html(html, self.manifest, RETRIEVED_AT)


class KoreaParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = load_manifest()

    def test_url_builder_preserves_exact_official_parameter_contract(self) -> None:
        url = build_korea_url("synthetic-key", "202601", "202612", "2404121000")
        parsed = urlparse(url)
        self.assertEqual(
            parsed.scheme + "://" + parsed.netloc + parsed.path,
            "https://apis.data.go.kr/1220000/Itemtrade/getItemtradeList",
        )
        self.assertEqual(
            parse_qs(parsed.query),
            {
                "serviceKey": ["synthetic-key"],
                "strtYymm": ["202601"],
                "endYymm": ["202612"],
                "hsSgn": ["2404121000"],
            },
        )

    def test_parser_keeps_import_and_export_customs_stages_separate(self) -> None:
        xml = """
        <response>
          <header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE.</resultMsg></header>
          <body><items><item>
            <year>202601</year><hsCode>2404121000</hsCode>
            <statKor>fixture</statKor>
            <impDlr>100</impDlr><impWgt>10</impWgt>
            <expDlr>40</expDlr><expWgt>4</expWgt>
            <balPayments>-60</balPayments>
          </item></items></body>
        </response>
        """
        result = parse_korea_xml(
            xml,
            self.manifest,
            "KCS_HS_CODE_20260101",
            RETRIEVED_AT,
        )
        self.assertEqual([item["flow"] for item in result], ["imports_cif", "exports_fob"])
        self.assertEqual([item["amount"] for item in result], [100, 40])
        self.assertTrue(all(item["amountUnit"] == "USD" for item in result))
        self.assertTrue(all(item["transactionStage"] == "customs_border_declaration" for item in result))
        self.assertTrue(all(item["globalRollupEligible"] is False for item in result))

    def test_2025_response_is_rejected_under_2026_codebook(self) -> None:
        xml = """
        <response><header><resultCode>00</resultCode></header><body><items><item>
          <year>2025</year><hsCode>2404121000</hsCode>
          <impDlr>1</impDlr><impWgt>1</impWgt>
          <expDlr>0</expDlr><expWgt>0</expWgt>
        </item></items></body></response>
        """
        with self.assertRaisesRegex(ValueError, "year-specific validated codebook"):
            parse_korea_xml(
                xml,
                self.manifest,
                "KCS_HS_CODE_20260101",
                RETRIEVED_AT,
            )


class JapanParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = load_manifest()

    def test_partner_rows_are_aggregated_per_code_but_codes_remain_separate(self) -> None:
        csv_text = """Exp or Imp,Year,HS,Country,Unit1,Unit2,Quantity1-Year,Quantity2-Year,Value-Year
2,2025,'240412000',105,  ,KG,0,10,100
2,2025,'240412000',205,  ,KG,0,5,50
2,2025,'854340000',105,  ,NO,0,20,200
2,2025,'854340000',113,  ,NO,0,30,300
"""
        result = parse_japan_import_csv(csv_text, 2025, self.manifest, RETRIEVED_AT)
        indexed = {item["classificationCode"]: item for item in result}
        self.assertEqual(set(indexed), {"240412000", "854340000"})
        self.assertEqual(indexed["240412000"]["amount"], 150)
        self.assertEqual(indexed["240412000"]["quantity2"], 15)
        self.assertEqual(indexed["240412000"]["permissionBoundary"], "nicotine_containing")
        self.assertEqual(indexed["854340000"]["amount"], 500)
        self.assertEqual(indexed["854340000"]["quantity2"], 50)
        self.assertEqual(indexed["854340000"]["permissionBoundary"], "device")
        self.assertTrue(all(item["amountUnit"] == "JPY_THOUSAND" for item in result))
        self.assertTrue(all(item["globalRollupEligible"] is False for item in result))

    def test_non_target_year_is_rejected(self) -> None:
        csv_text = """Exp or Imp,Year,HS,Country,Unit1,Unit2,Quantity1-Year,Quantity2-Year,Value-Year
2,2024,'854340000',105,  ,NO,0,20,200
"""
        with self.assertRaisesRegex(ValueError, "only the verified Japan 2025"):
            parse_japan_import_csv(csv_text, 2024, self.manifest, RETRIEVED_AT)


if __name__ == "__main__":
    unittest.main()
