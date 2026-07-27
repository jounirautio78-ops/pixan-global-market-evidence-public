#!/usr/bin/env python3
"""Build the privacy-safe public vendor-response control JSON and CSV.

The canonical source deliberately contains no correspondence, personal data,
private file references or licensed vendor material. Missing evidence remains
``not_scored`` and never becomes a numeric zero.
"""

from __future__ import annotations

import copy
import csv
from decimal import Decimal, ROUND_HALF_UP
import io
import json
import os
from pathlib import Path
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "source" / "vendor-response-control.json"
OUTPUT_JSON = ROOT / "site" / "data" / "vendor-response-control.json"
OUTPUT_CSV = ROOT / "site" / "data" / "vendor-response-control.csv"

CSV_FIELDS = [
    "vendorId",
    "vendor",
    "product",
    "requestState",
    "responseState",
    "publicStatusEn",
    "publicStatusFi",
    "sampleReceived",
    "methodologyReceived",
    "coverageMatrixReceived",
    "quoteReceived",
    "officialAnchorReconciliationReceived",
    "transactionUseRightsReceived",
    "totalCostTermsReceived",
    "sampleGateStatus",
    "sampleGateReasonCodes",
    "methodologyGateStatus",
    "methodologyGateReasonCodes",
    "coverageMatrixGateStatus",
    "coverageMatrixGateReasonCodes",
    "officialAnchorReconciliationGateStatus",
    "officialAnchorReconciliationGateReasonCodes",
    "transactionUseRightsGateStatus",
    "transactionUseRightsGateReasonCodes",
    "totalCostTermsGateStatus",
    "totalCostTermsGateReasonCodes",
    "evidenceReceivedCount",
    "evaluatedGateCount",
    "mandatoryGatePassCount",
    "scoringState",
    "weightedScore",
    "purchaseAuthorised",
    "controlVersion",
    "controlAsOf",
]


