#!/usr/bin/env python3
"""Fail-closed extractors for the ES/KR/JP official-data route wave.

The default run validates and prints route state only. Observations are emitted
only from explicitly supplied source files. The script never converts currency,
estimates retail sales or combines candidate classifications.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html import unescape
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "source" / "open-official-extraction-wave-es-kr-jp.json"
ALLOWED_ROUTE_STATUS = {"ready", "blocked", "auth_required", "fee_required"}
ALLOWED_FEE_STATUS = {"free", "not_applicable", "fee_required"}


def read_json(path: Path | str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _route_index(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        route["routeId"]: route
        for country in manifest["countries"]
        for route in country["routes"]
    }


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate the extraction control without optional third-party packages."""

    if manifest.get("schemaVersion") != "1.0":
        raise ValueError("schemaVersion must be 1.0")
    if manifest.get("waveId") != "ES_KR_JP_OPEN_OFFICIAL_2026_07_28":
        raise ValueError("unexpected waveId")
    if manifest.get("status") != "route_control_not_market_size":
        raise ValueError("wave must remain route_control_not_market_size")
    if manifest.get("targetPeriods") != [2022, 2023, 2024, 2025]:
        raise ValueError("targetPeriods must remain the exact 2022-2025 plan")

    countries = manifest.get("countries")
    if not isinstance(countries, list) or len(countries) != 3:
        raise ValueError("manifest must contain exactly three countries")
    if [country.get("countryIso2") for country in countries] != ["ES", "KR", "JP"]:
        raise ValueError("country order and membership must be ES, KR, JP")
    if manifest.get("countryCount") != len(countries):
        raise ValueError("countryCount does not match countries")

    seen_routes: set[str] = set()
    statuses: set[str] = set()
    for country in countries:
        if country.get("marketValueStatus") != "not_computed":
            raise ValueError(f"{country['countryIso2']}: market value must not be computed")
        routes = country.get("routes")
        if not isinstance(routes, list) or not routes:
            raise ValueError(f"{country['countryIso2']}: routes are required")
        for route in routes:
            route_id = route.get("routeId")
            if not isinstance(route_id, str) or not route_id.startswith(country["countryIso2"] + "_"):
                raise ValueError(f"{country['countryIso2']}: invalid routeId")
            if route_id in seen_routes:
                raise ValueError(f"duplicate routeId: {route_id}")
            seen_routes.add(route_id)
            status = route.get("status")
            if status not in ALLOWED_ROUTE_STATUS:
                raise ValueError(f"{route_id}: invalid route status")
            statuses.add(status)
            if route.get("feeStatus") not in ALLOWED_FEE_STATUS:
                raise ValueError(f"{route_id}: invalid fee status")
            if route.get("retailSalesEligible") is not False:
                raise ValueError(f"{route_id}: retailSalesEligible must be false")
            if route.get("globalRollupEligible") is not False:
                raise ValueError(f"{route_id}: globalRollupEligible must be false")
            if not route.get("transactionStage") or not route.get("flow"):
                raise ValueError(f"{route_id}: transaction stage and flow are required")
            for source in route.get("sources", []):
                if not source.get("url", "").startswith("https://"):
                    raise ValueError(f"{route_id}: every source must use https")
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", source.get("verifiedOn", "")):
                    raise ValueError(f"{route_id}: source verifiedOn must be an ISO date")

    if not {"ready", "blocked", "auth_required"}.issubset(statuses):
        raise ValueError("wave must expose ready, blocked and auth_required states")

    routes = _route_index(manifest)
    spain = routes["ES_AEAT_2025_MODEL573_AGGREGATE_RECEIPTS"]
    if spain["coverage"].get("prospectiveOnly") is not True:
        raise ValueError("Spain 2025 route must remain prospective-only")
    if len(spain["classification"].get("epigraphs", [])) != 4:
        raise ValueError("Spain aggregate must retain all four Model 573 epigraphs")

    korea = routes["KR_KCS_ITEMTRADE_HSK10"]
    query = korea["query"]
    if query.get("baseUrl") != "https://apis.data.go.kr/1220000/Itemtrade":
        raise ValueError("Korea baseUrl changed")
    if query.get("operationPath") != "/getItemtradeList":
        raise ValueError("Korea operation changed")
    if korea["classification"].get("historicalVersionState") != (
        "blocked_pending_year_specific_validation_for_2022_2025"
    ):
        raise ValueError("Korea historical codebook gate must remain blocked")
    for item in korea["classification"].get("codes", []):
        if not re.fullmatch(r"\d{10}", item.get("code", "")):
            raise ValueError("Korea classifications must retain 10-digit HSK codes")

    japan = routes["JP_MOF_ESTAT_COMMODITY_BY_COUNTRY_IMPORT"]
    codes = japan["classification"].get("codes", [])
    if {item.get("code") for item in codes} != {
        "240412000",
        "240419100",
        "240419200",
        "854340000",
    }:
        raise ValueError("Japan 2025 9-digit classification set changed")
    nicotine = next(item for item in codes if item["code"] == "240412000")
    if nicotine.get("permissionBoundary") != "nicotine_containing":
        raise ValueError("Japan nicotine classification must remain separate")
    if japan["permissionBoundary"].get("separationRule") is None:
        raise ValueError("Japan permission separation rule is required")

    required_output = set(manifest.get("outputSchema", {}).get("requiredFields", []))
    for field in {
        "transactionStage",
        "accessStatus",
        "retailSalesEligible",
        "globalRollupEligible",
        "limitations",
    }:
        if field not in required_output:
            raise ValueError(f"output schema is missing {field}")
    return manifest


