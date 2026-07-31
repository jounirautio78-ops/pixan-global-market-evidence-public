#!/usr/bin/env python3
"""Fail-closed validation for the public vendor-response control."""

from __future__ import annotations

import csv
from datetime import date
import io
import json
from pathlib import Path
import re
import sys
from typing import Any

from public_privacy_guard import contains_private_identifier
from build_vendor_response_control import (
    CSV_FIELDS,
    OUTPUT_CSV,
    OUTPUT_JSON,
    SOURCE_PATH,
    normalised,
    render_csv,
    render_json,
    score_vendor,
)


ROOT = Path(__file__).resolve().parents[1]
REVIEW_HTML = ROOT / "site" / "review.html"
VENDOR_SCRIPT = ROOT / "site" / "assets" / "vendor-response.js"
RECEIPT_LEDGER_HOOKS = (
    "function receiptLabel(",
    "function renderReceiptLedger(",
    "vendor.receivedEvidence",
    "vendor.evidenceReceivedCount",
    "control.evidenceTypes",
    "vendor-response-receipts",
    "vendor-response-receipt-list",
    "Material receipt does not establish completeness or gate passage.",
    "Aineiston vastaanotto ei osoita täydellisyyttä eikä portin läpäisyä.",
    "Rights-related material",
    "Commercial-terms material",
)

TOP_LEVEL_KEYS = {
    "schemaVersion",
    "controlId",
    "asOf",
    "version",
    "status",
    "publicBoundaryEn",
    "publicBoundaryFi",
    "scoreBoundaryEn",
    "scoreBoundaryFi",
    "scoreScale",
    "germanyBenchmark",
    "criteria",
    "mandatoryGates",
    "evidenceTypes",
    "vendors",
}
OUTPUT_TOP_LEVEL_KEYS = TOP_LEVEL_KEYS | {"summary"}
CRITERION_WEIGHTS = {
    "annualCountrySeriesFit": 0.20,
    "metricScopeClarity": 0.15,
    "coverage": 0.15,
    "methodTransparency": 0.15,
    "auditability": 0.10,
    "transactionLicenceFit": 0.15,
    "commercialClarity": 0.10,
}
EVIDENCE_KEYS = {
    "sample",
    "methodology",
    "coverageMatrix",
    "quote",
    "officialAnchorReconciliation",
    "transactionUseRights",
    "totalCostTerms",
}
MANDATORY_GATE_RULES = {
    "G1": {
        "evidenceKey": "sample",
        "allowedReasons": {
            "EVIDENCE_NOT_RECEIVED",
            "ROUTE_NOT_SUBMITTED",
            "SAMPLE_REQUIRED_YEARS_MISSING",
            "SAMPLE_REQUIRED_METRICS_INCOMPLETE",
        },
    },
    "G2": {
        "evidenceKey": "methodology",
        "allowedReasons": {
            "EVIDENCE_NOT_RECEIVED",
            "ROUTE_NOT_SUBMITTED",
            "METHOD_COUNTRY_DETAIL_MISSING",
            "METHOD_RECORD_STATUS_FLAGS_MISSING",
        },
    },
    "G3": {
        "evidenceKey": "coverageMatrix",
        "allowedReasons": {
            "EVIDENCE_NOT_RECEIVED",
            "ROUTE_NOT_SUBMITTED",
            "COVERAGE_MATRIX_NOT_RECEIVED",
            "COVERAGE_MATRIX_CATEGORY_DETAIL_INCOMPLETE",
        },
    },
    "G4": {
        "evidenceKey": "officialAnchorReconciliation",
        "allowedReasons": {
            "EVIDENCE_NOT_RECEIVED",
            "ROUTE_NOT_SUBMITTED",
            "ANCHOR_COMPARABLE_SERIES_MISSING",
            "ANCHOR_SCOPE_STAGE_BRIDGE_MISSING",
        },
    },
    "G5": {
        "evidenceKey": "transactionUseRights",
        "allowedReasons": {
            "EVIDENCE_NOT_RECEIVED",
            "ROUTE_NOT_SUBMITTED",
            "RIGHTS_ONWARD_SHARING_UNCONFIRMED",
            "RIGHTS_DATA_ROOM_UNCONFIRMED",
        },
    },
    "G6": {
        "evidenceKey": "totalCostTerms",
        "allowedReasons": {
            "EVIDENCE_NOT_RECEIVED",
            "ROUTE_NOT_SUBMITTED",
            "COMMERCIAL_TOTAL_COST_INCOMPLETE",
            "COMMERCIAL_EXPORT_AND_RETENTION_UNCONFIRMED",
            "COMMERCIAL_SELECTED_SCOPE_PRICE_PENDING",
            "COMMERCIAL_SPECIAL_USE_FEES_UNPRICED",
        },
    },
}
MANDATORY_GATE_IDS = set(MANDATORY_GATE_RULES)
MANDATORY_GATE_KEYS = {
    rule["evidenceKey"] for rule in MANDATORY_GATE_RULES.values()
}
GATE_STATUSES = {"pass", "fail", "not_testable", "missing"}
REASON_CODE_STATUSES = {
    "EVIDENCE_NOT_RECEIVED": {"missing"},
    "ROUTE_NOT_SUBMITTED": {"missing"},
    "SAMPLE_REQUIRED_YEARS_MISSING": {"not_testable"},
    "SAMPLE_REQUIRED_METRICS_INCOMPLETE": {"not_testable"},
    "METHOD_COUNTRY_DETAIL_MISSING": {"fail"},
    "METHOD_RECORD_STATUS_FLAGS_MISSING": {"fail"},
    "COVERAGE_MATRIX_NOT_RECEIVED": {"missing"},
    "COVERAGE_MATRIX_CATEGORY_DETAIL_INCOMPLETE": {"fail"},
    "ANCHOR_COMPARABLE_SERIES_MISSING": {"not_testable"},
    "ANCHOR_SCOPE_STAGE_BRIDGE_MISSING": {"not_testable"},
    "RIGHTS_ONWARD_SHARING_UNCONFIRMED": {"fail"},
    "RIGHTS_DATA_ROOM_UNCONFIRMED": {"fail"},
    "COMMERCIAL_TOTAL_COST_INCOMPLETE": {"fail"},
    "COMMERCIAL_EXPORT_AND_RETENTION_UNCONFIRMED": {"fail"},
    "COMMERCIAL_SELECTED_SCOPE_PRICE_PENDING": {"fail"},
    "COMMERCIAL_SPECIAL_USE_FEES_UNPRICED": {"fail"},
}
GERMANY_BENCHMARK_KEYS = {
    "benchmarkId",
    "countryIso2",
    "scopeEn",
    "scopeFi",
    "unit",
    "status",
    "statusReasonEn",
    "statusReasonFi",
    "officialAnchors",
    "thresholds",
    "requiredEvidence",
    "vendorPassDoesNotEstablishDonorPass",
    "donorGateEffect",
    "donorBoundaryEn",
    "donorBoundaryFi",
}
GERMANY_ANCHOR_KEYS = {
    "observationId",
    "sourceId",
    "year",
    "value",
    "unit",
    "finality",
    "role",
}
EXPECTED_GERMANY_ANCHORS = {
    2023: {
        "observationId": "DE-2023-TAXED-LIQUID-VOLUME-L",
        "sourceId": "DE-DESTATIS-73411-0003",
        "value": 1_241_000,
        "unit": "litre",
        "finality": "final",
        "role": "pass_test",
    },
    2024: {
        "observationId": "DE-2024-TAXED-LIQUID-VOLUME-L",
        "sourceId": "DE-DESTATIS-73411-0003",
        "value": 1_284_000,
        "unit": "litre",
        "finality": "final",
        "role": "pass_test",
    },
    2025: {
        "observationId": "DE-2025-TAXED-LIQUID-VOLUME-L",
        "sourceId": "DE-DESTATIS-73411-0003",
        "value": 1_518_000,
        "unit": "litre",
        "finality": "provisional",
        "role": "context_only",
    },
}
GERMANY_REQUIRED_EVIDENCE_IDS = {
    "productSplits",
    "definitions",
    "taxBasis",
    "methodology",
    "brandFields",
    "transactionUseRights",
    "commercialTerms",
}


