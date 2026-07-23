#!/usr/bin/env python3
"""Language-neutral parity checks for the bilingual Evidence Register."""

from __future__ import annotations

import re
from collections import Counter
from decimal import Decimal, InvalidOperation
from typing import Sequence


CONFIDENCE_MAP = {
    "Vahvistettu": "Confirmed",
    "Tuettu": "Supported",
    "Oletus": "Assumption",
    "Puuttuu": "Missing",
}

URL_RE = re.compile(r"https?://[^\s<>\"']+")
LOCAL_SOURCE_RE = re.compile(r"\b(?:site|source)/[A-Za-z0-9_./-]+")
SOURCE_ID_RE = re.compile(r"(?:Lähdetunnus|Source ID)\s*:\s*([A-Z0-9][A-Z0-9._/-]*)", re.IGNORECASE)
SOURCE_SELECTOR_RE = re.compile(r"\(([A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z][A-Za-z0-9]*)*)\)")

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "tammikuu": 1,
    "helmikuu": 2,
    "maaliskuu": 3,
    "huhtikuu": 4,
    "toukokuu": 5,
    "kesäkuu": 6,
    "heinäkuu": 7,
    "elokuu": 8,
    "syyskuu": 9,
    "lokakuu": 10,
    "marraskuu": 11,
    "joulukuu": 12,
}
MONTH_PATTERN = "|".join(sorted(MONTHS, key=len, reverse=True))
EN_DATE_RE = re.compile(
    rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({MONTH_PATTERN})\s+(\d{{4}})\b",
    re.IGNORECASE,
)
EN_MONTH_YEAR_RE = re.compile(rf"\b({MONTH_PATTERN})\s+(\d{{4}})\b", re.IGNORECASE)
FI_MONTH_YEAR_RE = re.compile(
    rf"\b({MONTH_PATTERN})(?:ssa|ssä|sta|stä|hun|hyn|ta|tä|lla|llä|n)?\s+(\d{{4}})\b",
    re.IGNORECASE,
)
ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
FI_DATE_RE = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b")
YEAR_RANGE_RE = re.compile(r"\b((?:19|20)\d{2})\s*[–—-]\s*((?:19|20)\d{2})\b")
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")

