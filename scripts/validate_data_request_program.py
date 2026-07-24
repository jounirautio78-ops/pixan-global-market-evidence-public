#!/usr/bin/env python3
"""Fail-closed validation for the public Top-20 data-request programme."""

from __future__ import annotations

import csv
from datetime import date
import hashlib
import io
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from build_data_request_program import (
    CSV_FIELDS,
    OUTPUT_CSV,
    OUTPUT_JSON,
    OUTPUT_TEMPLATE_EN,
    OUTPUT_TEMPLATE_FI,
    ROOT,
    SOURCE_PATH,
    SOURCE_TEMPLATE_EN,
    SOURCE_TEMPLATE_FI,
    normalised_program,
    render_csv,
    render_json,
)


EXPECTED_DATE = "2026-07-24"
EXPECTED_PROGRAMME_STATUS = "partially_dispatched"
EXPECTED_RANKING_TYPE = "operational_evidence_acquisition_order"
EXPECTED_STATE_UNIVERSE_COUNT = 195
EXPECTED_EVIDENCE_LAYER_IDS = (
    "statutory_sales",
    "excise_domestic_release",
    "customs_net_imports",
    "retail_or_shipments",
    "price_channel_bridge",
    "enforcement_signal",
)
LOCAL_REQUESTER_VALUES = {"not_required", "recommended", "conditional", "required"}
ROUTE_STATUS_VALUES = {"draft_not_sent", "sent"}
PROCESS_RESPONSE_STATE_VALUES = {
    "receipt_and_ifg_forwarding_confirmed",
    "registered_and_processing_confirmed",
    "registered_processing_notice_received",
    "automated_receipt_acknowledged",
    "automated_route_correction_received",
}
STRUCTURAL_RESPONSE_STATE_VALUES = {
    "official_structural_data_received_sales_not_available",
}
SALES_RESPONSE_STATE_VALUES = {
    "official_annual_sales_data_received",
}
RESPONSE_STATE_VALUES = {
    "not_applicable",
    "not_publicly_recorded",
    *PROCESS_RESPONSE_STATE_VALUES,
    *STRUCTURAL_RESPONSE_STATE_VALUES,
    *SALES_RESPONSE_STATE_VALUES,
}
EXPECTED_PROCESS_RESPONSE_COUNTRIES = {"DE", "FI", "DK"}
EXPECTED_STRUCTURAL_RESPONSE_COUNTRIES = {"SE"}
EXPECTED_SALES_RESPONSE_COUNTRIES: set[str] = set()
EXPECTED_DISPATCH = {
    "DE": {
        "state": "sent",
        "sentOn": "2026-07-23",
        "publicAuthorityReference": None,
        "responseState": "registered_and_processing_confirmed",
    },
    "CA": {
        "state": "sent",
        "sentOn": "2026-07-23",
        "publicAuthorityReference": None,
        "responseState": "not_publicly_recorded",
    },
    "US": {
        "state": "sent",
        "sentOn": "2026-07-24",
        "publicAuthorityReference": None,
        "responseState": "not_publicly_recorded",
    },
    "GB": {
        "state": "sent",
        "sentOn": "2026-07-16",
        "publicAuthorityReference": "CEC 261515",
        "responseState": "not_publicly_recorded",
    },
    "FI": {
        "state": "sent",
        "sentOn": "2026-07-22",
        "publicAuthorityReference": None,
        "responseState": "registered_processing_notice_received",
    },
    "PL": {
        "state": "sent",
        "sentOn": "2026-07-22",
        "publicAuthorityReference": None,
        "responseState": "not_publicly_recorded",
    },
    "SE": {
        "state": "sent",
        "sentOn": "2026-07-23",
        "publicAuthorityReference": None,
        "responseState": "official_structural_data_received_sales_not_available",
    },
    "IT": {
        "state": "sent",
        "sentOn": "2026-07-23",
        "publicAuthorityReference": None,
        "responseState": "not_publicly_recorded",
    },
    "FR": {
        "state": "sent",
        "sentOn": "2026-07-23",
        "publicAuthorityReference": None,
        "responseState": "not_publicly_recorded",
    },
    "NL": {
        "state": "sent",
        "sentOn": "2026-07-23",
        "publicAuthorityReference": None,
        "responseState": "not_publicly_recorded",
    },
    "DK": {
        "state": "sent",
        "sentOn": "2026-07-23",
        "publicAuthorityReference": None,
        "responseState": "automated_receipt_acknowledged",
    },
    "AU": {
        "state": "sent",
        "sentOn": "2026-07-23",
        "publicAuthorityReference": None,
        "responseState": "not_publicly_recorded",
    },
}
EXPECTED_SUPPLEMENTARY_DISPATCH = {
    "DE-BVL-TABAKERZV25-ANNUAL-SALES": {
        "countryIso2": "DE",
        "state": "sent",
        "sentOn": "2026-07-24",
        "publicAuthorityReference": None,
        "responseState": "not_publicly_recorded",
    },
}
EXPECTED_BVL_CHANNEL_URL = "https://www.bvl.bund.de/DE/Service/07_Kontakt/einleitung.html"
EXPECTED_BVL_GUIDANCE_URL = (
    "https://www.bvl.bund.de/DE/Arbeitsbereiche/03_Verbraucherprodukte/"
    "03_AntragstellerUnternehmen/04_Tabakerzeugnisse_E-Zigaretten/"
    "01_Mitteilungspflicht/bgs_tabakerzeugnisse_mitteilungspflicht_node.html"
    "?thema=Mitteilungspflicht"
)
EXPECTED_TABAKERZV_25_URL = "https://www.gesetze-im-internet.de/tabakerzv/__25.html"
EXPECTED_SWEDEN_CONTEXT_URL = (
    "https://www.folkhalsomyndigheten.se/regler-och-tillsyn/"
    "tobak-och-nikotinprodukter-regler-for-tillverkning-handel-och-hantering/"
    "elektroniska-cigaretter-och-pafyllningsbehallare-sa-foljer-du-reglerna/"
)
PRIVATE_METADATA_KEYS = {
    "acknowledgedon", "acknowledgementon", "acknowledgmenton", "bcc", "body", "cc",
    "conversationid", "correspondence", "deliveredon", "email", "emailaddress", "from",
    "gmailid", "header", "headers", "messageid", "missiveid", "mobile", "phone",
    "phonenumber", "receivedon", "recipient", "recipientemail", "recipientidentity",
    "recipientname", "sender", "senderemail", "senderidentity", "sendername", "senttime",
    "senttimestamp", "subject", "telephone", "threadid", "to",
}
FORBIDDEN_PUBLIC_TEXT = ("/users/", "file://")
FORBIDDEN_PROCESS_OVERSTATEMENTS = (
    "market data received",
    "substantive data response received",
    "a fee was accepted",
    "markkinadata saatu",
    "sisällöllinen datavastaus saatu",
    "maksu hyväksyttiin",
)
EMAIL_ADDRESS_RE = re.compile(r"(?i)\b[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+\b")
PRIVATE_IDENTIFIER_FINGERPRINTS = frozenset(
    {
        (7, "46d7415f6182ece9e933e8e9f780957e449361e0dbe10e34f46c186cad3382a1"),
        (7, "f910f0bbe95037851d18ca33b91ee7fc9f334c6cfcd02deaf66af4501c8a884c"),
        (9, "7e6578c2e34b53136741c6efe7799a2dce739651c22404a7894b48d42aa88b41"),
        (13, "933536a17b00f1b39ba9d3585427bd7232d44960ab35754318c1da8e4cf6c5be"),
        (25, "40f45830e7e3e21d88245728fe87f76b2e8919543a502aad248a465487cacee3"),
    }
)

