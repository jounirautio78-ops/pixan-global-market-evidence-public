#!/usr/bin/env python3
"""Fail-closed validation for the public investor-disclosure control."""

from __future__ import annotations

import json
from pathlib import Path
import re

from public_privacy_guard import contains_private_identifier


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "source" / "investor-disclosure-control.json"
PUBLIC_PATH = ROOT / "site" / "data" / "investor-disclosure-control.json"
SOURCE_SCHEMA_PATH = ROOT / "source" / "schemas" / "investor-disclosure-control.schema.json"
PUBLIC_SCHEMA_PATH = ROOT / "site" / "schemas" / "investor-disclosure-control.schema.json"
MEMO_PATH = ROOT / "source" / "INVESTOR_DISCLOSURE_CONTROL_2026-07-28.md"
DILIGENCE_HTML_PATH = ROOT / "site" / "diligence.html"
DILIGENCE_JS_PATH = ROOT / "site" / "assets" / "diligence.js"

EXPECTED_TOP_LEVEL_KEYS = {
    "$schema",
    "schemaVersion",
    "controlId",
    "asOf",
    "controlState",
    "languages",
    "publicBoundary",
    "audiences",
    "accessTiers",
    "materialFactsThatMustNotBeHidden",
    "prohibitedPublicItems",
    "safeguards",
    "publicAssetMapping",
    "hardGates",
    "decisionRule",
}
EXPECTED_TIERS = [
    "public",
    "nda",
    "restricted_clean_team_counsel",
    "board_counsel",
]
EXPECTED_AUDIENCES = {
    "lender",
    "strategic_buyer",
    "litigation_funder",
    "adviser",
}
REQUIRED_MATERIAL_FACTS = {
    "independent-not-official",
    "not-professional-opinion",
    "global-total-not-computed",
    "proxies-not-retail-sales",
    "missing-is-not-zero",
    "patent-status-is-territorial",
    "no-cross-border-litigation-extrapolation",
    "vendor-evidence-and-rights-open",
    "dashboard-package-version-separation",
    "adverse-and-corrective-evidence",
}
REQUIRED_PROHIBITED_ITEMS = {
    "named-potential-infringers",
    "legal-strategy",
    "negotiation-floors",
    "personal-data",
    "private-correspondence",
    "licensed-raw-data",
    "vendor-commercial-terms",
    "privileged-work-product",
    "private-corporate-records",
    "non-public-validation-records",
    "security-and-local-metadata",
    "unsupported-claims",
}
REQUIRED_SAFEGUARDS = {
    "vendor-licence",
    "privilege-and-work-product",
    "privacy-and-correspondence",
    "clean-team-and-competition",
    "evidence-integrity",
    "balanced-disclosure",
}
REQUIRED_GATES = {
    "counterparty-identity-authority",
    "lawful-purpose-and-scope",
    "executed-confidentiality",
    "balanced-material-disclosure",
    "provenance-quality-freshness",
    "vendor-rights",
    "privilege-work-product",
    "privacy-redaction",
    "competition-clean-team",
    "technical-access-controls",
    "release-authority",
    "release-log-expiry-destruction",
}
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SECRET_RE = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*[\"']?[^,\s\"']{8,}"
)


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def ids(items: list[dict], key: str) -> list[str]:
    return [str(item.get(key, "")) for item in items]


def require_bilingual(
    item: dict,
    bases: tuple[str, ...],
    context: str,
    errors: list[str],
) -> None:
    for base in bases:
        for suffix in ("En", "Fi"):
            value = item.get(f"{base}{suffix}")
            require(
                isinstance(value, str) and bool(value.strip()),
                f"{context}: missing {base}{suffix}",
                errors,
            )


def validate_public_path(path: object, context: str, errors: list[str]) -> None:
    require(isinstance(path, str), f"{context}: path must be a string", errors)
    if not isinstance(path, str):
        return
    require(path.startswith("site/"), f"{context}: path must remain under site/", errors)
    require(".." not in path and "\\" not in path, f"{context}: unsafe path", errors)
    target = ROOT / path
    require(target.is_file(), f"{context}: missing public asset {path}", errors)


