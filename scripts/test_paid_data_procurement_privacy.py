#!/usr/bin/env python3
"""Mutation tests for the published procurement workbook boundary."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from openpyxl import load_workbook

from public_privacy_guard import private_identifier_fingerprint
from validate_paid_data_procurement import (
    OUTPUT_XLSX,
    read_json,
    scan_public_workbook_text,
    SOURCE_PATH,
    validate_workbook,
)


class PaidDataWorkbookPrivacyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = read_json(SOURCE_PATH)

    def validate_mutation(
        self,
        coordinate: str,
        value: str,
        fingerprints: frozenset[tuple[int, str]] | None = None,
    ) -> list[str]:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "mutated.xlsx"
            shutil.copyfile(OUTPUT_XLSX, path)
            workbook = load_workbook(path, read_only=False, data_only=False)
            workbook["Response Scorecard"][coordinate] = value
            workbook.save(path)
            workbook.close()
            reviewed_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            errors: list[str] = []
            contexts = [
                patch("validate_paid_data_procurement.OUTPUT_XLSX", path),
                patch(
                    "validate_paid_data_procurement.EXPECTED_XLSX_SHA256",
                    reviewed_hash,
                ),
            ]
            if fingerprints is not None:
                contexts.append(
                    patch(
                        "public_privacy_guard.PRIVATE_IDENTIFIER_FINGERPRINTS",
                        fingerprints,
                    )
                )
            with contexts[0], contexts[1]:
                if len(contexts) == 3:
                    with contexts[2]:
                        validate_workbook(copy.deepcopy(self.source), errors)
                else:
                    validate_workbook(copy.deepcopy(self.source), errors)
            return errors

    def test_rejects_email_in_reviewer_note(self) -> None:
        errors = self.validate_mutation("V14", "analyst@example.test")
        self.assertTrue(any("email address" in error for error in errors), errors)

    def test_rejects_private_path_in_reviewer_note(self) -> None:
        errors = self.validate_mutation("V14", "/Users/example/private/reply.eml")
        self.assertTrue(any("local or private path" in error for error in errors), errors)

    def test_rejects_uuid_and_message_metadata(self) -> None:
        value = "Message-ID: 123e4567-e89b-42d3-a456-426614174000"
        errors = self.validate_mutation("V14", value)
        self.assertTrue(any("UUID-like" in error for error in errors), errors)
        self.assertTrue(
            any("message, form or thread metadata" in error for error in errors),
            errors,
        )
        self.assertTrue(any("correspondence header" in error for error in errors), errors)

    def test_rejects_fingerprinted_private_counterparty(self) -> None:
        marker = "Example Confidential Workbook Counterparty"
        fingerprints = frozenset({private_identifier_fingerprint(marker)})
        errors = self.validate_mutation("V14", marker, fingerprints)
        self.assertTrue(
            any("private identifier fingerprint" in error for error in errors),
            errors,
        )

    def test_rejects_false_public_outreach_state(self) -> None:
        errors = self.validate_mutation("D14", "RESPONSE RECEIVED · READY FOR PURCHASE")
        self.assertTrue(any("public state" in error for error in errors), errors)

    def test_rejects_unsupported_public_boundary_note(self) -> None:
        errors = self.validate_mutation("X14", "Unsupported commercial claim")
        self.assertTrue(any("boundary differs" in error for error in errors), errors)

    def test_relationship_text_uses_same_privacy_guard(self) -> None:
        errors: list[str] = []
        scan_public_workbook_text(
            "OOXML relationship fixture",
            "file:///Users/example/private/reply.eml",
            errors,
        )
        self.assertTrue(any("local or private path" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