def load_source() -> dict[str, Any]:
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def gate_results_by_evidence_key(
    vendor: dict[str, Any],
    mandatory_gates: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Return the canonical G1-G6 results keyed by their public evidence key."""

    results = vendor["gateResults"]
    return {
        gate["evidenceKey"]: results[gate["gateCode"]]
        for gate in mandatory_gates
    }


def score_vendor(
    vendor: dict[str, Any],
    criteria: list[dict[str, Any]],
    mandatory_gates: list[dict[str, Any]],
) -> Decimal | None:
    results = vendor["gateResults"]
    if not all(
        results[gate["gateCode"]]["status"] == "pass"
        for gate in mandatory_gates
    ):
        return None
    scores = vendor["criterionScores"]
    if not all(
        isinstance(scores.get(criterion["id"]), (int, float))
        and not isinstance(scores.get(criterion["id"]), bool)
        and Decimal(str(scores[criterion["id"]])).is_finite()
        and Decimal("0") <= Decimal(str(scores[criterion["id"]])) <= Decimal("5")
        for criterion in criteria
    ):
        return None
    value = sum(
        Decimal(str(scores[criterion["id"]])) * Decimal(str(criterion["weight"]))
        for criterion in criteria
    )
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def normalised(source: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(source)
    for vendor in result["vendors"]:
        gate_results = gate_results_by_evidence_key(vendor, result["mandatoryGates"])
        # Compatibility booleans mean gate PASS, not merely that a document was
        # received. The four-state gateResults object is the authoritative view.
        evidence = {
            evidence_key: gate_result["status"] == "pass"
            for evidence_key, gate_result in gate_results.items()
        }
        evidence["quote"] = vendor["quoteReceived"]
        vendor["receivedEvidence"] = evidence
        score = score_vendor(vendor, result["criteria"], result["mandatoryGates"])
        vendor["evidenceReceivedCount"] = sum(
            value is True for value in evidence.values()
        )
        vendor["evaluatedGateCount"] = sum(
            gate_result["status"] != "missing"
            for gate_result in gate_results.values()
        )
        vendor["mandatoryGatePassCount"] = sum(
            gate_result["status"] == "pass"
            for gate_result in gate_results.values()
        )
        vendor["weightedScore"] = None if score is None else float(score)
        vendor["scoringState"] = "not_scored" if score is None else "scored"

    result["summary"] = {
        "trackedVendors": len(result["vendors"]),
        "substantiveResponses": sum(
            vendor["responseState"] == "substantive_response_received"
            for vendor in result["vendors"]
        ),
        "scoredVendors": sum(
            vendor["scoringState"] == "scored" for vendor in result["vendors"]
        ),
        "purchaseAuthorisations": sum(
            vendor["purchaseAuthorised"] is True for vendor in result["vendors"]
        ),
    }
    return result


def render_json(source: dict[str, Any]) -> bytes:
    return (
        json.dumps(normalised(source), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def render_csv(source: dict[str, Any]) -> bytes:
    control = normalised(source)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for vendor in control["vendors"]:
        evidence = vendor["receivedEvidence"]
        gates = gate_results_by_evidence_key(vendor, control["mandatoryGates"])

        def gate_status(evidence_key: str) -> str:
            return gates[evidence_key]["status"]

        def gate_reasons(evidence_key: str) -> str:
            return "|".join(gates[evidence_key]["reasonCodes"])

        writer.writerow(
            {
                "vendorId": vendor["vendorId"],
                "vendor": vendor["vendor"],
                "product": vendor["product"],
                "requestState": vendor["requestState"],
                "responseState": vendor["responseState"],
                "publicStatusEn": vendor["publicStatusEn"],
                "publicStatusFi": vendor["publicStatusFi"],
                "sampleReceived": str(evidence["sample"]).lower(),
                "methodologyReceived": str(evidence["methodology"]).lower(),
                "coverageMatrixReceived": str(evidence["coverageMatrix"]).lower(),
                "quoteReceived": str(evidence["quote"]).lower(),
                "officialAnchorReconciliationReceived": str(
                    evidence["officialAnchorReconciliation"]
                ).lower(),
                "transactionUseRightsReceived": str(
                    evidence["transactionUseRights"]
                ).lower(),
                "totalCostTermsReceived": str(evidence["totalCostTerms"]).lower(),
                "sampleGateStatus": gate_status("sample"),
                "sampleGateReasonCodes": gate_reasons("sample"),
                "methodologyGateStatus": gate_status("methodology"),
                "methodologyGateReasonCodes": gate_reasons("methodology"),
                "coverageMatrixGateStatus": gate_status("coverageMatrix"),
                "coverageMatrixGateReasonCodes": gate_reasons("coverageMatrix"),
                "officialAnchorReconciliationGateStatus": gate_status(
                    "officialAnchorReconciliation"
                ),
                "officialAnchorReconciliationGateReasonCodes": gate_reasons(
                    "officialAnchorReconciliation"
                ),
                "transactionUseRightsGateStatus": gate_status("transactionUseRights"),
                "transactionUseRightsGateReasonCodes": gate_reasons(
                    "transactionUseRights"
                ),
                "totalCostTermsGateStatus": gate_status("totalCostTerms"),
                "totalCostTermsGateReasonCodes": gate_reasons("totalCostTerms"),
                "evidenceReceivedCount": vendor["evidenceReceivedCount"],
                "evaluatedGateCount": vendor["evaluatedGateCount"],
                "mandatoryGatePassCount": vendor["mandatoryGatePassCount"],
                "scoringState": vendor["scoringState"],
                "weightedScore": (
                    ""
                    if vendor["weightedScore"] is None
                    else f'{vendor["weightedScore"]:.2f}'
                ),
                "purchaseAuthorised": str(vendor["purchaseAuthorised"]).lower(),
                "controlVersion": control["version"],
                "controlAsOf": control["asOf"],
            }
        )
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
    source = load_source()
    outputs = {
        OUTPUT_JSON: render_json(source),
        OUTPUT_CSV: render_csv(source),
    }
    for path, content in outputs.items():
        write_atomic(path, content)
    return list(outputs)


def main() -> None:
    outputs = build()
    print(
        "Built vendor-response control outputs: "
        + ", ".join(str(path.relative_to(ROOT)) for path in outputs)
    )


if __name__ == "__main__":
    main()
