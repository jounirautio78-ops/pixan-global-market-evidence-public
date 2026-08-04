#!/usr/bin/env python3
"""Mutation tests for the once-daily bank-package snapshot rule."""

from __future__ import annotations

import copy
import json
import unittest
from unittest.mock import patch

from openpyxl import Workbook

try:
    from validate_bank_package import (
        EUR_EQUIVALENT_HEADERS,
        EXPECTED_LOCKED_EUR_EQUIVALENT_ROWS,
        EXPECTED_LOCKED_EUR_STATUS_COUNTS,
        EXPECTED_PACKAGE_CADENCE,
        LOCK_PATH,
        MANIFEST_PATH,
        validate_daily_package_snapshot,
        validate_eur_equivalent_sheet,
        validate_release_lock,
    )
except ModuleNotFoundError:
    from scripts.validate_bank_package import (
        EUR_EQUIVALENT_HEADERS,
        EXPECTED_LOCKED_EUR_EQUIVALENT_ROWS,
        EXPECTED_LOCKED_EUR_STATUS_COUNTS,
        EXPECTED_PACKAGE_CADENCE,
        LOCK_PATH,
        MANIFEST_PATH,
        validate_daily_package_snapshot,
        validate_eur_equivalent_sheet,
        validate_release_lock,
    )

try:
    from build_bank_package import (
        GERMANY_VENDOR_AUDIT_BOUNDARY_SOURCE,
        validate_v43_vendor_boundary,
    )
except ModuleNotFoundError:
    from scripts.build_bank_package import (
        GERMANY_VENDOR_AUDIT_BOUNDARY_SOURCE,
        validate_v43_vendor_boundary,
    )


PACKAGE_RELEASE = {
    "id": "2026-08-03-patent-valuation-pivot-v44",
    "version": "2026.08.03-44",
    "publishedAt": "2026-08-03T23:35:00+03:00",
}
INTERMEDIATE_SAME_DAY_RELEASE = {
    "id": "test-only-2026-08-03-intermediate-dashboard-release",
    "version": "test-only-intermediate",
    "publishedAt": "2026-08-03T23:40:00+03:00",
}
LATER_SAME_DAY_RELEASE = {
    "id": "test-only-2026-08-03-later-dashboard-release",
    "version": "test-only-later",
    "publishedAt": "2026-08-03T23:45:00+03:00",
}


def manifest(release: dict[str, str] | None = None) -> dict:
    return {
        "release": copy.deepcopy(release or PACKAGE_RELEASE),
        "asOf": "2026-08-03",
        "cadence": copy.deepcopy(EXPECTED_PACKAGE_CADENCE),
    }


def changelog(releases: list[dict[str, str]] | None = None) -> dict:
    return {
        "asOf": "2026-08-03",
        "releases": copy.deepcopy(releases or [PACKAGE_RELEASE]),
    }


