#!/usr/bin/env python3
"""Build the public 195-country Pixan evidence atlas.

Only explicitly allowlisted fields and sources are imported from the redacted
Marnet public baseline. The full upstream snapshot is intentionally not stored
in this repository. The generated files contain no private correspondence,
operational instructions, local paths, or credentials.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CURATED_PATH = ROOT / "source" / "curated.json"
PUBLIC_BASELINE_PATH = ROOT / "source" / "marnet-public-baseline.json"
UPSTREAM_METADATA_PATH = ROOT / "source" / "marnet-upstream.metadata.json"
MARKET_OBSERVATIONS_PATH = ROOT / "source" / "market-observations.json"
PATENT_HISTORY_PATH = ROOT / "source" / "patent-history.json"
CHANGELOG_PATH = ROOT / "source" / "changelog.json"
OUTPUT_DIR = ROOT / "site" / "data"

DIMENSIONS = (
    "officialSales",
    "officialVolume",
    "taxRevenue",
    "customs",
    "model",
    "regulation",
    "patent",
)
DIMENSION_STATUSES = {"verified", "partial", "missing", "notApplicable"}
STATUS_SCORE = {"verified": 1.0, "partial": 0.5, "missing": 0.0, "notApplicable": 1.0}
DIMENSION_WEIGHT = {
    "officialSales": 0.22,
    "officialVolume": 0.16,
    "taxRevenue": 0.14,
    "customs": 0.14,
    "model": 0.08,
    "regulation": 0.12,
    "patent": 0.14,
}

ALLOWED_EMAIL = "jouni.rautio78@gmail.com"
ALLOWED_PHONE_DIGITS = "358400355544"
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
PLUS_PHONE_RE = re.compile(r"(?<!\w)\+[0-9][0-9 .()\-/]{6,}[0-9]")
ABSOLUTE_PATH_RE = re.compile(
    r"(?i)(?:file://[^\s]+|(?<![:\w])/(?:Users|home|private|tmp|var|etc)/[^\s,;]+|[A-Z]:\\[^\s,;]+)"
)
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|passwd|authorization|bearer|private[_-]?key|connection[_-]?string)\b\s*[:=]\s*[^\s,;]+"
)

MARKET_SOURCE_TOP_LEVEL_KEYS = {
    "schemaVersion",
    "asOf",
    "reviewedAt",
    "modelReadiness",
    "donorProtocol",
    "donorCandidates",
    "disclaimerEn",
    "disclaimerFi",
    "sources",
    "observations",
    "models",
}
MARKET_READINESS_KEYS = {
    "status",
    "comparableFullYearMarketValueDonors",
    "minimumRequiredDonors",
    "reasonEn",
    "reasonFi",
}
MARKET_SOURCE_KEYS = {"sourceId", "publisher", "sourceKind", "pageUrl", "retrievedAt"}
MARKET_SOURCE_OPTIONAL_KEYS = {"downloadUrl"}
MARKET_DONOR_PROTOCOL_KEYS = {
    "protocolVersion",
    "acceptanceRuleEn",
    "acceptanceRuleFi",
    "criteria",
}
MARKET_DONOR_CRITERION_KEYS = {
    "criterionId",
    "titleEn",
    "titleFi",
    "requirementEn",
    "requirementFi",
}
MARKET_DONOR_CANDIDATE_KEYS = {
    "candidateId",
    "countryIso2",
    "geography",
    "year",
    "referenceType",
    "referenceId",
    "decision",
    "passedCriteria",
    "failedCriteria",
    "openCriteria",
    "headlineEn",
    "headlineFi",
    "decisionReasonEn",
    "decisionReasonFi",
    "nextEvidenceEn",
    "nextEvidenceFi",
    "sourceIds",
}
MARKET_OBSERVATION_KEYS = {
    "observationId",
    "countryIso2",
    "geography",
    "year",
    "metric",
    "value",
    "unit",
    "currency",
    "period",
    "evidenceStatus",
    "finality",
    "productScope",
    "marketValueBasis",
    "comparableMarketValue",
    "atlasEstimate",
    "sourceIds",
    "labelEn",
    "labelFi",
    "limitationEn",
    "limitationFi",
}
MARKET_MODEL_KEYS = {
    "modelId",
    "countryIso2",
    "year",
    "labelEn",
    "labelFi",
    "evidenceStatus",
    "confidence",
    "yearMismatch",
    "productScope",
    "marketValueBasis",
    "comparableMarketValue",
    "atlasEstimate",
    "formula",
    "inputIds",
    "rangeInputMap",
    "currency",
    "low",
    "central",
    "high",
    "exclusions",
    "limitationEn",
    "limitationFi",
}
MARKET_CSV_FIELDS = [
    "recordType",
    "recordId",
    "countryIso2",
    "geography",
    "year",
    "metric",
    "evidenceStatus",
    "finality",
    "productScope",
    "marketValueBasis",
    "comparableMarketValue",
    "atlasEstimate",
    "currency",
    "unit",
    "value",
    "low",
    "central",
    "high",
    "confidence",
    "yearMismatch",
    "formula",
    "inputIds",
    "sourceIds",
    "exclusions",
    "labelEn",
    "labelFi",
    "limitationEn",
    "limitationFi",
]

PATENT_SOURCE_TOP_LEVEL_KEYS = {
    "schemaVersion",
    "asOf",
    "reviewedAt",
    "disclaimerEn",
    "disclaimerFi",
    "patent",
    "sources",
    "timeline",
    "familyMembers",
    "proceedings",
    "diligenceAlerts",
    "monetisation",
}
PATENT_FAMILY_CSV_FIELDS = [
    "jurisdictionCode",
    "jurisdictionEn",
    "jurisdictionFi",
    "jurisdictionCategory",
    "applicationNumber",
    "publicationNumber",
    "publicationDate",
    "recordType",
    "centralRecordStatusEn",
    "centralRecordStatusFi",
    "currentNationalStatusEn",
    "currentNationalStatusFi",
    "verificationLevel",
    "sourceIds",
    "registerUrl",
    "limitationEn",
    "limitationFi",
]


# UN 193 member states plus the Holy See (VA) and the State of Palestine (PS).
# Dependent territories and Kosovo are intentionally outside this master.
COUNTRY_DATA = """iso2|name|nameFi|region
DZ|Algeria|Algeria|Africa
AO|Angola|Angola|Africa
BJ|Benin|Benin|Africa
BW|Botswana|Botswana|Africa
BF|Burkina Faso|Burkina Faso|Africa
BI|Burundi|Burundi|Africa
CV|Cabo Verde|Kap Verde|Africa
CM|Cameroon|Kamerun|Africa
CF|Central African Republic|Keski-Afrikan tasavalta|Africa
TD|Chad|Tšad|Africa
KM|Comoros|Komorit|Africa
CG|Congo|Kongon tasavalta|Africa
CD|Democratic Republic of the Congo|Kongon demokraattinen tasavalta|Africa
CI|Côte d'Ivoire|Norsunluurannikko|Africa
DJ|Djibouti|Djibouti|Africa
EG|Egypt|Egypti|Africa
GQ|Equatorial Guinea|Päiväntasaajan Guinea|Africa
ER|Eritrea|Eritrea|Africa
SZ|Eswatini|Eswatini|Africa
ET|Ethiopia|Etiopia|Africa
GA|Gabon|Gabon|Africa
GM|Gambia|Gambia|Africa
GH|Ghana|Ghana|Africa
GN|Guinea|Guinea|Africa
GW|Guinea-Bissau|Guinea-Bissau|Africa
KE|Kenya|Kenia|Africa
LS|Lesotho|Lesotho|Africa
LR|Liberia|Liberia|Africa
LY|Libya|Libya|Africa
MG|Madagascar|Madagaskar|Africa
MW|Malawi|Malawi|Africa
ML|Mali|Mali|Africa
MR|Mauritania|Mauritania|Africa
MU|Mauritius|Mauritius|Africa
MA|Morocco|Marokko|Africa
MZ|Mozambique|Mosambik|Africa
NA|Namibia|Namibia|Africa
NE|Niger|Niger|Africa
NG|Nigeria|Nigeria|Africa
RW|Rwanda|Ruanda|Africa
ST|Sao Tome and Principe|São Tomé ja Príncipe|Africa
SN|Senegal|Senegal|Africa
SC|Seychelles|Seychellit|Africa
SL|Sierra Leone|Sierra Leone|Africa
SO|Somalia|Somalia|Africa
ZA|South Africa|Etelä-Afrikka|Africa
SS|South Sudan|Etelä-Sudan|Africa
SD|Sudan|Sudan|Africa
TZ|United Republic of Tanzania|Tansania|Africa
TG|Togo|Togo|Africa
TN|Tunisia|Tunisia|Africa
UG|Uganda|Uganda|Africa
ZM|Zambia|Sambia|Africa
ZW|Zimbabwe|Zimbabwe|Africa
AG|Antigua and Barbuda|Antigua ja Barbuda|Americas
AR|Argentina|Argentiina|Americas
BS|Bahamas|Bahama|Americas
BB|Barbados|Barbados|Americas
BZ|Belize|Belize|Americas
BO|Bolivia|Bolivia|Americas
BR|Brazil|Brasilia|Americas
CA|Canada|Kanada|Americas
CL|Chile|Chile|Americas
CO|Colombia|Kolumbia|Americas
CR|Costa Rica|Costa Rica|Americas
CU|Cuba|Kuuba|Americas
DM|Dominica|Dominica|Americas
DO|Dominican Republic|Dominikaaninen tasavalta|Americas
EC|Ecuador|Ecuador|Americas
SV|El Salvador|El Salvador|Americas
GD|Grenada|Grenada|Americas
GT|Guatemala|Guatemala|Americas
GY|Guyana|Guyana|Americas
HT|Haiti|Haiti|Americas
HN|Honduras|Honduras|Americas
JM|Jamaica|Jamaika|Americas
MX|Mexico|Meksiko|Americas
NI|Nicaragua|Nicaragua|Americas
PA|Panama|Panama|Americas
PY|Paraguay|Paraguay|Americas
PE|Peru|Peru|Americas
KN|Saint Kitts and Nevis|Saint Kitts ja Nevis|Americas
LC|Saint Lucia|Saint Lucia|Americas
VC|Saint Vincent and the Grenadines|Saint Vincent ja Grenadiinit|Americas
SR|Suriname|Suriname|Americas
TT|Trinidad and Tobago|Trinidad ja Tobago|Americas
US|United States of America|Yhdysvallat|Americas
UY|Uruguay|Uruguay|Americas
VE|Venezuela|Venezuela|Americas
AF|Afghanistan|Afganistan|Asia
AM|Armenia|Armenia|Asia
AZ|Azerbaijan|Azerbaidžan|Asia
BH|Bahrain|Bahrain|Asia
BD|Bangladesh|Bangladesh|Asia
BT|Bhutan|Bhutan|Asia
BN|Brunei Darussalam|Brunei|Asia
KH|Cambodia|Kambodža|Asia
CN|China|Kiina|Asia
CY|Cyprus|Kypros|Asia
GE|Georgia|Georgia|Asia
IN|India|Intia|Asia
ID|Indonesia|Indonesia|Asia
IR|Iran|Iran|Asia
IQ|Iraq|Irak|Asia
IL|Israel|Israel|Asia
JP|Japan|Japani|Asia
JO|Jordan|Jordania|Asia
KZ|Kazakhstan|Kazakstan|Asia
KP|Democratic People's Republic of Korea|Pohjois-Korea|Asia
KR|Republic of Korea|Etelä-Korea|Asia
KW|Kuwait|Kuwait|Asia
KG|Kyrgyzstan|Kirgisia|Asia
LA|Lao People's Democratic Republic|Laos|Asia
LB|Lebanon|Libanon|Asia
MY|Malaysia|Malesia|Asia
MV|Maldives|Malediivit|Asia
MN|Mongolia|Mongolia|Asia
MM|Myanmar|Myanmar|Asia
NP|Nepal|Nepal|Asia
OM|Oman|Oman|Asia
PK|Pakistan|Pakistan|Asia
PS|State of Palestine|Palestiinan valtio|Asia
PH|Philippines|Filippiinit|Asia
QA|Qatar|Qatar|Asia
SA|Saudi Arabia|Saudi-Arabia|Asia
SG|Singapore|Singapore|Asia
LK|Sri Lanka|Sri Lanka|Asia
SY|Syrian Arab Republic|Syyria|Asia
TJ|Tajikistan|Tadžikistan|Asia
TH|Thailand|Thaimaa|Asia
TL|Timor-Leste|Itä-Timor|Asia
TR|Türkiye|Turkki|Asia
TM|Turkmenistan|Turkmenistan|Asia
AE|United Arab Emirates|Yhdistyneet arabiemiirikunnat|Asia
UZ|Uzbekistan|Uzbekistan|Asia
VN|Viet Nam|Vietnam|Asia
YE|Yemen|Jemen|Asia
AL|Albania|Albania|Europe
AD|Andorra|Andorra|Europe
AT|Austria|Itävalta|Europe
BY|Belarus|Valko-Venäjä|Europe
BE|Belgium|Belgia|Europe
BA|Bosnia and Herzegovina|Bosnia ja Hertsegovina|Europe
BG|Bulgaria|Bulgaria|Europe
HR|Croatia|Kroatia|Europe
CZ|Czechia|Tšekki|Europe
DK|Denmark|Tanska|Europe
EE|Estonia|Viro|Europe
FI|Finland|Suomi|Europe
FR|France|Ranska|Europe
DE|Germany|Saksa|Europe
GR|Greece|Kreikka|Europe
VA|Holy See|Pyhä istuin|Europe
HU|Hungary|Unkari|Europe
IS|Iceland|Islanti|Europe
IE|Ireland|Irlanti|Europe
IT|Italy|Italia|Europe
LV|Latvia|Latvia|Europe
LI|Liechtenstein|Liechtenstein|Europe
LT|Lithuania|Liettua|Europe
LU|Luxembourg|Luxemburg|Europe
MT|Malta|Malta|Europe
MD|Republic of Moldova|Moldova|Europe
MC|Monaco|Monaco|Europe
ME|Montenegro|Montenegro|Europe
NL|Netherlands|Alankomaat|Europe
MK|North Macedonia|Pohjois-Makedonia|Europe
NO|Norway|Norja|Europe
PL|Poland|Puola|Europe
PT|Portugal|Portugali|Europe
RO|Romania|Romania|Europe
RU|Russian Federation|Venäjä|Europe
SM|San Marino|San Marino|Europe
RS|Serbia|Serbia|Europe
SK|Slovakia|Slovakia|Europe
SI|Slovenia|Slovenia|Europe
ES|Spain|Espanja|Europe
SE|Sweden|Ruotsi|Europe
CH|Switzerland|Sveitsi|Europe
UA|Ukraine|Ukraina|Europe
GB|United Kingdom|Yhdistynyt kuningaskunta|Europe
AU|Australia|Australia|Oceania
FJ|Fiji|Fidži|Oceania
KI|Kiribati|Kiribati|Oceania
MH|Marshall Islands|Marshallinsaaret|Oceania
FM|Micronesia (Federated States of)|Mikronesia|Oceania
NR|Nauru|Nauru|Oceania
NZ|New Zealand|Uusi-Seelanti|Oceania
PW|Palau|Palau|Oceania
PG|Papua New Guinea|Papua-Uusi-Guinea|Oceania
WS|Samoa|Samoa|Oceania
SB|Solomon Islands|Salomonsaaret|Oceania
TO|Tonga|Tonga|Oceania
TV|Tuvalu|Tuvalu|Oceania
VU|Vanuatu|Vanuatu|Oceania
"""


def _country_catalog() -> list[dict[str, str]]:
    rows = list(csv.DictReader(COUNTRY_DATA.strip().splitlines(), delimiter="|"))
    if len(rows) != 195:
        raise RuntimeError(f"Internal UN195 catalogue has {len(rows)} rows")
    if len({row["iso2"] for row in rows}) != 195:
        raise RuntimeError("Internal UN195 catalogue contains duplicate ISO2 codes")
    return rows


COUNTRY_CATALOG = _country_catalog()
COUNTRY_ISO2 = {row["iso2"] for row in COUNTRY_CATALOG}

LEGACY_COUNTRY_TO_ISO2 = {
    "United States": "US",
    "Canada": "CA",
    "Germany": "DE",
    "France": "FR",
    "Italy": "IT",
    "Spain": "ES",
    "Poland": "PL",
    "Netherlands": "NL",
    "Belgium": "BE",
    "Luxembourg": "LU",
    "Finland": "FI",
    "Sweden": "SE",
    "Denmark": "DK",
    "Norway": "NO",
    "Austria": "AT",
    "Switzerland": "CH",
    "United Kingdom": "GB",
    "China": "CN",
    "Japan": "JP",
    "South Korea": "KR",
    "Australia": "AU",
    "Brazil": "BR",
    "Russia": "RU",
}

GRADE_BY_CLAIM_TYPE = {
    "delivery_sales": "A",
    "official_volume": "A",
    "official_volume_tax": "A",
    "tax_actual": "A",
    "customs": "B",
    "historical_sales": "B",
    "tax_rate": "B",
    "reporting_rule": "B",
    "reporting_schema": "B",
    "reporting_registry": "B",
    "registry": "B",
    "methodology": "B",
    "official_access_route": "B",
    "combined_tax_actual": "B",
    "official_forecast": "C",
    "model": "C",
    "prevalence": "C",
    "enforcement_sample": "C",
    "coverage_audit": "C",
}

CLAIM_USE_BY_TYPE = {
    "delivery_sales": "Virallisen toimitusmyynnin ankkuri; tarkista mittari, vuosi ja kattavuus alkuperäislähteestä.",
    "official_volume": "Virallisen määrähavainnon ankkuri; tarkista yksikkö, vuosi ja veropohja alkuperäislähteestä.",
    "official_volume_tax": "Virallisen määrä- ja verohavainnon ankkuri; pidä määrä ja verotuotto erillisinä mittareina.",
    "tax_actual": "Toteutuneen virallisen verotuoton ankkuri; ei yksin osoita vähittäismyyntiä tai tuotemäärää.",
    "customs": "Rajakaupan tai tullivirran ankkuri; ei yksin osoita kotimaista kuluttajamyyntiä.",
    "historical_sales": "Historiallinen myyntiankkuri; ajankohta ja mittarin jatkuvuus on tarkistettava erikseen.",
    "tax_rate": "Veroasteen sääntelyankkuri; ei toteutunut määrä- tai myyntihavainto.",
    "reporting_rule": "Raportointivelvoitteen sääntelyankkuri; julkisen toteumatiedon saatavuus tarkistetaan erikseen.",
    "reporting_schema": "Viranomaisraportoinnin tietorakenne; ei sellaisenaan kansallinen toteumasumma.",
    "reporting_registry": "Viranomaisrekisterin tai raportointikanavan ankkuri; ei sellaisenaan vuosimyyntiä.",
    "registry": "Tuote- tai ilmoitusrekisterin ankkuri; rekisteririvejä ei tulkita myyntimääräksi.",
    "methodology": "Virallisen tilastomenetelmän ankkuri; varsinainen toteumaluku on haettava erikseen.",
    "official_access_route": "Virallisen tietopalvelun reitti; tarvittava maakohtainen poiminta ja täsmäytys puuttuu.",
    "combined_tax_actual": "Yhdistetyn verokertymän ankkuri; tuoteryhmäjako on varmistettava ennen markkinatulkintaa.",
    "official_forecast": "Virallinen ennuste tai budjettioletus; ei toteutunut myynti tai verokertymä.",
    "model": "Mallinnettu markkina-arvio; oletukset ja epävarmuus on pidettävä näkyvissä.",
    "prevalence": "Käyttäjäyleisyyden tukihavainto; ei suora myynti-, määrä- tai veromittari.",
    "enforcement_sample": "Kohdennetun valvontaotoksen tukihavainto; osumaprosentti ei ole markkinaosuus.",
    "coverage_audit": "Raportoinnin kattavuuden tukihavainto; ei itsenäinen markkinamyyntiluku.",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object in {path.name}")
    return value


def normalize_phone(value: str) -> str:
    return "".join(character for character in value if character.isdigit())


def sanitize_text(value: Any) -> str:
    """Redact sensitive patterns from legacy free text and normalize spacing."""
    text = str(value or "").replace("\x00", " ").strip()
    text = ABSOLUTE_PATH_RE.sub("[redacted-path]", text)
    text = SECRET_ASSIGNMENT_RE.sub("[redacted-secret]", text)

    def email_replacement(match: re.Match[str]) -> str:
        return match.group(0) if match.group(0).lower() == ALLOWED_EMAIL else "[redacted-email]"

    def phone_replacement(match: re.Match[str]) -> str:
        digits = normalize_phone(match.group(0))
        return match.group(0) if digits == ALLOWED_PHONE_DIGITS else "[redacted-phone]"

    text = EMAIL_RE.sub(email_replacement, text)
    text = PLUS_PHONE_RE.sub(phone_replacement, text)
    return re.sub(r"[ \t]+", " ", text)


def safe_url(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    parsed = urlparse(text)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        return None
    if ABSOLUTE_PATH_RE.search(text) or SECRET_ASSIGNMENT_RE.search(text):
        return None
    return text


def apply_evidence_dimension(dimensions: dict[str, str], claim_type: str) -> None:
    updates = {
        "delivery_sales": ("officialSales", "verified"),
        "official_volume": ("officialVolume", "verified"),
        "official_volume_tax": ("officialVolume", "verified"),
        "tax_actual": ("taxRevenue", "verified"),
        "customs": ("customs", "partial"),
        "historical_sales": ("officialSales", "partial"),
        "tax_rate": ("regulation", "partial"),
        "reporting_rule": ("regulation", "partial"),
        "reporting_schema": ("regulation", "partial"),
        "reporting_registry": ("regulation", "partial"),
        "registry": ("regulation", "partial"),
        "official_access_route": ("customs", "partial"),
        "combined_tax_actual": ("taxRevenue", "partial"),
        "official_forecast": ("model", "partial"),
        "model": ("model", "partial"),
    }
    if claim_type == "official_volume_tax":
        dimensions["taxRevenue"] = "verified"
    update = updates.get(claim_type)
    if not update:
        return
    dimension, status = update
    if dimensions[dimension] == "missing":
        dimensions[dimension] = status


def best_evidence(dimensions: dict[str, str]) -> str:
    if any(dimensions[key] == "verified" for key in ("officialSales", "officialVolume", "taxRevenue")):
        return "A"
    if (
        dimensions["customs"] in {"verified", "partial"}
        or dimensions["regulation"] == "verified"
        or dimensions["patent"] in {"verified", "partial"}
        or any(dimensions[key] == "partial" for key in ("officialSales", "officialVolume", "taxRevenue"))
    ):
        return "B"
    if any(status != "missing" for status in dimensions.values()):
        return "C"
    return "D"


def coverage_percent(dimensions: dict[str, str]) -> int:
    score = sum(STATUS_SCORE[dimensions[key]] * DIMENSION_WEIGHT[key] for key in DIMENSIONS)
    return round(score * 100)


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def atomic_write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
                extrasaction="ignore",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def build() -> dict[str, Any]:
    curated = load_json(CURATED_PATH)
    baseline = load_json(PUBLIC_BASELINE_PATH)
    upstream_metadata = load_json(UPSTREAM_METADATA_PATH)

    expected_commit = curated["meta"]["legacySourceCommit"]
    if expected_commit != upstream_metadata.get("commit"):
        raise ValueError("The curated Marnet commit must match the recorded upstream metadata")
    if baseline.get("schemaVersion") != 1:
        raise ValueError("The Marnet public baseline schemaVersion must be 1")
    public_metadata = upstream_metadata.get("publicBaseline", {})
    if public_metadata.get("path") != "source/marnet-public-baseline.json":
        raise ValueError("The recorded public baseline path is invalid")
    baseline_bytes = PUBLIC_BASELINE_PATH.read_bytes()
    if hashlib.sha256(baseline_bytes).hexdigest() != public_metadata.get("sha256"):
        raise ValueError("The Marnet public baseline does not match its recorded SHA-256")
    if len(baseline_bytes) != public_metadata.get("size"):
        raise ValueError("The Marnet public baseline does not match its recorded byte size")

    legacy_countries: dict[str, dict[str, Any]] = {}
    for row in baseline.get("countries", []):
        source_name = row.get("sourceName")
        iso2 = LEGACY_COUNTRY_TO_ISO2.get(source_name)
        if iso2:
            legacy_countries[iso2] = row

    legacy_evidence = {row.get("title"): row for row in baseline.get("evidence", []) if row.get("title")}
    evidence: list[dict[str, Any]] = []
    country_evidence: dict[str, list[dict[str, Any]]] = {iso2: [] for iso2 in COUNTRY_ISO2}
    country_source_links: dict[str, set[str]] = {iso2: set() for iso2 in COUNTRY_ISO2}

    for index, rule in enumerate(curated["marnetEvidenceWhitelist"], start=1):
        title = rule["title"]
        source = legacy_evidence.get(title)
        if source is None:
            raise ValueError(f"Allowlisted legacy evidence is missing: {title}")
        source_url = safe_url(source.get("url"))
        if not source_url:
            raise ValueError(f"Allowlisted legacy evidence lacks a public HTTPS URL: {title}")
        claim_type = rule["claimType"]
        if claim_type not in GRADE_BY_CLAIM_TYPE:
            raise ValueError(f"Unknown claim type {claim_type!r} for {title}")
        markets = rule.get("countries", [])
        if not markets or any(iso2 not in COUNTRY_ISO2 for iso2 in markets):
            raise ValueError(f"Invalid country scope for {title}")
        item = {
            "evidenceId": f"MARNET-{index:03d}",
            "countries": markets,
            "grade": GRADE_BY_CLAIM_TYPE[claim_type],
            "legacyGrade": sanitize_text(source.get("grade")),
            "claimType": claim_type,
            "title": sanitize_text(source.get("title")),
            "coverage": f"Kuratoitu maapeitto ({len(markets)}): {', '.join(markets)}.",
            "use": CLAIM_USE_BY_TYPE[claim_type],
            "sourceUrl": source_url,
            "sourceKind": "institutional_model" if claim_type == "model" else "official_or_institutional_publication",
            "origin": f"source/marnet-public-baseline.json@{expected_commit}",
        }
        evidence.append(item)
        for iso2 in markets:
            country_evidence[iso2].append(item)
            country_source_links[iso2].add(source_url)

    # Preserve only the public HTTPS URLs explicitly retained in the redacted
    # country baseline. No arbitrary nested upstream object is traversed.
    for iso2, row in legacy_countries.items():
        for raw_url in row.get("sourceUrls", []):
            url = safe_url(raw_url)
            if not url:
                raise ValueError(f"Marnet public baseline has an invalid country source URL for {iso2}")
            country_source_links[iso2].add(url)

    dimensions_by_country: dict[str, dict[str, str]] = {
        iso2: {dimension: "missing" for dimension in DIMENSIONS} for iso2 in COUNTRY_ISO2
    }
    for iso2, items in country_evidence.items():
        for item in items:
            apply_evidence_dimension(dimensions_by_country[iso2], item["claimType"])

    for iso2, overrides in curated.get("dimensionOverrides", {}).items():
        if iso2 not in COUNTRY_ISO2:
            raise ValueError(f"Dimension override uses a non-UN195 country: {iso2}")
        unknown = set(overrides) - set(DIMENSIONS)
        if unknown:
            raise ValueError(f"Unknown dimensions for {iso2}: {sorted(unknown)}")
        for dimension, status in overrides.items():
            if status not in DIMENSION_STATUSES:
                raise ValueError(f"Invalid dimension status for {iso2}.{dimension}: {status}")
            dimensions_by_country[iso2][dimension] = status

    legal: list[dict[str, Any]] = []
    for raw in curated["germanyLegal"]:
        source_url = safe_url(raw.get("sourceUrl"))
        if not source_url:
            raise ValueError(f"German legal anchor lacks a public HTTPS URL: {raw.get('legalId')}")
        item = {key: sanitize_text(value) for key, value in raw.items() if key != "sourceUrl"}
        item["sourceUrl"] = source_url
        legal.append(item)
        country_source_links["DE"].add(source_url)

    countries: list[dict[str, Any]] = []
    for base in COUNTRY_CATALOG:
        iso2 = base["iso2"]
        legacy_row = legacy_countries.get(iso2)
        dimensions = dimensions_by_country[iso2]
        if legacy_row:
            current = "Julkisia lähdeviitteitä on tunnistettu. Tämä baseline ei siirrä upstreamin vapaamuotoista maakuvausta eikä itsessään osoita vahvistettua vuosimyyntiä."
            missing = "Virallinen vuosittainen laite- ja nestemyynti, verollinen määrä, verotuotto sekä lähteiden välinen markkinatäsmäytys on vahvistettava erikseen."
            legacy_status = "sourceLinksOnly"
        elif any(status != "missing" for status in dimensions.values()):
            current = "Julkinen sääntely- tai lähdereitti on tunnistettu; maakohtaista toteutunutta markkinamyyntiä ei ole siirretty."
            missing = "Virallinen vuosittainen laite- ja nestemyynti, verollinen määrä, verotuotto ja markkinatäsmäytys."
            legacy_status = "notTracked"
        else:
            current = "Ei julkista maakohtaista markkinahavaintoa siirretty."
            missing = "Virallinen myynti, määrä, verotuotto, tulli-, sääntely- ja patenttievidenssi."
            legacy_status = "notTracked"

        countries.append(
            {
                "iso2": iso2,
                "name": base["name"],
                "nameFi": base["nameFi"],
                "region": base["region"],
                "bestEvidence": best_evidence(dimensions),
                "coveragePercent": coverage_percent(dimensions),
                "dimensions": dimensions,
                "current": current,
                "missing": missing,
                "sourceLinks": sorted(country_source_links[iso2]),
                "legacyStatus": legacy_status,
            }
        )

    grade_counts = Counter(country["bestEvidence"] for country in countries)
    dimension_counts = {
        dimension: dict(Counter(country["dimensions"][dimension] for country in countries))
        for dimension in DIMENSIONS
    }
    region_counts = dict(Counter(country["region"] for country in countries))
    summary = {
        "countryCount": len(countries),
        "universe": "UN193+VA+PS",
        "gradeCounts": {grade: grade_counts.get(grade, 0) for grade in ("A", "B", "C", "D")},
        "dimensionCounts": {
            dimension: {status: dimension_counts[dimension].get(status, 0) for status in sorted(DIMENSION_STATUSES)}
            for dimension in DIMENSIONS
        },
        "regionCounts": region_counts,
        "evidenceCount": len(evidence),
        "legalAnchorCount": len(legal),
        "legacyCountryCount": len(legacy_countries),
    }

    reviewed_at = sanitize_text(curated["meta"]["reviewedAt"])
    if not reviewed_at:
        raise ValueError("curated meta.reviewedAt is required for a deterministic build")
    source_attribution = []
    for raw in curated["sourceAttribution"]:
        source_url = safe_url(raw.get("sourceUrl"))
        if not source_url:
            raise ValueError(f"Source attribution lacks a public HTTPS URL: {raw.get('sourceId')}")
        item = {key: sanitize_text(value) for key, value in raw.items() if key != "sourceUrl"}
        item["sourceUrl"] = source_url
        source_attribution.append(item)

    atlas = {
        "meta": {
            "title": sanitize_text(curated["meta"]["title"]),
            "version": sanitize_text(curated["meta"]["version"]),
            "asOf": sanitize_text(curated["meta"]["asOf"]),
            "generatedAt": reviewed_at,
            "legacySourceCommit": expected_commit,
            "disclaimer": sanitize_text(curated["meta"]["disclaimer"]),
            "independenceStatement": sanitize_text(curated["meta"]["independenceStatement"]),
        },
        "summary": summary,
        "countries": countries,
        "evidence": evidence,
        "legal": legal,
        "methodology": curated["methodology"],
        "submission": curated["submission"],
        "readiness": curated["readiness"],
        "sourceAttribution": source_attribution,
    }
    return atlas


def _sanitize_market_value(value: Any) -> Any:
    """Sanitize public text without altering numeric or Boolean semantics."""
    if isinstance(value, dict):
        return {key: _sanitize_market_value(nested) for key, nested in value.items()}
    if isinstance(value, list):
        return [_sanitize_market_value(nested) for nested in value]
    if isinstance(value, str):
        return sanitize_text(value)
    return value


def build_market_values() -> dict[str, Any]:
    """Build the separately consumable market-value observation dataset."""
    source = load_json(MARKET_OBSERVATIONS_PATH)
    if set(source) != MARKET_SOURCE_TOP_LEVEL_KEYS:
        raise ValueError("market-observations.json has an unexpected top-level schema")
    if source.get("schemaVersion") != 1:
        raise ValueError("market-observations.json schemaVersion must be 1")

    readiness = source.get("modelReadiness")
    if not isinstance(readiness, dict) or set(readiness) != MARKET_READINESS_KEYS:
        raise ValueError("market-observations.json modelReadiness has an unexpected schema")

    donor_protocol = source.get("donorProtocol")
    if not isinstance(donor_protocol, dict) or set(donor_protocol) != MARKET_DONOR_PROTOCOL_KEYS:
        raise ValueError("market-observations.json donorProtocol has an unexpected schema")
    donor_criteria = donor_protocol.get("criteria")
    if not isinstance(donor_criteria, list) or not donor_criteria:
        raise ValueError("market-observations.json donorProtocol.criteria must be a non-empty array")
    for raw in donor_criteria:
        if not isinstance(raw, dict) or set(raw) != MARKET_DONOR_CRITERION_KEYS:
            raise ValueError("market-observations.json donor criterion has an unexpected schema")

    donor_candidates = source.get("donorCandidates")
    if not isinstance(donor_candidates, list) or not donor_candidates:
        raise ValueError("market-observations.json donorCandidates must be a non-empty array")
    for raw in donor_candidates:
        if not isinstance(raw, dict) or set(raw) != MARKET_DONOR_CANDIDATE_KEYS:
            raise ValueError("market-observations.json donor candidate has an unexpected schema")

    sources = source.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("market-observations.json sources must be a non-empty array")
    for raw in sources:
        if not isinstance(raw, dict):
            raise ValueError("market-observations.json source entries must be objects")
        keys = set(raw)
        if not MARKET_SOURCE_KEYS.issubset(keys) or keys - MARKET_SOURCE_KEYS - MARKET_SOURCE_OPTIONAL_KEYS:
            raise ValueError(f"Unexpected market source schema: {raw.get('sourceId')}")
        for url_key in ("pageUrl", "downloadUrl"):
            if url_key in raw and not safe_url(raw[url_key]):
                raise ValueError(f"Market source {raw.get('sourceId')} has an invalid {url_key}")

    observations = source.get("observations")
    if not isinstance(observations, list) or not observations:
        raise ValueError("market-observations.json observations must be a non-empty array")
    for raw in observations:
        if not isinstance(raw, dict) or set(raw) != MARKET_OBSERVATION_KEYS:
            raise ValueError(f"Unexpected market observation schema: {raw.get('observationId') if isinstance(raw, dict) else raw}")

    models = source.get("models")
    if not isinstance(models, list) or not models:
        raise ValueError("market-observations.json models must be a non-empty array")
    for raw in models:
        if not isinstance(raw, dict) or set(raw) != MARKET_MODEL_KEYS:
            raise ValueError(f"Unexpected market model schema: {raw.get('modelId') if isinstance(raw, dict) else raw}")

    market_values = {
        "meta": {
            "schemaVersion": source["schemaVersion"],
            "asOf": source["asOf"],
            "generatedAt": source["reviewedAt"],
            "modelReadiness": readiness,
            "disclaimerEn": source["disclaimerEn"],
            "disclaimerFi": source["disclaimerFi"],
        },
        "donorProtocol": donor_protocol,
        "donorCandidates": donor_candidates,
        "sources": sources,
        "observations": observations,
        "models": models,
    }
    market_values = _sanitize_market_value(market_values)

    observations_by_id = {item["observationId"]: item for item in market_values["observations"]}
    for model in market_values["models"]:
        if model["formula"] != "volume_litres * 1000 * retail_price_eur_per_ml":
            raise ValueError(f"Unsupported market model formula: {model['modelId']}")
        input_ids = model["inputIds"]
        if any(identifier not in observations_by_id for identifier in input_ids):
            raise ValueError(f"Market model {model['modelId']} references an unknown observation")
        volume_inputs = [
            observations_by_id[identifier]
            for identifier in input_ids
            if observations_by_id[identifier]["metric"] == "taxed_substitutes_volume"
        ]
        if len(volume_inputs) != 1:
            raise ValueError(f"Market model {model['modelId']} must have one taxed-volume input")
        range_map = model["rangeInputMap"]
        if set(range_map) != {"low", "central", "high"}:
            raise ValueError(f"Market model {model['modelId']} rangeInputMap is invalid")
        volume_litres = volume_inputs[0]["value"]
        for bound in ("low", "central", "high"):
            price = observations_by_id[range_map[bound]]
            expected = round(volume_litres * 1000 * price["value"])
            if model[bound] != expected:
                raise ValueError(f"Market model {model['modelId']}.{bound} does not match its formula")
            model[bound] = expected

    return market_values


def market_values_csv_rows(market_values: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the deterministic flattened CSV representation."""
    rows: list[dict[str, Any]] = []
    observations_by_id = {item["observationId"]: item for item in market_values["observations"]}

    def bool_cell(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        return ""

    for item in market_values["observations"]:
        rows.append(
            {
                "recordType": "observation",
                "recordId": item["observationId"],
                "countryIso2": item["countryIso2"] or "",
                "geography": item["geography"],
                "year": item["year"],
                "metric": item["metric"],
                "evidenceStatus": item["evidenceStatus"],
                "finality": item["finality"],
                "productScope": item["productScope"],
                "marketValueBasis": item["marketValueBasis"],
                "comparableMarketValue": bool_cell(item["comparableMarketValue"]),
                "atlasEstimate": bool_cell(item["atlasEstimate"]),
                "currency": item["currency"] or "",
                "unit": item["unit"],
                "value": item["value"],
                "sourceIds": "|".join(item["sourceIds"]),
                "labelEn": item["labelEn"],
                "labelFi": item["labelFi"],
                "limitationEn": item["limitationEn"],
                "limitationFi": item["limitationFi"],
            }
        )

    catalog_by_iso = {item["iso2"]: item for item in COUNTRY_CATALOG}
    for model in market_values["models"]:
        source_ids: list[str] = []
        for input_id in model["inputIds"]:
            for source_id in observations_by_id[input_id]["sourceIds"]:
                if source_id not in source_ids:
                    source_ids.append(source_id)
        rows.append(
            {
                "recordType": "model",
                "recordId": model["modelId"],
                "countryIso2": model["countryIso2"],
                "geography": catalog_by_iso[model["countryIso2"]]["name"],
                "year": model["year"],
                "metric": "retail_equivalent_plausibility_range",
                "evidenceStatus": model["evidenceStatus"],
                "finality": "modelled",
                "productScope": model["productScope"],
                "marketValueBasis": model["marketValueBasis"],
                "comparableMarketValue": bool_cell(model["comparableMarketValue"]),
                "atlasEstimate": bool_cell(model["atlasEstimate"]),
                "currency": model["currency"],
                "unit": model["currency"],
                "low": model["low"],
                "central": model["central"],
                "high": model["high"],
                "confidence": model["confidence"],
                "yearMismatch": bool_cell(model["yearMismatch"]),
                "formula": model["formula"],
                "inputIds": "|".join(model["inputIds"]),
                "sourceIds": "|".join(source_ids),
                "exclusions": "|".join(model["exclusions"]),
                "labelEn": model["labelEn"],
                "labelFi": model["labelFi"],
                "limitationEn": model["limitationEn"],
                "limitationFi": model["limitationFi"],
            }
        )
    return rows


def build_patent_history() -> dict[str, Any]:
    """Build the separately consumable patent-history and strategy dataset."""
    source = load_json(PATENT_HISTORY_PATH)
    if set(source) != PATENT_SOURCE_TOP_LEVEL_KEYS or source.get("schemaVersion") != 1:
        raise ValueError("patent-history.json has an unexpected top-level schema")

    for key in ("asOf", "reviewedAt", "disclaimerEn", "disclaimerFi"):
        if not isinstance(source.get(key), str) or not source[key].strip():
            raise ValueError(f"patent-history.json requires a non-empty {key}")

    patent = source.get("patent")
    if not isinstance(patent, dict):
        raise ValueError("patent-history.json patent must be an object")

    sources = source.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("patent-history.json sources must be a non-empty array")
    source_ids: set[str] = set()
    for raw in sources:
        if not isinstance(raw, dict) or not raw.get("sourceId"):
            raise ValueError("patent-history.json source entries require sourceId")
        if raw["sourceId"] in source_ids:
            raise ValueError(f"Duplicate patent source ID: {raw['sourceId']}")
        source_ids.add(raw["sourceId"])
        if not safe_url(raw.get("url")):
            raise ValueError(f"Patent source {raw['sourceId']} has an invalid URL")

    for array_key in ("timeline", "familyMembers", "proceedings", "diligenceAlerts"):
        records = source.get(array_key)
        if not isinstance(records, list) or not records:
            raise ValueError(f"patent-history.json {array_key} must be a non-empty array")
        for raw in records:
            if not isinstance(raw, dict):
                raise ValueError(f"patent-history.json {array_key} entries must be objects")
            referenced_sources = raw.get("sourceIds")
            if not isinstance(referenced_sources, list) or not referenced_sources:
                raise ValueError(f"patent-history.json {array_key} entry requires sourceIds")
            unknown = set(referenced_sources) - source_ids
            if unknown:
                raise ValueError(f"patent-history.json {array_key} references unknown sources {sorted(unknown)}")
            if array_key == "familyMembers" and not safe_url(raw.get("registerUrl")):
                raise ValueError(f"Patent family record {raw.get('memberId')} has an invalid registerUrl")

    monetisation = source.get("monetisation")
    if not isinstance(monetisation, dict):
        raise ValueError("patent-history.json monetisation must be an object")

    output = {
        "meta": {
            "schemaVersion": source["schemaVersion"],
            "asOf": source["asOf"],
            "generatedAt": source["reviewedAt"],
            "disclaimerEn": source["disclaimerEn"],
            "disclaimerFi": source["disclaimerFi"],
        },
        "patent": patent,
        "summary": {
            "timelineEventCount": len(source["timeline"]),
            "familyRecordCount": len(source["familyMembers"]),
            "officialSourceCount": sum(1 for item in sources if item.get("evidenceTier") == "official"),
            "proceedingCount": len(source["proceedings"]),
            "diligenceAlertCount": len(source["diligenceAlerts"]),
            "unresolvedProceedingCount": sum(
                1
                for item in source["proceedings"]
                if item.get("outcomeStatus")
                in {"unverified", "pending", "appeal_pending", "official_judgment_finality_unverified"}
            ),
        },
        "sources": sources,
        "timeline": source["timeline"],
        "familyMembers": source["familyMembers"],
        "proceedings": source["proceedings"],
        "diligenceAlerts": source["diligenceAlerts"],
        "monetisation": monetisation,
    }
    return _sanitize_market_value(output)


def patent_family_csv_rows(patent_history: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the deterministic flattened patent-family inventory."""
    rows: list[dict[str, Any]] = []
    for item in patent_history["familyMembers"]:
        rows.append(
            {
                "jurisdictionCode": item["jurisdictionCode"],
                "jurisdictionEn": item["jurisdictionEn"],
                "jurisdictionFi": item["jurisdictionFi"],
                "jurisdictionCategory": item["jurisdictionCategory"],
                "applicationNumber": item["applicationNumber"],
                "publicationNumber": item["publicationNumber"],
                "publicationDate": item["publicationDate"],
                "recordType": item["recordType"],
                "centralRecordStatusEn": item["centralRecordStatusEn"],
                "centralRecordStatusFi": item["centralRecordStatusFi"],
                "currentNationalStatusEn": item["currentNationalStatusEn"],
                "currentNationalStatusFi": item["currentNationalStatusFi"],
                "verificationLevel": item["verificationLevel"],
                "sourceIds": "|".join(item["sourceIds"]),
                "registerUrl": item["registerUrl"],
                "limitationEn": item["limitationEn"],
                "limitationFi": item["limitationFi"],
            }
        )
    return rows


def build_changelog() -> dict[str, Any]:
    """Build the public release log used for device-local returning-visitor state."""
    source = load_json(CHANGELOG_PATH)
    if set(source) != {"schemaVersion", "asOf", "releases"} or source.get("schemaVersion") != 1:
        raise ValueError("changelog.json has an unexpected top-level schema")
    releases = source.get("releases")
    if not isinstance(releases, list) or not releases:
        raise ValueError("changelog.json releases must be a non-empty array")
    release_ids: set[str] = set()
    previous_timestamp = ""
    for release in releases:
        expected = {"id", "version", "publishedAt", "titleEn", "titleFi", "items"}
        if not isinstance(release, dict) or set(release) != expected:
            raise ValueError("changelog.json release has an unexpected schema")
        release_id = release.get("id")
        if not isinstance(release_id, str) or not release_id or release_id in release_ids:
            raise ValueError("changelog.json release IDs must be non-empty and unique")
        release_ids.add(release_id)
        timestamp = release.get("publishedAt")
        if not isinstance(timestamp, str) or not timestamp:
            raise ValueError(f"changelog release {release_id} requires publishedAt")
        if previous_timestamp and timestamp >= previous_timestamp:
            raise ValueError("changelog.json releases must be newest first")
        previous_timestamp = timestamp
        items = release.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError(f"changelog release {release_id} requires at least one item")
        for item in items:
            if not isinstance(item, dict) or set(item) != {"category", "textEn", "textFi"}:
                raise ValueError(f"changelog release {release_id} item has an unexpected schema")
    return _sanitize_market_value(source)


def write_outputs(
    atlas: dict[str, Any],
    market_values: dict[str, Any],
    patent_history: dict[str, Any],
    changelog: dict[str, Any],
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write_text(
        OUTPUT_DIR / "atlas.json",
        json.dumps(atlas, ensure_ascii=False, indent=2) + "\n",
    )

    country_rows = []
    for country in atlas["countries"]:
        country_rows.append(
            {
                "iso2": country["iso2"],
                "name": country["name"],
                "nameFi": country["nameFi"],
                "region": country["region"],
                "bestEvidence": country["bestEvidence"],
                "coveragePercent": country["coveragePercent"],
                **country["dimensions"],
                "legacyStatus": country["legacyStatus"],
                "current": country["current"],
                "missing": country["missing"],
                "sourceLinks": "|".join(country["sourceLinks"]),
            }
        )
    country_fields = [
        "iso2",
        "name",
        "nameFi",
        "region",
        "bestEvidence",
        "coveragePercent",
        *DIMENSIONS,
        "legacyStatus",
        "current",
        "missing",
        "sourceLinks",
    ]
    atomic_write_csv(OUTPUT_DIR / "countries.csv", country_fields, country_rows)

    evidence_rows = []
    for item in atlas["evidence"]:
        evidence_rows.append(
            {
                "evidenceId": item["evidenceId"],
                "countries": "|".join(item["countries"]),
                "grade": item["grade"],
                "legacyGrade": item["legacyGrade"],
                "claimType": item["claimType"],
                "title": item["title"],
                "coverage": item["coverage"],
                "use": item["use"],
                "sourceUrl": item["sourceUrl"],
                "sourceKind": item["sourceKind"],
                "origin": item["origin"],
            }
        )
    evidence_fields = [
        "evidenceId",
        "countries",
        "grade",
        "legacyGrade",
        "claimType",
        "title",
        "coverage",
        "use",
        "sourceUrl",
        "sourceKind",
        "origin",
    ]
    atomic_write_csv(OUTPUT_DIR / "evidence.csv", evidence_fields, evidence_rows)

    atomic_write_text(
        OUTPUT_DIR / "market-values.json",
        json.dumps(market_values, ensure_ascii=False, indent=2) + "\n",
    )
    atomic_write_csv(
        OUTPUT_DIR / "market-values.csv",
        MARKET_CSV_FIELDS,
        market_values_csv_rows(market_values),
    )
    atomic_write_text(
        OUTPUT_DIR / "patent-history.json",
        json.dumps(patent_history, ensure_ascii=False, indent=2) + "\n",
    )
    atomic_write_csv(
        OUTPUT_DIR / "patent-family.csv",
        PATENT_FAMILY_CSV_FIELDS,
        patent_family_csv_rows(patent_history),
    )
    atomic_write_text(
        OUTPUT_DIR / "changelog.json",
        json.dumps(changelog, ensure_ascii=False, indent=2) + "\n",
    )


def main() -> None:
    atlas = build()
    market_values = build_market_values()
    patent_history = build_patent_history()
    changelog = build_changelog()
    write_outputs(atlas, market_values, patent_history, changelog)
    print(
        f"Built {len(atlas['countries'])} countries, "
        f"{len(atlas['evidence'])} evidence records, {len(atlas['legal'])} legal anchors, "
        f"{len(market_values['observations'])} market observations, {len(market_values['models'])} market model, "
        f"{len(patent_history['familyMembers'])} patent-family records, {len(patent_history['proceedings'])} proceedings, "
        f"and {len(changelog['releases'])} changelog release."
    )


if __name__ == "__main__":
    main()
