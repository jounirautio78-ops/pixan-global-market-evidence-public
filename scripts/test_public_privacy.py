#!/usr/bin/env python3
"""Mutation tests for public-content and repository privacy scanning."""

from __future__ import annotations

import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory

from validate_public import (
    private_identifier_fingerprint,
    scan_javascript_text,
    scan_repository_private_identifiers,
    validate_repository_binary_allowlist,
)


class JavaScriptPrivacyTests(unittest.TestCase):
    def scan(self, value: str) -> list[str]:
        errors: list[str] = []
        scan_javascript_text("fixture.js", value, errors)
        return errors

    def test_rejects_local_user_path(self) -> None:
        self.assertTrue(self.scan('const source = "/Users/example/private.txt";'))

    def test_rejects_secret_assignment(self) -> None:
        self.assertTrue(self.scan("const api_key = 'example-secret';"))

    def test_rejects_named_negotiation_party(self) -> None:
        marker = "Example Negotiation Counterparty"
        fingerprints = frozenset({private_identifier_fingerprint(marker)})
        with patch("validate_public.PRIVATE_IDENTIFIER_FINGERPRINTS", fingerprints):
            self.assertTrue(self.scan(f'const buyer = "{marker}";'))

    def test_allows_approved_public_contact(self) -> None:
        self.assertFalse(self.scan('const contact = "jouni.rautio78@gmail.com";'))

    def test_repository_scan_rejects_named_negotiation_party(self) -> None:
        marker = "Example Repository Counterparty"
        fingerprints = frozenset({private_identifier_fingerprint(marker)})
        with TemporaryDirectory() as directory:
            path = Path(directory) / "validator.py"
            path.write_text(f'BLOCKED = "{marker}"\n', encoding="utf-8")
            errors: list[str] = []
            with patch("validate_public.PRIVATE_IDENTIFIER_FINGERPRINTS", fingerprints):
                scan_repository_private_identifiers(errors, [Path(directory)])
        self.assertTrue(errors)

    def test_repository_binary_allowlist_rejects_unreviewed_attachment(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            attachment = root / "confidential-vendor-sample.xlsx"
            attachment.write_bytes(b"not a reviewed public artifact")
            errors: list[str] = []
            with (
                patch("validate_public.ROOT", root),
                patch("validate_public.ALLOWED_REPOSITORY_BINARY_ATTACHMENTS", frozenset()),
            ):
                validate_repository_binary_allowlist(errors)
        self.assertTrue(
            any("unexpected binary attachment" in error for error in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