class DailyPackageSnapshotTests(unittest.TestCase):
    @staticmethod
    def reviewed_manifest_and_lock() -> tuple[dict, dict]:
        return (
            json.loads(MANIFEST_PATH.read_text(encoding="utf-8")),
            json.loads(LOCK_PATH.read_text(encoding="utf-8")),
        )

    @staticmethod
    def locked_snapshot_workbook() -> Workbook:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "EUR equivalents"
        sheet.append(EUR_EQUIVALENT_HEADERS["en"])
        row = 2
        for sequence in range(EXPECTED_LOCKED_EUR_STATUS_COUNTS["computed"]):
            sheet.append([
                "market_observation",
                f"CAD-{sequence}",
                "metric",
                "Canada",
                2024,
                "calendar_year",
                100,
                "CAD",
                1.5,
                f"=G{row}/I{row}",
                "ECB-EXR-A-CAD-EUR-SP00-A-2024",
                "https://data-api.ecb.europa.eu/service/data/EXR/A.CAD.EUR.SP00.A?startPeriod=2024&endPeriod=2024&format=csvdata",
                "computed",
                "original_amount_divided_by_ecb_annual_average",
            ])
            row += 1
        for sequence in range(EXPECTED_LOCKED_EUR_STATUS_COUNTS["already_eur"]):
            sheet.append([
                "market_observation",
                f"EUR-{sequence}",
                "metric",
                "Germany",
                2024,
                "calendar_year",
                100,
                "EUR",
                1,
                f"=G{row}",
                "EUR-IDENTITY",
                "https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html",
                "already_eur",
                "original_currency_already_eur",
            ])
            row += 1
        for sequence in range(EXPECTED_LOCKED_EUR_STATUS_COUNTS["not_computed"]):
            sheet.append([
                "market_observation",
                f"NZD-NOT-COMPUTED-{sequence}",
                "metric",
                "New Zealand",
                2023,
                "year_ended_june",
                100,
                "NZD",
                None,
                None,
                None,
                "https://data-api.ecb.europa.eu/service/data/EXR",
                "not_computed",
                "period_not_compatible_with_annual_average",
            ])
            row += 1
        if row - 2 != EXPECTED_LOCKED_EUR_EQUIVALENT_ROWS:
            raise AssertionError("locked EUR fixture does not match the v44 release counts")
        return workbook

    def test_accepts_current_combined_release_and_requires_input_hashes(self) -> None:
        errors: list[str] = []
        self.assertFalse(validate_daily_package_snapshot(manifest(), changelog(), errors))
        self.assertEqual(errors, [])

    def test_accepts_earlier_same_day_snapshot_and_allows_input_drift(self) -> None:
        errors: list[str] = []
        self.assertTrue(
            validate_daily_package_snapshot(
                manifest(),
                changelog([
                    LATER_SAME_DAY_RELEASE,
                    INTERMEDIATE_SAME_DAY_RELEASE,
                    PACKAGE_RELEASE,
                ]),
                errors,
            )
        )
        self.assertEqual(errors, [])

    def test_rejects_previous_calendar_day_in_asia_nicosia(self) -> None:
        errors: list[str] = []
        stale_release = {
            **PACKAGE_RELEASE,
            "publishedAt": "2026-08-02T23:59:00+03:00",
        }
        stale = manifest(stale_release)
        stale["asOf"] = "2026-08-02"
        history = changelog([PACKAGE_RELEASE, stale_release])
        self.assertFalse(validate_daily_package_snapshot(stale, history, errors))
        self.assertTrue(any("older than" in error for error in errors), errors)

    def test_rejects_missing_explicit_once_daily_cadence(self) -> None:
        errors: list[str] = []
        candidate = manifest()
        candidate["cadence"]["frequency"] = "continuous"
        self.assertFalse(validate_daily_package_snapshot(candidate, changelog(), errors))
        self.assertTrue(any("once_daily" in error for error in errors), errors)

    def test_uses_asia_nicosia_date_not_source_offset_date(self) -> None:
        errors: list[str] = []
        latest = {
            **LATER_SAME_DAY_RELEASE,
            "publishedAt": "2026-08-03T21:15:00Z",
        }
        package = {
            **PACKAGE_RELEASE,
            "publishedAt": "2026-08-03T21:05:00Z",
        }
        next_day_manifest = manifest(package)
        next_day_manifest["asOf"] = "2026-08-04"
        next_day_changelog = changelog([latest, package])
        next_day_changelog["asOf"] = "2026-08-04"
        self.assertTrue(
            validate_daily_package_snapshot(
                next_day_manifest,
                next_day_changelog,
                errors,
            )
        )
        self.assertEqual(errors, [])

    def test_locked_eur_sheet_is_validated_as_its_own_snapshot(self) -> None:
        workbook = self.locked_snapshot_workbook()
        errors: list[str] = []
        validate_eur_equivalent_sheet(
            workbook,
            "en",
            [{"not": "the locked snapshot"}] * 55,
            False,
            "locked.xlsx",
            errors,
        )
        self.assertEqual(errors, [])

    def test_locked_eur_sheet_still_fails_closed_on_formula_drift(self) -> None:
        workbook = self.locked_snapshot_workbook()
        workbook["EUR equivalents"]["J2"] = "=G2"
        errors: list[str] = []
        validate_eur_equivalent_sheet(
            workbook,
            "en",
            [],
            False,
            "locked.xlsx",
            errors,
        )
        self.assertTrue(any("full-precision formula" in error for error in errors), errors)

    def test_release_lock_accepts_the_reviewed_snapshot(self) -> None:
        manifest_snapshot, release_lock = self.reviewed_manifest_and_lock()
        errors: list[str] = []
        self.assertTrue(validate_release_lock(manifest_snapshot, release_lock, errors))
        self.assertEqual(errors, [])

    def test_release_lock_rejects_a_wrong_reviewed_hash(self) -> None:
        manifest_snapshot, release_lock = self.reviewed_manifest_and_lock()
        errors: list[str] = []
        module_name = validate_release_lock.__module__
        with patch(f"{module_name}.EXPECTED_LOCK_SHA256", "0" * 64):
            self.assertFalse(validate_release_lock(manifest_snapshot, release_lock, errors))
        self.assertTrue(any("lock SHA-256" in error for error in errors), errors)

    def test_release_lock_rejects_input_and_artifact_drift(self) -> None:
        manifest_snapshot, release_lock = self.reviewed_manifest_and_lock()
        release_lock["reviewedInputs"][0]["sha256"] = "0" * 64
        release_lock["artifacts"][0]["bytes"] += 1
        errors: list[str] = []
        self.assertFalse(validate_release_lock(manifest_snapshot, release_lock, errors))
        self.assertTrue(any("reviewedInputs" in error for error in errors), errors)
        self.assertTrue(any("artifacts differ" in error for error in errors), errors)

    def test_accepts_v43_privacy_safe_germany_vendor_boundary(self) -> None:
        control_path = GERMANY_VENDOR_AUDIT_BOUNDARY_SOURCE.parent / "vendor-response-control.json"
        control = json.loads(control_path.read_text(encoding="utf-8"))
        vendor = validate_v43_vendor_boundary(control)
        statuses = {
            gate: result["status"] for gate, result in vendor["gateResults"].items()
        }
        self.assertEqual(sum(status == "pass" for status in statuses.values()), 1)
        self.assertEqual(sum(status != "missing" for status in statuses.values()), 6)
        self.assertEqual(vendor["scoringState"], "not_scored")
        self.assertFalse(vendor["widerPackagePurchaseAuthorised"])

    def test_rejects_vendor_gate_or_wider_purchase_drift(self) -> None:
        control_path = GERMANY_VENDOR_AUDIT_BOUNDARY_SOURCE.parent / "vendor-response-control.json"
        control = json.loads(control_path.read_text(encoding="utf-8"))
        vendor = next(
            item
            for item in control["vendors"]
            if item["vendorId"] == "euromonitor-passport-nicotine"
        )
        vendor["gateResults"]["G1"]["status"] = "fail"
        vendor["widerPackagePurchaseAuthorised"] = True
        with self.assertRaisesRegex(ValueError, "1/6 vendor-gate"):
            validate_v43_vendor_boundary(control)


if __name__ == "__main__":
    unittest.main()
