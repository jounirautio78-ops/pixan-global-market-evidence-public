#!/usr/bin/env python3
"""Refresh the fail-closed UN195 global base observations.

The only numeric observations retrieved in v27 are three World Bank WDI
series. WHO and UN Comtrade are represented as explicit acquisition routes:
every country remains queued and missing until a later, separately reviewed
retrieval step supplies admissible observations.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from build_atlas import COUNTRY_CATALOG


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "source" / "global-base-config.json"
OUTPUT_PATH = ROOT / "source" / "global-base-observations.json"
WORLD_BANK_API = "https://api.worldbank.org/v2/country/all/indicator/{series}"


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def world_bank_url(series: str, start_year: int, end_year: int) -> str:
    query = urlencode(
        {
            "format": "json",
            "date": f"{start_year}:{end_year}",
            "per_page": "20000",
            "footnote": "y",
        }
    )
    return f"{WORLD_BANK_API.format(series=series)}?{query}"


def fetch_world_bank_rows(
    series: str,
    start_year: int,
    end_year: int,
    *,
    attempts: int = 3,
    timeout_seconds: int = 45,
) -> tuple[str, list[dict[str, Any]]]:
    """Fetch one complete World Bank indicator response with bounded retries."""

    url = world_bank_url(series, start_year, end_year)
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Pixan-Evidence-Center/1.0 (+official-open-data-snapshot)",
        },
    )
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                payload = json.load(response)
            if (
                not isinstance(payload, list)
                or len(payload) < 2
                or not isinstance(payload[1], list)
            ):
                raise ValueError(f"Unexpected World Bank payload for {series}")
            rows = [row for row in payload[1] if isinstance(row, dict)]
            return url, rows
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(attempt)
    raise RuntimeError(
        f"World Bank retrieval failed for {series} after {attempts} attempts"
    ) from last_error


def latest_non_null_by_country(
    rows: list[dict[str, Any]],
    country_iso2s: set[str],
) -> dict[str, dict[str, Any]]:
    """Return each country's newest non-null row without changing its year."""

    selected: dict[str, dict[str, Any]] = {}
    for row in rows:
        country = row.get("country")
        iso2 = country.get("id") if isinstance(country, dict) else None
        if iso2 not in country_iso2s or row.get("value") is None:
            continue
        try:
            year = int(row.get("date"))
        except (TypeError, ValueError):
            continue
        current = selected.get(iso2)
        if current is None or year > int(current["date"]):
            selected[iso2] = row
    return selected


def observation(
    *,
    iso2: str,
    measure: dict[str, Any],
    source_period: int | None,
    value: int | float | None,
    data_status: str,
    acquisition_status: str,
    missing_reason: str | None,
    source_url: str,
) -> dict[str, Any]:
    return {
        "observationId": f"global-base-{iso2.lower()}-{measure['measureId']}",
        "countryIso2": iso2,
        "measureId": measure["measureId"],
        "sourceId": measure["sourceId"],
        "sourceSeries": measure["sourceSeries"],
        "sourcePeriod": source_period,
        "value": value,
        "unit": measure["unit"],
        "currency": measure["currency"],
        "dataStatus": data_status,
        "acquisitionStatus": acquisition_status,
        "missingReason": missing_reason,
        "retailSalesEligible": False,
        "sourceUrl": source_url,
    }


def build_snapshot(
    config: dict[str, Any],
    *,
    retrieved_at: str,
) -> dict[str, Any]:
    countries = [dict(country) for country in COUNTRY_CATALOG]
    iso2s = {country["iso2"] for country in countries}
    if len(countries) != 195 or len(iso2s) != 195:
        raise ValueError("COUNTRY_CATALOG must contain exactly 195 unique ISO2 entries")

    policy = config["snapshotPolicy"]
    start_year = int(policy["startYear"])
    end_year = int(policy["endYear"])
    measures = config["measures"]
    active = [measure for measure in measures if measure["retrievalMode"] == "active"]
    queued = [measure for measure in measures if measure["retrievalMode"] == "queued"]

    observations: list[dict[str, Any]] = []
    queries: list[dict[str, Any]] = []
    for measure in active:
        url, rows = fetch_world_bank_rows(
            measure["sourceSeries"],
            start_year,
            end_year,
        )
        selected = latest_non_null_by_country(rows, iso2s)
        queries.append(
            {
                "sourceSeries": measure["sourceSeries"],
                "sourceUrl": url,
                "returnedRowCount": len(rows),
                "matchedCountryCount": len(selected),
            }
        )
        for country in countries:
            iso2 = country["iso2"]
            row = selected.get(iso2)
            if row is None:
                observations.append(
                    observation(
                        iso2=iso2,
                        measure=measure,
                        source_period=None,
                        value=None,
                        data_status="missing",
                        acquisition_status="validated",
                        missing_reason="no_non_null_value_2020_2024",
                        source_url=url,
                    )
                )
                continue
            observations.append(
                observation(
                    iso2=iso2,
                    measure=measure,
                    source_period=int(row["date"]),
                    value=row["value"],
                    data_status="observed",
                    acquisition_status="validated",
                    missing_reason=None,
                    source_url=url,
                )
            )

    source_by_id = {source["sourceId"]: source for source in config["sources"]}
    for measure in queued:
        source = source_by_id[measure["sourceId"]]
        for country in countries:
            observations.append(
                observation(
                    iso2=country["iso2"],
                    measure=measure,
                    source_period=None,
                    value=None,
                    data_status="missing",
                    acquisition_status="queued",
                    missing_reason="not_retrieved_in_v27",
                    source_url=source["landingUrl"],
                )
            )

    observations.sort(key=lambda item: (item["countryIso2"], item["measureId"]))
    return {
        "schemaVersion": config["schemaVersion"],
        "asOf": config["asOf"],
        "universe": config["universe"]["id"],
        "countryCount": len(countries),
        "sourceWindow": {
            "startYear": start_year,
            "endYear": end_year,
            "selection": policy["selection"],
        },
        "snapshot": {
            "sourceId": "WB-WDI",
            "retrievedAt": retrieved_at,
            "queries": queries,
        },
        "observations": observations,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument(
        "--retrieved-at",
        help="ISO-8601 UTC snapshot time; defaults to the current UTC time",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    retrieved_at = args.retrieved_at or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")
    config = read_json(args.config)
    snapshot = build_snapshot(config, retrieved_at=retrieved_at)
    atomic_write_json(args.output, snapshot)
    print(
        f"Wrote {len(snapshot['observations'])} observations for "
        f"{snapshot['countryCount']} countries to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