def validate_files(errors: list[str]) -> dict:
    required_files = (
        SOURCE_PATH,
        PUBLIC_PATH,
        SOURCE_SCHEMA_PATH,
        PUBLIC_SCHEMA_PATH,
        MEMO_PATH,
        DILIGENCE_HTML_PATH,
        DILIGENCE_JS_PATH,
    )
    for path in required_files:
        require(path.is_file(), f"missing required file: {path.relative_to(ROOT)}", errors)
    if errors:
        return {}

    source_bytes = SOURCE_PATH.read_bytes()
    public_bytes = PUBLIC_PATH.read_bytes()
    source_schema_bytes = SOURCE_SCHEMA_PATH.read_bytes()
    public_schema_bytes = PUBLIC_SCHEMA_PATH.read_bytes()
    require(source_bytes == public_bytes, "source/public disclosure JSON must be byte-identical", errors)
    require(source_schema_bytes == public_schema_bytes, "source/public schema must be byte-identical", errors)
    require(not contains_private_identifier(source_bytes.decode("utf-8")), "private identifier detected in public control", errors)
    require(not SECRET_RE.search(source_bytes.decode("utf-8")), "secret-like assignment detected in public control", errors)

    schema = json.loads(source_schema_bytes)
    require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "schema draft mismatch", errors)
    require(schema.get("type") == "object", "schema root must be an object", errors)
    require(schema.get("additionalProperties") is False, "schema root must reject additional properties", errors)
    require(set(schema.get("required", [])) == EXPECTED_TOP_LEVEL_KEYS, "schema required keys mismatch", errors)
    require(set(schema.get("properties", {})) == EXPECTED_TOP_LEVEL_KEYS, "schema properties mismatch", errors)
    return json.loads(source_bytes)


def validate_control(control: dict, errors: list[str]) -> None:
    require(set(control) == EXPECTED_TOP_LEVEL_KEYS, "control top-level keys mismatch", errors)
    require(control.get("schemaVersion") == "1.0", "schemaVersion must be 1.0", errors)
    require(control.get("controlId") == "pixan-investor-disclosure-control-2026-07-28", "controlId mismatch", errors)
    require(control.get("asOf") == "2026-07-30", "control asOf mismatch", errors)
    require(bool(ISO_DATE_RE.fullmatch(str(control.get("asOf", "")))), "control asOf must be ISO date", errors)
    require(control.get("controlState") == "fail_closed", "control must fail closed", errors)
    require(control.get("languages") == ["en", "fi"], "language order must be en, fi", errors)

    boundary = control.get("publicBoundary", {})
    require_bilingual(boundary, ("statement", "failClosedRule"), "publicBoundary", errors)
    require(boundary.get("defaultTier") == "public", "public boundary default tier mismatch", errors)
    require(
        boundary.get("deeperAccessIsNotGrantedByThisControl") is True,
        "public control must not grant deeper access",
        errors,
    )

    tiers = control.get("accessTiers", [])
    require(ids(tiers, "tierId") == EXPECTED_TIERS, "access tiers/order mismatch", errors)
    require(len(ids(tiers, "tierId")) == len(set(ids(tiers, "tierId"))), "tier IDs must be unique", errors)
    for index, tier in enumerate(tiers, start=1):
        context = f"tier {tier.get('tierId')}"
        require(tier.get("order") == index, f"{context}: order mismatch", errors)
        require_bilingual(
            tier,
            ("title", "purpose", "permittedContent", "excludedContent", "releaseRule"),
            context,
            errors,
        )
        require(
            tier.get("sensitiveMaterialEmbeddedInThisControl") is False,
            f"{context}: public control must not embed sensitive material",
            errors,
        )

    audiences = control.get("audiences", [])
    audience_ids = ids(audiences, "audienceId")
    require(set(audience_ids) == EXPECTED_AUDIENCES, "audience set mismatch", errors)
    require(len(audience_ids) == len(set(audience_ids)), "audience IDs must be unique", errors)
    for audience in audiences:
        context = f"audience {audience.get('audienceId')}"
        require_bilingual(audience, ("title", "legitimateUse", "constraint"), context, errors)
        require(audience.get("defaultTier") == "public", f"{context}: default tier must be public", errors)
        deeper = audience.get("potentialDeeperTiers", [])
        require(isinstance(deeper, list) and "public" not in deeper, f"{context}: deeper tier list invalid", errors)
        require(set(deeper).issubset(set(EXPECTED_TIERS)), f"{context}: unknown tier", errors)

    facts = control.get("materialFactsThatMustNotBeHidden", [])
    fact_ids = ids(facts, "factId")
    require(set(fact_ids) == REQUIRED_MATERIAL_FACTS, "material-fact set mismatch", errors)
    require(len(fact_ids) == len(set(fact_ids)), "material-fact IDs must be unique", errors)
    for fact in facts:
        context = f"material fact {fact.get('factId')}"
        require_bilingual(fact, ("title", "statement"), context, errors)
        require(fact.get("mustNotBeOmitted") is True, f"{context}: mustNotBeOmitted must be true", errors)
        require(fact.get("minimumDisclosureTier") in EXPECTED_TIERS, f"{context}: invalid tier", errors)
        paths = fact.get("publicEvidencePaths", [])
        require(isinstance(paths, list) and bool(paths), f"{context}: evidence paths missing", errors)
        for path in paths:
            validate_public_path(path, context, errors)

    prohibited = control.get("prohibitedPublicItems", [])
    prohibited_ids = ids(prohibited, "itemId")
    require(set(prohibited_ids) == REQUIRED_PROHIBITED_ITEMS, "prohibited-public set mismatch", errors)
    require(len(prohibited_ids) == len(set(prohibited_ids)), "prohibited item IDs must be unique", errors)
    for item in prohibited:
        require_bilingual(item, ("title", "rule"), f"prohibited item {item.get('itemId')}", errors)

    safeguards = control.get("safeguards", [])
    safeguard_ids = ids(safeguards, "safeguardId")
    require(set(safeguard_ids) == REQUIRED_SAFEGUARDS, "safeguard set mismatch", errors)
    require(len(safeguard_ids) == len(set(safeguard_ids)), "safeguard IDs must be unique", errors)
    for item in safeguards:
        context = f"safeguard {item.get('safeguardId')}"
        require_bilingual(item, ("title",), context, errors)
        en = item.get("controlsEn", [])
        fi = item.get("controlsFi", [])
        require(isinstance(en, list) and bool(en), f"{context}: controlsEn missing", errors)
        require(isinstance(fi, list) and len(fi) == len(en), f"{context}: bilingual control count mismatch", errors)

    assets = control.get("publicAssetMapping", [])
    asset_ids = ids(assets, "assetGroupId")
    require(len(asset_ids) == len(set(asset_ids)), "public asset-group IDs must be unique", errors)
    for asset in assets:
        context = f"public asset {asset.get('assetGroupId')}"
        require_bilingual(asset, ("title", "publicUse", "limitations"), context, errors)
        require(asset.get("tierId") == "public", f"{context}: tier must be public", errors)
        require(bool(str(asset.get("versionOrAsOf", "")).strip()), f"{context}: version/as-of missing", errors)
        paths = asset.get("paths", [])
        require(isinstance(paths, list) and bool(paths), f"{context}: paths missing", errors)
        for path in paths:
            validate_public_path(path, context, errors)

    gates = control.get("hardGates", [])
    gate_ids = ids(gates, "gateId")
    require(set(gate_ids) == REQUIRED_GATES, "hard-gate set mismatch", errors)
    require(len(gate_ids) == len(set(gate_ids)), "hard-gate IDs must be unique", errors)
    for gate in gates:
        context = f"hard gate {gate.get('gateId')}"
        require_bilingual(
            gate,
            ("title", "requirement", "evidenceRequired", "failureAction"),
            context,
            errors,
        )
        required_for = gate.get("requiredForTiers", [])
        require(isinstance(required_for, list) and bool(required_for), f"{context}: tier scope missing", errors)
        require("public" not in required_for, f"{context}: public tier must not require a gate", errors)
        require(set(required_for).issubset(set(EXPECTED_TIERS)), f"{context}: unknown tier", errors)

    decision = control.get("decisionRule", {})
    require_bilingual(decision, ("decision",), "decisionRule", errors)
    require(decision.get("defaultTier") == "public", "decision default must be public", errors)
    require(decision.get("gateLogic") == "all_applicable_gates_must_pass", "gate logic mismatch", errors)
    for key in ("noAutomaticPromotion", "noPartialOverride"):
        require(decision.get(key) is True, f"decisionRule {key} must be true", errors)
    for key in ("controlGrantsAccess", "restrictedMaterialEmbeddedOrLinked"):
        require(decision.get(key) is False, f"decisionRule {key} must be false", errors)


