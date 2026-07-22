#!/usr/bin/env python3
"""Mutation tests for JavaScript public-content privacy scanning."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from validate_public import private_identifier_fingerprint, scan_javascript_text


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


if __name__ == "__main__":
    unittest.main()