def uniform_missing_gate_results(reason_code: str) -> dict[str, dict[str, Any]]:
    return {
        gate_id: {"status": "missing", "reasonCodes": [reason_code]}
        for gate_id in MANDATORY_GATE_RULES
    }


EUROMONITOR_GATE_RESULTS = {
    "G1": {
        "status": "not_testable",
        "reasonCodes": [
            "SAMPLE_REQUIRED_YEARS_MISSING",
            "SAMPLE_REQUIRED_METRICS_INCOMPLETE",
        ],
    },
    "G2": {
        "status": "fail",
        "reasonCodes": [
            "METHOD_COUNTRY_DETAIL_MISSING",
            "METHOD_RECORD_STATUS_FLAGS_MISSING",
        ],
    },
    "G3": {
        "status": "fail",
        "reasonCodes": ["COVERAGE_MATRIX_CATEGORY_DETAIL_INCOMPLETE"],
    },
    "G4": {
        "status": "not_testable",
        "reasonCodes": ["ANCHOR_SCOPE_STAGE_BRIDGE_MISSING"],
    },
    "G5": {
        "status": "fail",
        "reasonCodes": [
            "RIGHTS_ONWARD_SHARING_UNCONFIRMED",
            "RIGHTS_DATA_ROOM_UNCONFIRMED",
        ],
    },
    "G6": {
        "status": "fail",
        "reasonCodes": [
            "COMMERCIAL_TOTAL_COST_INCOMPLETE",
            "COMMERCIAL_EXPORT_AND_RETENTION_UNCONFIRMED",
            "COMMERCIAL_SPECIAL_USE_FEES_UNPRICED",
        ],
    },
}
EMPTY_RECEIPTS = {key: False for key in EVIDENCE_KEYS}
EUROMONITOR_RECEIPTS = {
    "sample": True,
    "methodology": True,
    "coverageMatrix": True,
    "quote": True,
    "officialAnchorReconciliation": False,
    "transactionUseRights": True,
    "totalCostTerms": True,
}
EXPECTED_VENDORS = {
    "ecig-global-market-database": {
        "vendor": "ECigIntelligence",
        "product": "Global Market Database",
        "requestState": "request_sent",
        "responseState": "pending_no_acknowledgement",
        "publicStatusEn": (
            "Request sent 2026-07-23; first follow-up sent 2026-07-28. No response "
            "or evidence is recorded. NOT SCORED; no purchase, fee or commitment is authorised."
        ),
        "publicStatusFi": (
            "Pyyntö lähetettiin 23.7.2026 ja ensimmäinen seuranta 28.7.2026. Vastausta "
            "tai evidenssiä ei ole kirjattu. EI PISTEYTETTY; ostoa, maksua tai sitoumusta "
            "ei ole valtuutettu."
        ),
        "quoteReceived": False,
        "receivedEvidence": EMPTY_RECEIPTS,
        "gateResults": uniform_missing_gate_results("EVIDENCE_NOT_RECEIVED"),
    },
    "euromonitor-passport-nicotine": {
        "vendor": "Euromonitor International",
        "product": "Passport Nicotine / e-vapour country series",
        "requestState": "request_sent",
        "responseState": "substantive_response_received",
        "publicStatusEn": (
            "An expanded numerical Germany sample, a 78-market e-vapour value-coverage list, "
            "generic methodology, standard licence terms, three indicative annual package quotes "
            "and a later eight-tab category-schema workbook were received by 2026-07-27. The earlier "
            "sample permits a private 2023–2024 liquid-volume comparison. The later workbook exposes "
            "market-size, company/brand, channel, nicotine-strength, user and category structures "
            "across 95 listed geographies, but the supplied country-year value cells are unpopulated "
            "and the 95-geography structure is not reconciled to the 78-country quote. The vendor "
            "clarified end-consumer sales including applied product taxes/VAT, enterprise-AI use "
            "where provider training is disabled and availability of modelled Cyprus volume. "
            "Record-level observed/reported/modelled flags, the exact product-scope bridge, "
            "lender/buyer data-room rights and all-in tax, fee, retention and renewal terms remain "
            "unconfirmed. A populated Germany 2022–2025 test, field-year coverage reconciliation "
            "and proposed Special Condition remain open. A 2026-07-29 call was completed. The vendor "
            "then offered a limited Germany extract under a conditional "
            "paid arrangement: the extract fee would be waived only if a wider country package were "
            "purchased within the stated window; otherwise the extract could be invoiced. No extract, "
            "order, invoice, fee, subscription or commitment is authorised or accepted. The private "
            "Germany comparison remains non-testable because the product scope, retail-versus-tax "
            "stage and record-status bridge is unresolved. All six gates are evaluated, but none "
            "passes. NOT SCORED."
        ),
        "publicStatusFi": (
            "Laajennettu numeerinen Saksa-näyte, 78 sähkötupakkamarkkinan arvotietojen peittolista, "
            "yleinen menetelmäkuvaus, vakiolisenssiehdot, kolme suuntaa-antavaa vuosipakettitarjousta "
            "ja myöhempi kahdeksan välilehden kategoriaskeematyökirja saatiin 27.7.2026 mennessä. "
            "Aiempi näyte mahdollistaa yksityisen vuosien 2023–2024 nestemäärävertailun. Myöhempi "
            "työkirja näyttää markkinakoko-, yhtiö-/brändi-, kanava-, nikotiinivahvuus-, käyttäjä- "
            "ja kategoriarakenteet 95 luetellulle maantieteelle, mutta toimitetun kopion maa–vuosi-"
            "arvosolut ovat tyhjiä eikä 95 maantieteen rakennetta ole täsmäytetty 78 maan tarjoukseen. "
            "Toimittaja täsmensi lukujen kuvaavan loppuasiakasmyyntiä sovellettavine tuoteveroineen "
            "ja ALV:ineen, salli yritystason tekoälykäsittelyn ilman palveluntarjoajan mallikoulutusta "
            "ja ilmoitti Kyprokselle olevan saatavissa mallinnettuja volyymeja. Tietuekohtaiset "
            "havaittu/raportoitu/mallinnettu-merkinnät, täsmällinen tuoterajaussilta, lainanantaja-/"
            "ostaja-datahuoneoikeudet sekä kaikki verot, maksut, säilytys- ja uusimisehdot kattavat "
            "ehdot ovat vahvistamatta. Täytetty Saksan 2022–2025-testi, kenttä–vuosi-peiton täsmäytys "
            "ja ehdotettu erityisehto ovat avoinna. Puhelu pidettiin 29.7.2026. Toimittaja tarjosi "
            "sen jälkeen rajattua Saksa-otetta "
            "ehdollisella maksullisella järjestelyllä: otteen maksu poistuisi vain, jos laajempi "
            "maapaketti ostettaisiin ilmoitetun määräajan kuluessa; muutoin ote voitaisiin laskuttaa. "
            "Otetta, tilausta, laskua, maksua tai sitoumusta ei ole valtuutettu tai hyväksytty. "
            "Yksityinen Saksa-vertailu ei ole vielä testattavissa, koska tuoterajaus, vähittäis- ja "
            "verovaiheen ero sekä tietueiden tilasilta ovat ratkaisematta. Kaikki kuusi porttia on "
            "arvioitu, mutta yksikään ei läpäise. EI PISTEYTETTY."
        ),
        "quoteReceived": True,
        "receivedEvidence": EUROMONITOR_RECEIPTS,
        "gateResults": EUROMONITOR_GATE_RESULTS,
    },
    "niq-rms-pilot": {
        "vendor": "NielsenIQ",
        "product": "Retail Measurement Services pilot",
        "requestState": "not_submitted_terms_gate",
        "responseState": "not_submitted",
        "publicStatusEn": "Not submitted; terms gate",
        "publicStatusFi": "Ei lähetetty; ehtoraja",
        "quoteReceived": False,
        "receivedEvidence": EMPTY_RECEIPTS,
        "gateResults": uniform_missing_gate_results("ROUTE_NOT_SUBMITTED"),
    },
    "circana-us-tobacco-pilot": {
        "vendor": "Circana",
        "product": "US Tobacco POS pilot",
        "requestState": "submission_confirmed",
        "responseState": "commercial_qualification_response_received",
        "publicStatusEn": (
            "A commercial qualification response was received on 2026-07-27, and a same-thread "
            "clarification was sent on 2026-07-28. The vendor stated that retailer-level detail is "
            "not typically available and provided only non-binding indicative cost guidance, not a project-"
            "specific quote. A populated real-data sample, data dictionary and methodology, "
            "explicit channel coverage, a definitive lowest-cost scoped quote and written "
            "transaction-use rights remain pending. NOT SCORED; no activation, invoice, "
            "subscription, purchase, fee or commitment is authorised."
        ),
        "publicStatusFi": (
            "Kaupallista rajausta koskeva vastaus saatiin 27.7.2026, ja samaan ketjuun lähetettiin "
            "täsmennys 28.7.2026. Toimittaja ilmoitti, ettei jälleenmyyjäkohtaista tietoa "
            "tyypillisesti ole saatavilla, ja antoi vain sitomattoman suuntaa-antavan kustannusohjeen, ei "
            "projektikohtaista tarjousta. Täytetty reaalidatanäyte, tietosanasto ja "
            "menetelmäkuvaus, nimenomainen kanavapeitto, lopullinen halvimman rajatun vaihtoehdon "
            "tarjous ja kirjalliset transaktiokäyttöoikeudet odottavat. EI PISTEYTETTY; "
            "aktivointia, laskua, tilausta, ostoa, maksua tai sitoumusta ei ole valtuutettu."
        ),
        "quoteReceived": False,
        "receivedEvidence": EMPTY_RECEIPTS,
        "gateResults": uniform_missing_gate_results("EVIDENCE_NOT_RECEIVED"),
    },
}
VENDOR_KEYS = {
    "vendorId",
    "vendor",
    "product",
    "requestState",
    "responseState",
    "publicStatusEn",
    "publicStatusFi",
    "quoteReceived",
    "receivedEvidence",
    "gateResults",
    "criterionScores",
    "scoringState",
    "weightedScore",
    "purchaseAuthorised",
}
OUTPUT_VENDOR_KEYS = VENDOR_KEYS | {
    "receivedEvidence",
    "evidenceReceivedCount",
    "evaluatedGateCount",
    "mandatoryGatePassCount",
}
SUMMARY_KEYS = {
    "trackedVendors",
    "substantiveResponses",
    "scoredVendors",
    "purchaseAuthorisations",
}