def validate_experience(errors: list[str]) -> None:
    html = DILIGENCE_HTML_PATH.read_text(encoding="utf-8")
    script = DILIGENCE_JS_PATH.read_text(encoding="utf-8")
    required_html_hooks = (
        'lang="en"',
        'data-language="fi"',
        'data-language="en"',
        'id="diligence-tier-grid"',
        'id="diligence-audience-grid"',
        'id="diligence-reuse-grid"',
        'id="diligence-material-facts"',
        'id="diligence-hard-gates"',
        'id="diligence-load-error"',
        "GitHub Pages is not a secure data room.",
        "This public page does not grant confidential access",
        "Independent · not a Pixan Oy disclosure",
    )
    for hook in required_html_hooks:
        require(hook in html, f"diligence.html missing hook: {hook}", errors)
    required_script_hooks = (
        "EXPECTED_CONTROL_ID",
        "EXPECTED_TIERS",
        "validate(raw)",
        "failClosed()",
        'cache: "no-store"',
        "replaceChildren",
        "pixan:languagechange",
        "data/investor-disclosure-control.json",
        "requestLink.hidden = true",
    )
    for hook in required_script_hooks:
        require(hook in script, f"diligence.js missing fail-closed hook: {hook}", errors)
    require(".innerHTML" not in script, "diligence.js must not render JSON with innerHTML", errors)


def main() -> int:
    errors: list[str] = []
    control = validate_files(errors)
    if control:
        validate_control(control, errors)
    validate_experience(errors)
    if errors:
        print(f"FAIL: {len(errors)} investor-disclosure error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "OK: investor disclosure control is bilingual, public-safe, "
        "source/site-identical and fail-closed across four access tiers."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
