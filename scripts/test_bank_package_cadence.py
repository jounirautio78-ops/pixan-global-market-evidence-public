#!/usr/bin/env python3
"""Mutation tests for the once-daily bank-package snapshot rule."""

from __future__ import annotations

import copy
import unittest

try:
    from validate_bank_package import EXPECTED_PACKAGE_CADENCE, validate_daily_package_snapshot
except ModuleNotFoundError:
    from scripts.validate_bank_package import (
        EXPECTED_PACKAGE_CADENCE,
        validate_daily_package_snapshot,
    )


PACKAGE_RELEASE = {
    "id": "2026-07-30-canada-tax-basis-daily-package-v36",
    "version": "2026.07.30-36",
    "publishedAt": "2026-07-30T12:49:00+03:00",
}
LATER_SAME_DAY_RELEASE = {
    "id": "2026-07-30-dashboard-only-test-release",
    "version": "2026.07.30-37-test",
    "publishedAt": "2026-07-30T13:15:00+03:00",
}


def manifest(release: dict[str, str] | None = None) -> dict:
    return {
        "release": copy.deepcopy(release or PACKAGE_RELEASE),
        "asOf": "2026-07-30",
        "cadence": copy.deepcopy(EXPECTED_PACKAGE_CADENCE),
    }


def changelog(releases: list[dict[str, str]] | None = None) -> dict:
    return {
        "asOf": "2026-07-30",
        "releases": copy.deepcopy(releases or [PACKAGE_RELEASE]),
    }


class DailyPackageSnapshotTests(unittest.TestCase):
    def test_accepts_current_combined_release_and_requires_input_hashes(self) -> None:
        errors: list[str] = []
        self.assertFalse(validate_daily_package_snapshot(manifest(), changelog(), errors))
        self.assertEqual(errors, [])

    def test_accepts_earlier_same_day_snapshot_and_allows_input_drift(self) -> None:
        errors: list[str] = []
        self.assertTrue(
            validate_daily_package_snapshot(
                manifest(),
                changelog([LATER_SAME_DAY_RELEASE, PACKAGE_RELEASE]),
                errors,
            )
        )
        self.assertEqual(errors, [])

    def test_rejects_previous_calendar_day_in_asia_nicosia(self) -> None:
        errors: list[str] = []
        stale_release = {
            **PACKAGE_RELEASE,
            "publishedAt": "2026-07-29T23:59:00+03:00",
        }
        stale = manifest(stale_release)
        stale["asOf"] = "2026-07-29"
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
            "publishedAt": "2026-07-30T21:15:00Z",
        }
        package = {
            **PACKAGE_RELEASE,
            "publishedAt": "2026-07-30T21:05:00Z",
        }
        next_day_manifest = manifest(package)
        next_day_manifest["asOf"] = "2026-07-31"
        next_day_changelog = changelog([latest, package])
        next_day_changelog["asOf"] = "2026-07-31"
        self.assertTrue(
            validate_daily_package_snapshot(
                next_day_manifest,
                next_day_changelog,
                errors,
            )
        )
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
