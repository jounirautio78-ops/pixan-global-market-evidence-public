#!/usr/bin/env python3
"""Fail-closed validation for the public, generated lender package."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import zipfile
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse
from xml.etree import ElementTree as ET

from openpyxl import load_workbook
from pptx import Presentation

try:
    from bank_register_parity import validate_register_parity
except ModuleNotFoundError:  # Support importing this file as scripts.validate_bank_package.
    from scripts.bank_register_parity import validate_register_parity


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "site" / "data" / "bank-package-manifest.json"
LOCK_PATH = ROOT / "source" / "bank-package-en-lock.json"
CHANGELOG_PATH = ROOT / "site" / "data" / "changelog.json"
REGISTER_CSV_PATH = ROOT / "site" / "data" / "bank-evidence-register.csv"
EN_REGISTER_CSV_PATH = ROOT / "site" / "data" / "bank-evidence-register-en.csv"
MARKET_VALUES_PATH = ROOT / "site" / "data" / "market-values.json"
COUNTRY_SCENARIOS_PATH = ROOT / "site" / "data" / "country-scenarios.json"
PUBLIC_FX_PATH = ROOT / "site" / "data" / "fx-rates.json"
SOURCE_FX_PATH = ROOT / "source" / "fx-rates.json"
PUBLIC_FX_SCHEMA_PATH = ROOT / "site" / "schemas" / "fx-rates.schema.json"
SOURCE_FX_SCHEMA_PATH = ROOT / "source" / "schemas" / "fx-rates.schema.json"
ARTIFACT_BUILDER_PATH = ROOT / "scripts" / "artifact-build" / "build_bank_package_artifacts.mjs"

REGISTER_HEADERS = [
    "Väite",
    "Dia/osio",
    "Todiste",
    "Lähde",
    "Päivämäärä",
    "Laskentatapa",
    "Oletukset",
    "Luottamustaso",
    "Puutteet / tarvittava lisänäyttö",
]
ALLOWED_STATUSES = {"Vahvistettu", "Tuettu", "Oletus", "Puuttuu"}
EN_REGISTER_HEADERS = [
    "Claim",
    "Slide/section",
    "Evidence",
    "Source",
    "Date",
    "Calculation method",
    "Assumptions",
    "Confidence",
    "Gaps / additional evidence needed",
]
EN_ALLOWED_STATUSES = {"Confirmed", "Supported", "Assumption", "Missing"}
EUR_EQUIVALENT_HEADERS = {
    "fi": [
        "Tietuetyyppi",
        "Tunniste",
        "Erä / komponentti",
        "Maa / maantiede",
        "Vuosi",
        "Periodi",
        "Alkuperäinen määrä",
        "Valuutta",
        "ECB-kurssi (valuuttayksikköä / EUR)",
        "EUR-vasta-arvo (täysi tarkkuus)",
        "Rate ID",
        "ECB-lähde URL",
        "Tila",
        "Syy / menetelmä",
    ],
    "en": [
        "Record type",
        "Record ID",
        "Item / component",
        "Country / geography",
        "Year",
        "Period",
        "Original amount",
        "Currency",
        "ECB rate (currency units / EUR)",
        "EUR equivalent (full precision)",
        "Rate ID",
        "ECB source URL",
        "Status",
        "Reason / method",
    ],
}
EUR_EQUIVALENT_SHEET_NAMES = {"fi": "Eurovastineet", "en": "EUR equivalents"}
EXPECTED_TEMPLATE_INPUTS = {
    "scripts/artifact-build/seeds/v17/pixan-bank-deck-short-en.pptx",
    "scripts/artifact-build/seeds/v17/pixan-bank-deck-medium-en.pptx",
    "scripts/artifact-build/seeds/v17/pixan-bank-deck-large-en.pptx",
    "scripts/artifact-build/seeds/v17/pixan-bank-evidence-register-en.xlsx",
    "scripts/artifact-build/seeds/v17/pixan-bank-deck-short-fi.pptx",
    "scripts/artifact-build/seeds/v17/pixan-bank-deck-medium-fi.pptx",
    "scripts/artifact-build/seeds/v17/pixan-bank-deck-large-fi.pptx",
    "scripts/artifact-build/seeds/v17/pixan-bank-evidence-register-fi.xlsx",
}
EXPECTED_INPUTS = {
    "scripts/artifact-build/build_bank_package_artifacts.mjs",
    *EXPECTED_TEMPLATE_INPUTS,
    "site/data/atlas.json",
    "site/data/changelog.json",
    "site/data/country-scenarios.json",
    "site/data/donor-cockpit.json",
    "site/data/evidence-lanes.json",
    "site/data/fx-rates.json",
    "site/data/market-values.json",
    "site/data/patent-history.json",
    "site/schemas/fx-rates.schema.json",
    "source/bank-evidence-register-en.json",
    "source/bank-package-en-lock.json",
    "source/fx-rates.json",
    "source/schemas/fx-rates.schema.json",
    "source/NZ_2023_ANNUAL_RETURNS_FAIL_CLOSED.md",
    "source/NZ_2024_ANNUAL_RETURNS_RECONCILIATION.md",
    "source/NZ_2024_RPS_RETAIL_VALUE_SENSITIVITY.md",
    "source/CANADA_RCS_2019_2025_RETAIL_SALES.md",
    "source/US_FTC_2015_2021_REPORTED_SALES.md",
}
EXPECTED_ARTIFACTS = {
    "short-deck-fi": {
        "kind": "pptx",
        "language": "fi",
        "path": "downloads/pixan-bank-deck-short-fi.pptx",
        "slideCount": 6,
    },
    "medium-deck-fi": {
        "kind": "pptx",
        "language": "fi",
        "path": "downloads/pixan-bank-deck-medium-fi.pptx",
        "slideCount": 12,
    },
    "large-deck-fi": {
        "kind": "pptx",
        "language": "fi",
        "path": "downloads/pixan-bank-deck-large-fi.pptx",
        "slideCount": 30,
    },
    "evidence-register-fi": {
        "kind": "xlsx",
        "language": "fi",
        "path": "downloads/pixan-bank-evidence-register-fi.xlsx",
    },
    "short-deck-en": {
        "kind": "pptx",
        "language": "en",
        "path": "downloads/pixan-bank-deck-short-en.pptx",
        "slideCount": 6,
    },
    "medium-deck-en": {
        "kind": "pptx",
        "language": "en",
        "path": "downloads/pixan-bank-deck-medium-en.pptx",
        "slideCount": 12,
    },
    "large-deck-en": {
        "kind": "pptx",
        "language": "en",
        "path": "downloads/pixan-bank-deck-large-en.pptx",
        "slideCount": 30,
    },
    "evidence-register-en": {
        "kind": "xlsx",
        "language": "en",
        "path": "downloads/pixan-bank-evidence-register-en.xlsx",
    },
}
MEDIUM_SECTION_TITLES = [
    "rahoitusteesi",
    "ongelma",
    "patentoitu ratkaisu",
    "patentti ja ip-status",
    "tekninen erottautuminen",
    "markkinan koko ja rajaus",
    "asiakkaat ja ostoperuste",
    "kilpailu ja vaihtoehdot",
    "validointi ja nykyinen näyttö",
    "kaupallistamismalli",
    "taloudellinen malli ja herkkyydet",
    "riskit, hallintatoimet ja seuraavat vaiheet",
]
EN_MEDIUM_SECTION_TITLES = [
    "financing thesis",
    "problem",
    "patented solution",
    "patent and ip status",
    "technical differentiation",
    "market size and scope",
    "customers and purchase rationale",
    "competition and alternatives",
    "validation and current evidence",
    "commercialisation model",
    "financial model and sensitivities",
    "risks, controls and next steps",
]
FORBIDDEN_TEXT = (
    "/users/",
    "\\users\\",
    "file://",
    "tmp/pdfs",
)
PRIVATE_IDENTIFIER_FINGERPRINTS = frozenset(
    {
        (7, "46d7415f6182ece9e933e8e9f780957e449361e0dbe10e34f46c186cad3382a1"),
        (7, "f910f0bbe95037851d18ca33b91ee7fc9f334c6cfcd02deaf66af4501c8a884c"),
        (9, "7e6578c2e34b53136741c6efe7799a2dce739651c22404a7894b48d42aa88b41"),
        (13, "933536a17b00f1b39ba9d3585427bd7232d44960ab35754318c1da8e4cf6c5be"),
        (25, "40f45830e7e3e21d88245728fe87f76b2e8919543a502aad248a465487cacee3"),
    }
)
FORBIDDEN_ARCHIVE_PARTS = (
    "vbaproject",
    "/embeddings/",
    "/externalLinks/",
    "/oleObject",
    "/comments",
    "connections.xml",
)
SENSITIVE_QUERY_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "authorization",
    "key",
    "password",
    "secret",
    "sig",
    "signature",
    "token",
    "x-amz-credential",
    "x-amz-signature",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def validate_v18_market_bindings(errors: list[str]) -> None:
    try:
        market = load_json(MARKET_VALUES_PATH)
    except ValueError as error:
        errors.append(str(error))
        return
    observations = market.get("observations")
    sources = market.get("sources")
    if not isinstance(observations, list) or len(observations) != 43:
        errors.append("v19 bank package requires exactly 43 market observations")
        return
    if not isinstance(sources, list) or len(sources) != 20:
        errors.append("v19 bank package requires exactly 20 market sources")
    observation_by_id = {
        item.get("observationId"): item
        for item in observations
        if isinstance(item, dict) and isinstance(item.get("observationId"), str)
    }
    if len(observation_by_id) != len(observations):
        errors.append("market observations must have unique string observationId values")
        return
    official = [
        item
        for item in observations
        if isinstance(item.get("countryIso2"), str)
        and str(item.get("evidenceStatus", "")).startswith("official")
    ]
    if len(official) != 34 or {item["countryIso2"] for item in official} != {
        "CA", "DE", "FI", "NZ", "PL", "SE", "US"
    }:
        errors.append("v19 bank package requires 34 official records across seven reviewed countries")

    exact_observations = {
        "NZ-2024-SPECIALIST-RETAIL-SALES-LOWER-BOUND": (
            280_000_000,
            "official_provisional",
            "official_lower_bound_with_quality_warning",
        ),
        "NZ-2024-SPECIALIST-RETAIL-PRODUCT-SALES-RAW-FILE-SUM": (
            280_684_512.81,
            "derived_official_files",
            "reproduced_raw_file_sum_with_quality_warning",
        ),
        "NZ-2024-IDENTIFIED-VAPING-PRODUCT-SALES-RAW-SUM": (
            274_180_410.21,
            "derived_official_files",
            "keyword_classified_raw_file_sum_with_quality_warning",
        ),
        "EU-2023-EC-E-CIGARETTE-MARKET-BENCHMARK": (
            4_990_000_000,
            "institutional_supported",
            "published_secondary_benchmark",
        ),
        "US-2021-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES": (
            2_763_284_338,
            "official_table_derived",
            "official_table_sum",
        ),
    }
    for observation_id, (value, status, finality) in exact_observations.items():
        item = observation_by_id.get(observation_id)
        if (
            not isinstance(item, dict)
            or item.get("value") != value
            or item.get("evidenceStatus") != status
            or item.get("finality") != finality
            or item.get("comparableMarketValue") is not False
            or item.get("atlasEstimate") is not False
        ):
            errors.append(f"v18 reviewed observation binding differs: {observation_id}")

    protocol = market.get("donorProtocol")
    criteria = protocol.get("criteria") if isinstance(protocol, dict) else None
    candidates = market.get("donorCandidates")
    readiness = market.get("meta", {}).get("modelReadiness", {})
    if (
        not isinstance(criteria, list)
        or [item.get("criterionId") for item in criteria] != [f"D{index}" for index in range(1, 11)]
    ):
        errors.append("donor protocol must contain ordered criteria D1-D10")
    if (
        not isinstance(candidates, list)
        or len(candidates) != 5
        or any(item.get("decision") != "not_accepted" for item in candidates)
    ):
        errors.append("all five reviewed donor candidates must remain not accepted")
    if (
        readiness.get("comparableFullYearMarketValueDonors") != 0
        or readiness.get("minimumRequiredDonors") != 3
    ):
        errors.append("accepted-donor gate must remain 0/3")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read {path.relative_to(ROOT)}: {error}") from error


def decimal_value(value: Any) -> Decimal | None:
    if isinstance(value, bool):
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() else None


def validate_artifact_builder_fx_contract(builder_text: str, errors: list[str]) -> None:
    required_tokens = {
        '"site/data/fx-rates.json"': "public FX reviewed input",
        '"site/schemas/fx-rates.schema.json"': "public FX schema reviewed input",
        '"source/fx-rates.json"': "source FX reviewed input",
        '"source/schemas/fx-rates.schema.json"': "source FX schema reviewed input",
        "buildEurEquivalentRows": "data-driven EUR row builder",
        "scenario_component": "country-scenario component rows",
        "market_observation": "market-observation rows",
        '"model"': "market-model rows",
        "compatible_ecb_rate_missing": "missing-rate fail-closed reason",
        '"not_computed"': "missing-rate fail-closed status",
        "eur_equivalent = original_amount / currency_units_per_eur": "reviewed FX formula",
        "`=G${sheetRow}/I${sheetRow}`": "full-precision worksheet formula",
        '"EUR equivalents"': "English EUR-equivalent sheet",
        '"Eurovastineet"': "Finnish EUR-equivalent sheet",
        "[FX methodology]": "deck FX methodology notes",
        "fxSourcesInDeckNotes": "deck-source QA lock",
        "eurEquivalentRowsAfterReopen": "workbook-row QA lock",
    }
    for token, description in required_tokens.items():
        if token not in builder_text:
            errors.append(f"artifact builder lacks {description}: {token}")
    if re.search(r"=ROUND\(\s*G\$\{sheetRow", builder_text, flags=re.IGNORECASE):
        errors.append("artifact builder must not round EUR-equivalent worksheet formulas")


def validate_fx_artifact_inputs(
    public_fx: dict[str, Any],
    source_fx: dict[str, Any],
    errors: list[str],
) -> None:
    if public_fx != source_fx:
        errors.append("artifact FX input differs between source and site/data")
    if not PUBLIC_FX_SCHEMA_PATH.is_file() or not SOURCE_FX_SCHEMA_PATH.is_file():
        errors.append("artifact FX source and public schema files are both required")
    elif PUBLIC_FX_SCHEMA_PATH.read_bytes() != SOURCE_FX_SCHEMA_PATH.read_bytes():
        errors.append("artifact FX source and public schemas differ")
    policy = public_fx.get("calculationPolicy")
    if (
        public_fx.get("targetCurrency") != "EUR"
        or public_fx.get("provider", {}).get("name") != "European Central Bank"
        or not isinstance(policy, dict)
        or policy.get("formulaMachine")
        != "eur_equivalent = original_amount / currency_units_per_eur"
        or policy.get("missingRateStatus") != "not_computed"
        or policy.get("eligibleUnitRule") != "currency_must_equal_unit"
    ):
        errors.append("artifact FX input does not retain the reviewed ECB conversion policy")
    seen: set[tuple[str, int]] = set()
    for rate in public_fx.get("rates", []):
        if not isinstance(rate, dict):
            errors.append("artifact FX input contains a non-object rate")
            continue
        currency = rate.get("currency")
        year = rate.get("year")
        key = (currency, year)
        expected_id = f"ECB-EXR-A-{currency}-EUR-SP00-A-{year}"
        parsed = urlparse(str(rate.get("sourceUrl", "")))
        if (
            key in seen
            or rate.get("rateId") != expected_id
            or decimal_value(rate.get("currencyUnitsPerEur")) is None
            or decimal_value(rate.get("currencyUnitsPerEur")) <= 0
            or parsed.scheme != "https"
            or parsed.hostname != "data-api.ecb.europa.eu"
        ):
            errors.append(f"artifact FX rate is invalid: {currency}/{year}")
        seen.add(key)


def build_expected_eur_equivalent_rows(
    market: dict[str, Any],
    scenarios: dict[str, Any],
    fx: dict[str, Any],
) -> list[dict[str, Any]]:
    rates = {
        (rate.get("currency"), rate.get("year")): rate
        for rate in fx.get("rates", [])
        if isinstance(rate, dict)
    }
    eligible_periods = set(
        fx.get("calculationPolicy", {}).get("eligibleRecordPeriods", [])
    )
    rows: list[dict[str, Any]] = []

    def append(
        record_type: str,
        record_id: Any,
        item: Any,
        geography: Any,
        record: dict[str, Any],
    ) -> None:
        amount = decimal_value(record.get("value"))
        currency = record.get("currency")
        unit = record.get("unit")
        year = record.get("year")
        period = record.get("period")
        if (
            amount is None
            or amount <= 0
            or not isinstance(currency, str)
            or re.fullmatch(r"[A-Z]{3}", currency) is None
            or unit != currency
        ):
            return
        if currency == "EUR":
            status = "already_eur"
            reason = "original_currency_already_eur"
            rate_value: Decimal | None = Decimal("1")
            rate_id: str | None = "EUR-IDENTITY"
            source_url = fx.get("provider", {}).get("methodologyUrl")
        elif not isinstance(year, int) or isinstance(year, bool) or period not in eligible_periods:
            status = "not_computed"
            reason = "period_not_compatible_with_annual_average"
            rate_value = None
            rate_id = None
            source_url = fx.get("provider", {}).get("datasetUrl")
        else:
            rate = rates.get((currency, year))
            rate_value = decimal_value(rate.get("currencyUnitsPerEur")) if rate else None
            if rate_value is None or rate_value <= 0:
                status = "not_computed"
                reason = "compatible_ecb_rate_missing"
                rate_value = None
                rate_id = None
                source_url = fx.get("provider", {}).get("datasetUrl")
            else:
                status = "computed"
                reason = "original_amount_divided_by_ecb_annual_average"
                rate_id = rate.get("rateId")
                source_url = rate.get("sourceUrl")
        rows.append(
            {
                "recordType": record_type,
                "recordId": record_id,
                "item": item,
                "geography": geography,
                "year": year,
                "period": period,
                "originalAmount": amount,
                "currency": currency,
                "rateValue": rate_value,
                "rateId": rate_id,
                "sourceUrl": source_url,
                "status": status,
                "reason": reason,
            }
        )

    for observation in market.get("observations", []):
        if isinstance(observation, dict):
            append(
                "market_observation",
                observation.get("observationId"),
                observation.get("metric"),
                observation.get("geography"),
                observation,
            )

    for scenario in scenarios.get("countryYearScenarios", []):
        if not isinstance(scenario, dict):
            continue
        components = scenario.get("componentBreakdown")
        if not isinstance(components, dict):
            continue
        for range_key, component in components.items():
            if not isinstance(component, dict):
                continue
            for component_key, value in component.items():
                numeric = decimal_value(value)
                if numeric is None or numeric <= 0:
                    continue
                append(
                    "scenario_component",
                    scenario.get("scenarioId"),
                    f"{range_key}.{component_key}",
                    scenario.get("geography"),
                    {
                        "value": value,
                        "currency": scenario.get("currency"),
                        "unit": scenario.get("currency"),
                        "year": scenario.get("year"),
                        "period": "calendar_year",
                    },
                )

    for model in market.get("models", []):
        if not isinstance(model, dict):
            continue
        for bound in ("low", "base", "central", "high"):
            numeric = decimal_value(model.get(bound))
            if numeric is None or numeric <= 0:
                continue
            append(
                "model",
                model.get("modelId"),
                bound,
                model.get("geography"),
                {
                    "value": model.get(bound),
                    "currency": model.get("currency"),
                    "unit": model.get("currency"),
                    "year": model.get("year"),
                    "period": "calendar_year",
                },
            )
    return rows


def load_expected_eur_equivalent_rows(errors: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        market = load_json(MARKET_VALUES_PATH)
        scenarios = load_json(COUNTRY_SCENARIOS_PATH)
        public_fx = load_json(PUBLIC_FX_PATH)
        source_fx = load_json(SOURCE_FX_PATH)
    except ValueError as error:
        errors.append(str(error))
        return [], {}
    validate_fx_artifact_inputs(public_fx, source_fx, errors)
    rows = build_expected_eur_equivalent_rows(market, scenarios, public_fx)
    if not rows:
        errors.append("artifact EUR-equivalent ledger has no eligible rows")
    return rows, public_fx


def deck_fx_markers(
    rows: list[dict[str, Any]],
    language: str,
) -> tuple[str, str, str, str]:
    by_key = {
        (row["recordType"], row["recordId"], row["item"]): row
        for row in rows
    }
    nz_low = by_key.get(
        ("scenario_component", "NZ-2024-RETAIL-RANGE", "low.combinedNzd")
    )
    nz_high = by_key.get(
        ("scenario_component", "NZ-2024-RETAIL-RANGE", "high.combinedNzd")
    )
    ftc = by_key.get(
        (
            "market_observation",
            "US-2021-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES",
            "ftc_reported_cartridge_and_disposable_sales",
        )
    )
    canada_retail = by_key.get(
        (
            "market_observation",
            "CA-2024-STATCAN-RCS-VAPING-RETAIL-SALES",
            "statcan_rcs_vaping_retail_sales",
        )
    )
    canada_shipments = by_key.get(
        (
            "market_observation",
            "CA-2024-MANUFACTURER-IMPORTER-SHIPMENTS-VALUE",
            "manufacturer_importer_shipments_value",
        )
    )
    if not all(
        item
        and item["status"] == "computed"
        and isinstance(item["rateValue"], Decimal)
        and item["rateValue"] > 0
        for item in (nz_low, nz_high, ftc, canada_retail, canada_shipments)
    ):
        return (
            "eur not_computed",
            "eur not_computed",
            "eur not_computed",
            "eur not_computed",
        )
    nz_low_eur = nz_low["originalAmount"] / nz_low["rateValue"]
    nz_high_eur = nz_high["originalAmount"] / nz_high["rateValue"]
    ftc_eur = ftc["originalAmount"] / ftc["rateValue"]
    canada_retail_eur = canada_retail["originalAmount"] / canada_retail["rateValue"]
    canada_shipments_eur = canada_shipments["originalAmount"] / canada_shipments["rateValue"]
    nz_low_display = (nz_low_eur / Decimal("1000000")).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )
    nz_high_display = (nz_high_eur / Decimal("1000000")).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )
    ftc_display = (ftc_eur / Decimal("1000000000")).quantize(
        Decimal("0.001"), rounding=ROUND_HALF_UP
    )
    canada_retail_display = (canada_retail_eur / Decimal("1000000")).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )
    canada_shipments_display = (canada_shipments_eur / Decimal("1000000")).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )
    if language == "fi":
        return (
            f"≈{str(nz_low_display).replace('.', ',')}–"
            f"{str(nz_high_display).replace('.', ',')} milj. eur",
            f"≈{str(ftc_display).replace('.', ',')} mrd eur",
            f"≈{str(canada_retail_display).replace('.', ',')} milj. eur",
            f"≈{str(canada_shipments_display).replace('.', ',')} milj. eur",
        )
    return (
        f"≈eur {nz_low_display}–{nz_high_display}m",
        f"≈eur {ftc_display}bn",
        f"≈eur {canada_retail_display}m",
        f"≈eur {canada_shipments_display}m",
    )


def strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def validate_forbidden_terms(label: str, text: str, errors: list[str]) -> None:
    lowered = text.casefold()
    for phrase in FORBIDDEN_TEXT:
        if phrase in lowered:
            errors.append(f"{label}: forbidden private/local term {phrase!r}")
    normalised = re.sub(r"[^a-z0-9]+", "", lowered)
    for length, expected in PRIVATE_IDENTIFIER_FINGERPRINTS:
        if any(
            hashlib.sha256(normalised[index:index + length].encode("utf-8")).hexdigest() == expected
            for index in range(max(0, len(normalised) - length + 1))
        ):
            errors.append(f"{label}: forbidden private identifier fingerprint")
            break


def validate_text(label: str, text: str, errors: list[str]) -> None:
    validate_forbidden_terms(label, text, errors)
    for match in re.finditer(r"https?://[^\s<>\"']+", text):
        parsed = urlparse(match.group(0).rstrip(".,);]"))
        if parsed.scheme != "https" or not parsed.netloc:
            errors.append(f"{label}: only public HTTPS links are allowed")
            continue
        query_keys = {key.casefold() for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
        if query_keys & SENSITIVE_QUERY_KEYS:
            errors.append(f"{label}: URL contains a sensitive query key")


def validate_external_https_target(label: str, target: str, errors: list[str]) -> None:
    """Require the entire external relationship target to be a safe HTTPS URL."""

    if target != target.strip() or any(character.isspace() or ord(character) < 32 for character in target):
        errors.append(f"{label}: external hyperlink target contains whitespace/control characters")
        return
    if re.search(r"%(?![0-9A-Fa-f]{2})", target):
        errors.append(f"{label}: external hyperlink target contains malformed percent-encoding")
        return
    try:
        parsed = urlparse(target)
        # Accessing port forces urllib to reject malformed or out-of-range ports.
        _ = parsed.port
    except ValueError:
        errors.append(f"{label}: external hyperlink target is malformed")
        return
    if parsed.scheme.casefold() != "https" or not parsed.netloc or not parsed.hostname:
        errors.append(f"{label}: external hyperlink target must be an absolute HTTPS URL")
        return
    if parsed.username is not None or parsed.password is not None:
        errors.append(f"{label}: external hyperlink target must not contain credentials")
    if "\\" in target:
        errors.append(f"{label}: external hyperlink target must not contain backslashes or UNC syntax")
    query_keys = {key.casefold() for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
    if query_keys & SENSITIVE_QUERY_KEYS:
        errors.append(f"{label}: external hyperlink target contains a sensitive query key")
    validate_forbidden_terms(label, target, errors)


def validate_ooxml(
    path: Path,
    errors: list[str],
    *,
    require_deterministic_zip: bool,
    allow_notes: bool,
) -> str:
    label = str(path.relative_to(ROOT))
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if not names or "[Content_Types].xml" not in names:
                errors.append(f"{label}: invalid OOXML package")
                return ""
            if len(names) != len(set(names)):
                errors.append(f"{label}: duplicate ZIP entries")
            if any(name.startswith("/") or ".." in Path(name).parts for name in names):
                errors.append(f"{label}: unsafe ZIP path")
            if require_deterministic_zip:
                if names != sorted(names):
                    errors.append(f"{label}: ZIP entries are not deterministically ordered")
                timestamps = {info.date_time for info in infos}
                if len(timestamps) != 1:
                    errors.append(f"{label}: ZIP timestamps are not normalized")

            extracted_text: list[str] = []
            for info in infos:
                lowered_name = f"/{info.filename}".casefold()
                if any(part.casefold() in lowered_name for part in FORBIDDEN_ARCHIVE_PARTS):
                    errors.append(f"{label}: forbidden OOXML part {info.filename}")
                if info.file_size > 20 * 1024 * 1024:
                    errors.append(f"{label}: oversized OOXML part {info.filename}")
                if info.filename.endswith((".xml", ".rels")):
                    payload = archive.read(info).decode("utf-8", errors="replace")
                    extracted_text.append(payload)
                    is_notes_part = "/notesslides/" in lowered_name or "/notesmasters/" in lowered_name
                    if is_notes_part:
                        if not allow_notes:
                            errors.append(f"{label}: notes parts are forbidden ({info.filename})")
                        elif info.filename.endswith(".xml"):
                            try:
                                ET.fromstring(payload)
                            except ET.ParseError:
                                errors.append(f"{label}: malformed notes part {info.filename}")
                    if info.filename.endswith(".rels"):
                        try:
                            root = ET.fromstring(payload)
                        except ET.ParseError:
                            errors.append(f"{label}: malformed relationship part {info.filename}")
                            continue
                        for relation in root:
                            if relation.attrib.get("TargetMode") != "External":
                                continue
                            target = relation.attrib.get("Target", "")
                            relation_type = relation.attrib.get("Type", "").casefold()
                            if "hyperlink" not in relation_type:
                                errors.append(f"{label}: external non-hyperlink relationship is forbidden")
                            else:
                                validate_external_https_target(f"{label} relationship", target, errors)
            combined = "\n".join(extracted_text)
            # Namespace declarations and relationship type identifiers use HTTP
            # URIs by OOXML design; URL policy applies only to visible content
            # and explicit TargetMode=External relationships.
            validate_forbidden_terms(label, combined, errors)
            return combined
    except (OSError, zipfile.BadZipFile) as error:
        errors.append(f"{label}: unreadable OOXML package: {error}")
        return ""


def slide_texts(path: Path, errors: list[str]) -> list[str]:
    try:
        presentation = Presentation(path)
    except Exception as error:  # python-pptx exposes parser-specific exceptions
        errors.append(f"{path.relative_to(ROOT)}: cannot parse presentation: {error}")
        return []
    output: list[str] = []
    for slide in presentation.slides:
        chunks: list[str] = []
        for shape in slide.shapes:
            if getattr(shape, "has_text_frame", False):
                chunks.append(shape.text)
            if getattr(shape, "has_table", False):
                for row in shape.table.rows:
                    chunks.extend(cell.text for cell in row.cells)
        output.append("\n".join(chunks))
    return output


def validate_slide_source_notes(
    path: Path,
    fx: dict[str, Any],
    errors: list[str],
) -> None:
    label = str(path.relative_to(ROOT))
    rates = {
        (item.get("currency"), item.get("year")): item
        for item in fx.get("rates", [])
        if isinstance(item, dict)
    }
    required_fx_urls = {
        fx.get("provider", {}).get("methodologyUrl"),
        rates.get(("NZD", 2024), {}).get("sourceUrl"),
        rates.get(("USD", 2021), {}).get("sourceUrl"),
        rates.get(("CAD", 2024), {}).get("sourceUrl"),
    } - {None}
    formula = fx.get("calculationPolicy", {}).get("formulaEn")
    try:
        presentation = Presentation(path)
    except Exception as error:
        errors.append(f"{label}: cannot parse presentation notes: {error}")
        return
    for index, slide in enumerate(presentation.slides, start=1):
        if not slide.has_notes_slide or slide.notes_slide.notes_text_frame is None:
            errors.append(f"{label}: slide {index} is missing speaker notes")
            continue
        notes = str(slide.notes_slide.notes_text_frame.text or "").strip()
        validate_text(f"{label} slide {index} notes", notes, errors)
        if "[Sources]" not in notes:
            errors.append(f"{label}: slide {index} notes lack a [Sources] block")
        if not re.search(r"https://[^\s]+", notes):
            errors.append(f"{label}: slide {index} [Sources] block lacks a public HTTPS source")
        if "[FX methodology]" not in notes or not formula or formula not in notes:
            errors.append(f"{label}: slide {index} notes lack the reviewed FX methodology")
        for required_url in required_fx_urls:
            if required_url not in notes:
                errors.append(
                    f"{label}: slide {index} notes lack required FX source {required_url}"
                )


def read_register_csv(
    path: Path,
    headers: list[str],
    allowed_statuses: set[str],
    errors: list[str],
) -> list[list[str]]:
    label = str(path.relative_to(ROOT))
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle))
    except OSError as error:
        errors.append(f"{label}: {error}")
        return []
    if not rows or rows[0] != headers:
        errors.append(f"{label} has incorrect headers")
        return []
    data_rows = [[str(value) for value in row] for row in rows[1:] if any(str(value).strip() for value in row)]
    for index, row in enumerate(data_rows, start=2):
        if len(row) != len(headers):
            errors.append(f"{label} row {index} has {len(row)} columns")
            continue
        if row[7] not in allowed_statuses:
            errors.append(f"{label} row {index} has invalid status {row[7]!r}")
        validate_text(f"{label} row {index}", "\n".join(row), errors)
    if not data_rows:
        errors.append(f"{label} must contain evidence rows")
    elif {row[7] for row in data_rows if len(row) == len(headers)} != allowed_statuses:
        errors.append(f"{label} must visibly use all four evidence classifications")
    return data_rows


def validate_eur_equivalent_sheet(
    workbook: Any,
    language: str,
    expected_rows: list[dict[str, Any]],
    label: str,
    errors: list[str],
) -> None:
    sheet_name = EUR_EQUIVALENT_SHEET_NAMES[language]
    if sheet_name not in workbook.sheetnames:
        errors.append(f"{label}: missing {sheet_name} sheet")
        return
    sheet = workbook[sheet_name]
    headers = [str(sheet.cell(1, column).value or "") for column in range(1, 15)]
    if headers != EUR_EQUIVALENT_HEADERS[language]:
        errors.append(f"{label}: {sheet_name} headers are incorrect")
    actual_rows = [
        row
        for row in sheet.iter_rows(min_row=2, max_col=14)
        if any(cell.value not in (None, "") for cell in row)
    ]
    if len(actual_rows) != len(expected_rows):
        errors.append(
            f"{label}: {sheet_name} row coverage differs "
            f"({len(actual_rows)} != {len(expected_rows)})"
        )
    for index, expected in enumerate(expected_rows, start=2):
        if index - 2 >= len(actual_rows):
            break
        cells = actual_rows[index - 2]
        expected_text = {
            1: expected["recordType"],
            2: expected["recordId"],
            3: expected["item"],
            4: expected["geography"],
            5: expected["year"],
            6: expected["period"],
            8: expected["currency"],
            11: expected["rateId"],
            12: expected["sourceUrl"],
            13: expected["status"],
            14: expected["reason"],
        }
        for column, value in expected_text.items():
            actual = cells[column - 1].value
            if ("" if actual is None else str(actual)) != ("" if value is None else str(value)):
                errors.append(
                    f"{label}: {sheet_name}!{cells[column - 1].coordinate} "
                    "differs from the reviewed FX row"
                )
        actual_amount = decimal_value(cells[6].value)
        if actual_amount != expected["originalAmount"]:
            errors.append(
                f"{label}: {sheet_name}!{cells[6].coordinate} original amount differs"
            )
        actual_rate = decimal_value(cells[8].value)
        if actual_rate != expected["rateValue"]:
            errors.append(
                f"{label}: {sheet_name}!{cells[8].coordinate} ECB rate differs"
            )
        if expected["status"] == "computed":
            expected_formula = f"=G{index}/I{index}"
        elif expected["status"] == "already_eur":
            expected_formula = f"=G{index}"
        else:
            expected_formula = None
        if cells[9].value != expected_formula:
            errors.append(
                f"{label}: {sheet_name}!{cells[9].coordinate} must preserve "
                f"full-precision formula {expected_formula!r}"
            )
        source_url = str(cells[11].value or "")
        parsed = urlparse(source_url)
        if expected["status"] == "computed":
            if (
                not str(cells[10].value or "").startswith("ECB-EXR-A-")
                or parsed.scheme != "https"
                or parsed.hostname != "data-api.ecb.europa.eu"
            ):
                errors.append(
                    f"{label}: {sheet_name} row {index} lacks direct ECB rateId/source URL"
                )
        elif expected["status"] == "not_computed":
            if cells[9].value is not None or cells[10].value not in (None, ""):
                errors.append(
                    f"{label}: {sheet_name} row {index} must fail closed without an EUR value/rateId"
                )


def validate_workbook(
    path: Path,
    csv_rows: list[list[str]],
    expected_headers: list[str],
    expected_eur_rows: list[dict[str, Any]],
    errors: list[str],
) -> int:
    label = str(path.relative_to(ROOT))
    try:
        workbook = load_workbook(path, data_only=False, read_only=False)
    except Exception as error:
        errors.append(f"{label}: cannot parse workbook: {error}")
        return 0
    if "Evidence Register" not in workbook.sheetnames:
        errors.append(f"{label}: missing Evidence Register sheet")
        return 0
    for sheet in workbook.worksheets:
        if sheet.sheet_state != "visible":
            errors.append(f"{label}: hidden worksheets are forbidden ({sheet.title})")
        for row in sheet.iter_rows():
            for cell in row:
                if cell.comment is not None:
                    errors.append(f"{label}: comments are forbidden ({sheet.title}!{cell.coordinate})")
                if isinstance(cell.value, str):
                    validate_text(f"{label} {sheet.title}!{cell.coordinate}", cell.value, errors)
                    if cell.value.startswith("=") and "[" in cell.value:
                        errors.append(f"{label}: external workbook formula is forbidden")
                if cell.hyperlink is not None:
                    validate_text(f"{label} hyperlink", str(cell.hyperlink.target), errors)
    sheet = workbook["Evidence Register"]
    headers = [str(sheet.cell(1, column).value or "") for column in range(1, 10)]
    if headers != expected_headers:
        errors.append(f"{label}: Evidence Register headers are incorrect")
    workbook_rows: list[list[str]] = []
    for values in sheet.iter_rows(min_row=2, max_col=9, values_only=True):
        row = ["" if value is None else str(value) for value in values]
        if any(value.strip() for value in row):
            workbook_rows.append(row)
    if workbook_rows != csv_rows:
        errors.append(f"{label}: Evidence Register rows differ from the public CSV")
    is_finnish = expected_headers == REGISTER_HEADERS
    summary_name = "Yhteenveto" if is_finnish else "Summary"
    if summary_name not in workbook.sheetnames:
        errors.append(f"{label}: missing {summary_name} sheet")
    else:
        summary = workbook[summary_name]
        evidence_end = len(csv_rows) + 1
        expected_formulas = {
            "B8": f"=COUNTA('Evidence Register'!$A$2:$A${evidence_end})",
            **{
                f"B{row}": f"=COUNTIF('Evidence Register'!$H$2:$H${evidence_end},A{row})"
                for row in range(11, 15)
            },
        }
        for coordinate, formula in expected_formulas.items():
            if summary[coordinate].value != formula:
                errors.append(f"{label}: {summary_name}!{coordinate} must preserve formula {formula}")

    sources_name = "Lähteet" if is_finnish else "Sources"
    if sources_name not in workbook.sheetnames:
        errors.append(f"{label}: missing {sources_name} sheet")
    else:
        sources_sheet = workbook[sources_name]
        source_urls = {
            str(sources_sheet.cell(row, 4).value or "").strip()
            for row in range(2, sources_sheet.max_row + 1)
            if str(sources_sheet.cell(row, 4).value or "").strip()
        }
        register_urls = {
            match.group(0).rstrip(".,);]")
            for row in csv_rows
            for match in re.finditer(r"https://[^\s;]+", row[3])
        }
        missing_urls = sorted(register_urls - source_urls)
        if missing_urls:
            errors.append(f"{label}: {sources_name} omits register URLs: {missing_urls}")
        for required_url in {
            "https://www.ftc.gov/reports/e-cigarette-report-2015-2018",
            "https://www.ftc.gov/reports/e-cigarette-report-2021",
            "https://www.un.org/en/about-us/member-states",
            "https://www.un.org/en/about-us/non-member-states",
        }:
            if required_url not in source_urls:
                errors.append(f"{label}: {sources_name} lacks required source {required_url}")

    nz_prefix = (
        "Uuden-Seelannin vuoden 2024 tunnistetun"
        if is_finnish
        else "New Zealand's supported 2024 identified"
    )
    nz_row = next(
        (index for index, row in enumerate(csv_rows, start=2) if row[0].startswith(nz_prefix)),
        None,
    )
    if nz_row is None:
        errors.append(f"{label}: supported New Zealand model row is missing")
    else:
        row_height = sheet.row_dimensions[nz_row].height
        if row_height is None or row_height < 80:
            errors.append(f"{label}: supported New Zealand model row lacks the expanded review treatment")
        if sheet[f"F{nz_row}"].fill.fill_type is None:
            errors.append(f"{label}: supported New Zealand calculation cell lacks the review highlight")
    validate_eur_equivalent_sheet(
        workbook,
        "fi" if is_finnish else "en",
        expected_eur_rows,
        label,
        errors,
    )
    return len(workbook_rows)


def validate_manifest(errors: list[str]) -> None:
    expected_eur_rows, fx = load_expected_eur_equivalent_rows(errors)
    try:
        builder_text = ARTIFACT_BUILDER_PATH.read_text(encoding="utf-8")
    except OSError as error:
        errors.append(f"cannot read artifact builder: {error}")
        builder_text = ""
    validate_artifact_builder_fx_contract(builder_text, errors)
    try:
        manifest = load_json(MANIFEST_PATH)
        changelog = load_json(CHANGELOG_PATH)
        lock = load_json(LOCK_PATH)
    except ValueError as error:
        errors.append(str(error))
        return
    expected_keys = {
        "schemaVersion",
        "generatedFromPublicDataOnly",
        "release",
        "asOf",
        "languages",
        "publicBoundary",
        "templateInputs",
        "inputs",
        "artifacts",
    }
    if not isinstance(manifest, dict) or set(manifest) != expected_keys:
        errors.append("bank-package-manifest.json has an unexpected schema")
        return
    if manifest.get("schemaVersion") != 2 or manifest.get("generatedFromPublicDataOnly") is not True:
        errors.append("manifest must declare schemaVersion 2 and public-data-only generation")
    if manifest.get("languages") != ["en", "fi"]:
        errors.append("manifest languages must be exactly en and fi")
    latest_release = changelog.get("releases", [{}])[0]
    expected_release = {
        key: latest_release.get(key) for key in ("id", "version", "publishedAt")
    }
    if manifest.get("release") != expected_release:
        errors.append("manifest release must match the newest public changelog release")
    if manifest.get("asOf") != changelog.get("asOf"):
        errors.append("manifest asOf must match the public changelog")
    if (
        expected_release.get("id") != "2026-07-24-canada-retail-closure-board-v19"
        or expected_release.get("version") != "2026.07.24-19"
        or manifest.get("asOf") != "2026-07-24"
    ):
        errors.append("bank package must be locked to release 2026.07.24-19 as of 2026-07-24")
    boundary = manifest.get("publicBoundary")
    if not isinstance(boundary, dict) or set(boundary) != {"en", "fi"}:
        errors.append("manifest publicBoundary must contain exactly en and fi")
    else:
        boundary_text = " ".join(str(value) for value in boundary.values())
        validate_text("manifest public boundary", boundary_text, errors)
        if "public" not in str(boundary.get("en", "")).casefold() or "julk" not in str(boundary.get("fi", "")).casefold():
            errors.append("manifest must state the public-data boundary in both languages")

    template_inputs = manifest.get("templateInputs")
    if not isinstance(template_inputs, list):
        errors.append("manifest templateInputs must be an array")
        template_inputs = []
    template_by_path = {
        item.get("path"): item
        for item in template_inputs
        if isinstance(item, dict) and set(item) == {"path", "sha256"}
    }
    if set(template_by_path) != EXPECTED_TEMPLATE_INPUTS or len(template_by_path) != len(template_inputs):
        errors.append("manifest templateInputs must contain the exact reviewed seed artifacts")
    for relative, item in template_by_path.items():
        seed_path = ROOT / relative
        if not seed_path.is_file():
            errors.append(f"manifest seed artifact is missing: {relative}")
        elif item.get("sha256") != sha256(seed_path):
            errors.append(f"manifest seed artifact hash differs: {relative}")

    generated_by = lock.get("generatedBy") if isinstance(lock, dict) else None
    if not isinstance(generated_by, dict):
        errors.append("bank-package lock lacks generatedBy lineage")
    else:
        if generated_by.get("tool") != "@oai/artifact-tool":
            errors.append("bank-package lock must identify @oai/artifact-tool")
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", str(generated_by.get("toolVersion", ""))):
            errors.append("bank-package lock must record the runtime-resolved artifact-tool version")
        lock_templates = generated_by.get("sourceTemplates")
        if lock_templates != template_inputs:
            errors.append("bank-package lock sourceTemplates must match manifest templateInputs")
        quality = generated_by.get("qualityAssurance")
        if not isinstance(quality, dict) or any(
            quality.get(key) is not True
            for key in (
                "summaryFormulasAfterReopen",
                "allSlidesRendered",
                "allWorkbookSheetsRendered",
                "sourcesNotesOnEverySlide",
                "eurEquivalentRowsAfterReopen",
                "fxSourcesInDeckNotes",
            )
        ):
            errors.append("bank-package lock lacks required artifact QA lineage")

    if 'toolVersion: artifactToolVersion' not in builder_text or 'toolVersion: "2.8.' in builder_text:
        errors.append("artifact builder must derive the artifact-tool version at runtime")

    inputs = manifest.get("inputs")
    if not isinstance(inputs, list):
        errors.append("manifest inputs must be an array")
        inputs = []
    input_by_path = {
        item.get("path"): item for item in inputs if isinstance(item, dict) and set(item) == {"path", "sha256"}
    }
    if set(input_by_path) != EXPECTED_INPUTS or len(input_by_path) != len(inputs):
        errors.append("manifest inputs must be the exact reviewed public-data allowlist")
    for relative, item in input_by_path.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"manifest input is missing: {relative}")
        elif item.get("sha256") != sha256(path):
            errors.append(f"manifest input hash differs: {relative}")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("manifest artifacts must be an array")
        artifacts = []
    artifact_by_id = {
        item.get("id"): item
        for item in artifacts
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if set(artifact_by_id) != set(EXPECTED_ARTIFACTS) or len(artifact_by_id) != len(artifacts):
        errors.append("manifest artifacts must contain exactly the eight approved downloads")

    csv_rows_by_language = {
        "fi": read_register_csv(REGISTER_CSV_PATH, REGISTER_HEADERS, ALLOWED_STATUSES, errors),
        "en": read_register_csv(EN_REGISTER_CSV_PATH, EN_REGISTER_HEADERS, EN_ALLOWED_STATUSES, errors),
    }
    if any(len(rows) != 53 for rows in csv_rows_by_language.values()):
        errors.append("both v19 Evidence Registers must contain exactly 53 reviewed rows")
    register_markers = {
        "fi": (
            "280 684 512,81",
            "274 180 410,21",
            "258 327 110,88 + 275 335 272,80 = 533 662 383,68",
            "274 180 410,21 + 367 631 277,68 = 641 811 687,89",
            "274 180 410,21 + 456 995 382,29 = 731 175 792,50",
            "533 662 383,68",
            "731 175 792,50",
            "2 763 284 338",
            "4,99 mrd",
            "1 219 160 000",
            "5,03 %",
            "D1–D10",
        ),
        "en": (
            "280,684,512.81",
            "274,180,410.21",
            "258,327,110.88 + 275,335,272.80 = 533,662,383.68",
            "274,180,410.21 + 367,631,277.68 = 641,811,687.89",
            "274,180,410.21 + 456,995,382.29 = 731,175,792.50",
            "533,662,383.68",
            "731,175,792.50",
            "2,763,284,338",
            "4.99 billion",
            "1,219,160,000",
            "5.03%",
            "D1–D10",
        ),
    }
    for language, rows in csv_rows_by_language.items():
        joined = "\n".join("\t".join(row) for row in rows)
        for marker in register_markers[language]:
            if marker not in joined:
                errors.append(f"{language} Evidence Register lacks v18 marker {marker!r}")
    errors.extend(
        validate_register_parity(
            csv_rows_by_language["fi"],
            csv_rows_by_language["en"],
        )
    )
    headers_by_language = {"fi": REGISTER_HEADERS, "en": EN_REGISTER_HEADERS}
    for artifact_id, expected in EXPECTED_ARTIFACTS.items():
        item = artifact_by_id.get(artifact_id)
        if not isinstance(item, dict):
            continue
        required = {"id", "kind", "language", "titleFi", "titleEn", "fileName", "path", "sha256", "bytes"}
        if expected["kind"] == "pptx":
            required.add("slideCount")
        else:
            required.add("rowCount")
        if set(item) != required:
            errors.append(f"manifest artifact {artifact_id} has an unexpected schema")
        if (
            item.get("kind") != expected["kind"]
            or item.get("language") != expected["language"]
            or item.get("path") != expected["path"]
        ):
            errors.append(f"manifest artifact {artifact_id} kind/language/path differs from allowlist")
        if item.get("fileName") != Path(expected["path"]).name:
            errors.append(f"manifest artifact {artifact_id} filename differs from path")
        if not str(item.get("titleFi", "")).strip() or not str(item.get("titleEn", "")).strip():
            errors.append(f"manifest artifact {artifact_id} requires bilingual titles")
        relative = str(item.get("path", ""))
        path = ROOT / "site" / relative
        if path.parent != ROOT / "site" / "downloads" or not path.is_file():
            errors.append(f"download missing or outside allowlist: {relative}")
            continue
        if path.stat().st_size > 12 * 1024 * 1024:
            errors.append(f"{relative}: file exceeds 12 MiB")
        if item.get("bytes") != path.stat().st_size:
            errors.append(f"{relative}: manifest byte count differs")
        if not SHA256_RE.fullmatch(str(item.get("sha256", ""))) or item.get("sha256") != sha256(path):
            errors.append(f"{relative}: manifest SHA-256 differs")
        is_english = expected["language"] == "en"
        validate_ooxml(
            path,
            errors,
            require_deterministic_zip=False,
            allow_notes=expected["kind"] == "pptx",
        )
        if expected["kind"] == "pptx":
            validate_slide_source_notes(path, fx, errors)
            texts = slide_texts(path, errors)
            if len(texts) != expected["slideCount"] or item.get("slideCount") != expected["slideCount"]:
                errors.append(f"{relative}: expected exactly {expected['slideCount']} slides")
            for index, text in enumerate(texts, start=1):
                if not text.strip():
                    errors.append(f"{relative}: slide {index} has no readable text")
                validate_text(f"{relative} slide {index}", text, errors)
            combined = "\n".join(texts).casefold()
            expected_boundary = "independent public evidence" if is_english else "julkinen riippumaton"
            if expected_boundary not in combined:
                errors.append(f"{relative}: public-boundary disclosure is missing")
            v18_deck_markers = (
                (
                    "533,7–731,2 milj. nzd",
                    "2,763 mrd usd",
                    "4,99 mrd eur",
                    "34",
                    "7 maasta",
                    "0/3",
                    "d1–d10",
                    "1,219 mrd cad",
                    "2026.07.24-19",
                )
                if not is_english
                else (
                    "nzd 533.7–731.2m",
                    "usd 2.763bn",
                    "eur 4.99bn",
                    "34",
                    "7 countries",
                    "0/3",
                    "d1–d10",
                    "cad 1.219bn",
                    "2026.07.24-19",
                )
            )
            fx_markers = deck_fx_markers(
                expected_eur_rows,
                "en" if is_english else "fi",
            )
            v18_deck_markers = (*v18_deck_markers, *fx_markers)
            for marker in v18_deck_markers:
                if marker not in combined:
                    errors.append(f"{relative}: v18 market marker is missing: {marker!r}")
            if artifact_id in {"medium-deck-fi", "medium-deck-en"} and len(texts) == 12:
                titles = EN_MEDIUM_SECTION_TITLES if is_english else MEDIUM_SECTION_TITLES
                for index, expected_title in enumerate(titles):
                    normalized = " ".join(texts[index].casefold().split())
                    if expected_title not in normalized:
                        errors.append(
                            f"{relative}: slide {index + 1} lacks requested section title {expected_title!r}"
                        )
        else:
            csv_rows = csv_rows_by_language[expected["language"]]
            row_count = validate_workbook(
                path,
                csv_rows,
                headers_by_language[expected["language"]],
                expected_eur_rows,
                errors,
            )
            if item.get("rowCount") != row_count or row_count != len(csv_rows):
                errors.append(f"{relative}: manifest/workbook/CSV row counts differ")


def main() -> None:
    errors: list[str] = []
    validate_v18_market_bindings(errors)
    validate_manifest(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Bank-package validation failed with {len(errors)} error(s).", file=sys.stderr)
        raise SystemExit(1)
    print(
        "Validated bilingual public bank package: English and Finnish 6/12/30-slide decks, "
        "Evidence Register parity, release-lock and SHA-256 integrity, safe OOXML and public-data-only boundary."
    )


if __name__ == "__main__":
    main()
