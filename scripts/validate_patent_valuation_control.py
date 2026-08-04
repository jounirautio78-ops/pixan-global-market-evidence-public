#!/usr/bin/env python3
"""Validate the public fail-closed, multi-premise patent-valuation control."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TOP_LEVEL_KEYS = {
    "controlId", "controlVersion", "valuationDate", "purposeEn", "purposeFi",
    "status", "ultimatePatentValueEUR", "valueRangeEUR", "ultimateScalarPermitted",
    "ultimateScalarRoleEn", "ultimateScalarRoleFi", "decision", "gateLogic",
    "valuationBasis", "scopeKeyControl", "outputCases", "marketEvidenceRole",
    "donorGateSnapshot", "formulaBridge", "routeBranches", "components",
    "allocationControls", "presentValueConvention", "scenarioControl",
    "independentReview", "collateralRecoveryCase", "hardGates",
    "dependencyControl", "germanyRole", "guardrails",
}
EXPECTED_OUTPUT_IDS = [
    "MARKET-PARTICIPANT-PATENT-FAMILY-VALUE",
    "OWNER-SPECIFIC-STRATEGIC-INVESTMENT-VALUE",
    "RFR-DIRECT-USE-VALUE",
    "THIRD-PARTY-LICENSING-VALUE",
    "PAST-ENFORCEMENT-CLAIM-NPV",
    "EXIT-TRANSACTION-INDICATION",
    "COLLATERAL-RECOVERY-VALUE",
]
EXPECTED_STEP_IDS = [
    "MARKET-EVIDENCE", "SCOPE-KEY-RECONCILIATION", "POTENTIALLY-COVERED-SALES",
    "ROUTE-SPECIFIC-ECONOMIC-BENEFIT", "PROBABILITY-WEIGHTED-DATED-CASH-FLOWS",
    "PRESENT-VALUE-AND-NON-OVERLAPPING-ADJUSTMENTS", "SEPARATE-NON-ADDITIVE-OUTPUTS",
]
EXPECTED_ROUTE_IDS = [
    "PROSPECTIVE-RFR-DIRECT-USE", "THIRD-PARTY-LICENSING",
    "PAST-ENFORCEMENT-DAMAGES", "STRATEGIC-OPTION-BARRIER",
]
EXPECTED_COMPONENT_IDS = [
    "RIGHTS-PERIMETER", "PRODUCT-SALES-ATTRIBUTION", "ECONOMIC-CASH-FLOW",
    "RISK-AND-DISCOUNT", "PREMISE-SPECIFIC-OUTPUT-RANGES",
]
EXPECTED_GATE_IDS = [
    "BASIS-AND-SUBJECT", "RIGHTS-TITLE-TERM", "PRODUCT-CLAIM-MAPPING",
    "ATTRIBUTABLE-SALES", "ROYALTY-DAMAGES-LICENSING-BASIS",
    "CASH-FLOW-TIMING", "RISK-COST-TAX-COLLECTABILITY",
]
FORMULA_EN = (
    "market evidence -> scope-key reconciliation -> potentially covered sales -> "
    "route-specific economic benefit -> probability-weighted dated cash flows -> "
    "non-overlapping risk/cost/tax and present value -> separate non-additive output"
)


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def null_range(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"low", "central", "high"}
        and all(value.get(key) is None for key in ("low", "central", "high"))
    )


def bilingual(item: Any, bases: tuple[str, ...], context: str, errors: list[str]) -> None:
    if not isinstance(item, dict):
        errors.append(f"{context} must be an object")
        return
    for base in bases:
        for suffix in ("En", "Fi"):
            require(
                isinstance(item.get(f"{base}{suffix}"), str) and bool(item[f"{base}{suffix}"].strip()),
                f"{context}.{base}{suffix} must be a non-empty string",
                errors,
            )


def validate_source_ids(items: list[Any], context: str, known: set[str] | None, errors: list[str]) -> None:
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{context}[{index}] must be an object")
            continue
        source_ids = item.get("sourceIds")
        require(
            isinstance(source_ids, list) and bool(source_ids)
            and len(source_ids) == len(set(source_ids))
            and all(isinstance(source_id, str) and source_id for source_id in source_ids),
            f"{context}[{index}].sourceIds must be unique non-empty strings",
            errors,
        )
        if isinstance(source_ids, list) and known is not None:
            require(not (set(source_ids) - known), f"{context}[{index}] references unknown sources", errors)


def validate_control(control: Any, errors: list[str], *, known_source_ids: set[str] | None = None) -> None:
    if not isinstance(control, dict):
        errors.append("patent valuation control must be an object")
        return
    require(set(control) == EXPECTED_TOP_LEVEL_KEYS, "patent valuation control top-level keys mismatch", errors)
    require(control.get("controlId") == "PIXAN-PATENT-VALUATION-CONTROL-2026-08-03", "valuation controlId mismatch", errors)
    require(control.get("controlVersion") == "2.0", "valuation controlVersion must be 2.0", errors)
    require(control.get("valuationDate") == "2026-08-03", "valuationDate must be 2026-08-03", errors)
    require(control.get("purposeEn") == "Estimate defensible patent value range", "English valuation purpose mismatch", errors)
    require(control.get("purposeFi") == "Arvioida puolustettavissa oleva patentin arvon vaihteluväli", "Finnish valuation purpose mismatch", errors)
    require(control.get("status") == "NOT_COMPUTED", "patent value status must be NOT_COMPUTED", errors)
    require(control.get("ultimatePatentValueEUR") is None, "ultimatePatentValueEUR must remain a null-only legacy sentinel", errors)
    require(null_range(control.get("valueRangeEUR")), "legacy valueRangeEUR must remain null-only", errors)
    require(control.get("ultimateScalarPermitted") is False, "ultimate scalar patent value must not be permitted", errors)
    require("legacy null sentinel" in str(control.get("ultimateScalarRoleEn", "")).casefold(), "ultimate scalar role must state legacy null sentinel", errors)
    require(control.get("decision") == "HOLD", "patent valuation decision must remain HOLD", errors)
    require(control.get("gateLogic") == "OUTPUT_SPECIFIC_DEPENDENCIES_MUST_PASS", "gate logic must be output-specific", errors)

    basis = control.get("valuationBasis", {})
    require(basis.get("status") == "NOT_DEFINED", "valuation basis must remain NOT_DEFINED", errors)
    require(basis.get("otherPremisesAreIfrsFairValue") is False, "non-market-participant outputs must not be labelled IFRS fair value", errors)
    require(basis.get("grossNetTaxBasis") == "NOT_DEFINED", "gross/net/tax basis must remain NOT_DEFINED", errors)
    bilingual(basis, ("subjectMatter", "premiseAndUse", "marketParticipantBasis"), "valuationBasis", errors)
    validate_source_ids([basis], "valuationBasis", known_source_ids, errors)

    scope = control.get("scopeKeyControl", {})
    require(scope.get("requiredKeys") == ["product", "country", "counterparty", "period", "economicBenefit"], "scope-key list mismatch", errors)
    require(scope.get("allKeysMustReconcileBeforeUse") is True, "scope keys must reconcile", errors)
    require(scope.get("missingKeyIsZero") is False, "missing scope key must not become zero", errors)

    outputs = control.get("outputCases") if isinstance(control.get("outputCases"), list) else []
    require([item.get("outputId") for item in outputs if isinstance(item, dict)] == EXPECTED_OUTPUT_IDS, "output-case IDs/order mismatch", errors)
    for index, output in enumerate(outputs):
        if not isinstance(output, dict):
            continue
        require(output.get("valueEUR") is None, f"outputCases[{index}].valueEUR must remain null", errors)
        require(null_range(output.get("valueRangeEUR")), f"outputCases[{index}] range must remain null", errors)
        require(output.get("probabilityWeightedValueEUR") is None, f"outputCases[{index}].probabilityWeightedValueEUR must remain null", errors)
        require(output.get("status") == "NOT_COMPUTED", f"outputCases[{index}] must remain NOT_COMPUTED", errors)
        require(output.get("nonAdditive") is True, f"outputCases[{index}] must be non-additive", errors)
        bilingual(output, ("title",), f"outputCases[{index}]", errors)
    validate_source_ids(outputs, "outputCases", known_source_ids, errors)

    market = control.get("marketEvidenceRole", {})
    require(market.get("role") == "INPUT_ONLY", "market evidence must remain INPUT_ONLY", errors)
    for key, value in market.items():
        if key.startswith("maySet"):
            require(value is False, f"marketEvidenceRole.{key} must be false", errors)
    donor = control.get("donorGateSnapshot", {})
    require(donor.get("accepted") == 0 and donor.get("required") == 3 and donor.get("status") == "OPEN", "donor gate snapshot must remain 0/3 OPEN", errors)
    require("not the final valuation objective" in str(donor.get("roleEn", "")).casefold(), "donor gate must not be the final valuation objective", errors)

    bridge = control.get("formulaBridge", {})
    require(bridge.get("expressionEn") == FORMULA_EN, "English branch-safe formula mismatch", errors)
    steps = bridge.get("steps") if isinstance(bridge.get("steps"), list) else []
    require([item.get("stepId") for item in steps if isinstance(item, dict)] == EXPECTED_STEP_IDS, "formula bridge step IDs/order mismatch", errors)
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            continue
        require(step.get("sequence") == index, f"formula step {index} sequence mismatch", errors)
        require(step.get("valueEUR") is None, f"formula step {index} valueEUR must remain null", errors)
        require(step.get("status") == "NOT_COMPUTED", f"formula step {index} must remain NOT_COMPUTED", errors)
        bilingual(step, ("title", "requirement"), f"formula step {index}", errors)
    validate_source_ids(steps, "formulaBridge.steps", known_source_ids, errors)

    routes = control.get("routeBranches") if isinstance(control.get("routeBranches"), list) else []
    require([item.get("routeId") for item in routes if isinstance(item, dict)] == EXPECTED_ROUTE_IDS, "route branch IDs/order mismatch", errors)
    for route in routes:
        if not isinstance(route, dict):
            continue
        requires_infringement = route.get("routeId") == "PAST-ENFORCEMENT-DAMAGES"
        require(route.get("requiresPotentiallyInfringingSales") is requires_infringement, f"{route.get('routeId')} infringement dependency mismatch", errors)
        require(route.get("valueEUR") is None and route.get("status") == "NOT_COMPUTED", f"{route.get('routeId')} must remain null/NOT_COMPUTED", errors)

    components = control.get("components") if isinstance(control.get("components"), list) else []
    require([item.get("componentId") for item in components if isinstance(item, dict)] == EXPECTED_COMPONENT_IDS, "valuation component IDs/order mismatch", errors)
    for component in components:
        if isinstance(component, dict):
            require(component.get("status") == "OPEN" and component.get("valueEUR") is None, f"component {component.get('componentId')} must remain OPEN/null", errors)
    validate_source_ids(components, "components", known_source_ids, errors)

    allocation = control.get("allocationControls", {})
    require(allocation.get("overlappingHaircutsPermitted") is False, "overlapping territory/claim/infringement haircuts must be prohibited", errors)
    require(allocation.get("rightsAndTerm") == "BOOLEAN_COUNTRY_RIGHT_AND_TIME_MASKS", "rights/term mask control mismatch", errors)
    require(allocation.get("productSales") == "MEASURED_SKU_SALES_ALLOCATION", "SKU allocation control mismatch", errors)
    require(allocation.get("claimState") == "COUNSEL_REVIEWED_CLAIM_STATE", "claim-state control mismatch", errors)

    pv = control.get("presentValueConvention", {})
    require(pv.get("cashFlowBasis") == "PROBABILITY_WEIGHTED_DATED_CASH_FLOWS", "PV must use probability-weighted dated cash flows", errors)
    require(pv.get("discountRateExcludesSeparatelyModelledRisks") is True, "discount rate must exclude separately modelled risks", errors)
    require(pv.get("eachRiskMappedExactlyOnce") is True, "every risk must map exactly once", errors)
    require(pv.get("separateTimeDiscountFactorPermitted") is False, "separate time discount factor must be prohibited", errors)
    require(pv.get("probabilityWeightedValueEUR") is None, "PV probabilityWeightedValueEUR must remain null", errors)
    validate_source_ids([pv], "presentValueConvention", known_source_ids, errors)

    scenarios = control.get("scenarioControl", {})
    require(scenarios.get("scenarioProbabilities") == [], "scenario probabilities must remain empty until defined", errors)
    require(scenarios.get("probabilitiesMustSumToOne") is True, "scenario probabilities must sum to one", errors)
    require(scenarios.get("probabilitySum") is None, "scenario probability sum must remain null", errors)
    require(scenarios.get("probabilityWeightedValueEUR") is None, "scenario probabilityWeightedValueEUR must remain null", errors)
    require(scenarios.get("sumToOneQaStatus") == "NOT_COMPUTED", "scenario sum-to-one QA must remain NOT_COMPUTED", errors)

    review = control.get("independentReview", {})
    require(review.get("role") == "POST_COMPUTATION_RELEASE_AND_ASSURANCE_GATE", "independent review role mismatch", errors)
    require(review.get("usedAsComputationInput") is False, "independent review must not be a computation input", errors)
    collateral = control.get("collateralRecoveryCase", {})
    require(collateral.get("valueEUR") is None and collateral.get("probabilityWeightedValueEUR") is None, "collateral values must remain null", errors)
    require(collateral.get("simpleValueTimesHaircutPermitted") is False, "value times generic haircut must be prohibited", errors)
    require(collateral.get("lenderHaircutsApplyOnlyHere") is True, "lender haircuts must apply only to collateral case", errors)
    required_recovery = {"recoveryPremise", "perfection", "priority", "transferability", "foreclosureMarketability", "saleTime", "saleCosts"}
    recovery = collateral.get("requiredInputs")
    require(isinstance(recovery, dict) and set(recovery) == required_recovery and all(value is None for value in recovery.values()), "collateral recovery inputs must be exact null fields", errors)
    validate_source_ids([collateral], "collateralRecoveryCase", known_source_ids, errors)

    gates = control.get("hardGates") if isinstance(control.get("hardGates"), list) else []
    require([item.get("gateId") for item in gates if isinstance(item, dict)] == EXPECTED_GATE_IDS, "patent-value hard-gate IDs/order mismatch", errors)
    for gate in gates:
        if not isinstance(gate, dict):
            continue
        gate_id = gate.get("gateId")
        require(gate.get("status") == "OPEN" and gate.get("blocksComputation") is True, f"{gate_id} must remain OPEN and blocking", errors)
        require(gate.get("usedInModel") is True, f"{gate_id}.usedInModel must be true", errors)
        applies = gate.get("appliesToOutputIds")
        require(isinstance(applies, list) and bool(applies) and not (set(applies) - set(EXPECTED_OUTPUT_IDS)), f"{gate_id} appliesToOutputIds mismatch", errors)
        dependencies = gate.get("dependencies", {})
        require(dependencies.get("mode") == "OUTPUT_SPECIFIC", f"{gate_id} dependencies must be output-specific", errors)
        bilingual(gate, ("title", "requirement", "evidenceNeeded"), f"hardGate.{gate_id}", errors)
    validate_source_ids(gates, "hardGates", known_source_ids, errors)
    by_gate = {gate.get("gateId"): gate for gate in gates if isinstance(gate, dict)}
    attributable = by_gate.get("ATTRIBUTABLE-SALES", {})
    require(attributable.get("infringementRequiredOnlyForOutputIds") == ["PAST-ENFORCEMENT-CLAIM-NPV"], "infringement sales must be enforcement-only", errors)
    risk_gate = by_gate.get("RISK-COST-TAX-COLLECTABILITY", {})
    require(risk_gate.get("infringementRiskAppliesOnlyToOutputIds") == ["PAST-ENFORCEMENT-CLAIM-NPV"], "infringement risk must be enforcement-only", errors)
    require(risk_gate.get("lenderRecoveryAssumptionsApplyOnlyToOutputIds") == ["COLLATERAL-RECOVERY-VALUE"], "lender recovery assumptions must be collateral-only", errors)

    dependency = control.get("dependencyControl", {})
    require(dependency.get("globalCircularBlock") is False, "global circular block must be false", errors)
    require(dependency.get("gateDependenciesAreOutputSpecific") is True and dependency.get("sourceDependenciesAreOutputSpecific") is True, "gate/source dependencies must be output-specific", errors)
    dependency_outputs = dependency.get("outputs") if isinstance(dependency.get("outputs"), list) else []
    require([item.get("outputId") for item in dependency_outputs if isinstance(item, dict)] == EXPECTED_OUTPUT_IDS, "dependency output IDs/order mismatch", errors)

    germany = control.get("germanyRole", {})
    require(germany.get("role") == "CALIBRATION_AND_TECHNICAL_LEVERAGE_ONLY", "Germany role mismatch", errors)
    germany_text = str(germany.get("statementEn", "")).casefold()
    require("case-specific evidence" in germany_text and "adjudicated product and claim" in germany_text, "Germany must remain adjudicated-case evidence only", errors)
    require("current counsel-reviewed claim mapping" in germany_text and "procedural-status" in germany_text, "Germany transfer requires current counsel mapping and procedural status", errors)
    require("materially comparable" not in germany_text, "Germany wording must not assert material comparability", errors)
    for key in ("mayEstablishGlobalCoverage", "mayEstablishGlobalInfringement", "mayEstablishGlobalDamages", "maySetPatentValue"):
        require(germany.get(key) is False, f"germanyRole.{key} must be false", errors)
    validate_source_ids([germany], "germanyRole", known_source_ids, errors)

    guardrails = control.get("guardrails", {})
    true_keys = ("noDoubleCounting", "outputsAreNonAdditive", "scopeKeysMustReconcile", "independentResearchNotPixanPosition")
    false_keys = ("overlappingHaircutsPermitted", "missingIsZero", "marketEqualsPatentValue", "ultimateScalarPermitted", "independentReviewIsComputationInput", "lenderHaircutsOutsideCollateralCasePermitted", "licensedVendorValuesIncluded")
    for key in true_keys:
        require(guardrails.get(key) is True, f"guardrails.{key} must be true", errors)
    for key in false_keys:
        require(guardrails.get(key) is False, f"guardrails.{key} must be false", errors)


def validate_files(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    source_path = root / "source" / "patent-history.json"
    public_path = root / "site" / "data" / "patent-history.json"
    source_schema_path = root / "source" / "schemas" / "patent-valuation-control.schema.json"
    public_schema_path = root / "site" / "schemas" / "patent-valuation-control.schema.json"
    for path in (source_path, public_path, source_schema_path, public_schema_path):
        require(path.is_file(), f"missing patent-valuation file {path.relative_to(root)}", errors)
    if errors:
        return errors
    source = json.loads(source_path.read_text(encoding="utf-8"))
    public = json.loads(public_path.read_text(encoding="utf-8"))
    source_control = source.get("monetisation", {}).get("valuationControl")
    public_control = public.get("monetisation", {}).get("valuationControl")
    require(source_control == public_control, "source/public patent valuation controls must match", errors)
    require(source_schema_path.read_bytes() == public_schema_path.read_bytes(), "source/public patent valuation schemas must match", errors)
    schema = json.loads(source_schema_path.read_text(encoding="utf-8"))
    require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "valuation schema draft mismatch", errors)
    require(schema.get("additionalProperties") is False, "valuation schema must reject additional root properties", errors)
    require(set(schema.get("required", [])) == EXPECTED_TOP_LEVEL_KEYS, "valuation schema required fields mismatch", errors)
    try:
        from jsonschema import Draft202012Validator
        for error in Draft202012Validator(schema).iter_errors(source_control):
            errors.append(f"valuation schema: {'/'.join(str(part) for part in error.path)}: {error.message}")
    except ModuleNotFoundError:
        pass
    known_source_ids = {
        item.get("sourceId") for item in source.get("sources", [])
        if isinstance(item, dict) and isinstance(item.get("sourceId"), str)
    }
    validate_control(source_control, errors, known_source_ids=known_source_ids)
    return errors


def main() -> int:
    errors = validate_files()
    if errors:
        print(f"FAIL: {len(errors)} patent-valuation control error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("OK: seven non-additive outputs remain null/NOT_COMPUTED behind seven output-specific gates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