EMAIL_RE = re.compile(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", re.IGNORECASE)
UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
ABSOLUTE_PATH_RE = re.compile(
    r"(?i)(?:file:(?://|\\/\\/)|/(?:Users|home|private|tmp|var|etc)/|"
    r"[A-Z]:\\\\(?:Users|home|private|tmp|var|etc)\\\\)"
)
EXACT_TIME_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?")
FORBIDDEN_METADATA_TEXT = (
    "submissionguid",
    "submission guid",
    "formguid",
    "form guid",
    "message-id",
    "message id",
    "thread id",
    "private path",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def text_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from text_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from text_values(item)


def valid_date(value: Any) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def scan_privacy(label: str, value: Any, errors: list[str]) -> None:
    for text in text_values(value):
        folded = text.casefold()
        if EMAIL_RE.search(text):
            errors.append(f"{label} contains an email address")
        if UUID_RE.search(text):
            errors.append(f"{label} contains a UUID")
        if ABSOLUTE_PATH_RE.search(text):
            errors.append(f"{label} contains a local or private path")
        if EXACT_TIME_RE.search(text):
            errors.append(f"{label} contains an exact timestamp")
        if contains_private_identifier(text):
            errors.append(f"{label} contains a private identifier fingerprint")
        if any(marker in folded for marker in FORBIDDEN_METADATA_TEXT):
            errors.append(f"{label} contains a forbidden private metadata field")


def validate_germany_benchmark(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict) or set(value) != GERMANY_BENCHMARK_KEYS:
        errors.append("Germany benchmark schema differs")
        return
    if (
        value.get("benchmarkId") != "de-taxed-e-liquid-volume-vendor-gate"
        or value.get("countryIso2") != "DE"
        or value.get("unit") != "litre"
        or value.get("status") != "not_testable"
    ):
        errors.append("Germany benchmark identity or not-testable state differs")
    for field in (
        "scopeEn",
        "scopeFi",
        "statusReasonEn",
        "statusReasonFi",
        "donorBoundaryEn",
        "donorBoundaryFi",
    ):
        if not isinstance(value.get(field), str) or not value[field].strip():
            errors.append(f"Germany benchmark {field} must be non-empty")
    if (
        value.get("vendorPassDoesNotEstablishDonorPass") is not True
        or value.get("donorGateEffect") != "none"
        or "D1–D10" not in str(value.get("donorBoundaryEn", ""))
        or "0/3" not in str(value.get("donorBoundaryEn", ""))
    ):
        errors.append("Germany vendor-pass must not establish donor-market acceptance")

    anchors = value.get("officialAnchors")
    if not isinstance(anchors, list) or len(anchors) != len(EXPECTED_GERMANY_ANCHORS):
        errors.append("Germany benchmark must contain the three reviewed official anchors")
    else:
        seen_years: set[int] = set()
        for anchor in anchors:
            if not isinstance(anchor, dict) or set(anchor) != GERMANY_ANCHOR_KEYS:
                errors.append("Germany official-anchor schema differs")
                continue
            year = anchor.get("year")
            if year in seen_years or year not in EXPECTED_GERMANY_ANCHORS:
                errors.append(f"Germany official-anchor year differs: {year!r}")
                continue
            seen_years.add(year)
            expected = {"year": year, **EXPECTED_GERMANY_ANCHORS[year]}
            if anchor != expected:
                errors.append(f"Germany {year} official anchor differs")
        if seen_years != set(EXPECTED_GERMANY_ANCHORS):
            errors.append("Germany official-anchor year set differs")

    thresholds = value.get("thresholds")
    if not isinstance(thresholds, dict) or set(thresholds) != {
        "annualDeviation",
        "twoYearCumulativeDeviation",
    }:
        errors.append("Germany benchmark threshold schema differs")
    else:
        expected_thresholds = {
            "annualDeviation": (15, [2023, 2024]),
            "twoYearCumulativeDeviation": (10, [2023, 2024]),
        }
        for threshold_id, (maximum_pct, years) in expected_thresholds.items():
            threshold = thresholds.get(threshold_id)
            if not isinstance(threshold, dict) or set(threshold) != {
                "maximumPct",
                "years",
                "formulaEn",
                "formulaFi",
            }:
                errors.append(f"Germany {threshold_id} threshold schema differs")
                continue
            if (
                threshold.get("maximumPct") != maximum_pct
                or threshold.get("years") != years
                or not isinstance(threshold.get("formulaEn"), str)
                or not threshold["formulaEn"].strip()
                or not isinstance(threshold.get("formulaFi"), str)
                or not threshold["formulaFi"].strip()
            ):
                errors.append(f"Germany {threshold_id} threshold differs")

    required_evidence = value.get("requiredEvidence")
    if not isinstance(required_evidence, list) or len(required_evidence) != len(
        GERMANY_REQUIRED_EVIDENCE_IDS
    ):
        errors.append("Germany benchmark required-evidence set differs")
    else:
        seen_ids: set[str] = set()
        for item in required_evidence:
            if not isinstance(item, dict) or set(item) != {
                "id",
                "labelEn",
                "labelFi",
                "descriptionEn",
                "descriptionFi",
            }:
                errors.append("Germany required-evidence schema differs")
                continue
            item_id = item.get("id")
            if item_id in seen_ids or item_id not in GERMANY_REQUIRED_EVIDENCE_IDS:
                errors.append(f"Germany required-evidence ID differs: {item_id!r}")
                continue
            seen_ids.add(item_id)
            if any(
                not isinstance(item.get(field), str) or not item[field].strip()
                for field in ("labelEn", "labelFi", "descriptionEn", "descriptionFi")
            ):
                errors.append(f"Germany required-evidence copy is incomplete for {item_id!r}")
        if seen_ids != GERMANY_REQUIRED_EVIDENCE_IDS:
            errors.append("Germany required-evidence IDs differ")


def validate_gate_results(
    vendor_id: str,
    value: Any,
    errors: list[str],
) -> None:
    if not isinstance(value, dict) or set(value) != MANDATORY_GATE_IDS:
        errors.append(f"{vendor_id}: G1-G6 gate-result set differs")
        return
    for gate_id, result in value.items():
        if not isinstance(result, dict) or set(result) != {"status", "reasonCodes"}:
            errors.append(f"{vendor_id}: {gate_id} gate-result schema differs")
            continue
        status = result.get("status")
        reasons = result.get("reasonCodes")
        if status not in GATE_STATUSES:
            errors.append(f"{vendor_id}: {gate_id} has an invalid gate status")
            continue
        if not isinstance(reasons, list) or any(
            not isinstance(reason, str) for reason in reasons
        ):
            errors.append(f"{vendor_id}: {gate_id} reason codes must be a string array")
            continue
        if len(reasons) != len(set(reasons)):
            errors.append(f"{vendor_id}: {gate_id} reason codes must be unique")
        if status == "pass":
            if reasons:
                errors.append(f"{vendor_id}: {gate_id} PASS cannot carry failure reasons")
            continue
        if not reasons:
            errors.append(f"{vendor_id}: {gate_id} non-PASS status requires a reason code")
            continue
        allowed_reasons = MANDATORY_GATE_RULES[gate_id]["allowedReasons"]
        for reason in reasons:
            if reason not in allowed_reasons:
                errors.append(
                    f"{vendor_id}: {gate_id} has an unreviewed reason code {reason!r}"
                )
            if status not in REASON_CODE_STATUSES.get(reason, set()):
                errors.append(
                    f"{vendor_id}: {gate_id} reason {reason!r} is inconsistent "
                    f"with status {status!r}"
                )


def validate_source(source: Any, errors: list[str]) -> None:
    if not isinstance(source, dict):
        errors.append("source must contain an object")
        return
    if set(source) != TOP_LEVEL_KEYS:
        errors.append("source top-level schema differs")
        return
    if source.get("schemaVersion") != 2:
        errors.append("unsupported schema version")
    if source.get("controlId") != "vendor-response-control-public":
        errors.append("unexpected control ID")
    if source.get("status") != "public_status_only_no_purchase_authorised":
        errors.append("control must state that no purchase is authorised")
    if source.get("version") != "2026.07.31-37" or source.get("asOf") != "2026-07-31":
        errors.append("control version or date differs")
    if source.get("scoreScale") != {
        "minimum": 0,
        "maximum": 5,
        "missingValue": "not_scored",
    }:
        errors.append("score scale must preserve missing values as not_scored")
    validate_germany_benchmark(source.get("germanyBenchmark"), errors)

    criteria = source.get("criteria")
    if not isinstance(criteria, list) or len(criteria) != len(CRITERION_WEIGHTS):
        errors.append("exactly seven scoring criteria are required")
        return
    criterion_ids: set[str] = set()
    for criterion in criteria:
        if not isinstance(criterion, dict) or set(criterion) != {
            "id",
            "weight",
            "labelEn",
            "labelFi",
            "descriptionEn",
            "descriptionFi",
        }:
            errors.append("criterion schema differs")
            continue
        criterion_id = criterion["id"]
        criterion_ids.add(criterion_id)
        if criterion_id not in CRITERION_WEIGHTS:
            errors.append(f"unknown criterion {criterion_id!r}")
        elif abs(float(criterion["weight"]) - CRITERION_WEIGHTS[criterion_id]) > 1e-9:
            errors.append(f"criterion weight differs for {criterion_id!r}")
    if criterion_ids != set(CRITERION_WEIGHTS):
        errors.append("criterion IDs differ")
    if abs(sum(float(item["weight"]) for item in criteria) - 1.0) > 1e-9:
        errors.append("criterion weights must sum to 1.0")

    gates = source.get("mandatoryGates")
    if not isinstance(gates, list) or len(gates) != len(MANDATORY_GATE_KEYS):
        errors.append("exactly six mandatory gates are required")
        gates = []
    gate_evidence_keys: set[str] = set()
    gate_ids: set[str] = set()
    gate_codes: set[str] = set()
    for gate in gates:
        if not isinstance(gate, dict) or set(gate) != {
            "id",
            "gateCode",
            "evidenceKey",
            "labelEn",
            "labelFi",
            "descriptionEn",
            "descriptionFi",
        }:
            errors.append("mandatory gate schema differs")
            continue
        gate_ids.add(gate["id"])
        gate_codes.add(gate["gateCode"])
        gate_evidence_keys.add(gate["evidenceKey"])
        expected_rule = MANDATORY_GATE_RULES.get(gate["gateCode"])
        if (
            expected_rule is None
            or gate["evidenceKey"] != expected_rule["evidenceKey"]
            or gate["id"] != expected_rule["evidenceKey"]
        ):
            errors.append(f"mandatory gate mapping differs for {gate['gateCode']!r}")
    if (
        gate_ids != MANDATORY_GATE_KEYS
        or gate_codes != MANDATORY_GATE_IDS
        or gate_evidence_keys != MANDATORY_GATE_KEYS
    ):
        errors.append("mandatory gate set differs")

    evidence_types = source.get("evidenceTypes")
    if not isinstance(evidence_types, list) or len(evidence_types) != len(EVIDENCE_KEYS):
        errors.append("exactly seven public evidence indicators are required")
    elif (
        {item.get("key") for item in evidence_types if isinstance(item, dict)} != EVIDENCE_KEYS
        or any(
            not isinstance(item, dict)
            or set(item) != {"key", "labelEn", "labelFi"}
            for item in evidence_types
        )
    ):
        errors.append("evidence indicator schema or keys differ")

    vendors = source.get("vendors")
    if not isinstance(vendors, list) or len(vendors) != len(EXPECTED_VENDORS):
        errors.append("exactly four public vendor records are required")
        return
    seen: set[str] = set()
    for vendor in vendors:
        if not isinstance(vendor, dict) or set(vendor) != VENDOR_KEYS:
            errors.append("vendor record schema differs")
            continue
        vendor_id = vendor["vendorId"]
        if vendor_id in seen or vendor_id not in EXPECTED_VENDORS:
            errors.append(f"unknown or duplicate vendor ID {vendor_id!r}")
            continue
        seen.add(vendor_id)
        expected = EXPECTED_VENDORS[vendor_id]
        for field in (
            "vendor",
            "product",
            "requestState",
            "responseState",
            "publicStatusEn",
            "publicStatusFi",
            "quoteReceived",
            "receivedEvidence",
        ):
            if vendor[field] != expected[field]:
                errors.append(f"{vendor_id}: {field} differs from the reviewed public state")
        receipts = vendor.get("receivedEvidence")
        if (
            not isinstance(receipts, dict)
            or set(receipts) != EVIDENCE_KEYS
            or any(not isinstance(value, bool) for value in receipts.values())
        ):
            errors.append(f"{vendor_id}: received-evidence schema differs")
        elif receipts.get("quote") is not vendor.get("quoteReceived"):
            errors.append(f"{vendor_id}: quote receipt state differs")
        gate_results = vendor.get("gateResults")
        validate_gate_results(vendor_id, gate_results, errors)
        if gate_results != expected["gateResults"]:
            errors.append(f"{vendor_id}: gate results differ from the reviewed release")
        scores = vendor.get("criterionScores")
        if not isinstance(scores, dict) or set(scores) != set(CRITERION_WEIGHTS):
            errors.append(f"{vendor_id}: criterion score schema differs")
        elif any(value is not None for value in scores.values()):
            errors.append(f"{vendor_id}: missing evidence must not be converted into scores")
        if vendor.get("scoringState") != "not_scored" or vendor.get("weightedScore") is not None:
            errors.append(f"{vendor_id}: missing response must remain NOT SCORED")
        if vendor.get("purchaseAuthorised") is not False:
            errors.append(f"{vendor_id}: purchase authorisation must remain false")
        if isinstance(gate_results, dict) and isinstance(scores, dict):
            if isinstance(receipts, dict):
                for gate_id, result in gate_results.items():
                    evidence_key = MANDATORY_GATE_RULES[gate_id]["evidenceKey"]
                    if result.get("status") == "pass" and receipts.get(evidence_key) is not True:
                        errors.append(
                            f"{vendor_id}: {gate_id} cannot pass without received evidence"
                        )
            if score_vendor(vendor, criteria, gates) is not None:
                errors.append(f"{vendor_id}: vendor cannot be scored before the mandatory gates pass")
    if seen != set(EXPECTED_VENDORS):
        errors.append("vendor set differs from the reviewed four-vendor control")

    scan_privacy("vendor-response source", source, errors)


def validate_outputs(source: dict[str, Any], errors: list[str]) -> None:
    try:
        output_json_bytes = OUTPUT_JSON.read_bytes()
    except FileNotFoundError:
        errors.append("public vendor-response JSON is missing")
        output_json_bytes = b""
    if output_json_bytes and output_json_bytes != render_json(source):
        errors.append("public vendor-response JSON is stale or differs from the canonical source")
    try:
        output_csv_bytes = OUTPUT_CSV.read_bytes()
    except FileNotFoundError:
        errors.append("public vendor-response CSV is missing")
        output_csv_bytes = b""
    if output_csv_bytes and output_csv_bytes != render_csv(source):
        errors.append("public vendor-response CSV is stale or differs from the canonical source")

    if output_json_bytes:
        output = json.loads(output_json_bytes)
        source_vendor_by_id = {
            vendor["vendorId"]: vendor for vendor in source.get("vendors", [])
        }
        if set(output) != OUTPUT_TOP_LEVEL_KEYS:
            errors.append("public JSON top-level schema differs")
        if set(output.get("summary", {})) != SUMMARY_KEYS:
            errors.append("public JSON summary schema differs")
        elif output["summary"] != {
            "trackedVendors": 4,
            "substantiveResponses": 1,
            "scoredVendors": 0,
            "purchaseAuthorisations": 0,
        }:
            errors.append("public JSON summary differs from the reviewed current state")
        validate_germany_benchmark(output.get("germanyBenchmark"), errors)
        for vendor in output.get("vendors", []):
            if set(vendor) != OUTPUT_VENDOR_KEYS:
                errors.append("public JSON vendor output schema differs")
            vendor_id = str(vendor.get("vendorId", "unknown"))
            gate_results = vendor.get("gateResults")
            validate_gate_results(vendor_id, gate_results, errors)
            if isinstance(gate_results, dict):
                expected_receipts = source_vendor_by_id.get(vendor_id, {}).get(
                    "receivedEvidence"
                )
                if vendor.get("receivedEvidence") != expected_receipts:
                    errors.append(
                        f"{vendor_id}: received-evidence intake history differs"
                    )
                evaluated_count = sum(
                    isinstance(result, dict) and result.get("status") != "missing"
                    for result in gate_results.values()
                )
                pass_count = sum(
                    isinstance(result, dict) and result.get("status") == "pass"
                    for result in gate_results.values()
                )
                if vendor.get("evaluatedGateCount") != evaluated_count:
                    errors.append(f"{vendor_id}: evaluated gate count differs")
                if vendor.get("mandatoryGatePassCount") != pass_count:
                    errors.append(f"{vendor_id}: mandatory gate PASS count differs")
                if vendor.get("evidenceReceivedCount") != sum(
                    value is True for value in (expected_receipts or {}).values()
                ):
                    errors.append(f"{vendor_id}: evidence received count differs")
            if vendor.get("weightedScore") is not None:
                errors.append("public JSON cannot expose a score before evidence is complete")
        scan_privacy("public vendor-response JSON", output, errors)

    if output_csv_bytes:
        text = output_csv_bytes.decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(text)))
        if not rows or list(rows[0]) != CSV_FIELDS:
            errors.append("public vendor-response CSV columns differ")
        if len(rows) != 4:
            errors.append("public vendor-response CSV must contain exactly four rows")
        for row in rows:
            if row.get("scoringState") != "not_scored" or row.get("weightedScore") != "":
                errors.append("public CSV missing evidence must remain not_scored with a blank score")
            if row.get("purchaseAuthorised") != "false":
                errors.append("public CSV purchaseAuthorised must remain false")
            for field in (
                "sampleGateStatus",
                "methodologyGateStatus",
                "coverageMatrixGateStatus",
                "officialAnchorReconciliationGateStatus",
                "transactionUseRightsGateStatus",
                "totalCostTermsGateStatus",
            ):
                if row.get(field) not in GATE_STATUSES:
                    errors.append(f"public CSV {field} differs")
        scan_privacy("public vendor-response CSV", text, errors)


