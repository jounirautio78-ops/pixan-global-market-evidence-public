#!/usr/bin/env python3
"""Reproduce the 2022 CTNS vaping-acquisition channel shares.

Usage:
    python scripts/reproduce_canada_ctns_channel_2022.py /path/to/CSV.zip

The input is Statistics Canada's public CTNS 2022 CSV package. The script
prints survey-weighted point estimates and an explicit bootstrap-availability
diagnostic. The reviewed public package has non-matching PUMF and bootstrap ID
sets, so the script withholds standard errors and confidence intervals instead
of silently filling missing replicate weights with zero. It does not download
or retain respondent-level data.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from zipfile import ZipFile


FIELDS = {
    "device_vape_shop": "VAP_40AR",
    "device_other_store_or_online": "VAP_40BR",
    "device_other": "VAP_40HR",
    "liquid_vape_shop": "VAP_41AR",
    "liquid_other_store_or_online": "VAP_41BR",
    "liquid_other": "VAP_41IR",
}
EXPECTED_PUMF_ROWS = 12_133
EXPECTED_BOOTSTRAP_ROWS = 11_526


def zip_member(archive: ZipFile, suffix: str) -> bytes:
    matches = [name for name in archive.namelist() if name.endswith(f"/{suffix}")]
    if len(matches) != 1:
        raise ValueError(f"Expected one ZIP member ending in /{suffix}; found {matches!r}")
    return archive.read(matches[0])


def csv_rows(payload: bytes) -> list[dict[str, str]]:
    stream = io.StringIO(payload.decode("utf-8-sig"), newline="")
    return list(csv.DictReader(stream))


def assess(zip_path: Path) -> dict[str, object]:
    with ZipFile(zip_path) as archive:
        pumf = csv_rows(zip_member(archive, "pumf.csv"))
        bootstrap_rows = csv_rows(zip_member(archive, "pumf_bsw.csv"))

    if len(pumf) != EXPECTED_PUMF_ROWS:
        raise ValueError(f"Unexpected PUMF row count: {len(pumf)}")
    if len(bootstrap_rows) != EXPECTED_BOOTSTRAP_ROWS:
        raise ValueError(f"Unexpected bootstrap row count: {len(bootstrap_rows)}")

    pumf_ids = [row["PUMFID"] for row in pumf]
    bootstrap_ids = [row["PUMFID"] for row in bootstrap_rows]
    if len(set(pumf_ids)) != len(pumf_ids):
        raise ValueError("PUMF contains duplicate PUMFID values")
    if len(set(bootstrap_ids)) != len(bootstrap_ids):
        raise ValueError("Bootstrap file contains duplicate PUMFID values")
    missing_bootstrap_ids = set(pumf_ids) - set(bootstrap_ids)
    extra_bootstrap_ids = set(bootstrap_ids) - set(pumf_ids)

    results: dict[str, object] = {}
    for label, field in FIELDS.items():
        valid = [row for row in pumf if row[field] in {"1", "2"}]
        yes = [row for row in valid if row[field] == "1"]
        weighted_yes = sum(float(row["WTPP"]) for row in yes)
        weighted_valid = sum(float(row["WTPP"]) for row in valid)
        point = weighted_yes / weighted_valid
        results[label] = {
            "field": field,
            "unweightedYes": len(yes),
            "unweightedValid": len(valid),
            "weightedYes": weighted_yes,
            "weightedValid": weighted_valid,
            "percent": point * 100,
            "bootstrapStandardErrorPercentagePoints": None,
            "logit95PercentInterval": None,
        }

    return {
        "source": "Statistics Canada CTNS 2022 public-use microdata file",
        "multiSelectWarning": "Acquisition-source categories do not sum to 100 percent.",
        "bootstrapVariance": {
            "status": "not_computed_id_set_mismatch"
            if missing_bootstrap_ids or extra_bootstrap_ids
            else "not_computed_not_requested",
            "pumfUniqueIds": len(set(pumf_ids)),
            "bootstrapUniqueIds": len(set(bootstrap_ids)),
            "pumfIdsMissingFromBootstrap": len(missing_bootstrap_ids),
            "bootstrapIdsMissingFromPumf": len(extra_bootstrap_ids),
            "reason": "Replicate-weight variance is withheld because the public PUMF and bootstrap ID sets do not match; absent weights are not assumed to be zero."
            if missing_bootstrap_ids or extra_bootstrap_ids
            else "This point-estimate reproducer does not calculate replicate-weight variance.",
        },
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_zip", type=Path, help="Official Statistics Canada CTNS 2022 CSV.zip")
    args = parser.parse_args()
    print(json.dumps(assess(args.csv_zip), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