def load_manifest(path: Path | str = MANIFEST_PATH) -> dict[str, Any]:
    return validate_manifest(read_json(path))


def _number(text: str, field: str) -> int | float:
    try:
        value = Decimal(text.strip().replace(",", "."))
    except (InvalidOperation, AttributeError):
        raise ValueError(f"{field} must be numeric") from None
    if not value.is_finite() or value < 0:
        raise ValueError(f"{field} must be a finite non-negative number")
    return int(value) if value == value.to_integral_value() else float(value)


def _clean_html(source: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", source)
    return " ".join(unescape(no_tags).split())


def parse_spain_annual_html(
    source: str,
    manifest: dict[str, Any],
    retrieved_at: str,
) -> list[dict[str, Any]]:
    """Extract the one published 2025 aggregate without allocating epigraphs."""

    text = _clean_html(source)
    if "2025" not in text:
        raise ValueError("Spain source does not identify report year 2025")
    pattern = re.compile(
        r"Impuesto\s+sobre\s+los\s+L.quidos\s+para\s+Cigarrillos\s+"
        r"Electr.nicos\s+recaud.\s+(?:en\s+su\s+primer\s+a.o\s+)?"
        r"(\d+(?:[.,]\d+)?)\s+millones",
        re.IGNORECASE,
    )
    values = {_number(match, "Spain amount_million_eur") for match in pattern.findall(text)}
    if values != {30}:
        raise ValueError(f"Spain aggregate anchor must resolve uniquely to 30 million; found {values}")

    route = _route_index(manifest)["ES_AEAT_2025_MODEL573_AGGREGATE_RECEIPTS"]
    return [
        {
            "observationId": "ES-AEAT-M573-2025-ALL-EPIGRAPHS-RECEIPTS",
            "countryIso2": "ES",
            "routeId": route["routeId"],
            "sourcePeriod": 2025,
            "productBucket": "model_573_all_four_epigraphs",
            "classificationSystem": route["classification"]["system"],
            "classificationVersion": route["classification"]["version"],
            "classificationCode": route["classification"]["aggregateCode"],
            "transactionStage": route["transactionStage"],
            "flow": route["flow"],
            "amount": 30000000,
            "amountUnit": "EUR",
            "currency": "EUR",
            "dataStatus": "observed",
            "accessStatus": route["status"],
            "sourceUrl": route["query"]["endpoint"],
            "retrievedAt": retrieved_at,
            "retailSalesEligible": False,
            "globalRollupEligible": False,
            "limitations": list(route["limitations"]),
        }
    ]


def build_korea_url(service_key: str, start_yymm: str, end_yymm: str, hs_code: str) -> str:
    """Build the official KCS request URL; this function does not call it."""

    if not service_key:
        raise ValueError("Korea serviceKey is required")
    for name, value in (("strtYymm", start_yymm), ("endYymm", end_yymm)):
        if not re.fullmatch(r"\d{6}", value):
            raise ValueError(f"{name} must be YYYYMM")
    if start_yymm > end_yymm:
        raise ValueError("strtYymm cannot be later than endYymm")
    if not re.fullmatch(r"(?:\d{2}|\d{4}|\d{6}|\d{10})", hs_code):
        raise ValueError("hsSgn must contain 2, 4, 6 or 10 digits")
    params = {
        "serviceKey": service_key,
        "strtYymm": start_yymm,
        "endYymm": end_yymm,
        "hsSgn": hs_code,
    }
    return "https://apis.data.go.kr/1220000/Itemtrade/getItemtradeList?" + urlencode(params)


def parse_korea_xml(
    source: str,
    manifest: dict[str, Any],
    classification_version: str,
    retrieved_at: str,
) -> list[dict[str, Any]]:
    """Parse a saved KCS response, enforcing the currently verified 2026 codebook."""

    route = _route_index(manifest)["KR_KCS_ITEMTRADE_HSK10"]
    if classification_version != route["classification"]["version"]:
        raise ValueError("unverified Korea classification version")
    root = ElementTree.fromstring(source)
    result_code = root.findtext(".//header/resultCode")
    if result_code not in {None, "", "00", "0000"}:
        raise ValueError(f"Korea API returned resultCode={result_code}")
    code_map = {item["code"]: item for item in route["classification"]["codes"]}
    observations: list[dict[str, Any]] = []
    for item in root.findall(".//items/item"):
        period = (item.findtext("year") or "").strip()
        code = (item.findtext("hsCode") or "").strip()
        if not period.startswith("2026"):
            raise ValueError("2022-2025 Korea responses require a year-specific validated codebook")
        if code not in code_map:
            raise ValueError(f"Korea response contains an unreviewed HSK10 code: {code}")
        classification = code_map[code]
        for flow, amount_field, weight_field in (
            ("imports_cif", "impDlr", "impWgt"),
            ("exports_fob", "expDlr", "expWgt"),
        ):
            observations.append(
                {
                    "observationId": f"KR-KCS-{period}-{code}-{flow.upper()}",
                    "countryIso2": "KR",
                    "routeId": route["routeId"],
                    "sourcePeriod": period,
                    "productBucket": classification["bucket"],
                    "classificationSystem": route["classification"]["system"],
                    "classificationVersion": classification_version,
                    "classificationCode": code,
                    "transactionStage": route["transactionStage"],
                    "flow": flow,
                    "amount": _number(item.findtext(amount_field) or "0", amount_field),
                    "amountUnit": "USD",
                    "currency": "USD",
                    "quantity1": _number(item.findtext(weight_field) or "0", weight_field),
                    "quantity1Unit": "KG_NET",
                    "dataStatus": "observed",
                    "accessStatus": "ready",
                    "sourceUrl": route["sources"][0]["url"],
                    "retrievedAt": retrieved_at,
                    "retailSalesEligible": False,
                    "globalRollupEligible": False,
                    "limitations": list(route["limitations"]),
                }
            )
    if not observations:
        raise ValueError("Korea API response contained no item observations")
    return observations


def _read_csv_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "cp932", "shift_jis"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"{path}: unsupported CSV encoding")