NUMBER_WORDS = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "nolla": "0",
    "nollaa": "0",
    "nollasta": "0",
    "yhden": "1",
    "yksi": "1",
    "kaksi": "2",
    "kahden": "2",
    "kolme": "3",
    "kolmen": "3",
    "kolmella": "3",
    "kolmesta": "3",
    "neljä": "4",
    "neljän": "4",
    "neljässä": "4",
    "neljästä": "4",
    "viisi": "5",
    "viiden": "5",
    "viidestä": "5",
    "kuusi": "6",
    "kuuden": "6",
    "kuudesta": "6",
    "seitsemän": "7",
    "kahdeksan": "8",
    "yhdeksän": "9",
    "kymmenen": "10",
}
NUMBER_WORD_RE = re.compile(
    r"\b(" + "|".join(sorted((re.escape(word) for word in NUMBER_WORDS), key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
NUMBER_ATOM = (
    r"(?:"
    r"\d{1,3}(?:[ \u00a0\u202f]\d{3})+(?:[.,]\d+)?"
    r"|\d{1,3}(?:,\d{3})+(?:\.\d+)?"
    r"|\d{1,3}(?:\.\d{3})+(?:,\d+)?"
    r"|\d+(?:[.,]\d+)?"
    r")"
)
NUMBER_RE = re.compile(rf"(?<![\w]){NUMBER_ATOM}(?![\w])")
NUMBER_RANGE_RE = re.compile(rf"(?<![\w])({NUMBER_ATOM})\s*[–—-]\s*({NUMBER_ATOM})(?![\w])")
ALPHANUMERIC_ID_RE = re.compile(
    r"\b(?=[A-Za-z0-9_./-]*[A-Za-z])(?=[A-Za-z0-9_./-]*\d)[A-Za-z0-9_][A-Za-z0-9_./-]*\b"
)

CURRENCY_PATTERNS = {
    "CAD": re.compile(r"\bCAD\b", re.IGNORECASE),
    "EUR": re.compile(r"(?:€|\bEUR\b|\beuro(?:a|n|t|s)?\b|\beuros?\b)", re.IGNORECASE),
    "NZD": re.compile(
        r"(?:\bNZD\b|\bUuden-Seelannin dollari(?:a|n|t)?\b|\bNew Zealand dollars?\b)",
        re.IGNORECASE,
    ),
    "PLN": re.compile(r"\bPLN\b", re.IGNORECASE),
    "USD": re.compile(r"\bUSD\b", re.IGNORECASE),
}
UNIT_PATTERNS = {
    "litre": re.compile(
        r"(?:\blitra\w*\b|\blitres?\b|\bmilj\.\s*l\b|(?:^|_)litres?(?:_|$))",
        re.IGNORECASE,
    ),
    "millilitre": re.compile(r"(?:\bmillilitres?\b|\bml\b|_ml\b)", re.IGNORECASE),
}
MAGNITUDE_PATTERNS = {
    Decimal("1000000"): re.compile(r"(?:\bmilj\.?\b|\bmillion\b)", re.IGNORECASE),
    Decimal("1000000000"): re.compile(r"(?:\bmrd\.?\b|\bbillion\b)", re.IGNORECASE),
}


def _month_number(raw: str) -> int:
    folded = raw.casefold()
    for name, number in MONTHS.items():
        if folded.startswith(name):
            return number
    raise ValueError(f"Unsupported month name: {raw}")


def _decimal_value(raw: str, language: str) -> Decimal:
    compact = re.sub(r"[ \u00a0\u202f]", "", raw)
    comma_count = compact.count(",")
    dot_count = compact.count(".")
    if comma_count and dot_count:
        decimal_separator = "," if compact.rfind(",") > compact.rfind(".") else "."
        grouping_separator = "." if decimal_separator == "," else ","
        compact = compact.replace(grouping_separator, "").replace(decimal_separator, ".")
    elif comma_count > 1:
        compact = compact.replace(",", "")
    elif dot_count > 1:
        compact = compact.replace(".", "")
    elif comma_count == 1:
        integer, fraction = compact.split(",", 1)
        if language == "en" and len(fraction) == 3 and len(integer) <= 3:
            compact = integer + fraction
        else:
            compact = integer + "." + fraction
    # A single dot is accepted as a decimal separator in both languages. This
    # covers the public register's existing 1.241-million display as well as
    # conventional English decimals.
    try:
        number = Decimal(compact)
    except InvalidOperation as error:
        raise ValueError(f"Invalid numeric token: {raw}") from error
    return number


def _canonical_decimal(raw: str, language: str, multiplier: Decimal = Decimal("1")) -> str:
    number = _decimal_value(raw, language) * multiplier
    if number == 0:
        return "0"
    rendered = format(number.normalize(), "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def _extract_temporal_tokens(text: str) -> tuple[Counter[str], str]:
    tokens: Counter[str] = Counter()

    def replace_iso(match: re.Match[str]) -> str:
        tokens[f"date:{match.group(1)}-{match.group(2)}-{match.group(3)}"] += 1
        return " "

    def replace_fi_date(match: re.Match[str]) -> str:
        day, month, year = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        tokens[f"date:{year:04d}-{month:02d}-{day:02d}"] += 1
        return " "

    def replace_named_date(match: re.Match[str]) -> str:
        day, month, year = int(match.group(1)), _month_number(match.group(2)), int(match.group(3))
        tokens[f"date:{year:04d}-{month:02d}-{day:02d}"] += 1
        return " "

    def replace_month_year(match: re.Match[str]) -> str:
        month, year = _month_number(match.group(1)), int(match.group(2))
        tokens[f"month:{year:04d}-{month:02d}"] += 1
        return " "

    def replace_year_range(match: re.Match[str]) -> str:
        tokens[f"year-range:{match.group(1)}-{match.group(2)}"] += 1
        return " "

    text = ISO_DATE_RE.sub(replace_iso, text)
    text = FI_DATE_RE.sub(replace_fi_date, text)
    text = EN_DATE_RE.sub(replace_named_date, text)
    text = EN_MONTH_YEAR_RE.sub(replace_month_year, text)
    text = FI_MONTH_YEAR_RE.sub(replace_month_year, text)
    text = YEAR_RANGE_RE.sub(replace_year_range, text)
    for match in YEAR_RE.finditer(text):
        tokens[f"year:{match.group(0)}"] += 1
    text = YEAR_RE.sub(" ", text)
    return tokens, text


def _magnitude_matches(text: str) -> list[tuple[int, int, Decimal]]:
    matches: list[tuple[int, int, Decimal]] = []
    for multiplier, pattern in MAGNITUDE_PATTERNS.items():
        matches.extend((match.start(), match.end(), multiplier) for match in pattern.finditer(text))
    return sorted(matches)


def _nearest_multiplier(start: int, end: int, matches: Sequence[tuple[int, int, Decimal]]) -> Decimal:
    if not matches:
        return Decimal("1")
    unique = {multiplier for _, _, multiplier in matches}
    if len(unique) == 1:
        return next(iter(unique))

    def distance(item: tuple[int, int, Decimal]) -> int:
        magnitude_start, magnitude_end, _ = item
        if magnitude_end <= start:
            return start - magnitude_end
        if magnitude_start >= end:
            return magnitude_start - end
        return 0

    return min(matches, key=distance)[2]


def _cell_semantic_tokens(text: str, language: str) -> Counter[str]:
    tokens, remaining = _extract_temporal_tokens(URL_RE.sub(" ", text))

    # Currency and physical-unit repetition may differ in polished translation
    # (for example, repeating EUR before both range endpoints). Presence and
    # the normalized numeric amounts are the semantic invariants.
    for currency, pattern in CURRENCY_PATTERNS.items():
        if pattern.search(remaining):
            tokens[f"currency:{currency}"] = 1
    for unit, pattern in UNIT_PATTERNS.items():
        if pattern.search(remaining):
            tokens[f"unit:{unit}"] = 1

    def replace_number_word(match: re.Match[str]) -> str:
        tokens[f"number:{NUMBER_WORDS[match.group(1).casefold()]}"] += 1
        return " "

    remaining = NUMBER_WORD_RE.sub(replace_number_word, remaining)
    # Preserve semantic ordinals and hyphenated measurements before removing
    # patent, case and formula identifiers that merely happen to contain digits.
    remaining = re.sub(r"\b(\d+)(?:st|nd|rd|th)\b", r"\1", remaining, flags=re.IGNORECASE)
    remaining = re.sub(
        r"\b(\d+(?:[.,]\d+)?)\s*-\s*year\b",
        r"\1 year",
        remaining,
        flags=re.IGNORECASE,
    )
    remaining = ALPHANUMERIC_ID_RE.sub(" ", remaining)
    magnitudes = _magnitude_matches(remaining)

    range_count = 0

    def replace_number_range(match: re.Match[str]) -> str:
        nonlocal range_count
        low_multiplier = _nearest_multiplier(match.start(1), match.end(1), magnitudes)
        high_multiplier = _nearest_multiplier(match.start(2), match.end(2), magnitudes)
        tokens[f"number:{_canonical_decimal(match.group(1), language, low_multiplier)}"] += 1
        tokens[f"number:{_canonical_decimal(match.group(2), language, high_multiplier)}"] += 1
        tokens["relation:range"] += 1
        range_count += 1
        return " " * (match.end() - match.start())

    remaining = NUMBER_RANGE_RE.sub(replace_number_range, remaining)
    number_matches = list(NUMBER_RE.finditer(remaining))
    if (
        range_count == 0
        and len(number_matches) >= 2
        and re.search(r"\brange\s+(?:of|from)\b", remaining, flags=re.IGNORECASE)
        and re.search(r"\bto\b", remaining, flags=re.IGNORECASE)
    ):
        tokens["relation:range"] += 1
    for match in number_matches:
        multiplier = _nearest_multiplier(match.start(), match.end(), magnitudes)
        tokens[f"number:{_canonical_decimal(match.group(0), language, multiplier)}"] += 1
    return tokens


def semantic_tokens(row: Sequence[str], language: str = "fi") -> Counter[str]:
    """Return language-neutral numeric, currency, unit and period tokens."""

    tokens: Counter[str] = Counter()
    # Sources and confidence have their own stricter checks below. Processing
    # cell-by-cell keeps a magnitude local to the amount it scales.
    for index, value in enumerate(row):
        if index in {3, 7}:
            continue
        tokens.update(_cell_semantic_tokens(str(value), language))
    # Currency/unit presence is a row-level invariant, not a prose repetition
    # count. Numeric/date/range multiplicities remain strict.
    for token in list(tokens):
        if token.startswith(("currency:", "unit:")):
            tokens[token] = 1
    return tokens


def source_identifiers(source: str) -> Counter[str]:
    """Extract URLs, repository paths and explicit source selectors."""

    tokens: Counter[str] = Counter()
    for match in URL_RE.finditer(source):
        tokens[f"url:{match.group(0).rstrip('.,);]')}"] += 1
    without_urls = URL_RE.sub(" ", source)
    for match in LOCAL_SOURCE_RE.finditer(without_urls):
        tokens[f"path:{match.group(0)}"] += 1
    for match in SOURCE_ID_RE.finditer(without_urls):
        tokens[f"source-id:{match.group(1)}"] += 1
    for match in SOURCE_SELECTOR_RE.finditer(without_urls):
        tokens[f"selector:{match.group(1)}"] += 1
    return tokens


def date_tokens(value: str) -> Counter[str]:
    tokens, remaining = _extract_temporal_tokens(value)
    if remaining.strip(" /-–—"):
        # Date cells may contain translated descriptors (for example
        # "2025 volume / 2026 prices"); their period tokens still must match.
        pass
    return tokens


def validate_register_parity(
    finnish_rows: Sequence[Sequence[str]],
    english_rows: Sequence[Sequence[str]],
) -> list[str]:
    """Validate row-aligned factual parity without comparing prose literally."""

    errors: list[str] = []
    if len(finnish_rows) != len(english_rows):
        return [
            "Evidence Register language row counts differ: "
            f"fi={len(finnish_rows)}, en={len(english_rows)}"
        ]
    for index, (fi_row, en_row) in enumerate(zip(finnish_rows, english_rows), start=1):
        if len(fi_row) != 9 or len(en_row) != 9:
            errors.append(f"Evidence Register row {index} must contain nine cells in both languages")
            continue
        expected_confidence = CONFIDENCE_MAP.get(str(fi_row[7]))
        if expected_confidence != str(en_row[7]):
            errors.append(
                f"Evidence Register row {index} confidence differs: "
                f"fi={fi_row[7]!r}, en={en_row[7]!r}"
            )
        fi_dates = date_tokens(str(fi_row[4]))
        en_dates = date_tokens(str(en_row[4]))
        if fi_dates != en_dates:
            errors.append(
                f"Evidence Register row {index} date/period tokens differ: "
                f"fi={dict(fi_dates)}, en={dict(en_dates)}"
            )
        fi_sources = source_identifiers(str(fi_row[3]))
        en_sources = source_identifiers(str(en_row[3]))
        if fi_sources != en_sources:
            errors.append(
                f"Evidence Register row {index} URL/source identifiers differ: "
                f"fi={dict(fi_sources)}, en={dict(en_sources)}"
            )
        fi_semantics = semantic_tokens(fi_row, "fi")
        en_semantics = semantic_tokens(en_row, "en")
        if fi_semantics != en_semantics:
            errors.append(
                f"Evidence Register row {index} numeric/unit/currency/period tokens differ: "
                f"fi={dict(fi_semantics)}, en={dict(en_semantics)}"
            )
    return errors