TOP_LEVEL_KEYS = {
    "schemaVersion", "programmeId", "verificationDate", "status",
    "independenceNoticeEn", "independenceNoticeFi", "ranking", "scope",
    "evidenceStack", "supplementaryRequests", "routes",
}


def contains_private_identifier(value: str) -> bool:
    normalised = re.sub(r"[^a-z0-9]+", "", value.casefold())
    for length, expected in PRIVATE_IDENTIFIER_FINGERPRINTS:
        if any(
            hashlib.sha256(normalised[index:index + length].encode("utf-8")).hexdigest() == expected
            for index in range(max(0, len(normalised) - length + 1))
        ):
            return True
    return False
RANKING_KEYS = {"type", "isMarketSizeRanking", "statementEn", "statementFi"}
SCOPE_KEYS = {
    "period", "provisional2026En", "provisional2026Fi", "preferredFormats",
    "requestPrinciplesEn", "requestPrinciplesFi", "commonFieldsEn", "commonFieldsFi",
}
EVIDENCE_STACK_KEYS = {
    "stateUniverseCount", "stateUniverseEn", "stateUniverseFi",
    "methodBoundaryEn", "methodBoundaryFi", "layers",
}
EVIDENCE_LAYER_KEYS = {
    "order", "layerId", "titleEn", "titleFi", "purposeEn", "purposeFi",
    "outputEn", "outputFi",
}
ROUTE_KEYS = {
    "operationalRank", "priorityCode", "wave", "countryIso2", "countryEn", "countryFi",
    "status", "dispatch", "rationaleEn", "rationaleFi", "primaryAuthority", "recordsRequestedEn",
    "recordsRequestedFi", "requestChannel", "legalBasis", "languages",
    "requesterEligibility", "fallbackAuthority", "officialSources",
}
SUPPLEMENTARY_REQUEST_KEYS = {
    "requestId", "countryIso2", "countsTowardCountryQueue", "status", "dispatch",
    "authority", "purposeEn", "purposeFi", "queueBoundaryEn", "queueBoundaryFi",
    "recordsRequestedEn", "recordsRequestedFi", "requestChannel", "legalBasis",
    "officialSources",
}
AUTHORITY_KEYS = {"nameEn", "nameFi"}
LINKED_AUTHORITY_KEYS = {"nameEn", "nameFi", "url"}
ELIGIBILITY_KEYS = {"localRequester", "caveatEn", "caveatFi"}
SOURCE_KEYS = {"labelEn", "labelFi", "url", "verifiedOn"}
DISPATCH_KEYS = {"state", "sentOn", "publicAuthorityReference", "responseState"}