def validate_site_integration(errors: list[str]) -> None:
    try:
        html = REVIEW_HTML.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append("site/review.html is missing")
        return
    if 'data-vendor-response' not in html:
        errors.append("review page lacks the vendor-response control section")
    if 'src="assets/vendor-response.js' not in html:
        errors.append("review page does not load vendor-response.js")
    if 'href="data/vendor-response-control.csv"' not in html:
        errors.append("review page lacks the public vendor-response CSV download")
    if 'href="data/vendor-response-control.json"' not in html:
        errors.append("review page lacks the public vendor-response JSON download")
    for marker in (
        "data-vendor-response-germany-benchmark",
        "data-vendor-response-germany-anchors",
        "data-vendor-response-germany-requirements",
        "data-vendor-response-germany-note",
    ):
        if marker not in html:
            errors.append(f"review page lacks {marker}")
    if not VENDOR_SCRIPT.is_file():
        errors.append("site/assets/vendor-response.js is missing")
    else:
        validate_vendor_script_text(
            VENDOR_SCRIPT.read_text(encoding="utf-8"),
            errors,
        )


def validate_vendor_script_text(text: str, errors: list[str]) -> None:
    missing = [hook for hook in RECEIPT_LEDGER_HOOKS if hook not in text]
    if missing:
        errors.append(
            "vendor-response.js lacks the visible receipt-ledger hooks: "
            + ", ".join(repr(hook) for hook in missing)
        )


def main() -> None:
    errors: list[str] = []
    try:
        source = read_json(SOURCE_PATH)
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: cannot load canonical vendor-response source: {error}", file=sys.stderr)
        raise SystemExit(1)

    validate_source(source, errors)
    if not errors:
        validate_outputs(source, errors)
    validate_site_integration(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Validation failed with {len(errors)} error(s).", file=sys.stderr)
        raise SystemExit(1)

    output = normalised(source)
    print(
        "Validated privacy-safe vendor-response control: "
        f'{output["summary"]["trackedVendors"]} tracked, '
        f'{output["summary"]["substantiveResponses"]} substantive responses, '
        f'{output["summary"]["scoredVendors"]} scored, '
        f'{output["summary"]["purchaseAuthorisations"]} purchase authorisations.'
    )


if __name__ == "__main__":
    main()