def parse_japan_import_csv(
    source: str,
    year: int,
    manifest: dict[str, Any],
    retrieved_at: str,
) -> list[dict[str, Any]]:
    """Aggregate partner rows by 9-digit code, never across product codes."""

    route = _route_index(manifest)["JP_MOF_ESTAT_COMMODITY_BY_COUNTRY_IMPORT"]
    if year != 2025:
        raise ValueError("only the verified Japan 2025 code and table version is enabled")
    reader = csv.DictReader(StringIO(source))
    required = {
        "Exp or Imp",
        "Year",
        "HS",
        "Country",
        "Unit1",
        "Unit2",
        "Quantity1-Year",
        "Quantity2-Year",
        "Value-Year",
    }
    if reader.fieldnames is None or not required.issubset(reader.fieldnames):
        raise ValueError(f"Japan CSV is missing fields: {sorted(required - set(reader.fieldnames or []))}")

    code_map = {item["code"]: item for item in route["classification"]["codes"]}
    totals: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"amount": Decimal(0), "q1": Decimal(0), "q2": Decimal(0), "u1": set(), "u2": set()}
    )
    for row in reader:
        code = row["HS"].strip().strip("'")
        if code not in code_map:
            continue
        if row["Exp or Imp"].strip() != "2" or row["Year"].strip() != str(year):
            raise ValueError(f"Japan target code {code} has an unexpected flow or year")
        country = row["Country"].strip()
        if not re.fullmatch(r"\d{3}", country):
            raise ValueError(f"Japan target code {code} has a non-partner aggregate row")
        current = totals[code]
        current["amount"] += Decimal(str(_number(row["Value-Year"], "Value-Year")))
        current["q1"] += Decimal(str(_number(row["Quantity1-Year"], "Quantity1-Year")))
        current["q2"] += Decimal(str(_number(row["Quantity2-Year"], "Quantity2-Year")))
        if row["Unit1"].strip():
            current["u1"].add(row["Unit1"].strip())
        if row["Unit2"].strip():
            current["u2"].add(row["Unit2"].strip())

    observations: list[dict[str, Any]] = []
    for code in sorted(totals):
        total = totals[code]
        if len(total["u1"]) > 1 or len(total["u2"]) > 1:
            raise ValueError(f"Japan code {code} has inconsistent quantity units")
        classification = code_map[code]
        observation = {
            "observationId": f"JP-MOF-IMPORT-{year}-{code}",
            "countryIso2": "JP",
            "routeId": route["routeId"],
            "sourcePeriod": year,
            "productBucket": classification["bucket"],
            "classificationSystem": route["classification"]["system"],
            "classificationVersion": route["classification"]["version"],
            "classificationCode": code,
            "transactionStage": route["transactionStage"],
            "flow": route["flow"],
            "amount": _number(str(total["amount"]), "amount"),
            "amountUnit": "JPY_THOUSAND",
            "currency": "JPY",
            "quantity1": _number(str(total["q1"]), "quantity1"),
            "quantity1Unit": next(iter(total["u1"]), None),
            "quantity2": _number(str(total["q2"]), "quantity2"),
            "quantity2Unit": next(iter(total["u2"]), None),
            "permissionBoundary": classification["permissionBoundary"],
            "dataStatus": "observed",
            "accessStatus": route["status"],
            "sourceUrl": route["sources"][1]["url"] if code.startswith("24") else route["sources"][2]["url"],
            "retrievedAt": retrieved_at,
            "retailSalesEligible": False,
            "globalRollupEligible": False,
            "limitations": list(route["limitations"]),
        }
        observations.append(observation)
    if not observations:
        raise ValueError("Japan CSV contained no reviewed target codes")
    return observations


