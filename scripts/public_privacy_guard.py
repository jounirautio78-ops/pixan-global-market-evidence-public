#!/usr/bin/env python3
"""Shared privacy fingerprints for public-repository validation.

The values are one-way fingerprints of private identifiers reviewed outside
this repository. Keeping only length and SHA-256 prevents the validator itself
from publishing the identifiers it is designed to reject.
"""

from __future__ import annotations

import hashlib
import re


PRIVATE_IDENTIFIER_FINGERPRINTS = frozenset(
    {
        (7, "46d7415f6182ece9e933e8e9f780957e449361e0dbe10e34f46c186cad3382a1"),
        (7, "f910f0bbe95037851d18ca33b91ee7fc9f334c6cfcd02deaf66af4501c8a884c"),
        (9, "7e6578c2e34b53136741c6efe7799a2dce739651c22404a7894b48d42aa88b41"),
        (13, "933536a17b00f1b39ba9d3585427bd7232d44960ab35754318c1da8e4cf6c5be"),
        (15, "34ffed4db76374ed904b437c1e19187c3b469558946f22b88f38317322a4e75e"),
        (17, "d91ca0a7fbdfbd585109c3d3bab1233a92a1179e10e635f5bf1341efe10876b8"),
        (22, "9a4f0d4a8cf1a57c06c6aea58dc7494eabd55985b6de748525cae5292004ba25"),
        (25, "40f45830e7e3e21d88245728fe87f76b2e8919543a502aad248a465487cacee3"),
        (32, "eba767052e777d1e6ad413884309be77b9016a7ca61f9b83adf9f46c42d0bde9"),
    }
)


def private_identifier_fingerprint(value: str) -> tuple[int, str]:
    normalised = re.sub(r"[^a-z0-9]+", "", value.casefold())
    return len(normalised), hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def contains_private_identifier(
    value: str,
    fingerprints: frozenset[tuple[int, str]] | None = None,
) -> bool:
    if fingerprints is None:
        fingerprints = PRIVATE_IDENTIFIER_FINGERPRINTS
    normalised = re.sub(r"[^a-z0-9]+", "", value.casefold())
    for length, expected in fingerprints:
        if any(
            hashlib.sha256(normalised[index:index + length].encode("utf-8")).hexdigest() == expected
            for index in range(max(0, len(normalised) - length + 1))
        ):
            return True
    return False