OFFICIAL_HOSTS = {
    "DE": {"bund.de", "destatis.de", "gesetze-im-internet.de", "zoll.de"},
    "CA": {"canada.ca", "statcan.gc.ca"},
    "US": {"ftc.gov", "usitc.gov", "fda.gov", "cbp.gov"},
    "CN": {"stats.gov.cn", "customs.gov.cn", "samr.gov.cn"},
    "PL": {"gov.pl"},
    "GB": {"gov.uk", "mhra.gov.uk"},
    "SE": {"folkhalsomyndigheten.se", "skatteverket.se", "tullverket.se"},
    "IT": {"adm.gov.it", "salute.gov.it"},
    "FR": {"anses.fr", "cada.fr", "gouv.fr", "insee.fr"},
    "ES": {"gob.es"},
    "NL": {"rijksoverheid.nl", "rivm.nl", "belastingdienst.nl"},
    "FI": {"lvv.fi", "suomi.fi", "vero.fi", "finlex.fi", "tulli.fi"},
    "DK": {"erhvervsstyrelsen.dk", "sik.dk", "skat.dk"},
    "JP": {"mof.go.jp", "customs.go.jp", "mhlw.go.jp"},
    "KR": {"customs.go.kr", "open.go.kr", "go.kr"},
    "AU": {"tga.gov.au", "homeaffairs.gov.au", "oaic.gov.au", "abs.gov.au"},
    "RU": {"nalog.gov.ru", "rosstat.gov.ru", "customs.gov.ru"},
    "BR": {"gov.br"},
    "ID": {"beacukai.go.id", "kemenkeu.go.id", "bps.go.id"},
    "PH": {"foi.gov.ph", "bir.gov.ph", "customs.gov.ph", "psa.gov.ph"},
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def find_private_metadata_keys(value: Any, path: str = "root"):
    if isinstance(value, dict):
        for key, item in value.items():
            normalised = re.sub(r"[^a-z]", "", key.casefold())
            if normalised in PRIVATE_METADATA_KEYS:
                yield f"{path}.{key}"
            yield from find_private_metadata_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from find_private_metadata_keys(item, f"{path}[{index}]")


def valid_iso_date(value: Any) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def route_urls(route: dict[str, Any]) -> list[str]:
    urls = [route["requestChannel"]["url"], route["fallbackAuthority"]["url"]]
    urls.extend(source["url"] for source in route["officialSources"])
    return urls


def official_host(host: str, allowed: set[str]) -> bool:
    return any(host == suffix or host.endswith(f".{suffix}") for suffix in allowed)


def require_exact_keys(value: Any, expected: set[str], label: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        errors.append(f"{label} schema differs; missing={missing}, extra={extra}")
        return False
    return True


def require_text(value: Any, label: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty string")
        return False
    return True


def require_text_list(value: Any, label: str, errors: list[str]) -> bool:
    if not isinstance(value, list) or not value or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        errors.append(f"{label} must be a non-empty array of non-empty strings")
        return False
    return True


def validate_program(program: dict[str, Any], errors: list[str]) -> None:
    if not require_exact_keys(program, TOP_LEVEL_KEYS, "programme", errors):
        return
    if program.get("schemaVersion") != 3:
        errors.append("schemaVersion must be 3")
    if program.get("programmeId") != "pixan-independent-top20-official-data-request-programme-v3":
        errors.append("programmeId must identify the approved v3 programme")
    for field in ("programmeId", "independenceNoticeEn", "independenceNoticeFi"):
        require_text(program.get(field), field, errors)
    if not valid_iso_date(program.get("verificationDate")) or program.get("verificationDate") != EXPECTED_DATE:
        errors.append(f"verificationDate must be {EXPECTED_DATE}")
    if program.get("status") != EXPECTED_PROGRAMME_STATUS:
        errors.append(f"programme status must be {EXPECTED_PROGRAMME_STATUS}")
    ranking = program.get("ranking", {})
    if not require_exact_keys(ranking, RANKING_KEYS, "ranking", errors):
        return
    if ranking.get("type") != EXPECTED_RANKING_TYPE:
        errors.append("ranking type must be operational_evidence_acquisition_order")
    if ranking.get("isMarketSizeRanking") is not False:
        errors.append("ranking must explicitly state isMarketSizeRanking=false")

    scope = program.get("scope")
    if not require_exact_keys(scope, SCOPE_KEYS, "scope", errors):
        return
    for field in ("period", "provisional2026En", "provisional2026Fi"):
        require_text(scope.get(field), f"scope.{field}", errors)
    for field in ("preferredFormats", "requestPrinciplesEn", "requestPrinciplesFi", "commonFieldsEn", "commonFieldsFi"):
        require_text_list(scope.get(field), f"scope.{field}", errors)

    evidence_stack = program.get("evidenceStack")
    if not require_exact_keys(evidence_stack, EVIDENCE_STACK_KEYS, "evidenceStack", errors):
        return
    if evidence_stack.get("stateUniverseCount") != EXPECTED_STATE_UNIVERSE_COUNT:
        errors.append(f"evidenceStack.stateUniverseCount must be {EXPECTED_STATE_UNIVERSE_COUNT}")
    for field in (
        "stateUniverseEn", "stateUniverseFi", "methodBoundaryEn", "methodBoundaryFi",
    ):
        require_text(evidence_stack.get(field), f"evidenceStack.{field}", errors)
    method_boundary_en = str(evidence_stack.get("methodBoundaryEn", "")).casefold()
    method_boundary_fi = str(evidence_stack.get("methodBoundaryFi", "")).casefold()
    if not all(term in method_boundary_en for term in (
        "locked to one evidence group", "never mechanically added",
        "reconciliation, uncertainty and confidence sit above all six layers",
        "missing evidence remains missing", "never converted to zero",
    )):
        errors.append("English evidence-stack boundary must prohibit addition and missing-to-zero conversion")
    if not all(term in method_boundary_fi for term in (
        "lukitaan yhteen evidenssiryhmään", "koskaan lasketa mekaanisesti yhteen",
        "täsmäytys, epävarmuus ja luottamus ovat kaikkien kuuden kerroksen yläpuolinen menetelmä",
        "puuttuva näyttö säilyy puuttuvana", "eikä muutu nollaksi",
    )):
        errors.append("Finnish evidence-stack boundary must prohibit addition and missing-to-zero conversion")
    layers = evidence_stack.get("layers")
    if not isinstance(layers, list) or len(layers) != 6:
        errors.append("evidenceStack must contain exactly six layers")
        return
    if any(not isinstance(layer, dict) for layer in layers):
        errors.append("every evidence-stack layer must be an object")
        return
    layer_ids: list[str] = []
    layer_orders: list[int] = []
    for index, layer in enumerate(layers):
        label = f"evidenceStack.layers[{index}]"
        if not require_exact_keys(layer, EVIDENCE_LAYER_KEYS, label, errors):
            continue
        layer_ids.append(layer.get("layerId"))
        layer_orders.append(layer.get("order"))
        if type(layer.get("order")) is not int:
            errors.append(f"{label}.order must be an integer")
        for field in (
            "layerId", "titleEn", "titleFi", "purposeEn", "purposeFi",
            "outputEn", "outputFi",
        ):
            require_text(layer.get(field), f"{label}.{field}", errors)
    if tuple(layer_ids) != EXPECTED_EVIDENCE_LAYER_IDS:
        errors.append("evidence-stack layer IDs or order differ from the approved six-layer method")
    if layer_orders != list(range(1, 7)):
        errors.append("evidence-stack layer order must be the unique integers 1-6")

    supplementary_requests = program.get("supplementaryRequests")
    if not isinstance(supplementary_requests, list):
        errors.append("supplementaryRequests must be an array")
        return
    if len(supplementary_requests) != len(EXPECTED_SUPPLEMENTARY_DISPATCH):
        errors.append("supplementary request set differs from the approved public record")
        return
    supplementary_ids: set[str] = set()
    for request in supplementary_requests:
        request_id = request.get("requestId", "?") if isinstance(request, dict) else "?"
        label = f"supplementary request {request_id}"
        if not require_exact_keys(request, SUPPLEMENTARY_REQUEST_KEYS, label, errors):
            continue
        expected = EXPECTED_SUPPLEMENTARY_DISPATCH.get(request_id)
        if expected is None or request_id in supplementary_ids:
            errors.append(f"{label}: unapproved or duplicate supplementary request")
            continue
        supplementary_ids.add(request_id)
        if request.get("countryIso2") != expected["countryIso2"]:
            errors.append(f"{label}: country differs from the approved public record")
        if request.get("countsTowardCountryQueue") is not False:
            errors.append(f"{label}: supplementary route must not count as another country")
        if request.get("status") != "sent":
            errors.append(f"{label}: approved supplementary route must be sent")
        dispatch = request.get("dispatch")
        if require_exact_keys(dispatch, DISPATCH_KEYS, f"{label}.dispatch", errors):
            expected_dispatch = {
                "state": expected["state"],
                "sentOn": expected["sentOn"],
                "publicAuthorityReference": expected["publicAuthorityReference"],
                "responseState": expected["responseState"],
            }
            if dispatch != expected_dispatch or request.get("status") != dispatch.get("state"):
                errors.append(f"{label}: dispatch tracking differs from the approved public record")
            if not valid_iso_date(dispatch.get("sentOn")) or dispatch.get("sentOn") > EXPECTED_DATE:
                errors.append(f"{label}: sentOn must be valid and no later than verificationDate")
            if dispatch.get("publicAuthorityReference") is not None:
                errors.append(f"{label}: no public authority reference is approved")
        for field in (
            "requestId", "countryIso2", "purposeEn", "purposeFi",
            "queueBoundaryEn", "queueBoundaryFi",
        ):
            require_text(request.get(field), f"{label}.{field}", errors)
        for field in ("recordsRequestedEn", "recordsRequestedFi"):
            require_text_list(request.get(field), f"{label}.{field}", errors)
        nested_schemas = (
            (request.get("authority"), AUTHORITY_KEYS, f"{label}.authority"),
            (request.get("requestChannel"), LINKED_AUTHORITY_KEYS, f"{label}.requestChannel"),
            (request.get("legalBasis"), AUTHORITY_KEYS, f"{label}.legalBasis"),
        )
        nested_valid = all(
            require_exact_keys(value, keys, nested_label, errors)
            for value, keys, nested_label in nested_schemas
        )
        if nested_valid:
            for nested_name in ("authority", "requestChannel", "legalBasis"):
                for field, value in request[nested_name].items():
                    require_text(value, f"{label}.{nested_name}.{field}", errors)
        if request.get("requestChannel", {}).get("url") != EXPECTED_BVL_CHANNEL_URL:
            errors.append(f"{label}: BVL official contact route differs from the verified URL")
        queue_en = str(request.get("queueBoundaryEn", "")).casefold()
        queue_fi = str(request.get("queueBoundaryFi", "")).casefold()
        if not all(term in queue_en for term in (
            "adds no country", "12-sent/8-draft", "does not replace",
        )):
            errors.append(f"{label}: English queue boundary is incomplete")
        if not all(term in queue_fi for term in (
            "ei lisää maata", "12 lähetetyn ja 8 luonnoksen", "ei korvaa",
        )):
            errors.append(f"{label}: Finnish queue boundary is incomplete")
        sources = request.get("officialSources")
        if not isinstance(sources, list) or len(sources) < 2:
            errors.append(f"{label}: at least two official sources are required")
            continue
        allowed_hosts = OFFICIAL_HOSTS.get(request.get("countryIso2"), set())
        urls = [request.get("requestChannel", {}).get("url")]
        source_hosts: set[str] = set()
        for source in sources:
            if not require_exact_keys(source, SOURCE_KEYS, f"{label}.officialSources[]", errors):
                continue
            for field, value in source.items():
                require_text(value, f"{label}.officialSources[].{field}", errors)
            if not valid_iso_date(source.get("verifiedOn")) or source["verifiedOn"] > EXPECTED_DATE:
                errors.append(f"{label}: official source verification date must be valid and no later than {EXPECTED_DATE}")
            urls.append(source.get("url"))
        source_urls = {
            source.get("url") for source in sources if isinstance(source, dict)
        }
        if source_urls != {EXPECTED_BVL_GUIDANCE_URL, EXPECTED_TABAKERZV_25_URL}:
            errors.append(f"{label}: BVL guidance or official section 25 source differs from the verified set")
        for url in urls:
            if not isinstance(url, str):
                errors.append(f"{label}: official URL must be a string")
                continue
            parsed = urlparse(url)
            host = (parsed.hostname or "").casefold()
            if parsed.scheme != "https" or not host or parsed.username or parsed.password:
                errors.append(f"{label}: URL must be a public HTTPS URL without credentials: {url}")
            elif not official_host(host, allowed_hosts):
                errors.append(f"{label}: URL host is not on the country official-domain allowlist: {host}")
            source_hosts.add(host)
        if not any(official_host(host, {"bund.de"}) for host in source_hosts):
            errors.append(f"{label}: BVL official source or channel is required")
        if "www.gesetze-im-internet.de" not in source_hosts:
            errors.append(f"{label}: official section 25 law source is required")
    if supplementary_ids != set(EXPECTED_SUPPLEMENTARY_DISPATCH):
        errors.append("supplementary request IDs differ from the approved public record")

    routes = program.get("routes")
    if not isinstance(routes, list) or len(routes) != 20:
        errors.append("programme must contain exactly 20 routes")
        return
    if any(not isinstance(route, dict) for route in routes):
        errors.append("every route must be an object")
        return

    iso_codes = [route.get("countryIso2") for route in routes]
    if any(not isinstance(iso, str) for iso in iso_codes):
        errors.append("every route must have a string countryIso2")
        return
    if len(set(iso_codes)) != 20:
        errors.append("programme must contain exactly 20 unique country codes")
    if set(iso_codes) != set(OFFICIAL_HOSTS):
        errors.append("country set differs from the validated official-host allowlist")
    ranks = [route.get("operationalRank") for route in routes]
    if any(type(rank) is not int for rank in ranks):
        errors.append("operationalRank values must be integers")
        return
    if sorted(ranks) != list(range(1, 21)):
        errors.append("operationalRank values must be the unique integers 1-20")
    priorities = [route.get("priorityCode") for route in routes]
    if any(not isinstance(priority, str) or not priority.strip() for priority in priorities):
        errors.append("priorityCode values must be non-empty strings")
        return
    if len(set(priorities)) != 20:
        errors.append("priorityCode values must be unique")

    sent_countries: set[str] = set()
    process_response_countries: set[str] = set()
    structural_response_countries: set[str] = set()
    sales_response_countries: set[str] = set()
    for route in routes:
        iso = route.get("countryIso2", "?")
        label = f"route {iso}"
        if not require_exact_keys(route, ROUTE_KEYS, label, errors):
            continue
        if route.get("status") not in ROUTE_STATUS_VALUES:
            errors.append(f"{label}: status must be sent or draft_not_sent")
        dispatch = route.get("dispatch")
        if require_exact_keys(dispatch, DISPATCH_KEYS, f"{label}.dispatch", errors):
            if dispatch.get("state") not in ROUTE_STATUS_VALUES:
                errors.append(f"{label}: invalid dispatch state")
            if dispatch.get("responseState") not in RESPONSE_STATE_VALUES:
                errors.append(f"{label}: invalid response state")
            if dispatch.get("responseState") in PROCESS_RESPONSE_STATE_VALUES:
                process_response_countries.add(iso)
                if dispatch.get("publicAuthorityReference") is not None:
                    errors.append(f"{label}: process response must not expose a correspondence reference")
            if dispatch.get("responseState") in STRUCTURAL_RESPONSE_STATE_VALUES:
                structural_response_countries.add(iso)
                if dispatch.get("publicAuthorityReference") is not None:
                    errors.append(
                        f"{label}: structural response must not expose a correspondence reference"
                    )
            if dispatch.get("responseState") in SALES_RESPONSE_STATE_VALUES:
                sales_response_countries.add(iso)
            if route.get("status") != dispatch.get("state"):
                errors.append(f"{label}: route status and dispatch state must match")
            expected_dispatch = EXPECTED_DISPATCH.get(iso, {
                "state": "draft_not_sent",
                "sentOn": None,
                "publicAuthorityReference": None,
                "responseState": "not_applicable",
            })
            if dispatch != expected_dispatch:
                errors.append(f"{label}: dispatch tracking differs from the approved public record")
            if dispatch.get("state") == "sent":
                sent_countries.add(iso)
                if not valid_iso_date(dispatch.get("sentOn")):
                    errors.append(f"{label}: sentOn must be an ISO calendar date")
                elif dispatch["sentOn"] > EXPECTED_DATE:
                    errors.append(f"{label}: sentOn cannot be after verificationDate")
                reference = dispatch.get("publicAuthorityReference")
                if reference is not None and (
                    not isinstance(reference, str)
                    or not re.fullmatch(r"[A-Z0-9][A-Z0-9 ./_-]{2,39}", reference)
                ):
                    errors.append(f"{label}: publicAuthorityReference is unsafe")
            elif any(dispatch.get(field) is not None for field in ("sentOn", "publicAuthorityReference")):
                errors.append(f"{label}: draft route cannot expose dispatch data")
        for field in (
            "countryEn",
            "countryFi",
            "rationaleEn",
            "rationaleFi",
            "recordsRequestedEn",
            "recordsRequestedFi",
            "primaryAuthority",
            "requestChannel",
            "legalBasis",
            "fallbackAuthority",
            "officialSources",
        ):
            if not route.get(field):
                errors.append(f"{label}: missing {field}")
        for field in ("priorityCode", "wave", "countryIso2", "countryEn", "countryFi", "rationaleEn", "rationaleFi"):
            require_text(route.get(field), f"{label}.{field}", errors)
        for field in ("recordsRequestedEn", "recordsRequestedFi", "languages"):
            require_text_list(route.get(field), f"{label}.{field}", errors)

        nested_schemas = (
            (route.get("primaryAuthority"), AUTHORITY_KEYS, f"{label}.primaryAuthority"),
            (route.get("requestChannel"), LINKED_AUTHORITY_KEYS, f"{label}.requestChannel"),
            (route.get("legalBasis"), AUTHORITY_KEYS, f"{label}.legalBasis"),
            (route.get("requesterEligibility"), ELIGIBILITY_KEYS, f"{label}.requesterEligibility"),
            (route.get("fallbackAuthority"), LINKED_AUTHORITY_KEYS, f"{label}.fallbackAuthority"),
        )
        if not all(require_exact_keys(value, keys, nested_label, errors)
                   for value, keys, nested_label in nested_schemas):
            continue
        for nested_name in ("primaryAuthority", "requestChannel", "legalBasis", "fallbackAuthority"):
            for field, value in route[nested_name].items():
                require_text(value, f"{label}.{nested_name}.{field}", errors)

        eligibility = route.get("requesterEligibility", {})
        if eligibility.get("localRequester") not in LOCAL_REQUESTER_VALUES:
            errors.append(f"{label}: invalid or missing localRequester value")
        for language in ("En", "Fi"):
            caveat = eligibility.get(f"caveat{language}", "")
            if not isinstance(caveat, str) or len(caveat.strip()) < 40:
                errors.append(f"{label}: substantive eligibility caveat{language} is required")

        if iso in {"ID", "PH"} and eligibility.get("localRequester") != "required":
            errors.append(f"{label}: local requester must be marked required")
        if iso == "CA" and eligibility.get("localRequester") != "conditional":
            errors.append("route CA: formal requester eligibility must be marked conditional")

        sources = route.get("officialSources", [])
        if not isinstance(sources, list) or not sources:
            errors.append(f"{label}: at least one official source is required")
            continue
        sources_valid = True
        for source in sources:
            if not require_exact_keys(source, SOURCE_KEYS, f"{label}.officialSources[]", errors):
                sources_valid = False
                continue
            for field, value in source.items():
                if not require_text(value, f"{label}.officialSources[].{field}", errors):
                    sources_valid = False
            if not valid_iso_date(source.get("verifiedOn")) or source["verifiedOn"] > EXPECTED_DATE:
                errors.append(f"{label}: official source verification date must be valid and no later than {EXPECTED_DATE}")
        if not sources_valid:
            continue
        if iso == "SE" and EXPECTED_SWEDEN_CONTEXT_URL not in {
            source.get("url") for source in sources
        }:
            errors.append("route SE: official notified-product context source is required")

        allowed_hosts = OFFICIAL_HOSTS.get(iso, set())
        seen_urls: set[str] = set()
        for url in route_urls(route):
            if url in seen_urls:
                errors.append(f"{label}: duplicate official URL {url}")
            seen_urls.add(url)
            parsed = urlparse(url)
            host = (parsed.hostname or "").casefold()
            if parsed.scheme != "https" or not host or parsed.username or parsed.password:
                errors.append(f"{label}: URL must be a public HTTPS URL without credentials: {url}")
            elif not official_host(host, allowed_hosts):
                errors.append(f"{label}: URL host is not on the country official-domain allowlist: {host}")

    if sent_countries != set(EXPECTED_DISPATCH):
        errors.append("sent country set must match the approved 12-country public record")
    if sum(route.get("status") == "sent" for route in routes) != 12:
        errors.append("programme must contain exactly 12 sent routes and 8 drafts")
    if process_response_countries != EXPECTED_PROCESS_RESPONSE_COUNTRIES:
        errors.append("process-response country set must match the approved three-country public record")
    if structural_response_countries != EXPECTED_STRUCTURAL_RESPONSE_COUNTRIES:
        errors.append("structural-response country set must contain Sweden only")
    if sales_response_countries != EXPECTED_SALES_RESPONSE_COUNTRIES:
        errors.append("annual-sales-response country set must remain empty")
    private_metadata_paths = list(find_private_metadata_keys(program))
    if private_metadata_paths:
        errors.append("private correspondence metadata is forbidden: " + ", ".join(private_metadata_paths))
    programme_strings = list(strings(program))
    combined = "\n".join(programme_strings).casefold()
    for phrase in FORBIDDEN_PUBLIC_TEXT:
        if phrase in combined:
            errors.append(f"public programme contains forbidden text {phrase!r}")
    for phrase in FORBIDDEN_PROCESS_OVERSTATEMENTS:
        if phrase in combined:
            errors.append(f"public programme overstates a process response: {phrase!r}")
    if "no request has been sent" in combined or "yhtäkään pyyntöä ei ole lähetetty" in combined:
        errors.append("public programme contains a false all-draft claim")
    if any(EMAIL_ADDRESS_RE.search(value) for value in programme_strings):
        errors.append("public programme contains an email address")
    if any(contains_private_identifier(value) for value in programme_strings):
        errors.append("public programme contains a private identifier fingerprint")
    notice_en = str(program.get("independenceNoticeEn", "")).casefold()
    notice_fi = str(program.get("independenceNoticeFi", "")).casefold()
    if not all(term in notice_en for term in (
        "privacy-safe categorical process or evidence state",
        "official aggregate registration-structure counts",
        "not annual sales",
        "sold device units",
        "sold liquid volume",
        "donor evidence",
        "substantive data",
        "fee commitment",
    )):
        errors.append(
            "English independence notice must distinguish process, structural data, "
            "annual sales, donor evidence and fee commitment"
        )
    if not all(term in notice_fi for term in (
        "tietosuojatun kategorisen prosessi- tai evidenssitilan",
        "viralliset aggregoidut rekisterirakenneluvut",
        "ei vuosimyynnistä",
        "myytyjen laitteiden kappalemäärästä",
        "myydystä nestemäärästä",
        "luovuttajaevidenssistä",
        "sisällöllisenä datana",
        "maksusitoumuksena",
    )):
        errors.append(
            "Finnish independence notice must distinguish process, structural data, "
            "annual sales, donor evidence and fee commitment"
        )


def validate_outputs(program: dict[str, Any], errors: list[str]) -> None:
    expected_json = render_json(program)
    expected_csv = render_csv(program)
    if not OUTPUT_JSON.exists() or OUTPUT_JSON.read_bytes() != expected_json:
        errors.append("site/data/top20-data-request-routes.json is missing or stale")
    else:
        published = read_json(OUTPUT_JSON)
        if published != normalised_program(program):
            errors.append("published JSON differs semantically from source")
        if list(find_private_metadata_keys(published)):
            errors.append("published JSON contains private correspondence metadata")

    if not OUTPUT_CSV.exists() or OUTPUT_CSV.read_bytes() != expected_csv:
        errors.append("site/data/top20-data-request-routes.csv is missing or stale")
    else:
        rows = list(csv.DictReader(io.StringIO(OUTPUT_CSV.read_text(encoding="utf-8"))))
        if len(rows) != 20 or len({row["countryIso2"] for row in rows}) != 20:
            errors.append("published CSV must contain exactly 20 unique countries")
        if rows and list(rows[0]) != CSV_FIELDS:
            errors.append("published CSV columns differ from the privacy-safe tracking schema")
        if {row["countryIso2"] for row in rows if row["status"] == "sent"} != set(EXPECTED_DISPATCH):
            errors.append("published CSV sent country set differs from the approved 12-country public record")
        if any(row["status"] not in ROUTE_STATUS_VALUES for row in rows):
            errors.append("published CSV contains an unsupported status")
        if any(row["responseState"] not in RESPONSE_STATE_VALUES for row in rows):
            errors.append("published CSV contains an unsupported response state")
        if {
            row["countryIso2"] for row in rows
            if row["responseState"] in PROCESS_RESPONSE_STATE_VALUES
        } != EXPECTED_PROCESS_RESPONSE_COUNTRIES:
            errors.append("published CSV process-response country set differs from the approved three-country record")
        if {
            row["countryIso2"] for row in rows
            if row["responseState"] in STRUCTURAL_RESPONSE_STATE_VALUES
        } != EXPECTED_STRUCTURAL_RESPONSE_COUNTRIES:
            errors.append("published CSV structural-response country set must contain Sweden only")
        if {
            row["countryIso2"] for row in rows
            if row["responseState"] in SALES_RESPONSE_STATE_VALUES
        } != EXPECTED_SALES_RESPONSE_COUNTRIES:
            errors.append("published CSV annual-sales-response country set must remain empty")
        if any(
            row["publicAuthorityReference"]
            for row in rows
            if row["responseState"] in (
                PROCESS_RESPONSE_STATE_VALUES | STRUCTURAL_RESPONSE_STATE_VALUES
            )
        ):
            errors.append("published CSV exposes a response correspondence reference")
        if any(row["isMarketSizeRanking"] != "false" for row in rows):
            errors.append("published CSV must mark isMarketSizeRanking=false")
        if any(row["stateUniverseCount"] != str(EXPECTED_STATE_UNIVERSE_COUNT) for row in rows):
            errors.append("published CSV must retain the 195-state research universe")
        if any(row["evidenceStackLayerCount"] != "6" for row in rows):
            errors.append("published CSV must retain the six-layer evidence stack")
        germany_rows = [row for row in rows if row["countryIso2"] == "DE"]
        if len(germany_rows) != 1 or (
            germany_rows[0]["supplementaryRequestCount"] != "1"
            or germany_rows[0]["supplementarySentRequestCount"] != "1"
            or germany_rows[0]["supplementaryRequestIds"] != "DE-BVL-TABAKERZV25-ANNUAL-SALES"
        ):
            errors.append("published CSV must expose the one sent German BVL supplementary route")
        if any(
            row["supplementaryRequestCount"] != "0"
            or row["supplementarySentRequestCount"] != "0"
            or row["supplementaryRequestIds"]
            for row in rows
            if row["countryIso2"] != "DE"
        ):
            errors.append("published CSV must not add supplementary routes to other countries")
        if any(
            re.sub(r"[^a-z]", "", header.casefold()) in PRIVATE_METADATA_KEYS
            for header in (rows[0] if rows else {})
        ):
            errors.append("published CSV contains a private correspondence metadata column")

    template_pairs = (
        (
            SOURCE_TEMPLATE_EN, OUTPUT_TEMPLATE_EN, "English", "DRAFT — NOT SENT",
            {"[AUTHORITY]", "[COUNTRY]", "[LEGAL BASIS]", "[FEE LIMIT]", "[NAME]",
             "[INDEPENDENT EVIDENCE RESEARCH PROJECT]", "[CONTACT DETAILS]"},
        ),
        (
            SOURCE_TEMPLATE_FI, OUTPUT_TEMPLATE_FI, "Finnish", "LUONNOS — EI LÄHETETTY",
            {"[MAA]", "[OIKEUSPERUSTA]", "[MAKSURAJA]", "[NIMI]",
             "[RIIPPUMATON EVIDENSSITUTKIMUSHANKE]", "[YHTEYSTIEDOT]"},
        ),
    )
    for source_path, output_path, language, required_banner, required_placeholders in template_pairs:
        if not output_path.exists() or output_path.read_bytes() != source_path.read_bytes():
            errors.append(f"{language} public request template is missing or stale")
        text = source_path.read_text(encoding="utf-8")
        if text.splitlines()[:1] != [required_banner]:
            errors.append(f"{language} request template must begin with {required_banner!r}")
        missing_placeholders = sorted(required_placeholders - set(re.findall(r"\[[A-Z ÄÖ]+]", text)))
        if missing_placeholders:
            errors.append(f"{language} request template is missing neutral placeholders: {missing_placeholders}")
        if "Pixan" not in text or "represent" not in text.casefold() and "edusta" not in text.casefold():
            errors.append(f"{language} request template lacks the independence notice")
        if any(phrase in text.casefold() for phrase in FORBIDDEN_PUBLIC_TEXT):
            errors.append(f"{language} request template contains a forbidden negotiation reference")
        if contains_private_identifier(text):
            errors.append(f"{language} request template contains a private identifier fingerprint")


def main() -> int:
    errors: list[str] = []
    try:
        program = read_json(SOURCE_PATH)
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL: cannot read source programme: {error}", file=sys.stderr)
        return 1

    validate_program(program, errors)
    validate_outputs(program, errors)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print(
        "PASS: schema v3 with a 195-state six-layer evidence stack; 12 sent, 8 draft and "
        "3 privacy-safe process-response country routes; one official Sweden structural-data "
        "response with sales unavailable; one sent non-counting German BVL supplementary "
        "route; 0 annual-sales-data responses, operational ranking, official HTTPS URLs, "
        "requester caveats, and generated files verified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
