#!/usr/bin/env python3
"""Publish reviewed independent benchmark controls into the static site."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COPIES = {
    ROOT / "source" / "US_INDEPENDENT_BENCHMARK_CONTROL_2026-07-28.json":
        ROOT / "site" / "data" / "us-independent-benchmark-control.json",
    ROOT / "source" / "open-official-extraction-wave-es-kr-jp.json":
        ROOT / "site" / "data" / "open-official-extraction-wave-es-kr-jp.json",
    ROOT / "source" / "schemas" / "us-independent-benchmark-sample.schema.json":
        ROOT / "site" / "schemas" / "us-independent-benchmark-sample.schema.json",
    ROOT / "source" / "schemas" / "open-official-extraction-wave.schema.json":
        ROOT / "site" / "schemas" / "open-official-extraction-wave.schema.json",
    ROOT / "source" / "investor-disclosure-control.json":
        ROOT / "site" / "data" / "investor-disclosure-control.json",
    ROOT / "source" / "schemas" / "investor-disclosure-control.schema.json":
        ROOT / "site" / "schemas" / "investor-disclosure-control.schema.json",
}


def main() -> None:
    for source, target in COPIES.items():
        raw = source.read_bytes()
        json.loads(raw)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        print(f"{source.relative_to(ROOT)} -> {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
