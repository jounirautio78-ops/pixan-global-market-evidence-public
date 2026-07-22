#!/usr/bin/env python3
"""Build public Top-20 official-data request programme artefacts.

The source programme combines a planned-route register with a deliberately
minimal public dispatch record. This builder only publishes deterministic
JSON/CSV and copies the two neutral draft templates; it does not contact an
authority or send a request.
"""

from __future__ import annotations

import copy
import csv
import io
import json
import os
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "source" / "top20-data-request-routes.json"
SOURCE_TEMPLATE_EN = ROOT / "source" / "data-request-template-en.txt"
SOURCE_TEMPLATE_FI = ROOT / "source" / "data-request-template-fi.txt"
OUTPUT_JSON = ROOT / "site" / "data" / "top20-data-request-routes.json"
OUTPUT_CSV = ROOT / "site" / "data" / "top20-data-request-routes.csv"
OUTPUT_TEMPLATE_EN = ROOT / "site" / "downloads" / "data-request-template-en.txt"
OUTPUT_TEMPLATE_FI = ROOT / "site" / "downloads" / "data-request-template-fi.txt"

CSV_FIELDS = [
    "operationalRank",
    "priorityCode",
    "wave",
    "countryIso2",
    "countryEn",
    "countryFi",
    "status",
    "dispatchState",
    "sentOn",
    "publicAuthorityReference",
    "responseState",
    "rankingType",
    "isMarketSizeRanking",
    "rationaleEn",
    "rationaleFi",
    "primaryAuthorityEn",
    "primaryAuthorityFi",
    "recordsRequestedEn",
    "recordsRequestedFi",
    "requestChannelEn",
    "requestChannelFi",
    "requestUrl",
    "legalBasisEn",
    "legalBasisFi",
    "languages",
    "localRequester",
    "eligibilityCaveatEn",
    "eligibilityCaveatFi",
    "fallbackAuthorityEn",
    "fallbackAuthorityFi",
    "fallbackUrl",
    "officialSourceUrls",
    "verificationDate",
]


def load_program() -> dict[str, Any]:
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def normalised_program(program: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(program)
    result["routes"] = sorted(result["routes"], key=lambda route: route["operationalRank"])
    return result


def render_json(program: dict[str, Any]) -> bytes:
    normalised = normalised_program(program)
    return (json.dumps(normalised, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def flatten_route(program: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    return {
        "operationalRank": route["operationalRank"],
        "priorityCode": route["priorityCode"],
        "wave": route["wave"],
        "countryIso2": route["countryIso2"],
        "countryEn": route["countryEn"],
        "countryFi": route["countryFi"],
        "status": route["status"],
        "dispatchState": route["dispatch"]["state"],
        "sentOn": route["dispatch"]["sentOn"] or "",
        "publicAuthorityReference": route["dispatch"]["publicAuthorityReference"] or "",
        "responseState": route["dispatch"]["responseState"],
        "rankingType": program["ranking"]["type"],
        "isMarketSizeRanking": str(program["ranking"]["isMarketSizeRanking"]).lower(),
        "rationaleEn": route["rationaleEn"],
        "rationaleFi": route["rationaleFi"],
        "primaryAuthorityEn": route["primaryAuthority"]["nameEn"],
        "primaryAuthorityFi": route["primaryAuthority"]["nameFi"],
        "recordsRequestedEn": " | ".join(route["recordsRequestedEn"]),
        "recordsRequestedFi": " | ".join(route["recordsRequestedFi"]),
        "requestChannelEn": route["requestChannel"]["nameEn"],
        "requestChannelFi": route["requestChannel"]["nameFi"],
        "requestUrl": route["requestChannel"]["url"],
        "legalBasisEn": route["legalBasis"]["nameEn"],
        "legalBasisFi": route["legalBasis"]["nameFi"],
        "languages": " | ".join(route["languages"]),
        "localRequester": route["requesterEligibility"]["localRequester"],
        "eligibilityCaveatEn": route["requesterEligibility"]["caveatEn"],
        "eligibilityCaveatFi": route["requesterEligibility"]["caveatFi"],
        "fallbackAuthorityEn": route["fallbackAuthority"]["nameEn"],
        "fallbackAuthorityFi": route["fallbackAuthority"]["nameFi"],
        "fallbackUrl": route["fallbackAuthority"]["url"],
        "officialSourceUrls": " | ".join(source["url"] for source in route["officialSources"]),
        "verificationDate": program["verificationDate"],
    }


def render_csv(program: dict[str, Any]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for route in sorted(program["routes"], key=lambda item: item["operationalRank"]):
        writer.writerow(flatten_route(program, route))
    return buffer.getvalue().encode("utf-8")


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        handle.write(content)
        temporary_path = Path(handle.name)
    os.replace(temporary_path, path)


def build() -> list[Path]:
    program = load_program()
    outputs = {
        OUTPUT_JSON: render_json(program),
        OUTPUT_CSV: render_csv(program),
        OUTPUT_TEMPLATE_EN: SOURCE_TEMPLATE_EN.read_bytes(),
        OUTPUT_TEMPLATE_FI: SOURCE_TEMPLATE_FI.read_bytes(),
    }
    for path, content in outputs.items():
        write_atomic(path, content)
    return list(outputs)


def main() -> int:
    outputs = build()
    for path in outputs:
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