def _route_states(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "countryIso2": country["countryIso2"],
            "routeId": route["routeId"],
            "status": route["status"],
            "feeStatus": route["feeStatus"],
            "transactionStage": route["transactionStage"],
            "retailSalesEligible": False,
            "globalRollupEligible": False,
        }
        for country in manifest["countries"]
        for route in country["routes"]
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--spain-html", type=Path)
    parser.add_argument("--korea-xml", type=Path)
    parser.add_argument("--korea-codebook-version")
    parser.add_argument("--japan-import-csv", type=Path, action="append", default=[])
    parser.add_argument("--japan-year", type=int, default=2025)
    parser.add_argument("--retrieved-at")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    manifest = load_manifest(args.manifest)
    retrieved_at = args.retrieved_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    observations: list[dict[str, Any]] = []
    if args.spain_html:
        observations.extend(
            parse_spain_annual_html(args.spain_html.read_text(encoding="utf-8"), manifest, retrieved_at)
        )
    if args.korea_xml:
        if not args.korea_codebook_version:
            parser.error("--korea-codebook-version is required with --korea-xml")
        observations.extend(
            parse_korea_xml(
                args.korea_xml.read_text(encoding="utf-8"),
                manifest,
                args.korea_codebook_version,
                retrieved_at,
            )
        )
    for csv_path in args.japan_import_csv:
        observations.extend(
            parse_japan_import_csv(_read_csv_text(csv_path), args.japan_year, manifest, retrieved_at)
        )

    result = {
        "schemaVersion": "1.0",
        "waveId": manifest["waveId"],
        "asOf": manifest["asOf"],
        "runStatus": "observations_extracted" if observations else "route_control_only",
        "routeStates": _route_states(manifest),
        "observations": observations,
        "retailMarketValueComputed": False,
        "globalRollupChanged": False,
    }
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
