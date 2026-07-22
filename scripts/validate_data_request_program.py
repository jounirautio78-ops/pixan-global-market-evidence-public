#!/usr/bin/env python3
"""Fail-closed validation for the public Top-20 data-request programme."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from build_data_request_program import (
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


EXPECTED_DATE = "2026-07-22"
EXPECTED_STATUS = "draft_not_sent"
EXPECTED_RANKING_TYPE = "operational_evidence_acquisition_order"
LOCAL_REQUESTER_VALUES = {"not_required", "recommended", "conditional", "required"}
SENT_DATE_KEYS = {
    "sentat",
    "sentdate",
    "datesent",
    "requestsentat",
    "requestsentdate",
    "lastsentat",
    "lastsentdate",
}
FORBIDDEN_PUBLIC_TEXT = ("/users/", "file://")
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
    "independenceNoticeEn", "independenceNoticeFi", "ranking", "scope", "routes",
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
ROUTE_KEYS = {
    "operationalRank", "priorityCode", "wave", "countryIso2", "countryEn", "countryFi",
    "status", "rationaleEn", "rationaleFi", "primaryAuthority", "recordsRequestedEn",
    "recordsRequestedFi", "requestChannel", "legalBasis", "languages",
    "requesterEligibility", "fallbackAuthority", "officialSources",
}
AUTHORITY_KEYS = {"nameEn", "nameFi"}
LINKED_AUTHORITY_KEYS = {"nameEn", "nameFi", "url"}
ELIGIBILITY_KEYS = {"localRequester", "caveatEn", "caveatFi"}
SOURCE_KEYS = {"labelEn", "labelFi", "url", "verifiedOn"}

OFFICIAL_HOSTS = {
    "DE": {"bund.de", "destatis.de", "zoll.de"},
    "CA": {"canada.ca"},
    "US": {"ftc.gov", "usitc.gov", "fda.gov", "cbp.gov"},
    "CN": {"stats.gov.cn", "customs.gov.cn", "samr.gov.cn"},
    "PL": {"gov.pl"},
    "GB": {"gov.uk"},
    "SE": {"folkhalsomyndigheten.se", "skatteverket.se", "tullverket.se"},
    "IT": {"adm.gov.it", "salute.gov.it"},
    "FR": {"anses.fr", "cada.fr", "gouv.fr", "insee.fr"},
    "ES": {"gob.es"},
    "NL": {"rijksoverheid.nl", "rivm.nl", "belastingdienst.nl"},
    "FI": {"suomi.fi", "vero.fi", "finlex.fi", "tulli.fi"},
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


def find_sent_date_keys(value: Any, path: str = "root"):
    if isinstance(value, dict):
        for key, item in value.items():
            normalised = re.sub(r"[^a-z]", "", key.casefold())
            if normalised in SENT_DATE_KEYS:
                yield f"{path}.{key}"
            yield from find_sent_date_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from find_sent_date_keys(item, f"{path}[{index}]")


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
    if program.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    for field in ("programmeId", "independenceNoticeEn", "independenceNoticeFi"):
        require_text(program.get(field), field, errors)
    if program.get("verificationDate") != EXPECTED_DATE:
        errors.append(f"verificationDate must be {EXPECTED_DATE}")
    if program.get("status") != EXPECTED_STATUS:
        errors.append(f"programme status must be {EXPECTED_STATUS}")
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

    for route in routes:
        iso = route.get("countryIso2", "?")
        label = f"route {iso}"
        if not require_exact_keys(route, ROUTE_KEYS, label, errors):
            continue
        if route.get("status") != EXPECTED_STATUS:
            errors.append(f"{label}: status must be {EXPECTED_STATUS}")
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
            if source.get("verifiedOn") != EXPECTED_DATE:
                errors.append(f"{label}: every official source must be verified on {EXPECTED_DATE}")
        if not sources_valid:
            continue

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

    sent_date_paths = list(find_sent_date_keys(program))
    if sent_date_paths:
        errors.append("sent-date fields are forbidden: " + ", ".join(sent_date_paths))
    programme_strings = list(strings(program))
    combined = "\n".join(programme_strings).casefold()
    for phrase in FORBIDDEN_PUBLIC_TEXT:
        if phrase in combined:
            errors.append(f"public programme contains forbidden text {phrase!r}")
    if any(contains_private_identifier(value) for value in programme_strings):
        errors.append("public programme contains a private identifier fingerprint")


def validate_outputs(program: dict[str, Any], errors: list[str]) -> None:
    expected_json = render_json(program)
    expected_csv = render_csv(program)
    if not OUTPUT_JSON.exists() or OUTPUT_JSON.read_bytes() != expected_json:
        errors.append("site/data/top20-data-request-routes.json is missing or stale")
    else:
        published = read_json(OUTPUT_JSON)
        if published != normalised_program(program):
            errors.append("published JSON differs semantically from source")
        if list(find_sent_date_keys(published)):
            errors.append("published JSON contains a sent-date field")

    if not OUTPUT_CSV.exists() or OUTPUT_CSV.read_bytes() != expected_csv:
        errors.append("site/data/top20-data-request-routes.csv is missing or stale")
    else:
        rows = list(csv.DictReader(io.StringIO(OUTPUT_CSV.read_text(encoding="utf-8"))))
        if len(rows) != 20 or len({row["countryIso2"] for row in rows}) != 20:
            errors.append("published CSV must contain exactly 20 unique countries")
        if any(row["status"] != EXPECTED_STATUS for row in rows):
            errors.append("published CSV contains a status other than draft_not_sent")
        if any(row["isMarketSizeRanking"] != "false" for row in rows):
            errors.append("published CSV must mark isMarketSizeRanking=false")
        if any("sent" in header.casefold() and "date" in header.casefold() for header in (rows[0] if rows else {})):
            errors.append("published CSV contains a sent-date column")

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
        "PASS: 20 unique draft_not_sent country routes; operational ranking, "
        "official HTTPS URLs, requester caveats, no sent dates, and generated files verified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
