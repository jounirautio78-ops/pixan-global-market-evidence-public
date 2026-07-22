#!/usr/bin/env python3
"""Build the public, Finnish Pixan bank diligence package.

The builder deliberately reads only the repository's sanitised public data in
``site/data``.  It must never be pointed at a private data room.  All outputs
are deterministic OOXML files suitable for committing to GitHub Pages.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import tempfile
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "site" / "data"
DOWNLOAD_DIR = ROOT / "site" / "downloads"

INPUT_FILES = (
    DATA_DIR / "atlas.json",
    DATA_DIR / "market-values.json",
    DATA_DIR / "patent-history.json",
    DATA_DIR / "changelog.json",
)

OUTPUTS = {
    "short-deck": DOWNLOAD_DIR / "pixan-bank-deck-short-fi.pptx",
    "medium-deck": DOWNLOAD_DIR / "pixan-bank-deck-medium-fi.pptx",
    "large-deck": DOWNLOAD_DIR / "pixan-bank-deck-large-fi.pptx",
    "evidence-register": DOWNLOAD_DIR / "pixan-bank-evidence-register-fi.xlsx",
}
CSV_OUTPUT = DATA_DIR / "bank-evidence-register.csv"
MANIFEST_OUTPUT = DATA_DIR / "bank-package-manifest.json"

REGISTER_HEADERS = [
    "Väite",
    "Dia/osio",
    "Todiste",
    "Lähde",
    "Päivämäärä",
    "Laskentatapa",
    "Oletukset",
    "Luottamustaso",
    "Puutteet / tarvittava lisänäyttö",
]
ALLOWED_STATUSES = {"Vahvistettu", "Tuettu", "Oletus", "Puuttuu"}

# Restrictive boundary scan.  Generic finance terms are intentionally allowed;
# names and local path fragments from private work are not.
FORBIDDEN_PUBLIC_TERMS = (
    "/Users/",
    "jounirautio",
    "Rozella",
    "AI-Yield",
    "Peak Portfolio",
    "BlackRock",
    "Black Rock",
)

NAVY = "071A2B"
BLUE = "0D5F86"
TEAL = "00A4A6"
PALE = "EAF3F6"
PALE_TEAL = "E3F6F3"
GOLD = "F4B942"
RED = "C84B4B"
GREEN = "138A72"
INK = "182935"
MUTED = "5B6B75"
WHITE = "FFFFFF"
LINE = "CBD8DE"
LIGHT = "F6F9FA"

SLIDE_W = Inches(13.333333)
SLIDE_H = Inches(7.5)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rgb(value: str) -> RGBColor:
    return RGBColor.from_string(value)


def parse_iso_date(value: str) -> datetime:
    return datetime.strptime(value[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)


def euro_m(value: float, currency: str = "€") -> str:
    return f"{value / 1_000_000:,.1f} M{currency}".replace(",", " ")


def billion(value: float, currency: str) -> str:
    return f"{value / 1_000_000_000:,.2f} mrd {currency}".replace(",", " ")


def million_litres(value: float) -> str:
    return f"{value / 1_000_000:,.3f} milj. l".replace(",", " ")


def public_text_scan(values: Iterable[str]) -> None:
    joined = "\n".join(values)
    for term in FORBIDDEN_PUBLIC_TERMS:
        if term.casefold() in joined.casefold():
            raise ValueError(f"Forbidden private/public-boundary term found: {term}")


def source_url(source_id: str, market_sources: dict[str, Any], patent_sources: dict[str, Any]) -> str:
    source = market_sources.get(source_id) or patent_sources.get(source_id)
    if not source:
        return f"Lähdetunnus: {source_id}"
    return source.get("pageUrl") or source.get("url") or f"Lähdetunnus: {source_id}"


def build_context() -> dict[str, Any]:
    atlas = read_json(DATA_DIR / "atlas.json")
    market = read_json(DATA_DIR / "market-values.json")
    patent = read_json(DATA_DIR / "patent-history.json")
    changelog = read_json(DATA_DIR / "changelog.json")

    if not changelog.get("releases"):
        raise ValueError("changelog.json must contain at least one release")
    release = max(changelog["releases"], key=lambda item: item["publishedAt"])
    as_of = changelog["asOf"]
    if any(data.get("meta", {}).get("asOf", data.get("asOf")) != as_of for data in (atlas, market, patent)):
        raise ValueError("Public inputs do not share the changelog as-of date")

    observations = {item["observationId"]: item for item in market["observations"]}
    models = {item["modelId"]: item for item in market["models"]}
    proceedings = {item["proceedingId"]: item for item in patent["proceedings"]}
    alerts = {item["alertId"]: item for item in patent["diligenceAlerts"]}
    market_sources = {item["sourceId"]: item for item in market["sources"]}
    patent_sources = {item["sourceId"]: item for item in patent["sources"]}

    official_country_codes = sorted(
        {
            item["countryIso2"]
            for item in market["observations"]
            if item["geography"] != "Global" and item["evidenceStatus"].startswith("official")
        }
    )
    retail_donors = int(market["meta"]["modelReadiness"]["comparableFullYearMarketValueDonors"])
    grade_counts = atlas["summary"]["gradeCounts"]

    return {
        "atlas": atlas,
        "market": market,
        "patent_history": patent,
        "changelog": changelog,
        "release": release,
        "as_of": as_of,
        "observations": observations,
        "models": models,
        "proceedings": proceedings,
        "alerts": alerts,
        "market_sources": market_sources,
        "patent_sources": patent_sources,
        "official_country_codes": official_country_codes,
        "retail_donors": retail_donors,
        "grade_counts": grade_counts,
    }


def evidence_rows(ctx: dict[str, Any]) -> list[dict[str, str]]:
    p = ctx["patent_history"]["patent"]
    ps = ctx["proceedings"]
    obs = ctx["observations"]
    model = ctx["models"]["DE-2025-LIQUID-RETAIL-EQUIVALENT-RANGE"]
    market_sources = ctx["market_sources"]
    patent_sources = ctx["patent_sources"]
    as_of = ctx["as_of"]

    def sources(*ids: str) -> str:
        return " ; ".join(source_url(item, market_sources, patent_sources) for item in ids)

    def row(
        claim: str,
        section: str,
        proof: str,
        source: str,
        date: str,
        method: str,
        assumptions: str,
        status: str,
        gap: str,
    ) -> dict[str, str]:
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"Invalid evidence status: {status}")
        return dict(zip(REGISTER_HEADERS, (claim, section, proof, source, date, method, assumptions, status, gap)))

    de23 = obs["DE-2023-TAXED-LIQUID-VOLUME-L"]
    de24 = obs["DE-2024-TAXED-LIQUID-VOLUME-L"]
    de25 = obs["DE-2025-TAXED-LIQUID-VOLUME-L"]
    global_values = [
        obs["GLOBAL-2025-IMARC-COMMERCIAL-ESTIMATE"]["value"],
        obs["GLOBAL-2025-GVR-COMMERCIAL-ESTIMATE"]["value"],
        obs["GLOBAL-2025-FORTUNE-COMMERCIAL-ESTIMATE"]["value"],
    ]

    rows = [
        row(
            "Julkisen rekisteriaineiston mukaan patentin kirjattu haltija on Pixan Oy.",
            "IP-status",
            f"EPO:n päätietueessa kirjattu haltija: {p['recordedProprietor']}.",
            sources("EPO-REGISTER-MAIN"),
            ctx["patent_history"]["meta"].get("asOf", as_of),
            "Suora rekisterihavainto.",
            "Kirjaus vastaa tarkastelupäivän julkista tietuetta.",
            "Vahvistettu",
            "Täydellinen omistusketju, siirtokirjat ja rasitteet on tarkastettava erikseen.",
        ),
        row(
            f"Patenttiperheen varhaisin prioriteetti on {p['earliestPriorityNumber']} päivältä {p['earliestPriorityDate']}.",
            "IP-status",
            f"EPO-tietue: {p['familyLabel']}.",
            sources("EPO-REGISTER-MAIN", "EPO-REGISTER-FAMILY"),
            p["earliestPriorityDate"],
            "Suora rekisterihavainto.",
            "Ei oletuksia.",
            "Vahvistettu",
            "Ei olennaista puutetta prioriteettiväitteen osalta.",
        ),
        row(
            "EPO:n keskitetty väite- ja valitusmenettely päättyi patentin pysyttämiseen muutettuna.",
            "IP-status",
            ps["EPO-OPPOSITION-APPEAL"]["detailFi"],
            sources("EPO-REGISTER-EVENT", "EPO-REGISTER-DOCLIST", "EPO-B2-SPECIFICATION"),
            ps["EPO-OPPOSITION-APPEAL"]["eventDate"],
            "Virallisten EPO-tapahtumien ja B2-julkaisun ristiintarkastus.",
            "Kansallinen voimassaolo käsitellään erikseen.",
            "Vahvistettu",
            "Kunkin kansallisen oikeuden nykytila on vahvistettava kansallisesta rekisteristä.",
        ),
        row(
            "Muutetussa EP3032975B2-julkaisussa on yhdeksän vaatimusta.",
            "Patentoitu ratkaisu",
            p["claimScopeSummaryFi"],
            sources("EPO-B2-SPECIFICATION"),
            p["epCentralStatusDate"],
            "B2-julkaisun vaatimusten lukumäärä.",
            "Yleiskielinen tiivistelmä ei ole claim construction.",
            "Vahvistettu",
            "Maakohtainen asiantuntijan vaatimusvertailu tarvitaan kaupallisiin tai oikeudellisiin johtopäätöksiin.",
        ),
        row(
            "Patenttiperheessä on 22 julkaisupohjaista tietuetta.",
            "Maantieteellinen kattavuus",
            f"Julkisen patenttihistoriadatan familyRecordCount = {ctx['patent_history']['summary']['familyRecordCount']}.",
            sources("EPO-REGISTER-FAMILY"),
            as_of,
            "EPO-perhejulkaisujen lukumäärä; ei voimassa olevien oikeuksien lukumäärä.",
            "Julkaisutietue rinnastetaan vain perhereitiksi.",
            "Tuettu",
            "Vahvista omistus, maksut, käytettävät vaatimukset ja voimassaolo jokaisessa maassa.",
        ),
        row(
            "Saksan mitätöintikanne hylättiin 14.1.2026, mutta valitus on vireillä.",
            "Oikeudellinen näyttö",
            ps["DE-BPATG-8NI18-24"]["detailFi"],
            sources("DE-BPATG-8NI18-24"),
            ps["DE-BPATG-8NI18-24"]["eventDate"],
            "Virallisen ratkaisun ja valitusviitteen lukeminen.",
            "Väite rajataan Saksan osaan ja nykyiseen prosessitilaan.",
            "Vahvistettu",
            "Seuraa BGH-valituksen X ZR 21/26 etenemistä ja lopputulosta.",
        ),
        row(
            "Münchenin tuomioistuin totesi tarkasteltujen tuotteiden loukkaavan vaatimuksia 1 ja 6.",
            "Oikeudellinen näyttö",
            ps["DE-LGMUC-7O3341-24"]["detailFi"],
            sources("DE-LGMUC-7O3341-24"),
            ps["DE-LGMUC-7O3341-24"]["eventDate"],
            "Virallisen tuomion rajattu kuvaus.",
            "Ei yleistetä muihin tuotteisiin, yhtiöihin tai maihin.",
            "Vahvistettu",
            "Valitustila, lainvoimaisuus, täytäntöönpano ja maksetut korvaukset on vahvistettava.",
        ),
        row(
            "Kiinan tunnistettu asia on hakijapuolen uudelleentarkastus, ei loukkausoikeudenkäynti.",
            "Oikeudellinen näyttö",
            ps["CN-PRB-225669"]["detailFi"],
            sources("RPX-CN-225669", "CNIPA-REEXAMINATION-GUIDANCE"),
            ps["CN-PRB-225669"]["eventDate"],
            "Sekundäärisen docket-tiedon luokittelu virallisen prosessiohjeen avulla.",
            "Nimivastaavuus on vahva mutta virallista päätöstä ei saatu.",
            "Tuettu",
            "Hanki CNIPA:n virallinen päätös ja sen perustelut.",
        ),
        row(
            "Julkinen atlas sisältää muuttumattoman 195 maan tutkimusuniversumin.",
            "Markkinan rajaus",
            f"countryCount = {ctx['atlas']['summary']['countryCount']}; universe = {ctx['atlas']['summary']['universe']}.",
            "https://www.un.org/en/about-us/member-states ; https://www.un.org/en/about-us/non-member-states",
            as_of,
            "193 YK:n jäsenvaltiota + Pyhä istuin + Palestiinan valtio.",
            "Universumi on tutkimusrunko, ei todistettu markkinapeitto.",
            "Vahvistettu",
            "Ei puutetta universumin määrittelyssä; evidenssipeitto on erillinen asia.",
        ),
        row(
            "Hyväksyttyjä vuosittaisia virallisia määrähavaintoja on viidestä maasta.",
            "Markkinan koko",
            "Maat: Kanada, Saksa, Suomi, Puola ja Ruotsi.",
            "site/data/market-values.json (julkisen sivuston koneellisesti luettava lähdetiedosto)",
            as_of,
            "Uniikit maat virallisiksi luokitelluista vuosihavainnoista.",
            "Mittarit eivät ole keskenään samanlaisia.",
            "Vahvistettu",
            "Tarvitaan vertailukelpoiset laite- ja nestemyyntisarjat muista maista.",
        ),
        row(
            "Hyväksyttyjä virallisia koko vuoden kansallisia kuluttajavähittäisarvon luovuttajamarkkinoita on nolla.",
            "Markkinan koko",
            f"comparableFullYearMarketValueDonors = {ctx['retail_donors']}.",
            "site/data/market-values.json (modelReadiness)",
            as_of,
            "Yhteensopivien koko vuoden kuluttajavähittäisarvojen hyväksyntäkriteeri.",
            "Toimitus-, vero- ja määräluvut eivät ole vähittäisarvoja.",
            "Vahvistettu",
            "Hanki vähintään kolme yhteensopivaa luovuttajamarkkinaa sekä alue- ja sääntelytyyppien peitto.",
        ),
        row(
            "Kanadan vuoden 2024 valmistaja- ja maahantuojatoimitusten arvo oli 1,16075379678 mrd CAD.",
            "Markkinan koko",
            obs["CA-2024-MANUFACTURER-IMPORTER-SHIPMENTS-VALUE"]["limitationFi"],
            sources("CA-HC-VAPING-SALES-2024"),
            "2024",
            "Health Canadan neljän raportoidun tuoteryhmän toimitusarvon summa.",
            "Ei kuluttajavähittäismyyntiä.",
            "Vahvistettu",
            "Tarvitaan vähittäismarginaali-, kanava- ja varastomuutostäsmäytys.",
        ),
        row(
            "Kanadan vuoden 2024 raportoidut toimitukset sisälsivät 1 251 843 litraa nestettä.",
            "Markkinan koko",
            obs["CA-2024-MANUFACTURER-IMPORTER-SHIPMENTS-LITRES"]["limitationFi"],
            sources("CA-HC-VAPING-SALES-2024"),
            "2024",
            "Raportoitujen nestettä sisältävien tuoteryhmien summa.",
            "Fyysinen määrä, ei markkina-arvo.",
            "Vahvistettu",
            "Tarvitaan tuotemixin, keskihinnan ja vähittäiskanavan tiedot.",
        ),
        row(
            f"Saksan verotettu nestemäärä kasvoi {million_litres(de23['value'])}:sta {million_litres(de25['value'])}:aan vuosina 2023–2025.",
            "Markkinan koko",
            "2023 ja 2024 lopullisia; 2025 alustava.",
            sources("DE-DESTATIS-73411-0003"),
            "2023–2025",
            "Destatis-taulukon nettomäärät, ei ekstrapolointia.",
            "Mittaa verotettua nestettä, ei laitteita tai laitonta myyntiä.",
            "Vahvistettu",
            "Vuoden 2025 lopullinen luku ja vähittäismyyntitiedot puuttuvat.",
        ),
        row(
            "Saksan tupakankorvikkeiden valmisteverotulot olivat 404 milj. euroa vuonna 2025 (alustava).",
            "Markkinan koko",
            obs["DE-2025-SUBSTITUTES-EXCISE-RECEIPTS"]["limitationFi"],
            sources("DE-DESTATIS-73411-0003"),
            "2025",
            "Virallinen kassaperusteinen verohavainto.",
            "Verotulo ei ole myyntitulo tai vähittäismarkkina-arvo.",
            "Vahvistettu",
            "Tarvitaan lopullinen 2025 tilasto ja tuoteryhmäkohtainen veropohja.",
        ),
        row(
            "Suomessa verotettiin 11 801,062 litraa nikotiininestettä vuonna 2025.",
            "Markkinan koko",
            obs["FI-2025-NICOTINE-E-LIQUID-TAXED-VOLUME-L"]["limitationFi"],
            sources("FI-TAX-EXCISE-VVT-010-2025"),
            "2025",
            "Verohallinnon PXWeb-havainto.",
            "Verotettu nikotiinineste ei kata koko sähkötupakkamarkkinaa.",
            "Vahvistettu",
            "Laitteet, nikotiinittomat tuotteet, veroton ja laiton kauppa puuttuvat.",
        ),
        row(
            "Suomen nikotiininesteiden valmisteverotulot olivat 3 540 319 euroa vuonna 2025.",
            "Markkinan koko",
            obs["FI-2025-NICOTINE-E-LIQUID-EXCISE-RECEIPTS"]["limitationFi"],
            sources("FI-TAX-EXCISE-VVT-010-2025"),
            "2025",
            "Verohallinnon PXWeb-havainto.",
            "Verotulo ei ole kuluttajamyynti.",
            "Vahvistettu",
            "Tarvitaan vähittäismyynti- ja hintadata.",
        ),
        row(
            "Puolassa raportoitu sähkötupakkanesteiden määrä oli 805 441 litraa vuonna 2023.",
            "Markkinan koko",
            obs["PL-2023-E-LIQUID-REPORTED-VOLUME-L"]["limitationFi"],
            sources("PL-SEJM-I07255-O1"),
            "2023",
            "Parlamentaariseen vastaukseen raportoitu määrä.",
            "Mittarin kattavuus on luettava alkuperäislähteen rajauksin.",
            "Vahvistettu",
            "Tarvitaan uudempi vuosisarja ja vähittäisarvo.",
        ),
        row(
            "Puolan vuoden 2025 ilmoitettu e-nestevalmisteveron määrä oli 993,1 milj. PLN.",
            "Markkinan koko",
            obs["PL-2025-E-LIQUID-EXCISE-AMOUNT"]["limitationFi"],
            sources("PL-SEJM-I17526-O1"),
            "2025",
            "Parlamentaariseen vastaukseen raportoitu veromäärä.",
            "Veromäärä ei ole vähittäismyynti.",
            "Vahvistettu",
            "Tarvitaan toteuman lopullisuus ja veropohjan täsmäytys.",
        ),
        row(
            "Ruotsissa verotettiin 26 000 litraa nikotiininestettä vuonna 2024.",
            "Markkinan koko",
            obs["SE-2024-NICOTINE-E-LIQUID-TAXED-VOLUME-L"]["limitationFi"],
            sources("SE-GOV-BERAKNINGSKONVENTIONER-2026"),
            "2024",
            "Hallituksen laskentaperusteessa ilmoitettu määrä.",
            "Verotettu nikotiinineste ei kata koko sähkötupakkamarkkinaa.",
            "Vahvistettu",
            "Tarvitaan toteutunut vähittäismyynti ja laitedata.",
        ),
        row(
            "Kolme kaupallista vuoden 2025 globaaliarviota muodostavat 26,0–46,32 mrd USD haarukan.",
            "Markkinan koko",
            "IMARC 26,0; Grand View Research 45,7; Fortune Business Insights 46,32 mrd USD.",
            sources("IMARC-GLOBAL-2025", "GVR-GLOBAL-2025", "FORTUNE-GLOBAL-2025"),
            "2025",
            f"Minimi {min(global_values):.0f}, maksimi {max(global_values):.0f}; arvioita verrataan, ei summata.",
            "Tuoterajaukset ja menetelmät eivät välttämättä ole yhteismitallisia.",
            "Tuettu",
            "Hanki raporttien täydet metodit ja harmonisoi tuoterajaus.",
        ),
        row(
            "Saksan vuoden 2025 verotetun nesteen vähittäismyyntivastaavuuden mallihaitari on 667,92–1 654,62 milj. euroa.",
            "Taloudellinen malli",
            model["limitationFi"],
            sources("DE-DESTATIS-73411-0003", "INTASTE-GERMANFLAVOURS-2026", "INTASTE-SAMURAI-2026", "INTASTE-REVOLTAGE-2026"),
            "2025 määrä / 2026 hinnat",
            model["formula"],
            "Kolme yksittäistä verkkokauppahintaa; vuosiero; vain verotettu neste.",
            "Oletus",
            "Tarvitaan edustava hintakori, tuotemix, kanavamarginaalit ja saman vuoden hinnat.",
        ),
        row(
            "Atlas ei ole vielä lainanantajavalmis markkina-arvio.",
            "Rahoitusteesi",
            ctx["atlas"]["readiness"]["status"] + ": " + " ".join(ctx["atlas"]["readiness"]["blockers"]),
            "site/data/atlas.json (readiness)",
            as_of,
            "Julkisen datasetin oma readiness-luokitus.",
            "Markkinadata ja IP-arvo pidetään erillään.",
            "Vahvistettu",
            "Täytä blocker-lista ennen vakuusarvo- tai yritysarvopäätelmää.",
        ),
        row(
            "Julkinen aineisto ei sisällä riippumatonta IVS-arvonmääritystä.",
            "Taloudellinen malli",
            "Readiness-blocker ilmoittaa riippumattoman arvonmäärityksen puuttuvan.",
            "site/data/atlas.json (readiness.blockers)",
            as_of,
            "Aineiston puute.",
            "Ei oletuksia.",
            "Puuttuu",
            "Tilaa riippumaton IP- ja tarvittaessa yritysarvonmääritys skenaarioineen.",
        ),
        row(
            "Julkinen aineisto ei osoita toteutunutta lisenssi- tai vahingonkorvauskassavirtaa.",
            "Kaupallistamismalli",
            "Readiness-blocker ilmoittaa realisoituneen kassavirran puuttuvan.",
            "site/data/atlas.json (readiness.blockers)",
            as_of,
            "Aineiston puute.",
            "Ei oletuksia.",
            "Puuttuu",
            "Lisää allekirjoitetut sopimukset, laskut, maksutositteet ja saamisten täsmäytys.",
        ),
        row(
            "Julkinen aineisto ei vahvista testituloksia tai riippumatonta teknistä validointia.",
            "Tekninen erottautuminen",
            "Patenttiselitys kuvaa ratkaisun; erillistä testirekisteriä ei ole julkisessa datassa.",
            "site/data/patent-history.json",
            as_of,
            "Aineiston puute suhteessa tekniseen suorituskykyväitteeseen.",
            "Patenttijulkaisu ei ole tuotetestiraportti.",
            "Puuttuu",
            "Hanki testiprotokolla, riippumaton laboratorio, tulokset ja raakadata.",
        ),
        row(
            "Julkinen aineisto ei vahvista piloteja tai nimettyä asiakasnäyttöä.",
            "Validointi",
            "Julkisessa evidenssirekisterissä ei ole pilotti- tai asiakasvalidointia.",
            "site/data/evidence.csv",
            as_of,
            "Aineiston puute.",
            "Ei päätellä asiakkaiden olemassaoloa tai puuttumista yhtiötasolla.",
            "Puuttuu",
            "Lisää allekirjoitetut pilotit, toimitusnäyttö, asiakasreferenssit ja käyttödata.",
        ),
        row(
            "Julkinen aineisto ei vahvista nykyistä maakohtaista omistusta, vuosimaksuja ja rasitteettomuutta koko perheessä.",
            "IP-status",
            "Perhejulkaisut eivät yksin osoita kansallista post-grant-tilaa.",
            sources("EPO-REGISTER-FAMILY", "EPO-REGISTER-LEGAL", "EPO-NATIONAL-VALIDATION"),
            as_of,
            "Diligence-rajaus.",
            "Neljä rekisteritarkistusta ei kata koko perhettä.",
            "Puuttuu",
            "Laadi asiamiehen allekirjoittama maamatriisi ja liitä tuoreet rekisteriotteet sekä maksukuitit.",
        ),
        row(
            "Julkinen aineisto ei sisällä maakohtaisia tuote–vaatimusvertailuja.",
            "Tekninen erottautuminen",
            "Patenttihistorian guardrail edellyttää counsel-reviewed claim chartia.",
            sources("EPO-B2-SPECIFICATION", "DE-LGMUC-7O3341-24"),
            as_of,
            "Vaatimuspiirteiden tuotekohtainen kartoitus puuttuu.",
            "Samankaltaisuus ei ole loukkaus.",
            "Puuttuu",
            "Hanki tuotteet, säilytä hallussapitoketju, tee teardown ja asiamiehen tarkastama claim chart.",
        ),
        row(
            "Markkinan kokonaisarvo ei ole automaattisesti rojaltipohja.",
            "Taloudellinen malli",
            "Patenttihistorian kaupallistamisrajaus erottaa markkinan, kohdistettavan myynnin ja kassavirran.",
            sources("WIPO-IP-VALUATION"),
            as_of,
            "Arvonmäärityksen perusrajaus.",
            "Rojaltipohja vaatii patentin maantieteellisen, ajallisen ja tuotekohtaisen osuvuuden.",
            "Vahvistettu",
            "Tarvitaan addressable/in-scope/claim-mapped sales -silta.",
        ),
        row(
            "Patenttiarvo, yritysarvo, osakearvo ja vakuusarvo ovat eri mittareita.",
            "Rahoitusteesi",
            "WIPO:n IP-arvonmääritys- ja rahoituskehys sekä aineiston oma guardrail.",
            sources("WIPO-IP-VALUATION", "WIPO-IP-FINANCE"),
            as_of,
            "Arvokäsitteiden erottelu.",
            "Ei oletuksia.",
            "Vahvistettu",
            "Rahoitusrakenne ja vakuusarvo vaativat erillisen oikeudellisen ja taloudellisen analyysin.",
        ),
        row(
            "Asiantuntijavetoinen rajattu lisensointi- tai sovintopilotti on mahdollinen kaupallistamishypoteesi.",
            "Kaupallistamismalli",
            "Patenttihistorian vaiheistus suosittelee kovia portteja, claim chartia ja auditoitavaa yhteydenottoa.",
            sources("WIPO-ASSIGNMENT-LICENSING", "WIPO-DISPUTE-RESOLUTION", "EPO-IPSCORE"),
            as_of,
            "Hypoteesi, ei toteutunut kaupallinen näyttö.",
            "Kohdemaat ja vastapuolet valitaan vasta oikeus- ja evidenssiporttien jälkeen.",
            "Oletus",
            "Hyväksytä pilottimalli johdolla ja patenttiasiantuntijalla; dokumentoi kustannus, vasteet ja termit.",
        ),
        row(
            "Patenttivakuudellinen rahoitus on arvioitava vain vahvistettujen oikeuksien ja kassavirtojen pohjalta.",
            "Rahoitusteesi",
            "WIPO IP Finance ja patenttihistorian vaihe 5.",
            sources("WIPO-IP-FINANCE", "WIPO-IP-VALUATION"),
            as_of,
            "Rahoitusperiaate.",
            "Ei näyttöä olemassa olevasta vakuusarvosta.",
            "Tuettu",
            "Tarvitaan riippumaton arvonmääritys, oikeuksien due diligence, toteutuneet tai sopimuspohjaiset kassavirrat ja downside-analyysi.",
        ),
        row(
            "Australian oikeuden seuraava uusiminen on vahvistettava välittömästi.",
            "Riskit",
            ctx["alerts"]["AU-RENEWAL-CONFIRM-2026"]["detailFi"],
            sources("IPAU-PATENT-API"),
            ctx["alerts"]["AU-RENEWAL-CONFIRM-2026"]["targetDate"],
            "Virallisen API-tiedon diligence-hälytys.",
            "API:n in-force-through-päivä ei ole tässä lakisääteinen eräpäiväväite.",
            "Vahvistettu",
            ctx["alerts"]["AU-RENEWAL-CONFIRM-2026"]["actionFi"],
        ),
        row(
            "Suomen 14. vuosimaksun eräpäiväksi on rekisteröity 31.8.2026.",
            "Riskit",
            ctx["alerts"]["FI-YEAR14-FEE-2026"]["detailFi"],
            sources("PRH-FI-REGISTER"),
            ctx["alerts"]["FI-YEAR14-FEE-2026"]["targetDate"],
            "PRH:n rekisterihavainto.",
            "Tavoite on maksaa normaalina eräpäivänä.",
            "Vahvistettu",
            ctx["alerts"]["FI-YEAR14-FEE-2026"]["actionFi"],
        ),
        row(
            "Yhdysvaltain 7,5 vuoden ylläpitomaksun tila on vahvistettava.",
            "Riskit",
            ctx["alerts"]["US-MAINTENANCE-2026"]["detailFi"],
            sources("USPTO-MAINTENANCE", "USPTO-PATENT-CENTER"),
            ctx["alerts"]["US-MAINTENANCE-2026"]["targetDate"],
            "Virallisen maksuikkunan tarkistus.",
            "Julkaisu ei väitä, että maksu on tai ei ole suoritettu.",
            "Vahvistettu",
            ctx["alerts"]["US-MAINTENANCE-2026"]["actionFi"],
        ),
        row(
            "Julkinen aineisto ei sisällä auditoituja historiallisia tilinpäätöksiä tai kassavirtaennustetta.",
            "Taloudellinen malli",
            "Markkina- ja patenttiaineisto ei ole yhtiön talousaineisto.",
            "Julkisen paketin rajaus",
            as_of,
            "Aineiston puute.",
            "Yhtiön taloudellisesta tilanteesta ei tehdä päätelmää.",
            "Puuttuu",
            "Lisää 3–5 vuoden tilinpäätökset, tuore pääkirja, budjetti, kassavirta, velat ja verovelkatodistus.",
        ),
        row(
            "Julkinen aineisto ei yksilöi rahoitustarvetta, käyttötarkoitusta tai takaisinmaksulähdettä.",
            "Rahoitusteesi",
            "Rahoitusparametreja ei ole markkina- tai patenttidatassa.",
            "Julkisen paketin rajaus",
            as_of,
            "Aineiston puute.",
            "Ei oleteta lainamäärää, maturiteettia tai vakuusrakennetta.",
            "Puuttuu",
            "Määritä lainamäärä, käyttötarkoitus, maturiteetti, lyhennysprofiili, takaisinmaksu ja kovenantit.",
        ),
        row(
            "Julkinen aineisto ei osoita osakekantaa, cap tablea tai osakkeiden rasitteita.",
            "Rahoitusteesi",
            "Julkinen paketti on rajattu markkina- ja patenttievidenssiin.",
            "Julkisen paketin rajaus",
            as_of,
            "Aineiston puute.",
            "Ei oleteta omistusosuuksia tai vakuuskelpoisuutta.",
            "Puuttuu",
            "Toimita varmennettu osakasluettelo, yhtiöjärjestys, päätökset, panttaus- ja rasiteselvitys suljettuun datahuoneeseen.",
        ),
        row(
            "Julkinen aineisto ei sisällä vertailukelpoista kilpailija- ja vaihtoehtoanalyysiä.",
            "Kilpailu",
            "Patenttiselitys ja oikeustapaukset eivät yksin muodosta markkinakilpailukarttaa.",
            "site/data/patent-history.json",
            as_of,
            "Aineiston puute.",
            "Kilpailu on erotettava patenttien päällekkäisyydestä ja ei-patentoiduista vaihtoehdoista.",
            "Puuttuu",
            "Laadi tuotteet, valmistajat, vaihtoehtoiset teknologiat, patenttiperheet, hinnat ja claim-map-status kattava vertailu.",
        ),
        row(
            "Asiakassegmentit voidaan alustavasti jäsentää valmistajiin, teknologiatoimittajiin ja IP-rahoittajiin.",
            "Asiakkaat",
            "Patenttihistorian kaupallistamisreitit sisältävät lisensoinnin, luovutuksen ja IP-rahoituksen.",
            sources("WIPO-ASSIGNMENT-LICENSING", "WIPO-IP-FINANCE"),
            as_of,
            "Segmentointihypoteesi kaupallistamisreiteistä.",
            "Ei todennettua ostoaikomusta tai asiakaskantaa.",
            "Oletus",
            "Validoi 10–15 strukturoitua ostaja- ja rahoittajahaastattelua sekä dokumentoi päätöskriteerit.",
        ),
        row(
            "Saksan ratkaisut voivat toimia evidenssiankkurina, mutta eivät maailmanlaajuisena loukkausratkaisuna.",
            "Rahoitusteesi",
            "Ratkaisut ovat kansallisia, tuote-, osapuoli- ja ajanjaksokohtaisia.",
            sources("DE-BPATG-8NI18-24", "DE-LGMUC-7O3341-24"),
            as_of,
            "Oikeudellisen vaikutuksen alueellinen rajaus.",
            "Muiden maiden tulokset riippuvat paikallisista oikeuksista ja tuotteista.",
            "Vahvistettu",
            "Laadi maakohtaiset oikeus- ja claim chart -paketit ennen yhteydenottoja.",
        ),
        row(
            "Aineiston A-luokan maita on viisi, mutta 158 maata on D-luokassa.",
            "Markkinan koko",
            f"Luokat: A {ctx['grade_counts']['A']}, B {ctx['grade_counts']['B']}, C {ctx['grade_counts']['C']}, D {ctx['grade_counts']['D']}.",
            "site/data/atlas.json (summary.gradeCounts)",
            as_of,
            "Maakohtaisten evidenssiluokkien laskenta.",
            "Luokka mittaa evidenssikypsyyttä, ei markkinan houkuttelevuutta.",
            "Vahvistettu",
            "Priorisoi D-maiden tietopyynnöt talouskoon, patenttistatuksen ja sääntelyn mukaan.",
        ),
        row(
            "Maailmanlaajuista atlasestimaattia ei ole hyväksytty julkaistavaksi.",
            "Markkinan koko",
            "Nolla vertailukelpoista vähittäisarvoluovuttajaa alittaa kolmen luovuttajan minimikynnyksen.",
            "site/data/market-values.json (modelReadiness)",
            as_of,
            "Hard gate: vähintään kolme yhteensopivaa luovuttajaa + alueellinen validointi.",
            "Kaupallisia globaaliarvioita käytetään vain sanity check -haarukkana.",
            "Vahvistettu",
            "Älä esitä yhtä maailmanlukua ennen metodin porttien täyttymistä.",
        ),
        row(
            "Korkean luottamuksen rahoituspaketti vaatii suljetun datahuoneen julkisen paketin rinnalle.",
            "Seuraavat vaiheet",
            "Julkinen paketti osoittaa lähteet ja puutteet mutta ei sisällä luottamuksellista talous-, sopimus- tai omistusaineistoa.",
            "Julkisen paketin rajaus",
            as_of,
            "Diligence-arkkitehtuurin suositus.",
            "Pääsy rajataan ja lokitetaan.",
            "Tuettu",
            "Perusta indeksoitu datahuone: Corporate, IP, Legal, Commercial, Finance, Valuation, Security.",
        ),
    ]
    public_text_scan(value for item in rows for value in item.values())
    return rows


def add_text(
    slide,
    text: str,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    size: float = 18,
    color: str = INK,
    bold: bool = False,
    font: str = "Aptos",
    align: PP_ALIGN = PP_ALIGN.LEFT,
    valign: MSO_ANCHOR = MSO_ANCHOR.TOP,
    margin: float = 0.04,
) -> Any:
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(margin)
    frame.margin_right = Inches(margin)
    frame.margin_top = Inches(margin)
    frame.margin_bottom = Inches(margin)
    frame.vertical_anchor = valign
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = rgb(color)
    return box


def add_rect(slide, x: float, y: float, w: float, h: float, fill: str, line: str | None = None, radius: bool = False):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(fill)
    shape.line.color.rgb = rgb(line or fill)
    if radius:
        shape.adjustments[0] = 0.08
    return shape


def add_footer(slide, ctx: dict[str, Any], page: int, source_ids: str = "") -> None:
    add_rect(slide, 0.38, 7.13, 12.57, 0.015, LINE)
    footer = f"Julkinen riippumaton evidenssikooste · {ctx['release']['version']} · {ctx['as_of']}"
    if source_ids:
        footer += f" · Lähteet: {source_ids}"
    add_text(slide, footer, 0.42, 7.17, 11.85, 0.19, size=8.5, color=MUTED)
    add_text(slide, str(page), 12.45, 7.15, 0.45, 0.22, size=9, color=MUTED, align=PP_ALIGN.RIGHT)


def add_slide_title(slide, title: str, section: str, ctx: dict[str, Any], page: int, sources: str = "") -> None:
    add_text(slide, section.upper(), 0.55, 0.32, 3.8, 0.28, size=10, color=TEAL, bold=True)
    add_text(slide, title, 0.55, 0.68, 12.15, 0.6, size=34, color=NAVY, bold=True)
    add_rect(slide, 0.55, 1.34, 1.05, 0.055, TEAL)
    add_footer(slide, ctx, page, sources)


def add_bullets(slide, bullets: list[str], x: float, y: float, w: float, h: float, size: float = 18, color: str = INK) -> None:
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.03)
    frame.margin_right = Inches(0.03)
    frame.margin_top = Inches(0.02)
    frame.margin_bottom = Inches(0.02)
    for idx, text in enumerate(bullets):
        para = frame.paragraphs[0] if idx == 0 else frame.add_paragraph()
        para.text = text
        para.level = 0
        para.font.name = "Aptos"
        para.font.size = Pt(size)
        para.font.color.rgb = rgb(color)
        para.space_after = Pt(12)
        para.line_spacing = 1.05
        para.text = "•  " + para.text


def add_metric(slide, value: str, label: str, x: float, y: float, w: float, color: str = TEAL) -> None:
    add_rect(slide, x, y, w, 1.5, LIGHT, LINE, True)
    add_text(slide, value, x + 0.18, y + 0.18, w - 0.36, 0.58, size=27, color=color, bold=True)
    add_text(slide, label, x + 0.18, y + 0.82, w - 0.36, 0.48, size=14, color=MUTED)


def add_callout(slide, title: str, body: str, x: float, y: float, w: float, h: float, fill: str = PALE_TEAL) -> None:
    add_rect(slide, x, y, w, h, fill, fill, True)
    add_text(slide, title, x + 0.18, y + 0.16, w - 0.36, 0.3, size=17, color=NAVY, bold=True)
    add_text(slide, body, x + 0.18, y + 0.55, w - 0.36, h - 0.68, size=15, color=INK)


def add_table(slide, headers: list[str], rows: list[list[str]], x: float, y: float, w: float, h: float, widths: list[float] | None = None, font_size: float = 13.5) -> None:
    table_shape = slide.shapes.add_table(len(rows) + 1, len(headers), Inches(x), Inches(y), Inches(w), Inches(h))
    table = table_shape.table
    if widths:
        total = sum(widths)
        for idx, value in enumerate(widths):
            table.columns[idx].width = Inches(w * value / total)
    header_height = min(0.48, h / (len(rows) + 1) * 1.2)
    table.rows[0].height = Inches(header_height)
    body_height = (h - header_height) / max(1, len(rows))
    for row_index in range(1, len(table.rows)):
        table.rows[row_index].height = Inches(body_height)
    for col, value in enumerate(headers):
        cell = table.cell(0, col)
        cell.text = value
        cell.fill.solid()
        cell.fill.fore_color.rgb = rgb(NAVY)
        cell.margin_left = Inches(0.08)
        cell.margin_right = Inches(0.08)
        for para in cell.text_frame.paragraphs:
            para.font.name = "Aptos"
            para.font.size = Pt(font_size)
            para.font.bold = True
            para.font.color.rgb = rgb(WHITE)
    for ridx, row_values in enumerate(rows, start=1):
        for cidx, value in enumerate(row_values):
            cell = table.cell(ridx, cidx)
            cell.text = str(value)
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(WHITE if ridx % 2 else LIGHT)
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.04)
            cell.margin_bottom = Inches(0.04)
            for para in cell.text_frame.paragraphs:
                para.font.name = "Aptos"
                para.font.size = Pt(font_size)
                para.font.color.rgb = rgb(INK)
                para.alignment = PP_ALIGN.LEFT


def new_presentation(ctx: dict[str, Any], title: str) -> Presentation:
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    prs.core_properties.title = title
    prs.core_properties.subject = "Julkinen pankki- ja rahoitusarvioinnin evidenssipaketti"
    prs.core_properties.author = "Pixan Global Market Evidence Atlas"
    prs.core_properties.keywords = "Pixan, patentti, markkinaevidenssi, due diligence"
    stamp = parse_iso_date(ctx["as_of"])
    prs.core_properties.created = stamp
    prs.core_properties.modified = stamp
    return prs


def cover_slide(prs: Presentation, ctx: dict[str, Any], subtitle: str, slide_count: int) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = rgb(NAVY)
    add_rect(slide, 0.58, 0.62, 1.2, 0.07, TEAL)
    add_text(slide, "PIXAN · JULKINEN EVIDENSSIPAKETTI", 0.58, 1.0, 7.4, 0.35, size=13, color=TEAL, bold=True)
    # Keep the cover title and subtitle in distinct vertical bands.  The title
    # can wrap to three lines in LibreOffice/PowerPoint depending on font
    # metrics, so reserve enough height instead of relying on a two-line fit.
    add_text(slide, "Patentista pankkikelpoiseksi\ntodistelupaketiksi", 0.58, 1.52, 8.05, 2.25, size=40, color=WHITE, bold=True)
    add_text(slide, subtitle, 0.62, 4.05, 7.7, 0.48, size=18, color="C6D8E2")
    add_rect(slide, 9.05, 0.0, 4.28, 7.5, BLUE)
    add_text(slide, "Aineiston tila", 9.55, 1.25, 3.2, 0.4, size=19, color=WHITE, bold=True)
    add_text(slide, ctx["release"]["version"], 9.55, 1.86, 3.15, 0.55, size=29, color=GOLD, bold=True)
    add_text(slide, f"Päivitetty {ctx['as_of']}\n{slide_count} diaa · suomeksi", 9.55, 2.58, 3.05, 0.8, size=17, color=WHITE)
    add_text(slide, "Lähtökohta", 9.55, 4.18, 3.0, 0.35, size=13, color="B8DFE2", bold=True)
    add_text(slide, "Vahvistettu näyttö erotetaan tuetusta tiedosta, oletuksista ja puuttuvasta näytöstä.", 9.55, 4.65, 3.05, 1.2, size=18, color=WHITE)
    add_text(slide, "Ei Pixan Oy:n virallinen kanta · ei arvo-, sijoitus-, laina- tai oikeudellinen lausunto", 0.62, 6.84, 7.7, 0.34, size=10, color="9DB3C0")


def slide_claim(prs: Presentation, ctx: dict[str, Any], page: int, title: str, section: str, claim: str, bullets: list[str], side_title: str, side_body: str, sources: str) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_title(slide, title, section, ctx, page, sources)
    # Finnish compound words and evidence-qualified claims vary materially in
    # length.  Reserve claim height before placing bullets so the two text
    # regions can never collide after Office/LibreOffice line wrapping.
    if len(claim) <= 115:
        claim_size, claim_height = 23, 1.12
    elif len(claim) <= 175:
        claim_size, claim_height = 20, 1.42
    else:
        claim_size, claim_height = 17.5, 1.78
    bullet_y = 1.78 + claim_height + 0.18
    add_text(slide, claim, 0.6, 1.7, 7.4, claim_height, size=claim_size, color=BLUE, bold=True)
    add_bullets(slide, bullets, 0.64, bullet_y, 7.25, 6.45 - bullet_y, size=16.5)
    add_callout(slide, side_title, side_body, 8.45, 1.7, 4.25, 4.75, PALE_TEAL)


def slide_metrics(prs: Presentation, ctx: dict[str, Any], page: int, title: str, section: str, metrics: list[tuple[str, str]], takeaway: str, note: str, sources: str) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_title(slide, title, section, ctx, page, sources)
    count = len(metrics)
    card_w = (12.15 - 0.28 * (count - 1)) / count
    for idx, (value, label) in enumerate(metrics):
        add_metric(slide, value, label, 0.58 + idx * (card_w + 0.28), 1.88, card_w, [TEAL, BLUE, GOLD, GREEN][idx % 4])
    add_text(slide, takeaway, 0.62, 3.86, 11.95, 0.86, size=25, color=NAVY, bold=True)
    add_callout(slide, "Tulkinta", note, 0.62, 4.96, 11.95, 1.25, PALE)


def slide_table(prs: Presentation, ctx: dict[str, Any], page: int, title: str, section: str, headers: list[str], rows: list[list[str]], takeaway: str, sources: str, widths: list[float] | None = None) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_title(slide, title, section, ctx, page, sources)
    add_table(slide, headers, rows, 0.58, 1.68, 12.15, 4.35, widths, font_size=13.2)
    add_text(slide, takeaway, 0.66, 6.19, 11.9, 0.55, size=17, color=BLUE, bold=True)


def slide_process(prs: Presentation, ctx: dict[str, Any], page: int, title: str, section: str, steps: list[tuple[str, str]], takeaway: str, sources: str) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_title(slide, title, section, ctx, page, sources)
    top = 1.78
    row_h = 1.05
    for idx, (head, body) in enumerate(steps):
        y = top + idx * 1.18
        add_rect(slide, 0.72, y, 0.62, 0.62, TEAL if idx < 3 else BLUE, None, True)
        add_text(slide, str(idx + 1), 0.72, y + 0.08, 0.62, 0.36, size=19, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, head, 1.62, y - 0.02, 3.0, 0.34, size=18, color=NAVY, bold=True)
        add_text(slide, body, 4.5, y - 0.02, 7.75, row_h, size=16, color=INK)
    add_text(slide, takeaway, 0.72, 6.44, 11.65, 0.44, size=16, color=BLUE, bold=True)


def closing_slide(prs: Presentation, ctx: dict[str, Any], page: int, title: str, bullets: list[str], sources: str = "") -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = rgb(NAVY)
    add_text(slide, "PÄÄTÖSKEHYS", 0.62, 0.55, 3.0, 0.3, size=12, color=TEAL, bold=True)
    add_text(slide, title, 0.62, 1.1, 11.9, 1.0, size=39, color=WHITE, bold=True)
    add_bullets(slide, bullets, 0.68, 2.5, 10.95, 3.55, size=19, color=WHITE)
    add_text(slide, f"Versio {ctx['release']['version']} · {ctx['as_of']} · {page} / {len(prs.slides)}", 0.65, 6.86, 11.2, 0.25, size=10, color="9DB3C0")


def common_values(ctx: dict[str, Any]) -> dict[str, Any]:
    obs = ctx["observations"]
    model = ctx["models"]["DE-2025-LIQUID-RETAIL-EQUIVALENT-RANGE"]
    p = ctx["patent_history"]
    return {
        "ca_value": billion(obs["CA-2024-MANUFACTURER-IMPORTER-SHIPMENTS-VALUE"]["value"], "CAD"),
        "ca_litres": million_litres(obs["CA-2024-MANUFACTURER-IMPORTER-SHIPMENTS-LITRES"]["value"]),
        "de23": million_litres(obs["DE-2023-TAXED-LIQUID-VOLUME-L"]["value"]),
        "de24": million_litres(obs["DE-2024-TAXED-LIQUID-VOLUME-L"]["value"]),
        "de25": million_litres(obs["DE-2025-TAXED-LIQUID-VOLUME-L"]["value"]),
        "de_model": f"{euro_m(model['low'])}–{euro_m(model['high'])}",
        "de_model_central": euro_m(model["central"]),
        "global_range": "$26,0–46,32 mrd",
        "family_count": p["summary"]["familyRecordCount"],
        "official_sources": p["summary"]["officialSourceCount"],
        "proceedings": p["summary"]["proceedingCount"],
    }


def build_short_deck(ctx: dict[str, Any], path: Path) -> None:
    v = common_values(ctx)
    prs = new_presentation(ctx, "Pixan · suppea julkinen pankkidekki")
    cover_slide(prs, ctx, "Suppea päätöksenteon tiivistelmä", 6)
    slide_claim(
        prs, ctx, 2, "Rahoitusteesi perustuu näyttöön — ei markkinahypeen", "Rahoitusteesi",
        "Patentilla on dokumentoitu tekninen ydin ja merkittävää virallista oikeusnäyttöä, mutta vakuusarvo ei ole vielä todistettu.",
        ["EPO pysytti patentin muutettuna; B2-julkaisu sisältää 9 vaatimusta.", "Saksassa on virallinen mitätöinti- ja loukkausratkaisu, mutta lopullisuus- ja aluerajat säilyvät.", "Rahoituskelpoisuus syntyy, kun oikeudet, claim chartit, kassavirta ja riippumaton arvonmääritys sidotaan yhteen."],
        "Pankin lukutapa", "Nykyinen aineisto tukee jatkodiligenceä. Se ei vielä yksin tue tiettyä lainamäärää, osakearvoa tai patentin vakuusarvoa.",
        "EPO, Saksan viralliset tuomiot, WIPO",
    )
    slide_metrics(
        prs, ctx, 3, "Patenttihistoria antaa vahvan mutta rajatun ankkurin", "Patentti ja IP",
        [("9", "vaatimusta EP3032975B2:ssa"), (str(v["family_count"]), "perhejulkaisutietuetta"), ("2", "virallista Saksan ratkaisua")],
        "Todistettu oikeusnäyttö on arvokasta vain maakohtaisen voimassaolo- ja tuotekytkennän kanssa.",
        "Kirjattu haltija, prioriteetti ja EPO:n keskitetty lopputulos ovat vahvistettavissa. Koko perheen nykyinen kansallinen tila, rasitteet ja täytäntöönpano vaativat lisänäyttöä.",
        "EPO Register; EP3032975B2; DE 8 Ni 18/24; DE 7 O 3341/24",
    )
    slide_metrics(
        prs, ctx, 4, "Markkina-aineisto on läpinäkyvä mutta ei vielä valmis globaaliksi arvoksi", "Markkina",
        [("195", "maan tutkimusuniversumi"), ("5", "maata virallisilla vuosihavainnoilla"), ("0", "hyväksyttyä retail-arvon luovuttajaa")],
        "Kaupallinen $26,0–46,32 mrd haarukka on sanity check — ei atlaksen oma maailmanestimaatti.",
        f"Kanada: {v['ca_value']} toimitusarvo. Saksa: {v['de25']} verotettua nestettä vuonna 2025 (alustava). Mittareita ei summata keskenään.",
        "Health Canada; Destatis; FI/PL/SE viralliset lähteet",
    )
    slide_table(
        prs, ctx, 5, "Puutteet ovat rajattavissa konkreettiseksi työohjelmaksi", "Riskit ja näyttö",
        ["Puutuva näyttö", "Miksi ratkaiseva", "Seuraava todiste"],
        [["Koko perheen kansallinen tila", "Määrittää toteuttamiskelpoiset oikeudet", "Asiamiehen allekirjoittama maamatriisi"], ["Tuote–vaatimusvertailut", "Rajaa relevantin myynnin", "Näytteet, teardown, claim chart"], ["Kassavirta ja sopimukset", "Määrittää takaisinmaksun", "Sopimukset, laskut, maksut"], ["Riippumaton arvonmääritys", "Määrittää skenaariot ja downside-riskin", "IVS-yhteensopiva arvio"]],
        "Pankkikelpoisuus paranee eniten, kun nämä neljä aukkoa suljetaan ennen arvokeskustelua.", "Evidence Register; WIPO IP valuation", [2.7, 3.7, 4.8],
    )
    closing_slide(
        prs, ctx, 6, "Ehdollinen eteneminen: 90 päivän diligence ennen rahoituspäätöstä",
        ["0–30 päivää: omistus-, rasite-, maksu- ja oikeusmatriisi.", "31–60 päivää: priorisoidut claim chartit, markkinamyynnin rajaus ja vastapuolidata.", "61–90 päivää: riippumaton arvonmääritys, kassavirtaskenaariot ja rahoitusehdot.", "Päätösportti: vain vahvistettuun oikeuteen ja takaisinmaksulähteeseen perustuva rakenne."],
        "Evidence Register; WIPO IP Finance",
    )
    if len(prs.slides) != 6:
        raise AssertionError("Short deck must have 6 slides")
    save_presentation(prs, path)


def build_medium_deck(ctx: dict[str, Any], path: Path) -> None:
    v = common_values(ctx)
    p = ctx["patent_history"]["patent"]
    prs = new_presentation(ctx, "Pixan · keskikokoinen julkinen pankkidekki")
    cover_slide(prs, ctx, "12 dian rahoitus- ja teknologia-arvio", 12)
    add_text(prs.slides[0], "1 · Rahoitusteesi", 0.62, 4.72, 6.0, 0.35, size=15, color=TEAL, bold=True)
    # Slide 1 is the cover and carries the financing thesis.
    slide_claim(prs, ctx, 2, "Ongelma on yhtä paljon evidenssissä kuin teknologiassa", "2 · Ongelma",
                "Laaja markkinapuhe ei muutu pankkikelpoiseksi vakuudeksi ilman maakohtaista oikeus-, tuote-, myynti- ja kassavirtaketjua.",
                ["Markkinamittarit ovat hajanaisia: toimitukset, verot, litrat ja kaupalliset arviot eivät ole sama asia.", "Perhejulkaisu ei todista nykyistä voimassaoloa tai rasitteettomuutta.", "Oikeustuomio ei yksin todista maksettua korvausta tai globaalia rojaltipohjaa."],
                "Pankin ydinkysymys", "Mikä todennettu omaisuus ja kassavirta kattaa lainan myös downside-tapauksessa?", "Atlas readiness; WIPO" )
    slide_claim(prs, ctx, 3, "Ratkaisu ohjaa höyrystimen tehoa mitatun resistanssin perusteella", "3 · Patentoitu ratkaisu",
                p["inventionSummaryFi"],
                ["Ohjaus perustuu tallennettuihin resistanssi–tehoarvoihin.", "Tehosuhde kuvataan ei-suoraan-verrannolliseksi.", "Käyttäjäsäätö tapahtuu nollasta poikkeavan minimin ja tallennetun maksimin välillä."],
                "Rajaus", "Tämä on julkaistun patenttiselityksen yleiskielinen tiivistelmä. Vain kyseisen maan operative claims ja tuotekohtainen claim chart ratkaisevat.", "EP3032975B2" )
    slide_metrics(prs, ctx, 4, "IP-ydin on dokumentoitu; maakohtainen käyttökelpoisuus on vielä täsmäytettävä", "4 · Patentti ja IP-status",
                  [("2013", "varhaisin prioriteettivuosi"), ("9", "B2-vaatimusta"), (str(v["family_count"]), "perhejulkaisutietuetta")],
                  "EPO pysytti patentin muutettuna; B2 julkaistiin 24.4.2024.",
                  "Julkinen rekisteri nimeää Pixan Oy:n haltijaksi. Koko perheen nykyistä kansallista voimassaoloa, maksuja ja rasitteita ei ole vielä varmennettu.", "EPO Register; EP3032975B2" )
    slide_claim(prs, ctx, 5, "Tekninen erottautuminen on vaatimuksissa — ei tuotteen ulkonäössä", "5 · Tekninen erottautuminen",
                "Rahoitusarvioinnin tulee jäljittää jokainen olennainen vaatimuspiirre tuotteeseen ja maahan.",
                ["Patenttiselitys antaa teknisen hypoteesin ja dokumentoidun suojatekstin.", "Saksan ratkaisu tukee tiettyjen tuotteiden ja vaatimusten 1 sekä 6 kytkentää.", "Riippumattomat testit, teardown-dossierit ja muiden maiden claim chartit puuttuvat julkisesta aineistosta."],
                "Todistusketju", "Näyte → hallussapitoketju → teardown → mittausdata → claim chart → asiamiehen tarkastus → relevantti myynti.", "EP3032975B2; DE 7 O 3341/24" )
    slide_metrics(prs, ctx, 6, "Markkinakoko on tällä hetkellä haarukka ja havaintokokoelma — ei yksi luku", "6 · Markkinan koko ja rajaus",
                  [("195", "maan tutkimusrivit"), ("5", "maata vuosihavainnoilla"), ("$26,0–46,32 mrd", "kaupallinen globaali 2025 haarukka")],
                  f"Saksan matalan luottamuksen nestemalli on {v['de_model']}; sitä ei saa esittää havaittuna myyntinä.",
                  "Hyväksyttyjä virallisia kansallisia consumer-retail-arvoja on 0. Atlas ei julkaise omaa maailmanestimaattia ennen metodisten porttien täyttymistä.", "Market-values; IMARC; GVR; Fortune" )
    slide_claim(prs, ctx, 7, "Asiakkuus on vielä validoitava kolmessa eri päätöksentekologiikassa", "7 · Asiakkaat ja ostoperuste",
                "Mahdolliset segmentit ovat valmistajat, teknologiatoimittajat sekä IP-rahoittajat tai ostajat.",
                ["Valmistaja ostaa toimintarauhaa, oikeusvarmuutta tai teknologiaa — jos relevantti tuote ja alue osoitetaan.", "Teknologiatoimittaja arvioi integroitavuutta, vapautta toimia ja yksikkötaloutta.", "Rahoittaja arvioi omistusta, realisoitavaa kassavirtaa, kontrollia ja downside-arvoa."],
                "Nykyinen näyttö", "Julkinen aineisto ei vahvista nimettyjä asiakkaita, piloteja, ostoaikomuksia tai allekirjoitettuja lisenssejä.", "WIPO licensing; WIPO IP Finance" )
    slide_table(prs, ctx, 8, "Kilpailu on erotettava vaihtoehtoisista teknologioista ja patenttiriskistä", "8 · Kilpailu ja vaihtoehdot",
                ["Vertailutaso", "Kysymys", "Nykytila"],
                [["Tuoteratkaisut", "Ratkaiseeko tuote saman ongelman eri tavalla?", "Puuttuu"], ["Patenttiperheet", "Onko suojan päällekkäisyys tai FTO-riski?", "Puuttuu"], ["Kaupalliset vaihtoehdot", "Lisenssi, luovutus, sovinto vai oma käyttö?", "Oletus"], ["Ei-patentoidut vaihtoehdot", "Voiko suorituskyvyn saavuttaa kiertämällä vaatimukset?", "Puuttuu"]],
                "Kilpailija-analyysi on pankin teknologia-arvioinnin olennainen avoin työpaketti.", "Evidence Register; EPO; WIPO", [2.6, 5.6, 2.1] )
    slide_table(prs, ctx, 9, "Validoinnin vahvuus on epätasainen ja siksi näkyvästi luokiteltu", "9 · Validointi ja nykyinen näyttö",
                ["Väitealue", "Luokitus", "Mitä on", "Mitä puuttuu"],
                [["Patenttiydin", "Vahvistettu", "EPO-rekisteri ja B2", "Maakohtainen statusmatriisi"], ["Saksan prosessit", "Vahvistettu", "Kaksi virallista ratkaisua", "Lopullisuus, täytäntöönpano, kassa"], ["Markkinahavainnot", "Vahvistettu", "5 maan viralliset luvut", "Yhteismitallinen retail-arvo"], ["Tekninen testaus", "Puuttuu", "Patenttiselitys", "Riippumaton testi ja raakadata"], ["Kaupallinen näyttö", "Puuttuu", "Kaupallistamiskehys", "Asiakkaat, sopimukset, maksut"]],
                "Todistettu oikeusnäyttö ei korvaa teknistä, kaupallista tai taloudellista validointia.", "Evidence Register", [2.5, 1.8, 3.8, 4.4] )
    slide_process(prs, ctx, 10, "Kaupallistaminen etenee porttien kautta, ei massaväitteillä", "10 · Kaupallistamismalli",
                  [("Oikeusmatriisi", "Vahvista maa, haltija, maksu, rasite, operative claims ja määräpäivät."), ("Tuotedossier", "Hanki näyte, dokumentoi ketju ja tee asiamiehen tarkastama claim chart."), ("Kohdepisteytys", "Arvioi oikeus, näyttö, myynti, vastapuoli, kustannus ja täytäntöönpano."), ("Rajattu pilotti", "Testaa lisenssi-, sovinto-, luovutus- tai rahoitusreitti auditoitavin ehdoin.")],
                  "Vasta toteutunut sopimus tai saaminen luo kassavirtanäyttöä.", "WIPO licensing; dispute resolution; IPscore" )
    slide_table(prs, ctx, 11, "Taloudellinen malli on rakennettava lähteistä, ei markkinaosuusoletuksesta", "11 · Taloudellinen malli ja herkkyydet",
                ["Silta", "Todennettava syöte", "Nykytila"],
                [["Kokonaismarkkina", "Yhteismitallinen maakohtainen myynti", "0 retail-luovuttajaa"], ["Kohdistettava myynti", "Voimassaolo × tuote × aika × maa", "Puuttuu"], ["Rojaltipohja", "Claim-mapped net sales", "Puuttuu"], ["Kassavirta", "Sopimusehdot, kulut, verot, viive", "Puuttuu"], ["Vakuusarvo", "Downside-realisointi ja kontrolli", "Puuttuu"]],
                "Näytä downside/base/upside vasta, kun jokainen sillan syöte on dokumentoitu.", "WIPO IP valuation; Market-values", [2.5, 5.7, 1.8] )
    closing_slide(prs, ctx, 12, "Rahoituspäätös vasta neljän kriittisen aukon sulkeuduttua",
                  ["1. Asiamiehen allekirjoittama omistus-, rasite-, maksu- ja oikeusmatriisi.", "2. Priorisoitujen tuotteiden claim chartit ja dokumentoitu relevantti myynti.", "3. Toteutuneet tai sopimuspohjaiset kassavirrat sekä auditoidut taloustiedot.", "4. Riippumaton arvonmääritys ja downside-vakuusanalyysi.", "Seuraava päätös: hyväksytäänkö 90 päivän kontrolloitu diligence-vaihe?"], "Evidence Register; WIPO" )
    add_text(prs.slides[-1], "12 · Riskit, hallintatoimet ja seuraavat vaiheet", 0.64, 0.82, 8.7, 0.28, size=12, color=TEAL, bold=True)
    if len(prs.slides) != 12:
        raise AssertionError("Medium deck must have 12 slides")
    save_presentation(prs, path)


def build_large_deck(ctx: dict[str, Any], path: Path) -> None:
    v = common_values(ctx)
    p = ctx["patent_history"]["patent"]
    obs = ctx["observations"]
    model = ctx["models"]["DE-2025-LIQUID-RETAIL-EQUIVALENT-RANGE"]
    prs = new_presentation(ctx, "Pixan · laaja julkinen pankkidekki")
    cover_slide(prs, ctx, "Laaja 30 dian tutkija- ja rahoituspäätöspaketti", 30)
    slide_claim(prs, ctx, 2, "Rahoitettavuus on mahdollisuus, ei nykyinen johtopäätös", "Rahoitusteesi",
                "Viralliset patentti- ja oikeuslähteet oikeuttavat jatkodiligencen; ne eivät vielä osoita vakuusarvoa tai takaisinmaksua.",
                ["EPO:n muutettu B2-patentti ja Saksan ratkaisut muodostavat harvinaisen vahvan oikeusnäytön ankkurin.", "Markkina-aineisto kattaa 195 maan tutkimusrungon, mutta yhteismitallista vähittäisarvoa ei vielä ole.", "Rahoitusrakenne tarvitsee kansalliset oikeudet, claim-mapped sales -sillan, kassavirran ja riippumattoman arvonmäärityksen."],
                "Suositus", "Avaa 90 päivän ehdollinen diligence, ei lopullista luottopäätöstä.", "EPO; Saksan tuomiot; WIPO" )
    slide_table(prs, ctx, 3, "Kolme perustetta jatkaa — ja kolme rajaa olla kiirehtimättä", "Rahoitusteesi",
                ["Vahva signaali", "Mitä se tukee", "Mitä se ei todista"],
                [["EPO pysytti patentin muutettuna", "Dokumentoitu patenttiydin", "Kansallinen voimassaolo"], ["Saksan mitätöintiratkaisu", "Pätevyyden kansallinen signaali", "Lainvoima tai globaali pätevyys"], ["Saksan loukkausratkaisu", "Tuote- ja claim-kohtainen signaali", "Muu tuote, maa tai maksettu korvaus"]],
                "Pankin tulee hinnoitella vain se osa näytöstä, jonka omistus, toteutettavuus ja kassavirta on vahvistettu.", "EPO; DE 8 Ni 18/24; DE 7 O 3341/24", [3.1,4.6,4.6] )
    slide_claim(prs, ctx, 4, "Todennusketju katkeaa tällä hetkellä ennen kassavirtaa", "Ongelma",
                "Patentti → voimassa oleva maaoikeus → relevantti tuote → relevantti myynti → sopimus tai tuomio → maksu → velanhoito.",
                ["Ketjun alku on osin vahvistettu virallisilla lähteillä.", "Tuote- ja myyntikytkentä on vahvistettu vain rajatusti Saksan tuomiossa.", "Sopimus-, maksu-, yhtiötalous- ja vakuusarvonäyttö puuttuu julkisesta paketista."],
                "Luottoriski", "Yksi vahvistamaton lenkki voi muuttaa nimellisen markkina-arvon nollaksi realisoitavassa downside-skenaariossa.", "Evidence Register; WIPO" )
    slide_claim(prs, ctx, 5, "Patentoitu ratkaisu ohjaa lämmitystehoa resistanssitiedon avulla", "Ratkaisu",
                p["inventionSummaryFi"],
                ["Mittaus: lämmityselementin resistanssi.", "Tieto: tallennetut resistanssi–tehoarvot.", "Ohjaus: lämmittimelle syötetty teho ja käyttäjäsäädön rajat."],
                "Tulkintaraja", "Yleiskielinen kuvaus ei korvaa maakohtaista claim constructionia tai tuotekohtaista vaatimusanalyysiä.", "EP3032975B2" )
    slide_table(prs, ctx, 6, "B2-tekstin yhdeksän vaatimusta ovat arvioinnin lähtöpiste", "Patentti",
                ["Elementti", "Julkinen kuvaus", "Diligence-testi"],
                [["Ohjain / menetelmä", "Sähköisen höyrystimen hallinta", "Mikä tuoteversio ja maa?"], ["Resistanssin mittaus", "Lämmityselementin resistanssi", "Miten ja milloin mitataan?"], ["Tallennetut arvot", "Resistanssi–teho-kytkentä", "Missä data sijaitsee?"], ["Ei-proportionaalisuus", "Tehosuhteen määritelty luonne", "Täyttyykö vaatimuspiirre?"], ["Säätörajat", "Minimi ja tallennettu maksimi", "Miten käyttöliittymä toteuttaa rajat?"]],
                "Jokainen vaatimuspiirre on osoitettava todisteella; ominaisuusluettelo ei yksin riitä.", "EP3032975B2", [2.2,5.9,3.1] )
    slide_metrics(prs, ctx, 7, "IP-historian ydintapahtumat ovat virallisesti jäljitettävissä", "Patentti",
                  [("14.8.2013", "varhaisin prioriteetti"), ("24.4.2024", "B2-julkaisu"), ("9", "muutettua vaatimusta")],
                  "EPO:n keskitetty väite- ja valitusmenettely on päättynyt.",
                  "Kansalliset post-grant-oikeudet elävät erillään EPO:n keskusmenettelystä.", "EPO Register; B2" )
    slide_metrics(prs, ctx, 8, "Perhejulkaisuja on 22 — voimassa olevien maiden määrää ei vielä väitetä", "Maantieteellinen kattavuus",
                  [(str(v["family_count"]), "perhejulkaisutietuetta"), ("4", "kansallista rekisteritarkistusta"), ("?", "täytäntöönpanokelpoista maata")],
                  "Julkaisureitti on kartta, ei omistus- tai voimassaolotodistus.",
                  "Asiamiehen maamatriisin tulee sisältää haltija, operative claims, vuosimaksu, kuitti, rasitteet, UPC-asema ja seuraava määräpäivä.", "EPO family; kansalliset rekisterit" )
    slide_table(prs, ctx, 9, "Saksan ratkaisut ovat vahvaa näyttöä tarkasti rajatussa kehyksessä", "Oikeudellinen näyttö",
                ["Ratkaisu", "Vahvistettu", "Avoin"],
                [["8 Ni 18/24 (EP)", "Mitätöintikanne hylättiin 14.1.2026", "BGH-valitus X ZR 21/26"], ["7 O 3341/24", "Vaatimusten 1 ja 6 loukkaus tarkastelluissa tuotteissa", "Valitustila, lainvoima, täytäntöönpano, maksu"]],
                "Saksan näyttö ei automaattisesti siirry toiseen tuotteeseen, vastapuoleen tai valtioon.", "Viralliset Saksan tuomiot", [3.6,4.2,5.2] )
    slide_claim(prs, ctx, 10, "Kiinan asia ei ole loukkausvoitto", "Oikeudellinen näyttö",
                "Julkinen sekundäärinen docket-tieto viittaa hylätyn hakemuksen hakijapuolen uudelleentarkastukseen.",
                ["Menettely luokitellaan review request -asiaksi.", "Virallista päätöstä ja tarkkoja perusteluja ei saatu julkiseen pakettiin.", "CN105764365B julkaistiin myöhemmin myönnettynä 4.5.2021."],
                "Käyttöraja", "Asiaa ei saa kuvata Kiinan loukkausoikeudenkäynniksi, vastapuolen mitätöintiasiaksi tai kassavirtanäytöksi.", "RPX; CNIPA guidance; EPO family" )
    slide_table(prs, ctx, 11, "Neljä ajankohtaista IP-hälytystä vaatii dokumentoidun omistajan", "Riskit",
                ["Maa / alue", "Päivä", "Toimi"],
                [["Australia", "14.8.2026", "Vahvista maksu, kuitti ja uusi rekisteriote"], ["Suomi", "31.8.2026", "Maksa 14. vuosimaksu ja arkistoi kuitti"], ["Eurooppa", "7.8.2026", "Täsmäytä kaikki kansalliset oikeudet"], ["Yhdysvallat", "4.12.2026", "Vahvista 7,5 vuoden ylläpitomaksu"]],
                "Määräpäivävalvonta on vakuusarvon operatiivinen kontrolli, ei hallinnollinen sivuseikka.", "IP Australia; PRH; EPO; USPTO", [2.4,2.0,7.1] )
    slide_metrics(prs, ctx, 12, "Atlas kattaa maailman tutkimusrunkona, ei vielä markkina-arvona", "Markkina",
                  [("195", "maata universumissa"), ("37", "evidenssimerkintää"), ("158", "D-luokan maata")],
                  "Kattavuus tarkoittaa tutkimusrivejä; useimmista maista puuttuu virallinen vuosimyynti.",
                  "Luokat A–D kuvaavat evidenssikypsyyttä, eivät markkinan kokoa tai kaupallista houkuttelevuutta.", "UN; Atlas" )
    slide_table(prs, ctx, 13, "Viiden maan viralliset havainnot mittaavat eri asioita", "Markkina",
                ["Maa", "Vuosi", "Virallinen havainto"],
                [["Kanada", "2024", f"{v['ca_value']} toimitusarvo; {v['ca_litres']} nestettä"], ["Saksa", "2023–2025", f"{v['de23']} → {v['de25']} verotettua nestettä"], ["Suomi", "2025", "11 801,062 l; 3,540 milj. € valmisteveroa"], ["Puola", "2023 / 2025", "805 441 l; 993,1 milj. PLN e-nesteveroa"], ["Ruotsi", "2024", "26 000 l; 80 milj. SEK valmisteveroa"]],
                "Litroja, toimitusarvoja ja valmisteveroja ei summata yhdeksi markkinaksi.", "Health Canada; Destatis; Vero; Sejm; Ruotsin hallitus", [1.6,2.1,8.3] )
    slide_metrics(prs, ctx, 14, "Kanada on vahva toimitusmyynnin ankkuri, ei retail-arvon luovuttaja", "Kanada",
                  [(v["ca_value"], "valmistaja-/maahantuojatoimitukset"), ("118,9 milj.", "raportoitua yksikköä"), (v["ca_litres"], "raportoitua nestettä")],
                  "Virallinen koko vuoden havainto kattaa neljä vaping-tuoteryhmää.",
                  "Tukku-/vähittäismyyjille toimitettu arvo ei ole kuluttajien kassamyynti; varasto, kate ja kanava on täsmäytettävä.", "Health Canada 2024" )
    slide_table(prs, ctx, 15, "Saksan virallinen nestemäärä kasvoi, mutta arvo vaatii hintaoletuksen", "Saksa",
                ["Vuosi", "Verotettu neste", "Valmistevero", "Lopullisuus"],
                [["2023", v["de23"], "201 milj. €", "Lopullinen"], ["2024", v["de24"], "266 milj. €", "Lopullinen"], ["2025", v["de25"], "404 milj. €", "Alustava"]],
                "Verotettu nestemäärä ei sisällä laitteita, verotonta tai laitonta kauppaa eikä ole retail-arvo.", "Destatis 73411-0003", [1.4,2.3,2.1,1.8] )
    slide_metrics(prs, ctx, 16, "Saksan mallihaitari näyttää herkkyyden — ei havaittua myyntiä", "Mallinnus",
                  [(euro_m(model["low"]), "0,44 €/ml"), (euro_m(model["central"]), "0,79 €/ml"), (euro_m(model["high"]), "1,09 €/ml")],
                  f"Kaava: {model['formula']}.",
                  "Vuoden 2025 alustava määrä kerrotaan kolmella yhden verkkokaupan vuoden 2026 hinnalla. Confidence = low; laitteet ja useita kanava-/mix-tekijöitä puuttuu.", "Destatis; inTaste-hintapisteet" )
    slide_metrics(prs, ctx, 17, "Kaupalliset globaaliarviot ovat sanity check, eivät oma estimaatti", "Globaali markkina",
                  [("$26,0 mrd", "IMARC 2025"), ("$45,7 mrd", "GVR 2025"), ("$46,32 mrd", "Fortune 2025")],
                  "Haarukka on leveä, koska tuoterajaukset ja metodit voivat poiketa.",
                  "Arvioita verrataan keskenään. Niitä ei summata, eikä haarukkaa käytetä automaattisesti rojaltipohjana.", "IMARC; Grand View Research; Fortune Business Insights" )
    slide_claim(prs, ctx, 18, "Hyväksyttävä maailmanestimaatti tarvitsee vähintään kolme yhteensopivaa luovuttajaa", "Metodi",
                "Nykyinen comparable consumer-retail donor count on 0; hard gate ei täyty.",
                ["Sama tuoterajaus ja kalenterivuosi.", "Kuluttajavähittäisarvo, ei toimitus-, vero- tai volyymiproxy.", "Alue- ja sääntelytyyppien peitto sekä suora validointi suurissa talouksissa."],
                "Vasta sitten", "Trianguloi kysyntä-, vero-, tulli-, yritys- ja hintamenetelmät. Vertaa tuloksia; älä lisää vaihtoehtoisia arvioita yhteen.", "Market-values modelReadiness" )
    slide_table(prs, ctx, 19, "Markkinan ja patentin väliin tarvitaan viisi läpinäkyvää suodatinta", "Arvosilta",
                ["Taso", "Suodatin", "Näyttö"],
                [["1. Kokonaismarkkina", "Tuote- ja mittarirajaus", "Osittainen"], ["2. Oikeusalue", "Voimassa oleva operative claim", "Puuttuu globaalisti"], ["3. Relevantit tuotteet", "Claim chart", "Rajattu Saksan näyttö"], ["4. Relevantti myynti", "Tuote × maa × aika × net sales", "Puuttuu"], ["5. Kassavirta", "Rojalti/sovinto − kulut − verot − viive", "Puuttuu"]],
                "Vain alimman tason kassavirta voi palvella velkaa; ylempi markkina ei sellaisenaan voi.", "WIPO valuation; Evidence Register", [2.1,4.1,4.6] )
    slide_claim(prs, ctx, 20, "Mahdolliset asiakkaat ovat hypoteeseja, eivät vielä näyttöä", "Asiakkaat",
                "Segmentointi johdetaan kaupallistamisreiteistä: valmistajat, teknologiatoimittajat sekä IP-rahoittajat ja ostajat.",
                ["Valmistajalle arvo voi olla lisenssi, toimintarauha tai sovinto.", "Teknologiatoimittajalle arvo voi olla integroitava toiminto tai oikeusasema.", "Rahoittajalle arvo on kontrolloitava, realisoitava kassavirta ja downside-suoja."],
                "Validointi", "Dokumentoi 10–15 haastattelua, päätöskriteerit, vastalauseet, budjetti ja seuraava askel. Julkinen aineisto ei vielä sisällä näitä.", "WIPO licensing; IP Finance" )
    slide_table(prs, ctx, 21, "Kilpailukartta on rakennettava neljälle rinnakkaiselle tasolle", "Kilpailu",
                ["Taso", "Analyysi", "Tuotos"],
                [["Tuotteet", "Toiminto, arkkitehtuuri, hinta, markkina", "Vertailumatriisi"], ["Patentit", "Claims, prior art, status, FTO", "Patenttilandscape"], ["Kiertoratkaisut", "Voiko suorituskyvyn toteuttaa eri tavalla?", "Design-around-arvio"], ["Kaupallinen vaihtoehto", "Lisenssi, hankinta, oma kehitys, riitely", "Buy/build/license/litigate-malli"]],
                "Tekninen etu ei ole uskottava ennen kuin vaihtoehdot on kuvattu ja lähteistetty.", "Evidence Register; EPO" , [2.0,5.3,3.5] )
    slide_process(prs, ctx, 22, "Tuotevalidointi rakentuu katkeamattomaksi todisteketjuksi", "Tekninen validointi",
                  [("Näyte", "Osta oikeasta maasta ja ajankohdasta; dokumentoi myyjä, tuoteversio ja sarjatiedot."), ("Hallussapitoketju", "Tallenna vastaanotto, säilytys, avaaminen, kuvaus ja tiedostojen hashit."), ("Teardown ja testi", "Tee riippumaton mittausprotokolla, raakadata ja toistettavuustesti."), ("Claim chart", "Mapita jokainen vaatimuspiirre todisteeseen ja asiamiehen johtopäätökseen.")],
                  "Markkinamyynti voidaan kohdistaa vasta, kun tuoteidentiteetti ja claim-kytkentä ovat hallittuja.", "EP3032975B2; Saksan tuomio" )
    slide_process(prs, ctx, 23, "Kaupallistaminen aloitetaan kovista porteista", "Kaupallistaminen",
                  [("Vahvista oikeus", "Ei yhteydenottoa ilman maakohtaista omistusta, voimassaoloa, rasite- ja määräpäivätietoa."), ("Vahvista tuote", "Ei väitettä ilman tuotenäytettä, claim chartia ja paikallisen teon dokumentointia."), ("Pisteytä kohde", "Arvioi myynti, näyttö, vastapuoli, toimivalta, kustannus ja perittävyys."), ("Testaa pilotti", "Neuvottele lisenssi-, sovinto-, luovutus- tai rahoitusvaihtoehdot kontrolloidusti.")],
                  "Yhteydenottokirje ei automaattisesti katkaise vanhentumista tai todista tiedoksiantoa.", "WIPO dispute resolution; EPO IPscore" )
    slide_table(prs, ctx, 24, "Kaupallistamisreitit eroavat kassavirran, kontrollin ja riskin suhteen", "Kaupallistaminen",
                ["Reitti", "Kassavirta", "Keskeinen riski"],
                [["Lisenssi", "Upfront + jatkuva rojalti", "Rojaltipohjan auditointi"], ["Sovinto", "Kertamaksu / vaiheistus", "Ei automaattista ennakkotapausta"], ["Luovutus", "Kauppahinta", "Luovutetaan tuleva upside"], ["IP-rahoitus", "Velka tai revenue share", "Vakuusarvo ja kontrollit"], ["Prosessirahoitus", "Kuluihin sidottu pääoma", "Korkea kustannus ja lopputulosriski"]],
                "Valitse reitti vasta, kun oikeus, vastapuoli, kassavirta ja downside on todennettu.", "WIPO licensing; IP Finance; TPLF mapping", [2.1,4.1,5.2] )
    slide_table(prs, ctx, 25, "Taloudellinen malli alkaa todennettavista syötteistä", "Taloudellinen malli",
                ["Syöte", "Lähde", "Status"],
                [["Maakohtainen relevantti myynti", "Viranomainen / vastapuolen disclosure", "Puuttuu"], ["Claim-mapped osuus", "Asiamiehen tuotedossier", "Puuttuu"], ["Rojalti tai vahinko", "Sopimus / oikeudellinen analyysi", "Puuttuu"], ["Ajoitus ja perittävyys", "Prosessi- ja vastapuolianalyysi", "Puuttuu"], ["Kulut ja verot", "Budjetti / veroasiantuntija", "Puuttuu"], ["Diskontto ja downside", "Riippumaton arvonmääritys", "Puuttuu"]],
                "Nykyisestä julkisesta paketista ei voi johtaa pankkikelpoista NPV:tä.", "Evidence Register; WIPO valuation", [3.3,5.6,1.7] )
    slide_table(prs, ctx, 26, "Herkkyydet on sidottava todellisiin riskeihin", "Herkkyydet",
                ["Ajuri", "Downside", "Base", "Upside"],
                [["Oikeusalueet", "Vain vahvistettu maa", "Priorisoidut maat", "Laajempi varmennettu peitto"], ["Claim-osuvuus", "Yksi tuote", "Validoitu portfolio", "Laaja mutta dokumentoitu osuus"], ["Rojalti / korvaus", "Asiantuntijan alaraja", "Vertailuehdot", "Vain todennettu yläraja"], ["Ajoitus", "Valitus ja pitkä perintä", "Sopimuspolku", "Upfront-rakenne"], ["Kulut", "Täysi riitelybudjetti", "Rajattu pilotti", "Vastapuolen kattamat kulut"]],
                "Taulukkoon ei syötetä prosentteja ennen lähdetodisteita; tämä dia määrittää skenaarioiden rakenteen.", "WIPO valuation", [2.7,3.1,2.0,2.0] )
    slide_table(prs, ctx, 27, "Viisi kysymystä määrittää pankin seuraavan päätöksen", "Tutkijan kysymykset",
                ["#", "Kysymys", "Vaadittu vastaus"],
                [["1", "Mitä tarkalleen omistetaan ja missä se on voimassa?", "Allekirjoitettu oikeusmatriisi"], ["2", "Mikä tuote täyttää mitkä vaatimuspiirteet?", "Claim chart + riippumaton testi"], ["3", "Mikä on todennettu relevantti myynti?", "Tuote–maa–aika-net sales"], ["4", "Mistä ja milloin velanhoitokassa syntyy?", "Sopimukset, maksut, ennuste"], ["5", "Mitä vakuus realisoi downside-tilanteessa?", "Riippumaton arvo + toteutuspolku"]],
                "Jos yksikin vastaus jää olennaisesti auki, rahoitus on rakennettava ehdolliseksi ja vaiheistetuksi.", "Evidence Register", [0.7,5.2,6.5] )
    slide_table(prs, ctx, 28, "Puuttuva aineisto priorisoituu vaikutuksen, ei helppouden mukaan", "Aineistopyynnöt",
                ["Prioriteetti", "Aineisto", "Päätösvaikutus"],
                [["1", "Omistus, siirrot, rasitteet, vuosimaksut", "Olemassa oleva ja kontrolloitava oikeus"], ["2", "Tuotenäytteet, testit ja claim chartit", "Tekninen osuvuus"], ["3", "Relevantti myynti ja vastapuolidata", "Rojaltipohja"], ["4", "Sopimukset, saatavat ja maksut", "Velanhoitokyky"], ["5", "Tilinpäätös, velat, budjetti ja rahoitustarve", "Yhtiö- ja luottoriski"], ["6", "Riippumaton IP-/yritysarvonmääritys", "Vakuus ja hinta"]],
                "Julkinen paketti näyttää aukot; luottamuksellinen näyttö kuuluu pääsyrajattuun datahuoneeseen.", "Evidence Register", [1.2,5.0,5.4] )
    slide_process(prs, ctx, 29, "90 päivän ohjelma muuttaa aukot päätöskelpoisiksi kontrolleiksi", "Seuraavat vaiheet",
                  [("0–30 päivää", "Oikeusmatriisi, määräpäivät, omistus- ja rasiteselvitys sekä yhtiöaineiston indeksi."), ("31–60 päivää", "Tuotedossierit, claim chartit, priorisoitu markkinamyynti ja asiakasvalidointi."), ("61–90 päivää", "Kassavirtamalli, riippumaton arvonmääritys, downside ja term sheet -vaihtoehdot."), ("Päätösportti", "Hyväksy, rajaa, vaiheista tai hylkää rahoitus näkyvillä ehdoilla ja stop-kriteereillä.")],
                  "Paketti päivitetään samasta julkisesta lähdedatasta jokaisessa sivustojulkaisussa.", "Evidence Register; changelog" )
    closing_slide(prs, ctx, 30, "Pankkikelpoinen tarina on todennusketju — ei suurin mahdollinen markkinaluku",
                  ["Vahva lähtökohta: dokumentoitu patenttiydin ja virallista Saksan oikeusnäyttöä.", "Ratkaiseva avoin työ: kansalliset oikeudet, claim-mapped sales, kassavirta ja downside-arvo.", "Suositus: ehdollinen 90 päivän diligence, selkeät päätösportit ja pääsyrajattu datahuone.", "Tämä julkinen paketti on tarkistettava evidenssikartta, ei Pixan Oy:n virallinen kanta tai rahoitussuositus."], "Kaikki lähteet Evidence Registerissä" )
    if len(prs.slides) != 30:
        raise AssertionError(f"Large deck must have 30 slides, got {len(prs.slides)}")
    save_presentation(prs, path)


def save_presentation(prs: Presentation, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(path)
    normalize_ooxml(path)


def normalize_ooxml(path: Path) -> None:
    """Rewrite an OOXML zip with stable order, metadata and timestamps."""
    with zipfile.ZipFile(path, "r") as source:
        entries = []
        for name in sorted(source.namelist()):
            payload = source.read(name)
            if name == "docProps/core.xml":
                # openpyxl replaces the modified property with wall-clock time
                # during save.  Canonicalise it to the already fixed created
                # timestamp so identical source data always yields identical
                # files and manifest hashes.
                core = payload.decode("utf-8")
                created = re.search(r"<dcterms:created\b[^>]*>([^<]+)</dcterms:created>", core)
                if created:
                    core = re.sub(
                        r"(<dcterms:modified\b[^>]*>)[^<]*(</dcterms:modified>)",
                        rf"\g<1>{created.group(1)}\g<2>",
                        core,
                    )
                    payload = core.encode("utf-8")
            entries.append((name, payload))
    fd, temp_name = tempfile.mkstemp(prefix=path.stem + "-", suffix=path.suffix, dir=path.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        # Store canonical members without DEFLATE.  ZIP compression output can
        # vary with the system zlib version (macOS builder vs GitHub's Linux
        # runner), whereas ZIP_STORED makes the committed artifact reproducible
        # byte-for-byte across those environments.
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_STORED) as target:
            for name, payload in entries:
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_STORED
                info.create_system = 3
                info.external_attr = 0o600 << 16
                target.writestr(info, payload)
        temp_path.replace(path)
        path.chmod(0o644)
    finally:
        temp_path.unlink(missing_ok=True)


def build_workbook(ctx: dict[str, Any], rows: list[dict[str, str]], path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Evidence Register"
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:I{len(rows) + 1}"

    for col, header in enumerate(REGISTER_HEADERS, start=1):
        cell = ws.cell(1, col, header)
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.font = Font(name="Aptos", size=11, bold=True, color=WHITE)
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 34

    status_fill = {
        "Vahvistettu": "D9EDE7",
        "Tuettu": "DCEAF5",
        "Oletus": "FFF0CB",
        "Puuttuu": "F8DADA",
    }
    thin = Side(style="thin", color="D9E2E7")
    for ridx, item in enumerate(rows, start=2):
        for cidx, header in enumerate(REGISTER_HEADERS, start=1):
            cell = ws.cell(ridx, cidx, item[header])
            cell.font = Font(name="Aptos", size=10, color="000000")
            cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            cell.border = Border(bottom=thin)
        ws.cell(ridx, 8).fill = PatternFill("solid", fgColor=status_fill[item["Luottamustaso"]])
        ws.cell(ridx, 8).font = Font(name="Aptos", size=10, bold=True, color=INK)
        ws.row_dimensions[ridx].height = 78

    widths = {"A": 44, "B": 22, "C": 54, "D": 46, "E": 15, "F": 42, "G": 42, "H": 16, "I": 54}
    for col, width in widths.items():
        ws.column_dimensions[col].width = width
    ws.sheet_view.zoomScale = 65
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A3
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"
    ws.page_margins.left = 0.2
    ws.page_margins.right = 0.2
    ws.page_margins.top = 0.35
    ws.page_margins.bottom = 0.35
    table = Table(displayName="EvidenceRegister", ref=f"A1:I{len(rows) + 1}")
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showFirstColumn=False, showLastColumn=False, showRowStripes=True, showColumnStripes=False)
    ws.add_table(table)
    validation = DataValidation(type="list", formula1='"Vahvistettu,Tuettu,Oletus,Puuttuu"', allow_blank=False)
    ws.add_data_validation(validation)
    validation.add(f"H2:H{len(rows) + 1}")

    summary = wb.create_sheet("Yhteenveto")
    summary.sheet_view.showGridLines = False
    summary.merge_cells("A1:H2")
    summary["A1"] = "Pixan · julkisen evidenssipaketin yhteenveto"
    summary["A1"].fill = PatternFill("solid", fgColor=NAVY)
    summary["A1"].font = Font(name="Aptos Display", size=24, bold=True, color=WHITE)
    summary["A1"].alignment = Alignment(vertical="center")
    meta = [
        ("Versio", ctx["release"]["version"]),
        ("Päivitetty", ctx["as_of"]),
        ("Rajaus", "Julkinen riippumaton kooste; ei Pixan Oy:n virallinen kanta eikä arvo-, laina-, sijoitus- tai oikeudellinen lausunto."),
        ("Rivit", len(rows)),
    ]
    for idx, (label, value) in enumerate(meta, start=4):
        summary.cell(idx, 1, label).font = Font(name="Aptos", size=11, bold=True, color=MUTED)
        summary.cell(idx, 2, value).font = Font(name="Aptos", size=11, color=INK)
        summary.cell(idx, 2).alignment = Alignment(wrap_text=True)
    summary["A10"] = "Näytön jakauma"
    summary["A10"].font = Font(name="Aptos", size=14, bold=True, color=NAVY)
    counts = Counter(item["Luottamustaso"] for item in rows)
    for idx, status in enumerate(("Vahvistettu", "Tuettu", "Oletus", "Puuttuu"), start=11):
        summary.cell(idx, 1, status)
        summary.cell(idx, 2, counts[status])
        summary.cell(idx, 1).fill = PatternFill("solid", fgColor=status_fill[status])
        summary.cell(idx, 1).font = Font(name="Aptos", size=11, bold=True, color=INK)
        summary.cell(idx, 2).font = Font(name="Aptos", size=11, color=INK)
    summary["A17"] = "Kolme vahvinta rahoitusperustetta"
    summary["A17"].font = Font(name="Aptos", size=14, bold=True, color=NAVY)
    strongest = [
        "EPO pysytti patentin muutettuna ja B2-julkaisu on virallisesti jäljitettävissä.",
        "Saksasta on viralliset mitätöinti- ja loukkausratkaisut tarkoin näkyvin rajauksin.",
        "Julkinen markkina-aineisto erottaa viralliset havainnot, proxyt, mallit ja puutteet toisistaan.",
    ]
    for idx, text in enumerate(strongest, start=18):
        summary.cell(idx, 1, idx - 17)
        summary.cell(idx, 2, text)
    summary["A23"] = "Pankkikelpoisuuden neljä korjausta"
    summary["A23"].font = Font(name="Aptos", size=14, bold=True, color=NAVY)
    fixes = [
        "Asiamiehen allekirjoittama oikeus-, omistus-, rasite- ja maksumatriisi.",
        "Priorisoitujen tuotteiden riippumattomat testit ja claim chartit.",
        "Toteutunut tai sopimuspohjainen kassavirta sekä auditoidut taloustiedot.",
        "Riippumaton arvonmääritys ja downside-vakuusanalyysi.",
    ]
    for idx, text in enumerate(fixes, start=24):
        summary.cell(idx, 1, idx - 23)
        summary.cell(idx, 2, text)
    summary.column_dimensions["A"].width = 28
    summary.column_dimensions["B"].width = 95
    summary.sheet_view.zoomScale = 90
    summary.page_setup.orientation = "landscape"
    summary.page_setup.fitToWidth = 1
    summary.page_setup.fitToHeight = 1
    summary.sheet_properties.pageSetUpPr.fitToPage = True
    for row in range(1, 30):
        summary.row_dimensions[row].height = 23
    summary.row_dimensions[1].height = 32
    summary.row_dimensions[2].height = 32

    questions = wb.create_sheet("Tutkijan kysymykset")
    questions.sheet_view.showGridLines = False
    q_headers = ["Prioriteetti", "Todennäköinen kysymys", "Vaadittu näyttö", "Nykytila"]
    q_rows = [
        (1, "Mitä tarkalleen omistetaan ja missä oikeus on voimassa?", "Maakohtainen oikeusmatriisi", "Puuttuu kattavasti"),
        (2, "Mikä tuote täyttää mitkä vaatimuspiirteet?", "Riippumaton testi ja claim chart", "Rajattu Saksan näyttö"),
        (3, "Mikä on todennettu relevantti myynti?", "Tuote–maa–aika-net sales", "Puuttuu"),
        (4, "Mistä ja milloin velanhoitokassa syntyy?", "Sopimukset, maksut ja ennuste", "Puuttuu"),
        (5, "Mitä vakuus realisoi downside-tilanteessa?", "Riippumaton arvio ja toteutuspolku", "Puuttuu"),
    ]
    for cidx, value in enumerate(q_headers, start=1):
        questions.cell(1, cidx, value).fill = PatternFill("solid", fgColor=NAVY)
        questions.cell(1, cidx).font = Font(name="Aptos", size=11, bold=True, color=WHITE)
    for ridx, values in enumerate(q_rows, start=2):
        for cidx, value in enumerate(values, start=1):
            questions.cell(ridx, cidx, value)
            questions.cell(ridx, cidx).alignment = Alignment(wrap_text=True, vertical="top")
            questions.cell(ridx, cidx).font = Font(name="Aptos", size=11, color=INK)
        questions.row_dimensions[ridx].height = 52
    for col, width in zip("ABCD", (14, 52, 50, 28)):
        questions.column_dimensions[col].width = width
    questions.freeze_panes = "A2"
    questions.sheet_view.zoomScale = 90
    questions.page_setup.orientation = "landscape"
    questions.page_setup.fitToWidth = 1
    questions.page_setup.fitToHeight = 1
    questions.sheet_properties.pageSetUpPr.fitToPage = True

    sources_ws = wb.create_sheet("Lähteet")
    sources_ws.sheet_view.showGridLines = False
    sources_ws.append(["Lähdetunnus", "Julkaisija", "Lähdeluokka", "URL", "Haettu / data-as-of"])
    all_sources = list(ctx["market"]["sources"]) + list(ctx["patent_history"]["sources"])
    for source in sorted(all_sources, key=lambda item: item["sourceId"]):
        sources_ws.append([
            source["sourceId"],
            source.get("publisher", ""),
            source.get("sourceKind", source.get("evidenceTier", "")),
            source.get("pageUrl") or source.get("url") or "",
            source.get("retrievedAt", ctx["as_of"]),
        ])
    for cell in sources_ws[1]:
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.font = Font(name="Aptos", size=11, bold=True, color=WHITE)
    for row in sources_ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = Font(name="Aptos", size=10, color=INK)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for col, width in zip("ABCDE", (30, 38, 25, 80, 20)):
        sources_ws.column_dimensions[col].width = width
    sources_ws.freeze_panes = "A2"
    sources_ws.auto_filter.ref = f"A1:E{sources_ws.max_row}"
    sources_ws.sheet_view.zoomScale = 75
    sources_ws.page_setup.orientation = "landscape"
    sources_ws.page_setup.paperSize = sources_ws.PAPERSIZE_A3
    sources_ws.page_setup.fitToWidth = 1
    sources_ws.page_setup.fitToHeight = 0
    sources_ws.sheet_properties.pageSetUpPr.fitToPage = True
    sources_ws.print_title_rows = "1:1"

    wb.properties.title = "Pixan Evidence Register"
    wb.properties.subject = "Julkinen pankki- ja teknologia-arvioinnin evidenssirekisteri"
    wb.properties.creator = "Pixan Global Market Evidence Atlas"
    stamp = parse_iso_date(ctx["as_of"]).replace(tzinfo=None)
    wb.properties.created = stamp
    wb.properties.modified = stamp
    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    normalize_ooxml(path)


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REGISTER_HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def inspect_pptx(path: Path, expected_slides: int) -> None:
    prs = Presentation(path)
    if len(prs.slides) != expected_slides:
        raise AssertionError(f"{path.name}: expected {expected_slides} slides, got {len(prs.slides)}")
    text = "\n".join(shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text_frame"))
    public_text_scan([text])
    if "Julkinen riippumaton" not in text and "Julkinen riippumaton evidenssikooste" not in text:
        raise AssertionError(f"{path.name}: public boundary disclosure missing")


def inspect_xlsx(path: Path, expected_rows: int) -> None:
    wb = load_workbook(path, read_only=False, data_only=False)
    if wb.sheetnames != ["Evidence Register", "Yhteenveto", "Tutkijan kysymykset", "Lähteet"]:
        raise AssertionError(f"Unexpected workbook sheets: {wb.sheetnames}")
    ws = wb["Evidence Register"]
    headers = [ws.cell(1, col).value for col in range(1, 10)]
    if headers != REGISTER_HEADERS:
        raise AssertionError("Evidence Register headers changed")
    if ws.max_row - 1 != expected_rows:
        raise AssertionError(f"Expected {expected_rows} evidence rows, got {ws.max_row - 1}")
    statuses = {ws.cell(row, 8).value for row in range(2, ws.max_row + 1)}
    if not statuses.issubset(ALLOWED_STATUSES) or statuses != ALLOWED_STATUSES:
        raise AssertionError(f"Evidence statuses invalid or incomplete: {statuses}")
    public_text_scan(str(cell.value or "") for sheet in wb.worksheets for row in sheet.iter_rows() for cell in row)


def inspect_ooxml(path: Path) -> None:
    forbidden_parts = ("vbaproject", "oleobject", "externallink", "connections", "comments", "notesmaster", "notesslide")
    with zipfile.ZipFile(path) as package:
        names = [name.casefold() for name in package.namelist()]
        for name in names:
            if any(part in name for part in forbidden_parts):
                raise AssertionError(f"{path.name}: forbidden OOXML part {name}")
        payload = b"\n".join(package.read(name) for name in package.namelist() if name.endswith((".xml", ".rels")))
        decoded = payload.decode("utf-8", errors="ignore")
        public_text_scan([decoded])


def artifact_entry(artifact_id: str, path: Path, *, kind: str, title_fi: str, title_en: str, slide_count: int | None = None, row_count: int | None = None) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "id": artifact_id,
        "kind": kind,
        "titleFi": title_fi,
        "titleEn": title_en,
        "fileName": path.name,
        "path": f"downloads/{path.name}",
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }
    if slide_count is not None:
        entry["slideCount"] = slide_count
    if row_count is not None:
        entry["rowCount"] = row_count
    return entry


def write_manifest(ctx: dict[str, Any], rows: list[dict[str, str]]) -> None:
    manifest = {
        "schemaVersion": 1,
        "generatedFromPublicDataOnly": True,
        "release": {
            "id": ctx["release"]["id"],
            "version": ctx["release"]["version"],
            "publishedAt": ctx["release"]["publishedAt"],
        },
        "asOf": ctx["as_of"],
        "language": "fi",
        "publicBoundary": {
            "en": "Independent public evidence summary. Not Pixan Oy's official position; not an audit, valuation, legal opinion, investment recommendation or lending recommendation.",
            "fi": "Riippumaton julkinen evidenssikooste. Ei Pixan Oy:n virallinen kanta; ei tilintarkastus, arvonmääritys, oikeudellinen lausunto, sijoitussuositus tai lainasuositus.",
        },
        "inputs": [{"path": str(path.relative_to(ROOT)), "sha256": sha256(path)} for path in INPUT_FILES],
        "artifacts": [
            artifact_entry("short-deck", OUTPUTS["short-deck"], kind="pptx", title_fi="Suppea pankkidekki", title_en="Short bank deck", slide_count=6),
            artifact_entry("medium-deck", OUTPUTS["medium-deck"], kind="pptx", title_fi="Keskikokoinen pankkidekki", title_en="Medium bank deck", slide_count=12),
            artifact_entry("large-deck", OUTPUTS["large-deck"], kind="pptx", title_fi="Laaja pankkidekki", title_en="Large bank deck", slide_count=30),
            artifact_entry("evidence-register", OUTPUTS["evidence-register"], kind="xlsx", title_fi="Evidence Register", title_en="Evidence Register", row_count=len(rows)),
        ],
    }
    public_text_scan([json.dumps(manifest, ensure_ascii=False)])
    MANIFEST_OUTPUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_all() -> dict[str, Any]:
    ctx = build_context()
    rows = evidence_rows(ctx)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    build_short_deck(ctx, OUTPUTS["short-deck"])
    build_medium_deck(ctx, OUTPUTS["medium-deck"])
    build_large_deck(ctx, OUTPUTS["large-deck"])
    build_workbook(ctx, rows, OUTPUTS["evidence-register"])
    write_csv(rows, CSV_OUTPUT)

    inspect_pptx(OUTPUTS["short-deck"], 6)
    inspect_pptx(OUTPUTS["medium-deck"], 12)
    inspect_pptx(OUTPUTS["large-deck"], 30)
    inspect_xlsx(OUTPUTS["evidence-register"], len(rows))
    for path in OUTPUTS.values():
        inspect_ooxml(path)
    write_manifest(ctx, rows)
    return {"version": ctx["release"]["version"], "asOf": ctx["as_of"], "evidenceRows": len(rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-determinism", action="store_true", help="Build twice and verify stable artifact hashes.")
    args = parser.parse_args()
    result = build_all()
    if args.check_determinism:
        first = {path.name: sha256(path) for path in (*OUTPUTS.values(), CSV_OUTPUT, MANIFEST_OUTPUT)}
        result = build_all()
        second = {path.name: sha256(path) for path in (*OUTPUTS.values(), CSV_OUTPUT, MANIFEST_OUTPUT)}
        if first != second:
            changed = sorted(name for name in first if first[name] != second[name])
            raise AssertionError(f"Non-deterministic outputs: {changed}")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
