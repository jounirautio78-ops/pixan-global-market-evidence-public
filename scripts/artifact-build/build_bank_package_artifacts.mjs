import crypto from "node:crypto";
import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  FileBlob,
  PresentationFile,
  SpreadsheetFile,
  Workbook,
} from "@oai/artifact-tool";

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const downloadDir = path.join(repo, "site", "downloads");
const dataDir = path.join(repo, "site", "data");
const sourceDir = path.join(repo, "source");
const seedDir = path.join(repo, "scripts", "artifact-build", "seeds", "v17");
const qaDir = path.join(repo, "tmp", "bank-v32", "qa");
const renderRoot = path.join(repo, "tmp", "bank-v32", "renders");
const releaseVersion = "2026.07.28-32";
const releaseId = "2026-07-28-daily-evidence-package-v32";
const releaseDate = "2026-07-28";
const packageCadence = Object.freeze({
  frequency: "once_daily",
  timeZone: "Asia/Nicosia",
  dashboardMayUpdateIntraday: true,
});
const fhmSourceId = "SE-FHM-PUBLIC-RECORD-RESPONSE-2026-07-24";
const fhmSourceUrl = "https://www.folkhalsomyndigheten.se/regler-och-tillsyn/tobak-och-nikotinprodukter-regler-for-tillverkning-handel-och-hantering/elektroniska-cigaretter-och-pafyllningsbehallare-sa-foljer-du-reglerna/";
const swedenStructureBasis = "official_registration_structure_count_not_sales_or_market_value";
const swedenStructureMetrics = [
  "reporting_entities_count",
  "notified_products_count",
  "active_products_count",
  "withdrawn_products_count",
];
const swedenStructureSuffixByMetric = new Map([
  ["reporting_entities_count", "REPORTING-ENTITIES"],
  ["notified_products_count", "NOTIFIED-PRODUCTS"],
  ["active_products_count", "ACTIVE-PRODUCTS"],
  ["withdrawn_products_count", "WITHDRAWN-PRODUCTS"],
]);
const expectedMarketCounts = {
  observations: 84,
  sources: 24,
  official: 75,
  officialMarketMeasures: 39,
  swedenRegisterStructure: 36,
};
const artifactToolPackageUrl = new URL("../package.json", import.meta.resolve("@oai/artifact-tool"));
const artifactToolPackage = JSON.parse(await fs.readFile(artifactToolPackageUrl, "utf8"));
if (
  artifactToolPackage.name !== "@oai/artifact-tool"
  || !/^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$/.test(String(artifactToolPackage.version ?? ""))
) {
  throw new Error("Unable to resolve the active @oai/artifact-tool package version");
}
const artifactToolVersion = artifactToolPackage.version;
const publicDeckNames = Object.freeze(["short", "large"]);

const seedPaths = [
  "scripts/artifact-build/seeds/v17/pixan-bank-deck-short-en.pptx",
  "scripts/artifact-build/seeds/v17/pixan-bank-deck-large-en.pptx",
  "scripts/artifact-build/seeds/v17/pixan-bank-evidence-register-en.xlsx",
  "scripts/artifact-build/seeds/v17/pixan-bank-deck-short-fi.pptx",
  "scripts/artifact-build/seeds/v17/pixan-bank-deck-large-fi.pptx",
  "scripts/artifact-build/seeds/v17/pixan-bank-evidence-register-fi.xlsx",
];

const DECK_SOURCE_URLS = [
  "https://register.epo.org/application?number=EP14836345&lng=en&tab=main",
  "https://data.epo.org/publication-server/rest/v1.2/patents/EP3032975NWB2/document.pdf",
  "https://www.rechtsprechung-im-internet.de/jportal/?quelle=jlink&docid=JURE269032275&psml=bsjrsprod.psml",
  "https://www.gesetze-bayern.de/Content/Document/Y-300-Z-BECKRS-B-2026-N-14206",
  "https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2024",
  "https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return",
  "https://www.health.govt.nz/system/files/2024-12/2024-annual-returns-user-guide.pdf",
  "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010007101",
  "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010008001",
  "https://www23.statcan.gc.ca/imdb/p2SV.pl?Function=getSurvey&Id=1544050",
  "https://www23.statcan.gc.ca/imdb/p2SV.pl?Function=getSurvey&SDDS=2008",
  "https://www23.statcan.gc.ca/imdb/p2SV.pl?Function=getSurvey&SDDS=2406",
  "https://www150.statcan.gc.ca/n1/pub/36-28-0001/2025004/article/00001-eng.pdf",
  "https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures",
  "https://www.who.int/data/gho/info/gho-odata-api",
  "https://uncomtrade.org/docs/un-comtrade-api/",
  "https://www.podatki.gov.pl/akcyza/stawki-podatkowe/",
  "https://www.gov.pl/web/chemical/notification-of-electronic-cigarettes-and-refill-containers",
  "https://www.customs.govt.nz/about-us/news/important-notices-archive/important-notices-archive-2023/reminder-classification-of-vaping-devices-and-similar",
  "https://www.ftc.gov/reports/e-cigarette-report-2021",
  fhmSourceUrl,
  "https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10010907",
  "https://www.health.belgium.be/en/organisation-policy/legislation-policy-documents/e-cigarette-notification-eu-ceg-belgian-guidelines",
  "https://www.lachambre.be/doc/CCRI/html/56/ic041x.html",
  "https://www.bazg.admin.ch/dam/en/sd-web/GljEzThGISer/Tobacco%20tax.pdf",
  "https://douanes.public.lu/fr/support/faq/e-liquides.html",
  "https://www.helsedirektoratet.no/veiledere/tobakksskadeloven/e-sigaretter",
  "https://www.adm.gov.it/portale/documents/20182/261920520/Libro+blu+2024+-+Relazione.pdf/e46989ce-b39f-a404-3b4b-2af3196cba43",
  "https://www.wipo.int/en/web/ip-financing",
];

const SOURCE_METADATA = new Map([
  [
    "https://www.ftc.gov/reports/e-cigarette-report-2015-2018",
    ["US-FTC-E-CIGARETTE-REPORT-2015-2018", "Federal Trade Commission", "official_report"],
  ],
  [
    "https://www.ftc.gov/reports/e-cigarette-report-2021",
    ["US-FTC-E-CIGARETTE-REPORT-2021", "Federal Trade Commission", "official_report"],
  ],
  [
    "https://www.un.org/en/about-us/member-states",
    ["UN-MEMBER-STATES", "United Nations", "official_reference"],
  ],
  [
    "https://www.un.org/en/about-us/non-member-states",
    ["UN-NON-MEMBER-STATES", "United Nations", "official_reference"],
  ],
  [
    fhmSourceUrl,
    [fhmSourceId, "Public Health Agency of Sweden", "official_reference"],
  ],
]);

const FI_HEADERS = [
  "Väite",
  "Dia/osio",
  "Todiste",
  "Lähde",
  "Päivämäärä",
  "Laskentatapa",
  "Oletukset",
  "Luottamustaso",
  "Puutteet / tarvittava lisänäyttö",
];
const EN_HEADERS = [
  "Claim",
  "Slide/section",
  "Evidence",
  "Source",
  "Date",
  "Calculation method",
  "Assumptions",
  "Confidence",
  "Gaps / additional evidence needed",
];

const EUR_EQUIVALENT_HEADERS = {
  fi: [
    "Tietuetyyppi",
    "Tunniste",
    "Erä / komponentti",
    "Maa / maantiede",
    "Vuosi",
    "Periodi",
    "Alkuperäinen määrä",
    "Valuutta",
    "ECB-kurssi (valuuttayksikköä / EUR)",
    "EUR-vasta-arvo (täysi tarkkuus)",
    "Rate ID",
    "ECB-lähde URL",
    "Tila",
    "Syy / menetelmä",
  ],
  en: [
    "Record type",
    "Record ID",
    "Item / component",
    "Country / geography",
    "Year",
    "Period",
    "Original amount",
    "Currency",
    "ECB rate (currency units / EUR)",
    "EUR equivalent (full precision)",
    "Rate ID",
    "ECB source URL",
    "Status",
    "Reason / method",
  ],
};

const EUR_EQUIVALENT_SHEET_NAMES = {
  fi: "Eurovastineet",
  en: "EUR equivalents",
};

const COLORS = {
  navy: "#071A2B",
  blue: "#0D5F86",
  teal: "#00A4A6",
  white: "#FFFFFF",
  ink: "#182935",
  muted: "#5B6B75",
  line: "#CBD8DE",
  pale: "#EAF3F6",
  paleTeal: "#E3F6F3",
  paleGold: "#FFF0CB",
  paleRed: "#F8DADA",
  paleGreen: "#D9EDE7",
};

const deckUpdates = {
  fi: {
    short: {
      shapes: {
        "sh/ozy1ofad": "Rahoitusteesi perustuu näyttöön",
        "sh/doj29oba": `Julkinen riippumaton evidenssikooste · ${releaseVersion} · ${releaseDate} · Lähteet: World Bank; Statistics Canada; Health Canada; NZ Ministry of Health; Sejm; FHM; FTC; ADM`,
        "sh/0ba143al": "Globaali markkina-arvo ei ole vielä tuettu",
        "sh/ih8ju9sn": "195",
        "sh/kbm987y5": "578 WB-havaintoa · 39 markkinamittaria + 36 Ruotsin FHM-lukua",
        "sh/i94r6xgz": "274,180 milj. NZD",
        "sh/jadsz2xk": "Uusi-Seelanti 2024: tunnistettu AIS/AVP-summa",
        "sh/v6tsv2xo": "Uusi-Seelanti läpäisee 7/10: D5 hylätty, D8 ja D10 avoinna. Ei hyväksytty; donor-portti 0/3.",
        "sh/p0batw72": "Menetelmäkontrolli 28 / 0 / 15 / 152; 5 uutta maasuunnitelmaa, ei myyntiä. Belgia ≈83 333 litraa (9 kk; ei retail); Italia 84,31 milj. EUR PLI-veroa (ei retail). Kanada retail 1,219160 mrd CAD ja toimitukset 1,160754 mrd CAD; FTC 2,763 mrd USD. Donor 0/3.",
      },
    },
    medium: {
      shapes: {
        "sh/ozy1ofad": "Ongelma on evidenssissä ja teknologiassa",
        "sh/d0jax03i": "Ratkaisu ohjaa tehoa resistanssin perusteella",
        "sh/0ba143al": "IP-ydin on dokumentoitu; maapeitto avoin",
        "sh/cf2tcr61": "Tekninen ero on patenttivaatimuksissa",
        "sh/dcbud0ra": "Asiakkuus vaatii kolmen ostajaryhmän validoinnin",
        "sh/cbu58j2h": "Kaupallistaminen etenee näyttöporttien kautta",
        "sh/ml07i9sv": `Julkinen riippumaton evidenssikooste · ${releaseVersion} · ${releaseDate} · Lähteet: Statistics Canada; Market-values; FHM; FTC; IMARC; GVR; Fortune; European Commission`,
        "sh/zi98nu94": "Markkinakoko on haarukka — ei yksi luku",
        "sh/pc76hkr2": "39 + 36",
        "sh/h4bupgn6": "39 markkinamittaria 7 maasta + 36 Ruotsin FHM-rekisterilukua; ei myyntiä",
        "sh/v2tcn650": "274,180 milj. NZD",
        "sh/u1kbu1ov": "Uusi-Seelanti 2024: tunnistettu AIS/AVP-summa",
        "sh/i54bylor": "Uusi-Seelanti läpäisee 7/10: D5 hylätty, D8 ja D10 avoinna. Ei hyväksytty; donor-portti 0/3.",
        "sh/cbe5g3ih": "Kanada 2024: retail 1,219160 mrd CAD; toimitukset 1,160754 mrd CAD. Saman kyselyn kuukausireitti eroaa 1 000 CAD. Kanada 7/10; D5/D7/D10 avoinna. Ei summata.",
      },
      tables: {
        "tb/nq547y9g": [[3, 2, "39 markkinamittaria 7 maasta + 36 Ruotsin FHM-rekisterilukua; ei myyntiä"]],
        "tb/rexkf2d4": [[1, 2, "0/3 retail-luovuttajaa; 5 ehdokasta jäi D1–D10-portin ulkopuolelle"]],
      },
    },
    large: {
      shapes: {
        "sh/ozy1ofad": "Rahoitettavuus on mahdollisuus, ei johtopäätös",
        "sh/0ba143al": "Todennusketju katkeaa ennen kassavirtaa",
        "sh/cf2tcr61": "Patentoitu ratkaisu ohjaa tehoa resistanssitiedolla",
        "sh/dcbud0ra": "IP-historian ydintapahtumat ovat jäljitettävissä",
        "sh/g72x4zyd": "Patenttiperhe: 22 julkaisua, maapeitto avoin",
        "sh/0f2lgnmp": "195 maan pohja: 578 WB-havaintoa; reitit 28 / 0 / 15 / 152; ei myyntiä",
        "sh/4felwzu5": `Julkinen riippumaton evidenssikooste · ${releaseVersion} · ${releaseDate} · Lähteet: Market-values model; Method-route control; Readiness ja donorCandidates`,
        "sh/wbydknq1": "Kanada 2024: vahva piste-estimaatti, 7/10",
        "sh/5grehs7i": `Julkinen riippumaton evidenssikooste · ${releaseVersion} · ${releaseDate} · Lähteet: Statistics Canada; Health Canada 2024`,
        "sh/ehwvat8n": "1,219160 mrd CAD",
        "sh/c3e1gjyd": "retail · 822,58 milj. EUR",
        "sh/a1wze9g7": "1,160754 mrd CAD",
        "sh/b2507exs": "toimitukset · 783,18 milj. EUR",
        "sh/ls7idofu": "1 000 CAD",
        "sh/y5wjitgj": "kuukausi–kvartaali-ero",
        "sh/z650byxo": "Retail ylittää toimitukset 58,406 milj. CAD eli 5,03 %, mutta jäännös ei ole kate tai markkinahaarukka. D8 on suljettu virallisella veroperustalla.",
        "sh/hsvy50re": "Kanada läpäisee 7/10. D5: NAICS 459993/459999 -peitto. D7: tarkka vuositason virheraja puuttuu. D10: eri tapahtumatasojen silta on täsmäyttämättä.",
        "sh/9kby1g7m": "Saksan malli näyttää herkkyyden, ei myyntiä",
        "sh/mpgj6t8j": "Ei havaittua myyntiä. Laskelma käyttää vuoden 2025 alustavaa verotettua nestemäärää ja kolmea verkkokaupan vuoden 2026 hintaa. Rajattu tuotejakauma ja poikkeava ajankohta pitävät luottamustason matalana.",
        "sh/gbedwfmx": "Globaalit arviot ovat ristiintarkistus",
        "sh/hsn2l4bu": "Maailmanestimaatti vaatii vähintään 3 donoria",
        "sh/rq50vmp8": "Asiakassegmentit ovat vielä hypoteeseja",
        "sh/7a18rydc": "Tuotevalidointi tarvitsee katkeamattoman ketjun",
        "sh/8jup8rad": "Ensimmäisen donorin 90 päivän sulkemissprintti",
        "sh/5gbupcrm": "Uusi-Seelanti: ministeriön D5/D8-vahvistus ja riippumaton D10-silta. Kanada: StatCanin D5/D7-vahvistus.",
        "sh/t4butcri": "Puola: 2020–2023 virallinen e-nestevirta ja vuoden 2025 laite-/osasarjaverosilta; retail-arvo ja D1–D10-silta puuttuvat.",
        "sh/98ruxsre": "Viiden maan normalisointi: Belgia ≈83 333 litraa (9 kk; ei retail) ja Italia 84,31 milj. EUR PLI-veroa (ei retail). Menetelmät pidetään erossa myynnistä; Euromonitor 0/6.",
        "sh/218rq9kr": "Hyväksy donor vain, jos kaikki kymmenen ehtoa läpäisevät. Muuten 0/3 ja not_computed säilyvät.",
        "sh/21gnuts7": `Julkinen riippumaton evidenssikooste · ${releaseVersion} · ${releaseDate} · Lähteet: World Bank; Statistics Canada; Health Canada; New Zealand Ministry of Health; Destatis; Vero; Sejm; FHM; FTC; ADM`,
        "sh/q5wjelsz": "•  EPO:n muutettu EP3032975B2 ja Saksan kaksi virallista ratkaisua muodostavat oikeusnäytön ankkurin.\n•  195 maan menetelmäkontrolli erottaa 28 tarkistettua suunnitelmaa, 0 lähdepolkua, 15 EU TPD -mallia ja 152 rajaamatonta proxy-reittiä; mikään ei avaa 0/3 donor-porttia.\n•  Rahoitusrakenne tarvitsee kansalliset oikeudet, claim-mapped sales -sillan, kassavirran ja riippumattoman arvonmäärityksen.",
        "sh/bq9orito": "39 markkinamittaria ja 36 Ruotsin FHM-lukua; menetelmäkontrolli 28 / 0 / 15 / 152",
        "sh/6hw3y9sb": "Uusi-Seelanti 7/10: D5 hylätty, D8 ja D10 avoinna. Kaikki 5 ehdokasta ovat ulkona; donor-portti 0/3.",
        "sh/rip4retw": "•  Uuden-Seelannin tunnistettu AIS/AVP-summa 274,180 milj. NZD jakautuu kulutustarvikkeisiin 189 402 451,96, laitteisiin/hardwareen 84 709 409,85 ja sekajärjestelmiin 68 548,40 NZD.\n•  Viereiset 2 137 085,24 ja ratkaisemattomat 4 367 017,37 NZD rajataan pois. Maa läpäisee 7/10; D5 hylätään sekä D8 ja D10 ovat avoimia.\n•  Erillinen 533,7–731,2 milj. NZD RPS-herkkyys on tuettu malli, ei havaittu kansallinen arvo. Donor-portti pysyy 0/3:ssa.",
        "sh/x8japo3e": "Päiväpaketti muodostetaan enintään kerran Asia/Nicosia-kalenteripäivässä; dashboard voi päivittyä päivän aikana.",
      },
      tables: {
        "tb/m983m983": [
          [0, 2, "Virallinen havainto / tuettu malli"],
          [1, 1, "2019–2025"],
          [1, 2, "StatsCan retail 2024: 1,219160 mrd CAD / 822,58 milj. EUR; kuukausireitti +1 000 CAD. Kanada 7/10; D5, D7 ja D10 avoimia"],
          [4, 2, "tunnistettu AIS/AVP-vaping-summa 274,180 milj. NZD; kulutustarvikkeet 189,402 + laitteet/hardware 84,709 + sekajärjestelmät 0,069 milj. NZD. NZ 7/10; D5 hylätty, D8/D10 avoinna"],
          [5, 1, "2020–2023 / 2025"],
          [5, 2, "e-nestevirta 1 451 529 → 805 441 litraa; verosilta 4 382 500 laitteelle + 62 500 osasarjalle. Ei retail-arvoa tai donoria"],
          [6, 0, "Yhdysvallat"],
          [6, 1, "2015–2021"],
          [6, 2, "FTC: suljettujen järjestelmien ja kertakäyttötuotteiden raportoitu myynti 2,763 mrd USD vuonna 2021; valmistajaraportointia"],
        ],
      },
    },
  },
  en: {
    short: {
      shapes: {
        "sh/doj29oba": `Independent public evidence summary · ${releaseVersion} · ${releaseDate} · Sources: World Bank; Statistics Canada; Health Canada; NZ Ministry of Health; Sejm; FHM; FTC; ADM`,
        "sh/0ba143al": "Market evidence is transparent; a global value is not yet supported",
        "sh/ih8ju9sn": "195",
        "sh/kbm987y5": "578 WB records; 39 market measures + 36 Swedish FHM register counts; not sales",
        "sh/i94r6xgz": "NZD 274.180m",
        "sh/jadsz2xk": "New Zealand 2024: identified AIS/AVP subtotal",
        "sh/v6tsv2xo": "New Zealand passes 7/10: D5 failed; D8 and D10 open. Not accepted; the donor gate remains 0/3.",
        "sh/p0batw72": "Method control 28 / 0 / 15 / 152; 5 new country plans, not sales. Belgium ≈83,333 litres (9 months; not retail); Italy EUR 84.31m PLI tax (not retail). Canada retail CAD 1.219160bn and shipments CAD 1.160754bn; FTC USD 2.763bn. Donor 0/3.",
      },
    },
    medium: {
      shapes: {
        "sh/ml07i9sv": `Independent public evidence summary · ${releaseVersion} · ${releaseDate} · Sources: Statistics Canada; Market-values; FHM; FTC; IMARC; GVR; Fortune; European Commission`,
        "sh/zi98nu94": "Market size remains a range — not a single value",
        "sh/pc76hkr2": "39 + 36",
        "sh/h4bupgn6": "39 market measures across 7 countries + 36 Swedish FHM register counts; not sales",
        "sh/v2tcn650": "NZD 274.180m",
        "sh/u1kbu1ov": "New Zealand 2024: identified AIS/AVP subtotal",
        "sh/i54bylor": "New Zealand passes 7/10: D5 failed; D8 and D10 open. Not accepted; the donor gate remains 0/3.",
        "sh/cbe5g3ih": "Canada 2024: retail CAD 1.219160bn; shipments CAD 1.160754bn. Same-survey monthly retail differs by CAD 1,000. Canada 7/10; D5/D7/D10 open. Do not sum.",
      },
      tables: {
        "tb/nq547y9g": [[3, 2, "39 market measures across 7 countries + 36 Swedish FHM register counts; not sales"]],
        "tb/rexkf2d4": [[1, 2, "0/3 retail-value donors; 5 candidates remain outside the D1–D10 gate"]],
      },
    },
    large: {
      shapes: {
        "sh/0f2lgnmp": "195-country open base: 578 WB records; method control 28 / 0 / 15 / 152; not sales",
        "sh/4felwzu5": `Independent public evidence summary · ${releaseVersion} · ${releaseDate} · Sources: Market-values model; Method-route control; Readiness and donorCandidates`,
        "sh/wbydknq1": "Canada 2024: strong point estimate, 7/10",
        "sh/5grehs7i": `Independent public evidence summary · ${releaseVersion} · ${releaseDate} · Sources: Statistics Canada; Health Canada 2024`,
        "sh/ehwvat8n": "CAD 1.219160bn",
        "sh/c3e1gjyd": "retail · EUR 822.58m",
        "sh/a1wze9g7": "CAD 1.160754bn",
        "sh/b2507exs": "shipments · EUR 783.18m",
        "sh/ls7idofu": "CAD 1,000",
        "sh/y5wjitgj": "monthly–quarterly gap",
        "sh/z650byxo": "Retail is CAD 58.406m, or 5.03%, above shipments. The residual is not margin or a market range; official tax evidence closes D8.",
        "sh/hsvy50re": "Canada passes 7/10. D5: NAICS 459993/459999 coverage. D7: exact annual error boundary missing. D10: different transaction stages remain unreconciled.",
        "sh/hk3ipcr6": "Manufacturer: licence, freedom to operate or settlement.\nTechnology provider: integrable function or legal position.\nFinancier or buyer: controllable, realisable cash flow and downside protection.",
        "sh/8jup8rad": "First-donor conversion sprint · next 90 days",
        "sh/5gbupcrm": "New Zealand: Ministry D5/D8 confirmation and an independent D10 bridge. Canada: Statistics Canada D5/D7 confirmation.",
        "sh/t4butcri": "Poland: official 2020–2023 e-liquid flow and a 2025 device/component tax bridge; retail value and a D1–D10 bridge remain missing.",
        "sh/98ruxsre": "Five-country normalisation: Belgium ≈83,333 litres (9 months; not retail) and Italy EUR 84.31m PLI tax (not retail). Methods stay separate from sales; Euromonitor 0/6.",
        "sh/218rq9kr": "Accept a donor only if all ten criteria pass. Otherwise retain 0/3 and not_computed.",
        "sh/21gnuts7": `Independent public evidence summary · ${releaseVersion} · ${releaseDate} · Sources: World Bank; Statistics Canada; Health Canada; New Zealand Ministry of Health; Destatis; Vero; Sejm; FHM; FTC; ADM`,
        "sh/q5wjelsz": "•  The amended EP3032975B2 and two official German decisions anchor the legal evidence.\n•  The 195-country method control separates 28 reviewed plans, 0 source leads, 15 EU TPD patterns and 152 unscoped proxy routes; none unlocks the 0/3 donor gate.\n•  A financing structure requires national rights, a claim-mapped-sales bridge, cash flow and an independent valuation.",
        "sh/bq9orito": "39 market measures and 36 Swedish FHM register counts; method control 28 / 0 / 15 / 152",
        "sh/6hw3y9sb": "New Zealand is 7/10: D5 failed; D8 and D10 open. All 5 candidates remain outside; the donor gate is 0/3.",
        "sh/rip4retw": "•  New Zealand's identified AIS/AVP subtotal of NZD 274.180m comprises NZD 189,402,451.96 consumables, NZD 84,709,409.85 devices/hardware and NZD 68,548.40 mixed systems.\n•  NZD 2,137,085.24 adjacent and NZD 4,367,017.37 unresolved rows are excluded. New Zealand passes 7/10; D5 fails and D8/D10 remain open.\n•  The separate NZD 533.7–731.2m RPS sensitivity remains a supported model, not observed national value. The donor gate remains 0/3.",
        "sh/x8japo3e": "The daily package is generated at most once per Asia/Nicosia calendar day; the dashboard may update intraday.",
      },
      tables: {
        "tb/m983m983": [
          [0, 2, "Official observation / supported model"],
          [1, 1, "2019–2025"],
          [1, 2, "StatsCan retail 2024: CAD 1.219160bn / EUR 822.58m; monthly route +CAD 1,000. Canada 7/10; D5, D7 and D10 open"],
          [4, 2, "identified AIS/AVP vaping subtotal NZD 274.180m: consumables 189.402 + devices/hardware 84.709 + mixed systems 0.069m. NZ 7/10; D5 failed, D8/D10 open"],
          [5, 1, "2020–2023 / 2025"],
          [5, 2, "e-liquid flow 1,451,529 → 805,441 litres; tax bridge for 4,382,500 devices + 62,500 component sets. Not retail value or a donor"],
          [6, 0, "United States"],
          [6, 1, "2015–2021"],
          [6, 2, "FTC: reported cartridge-system-plus-disposable sales reached USD 2.763bn in 2021; manufacturer reporting"],
        ],
      },
    },
  },
};

const registerAdditions = {
  fi: [
    [
      "Uuden-Seelannin erillinen vuoden 2024 RPS-vähittäisherkkyys on tuettu malli: 533 662 383,68–731 175 792,50 NZD ja perusskenaario 641 811 687,89 NZD.",
      "Markkinakoko",
      "Matalan, perus- ja korkean skenaarion yhdistetyt arvot ovat 533 662 383,68 / 641 811 687,89 / 731 175 792,50 NZD. Malli yhdistää erikoisvähittäiskaupan ankkurin yleisvähittäiskaupan määrä- ja hintamalliin.",
      "https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2024 ; source/NZ_2024_RPS_RETAIL_VALUE_SENSITIVITY.md ; source/NZ_2024_DONOR_CLOSURE_PACK.md",
      "2026-07-26",
      "Matala (täsmällisten rivien deduplikointi): 258 327 110,88 + 275 335 272,80 = 533 662 383,68 NZD. Perus (raportoidut/raakrivit): 274 180 410,21 + 367 631 277,68 = 641 811 687,89 NZD. Korkea (raportoidut/raakrivit): 274 180 410,21 + 456 995 382,29 = 731 175 792,50 NZD.",
      "GST-käsittely, palautusten täydellisyys ja riippumaton täsmäytys ovat avoimia; ilmoittajien toimitusketjutason arvot on jätetty pois.",
      "Tuettu",
      "Ei havaittu kansallinen arvo eikä hyväksytty donor. Tarvitaan viranomaisen scope- ja GST-vahvistus sekä riippumaton toisto.",
    ],
    [
      "Vuoden 2023 kuuden virallisen työkirjan uusi numeerinen rekonstruktio on jätetty tarkoituksella laskematta.",
      "Markkinakoko",
      "Ministeriön julkaisema koonti on vähintään 374 milj. NZD ja 2 570 ilmoitusta. Se sisältää kaikki ilmoitettavat tuotteet, myös heated tobacco -tuotteet, ja ministeriö varoittaa laadusta.",
      "https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2023 ; source/NZ_2023_ANNUAL_RETURNS_FAIL_CLOSED.md",
      "2026-07-26",
      "Kuusi virallista tiedostoa on eheystiivistetty; kaikki uusi laskenta palauttaa tilan not_computed.",
      "Tuoterajaus, määräkentät, duplikaatit, toimitusketjutaso, veroperusta ja riippumaton täsmäytys ovat ratkaisematta.",
      "Vahvistettu",
      "Vuoden 2023 uusi vaping-only-arvo puuttuu, eikä 374 milj. NZD:tä saa nimetä puhtaaksi sähkötupakkamarkkinaksi.",
    ],
    [
      "FTC:n virallisista taulukoista johdettu suljettujen järjestelmien ja kertakäyttötuotteiden raportoitu myynti oli 2 763 284 338 USD vuonna 2021.",
      "Markkinakoko",
      "Seitsemän vuoden 2015–2021 sarja on laskettu summaamalla vuosittain cartridge-system- ja disposable-rivit. Vuoden 2020 korjattu taulukko kattaa viisi aiempaa raportoijaa sekä kolme neljästä uudesta; vuosi 2021 kattaa kaikki yhdeksän vastaanottajaa.",
      "https://www.ftc.gov/reports/e-cigarette-report-2015-2018 ; https://www.ftc.gov/reports/e-cigarette-report-2021 ; source/US_FTC_2015_2021_REPORTED_SALES.md",
      "2021",
      "FTC-taulukoiden cartridge systems + disposable e-cigarettes -myynnin vuosittainen summa.",
      "Raportoijajoukko muuttuu, open-system-tuotteet puuttuvat, taso on valmistajaraportointi ja veroperustaa ei ilmoiteta.",
      "Tuettu",
      "Ei täydellinen kansallinen kuluttajavähittäisarvo eikä hyväksytty donor; tarvitaan avoin POS- tai kuluttajamyyntisarja ja veroperusta.",
    ],
    [
      "Julkinen sivusto erottaa kolme evidenssikaistaa ja estää maailman kokonaisarvon, kun hyväksytty donor-portti on 0/3.",
      "Markkinakoko",
      "Viisi ehdokasta on arvioitu samoilla 10 D1–D10-kriteerillä; yksikään ei ole hyväksytty. Lisäksi alue- ja sääntelytyyppien peittoporttien on läpäistävä tarkistus.",
      "site/data/evidence-lanes.json ; site/data/donor-cockpit.json ; site/data/third-donor-screen.json ; site/data/country-scenarios.json",
      "2026-07-27",
      "Fail-closed-portit: puuttuva tai virheellinen syöte tuottaa tilan not_computed eikä nollaa.",
      "Vain tarkistetut julkiset koontitiedot ja menetelmät ovat julkisella kaistalla; lisensoitu ja yksityinen aineisto eivät siirry repositorioon.",
      "Vahvistettu",
      "Maailmanarvo pysyy laskematta, kunnes vähintään kolme donoria sekä molemmat peittoportit hyväksytään.",
    ],
  ],
  en: [
    [
      "New Zealand's separate supported 2024 RPS retail-sensitivity model is NZD 533,662,383.68–731,175,792.50, with a base case of NZD 641,811,687.89.",
      "Market size",
      "The combined low, base and high cases are NZD 533,662,383.68 / 641,811,687.89 / 731,175,792.50. The model combines the specialist-retailer anchor with a general-retailer quantity-and-price model.",
      "https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2024 ; source/NZ_2024_RPS_RETAIL_VALUE_SENSITIVITY.md ; source/NZ_2024_DONOR_CLOSURE_PACK.md",
      "2026-07-26",
      "Low (exact-row deduplication): NZD 258,327,110.88 + 275,335,272.80 = 533,662,383.68. Base (reported/raw rows): NZD 274,180,410.21 + 367,631,277.68 = 641,811,687.89. High (reported/raw rows): NZD 274,180,410.21 + 456,995,382.29 = 731,175,792.50.",
      "GST treatment, return completeness and independent reconciliation are open; notifier supply-stage values are excluded.",
      "Supported",
      "Not an observed national value or accepted donor. Authority confirmation of scope and GST plus independent reproduction are required.",
    ],
    [
      "The new numerical reconstruction from the six official 2023 workbooks is intentionally not computed.",
      "Market size",
      "The Ministry's published aggregate is at least NZD 374 million and 2,570 returns. It covers all notifiable products, including heated tobacco, and the Ministry warns about data quality.",
      "https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2023 ; source/NZ_2023_ANNUAL_RETURNS_FAIL_CLOSED.md",
      "2026-07-26",
      "Six official files are integrity-hashed; every new computation returns not_computed.",
      "Product scope, quantity fields, duplication, supply-chain level, tax basis and independent reconciliation remain unresolved.",
      "Confirmed",
      "A new 2023 vaping-only value is missing, and NZD 374 million must not be relabelled as a pure vaping market.",
    ],
    [
      "Official FTC tables yield USD 2,763,284,338 of reported cartridge-system-plus-disposable sales in 2021.",
      "Market size",
      "The seven-year 2015–2021 series sums the cartridge-system and disposable rows annually. The corrected 2020 table covers five prior recipients plus three of four new recipients; 2021 covers all nine recipients.",
      "https://www.ftc.gov/reports/e-cigarette-report-2015-2018 ; https://www.ftc.gov/reports/e-cigarette-report-2021 ; source/US_FTC_2015_2021_REPORTED_SALES.md",
      "2021",
      "Annual sum of FTC-table cartridge systems + disposable e-cigarette sales.",
      "The reporting population changes, open-system products are excluded, the level is manufacturer reporting and the tax basis is unstated.",
      "Supported",
      "Not complete national consumer-retail value or an accepted donor; an open POS or consumer-sales series and tax basis are required.",
    ],
    [
      "The public site separates three evidence lanes and blocks a global total while the accepted-donor gate is 0/3.",
      "Market size",
      "Five candidates are assessed against the same ten D1–D10 criteria; none is accepted. The regional and regulatory-archetype coverage gates must also pass.",
      "site/data/evidence-lanes.json ; site/data/donor-cockpit.json ; site/data/third-donor-screen.json ; site/data/country-scenarios.json",
      "2026-07-27",
      "Fail-closed gates: a missing or invalid input returns not_computed rather than zero.",
      "Only reviewed public aggregates and methods enter the public lane; licensed and private material do not enter the repository.",
      "Confirmed",
      "The global value remains uncomputed until at least three donors and both coverage gates are accepted.",
    ],
  ],
};

const v32MethodAndFiscalClaims = {
  fi: [
    [
      "Itävallalla on tarkistettu vuosittaiseen lakisääteiseen myyntiraportointiin ja sähkönestevalmisteveroon perustuva menetelmäsuunnitelma; vähittäismarkkina-arvoa ei ole laskettu.",
      "Markkinakoko / Itävalta",
      "Virallinen reitti edellyttää edellisen vuoden vuosivolyymien raportointia ja vahvistaa sähkönestevalmisteveron alkavan 2026-04-01 tasolla EUR 200 litralta.",
      "source/FIVE_COUNTRY_METHOD_SPRINT_2026-07-27.md (Austria)",
      "2026-07-27",
      "Verolliset litrat = sähkönestekohtainen nettovero / sovellettava EUR 200 litralta 2026-04-01 alkavalla jaksolla.",
      "Sekajaksot erotellaan; vuosiraportointi ja veroinversio ovat vaihtoehtoisia sovitusreittejä, eivät yhteenlaskettavia.",
      "Vahvistettu",
      "Kansallista vuosikoostetta, hintasarjaa, kattavuutta ja vähittäismyynnin sovitusta ei ole saatu; retailValueStatus on not_computed.",
    ],
    [
      "Belgian virallinen osavuosiveroluku tuottaa vain pyöristetyn 9 kuukauden verovolyymi-indikaattorin; se ei ole koko vuoden myynti eikä vähittäismarkkina-arvo.",
      "Markkinakoko / Belgia",
      "Virallinen arviolta EUR 12 500 000 ja verokanta EUR 0,15 per ml vastaavat arviolta 83 333 333 ml eli 83 333 litraa.",
      "source/FIVE_COUNTRY_METHOD_SPRINT_2026-07-27.md (Belgium)",
      "2026-07-27",
      "EUR 12 500 000 / EUR 0,15 per ml = arviolta 83 333 333 ml ≈ 83 333 litraa.",
      "Luku koskee 9 kuukauden jaksoa; varastointi, rajakauppa ja maksujen ajoitus voivat vääristää tulkintaa.",
      "Tuettu",
      "Nettoveronalaisia luovutuksia, koko vuotta, kuluttajamyyntiä, hintaa ja kanavakattavuutta ei ole vahvistettu; 9 kuukauden indikaattoria ei hyväksytä donoriksi.",
    ],
    [
      "Sveitsillä on 2024-10-01 alkanut kahden verokannan menetelmäreitti; vähittäismarkkina-arvoa ei ole laskettu.",
      "Markkinakoko / Sveitsi",
      "Virallinen reitti erottaa kertakäyttötuotteiden CHF 1,00 per ml ja uudelleenkäytettävien nikotiinituotteiden CHF 0,20 per ml; ensimmäinen jakso on 2024-10-01–2024-12-31.",
      "source/FIVE_COUNTRY_METHOD_SPRINT_2026-07-27.md (Switzerland)",
      "2026-07-27",
      "Kertakäyttötuotteiden verollinen ml = luokan nettovero / CHF 1,00; uudelleenkäytettävien nikotiinituotteiden verollinen ml = luokan nettovero / CHF 0,20; litrat = ml / 1 000.",
      "Veroluokat on toimitettava erillään eikä yhdistetylle verolle ole yksikäsitteistä volyymiratkaisua.",
      "Vahvistettu",
      "Luokkakohtaiset nettoverot tai millilitrat, oikaisut, nikotiinittomat täyttönesteet, hinnat ja kuluttajamyynti puuttuvat; retailValueStatus on not_computed.",
    ],
    [
      "Luxemburgilla on 2024-10-01 alkanut valmistevero- ja veromerkkimenetelmä; vähittäismarkkina-arvoa ei ole laskettu.",
      "Markkinakoko / Luxemburg",
      "Virallinen verokanta on EUR 0,12 per ml 2024-10-01 alkaen, ja veromerkit sisältävät nestetilavuuden sekä pakollisen kuluttajahinnan.",
      "source/FIVE_COUNTRY_METHOD_SPRINT_2026-07-27.md (Luxembourg)",
      "2026-07-27",
      "Verolliset litrat = sähkönestekohtainen nettovero / EUR 120 litralta; merkitty kuluttajahintainen arvo = summa(merkitty pakkausmäärä × pakollinen merkitty hinta).",
      "Volyymi- ja veromerkkilaskelmia ei lasketa yhteen; ulkomaan B2B-toimitukset, hävitykset, palautukset ja oikaisut erotellaan.",
      "Vahvistettu",
      "Kansallinen kooste, veromerkkien määrä- ja hintakentät, kuluttajamyynti ja kauden lopullisuus puuttuvat; retailValueStatus on not_computed.",
    ],
    [
      "Norjalla ei ole nykyistä Article 20(7) -vuosimyyntireittiä; vuoden 2026 NOK 5,38 per ml oleva lakisääteinen verokanta ei ole käytännössä voimassa eikä osoita markkina-arvoa.",
      "Markkinakoko / Norja",
      "Virallinen ohje kieltää nikotiinituotteiden kaupallisen tuonnin ja myynnin, eikä uutta TPD-reittiä sovelleta; SSB:n ulkomaankauppatiedot ovat vain tulliproxy.",
      "source/FIVE_COUNTRY_METHOD_SPRINT_2026-07-27.md (Norway)",
      "2026-07-27",
      "Veroinversio sallitaan vain, jos käytännössä voimassa olevat luokkakohtaiset nettotulot saadaan; tulliproxy ei muutu kansalliseksi kuluttajamyynniksi.",
      "Kielto, lakisääteinen verokanta tai puuttuva tietue ei osoita markkinan puuttumista.",
      "Vahvistettu",
      "Nikotiinittomien tuotteiden kuluttajamyynti, millilitrat, hinnat, kotimainen tuotanto, varastot, jälleenvienti ja laittomat kanavat puuttuvat; retailValueStatus on not_computed.",
    ],
    [
      "Italian ADM:n PLI-tuotteiden kulutusverotuotto oli 55 910 871,89 EUR vuonna 2023 ja 84 309 841,41 EUR vuonna 2024; kyse ei ole vähittäismarkkina-arvosta.",
      "Markkinakoko / Italia",
      "ADM:n Libro Blu 2024 -raportin taulukko III.9 näyttää 50,79 prosentin verotuottomuutoksen. Vuonna 2024 verotus laajeni myös PLI-tuotteisiin tarkoitettuihin aromeihin ja verotukseen kohdistui muutoksia, joten prosenttia ei tulkita myynti- tai volyymikasvuksi.",
      "https://www.adm.gov.it/portale/documents/20182/261920520/Libro+blu+2024+-+Relazione.pdf/e46989ce-b39f-a404-3b4b-2af3196cba43 ; source/ITALY_ADM_RESPONSE_BOUNDARY_2026-07-24.md",
      "2026-07-28",
      "Suora taulukkotoisto: 55 910 871,89 EUR vuonna 2023; 84 309 841,41 EUR vuonna 2024; ilmoitettu muutos 50,79 prosenttia.",
      "Verotuotto on fiskaalinen mittari. Sitä ei käännetä litroiksi tai vähittäisarvoksi ilman erillisiä verokantoja, luokkia, oikaisuja ja samaa rajausta.",
      "Vahvistettu",
      "Nikotiini- ja nikotiiniton jako, litrat, laitteet, kuluttajahinta, palautukset, maksujen ajoitus ja rajaukseltaan vertailukelpoinen sarja puuttuvat; Italia ei ole donor.",
    ],
  ],
  en: [
    [
      "Austria has a reviewed method plan based on statutory annual sales reporting and e-liquid excise; no retail market value has been computed.",
      "Market size / Austria",
      "The official route requires annual prior-year volume reporting and confirms e-liquid excise starting on 2026-04-01 at EUR 200 per litre.",
      "source/FIVE_COUNTRY_METHOD_SPRINT_2026-07-27.md (Austria)",
      "2026-07-27",
      "Taxed litres = e-liquid-specific net excise / applicable EUR 200 per litre for the period starting 2026-04-01.",
      "Mixed-rate periods are separated; annual reporting and excise inversion are alternative reconciliation routes, not additive.",
      "Confirmed",
      "No national annual aggregate, price series, coverage evidence or retail reconciliation has been received; retailValueStatus is not_computed.",
    ],
    [
      "Belgium’s official partial-period tax figure yields only a rounded 9 month tax-volume indicator; it is not full-year sales or retail market value.",
      "Market size / Belgium",
      "The official approximate EUR 12,500,000 and EUR 0.15 per ml rate imply approximately 83,333,333 ml or 83,333 litres.",
      "source/FIVE_COUNTRY_METHOD_SPRINT_2026-07-27.md (Belgium)",
      "2026-07-27",
      "EUR 12,500,000 / EUR 0.15 per ml = approximately 83,333,333 ml ≈ 83,333 litres.",
      "The figure covers a 9 month period; stockpiling, cross-border purchases and collection timing may distort interpretation.",
      "Supported",
      "Net releases for consumption, the full year, consumer sell-through, price and channel coverage are unverified; the 9 month indicator is not accepted as a donor.",
    ],
    [
      "Switzerland has a two-rate method route that started on 2024-10-01; no retail market value has been computed.",
      "Market size / Switzerland",
      "The official route separates CHF 1.00 per ml for disposables and CHF 0.20 per ml for reusable nicotine products; the first period is 2024-10-01–2024-12-31.",
      "source/FIVE_COUNTRY_METHOD_SPRINT_2026-07-27.md (Switzerland)",
      "2026-07-27",
      "Disposable taxed ml = category net tax / CHF 1.00; reusable-nicotine taxed ml = category net tax / CHF 0.20; litres = ml / 1,000.",
      "The tax categories must be supplied separately and combined receipts have no unique volume solution.",
      "Confirmed",
      "Category-specific net tax or millilitres, adjustments, reusable nicotine-free liquids, prices and sell-through are missing; retailValueStatus is not_computed.",
    ],
    [
      "Luxembourg has an excise and fiscal-mark method starting on 2024-10-01; no retail market value has been computed.",
      "Market size / Luxembourg",
      "The official rate is EUR 0.12 per ml from 2024-10-01, and fiscal marks carry liquid volume and mandatory consumer price.",
      "source/FIVE_COUNTRY_METHOD_SPRINT_2026-07-27.md (Luxembourg)",
      "2026-07-27",
      "Taxed litres = e-liquid-specific net excise / EUR 120 per litre; marked consumer-price value = sum(marked pack quantity × mandatory marked price).",
      "The volume and fiscal-mark calculations are not additive; foreign B2B dispatches, destruction, refunds and corrections are separated.",
      "Confirmed",
      "The national aggregate, fiscal-mark quantity and price fields, sell-through and period finality are missing; retailValueStatus is not_computed.",
    ],
    [
      "Norway has no current Article 20(7) annual-sales route; the 2026 statutory NOK 5.38 per ml rate has no practical effect and does not establish market value.",
      "Market size / Norway",
      "Official guidance prohibits commercial import and sale of nicotine products and the new TPD route does not apply; SSB external-trade data are only a customs proxy.",
      "source/FIVE_COUNTRY_METHOD_SPRINT_2026-07-27.md (Norway)",
      "2026-07-27",
      "Excise inversion is permitted only if category-specific net receipts with practical effect are supplied; the customs proxy does not become national consumer sell-through.",
      "A prohibition, statutory tax rate or missing record does not establish the absence of a market.",
      "Confirmed",
      "Nicotine-free sell-through, millilitres, prices, domestic production, inventories, re-exports and illicit channels are missing; retailValueStatus is not_computed.",
    ],
    [
      "Italian ADM PLI consumption-tax receipts were EUR 55,910,871.89 in 2023 and EUR 84,309,841.41 in 2024; this is not retail market value.",
      "Market size / Italy",
      "Table III.9 of ADM’s Libro Blu 2024 reports a 50.79 percent tax-receipt change. In 2024 the tax scope expanded to aromas intended for PLI products and taxation changed, so the percentage is not interpreted as sales or volume growth.",
      "https://www.adm.gov.it/portale/documents/20182/261920520/Libro+blu+2024+-+Relazione.pdf/e46989ce-b39f-a404-3b4b-2af3196cba43 ; source/ITALY_ADM_RESPONSE_BOUNDARY_2026-07-24.md",
      "2026-07-28",
      "Direct table transcription: EUR 55,910,871.89 in 2023; EUR 84,309,841.41 in 2024; reported change 50.79 percent.",
      "Tax receipts are a fiscal measure. They are not inverted into litres or retail value without separate rates, categories, adjustments and a like-for-like scope.",
      "Confirmed",
      "Nicotine and nicotine-free split, litres, devices, consumer prices, refunds, cash timing and a scope-comparable series are missing; Italy is not a donor.",
    ],
  ],
};

function sha256(filePath) {
  return crypto.createHash("sha256").update(fsSync.readFileSync(filePath)).digest("hex");
}

function sha256Text(value) {
  return crypto.createHash("sha256").update(String(value)).digest("hex");
}

function calendarDateInTimeZone(value, timeZone) {
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) throw new Error(`Invalid release timestamp: ${value}`);
  const parts = new Intl.DateTimeFormat("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone,
  }).formatToParts(date);
  const byType = new Map(parts.map((part) => [part.type, part.value]));
  return `${byType.get("year")}-${byType.get("month")}-${byType.get("day")}`;
}

async function assertDailyBuildWindow() {
  const changelog = JSON.parse(await fs.readFile(path.join(dataDir, "changelog.json"), "utf8"));
  const release = changelog.releases?.[0];
  if (typeof release?.publishedAt !== "string") {
    throw new Error("The public changelog lacks a valid target release timestamp");
  }
  const targetDate = calendarDateInTimeZone(release.publishedAt, packageCadence.timeZone);
  if (changelog.asOf !== targetDate) {
    throw new Error("The target release and changelog asOf are on different Asia/Nicosia dates");
  }

  let existingManifest;
  try {
    existingManifest = JSON.parse(
      await fs.readFile(path.join(dataDir, "bank-package-manifest.json"), "utf8"),
    );
  } catch (error) {
    if (error?.code !== "ENOENT") throw error;
    existingManifest = null;
  }
  if (existingManifest) {
    const existingPublishedAt = existingManifest?.release?.publishedAt;
    if (typeof existingPublishedAt !== "string") {
      throw new Error("Existing bank-package manifest lacks a valid release timestamp");
    }
    const existingDate = calendarDateInTimeZone(
      existingPublishedAt,
      packageCadence.timeZone,
    );
    if (existingDate === targetDate) {
      throw new Error(
        `Bank-package artifacts may be generated at most once per ${packageCadence.timeZone} calendar day; ${targetDate} already has a package snapshot.`,
      );
    }
    if (existingDate > targetDate) {
      throw new Error("Existing bank-package snapshot is newer than the target artifact release");
    }
  }
  if (
    release.id !== releaseId
    || release.version !== releaseVersion
  ) {
    throw new Error("The public changelog is not locked to the target artifact release");
  }
}

function deckSeedPath(language, deckName) {
  return path.join(seedDir, `pixan-bank-deck-${deckName}-${language}.pptx`);
}

function workbookSeedPath(language) {
  return path.join(seedDir, `pixan-bank-evidence-register-${language}.xlsx`);
}

function fxRateMap(fxData) {
  return new Map((fxData?.rates ?? []).map((rate) => [
    `${rate.currency}:${rate.year}`,
    rate,
  ]));
}

function validateReviewedFx(publicFx, sourceFx) {
  if (JSON.stringify(publicFx) !== JSON.stringify(sourceFx)) {
    throw new Error("Public FX data differs from the reviewed source");
  }
  if (
    publicFx?.schemaVersion !== "1.0"
    || publicFx?.targetCurrency !== "EUR"
    || publicFx?.provider?.name !== "European Central Bank"
    || publicFx?.calculationPolicy?.formulaMachine
      !== "eur_equivalent = original_amount / currency_units_per_eur"
    || publicFx?.calculationPolicy?.missingRateStatus !== "not_computed"
  ) {
    throw new Error("Reviewed FX control is invalid");
  }
  const seen = new Set();
  for (const rate of publicFx.rates ?? []) {
    const key = `${rate.currency}:${rate.year}`;
    const parsed = new URL(rate.sourceUrl);
    if (
      seen.has(key)
      || rate.rateId !== `ECB-EXR-A-${rate.currency}-EUR-SP00-A-${rate.year}`
      || rate.rateType !== "annual_average_reference_rate"
      || !Number.isFinite(Number(rate.currencyUnitsPerEur))
      || Number(rate.currencyUnitsPerEur) <= 0
      || parsed.protocol !== "https:"
      || parsed.hostname !== "data-api.ecb.europa.eu"
    ) {
      throw new Error(`Invalid reviewed FX rate ${key}`);
    }
    seen.add(key);
  }
}

function deckSourceNotes(fxData) {
  const rates = fxRateMap(fxData);
  const nzRate = rates.get("NZD:2024");
  const usRate = rates.get("USD:2021");
  const cadRate = rates.get("CAD:2024");
  if (!nzRate || !usRate || !cadRate) throw new Error("Deck FX source rates are unavailable");
  const sourceUrls = [
    ...DECK_SOURCE_URLS,
    fxData.provider.datasetUrl,
    fxData.provider.methodologyUrl,
    nzRate.sourceUrl,
    usRate.sourceUrl,
    cadRate.sourceUrl,
  ];
  return [
    "[Sources]",
    ...[...new Set(sourceUrls)].map((url) => `- ${url}`),
    "",
    "[FX methodology]",
    `- ${fxData.calculationPolicy.formulaEn}`,
    `- ${fxData.calculationPolicy.originalValueRuleEn}`,
    `- NZD 2024: ${nzRate.rateId} · ${nzRate.currencyUnitsPerEur} currency units per EUR`,
    `- USD 2021: ${usRate.rateId} · ${usRate.currencyUnitsPerEur} currency units per EUR`,
    `- CAD 2024: ${cadRate.rateId} · ${cadRate.currencyUnitsPerEur} currency units per EUR`,
  ].join("\n");
}

function extractHttpsUrls(value) {
  return [...String(value ?? "").matchAll(/https:\/\/[^\s;]+/g)]
    .map((match) => match[0].replace(/[.,)\]]+$/g, ""));
}

function ensureSourceCoverage(sourceRows, registerRows, additionalUrls = []) {
  const output = sourceRows.map((row) => row.slice(0, 5));
  const existingUrls = new Set(output.map((row) => String(row[3] ?? "").trim()).filter(Boolean));
  const registerUrls = new Set([
    ...registerRows.flatMap((row) => extractHttpsUrls(row[3])),
    ...additionalUrls,
  ]);
  for (const url of [...registerUrls].sort()) {
    if (existingUrls.has(url)) continue;
    const metadata = SOURCE_METADATA.get(url);
    const hostname = new URL(url).hostname.replace(/^www\./, "");
    const [sourceId, publisher, sourceClass] = metadata ?? [
      `REGISTER-REFERENCE-${sha256Text(url).slice(0, 12).toUpperCase()}`,
      hostname,
      "register_reference",
    ];
    output.push([sourceId, publisher, sourceClass, url, releaseDate]);
    existingUrls.add(url);
  }
  const unresolved = [...registerUrls].filter((url) => !existingUrls.has(url));
  if (unresolved.length) {
    throw new Error(`Sources sheet is missing register URLs: ${unresolved.join(", ")}`);
  }
  return output;
}

function assessArtifactEur(record, fxData) {
  const value = Number(record?.value);
  const currency = String(record?.currency ?? "");
  const unit = String(record?.unit ?? "");
  const year = Number(record?.year);
  const period = String(record?.period ?? "");
  if (
    !Number.isFinite(value)
    || value <= 0
    || !/^[A-Z]{3}$/.test(currency)
    || unit !== currency
  ) {
    return { status: "ineligible", reason: "not_a_positive_monetary_total" };
  }
  if (currency === "EUR") {
    return {
      status: "already_eur",
      reason: "original_currency_already_eur",
      rateValue: 1,
      rateId: "EUR-IDENTITY",
      sourceUrl: fxData.provider.methodologyUrl,
    };
  }
  const eligiblePeriods = new Set(fxData.calculationPolicy.eligibleRecordPeriods ?? []);
  if (!Number.isInteger(year) || !eligiblePeriods.has(period)) {
    return {
      status: "not_computed",
      reason: "period_not_compatible_with_annual_average",
      rateValue: null,
      rateId: null,
      sourceUrl: fxData.provider.datasetUrl,
    };
  }
  const rate = fxRateMap(fxData).get(`${currency}:${year}`);
  if (!rate) {
    return {
      status: "not_computed",
      reason: "compatible_ecb_rate_missing",
      rateValue: null,
      rateId: null,
      sourceUrl: fxData.provider.datasetUrl,
    };
  }
  return {
    status: "computed",
    reason: "original_amount_divided_by_ecb_annual_average",
    rateValue: Number(rate.currencyUnitsPerEur),
    rateId: rate.rateId,
    sourceUrl: rate.sourceUrl,
  };
}

function buildEurEquivalentRows(market, scenarios, fxData) {
  const rows = [];
  const append = (recordType, recordId, item, geography, record) => {
    const assessment = assessArtifactEur(record, fxData);
    if (assessment.status === "ineligible") return;
    rows.push({
      recordType,
      recordId,
      item,
      geography,
      year: record.year,
      period: record.period,
      originalAmount: Number(record.value),
      currency: record.currency,
      ...assessment,
    });
  };

  for (const observation of market?.observations ?? []) {
    append(
      "market_observation",
      observation.observationId,
      observation.metric,
      observation.geography,
      observation,
    );
  }

  for (const scenario of scenarios?.countryYearScenarios ?? []) {
    for (const [rangeKey, component] of Object.entries(scenario.componentBreakdown ?? {})) {
      for (const [componentKey, value] of Object.entries(component ?? {})) {
        if (!Number.isFinite(Number(value)) || Number(value) <= 0) continue;
        append(
          "scenario_component",
          scenario.scenarioId,
          `${rangeKey}.${componentKey}`,
          scenario.geography,
          {
            value,
            currency: scenario.currency,
            unit: scenario.currency,
            year: scenario.year,
            period: "calendar_year",
          },
        );
      }
    }
  }

  for (const model of market?.models ?? []) {
    for (const bound of ["low", "base", "central", "high"]) {
      if (!Number.isFinite(Number(model?.[bound])) || Number(model[bound]) <= 0) continue;
      append(
        "model",
        model.modelId,
        bound,
        model.geography,
        {
          value: model[bound],
          currency: model.currency,
          unit: model.currency,
          year: model.year,
          period: "calendar_year",
        },
      );
    }
  }
  if (!rows.length) throw new Error("EUR-equivalent ledger has no eligible records");
  return rows;
}

function validateV27MarketEvidence(market) {
  const observations = market?.observations;
  const sources = market?.sources;
  if (
    !Array.isArray(observations)
    || observations.length !== expectedMarketCounts.observations
  ) {
    throw new Error(
      `v27 bank package requires exactly ${expectedMarketCounts.observations} market observations`,
    );
  }
  if (!Array.isArray(sources) || sources.length !== expectedMarketCounts.sources) {
    throw new Error(
      `v27 bank package requires exactly ${expectedMarketCounts.sources} market sources`,
    );
  }

  const observationIds = observations.map((item) => item?.observationId);
  if (
    observationIds.some((value) => typeof value !== "string" || !value)
    || new Set(observationIds).size !== observations.length
  ) {
    throw new Error("v27 market observations must have unique non-empty observationId values");
  }
  const sourceIds = sources.map((item) => item?.sourceId);
  if (
    sourceIds.some((value) => typeof value !== "string" || !value)
    || new Set(sourceIds).size !== sources.length
  ) {
    throw new Error("v27 market sources must have unique non-empty sourceId values");
  }

  const official = observations.filter(
    (item) => String(item?.evidenceStatus ?? "").startsWith("official"),
  );
  const swedenStructure = observations.filter(
    (item) => (
      item?.marketValueBasis === swedenStructureBasis
      || (item?.sourceIds ?? []).includes(fhmSourceId)
    ),
  );
  const officialMarketMeasures = official.filter((item) => !swedenStructure.includes(item));
  if (official.length !== expectedMarketCounts.official) {
    throw new Error(
      `v27 bank package requires ${expectedMarketCounts.official} official observations`,
    );
  }
  if (officialMarketMeasures.length !== expectedMarketCounts.officialMarketMeasures) {
    throw new Error(
      `v27 bank package requires ${expectedMarketCounts.officialMarketMeasures} official market measures`,
    );
  }
  if (swedenStructure.length !== expectedMarketCounts.swedenRegisterStructure) {
    throw new Error(
      `v27 bank package requires ${expectedMarketCounts.swedenRegisterStructure} Swedish FHM register-structure counts`,
    );
  }
  const officialMeasureCountries = new Set(
    officialMarketMeasures.map((item) => item.countryIso2).filter(Boolean),
  );
  if (
    JSON.stringify([...officialMeasureCountries].sort())
    !== JSON.stringify(["CA", "DE", "FI", "NZ", "PL", "SE", "US"])
  ) {
    throw new Error("v27 official market measures must retain the seven reviewed countries");
  }

  const expectedStructureIds = new Set();
  for (let year = 2018; year <= 2026; year += 1) {
    for (const metric of swedenStructureMetrics) {
      expectedStructureIds.add(`SE-${year}-FHM-${swedenStructureSuffixByMetric.get(metric)}`);
    }
  }
  for (const item of swedenStructure) {
    const snapshot = item.year === 2026;
    const expectedUnit = item.metric === "reporting_entities_count"
      ? "reporting_entity"
      : "product";
    if (
      !expectedStructureIds.delete(item.observationId)
      || item.countryIso2 !== "SE"
      || item.geography !== "Sweden"
      || !swedenStructureMetrics.includes(item.metric)
      || !Number.isInteger(Number(item.value))
      || Number(item.value) < 0
      || item.unit !== expectedUnit
      || item.currency !== null
      || item.period !== (snapshot
        ? "current_snapshot_as_of_2026_07_24"
        : "authority_supplied_year_label")
      || item.finality !== (snapshot
        ? "official_current_snapshot"
        : "official_response_year_label")
      || item.marketValueBasis !== swedenStructureBasis
      || item.comparableMarketValue !== false
      || item.atlasEstimate !== false
      || !String(item.evidenceStatus ?? "").startsWith("official")
      || JSON.stringify(item.sourceIds) !== JSON.stringify([fhmSourceId])
    ) {
      throw new Error(
        `Swedish FHM structure record is not a non-sales count: ${item.observationId ?? "unknown"}`,
      );
    }
    if (snapshot) {
      const snapshotDisclosure = [
        item.period,
        item.finality,
        item.limitationEn,
        item.limitationFi,
      ].join(" ").toLowerCase();
      if (
        item.period === "calendar_year"
        || (!snapshotDisclosure.includes("snapshot") && !snapshotDisclosure.includes("tilannekuva"))
      ) {
        throw new Error(`${item.observationId}: 2026 must be disclosed as a snapshot, not a full year`);
      }
    }
  }
  if (expectedStructureIds.size) {
    throw new Error(
      `Swedish FHM structure series is incomplete: ${[...expectedStructureIds].join(", ")}`,
    );
  }

  const fhmSource = sources.find((item) => item.sourceId === fhmSourceId);
  if (!fhmSource || fhmSource.pageUrl !== fhmSourceUrl) {
    throw new Error("v27 market sources must retain the reviewed public FHM reference");
  }
  const nzObservation = observations.find(
    (item) => item.observationId === "NZ-2024-IDENTIFIED-VAPING-PRODUCT-SALES-RAW-SUM",
  );
  const nzCandidate = (market?.donorCandidates ?? []).find(
    (item) => item.candidateId === "NZ-2024-IDENTIFIED-VAPING-RETAIL-SUBTOTAL",
  );
  const nzAudit = JSON.parse(
    fsSync.readFileSync(path.join(sourceDir, "NZ_2024_PRODUCT_SCOPE_AUDIT.json"), "utf8"),
  );
  const nzBuckets = nzAudit?.productScopeBuckets ?? {};
  const nzPublished = nzAudit?.publishedAggregates ?? {};
  if (
    Number(nzObservation?.value) !== 274180410.21
    || Number(nzBuckets?.vaping_consumable?.reportedTotalSalesNzd) !== 189402451.96
    || Number(nzBuckets?.vaping_device_or_hardware?.reportedTotalSalesNzd) !== 84709409.85
    || Number(nzBuckets?.vaping_mixed_system?.reportedTotalSalesNzd) !== 68548.40
    || Number(nzPublished?.identifiedAdjacentSalesNzd) !== 2137085.24
    || Number(nzPublished?.unresolvedProductTypeSalesNzd) !== 4367017.37
  ) {
    throw new Error("v27 New Zealand product-scope aggregates differ from the reviewed audit");
  }
  if (
    nzCandidate?.decision !== "not_accepted"
    || JSON.stringify(nzCandidate?.passedCriteria) !== JSON.stringify([
      "D1", "D2", "D3", "D4", "D6", "D7", "D9",
    ])
    || JSON.stringify(nzCandidate?.failedCriteria) !== JSON.stringify(["D5"])
    || JSON.stringify(nzCandidate?.openCriteria) !== JSON.stringify(["D8", "D10"])
    || market?.meta?.modelReadiness?.comparableFullYearMarketValueDonors !== 0
    || market?.meta?.modelReadiness?.minimumRequiredDonors !== 3
  ) {
    throw new Error("v27 New Zealand must remain not accepted at 7/10 with a 0/3 donor gate");
  }
}

function validateGlobalBase(globalBase) {
  if (
    globalBase?.schemaVersion !== "1.1"
    || globalBase?.asOf !== "2026-07-27"
    || !Array.isArray(globalBase?.countries)
    || globalBase.countries.length !== 195
    || globalBase?.summary?.observedCount !== 578
    || globalBase?.summary?.missingCount !== 397
    || globalBase?.summary?.queuedCount !== 390
    || globalBase?.summary?.gdpEurEquivalent?.computedCount !== 190
    || globalBase?.summary?.gdpEurEquivalent?.notComputedCount !== 5
    || globalBase?.globalRetailSales?.status !== "blocked"
    || globalBase?.globalRetailSales?.value !== null
    || globalBase?.globalRetailSales?.eligibleObservationCount !== 0
    || globalBase?.methodRouteControl?.version !== releaseVersion
    || globalBase?.methodRouteControl?.summary?.reviewedMethodPlanCount !== 28
    || globalBase?.methodRouteControl?.summary?.reviewedSourceLeadCount !== 0
    || globalBase?.methodRouteControl?.summary?.regionalTpdPatternOnlyCount !== 15
    || globalBase?.methodRouteControl?.summary?.proxyOnlyUnscopedCount !== 152
  ) {
    throw new Error("v32 global base differs from the reviewed fail-closed method-control snapshot");
  }
  const measureSummary = new Map(
    (globalBase.summary.measures ?? []).map((item) => [item.measureId, item]),
  );
  const expectedMeasures = {
    population_total: [194, 1, 0],
    population_ages_15_64: [194, 1, 0],
    gdp_per_capita_current_usd: [190, 5, 0],
    who_adult_current_ecig_prevalence: [0, 195, 195],
    un_comtrade_vaping_trade: [0, 195, 195],
  };
  for (const [measureId, expected] of Object.entries(expectedMeasures)) {
    const actual = measureSummary.get(measureId);
    if (
      !actual
      || actual.observedCount !== expected[0]
      || actual.missingCount !== expected[1]
      || actual.queuedCount !== expected[2]
      || actual.retailSalesEligible !== false
    ) {
      throw new Error(`v27 global-base measure summary differs: ${measureId}`);
    }
  }
  for (const country of globalBase.countries) {
    const who = country?.routes?.whoAdultCurrentEcigPrevalence;
    const trade = country?.routes?.unComtradeVapingTrade;
    if (
      country?.retailSalesEligible !== false
      || who?.value !== null
      || who?.dataStatus !== "missing"
      || who?.acquisitionStatus !== "queued"
      || who?.retailSalesEligible !== false
      || trade?.value !== null
      || trade?.dataStatus !== "missing"
      || trade?.acquisitionStatus !== "queued"
      || trade?.retailSalesEligible !== false
      || country?.methodRoute?.eligibleForGlobalRollup !== false
      || country?.methodRoute?.donorAccepted !== false
    ) {
      throw new Error(`v32 global-base proxy boundary differs: ${country?.iso2 ?? "unknown"}`);
    }
  }
}

function validateVendorGateBoundary(vendorControl) {
  const euromonitor = (vendorControl?.vendors ?? []).find(
    (vendor) => vendor.vendorId === "euromonitor-passport-nicotine",
  );
  const expected = {
    G1: "not_testable",
    G2: "fail",
    G3: "fail",
    G4: "not_testable",
    G5: "fail",
    G6: "fail",
  };
  if (
    vendorControl?.schemaVersion !== 2
    || vendorControl?.asOf !== releaseDate
    || vendorControl?.version !== releaseVersion
    || vendorControl?.status !== "public_status_only_no_purchase_authorised"
    || !euromonitor
    || euromonitor.quoteReceived !== true
    || euromonitor.mandatoryGatePassCount !== 0
    || euromonitor.evaluatedGateCount !== 6
    || euromonitor.scoringState !== "not_scored"
    || euromonitor.purchaseAuthorised !== false
    || Object.entries(expected).some(
      ([gate, status]) => euromonitor?.gateResults?.[gate]?.status !== status,
    )
  ) {
    throw new Error("v32 Euromonitor 0/6 vendor-gate boundary differs");
  }
}

function validateThirdDonorScreen(publicScreen, sourceScreen) {
  if (JSON.stringify(publicScreen) !== JSON.stringify(sourceScreen)) {
    throw new Error("Public third-donor screen differs from the reviewed source");
  }
  const countries = Array.isArray(publicScreen?.countries) ? publicScreen.countries : [];
  const wave = publicScreen?.followUpWave ?? {};
  if (
    publicScreen?.schemaVersion !== "1.0"
    || publicScreen?.asOf !== releaseDate
    || publicScreen?.status !== "screening_only_not_donor_assessment"
    || publicScreen?.decision?.primaryProgrammeCountryIso2 !== "PL"
    || publicScreen?.decision?.sourceOnlyLeadCountryIso2 !== "RU"
    || JSON.stringify(publicScreen?.decision?.secondaryProgrammeCountryIso2) !== JSON.stringify(["FI", "DK", "FR"])
    || JSON.stringify(countries.map((item) => item?.countryIso2)) !== JSON.stringify([
      "RU", "PL", "FI", "DK", "FR", "AE", "CN", "GB", "US", "NL", "IT", "ES", "SE", "PH", "SA",
    ])
    || countries.some((item, index) => (
      item?.rank !== index + 1
      || item?.donorStatus !== "not_assessed"
    ))
    || wave?.dueOn !== "2026-07-28"
    || wave?.draftState !== "completed_or_superseded"
    || JSON.stringify((wave?.items ?? []).map((item) => item?.vendor)) !== JSON.stringify([
      "ECigIntelligence", "Euromonitor", "Circana",
    ])
    || JSON.stringify((wave?.items ?? []).map((item) => item?.threadStatus)) !== JSON.stringify([
      "follow_up_sent", "superseded_by_comprehensive_request_sent", "follow_up_sent",
    ])
    || wave?.excluded?.[0]?.vendor !== "NIQ"
  ) {
    throw new Error("Third-donor screen differs from the reviewed v32 acquisition decision");
  }
}

function formatDeckNumber(value, digits, language) {
  const output = Number(value).toFixed(digits);
  return language === "fi" ? output.replace(".", ",") : output;
}

function prominentDeckFxPhrases(language, market, scenarios, fxData) {
  const nzModel = (scenarios?.countryYearScenarios ?? []).find(
    (item) => item.scenarioId === "NZ-2024-RETAIL-RANGE",
  );
  const nzObserved = (market?.observations ?? []).find(
    (item) => item.observationId === "NZ-2024-IDENTIFIED-VAPING-PRODUCT-SALES-RAW-SUM",
  );
  const ftc = (market?.observations ?? []).find(
    (item) => item.observationId === "US-2021-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES",
  );
  const canadaRetail = (market?.observations ?? []).find(
    (item) => item.observationId === "CA-2024-STATCAN-RCS-VAPING-RETAIL-SALES",
  );
  const canadaShipments = (market?.observations ?? []).find(
    (item) => item.observationId === "CA-2024-MANUFACTURER-IMPORTER-SHIPMENTS-VALUE",
  );
  const nzModelLow = assessArtifactEur({
    value: nzModel?.inputs?.low?.value,
    currency: nzModel?.currency,
    unit: nzModel?.currency,
    year: nzModel?.year,
    period: "calendar_year",
  }, fxData);
  const nzModelHigh = assessArtifactEur({
    value: nzModel?.inputs?.high?.value,
    currency: nzModel?.currency,
    unit: nzModel?.currency,
    year: nzModel?.year,
    period: "calendar_year",
  }, fxData);
  const nzObservedEur = assessArtifactEur(nzObserved, fxData);
  const ftcEur = assessArtifactEur(ftc, fxData);
  const canadaRetailEur = assessArtifactEur(canadaRetail, fxData);
  const canadaShipmentsEur = assessArtifactEur(canadaShipments, fxData);
  const nzModelComputed = (
    nzModelLow.status === "computed"
    && nzModelHigh.status === "computed"
  );
  const nzObservedComputed = nzObservedEur.status === "computed";
  const ftcComputed = ftcEur.status === "computed";
  const canadaRetailComputed = canadaRetailEur.status === "computed";
  const canadaShipmentsComputed = canadaShipmentsEur.status === "computed";
  const nzModelEurLow = nzModelComputed
    ? Number(nzModel.inputs.low.value) / nzModelLow.rateValue
    : null;
  const nzModelEurHigh = nzModelComputed
    ? Number(nzModel.inputs.high.value) / nzModelHigh.rateValue
    : null;
  const nzObservedEurValue = nzObservedComputed
    ? Number(nzObserved.value) / nzObservedEur.rateValue
    : null;
  const ftcEurValue = ftcComputed ? Number(ftc.value) / ftcEur.rateValue : null;
  const canadaRetailEurValue = canadaRetailComputed
    ? Number(canadaRetail.value) / canadaRetailEur.rateValue
    : null;
  const canadaShipmentsEurValue = canadaShipmentsComputed
    ? Number(canadaShipments.value) / canadaShipmentsEur.rateValue
    : null;
  if (language === "fi") {
    return {
      nzObservedOriginal: "274,180 milj. NZD",
      nzObservedReplacement: nzObservedComputed
        ? `274,180 milj. NZD (≈${formatDeckNumber(nzObservedEurValue / 1e6, 1, language)} milj. EUR; ECB 2024)`
        : "274,180 milj. NZD (EUR not_computed)",
      nzModelOriginal: "533,7–731,2 milj. NZD",
      nzModelReplacement: nzModelComputed
        ? `533,7–731,2 milj. NZD (≈${formatDeckNumber(nzModelEurLow / 1e6, 1, language)}–${formatDeckNumber(nzModelEurHigh / 1e6, 1, language)} milj. EUR; ECB 2024)`
        : "533,7–731,2 milj. NZD (EUR not_computed)",
      nzCardSubtitle: nzObservedComputed
        ? `tunnistettu AIS/AVP-summa · ≈${formatDeckNumber(nzObservedEurValue / 1e6, 1, language)} milj. EUR`
        : "EUR not_computed · NZ 2024",
      ftcOriginal: "2,763 mrd USD",
      ftcReplacement: ftcComputed
        ? `2,763 mrd USD (≈${formatDeckNumber(ftcEurValue / 1e9, 3, language)} mrd EUR; ECB 2021)`
        : "2,763 mrd USD (EUR not_computed)",
      canadaRetailOriginal: "1,219160 mrd CAD",
      canadaRetailReplacement: canadaRetailComputed
        ? `1,219160 mrd CAD (≈${formatDeckNumber(canadaRetailEurValue / 1e6, 1, language)} milj. EUR; ECB 2024)`
        : "1,219160 mrd CAD (EUR not_computed)",
      canadaRetailCardSubtitle: canadaRetailComputed
        ? `kuluttajavähittäismyynti · ≈${formatDeckNumber(canadaRetailEurValue / 1e6, 1, language)} milj. EUR`
        : "kuluttajavähittäismyynti · EUR not_computed",
      canadaShipmentsOriginal: "1,160754 mrd CAD",
      canadaShipmentsReplacement: canadaShipmentsComputed
        ? `1,160754 mrd CAD (≈${formatDeckNumber(canadaShipmentsEurValue / 1e6, 1, language)} milj. EUR; ECB 2024)`
        : "1,160754 mrd CAD (EUR not_computed)",
      canadaShipmentsCardSubtitle: canadaShipmentsComputed
        ? `toimitukset · ≈${formatDeckNumber(canadaShipmentsEurValue / 1e6, 1, language)} milj. EUR`
        : "toimitukset · EUR not_computed",
    };
  }
  return {
    nzObservedOriginal: "NZD 274.180m",
    nzObservedReplacement: nzObservedComputed
      ? `NZD 274.180m (≈EUR ${formatDeckNumber(nzObservedEurValue / 1e6, 1, language)}m; ECB 2024)`
      : "NZD 274.180m (EUR not_computed)",
    nzModelOriginal: "NZD 533.7–731.2m",
    nzModelReplacement: nzModelComputed
      ? `NZD 533.7–731.2m (≈EUR ${formatDeckNumber(nzModelEurLow / 1e6, 1, language)}–${formatDeckNumber(nzModelEurHigh / 1e6, 1, language)}m; ECB 2024)`
      : "NZD 533.7–731.2m (EUR not_computed)",
    nzCardSubtitle: nzObservedComputed
      ? `identified AIS/AVP subtotal · ≈EUR ${formatDeckNumber(nzObservedEurValue / 1e6, 1, language)}m`
      : "EUR not_computed · NZ 2024",
    ftcOriginal: "USD 2.763bn",
    ftcReplacement: ftcComputed
      ? `USD 2.763bn (≈EUR ${formatDeckNumber(ftcEurValue / 1e9, 3, language)}bn; ECB 2021)`
      : "USD 2.763bn (EUR not_computed)",
    canadaRetailOriginal: "CAD 1.219160bn",
    canadaRetailReplacement: canadaRetailComputed
      ? `CAD 1.219160bn (≈EUR ${formatDeckNumber(canadaRetailEurValue / 1e6, 1, language)}m; ECB 2024)`
      : "CAD 1.219160bn (EUR not_computed)",
    canadaRetailCardSubtitle: canadaRetailComputed
      ? `consumer retail · ≈EUR ${formatDeckNumber(canadaRetailEurValue / 1e6, 1, language)}m`
      : "consumer retail · EUR not_computed",
    canadaShipmentsOriginal: "CAD 1.160754bn",
    canadaShipmentsReplacement: canadaShipmentsComputed
      ? `CAD 1.160754bn (≈EUR ${formatDeckNumber(canadaShipmentsEurValue / 1e6, 1, language)}m; ECB 2024)`
      : "CAD 1.160754bn (EUR not_computed)",
    canadaShipmentsCardSubtitle: canadaShipmentsComputed
      ? `shipments · ≈EUR ${formatDeckNumber(canadaShipmentsEurValue / 1e6, 1, language)}m`
      : "shipments · EUR not_computed",
  };
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (quoted) {
      if (char === '"' && text[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }
  if (field || row.length) {
    row.push(field);
    rows.push(row);
  }
  return rows.filter((item) => item.some((value) => String(value).trim()));
}

function csvCell(value) {
  const text = String(value ?? "");
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function csvText(headers, rows) {
  return `\uFEFF${[headers, ...rows].map((row) => row.map(csvCell).join(",")).join("\n")}\n`;
}

function assertRegister(rows, headers, allowed) {
  if (headers.length !== 9 || rows.some((row) => row.length !== 9)) {
    throw new Error("Evidence Register must contain exactly nine columns");
  }
  if (rows.length !== 60) throw new Error(`Evidence Register must contain 60 rows, got ${rows.length}`);
  const statuses = new Set(rows.map((row) => row[7]));
  if (statuses.size !== 4 || [...statuses].some((value) => !allowed.has(value))) {
    throw new Error("Evidence Register confidence classification mismatch");
  }
}

function upgradeRegister(rows, language) {
  const output = rows.map((row) => [...row]);
  const oldCountPrefix = language === "fi"
    ? "Hyväksyttyjä vuosittaisia virallisia määrähavaintoja"
    : "Accepted annual official quantitative observations";
  const countIndex = output.findIndex((row) => (
    row[0].startsWith(oldCountPrefix)
    || row[0].includes("27 annual observations")
    || row[0].includes("27 virallisista reiteistä")
    || row[0].includes("34 annual observations")
    || row[0].includes("34 virallisista reiteistä")
    || row[0].includes("79 observations")
    || row[0].includes("79 havaintoa")
    || row[0].includes("84 observations")
    || row[0].includes("84 havaintoa")
  ));
  if (countIndex < 0) throw new Error(`${language}: official-observation row not found`);
  output[countIndex] = language === "fi"
    ? [
      "Julkinen markkina-aineisto sisältää 84 havaintoa 24 lähteestä; 75 virallista havaintoa jakautuvat 39 markkinamittariin ja 36 Ruotsin FHM-rekisterirakenteen lukuun.",
      "Markkinakoko",
      "Markkinamittarit kattavat Kanadan, Saksan, Suomen, Uuden-Seelannin, Puolan, Ruotsin ja Yhdysvallat. FHM-luvut kuvaavat vuosien 2018–2026 raportoivia toimijoita sekä ilmoitettuja, aktiivisia ja markkinoilta poistettuja tuotteita; ne eivät ole myyntiä tai markkina-arvoa.",
      "site/data/market-values.json (julkisen sivuston koneellisesti luettava lähdetiedosto)",
      "2026-07-27",
      "84 = 48 markkina- ja mallihavaintoa + 36 FHM-rakennelukua; 75 virallista = 39 markkinamittaria + 36 rakennelukua. Luokat pidetään erillään eikä niitä summata markkinaksi.",
      "Vuosien 2018–2025 luvut ovat viranomaisen vuosilabeleita, eivät oletettuja kalenterivuoden virtoja tai vuoden lopun tilannekuvia. Vuosi 2026 on tarkistushetken tilannekuva, ei valmis vuosijakso. Virallinen lähde ei tee eri mittareista yhteismitallisia.",
      "Vahvistettu",
      "Lisämaista tarvitaan yhteismitalliset vuotuiset laite- ja nestemäisen kuluttajavähittäisarvon sarjat.",
    ]
    : [
      "The public market dataset contains 84 observations from 24 sources; its 75 official observations split into 39 market measures and 36 Swedish FHM register-structure counts.",
      "Market size",
      "The market measures cover Canada, Germany, Finland, New Zealand, Poland, Sweden and the United States. The FHM counts describe reporting entities and notified, active and withdrawn products for 2018–2026; they are not sales or market value.",
      "site/data/market-values.json (machine-readable source file of the public site)",
      "2026-07-27",
      "84 = 48 market and model observations + 36 FHM structure counts; 75 official = 39 market measures + 36 structure counts. The roles remain separate and are not summed into a market.",
      "The 2018–2025 figures are authority-supplied year labels, not assumed calendar-year flows or year-end snapshots. The 2026 FHM records are a current snapshot, not a completed annual period. Official sourcing does not make unlike metrics comparable.",
      "Confirmed",
      "Comparable annual device and liquid consumer-retail-value series are required from additional countries.",
    ];

  const globalBaseIndex = output.findIndex((row) => (
    row[0].startsWith(language === "fi"
      ? "Julkinen atlas sisältää"
      : "The public atlas contains")
    || row[0].startsWith(language === "fi"
      ? "Julkinen 195 maan avoin pohjakerros sisältää"
      : "The public 195-country open base contains")
    || row[0].startsWith(language === "fi"
      ? "Julkinen avoin maapohja sisältää"
      : "The public 195-country open base contains")
  ));
  if (globalBaseIndex < 0) throw new Error(`${language}: global-base row not found`);
  output[globalBaseIndex] = language === "fi"
    ? [
      "Julkinen avoin maapohja sisältää 578 havaittua World Bank -lukua; siinä on 0 sähkötupakkavähittäismyyntihavaintoa.",
      "Markkinan rajaus",
      "Väestö ja ikäryhmä 15–64 vuotta kattavat kumpikin 194/195 maata. BKT asukasta kohti kattaa 190/195 maata, ja kaikille 190 havainnolle on laskettu saman lähdevuoden EKP-kurssilla EUR-vasta-arvo. WHO- ja UN Comtrade -reitit ovat 195/195 jonossa ja puuttuvina, eivät nollina; vähittäismyyntiin kelpaavia havaintoja on 0.",
      "site/data/global-base-layer.json ; site/data/global-base-layer.csv ; https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures ; https://www.un.org/en/about-us/member-states ; https://www.un.org/en/about-us/non-member-states",
      "2026-07-27",
      "Kustakin World Bank -sarjasta valitaan uusin ei-tyhjä havainto vuosilta 2020–2024 ja alkuperäinen lähdevuosi säilytetään. USD/asukas jaetaan vain saman lähdevuoden EKP-kurssilla.",
      "Väestö, BKT, käyttäjäprevalenssi ja kauppavirrat ovat tausta- tai proxymittareita, eivät sähkötupakkamyynnin arvoja.",
      "Vahvistettu",
      "Maakohtaiset vuosittaiset laite- ja e-nestemyyntiarvot, WHO-reitin numeerinen poiminta ja UN Comtrade -luokituksen validointi puuttuvat.",
    ]
    : [
      "The public 195-country open base contains 578 observed World Bank records; it contains zero vaping retail-sales observations.",
      "Market scope",
      "Population and population ages 15–64 each cover 194/195 countries. GDP per capita covers 190/195 countries, and all 190 observations have a EUR equivalent calculated with the ECB rate for the same source year. WHO and UN Comtrade routes are queued and missing for 195/195 countries, not zero.",
      "site/data/global-base-layer.json ; site/data/global-base-layer.csv ; https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures ; https://www.un.org/en/about-us/member-states ; https://www.un.org/en/about-us/non-member-states",
      "2026-07-27",
      "For each World Bank series, the latest non-null observation from 2020–2024 is selected and its real source year is retained. USD per person is divided only by the ECB rate for that same source year.",
      "Population, GDP, user prevalence and trade flows are context or proxy measures, not vaping sales values.",
      "Confirmed",
      "Annual country device and e-liquid sales values, numeric WHO extraction and validation of the UN Comtrade classification remain missing.",
    ];

  const methodControlRow = language === "fi"
    ? [
      "195 maan menetelmäkontrolli erottaa 28 tarkistettua maasuunnitelmaa, 0 tarkistettua lähdepolkua, 15 alueellista EU TPD -raportointimallia ja 152 maakohtaisesti rajaamatonta proxy-reittiä.",
      "Markkinan rajaus",
      "Jokaisella maalla on näkyvä menetelmäluokka, seuraava evidenssitoimi ja lähdeperusta. Luokitus ei ole myyntihavainto: kaikilla 195 maalla eligibleForGlobalRollup=false ja donorAccepted=false.",
      "site/data/global-base-layer.json ; source/country-method-route-config.json ; source/COUNTRY_METHOD_ROUTE_MAP.md ; source/FIVE_COUNTRY_METHOD_SPRINT_2026-07-27.md",
      "2026-07-27",
      "195 = 28 reviewed_method_plan + 0 reviewed_source_lead + 15 regional_tpd_pattern_only + 152 proxy_only_unscoped.",
      "Vain 28 maalla on tarkistettu maakohtainen menetelmäsuunnitelma. Viisi tässä sprintissä tarkistettua lähdepolkua siirrettiin maasuunnitelmiksi vasta, kun virallinen haltija, kentät, kaava ja rajoitteet oli dokumentoitu. Luokitus ei osoita kansallista myyntisarjaa; 152 reittiä vaatii maakohtaisen rajauksen.",
      "Vahvistettu",
      "Yksikään menetelmäluokka ei korvaa vuosittaista laite- ja e-nestemyynnin arvoa, veroperustaa, kanavapeittoa tai D1–D10-hyväksyntää.",
    ]
    : [
      "The 195-country method control separates 28 reviewed country plans, 0 reviewed source leads, 15 regional EU TPD reporting patterns and 152 country-unscoped proxy routes.",
      "Market scope",
      "Every country has a visible method class, next evidence action and provenance basis. Classification is not a sales observation: all 195 countries in the 195-country universe have eligibleForGlobalRollup=false and donorAccepted=false.",
      "site/data/global-base-layer.json ; source/country-method-route-config.json ; source/COUNTRY_METHOD_ROUTE_MAP.md ; source/FIVE_COUNTRY_METHOD_SPRINT_2026-07-27.md",
      "2026-07-27",
      "195 = 28 reviewed_method_plan + 0 reviewed_source_lead + 15 regional_tpd_pattern_only + 152 proxy_only_unscoped.",
      "Across 195 countries, only 28 have a reviewed country-specific method plan. Five leads reviewed in this sprint were promoted only after their official holder, fields, formula and limitations were documented. Classification does not establish a national sales series; 152 routes still require country-specific scoping.",
      "Confirmed",
      "No method class replaces annual device and e-liquid sales value, tax basis, channel coverage or D1–D10 acceptance.",
    ];
  const existingMethodControlIndex = output.findIndex((row) => (
    row[0].startsWith(language === "fi"
      ? "195 maan menetelmäkontrolli erottaa"
      : "The 195-country method control separates")
  ));
  if (existingMethodControlIndex < 0) {
    output.splice(globalBaseIndex + 1, 0, methodControlRow);
  } else {
    output[existingMethodControlIndex] = methodControlRow;
  }
  const actualMethodControlIndex = output.findIndex((row) => (
    row[0].startsWith(language === "fi"
      ? "195 maan menetelmäkontrolli erottaa"
      : "The 195-country method control separates")
  ));
  const v32ClaimPrefix = language === "fi"
    ? "Itävallalla on tarkistettu"
    : "Austria has a reviewed";
  const existingV32ClaimIndex = output.findIndex((row) => row[0].startsWith(v32ClaimPrefix));
  if (existingV32ClaimIndex < 0) {
    output.splice(actualMethodControlIndex + 1, 0, ...v32MethodAndFiscalClaims[language]);
  } else {
    output.splice(
      existingV32ClaimIndex,
      v32MethodAndFiscalClaims[language].length,
      ...v32MethodAndFiscalClaims[language],
    );
  }

  const polandFlowIndex = output.findIndex((row) => (
    row[0].startsWith(language === "fi"
      ? "Puolassa raportoitu sähkötupakkanesteiden määrä"
      : "Poland reported 805,441 litres")
    || row[0].startsWith(language === "fi"
      ? "Puolan virallinen sähkötupakkanesteiden virta"
      : "Poland's official e-liquid flow")
  ));
  if (polandFlowIndex < 0) throw new Error(`${language}: Poland flow row not found`);
  output[polandFlowIndex] = language === "fi"
    ? [
      "Puolan virallinen sähkötupakkanesteiden virta oli 1 451 529 litraa vuonna 2020, 277 265 litraa vuonna 2021, 416 088 litraa vuonna 2022 ja 805 441 litraa vuonna 2023.",
      "Markkinakoko",
      "Ministeriön parlamenttivastauksen taulukko yhdistää ZEFIR2/AIS-järjestelmiin kirjatut kotimaan myynnit, EU-sisäiset hankinnat ja tuonnin. Sarja on fyysinen e-nestevirta, ei kuluttajamyynti tai havaittu vähittäismarkkina-arvo.",
      "https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTDDEJZ5/i07255-o1.pdf",
      "2020–2023",
      "Neljän virallisen vuosihavainnon suora toisto; eri vuosia ei summata markkina-arvoksi.",
      "Julkaistu taulukko ei erittele kotimaan myyntiä, EU-sisäisiä hankintoja ja tuontia eikä sisällä laitteiden arvoa.",
      "Vahvistettu",
      "Tarvitaan kuluttajavähittäisarvo, kanavapeitto, veroperusta ja riippumaton täsmäytys.",
    ]
    : [
      "Poland's official e-liquid flow was 1,451,529 litres in 2020, 277,265 litres in 2021, 416,088 litres in 2022 and 805,441 litres in 2023.",
      "Market size",
      "The ministry's parliamentary-response table combines domestic sales, intra-EU acquisitions and imports recorded in ZEFIR2/AIS. The series is a physical e-liquid flow, not consumer sales or observed retail market value.",
      "https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTDDEJZ5/i07255-o1.pdf",
      "2020–2023",
      "Direct reproduction of four official annual observations; years are not summed into a market value.",
      "The published table does not split domestic sales, intra-EU acquisitions and imports and contains no device value.",
      "Confirmed",
      "Consumer retail value, channel coverage, tax basis and independent reconciliation are required.",
    ];

  const polandTaxIndex = output.findIndex((row) => (
    row[0].startsWith(language === "fi"
      ? "Puolan vuoden 2025 ilmoitettu e-nestevalmisteveron määrä"
      : "Poland reported PLN 993.1 million")
    || row[0].startsWith(language === "fi"
      ? "Puolan vuoden 2025 verosilta antaa"
      : "Poland's 2025 tax bridge yields")
  ));
  if (polandTaxIndex < 0) throw new Error(`${language}: Poland tax-bridge row not found`);
  output[polandTaxIndex] = language === "fi"
    ? [
      "Puolan vuoden 2025 verosilta antaa 4 382 500 johdettua verollista sähkötupakkalaitetta ja 62 500 johdettua verollista osasarjaa.",
      "Markkinakoko",
      "Virallinen parlamenttivastaus raportoi 993,1 milj. PLN e-nesteistä, 175,3 milj. PLN laitteista ja 2,5 milj. PLN osasarjoista. Laitteiden ja osasarjojen vero oli 40 PLN yksiköltä 1.7.2025 alkaen.",
      "https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTDVKHSJ/i17526-o1.pdf ; https://www.podatki.gov.pl/akcyza/stawki-podatkowe/",
      "2025",
      "175 300 000 / 40 = 4 382 500 verollista laitetta; 2 500 000 / 40 = 62 500 verollista osasarjaa.",
      "Johdettu veropohja kattaa vain 1.7.2025 alkaen verotetut laitteet ja osasarjat. Se ei osoita kuluttajahintaa, vähittäismyyntiä, verottomia määriä tai varastosiirtymiä.",
      "Tuettu",
      "Tarvitaan veron kuukausijakauma, lopullisuus, vähittäishinnat, kanavapeitto ja riippumaton täsmäytys.",
    ]
    : [
      "Poland's 2025 tax bridge yields 4,382,500 derived taxable e-cigarette devices and 62,500 derived taxable component sets.",
      "Market size",
      "The official parliamentary response reports PLN 993.1 million for e-liquids, PLN 175.3 million for devices and PLN 2.5 million for component sets. The device and component-set duty was PLN 40 per unit from 1 July 2025.",
      "https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTDVKHSJ/i17526-o1.pdf ; https://www.podatki.gov.pl/akcyza/stawki-podatkowe/",
      "2025",
      "PLN 175,300,000 / 40 = 4,382,500 taxable devices; PLN 2,500,000 / 40 = 62,500 taxable component sets.",
      "The derived tax base covers only devices and component sets taxed from 1 July 2025. It does not establish consumer prices, retail sales, untaxed quantities or stock transitions.",
      "Supported",
      "The monthly duty profile, finality, retail prices, channel coverage and independent reconciliation are required.",
    ];

  const nzScopeIndex = output.findIndex((row) => (
    row[0].startsWith(language === "fi"
      ? "Varovainen tekstiluokitus"
      : "A conservative text classification")
    || row[0].startsWith(language === "fi"
      ? "Uuden-Seelannin vuoden 2024 AIS/AVP"
      : "New Zealand's 2024 AIS/AVP")
  ));
  if (nzScopeIndex < 0) throw new Error(`${language}: New Zealand scope row not found`);
  output[nzScopeIndex] = language === "fi"
    ? [
      "Uuden-Seelannin vuoden 2024 AIS/AVP-erikoisvähittäiskaupan tunnistettu sähkötupakkasumma on 274 180 410,21 NZD; donor-testi läpäisee 7/10 ehtoa, mutta maa ei ole hyväksytty donor.",
      "Markkinakoko",
      "Kulutustarvikkeet ovat 189 402 451,96 NZD, laitteet/hardware 84 709 409,85 NZD ja sekajärjestelmät 68 548,40 NZD. Viereiset ilmoitusvelvolliset tuotteet 2 137 085,24 NZD ja ratkaisemattomat tuotetyypit 4 367 017,37 NZD määrällistetään erikseen ja rajataan pois. Havaittu arvo tulee vain AIS/AVP-työkirjoista; Notifier- ja RPS-arvoa ei lisätä.",
      "https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2024 ; https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return ; https://www.health.govt.nz/system/files/2024-12/2024-annual-returns-user-guide.pdf ; source/NZ_2024_DONOR_CLOSURE_PACK.md ; source/NZ_2024_D8_D10_OFFICIAL_SOURCE_AUDIT.md ; source/NZ_2024_WORKBOOK_MANIFEST.json ; source/NZ_2024_PRODUCT_SCOPE_AUDIT.json ; scripts/analyze_nz_2024_returns.py",
      "2026-07-27",
      "189 402 451,96 + 84 709 409,85 + 68 548,40 = 274 180 410,21 NZD. Viereiset ja ratkaisemattomat luokat käsitellään ennen vaping-summaa ja jätetään siitä pois. Kaikkien 29 tiedoston URL:t, koot ja SHA-256-tiivisteet validoidaan ennen aggregointia.",
      "Deterministinen tuoterajaus on julkinen. Yleisvähittäiskaupan havaittu arvo puuttuu, GST-perusta on tuntematon, täsmälleen toistuvien rivien herkkyys ei ole korjattu estimaatti eikä riippumatonta täsmäytystä ole.",
      "Tuettu",
      "D5 hylätään puuttuvan kansallisen kanavapeiton vuoksi; D8:n GST-perusta ja D10:n riippumaton täsmäytys ovat avoimia. Donor-portti pysyy 0/3:ssa.",
    ]
    : [
      "New Zealand's 2024 AIS/AVP specialist-retailer identified-vaping subtotal is NZD 274,180,410.21; the donor test passes 7/10 criteria, but New Zealand is not an accepted donor.",
      "Market size",
      "Consumables are NZD 189,402,451.96, devices/hardware NZD 84,709,409.85 and mixed systems NZD 68,548.40. Adjacent notifiable products of NZD 2,137,085.24 and unresolved product types of NZD 4,367,017.37 are separately quantified and excluded. All observed value comes from AIS/AVP workbooks; no Notifier or RPS value is added.",
      "https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2024 ; https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return ; https://www.health.govt.nz/system/files/2024-12/2024-annual-returns-user-guide.pdf ; source/NZ_2024_DONOR_CLOSURE_PACK.md ; source/NZ_2024_D8_D10_OFFICIAL_SOURCE_AUDIT.md ; source/NZ_2024_WORKBOOK_MANIFEST.json ; source/NZ_2024_PRODUCT_SCOPE_AUDIT.json ; scripts/analyze_nz_2024_returns.py",
      "2026-07-27",
      "NZD 189,402,451.96 + 84,709,409.85 + 68,548.40 = NZD 274,180,410.21. Adjacent and unresolved classes are applied before the vaping subtotal and excluded. URLs, byte sizes and SHA-256 hashes for all 29 files are validated before aggregation.",
      "The deterministic scope rules are public. Observed general-retail value is absent, the GST basis is unknown, exact-row-deduplication sensitivity is not a corrected estimate and no independent reconciliation has passed.",
      "Supported",
      "D5 fails for missing national channel coverage; D8 GST basis and D10 independent reconciliation remain open. The donor gate remains 0/3.",
    ];

  const swedenIndex = output.findIndex((row) => (
    row[0].startsWith(language === "fi" ? "Ruotsissa verotettiin" : "Sweden taxed")
    || row[0].startsWith(language === "fi"
      ? "Ruotsin julkinen evidenssi yhdistää"
      : "Sweden's public evidence combines")
  ));
  if (swedenIndex < 0) throw new Error(`${language}: Sweden register row not found`);
  output[swedenIndex] = language === "fi"
    ? [
      "Ruotsin julkinen evidenssi yhdistää vuoden 2024 veroankkurin ja 36 virallista FHM-rekisterirakenteen lukua vuosilta 2018–2026; rekisteriluvut eivät ole myyntiä tai markkina-arvoa.",
      "Markkinakoko",
      "Vuonna 2024 verotettiin 26 000 litraa nikotiininestettä ja valmisteverotulo oli pyöristetysti 80 000 000 SEK. Viranomaisen toimittamassa ja 24.7.2026 tarkistetussa työkirjassa on 9 vuosilabelia × 4 rakennemittaria: raportoivat toimijat sekä ilmoitetut, aktiiviset ja markkinoilta poistetut tuotteet. Julkinen FHM-sivu dokumentoi ilmoitusjärjestelmän, ei siinä julkaistua numeerista sarjaa.",
      `https://www.regeringen.se/contentassets/1ed01e00001b42e5ad8d47433db63ece/berakningskonventioner_2026.pdf ; ${fhmSourceUrl} ; site/data/market-values.json`,
      "2026-07-24",
      "36 = 9 vuotta (2018–2026) × 4 rekisterirakenteen mittaria. Veroankkuri, 39 markkinamittaria ja 36 rakennelukua pidetään erillään.",
      "Rakenneluvuista ei päätellä myyntiarvoa, myyntimäärää tai markkinaosuutta. Vuosien 2018–2025 luvut ovat viranomaisen vuosilabeleita, eivät oletettuja vuosivirtoja tai vuoden lopun tilannekuvia. Vuosi 2026 on tarkistushetken tilannekuva eikä sitä vuositasoiteta.",
      "Vahvistettu",
      "Tarvitaan toteutunut kuluttajamyynti EUR-määräisenä, laitekappaleet ja ml-määrät sekä julkisesti uudelleenkäytettävä numeerinen FHM-sarja.",
    ]
    : [
      "Sweden's public evidence combines a 2024 tax anchor with 36 official FHM register-structure counts for 2018–2026; the register counts are not sales or market value.",
      "Market size",
      "Sweden taxed 26,000 litres of nicotine liquid in 2024 and reported rounded excise receipts of SEK 80,000,000. An authority-supplied workbook received and reviewed on 24 July 2026 contains 9 year labels × 4 structure metrics: reporting entities and notified, active and withdrawn products. The public FHM page documents the notification system; it is not presented as publishing the numeric series.",
      `https://www.regeringen.se/contentassets/1ed01e00001b42e5ad8d47433db63ece/berakningskonventioner_2026.pdf ; ${fhmSourceUrl} ; site/data/market-values.json`,
      "2026-07-24",
      "36 = 9 years (2018–2026) × 4 register-structure metrics. The tax anchor, 39 market measures and 36 structure counts remain separate.",
      "No sales value, sales volume or market share is inferred from the structure counts. The 2018–2025 figures are authority-supplied year labels, not assumed annual flows or year-end snapshots. The 2026 records are a current snapshot and are not annualised.",
      "Confirmed",
      "Observed consumer sales in euros, device units and liquid millilitres, plus a publicly reusable numeric FHM series, are still required.",
    ];

  const donorIndex = output.findIndex((row) => row[0].includes(language === "fi"
    ? "kuluttajavähittäisarvon luovuttajamarkkinoita"
    : "consumer-retail-value donor markets"));
  if (donorIndex < 0) throw new Error(`${language}: donor row not found`);
  output[donorIndex] = language === "fi"
    ? [
      "Hyväksyttyjä virallisia koko vuoden kansallisia kuluttajavähittäisarvon luovuttajamarkkinoita on nolla.",
      "Markkinakoko",
      "comparableFullYearMarketValueDonors = 0. Viisi ehdokasta on julkaistu samaa kymmenen ehdon protokollaa vasten.",
      "site/data/market-values.json (modelReadiness, donorProtocol ja donorCandidates)",
      "2026-07-27",
      "Ehdokas tulee donor-lukuun vain, kun D1–D10 läpäisevät tarkistuksen; hylätty tai avoin ehto pitää sen luvun ulkopuolella.",
      "Virallisia alarajoja, institutionaalisia vertailuarvoja, toimitusarvoja, veroja, fyysisiä määriä ja malleja ei nimetä täydelliseksi kuluttajavähittäisarvoksi.",
      "Vahvistettu",
      "Tarvitaan vähintään kolme hyväksyttyä donoria sekä alue- ja sääntelytyyppien peitto.",
    ]
    : [
      "There are zero accepted full-year national consumer-retail-value donor markets.",
      "Market size",
      "comparableFullYearMarketValueDonors = 0. Five candidate tests are published against the same ten-criterion protocol.",
      "site/data/market-values.json (modelReadiness, donorProtocol and donorCandidates)",
      "2026-07-27",
      "A candidate enters the donor count only when D1–D10 all pass; a failed or open criterion keeps it outside the count.",
      "Official lower bounds, institutional benchmarks, shipment values, tax receipts, physical volumes and models are not relabelled as complete consumer-retail value.",
      "Confirmed",
      "At least three accepted donors are required, with regional and regulatory-archetype coverage.",
    ];

  const canadaIndex = output.findIndex((row) => (
    row[0].startsWith(language === "fi"
      ? "Kanadan vuoden 2024"
      : "Canada's 2024 manufacturer")
    || row[0].startsWith(language === "fi"
      ? "Kanadan Statistics Canada -sarja"
      : "Statistics Canada's Canada series")
    || row[0].startsWith(language === "fi"
      ? "Kanadan virallinen vuoden 2024"
      : "Canada's official 2024")
  ));
  if (canadaIndex < 0) throw new Error(`${language}: Canada register row not found`);
  output[canadaIndex] = language === "fi"
    ? [
      "Kanadan virallinen vuoden 2024 kuluttajavähittäismyynnin piste-estimaatti on 1 219 160 000 CAD eli 822 583 715,21 EUR; donor-testi läpäisee 7/10 ehtoa.",
      "Markkinakoko",
      "Neljän kvartaalin summa on 1 219 160 000 CAD; 12 kuukauden samaan kyselyyn perustuva summa on 1 219 161 000 CAD. Health Canadan vuoden 2024 valmistaja-/maahantuojatoimitusten nettoarvo on 1 160 753 796,78 CAD.",
      "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010007101 ; https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010008001 ; https://health-infobase.canada.ca/substance-use/vaping/sales/ ; source/CANADA_2024_DONOR_CLOSURE_PACK.md ; source/CANADA_2024_D5_D7_D10_OFFICIAL_SOURCE_AUDIT.md",
      "2026-07-27",
      "Kuukausi − kvartaali = 1 000 CAD (0,000082 %). Retail − toimitukset = 58 406 203,22 CAD; retail / toimitukset − 1 = 5,031748 %. ECB 2024: 1 219 160 000 / 1,482110546875 = 822 583 715,21 EUR.",
      "D8 läpäisee: CAD sekä GST/HST-, provinssi- ja valmisteverojen poissulku on lähteistetty. Kuukausireitti on saman kyselyn QA, ei D10; retail- ja toimitusreitit eivät muodosta markkinahaarukkaa.",
      "Tuettu",
      "D5:n NAICS 459993/459999 -peitto, D7:n vuositason virheraja ja D10:n retail–toimitus-silta ovat avoimia; Kanada ei ole hyväksytty donor.",
    ]
    : [
      "Canada's official 2024 consumer-retail point estimate is CAD 1,219,160,000, or EUR 822,583,715.21; the donor test passes 7/10 criteria.",
      "Market size",
      "The four-quarter sum is CAD 1,219,160,000; the same-survey sum of 12 months is CAD 1,219,161,000. Health Canada's 2024 manufacturer/importer net shipment value is CAD 1,160,753,796.78.",
      "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010007101 ; https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010008001 ; https://health-infobase.canada.ca/substance-use/vaping/sales/ ; source/CANADA_2024_DONOR_CLOSURE_PACK.md ; source/CANADA_2024_D5_D7_D10_OFFICIAL_SOURCE_AUDIT.md",
      "2026-07-27",
      "Monthly − quarterly = CAD 1,000 (0.000082%). Retail − shipments = CAD 58,406,203.22; retail / shipments − 1 = 5.031748%. ECB 2024: 1,219,160,000 / 1.482110546875 = EUR 822,583,715.21.",
      "D8 passes: CAD and exclusion of GST/HST, provincial sales taxes and excise are source-linked. The monthly route is same-survey QA, not D10; retail and shipments do not form a market range.",
      "Supported",
      "D5 NAICS 459993/459999 coverage, D7 annual error boundary and D10 retail-to-shipment reconciliation remain open; Canada is not an accepted donor.",
    ];

  const canadaShipmentIndex = output.findIndex((row) => row[0].startsWith(language === "fi"
    ? "Kanadan vuoden 2024 raportoidut toimitukset"
    : "Canada's 2024 shipments included")
    || row[0].startsWith(language === "fi"
      ? "Health Canadan neljä vuoden 2024"
      : "Health Canada's four 2024"));
  if (canadaShipmentIndex < 0) throw new Error(`${language}: Canada shipment row not found`);
  output[canadaShipmentIndex] = language === "fi"
    ? [
      "Health Canadan neljä vuoden 2024 tuoteryhmää summautuvat 1 160 753 796,78 CAD:n nettotoimitusarvoon, 118 901 910 yksikköön ja 1 251 843 litraan.",
      "Markkinakoko",
      "Arvo-osuudet ovat: laite tai osa ilman ainetta 2,602 %, aineen sisältävä laite 48,154 %, aineen sisältävä osa 27,252 % ja höyrystettävä aine 21,992 %. Kyse on toimituksista tukku- tai vähittäismyyjille, ei kuluttajaostoista.",
      "https://health-infobase.canada.ca/substance-use/vaping/sales/ ; https://laws-lois.justice.gc.ca/eng/regulations/SOR-2023-123/FullText.html ; source/CANADA_2024_DONOR_CLOSURE_PACK.md",
      "2026-07-25",
      "30 207 822,87 + 558 947 200,26 + 316 329 158,83 + 255 269 614,82 = 1 160 753 796,78 CAD; osuudet lasketaan tästä summasta.",
      "Nettomyynti on myynti vähennettynä palautuksilla ja arvot ilmoitetaan ilman veroja ja maksuja. Nestettä sisältävä laite tai osa yhdistää laite- ja neste-arvoa.",
      "Vahvistettu",
      "Toimitusosuuksia ei saa soveltaa retail-arvoon laite–neste-jaoksi eikä eri tapahtumatasoja summata.",
    ]
    : [
      "Health Canada's four 2024 categories sum to CAD 1,160,753,796.78 of net shipment value, 118,901,910 units and 1,251,843 litres.",
      "Market size",
      "Value shares are: part/device without substance 2.602%, device with substance 48.154%, part with substance 27.252% and vaping substance 21.992%. These are shipments to wholesalers or retailers, not consumer purchases.",
      "https://health-infobase.canada.ca/substance-use/vaping/sales/ ; https://laws-lois.justice.gc.ca/eng/regulations/SOR-2023-123/FullText.html ; source/CANADA_2024_DONOR_CLOSURE_PACK.md",
      "2026-07-25",
      "CAD 30,207,822.87 + 558,947,200.26 + 316,329,158.83 + 255,269,614.82 = CAD 1,160,753,796.78; shares use this total.",
      "Net sales are sales less returns and values are reported excluding taxes and duties. A device or part containing substance combines hardware and liquid value.",
      "Confirmed",
      "Do not apply shipment shares to retail as a device/liquid split and do not add transaction stages.",
    ];

  const existingAddition = output.findIndex((row) => (
    row[0].startsWith(language === "fi"
      ? "Uuden-Seelannin erillinen vuoden 2024 RPS"
      : "New Zealand's separate supported 2024 RPS")
    || row[0].startsWith(language === "fi"
      ? "Uuden-Seelannin vuoden 2024 tunnistetun"
      : "New Zealand's supported 2024 identified")
  ));
  if (existingAddition < 0) {
    output.splice(nzScopeIndex + 1, 0, ...registerAdditions[language]);
  } else {
    output.splice(existingAddition, registerAdditions[language].length, ...registerAdditions[language]);
  }

  const globalIndex = output.findIndex((row) => row[0].startsWith(language === "fi"
    ? "Maailmanlaajuista atlasestimaattia"
    : "No global atlas estimate"));
  if (globalIndex < 0) throw new Error(`${language}: global estimate row not found`);
  output[globalIndex] = language === "fi"
    ? [
      "Maailmanlaajuista atlasestimaattia ei ole hyväksytty julkaistavaksi.",
      "Markkinakoko",
      "Nolla hyväksyttyä donoria alittaa kolmen vähimmäisrajan. Uuden-Seelannin, EU:n, Kanadan, Saksan ja Yhdysvaltain 5 julkaistulla ehdokkaalla on jokaisella vähintään yksi hylätty tai avoin D1–D10-ehto; myös alue- ja sääntelytyyppien peittoportit puuttuvat.",
      "site/data/market-values.json (modelReadiness, donorProtocol ja donorCandidates)",
      "2026-07-27",
      "Kova portti: jokaisen donorin on läpäistävä D1–D10, ja lisäksi tarvitaan vähintään kolme yhteensopivaa donoria sekä molemmat peittoportit.",
      "Viralliset alarajat ja ulkoiset vertailuarvot säilyvät ristiintarkistuksina, mutta niitä ei lasketa hyväksytyiksi donoreiksi.",
      "Vahvistettu",
      "Älä julkaise yhtä maailmanarvoa ennen menetelmäporttien läpäisyä.",
    ]
    : [
      "No global atlas estimate has been approved for publication.",
      "Market size",
      "Zero accepted donors is below the minimum of three. Each of the five published New Zealand, EU, Canada, Germany and United States candidates has at least one failed or open D1–D10 criterion; the regional and regulatory-archetype coverage gates also remain unmet.",
      "site/data/market-values.json (modelReadiness, donorProtocol and donorCandidates)",
      "2026-07-27",
      "Hard gate: every donor must pass D1–D10, and at least three compatible donors plus both coverage gates are required.",
      "Official lower bounds and external benchmarks remain useful cross-checks but are not counted as accepted donors.",
      "Confirmed",
      "Do not publish a single global value before the methodology gates are met.",
    ];
  return output;
}

function rewriteText(target, desired) {
  const before = target?.text?.toString?.() ?? "";
  if (before === desired) return;
  const beforeLines = before.split("\n");
  const afterLines = desired.split("\n");
  if (beforeLines.length !== afterLines.length) {
    throw new Error(`Paragraph mismatch for ${before} -> ${desired}`);
  }
  for (let index = 0; index < beforeLines.length; index += 1) {
    target.text.replace(beforeLines[index], afterLines[index]);
  }
  const after = target?.text?.toString?.() ?? "";
  if (after !== desired) throw new Error(`Shape rewrite failed: ${after}`);
}

async function buildDeck(language, deckName, market, scenarios, fxData) {
  const outputPath = path.join(downloadDir, `pixan-bank-deck-${deckName}-${language}.pptx`);
  const seedPath = deckSeedPath(language, deckName);
  const presentation = await PresentationFile.importPptx(await FileBlob.load(seedPath));
  const snapshot = await presentation.inspect({ kind: "textbox,shape", maxChars: 600000 });
  for (const line of snapshot.ndjson.split("\n").filter(Boolean)) {
    const record = JSON.parse(line);
    if (typeof record.text !== "string") continue;
    const reviewedText = record.text
      .replaceAll("2026.07.24-17", releaseVersion)
      .replaceAll("2026-07-24", releaseDate);
    if (reviewedText === record.text) continue;
    rewriteText(presentation.resolve(record.id), reviewedText);
  }
  const update = deckUpdates[language][deckName];
  const fxPhrases = prominentDeckFxPhrases(language, market, scenarios, fxData);
  const nzCardValueShapeIds = new Set(["sh/i94r6xgz", "sh/v2tcn650"]);
  const nzCardSubtitleShapeIds = new Set(["sh/jadsz2xk", "sh/u1kbu1ov"]);
  const canadaCardValueShapeIds = new Set(["sh/ehwvat8n", "sh/a1wze9g7"]);
  const canadaRetailCardSubtitleShapeIds = new Set(["sh/c3e1gjyd"]);
  const canadaShipmentsCardSubtitleShapeIds = new Set(["sh/b2507exs"]);
  let nzFxMarkers = 0;
  let ftcFxMarkers = 0;
  let canadaFxMarkers = 0;
  const withFxEquivalents = (text) => {
    let output = String(text);
    if (output.includes(fxPhrases.nzObservedOriginal)) {
      nzFxMarkers += 1;
      output = output.replaceAll(
        fxPhrases.nzObservedOriginal,
        fxPhrases.nzObservedReplacement,
      );
    }
    if (output.includes(fxPhrases.nzModelOriginal)) {
      nzFxMarkers += 1;
      output = output.replaceAll(fxPhrases.nzModelOriginal, fxPhrases.nzModelReplacement);
    }
    if (output.includes(fxPhrases.ftcOriginal)) {
      ftcFxMarkers += 1;
      output = output.replaceAll(fxPhrases.ftcOriginal, fxPhrases.ftcReplacement);
    }
    if (output.includes(fxPhrases.canadaRetailOriginal)) {
      canadaFxMarkers += 1;
      output = output.replaceAll(
        fxPhrases.canadaRetailOriginal,
        fxPhrases.canadaRetailReplacement,
      );
    }
    if (output.includes(fxPhrases.canadaShipmentsOriginal)) {
      canadaFxMarkers += 1;
      output = output.replaceAll(
        fxPhrases.canadaShipmentsOriginal,
        fxPhrases.canadaShipmentsReplacement,
      );
    }
    return output;
  };
  for (const [shapeId, text] of Object.entries(update.shapes ?? {})) {
    if (nzCardValueShapeIds.has(shapeId)) {
      rewriteText(presentation.resolve(shapeId), text);
      continue;
    }
    if (nzCardSubtitleShapeIds.has(shapeId)) {
      nzFxMarkers += 1;
      rewriteText(presentation.resolve(shapeId), fxPhrases.nzCardSubtitle);
      continue;
    }
    if (canadaCardValueShapeIds.has(shapeId)) {
      rewriteText(presentation.resolve(shapeId), text);
      continue;
    }
    if (canadaRetailCardSubtitleShapeIds.has(shapeId)) {
      canadaFxMarkers += 1;
      rewriteText(presentation.resolve(shapeId), fxPhrases.canadaRetailCardSubtitle);
      continue;
    }
    if (canadaShipmentsCardSubtitleShapeIds.has(shapeId)) {
      canadaFxMarkers += 1;
      rewriteText(presentation.resolve(shapeId), fxPhrases.canadaShipmentsCardSubtitle);
      continue;
    }
    rewriteText(presentation.resolve(shapeId), withFxEquivalents(text));
  }
  for (const [tableId, changes] of Object.entries(update.tables ?? {})) {
    const table = presentation.resolve(tableId);
    for (const [row, column, value] of changes) {
      table.cells.set(row, column, withFxEquivalents(value));
    }
  }
  if (nzFxMarkers < 1 || ftcFxMarkers < 1 || canadaFxMarkers < 1) {
    throw new Error(`${language}/${deckName}: prominent NZ, FTC or Canada FX marker is missing`);
  }
  if (language === "fi") {
    const singleLineTitleIds = {
      short: ["sh/ozy1ofad"],
      medium: [
        "sh/ozy1ofad",
        "sh/d0jax03i",
        "sh/0ba143al",
        "sh/cf2tcr61",
        "sh/dcbud0ra",
        "sh/cbu58j2h",
      ],
      large: [
        "sh/ozy1ofad",
        "sh/0ba143al",
        "sh/cf2tcr61",
        "sh/dcbud0ra",
        "sh/g72x4zyd",
        "sh/0f2lgnmp",
        "sh/wbydknq1",
        "sh/9kby1g7m",
        "sh/gbedwfmx",
        "sh/hsn2l4bu",
        "sh/rq50vmp8",
        "sh/7a18rydc",
        "sh/0b65obm9",
        "sh/wbih4b6d",
        "sh/bq9orito",
        "sh/k3y5ov21",
        "sh/8v2pobax",
        "sh/0r6p4nul",
        "sh/ralgf21g",
      ],
    }[deckName];
    for (const shapeId of singleLineTitleIds) {
      const title = presentation.resolve(shapeId);
      title.text.fontSize = 32;
      title.text.wrap = "none";
      title.text.autoFit = "shrinkText";
    }
  }
  if (language === "en" && deckName === "large") {
    const title = presentation.resolve("sh/bq9orito");
    title.text.fontSize = 32;
    title.text.wrap = "none";
    title.text.autoFit = "shrinkText";
  }
  if (deckName === "medium") {
    presentation.resolve("sh/cbe5g3ih").text.fontSize = 18;
  }
  if (deckName === "short") {
    presentation.resolve("sh/p0batw72").text.fontSize = 18;
    const marketScopeSubtitle = presentation.resolve("sh/kbm987y5");
    marketScopeSubtitle.text.fontSize = language === "fi" ? 16 : 17;
    marketScopeSubtitle.text.autoFit = "shrinkText";
  }
  if (language === "fi" && deckName === "large") {
    presentation.resolve("sh/mpgj6t8j").text.fontSize = 18;
    for (const shapeId of ["sh/ihcvml4j", "sh/29grm1of", "sh/honqdwnu", "sh/0ji9wb6t"]) {
      const value = presentation.resolve(shapeId);
      value.text.fontSize = 28;
      value.text.wrap = "none";
      value.text.autoFit = "shrinkText";
    }
  }
  const sourceNotes = deckSourceNotes(fxData);
  for (const slide of presentation.slides.items) {
    slide.speakerNotes.text = sourceNotes;
    slide.speakerNotes.setVisible(true);
  }
  const renderDir = path.join(renderRoot, `${deckName}-${language}`);
  await fs.mkdir(renderDir, { recursive: true });
  for (let index = 0; index < presentation.slides.items.length; index += 1) {
    const slide = presentation.slides.items[index];
    const png = await presentation.export({
      slide,
      format: "png",
      scale: 1,
    });
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(
      path.join(renderDir, `slide-${String(index + 1).padStart(2, "0")}.png`),
      new Uint8Array(await png.arrayBuffer()),
    );
    await fs.writeFile(
      path.join(renderDir, `slide-${String(index + 1).padStart(2, "0")}.layout.json`),
      await layout.text(),
    );
  }
  const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(
    path.join(renderDir, "montage.webp"),
    new Uint8Array(await montage.arrayBuffer()),
  );
  await (await PresentationFile.exportPptx(presentation)).save(outputPath);
  return {
    path: outputPath,
    sha256: sha256(outputPath),
    bytes: fsSync.statSync(outputPath).size,
    slideCount: presentation.slides.items.length,
    renderDir,
  };
}

function colLetter(index) {
  let number = index;
  let output = "";
  while (number > 0) {
    number -= 1;
    output = String.fromCharCode(65 + (number % 26)) + output;
    number = Math.floor(number / 26);
  }
  return output;
}

function setWidths(sheet, widths, lastRow) {
  widths.forEach((width, index) => {
    const column = colLetter(index + 1);
    sheet.getRange(`${column}1:${column}${lastRow}`).format.columnWidthPx = width;
  });
}

function formatHeader(range) {
  range.format = {
    fill: COLORS.navy,
    font: { name: "Aptos", size: 10, bold: true, color: COLORS.white },
    verticalAlignment: "center",
    wrapText: true,
    borders: { bottom: { style: "medium", color: COLORS.teal } },
  };
}

function formatBody(range) {
  range.format = {
    font: { name: "Aptos", size: 9, color: COLORS.ink },
    verticalAlignment: "top",
    wrapText: true,
    borders: { insideHorizontal: { style: "thin", color: COLORS.line } },
  };
}

function titleBlock(sheet, endColumn, title, subtitle) {
  sheet.getRange(`A1:${endColumn}2`).merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange(`A1:${endColumn}2`).format = {
    fill: COLORS.navy,
    font: { name: "Aptos Display", size: 22, bold: true, color: COLORS.white },
    verticalAlignment: "center",
    horizontalAlignment: "left",
  };
  sheet.getRange(`A3:${endColumn}3`).merge();
  sheet.getRange("A3").values = [[subtitle]];
  sheet.getRange(`A3:${endColumn}3`).format = {
    fill: COLORS.paleGold,
    font: { name: "Aptos", size: 9, bold: true, color: COLORS.ink },
    verticalAlignment: "center",
    wrapText: true,
    borders: { bottom: { style: "thin", color: COLORS.teal } },
  };
  sheet.getRange("A1").format.rowHeightPx = 34;
  sheet.getRange("A2").format.rowHeightPx = 34;
  sheet.getRange("A3").format.rowHeightPx = 38;
}

async function readSourceRows(filePath, sheetName) {
  const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(filePath));
  const values = workbook.worksheets.getItem(sheetName).getRange("A1:E100").values;
  return values.slice(1).filter((row) => row.slice(0, 5).some((value) => String(value ?? "").trim()));
}

async function buildWorkbook(language, rows, sourceRows, eurRows) {
  const isFi = language === "fi";
  const headers = isFi ? FI_HEADERS : EN_HEADERS;
  const workbook = Workbook.create();
  const register = workbook.worksheets.add("Evidence Register");
  const summary = workbook.worksheets.add(isFi ? "Yhteenveto" : "Summary");
  const questions = workbook.worksheets.add(isFi ? "Tutkijan kysymykset" : "Reviewer questions");
  const sources = workbook.worksheets.add(isFi ? "Lähteet" : "Sources");
  const equivalents = workbook.worksheets.add(EUR_EQUIVALENT_SHEET_NAMES[language]);
  const evidenceEnd = rows.length + 1;

  register.showGridLines = false;
  register.getRange(`A1:I${evidenceEnd}`).values = [headers, ...rows];
  formatHeader(register.getRange("A1:I1"));
  formatBody(register.getRange(`A2:I${evidenceEnd}`));
  register.getRange("A1:I1").format.rowHeightPx = 44;
  register.getRange(`A2:I${evidenceEnd}`).format.rowHeightPx = 78;
  setWidths(register, [330, 170, 390, 370, 115, 300, 300, 125, 390], evidenceEnd);
  register.freezePanes.freezeRows(1);
  const evidenceTable = register.tables.add(`A1:I${evidenceEnd}`, true, `EvidenceRegister${language.toUpperCase()}`);
  evidenceTable.style = "TableStyleMedium2";
  evidenceTable.showHeaders = true;
  evidenceTable.showFilterButton = true;
  const statuses = isFi
    ? ["Vahvistettu", "Tuettu", "Oletus", "Puuttuu"]
    : ["Confirmed", "Supported", "Assumption", "Missing"];
  register.getRange(`H2:H${evidenceEnd}`).dataValidation = { rule: { type: "list", values: statuses } };
  for (const [status, fill] of [
    [statuses[0], COLORS.paleGreen],
    [statuses[1], COLORS.pale],
    [statuses[2], COLORS.paleGold],
    [statuses[3], COLORS.paleRed],
  ]) {
    register.getRange(`H2:H${evidenceEnd}`).conditionalFormats.add("containsText", {
      text: status,
      format: { fill, font: { bold: true, color: COLORS.ink } },
    });
  }
  const nzAdditionIndex = rows.findIndex((row) => row[0].startsWith(isFi
    ? "Uuden-Seelannin vuoden 2024 AIS/AVP"
    : "New Zealand's 2024 AIS/AVP"));
  if (nzAdditionIndex < 0) throw new Error(`${language}: New Zealand closure row is missing`);
  const nzAdditionSheetRow = nzAdditionIndex + 2;
  register.getRange(`A${nzAdditionSheetRow}:I${nzAdditionSheetRow}`).format.rowHeightPx = 124;
  register.getRange(`F${nzAdditionSheetRow}`).format.fill = COLORS.paleTeal;
  register.getRange(`F${nzAdditionSheetRow}`).format.font = {
    name: "Aptos",
    size: 9,
    bold: true,
    color: COLORS.ink,
  };
  register.getRange(`F${nzAdditionSheetRow}`).format.wrapText = true;

  summary.showGridLines = false;
  titleBlock(
    summary,
    "H",
    isFi ? "Pixan · evidenssipaketin yhteenveto" : "Pixan · public evidence package summary",
    isFi
      ? "Riippumaton julkinen evidenssikooste. Ei Pixan Oy:n virallinen kanta; ei tilintarkastus, arvonmääritys, oikeudellinen lausunto, sijoitussuositus tai lainasuositus."
      : "Independent public evidence summary. Not Pixan Oy's official position; not an audit, valuation, legal opinion, investment recommendation or lending recommendation.",
  );
  summary.getRange("A5:B8").values = [
    [isFi ? "Versio" : "Version", releaseVersion],
    [isFi ? "Päivitetty" : "Updated", releaseDate],
    [isFi ? "Rajaus" : "Scope", isFi
      ? "Julkinen ja riippumaton evidenssikooste; faktat, laskelmat, tulkinnat ja oletukset on erotettu."
      : "Public and independent evidence summary; facts, calculations, interpretations and assumptions are separated."],
    [isFi ? "Evidenssirivejä" : "Evidence rows", null],
  ];
  summary.getRange("B8").formulas = [[`=COUNTA('Evidence Register'!$A$2:$A$${evidenceEnd})`]];
  summary.getRange("A5:A8").format = {
    fill: COLORS.pale,
    font: { name: "Aptos", size: 10, bold: true, color: COLORS.muted },
    wrapText: true,
    horizontalAlignment: "left",
  };
  formatBody(summary.getRange("B5:B8"));
  summary.getRange("A10:B10").merge();
  summary.getRange("A10").values = [[isFi ? "Evidenssin jakauma" : "Evidence distribution"]];
  summary.getRange("A10:B10").format = {
    fill: COLORS.blue,
    font: { name: "Aptos", size: 12, bold: true, color: COLORS.white },
  };
  summary.getRange("A11:B14").values = statuses.map((status) => [status, null]);
  summary.getRange("B11").formulas = [[`=COUNTIF('Evidence Register'!$H$2:$H$${evidenceEnd},A11)`]];
  summary.getRange("B11:B14").fillDown();
  formatBody(summary.getRange("A11:B14"));
  summary.getRange("A11:A11").format.fill = COLORS.paleGreen;
  summary.getRange("A12:A12").format.fill = COLORS.pale;
  summary.getRange("A13:A13").format.fill = COLORS.paleGold;
  summary.getRange("A14:A14").format.fill = COLORS.paleRed;
  summary.getRange("A11:A14").format.font = { name: "Aptos", size: 10, bold: true, color: COLORS.ink };
  summary.getRange("A17:B17").merge();
  summary.getRange("A17").values = [[isFi ? "Kolme vahvinta rahoitusperustetta" : "Three strongest financing grounds"]];
  summary.getRange("A17:B17").format = {
    fill: COLORS.blue,
    font: { name: "Aptos", size: 12, bold: true, color: COLORS.white },
  };
  summary.getRange("A18:B20").values = isFi
    ? [
      [1, "EPO piti patentin voimassa muutetussa muodossa, ja B2-julkaisu on jäljitettävissä virallisiin lähteisiin."],
      [2, "Saksa tarjoaa viralliset mitättömyys- ja loukkausratkaisut niiden selvästi rajatuissa puitteissa."],
      [3, "Julkinen markkina-aineisto erottaa viralliset havainnot, proxyt, mallit ja puutteet näkyvästi."],
    ]
    : [
      [1, "EPO maintained the patent in amended form, and the B2 publication is traceable to official records."],
      [2, "Germany provides official nullity and infringement decisions within clearly stated limits."],
      [3, "The public market evidence visibly separates official observations, proxies, models and gaps."],
    ];
  formatBody(summary.getRange("A18:B20"));
  summary.getRange("A23:B23").merge();
  summary.getRange("A23").values = [[isFi ? "Neljä korjausta pankkikelpoisuuteen" : "Four corrections required for lender readiness"]];
  summary.getRange("A23:B23").format = {
    fill: COLORS.blue,
    font: { name: "Aptos", size: 12, bold: true, color: COLORS.white },
  };
  summary.getRange("A24:B27").values = isFi
    ? [
      [1, "Asianajajan allekirjoittama oikeus-, omistus-, rasite- ja vuosimaksumatriisi."],
      [2, "Riippumattomat testit ja claim chartit priorisoiduille tuotteille."],
      [3, "Toteutunut tai sopimuspohjainen kassavirta ja tarkastetut taloustiedot."],
      [4, "Riippumaton arvonmääritys ja vakuuden downside-analyysi."],
    ]
    : [
      [1, "Counsel-signed rights, title, encumbrance and fee-payment matrix."],
      [2, "Independent tests and claim charts for prioritised products."],
      [3, "Realised or contract-based cash flow and audited financial information."],
      [4, "Independent valuation and downside collateral analysis."],
    ];
  formatBody(summary.getRange("A24:B27"));
  setWidths(summary, [210, 720, 80, 80, 80, 80, 80, 80], 27);
  summary.getRange("A5:B27").format.rowHeightPx = 27;
  summary.getRange("B7:B7").format.rowHeightPx = 42;
  summary.getRange("A18:B20").format.rowHeightPx = 38;
  summary.getRange("A24:B27").format.rowHeightPx = 36;
  summary.freezePanes.freezeRows(3);

  questions.showGridLines = false;
  questions.getRange("A1:D6").values = isFi
    ? [
      ["Prioriteetti", "Todennäköinen kysymys", "Tarvittava näyttö", "Nykytila"],
      [1, "Mitä tarkalleen omistetaan ja missä oikeus on käytettävissä?", "Maakohtainen oikeusmatriisi", "Kattavasti puuttuu"],
      [2, "Mikä tuote täyttää mitkä patenttivaatimuksen rajat?", "Riippumaton testi ja claim chart", "Rajallinen Saksan näyttö"],
      [3, "Mitkä ovat varmennetut relevantit myynnit?", "Tuote–maa–aika-nettomyynti", "Puuttuu"],
      [4, "Mistä ja milloin velanhoitokassa syntyy?", "Sopimukset, maksut ja ennuste", "Puuttuu"],
      [5, "Mitä vakuudesta realisoidaan downside-tilanteessa?", "Riippumaton arvo ja realisointipolku", "Puuttuu"],
    ]
    : [
      ["Priority", "Likely question", "Required evidence", "Current status"],
      [1, "What exactly is owned, and where is the right enforceable?", "Country-specific rights matrix", "Missing comprehensively"],
      [2, "Which product satisfies which claim limitations?", "Independent test and claim chart", "Limited German evidence"],
      [3, "What are the verified relevant sales?", "Product–country–period net sales", "Missing"],
      [4, "From where and when does debt-service cash arise?", "Contracts, payments and forecast", "Missing"],
      [5, "What does the collateral realise in a downside case?", "Independent valuation and realisation path", "Missing"],
    ];
  formatHeader(questions.getRange("A1:D1"));
  formatBody(questions.getRange("A2:D6"));
  questions.getRange("A1:D1").format.rowHeightPx = 42;
  questions.getRange("A2:D6").format.rowHeightPx = 54;
  setWidths(questions, [140, 430, 400, 230], 6);
  questions.getRange("A1:A6").format.horizontalAlignment = "left";
  questions.freezePanes.freezeRows(1);
  const questionTable = questions.tables.add("A1:D6", true, `ReviewerQuestions${language.toUpperCase()}`);
  questionTable.style = "TableStyleMedium2";

  sources.showGridLines = false;
  sources.getRange(`A1:E${sourceRows.length + 1}`).values = [[
    isFi ? "Lähdetunnus" : "Source ID",
    isFi ? "Julkaisija" : "Publisher",
    isFi ? "Lähdeluokka" : "Source class",
    "URL",
    isFi ? "Haettu / data-ajankohta" : "Retrieved / data as of",
  ], ...sourceRows];
  formatHeader(sources.getRange("A1:E1"));
  formatBody(sources.getRange(`A2:E${sourceRows.length + 1}`));
  sources.getRange("A1:E1").format.rowHeightPx = 42;
  sources.getRange(`A2:E${sourceRows.length + 1}`).format.rowHeightPx = 42;
  setWidths(sources, [230, 300, 190, 600, 160], sourceRows.length + 1);
  sources.freezePanes.freezeRows(1);
  const sourcesTable = sources.tables.add(`A1:E${sourceRows.length + 1}`, true, `Sources${language.toUpperCase()}`);
  sourcesTable.style = "TableStyleMedium2";

  const equivalentEnd = eurRows.length + 1;
  equivalents.showGridLines = false;
  equivalents.getRange(`A1:N${equivalentEnd}`).values = [
    EUR_EQUIVALENT_HEADERS[language],
    ...eurRows.map((row) => [
      row.recordType,
      row.recordId,
      row.item,
      row.geography,
      row.year,
      row.period,
      row.originalAmount,
      row.currency,
      row.rateValue,
      null,
      row.rateId,
      row.sourceUrl,
      row.status,
      row.reason,
    ]),
  ];
  for (let index = 0; index < eurRows.length; index += 1) {
    const sheetRow = index + 2;
    const row = eurRows[index];
    if (row.status === "computed") {
      equivalents.getRange(`J${sheetRow}`).formulas = [[`=G${sheetRow}/I${sheetRow}`]];
    } else if (row.status === "already_eur") {
      equivalents.getRange(`J${sheetRow}`).formulas = [[`=G${sheetRow}`]];
    }
  }
  formatHeader(equivalents.getRange("A1:N1"));
  formatBody(equivalents.getRange(`A2:N${equivalentEnd}`));
  equivalents.getRange("A1:N1").format.rowHeightPx = 50;
  equivalents.getRange(`A2:N${equivalentEnd}`).format.rowHeightPx = 34;
  equivalents.getRange(`G2:J${equivalentEnd}`).format.numberFormat = "0.00000000000000";
  setWidths(
    equivalents,
    [150, 330, 260, 210, 90, 150, 190, 100, 210, 220, 290, 620, 150, 330],
    equivalentEnd,
  );
  equivalents.freezePanes.freezeRows(1);
  const equivalentsTable = equivalents.tables.add(
    `A1:N${equivalentEnd}`,
    true,
    `EurEquivalents${language.toUpperCase()}`,
  );
  equivalentsTable.style = "TableStyleMedium2";

  const outputPath = path.join(downloadDir, `pixan-bank-evidence-register-${language}.xlsx`);
  await (await SpreadsheetFile.exportXlsx(workbook)).save(outputPath);
  const reopened = await SpreadsheetFile.importXlsx(await FileBlob.load(outputPath));
  const reopenedRows = reopened.worksheets.getItem("Evidence Register").getRange(`A1:I${evidenceEnd}`).values;
  if (JSON.stringify(reopenedRows) !== JSON.stringify([headers, ...rows])) {
    throw new Error(`${language}: reopened workbook differs from reviewed register`);
  }
  const reopenedSummary = reopened.worksheets.getItem(isFi ? "Yhteenveto" : "Summary");
  const expectedSummaryFormulas = [
    `=COUNTA('Evidence Register'!$A$2:$A$${evidenceEnd})`,
    ...[11, 12, 13, 14].map(
      (row) => `=COUNTIF('Evidence Register'!$H$2:$H$${evidenceEnd},A${row})`,
    ),
  ];
  const reopenedSummaryFormulas = [
    reopenedSummary.getRange("B8").formulas[0][0],
    ...reopenedSummary.getRange("B11:B14").formulas.map((row) => row[0]),
  ];
  if (JSON.stringify(reopenedSummaryFormulas) !== JSON.stringify(expectedSummaryFormulas)) {
    throw new Error(`${language}: Summary formulas did not survive workbook reopen`);
  }
  const reopenedEquivalents = reopened.worksheets.getItem(EUR_EQUIVALENT_SHEET_NAMES[language]);
  const expectedEurFormulas = eurRows.map((row, index) => {
    const sheetRow = index + 2;
    if (row.status === "computed") return `=G${sheetRow}/I${sheetRow}`;
    if (row.status === "already_eur") return `=G${sheetRow}`;
    return "";
  });
  const reopenedEurFormulas = reopenedEquivalents
    .getRange(`J2:J${equivalentEnd}`)
    .formulas
    .map((row) => row[0] || "");
  if (JSON.stringify(reopenedEurFormulas) !== JSON.stringify(expectedEurFormulas)) {
    throw new Error(`${language}: EUR-equivalent formulas did not survive workbook reopen`);
  }
  const renderDir = path.join(renderRoot, `evidence-register-${language}`);
  await fs.mkdir(renderDir, { recursive: true });
  const sheetNames = [
    "Evidence Register",
    isFi ? "Yhteenveto" : "Summary",
    isFi ? "Tutkijan kysymykset" : "Reviewer questions",
    isFi ? "Lähteet" : "Sources",
    EUR_EQUIVALENT_SHEET_NAMES[language],
  ];
  for (const sheetName of sheetNames) {
    const preview = await reopened.render({ sheetName, autoCrop: "all", scale: 0.8, format: "png" });
    await fs.writeFile(
      path.join(renderDir, `${sheetName.toLowerCase().replace(/[^a-z0-9]+/g, "-")}.png`),
      new Uint8Array(await preview.arrayBuffer()),
    );
  }
  return {
    path: outputPath,
    sha256: sha256(outputPath),
    bytes: fsSync.statSync(outputPath).size,
    rowCount: rows.length,
    eurRowCount: eurRows.length,
    renderDir,
  };
}

function artifactManifestEntry(id, artifact) {
  const [deckName] = id.split("-deck-");
  const language = id.endsWith("-fi") ? "fi" : "en";
  const isRegister = id.startsWith("evidence-register");
  const titles = {
    "short-deck-en": ["Suppea pankkidekki (englanti)", "Concise bank deck (English)"],
    "large-deck-en": ["Laaja pankkidekki (englanti)", "Extended bank deck (English)"],
    "evidence-register-en": ["Evidence Register (englanti)", "Evidence Register (English)"],
    "short-deck-fi": ["Suppea pankkidekki (suomi)", "Concise bank deck (Finnish)"],
    "large-deck-fi": ["Laaja pankkidekki (suomi)", "Extended bank deck (Finnish)"],
    "evidence-register-fi": ["Evidence Register (suomi)", "Evidence Register (Finnish)"],
  };
  const fileName = path.basename(artifact.path);
  const entry = {
    id,
    kind: isRegister ? "xlsx" : "pptx",
    language,
    titleFi: titles[id][0],
    titleEn: titles[id][1],
    fileName,
    path: `downloads/${fileName}`,
    sha256: artifact.sha256,
    bytes: artifact.bytes,
  };
  if (isRegister) entry.rowCount = artifact.rowCount;
  else {
    if (!publicDeckNames.includes(deckName)) throw new Error(`Unknown deck id ${id}`);
    entry.slideCount = artifact.slideCount;
  }
  return entry;
}

async function writeReleaseLocks(artifacts) {
  const changelog = JSON.parse(await fs.readFile(path.join(dataDir, "changelog.json"), "utf8"));
  const release = changelog.releases?.[0];
  if (
    release?.id !== releaseId
    || release?.version !== releaseVersion
    || changelog.asOf !== releaseDate
  ) {
    throw new Error("The public changelog is not locked to the reviewed v32 release");
  }
  const artifactOrder = [
    "short-deck-en",
    "large-deck-en",
    "evidence-register-en",
    "short-deck-fi",
    "large-deck-fi",
    "evidence-register-fi",
  ];
  const reviewedInputPaths = [
    "scripts/artifact-build/build_bank_package_artifacts.mjs",
    "scripts/build_global_base.py",
    "scripts/refresh_global_base.py",
    "scripts/build_vendor_response_control.py",
    ...seedPaths,
    "site/data/atlas.json",
    "site/data/changelog.json",
    "site/data/global-base-layer.json",
    "site/data/global-base-layer.csv",
    "site/data/market-values.json",
    "site/data/patent-history.json",
    "site/data/donor-cockpit.json",
    "site/data/third-donor-screen.json",
    "site/data/country-scenarios.json",
    "site/data/evidence-lanes.json",
    "site/data/fx-rates.json",
    "site/data/vendor-response-control.json",
    "site/data/vendor-response-control.csv",
    "site/schemas/fx-rates.schema.json",
    "site/schemas/global-base-layer.schema.json",
    "site/schemas/third-donor-screen.schema.json",
    "source/bank-evidence-register-en.json",
    "source/fx-rates.json",
    "source/global-base-config.json",
    "source/global-base-observations.json",
    "source/country-method-route-config.json",
    "source/COUNTRY_METHOD_ROUTE_MAP.md",
    "source/FIVE_COUNTRY_METHOD_SPRINT_2026-07-27.md",
    "source/ITALY_ADM_RESPONSE_BOUNDARY_2026-07-24.md",
    "source/POLAND_EUCEG_ANNUAL_SALES_REQUEST_2026-07-28.md",
    "source/vendor-response-control.json",
    "source/third-donor-screen.json",
    "source/schemas/fx-rates.schema.json",
    "source/schemas/global-base-layer.schema.json",
    "source/schemas/third-donor-screen.schema.json",
    "source/NZ_2024_ANNUAL_RETURNS_RECONCILIATION.md",
    "source/NZ_2024_DONOR_CLOSURE_PACK.md",
    "source/NZ_2024_D8_D10_OFFICIAL_SOURCE_AUDIT.md",
    "source/NZ_2024_WORKBOOK_MANIFEST.json",
    "source/NZ_2024_PRODUCT_SCOPE_AUDIT.json",
    "scripts/analyze_nz_2024_returns.py",
    "source/NZ_2024_RPS_RETAIL_VALUE_SENSITIVITY.md",
    "source/NZ_2023_ANNUAL_RETURNS_FAIL_CLOSED.md",
    "source/CANADA_RCS_2019_2025_RETAIL_SALES.md",
    "source/CANADA_2024_DONOR_CLOSURE_PACK.md",
    "source/CANADA_2024_D5_D7_D10_OFFICIAL_SOURCE_AUDIT.md",
    "source/THIRD_DONOR_SCREEN_2026-07-27.md",
    "source/POLAND_2020_2025_RECONSTRUCTION.md",
    "source/FOLLOW_UP_DRAFTS_2026-07-28.md",
    "source/US_FTC_2015_2021_REPORTED_SALES.md",
    "source/SWEDEN_FHM_REGISTRATION_STRUCTURE_2018_2026.md",
  ];
  const reviewedInputs = reviewedInputPaths.map((relative) => ({
    path: relative,
    sha256: sha256(path.join(repo, relative)),
  }));
  const templateInputs = seedPaths.map((relative) => ({
    path: relative,
    sha256: sha256(path.join(repo, relative)),
  }));
  const lockArtifacts = artifactOrder.map((id) => {
    const item = artifactManifestEntry(id, artifacts[id]);
    return {
      id: item.id,
      kind: item.kind,
      language: item.language,
      path: `site/${item.path}`,
      sha256: item.sha256,
      bytes: item.bytes,
      ...(item.slideCount ? { slideCount: item.slideCount } : { rowCount: item.rowCount }),
    };
  });
  const lock = {
    schemaVersion: 2,
    release: {
      id: release.id,
      version: release.version,
      publishedAt: release.publishedAt,
    },
    asOf: changelog.asOf,
    reviewedInputs,
    artifacts: lockArtifacts,
    generatedBy: {
      tool: "@oai/artifact-tool",
      toolVersion: artifactToolVersion,
      sourceLocked: true,
      byteReproducible: false,
      sourceTemplates: templateInputs,
      executionNote: "Both language versions were authored and rendered from reviewed public aggregates. The 60-row bilingual registers and 84-observation, 24-source market dataset share one v32 release boundary. The 75 official observations remain separated into 39 market measures across seven countries and 36 Swedish FHM register-structure counts. The 195-country method control separates 28 reviewed country plans, 0 reviewed source leads, 15 regional EU TPD reporting patterns and 152 country-unscoped proxy routes; all remain ineligible for the global roll-up. Five new country rows document methods, not measured sales. Belgium's rounded nine-month tax-volume indicator and Italy's exact PLI consumption-tax receipts are fiscal anchors, not retail value, full-year sales, volume growth or donor evidence. ECigIntelligence and Circana follow-ups were sent on 28 July; the Euromonitor draft was superseded by the comprehensive 27 July request. No vendor route is scored or authorised for purchase. The donor gate remains 0/3 and the global estimate remains not_computed.",
      qualityAssurance: {
        exactRegisterRowsAfterReopen: true,
        summaryFormulasAfterReopen: true,
        allSlidesRendered: true,
        allWorkbookSheetsRendered: true,
        sourcesNotesOnEverySlide: true,
        eurEquivalentRowsAfterReopen: true,
        fxSourcesInDeckNotes: true,
        globalEstimateGate: "0/3; not_computed",
      },
    },
  };
  const lockPath = path.join(sourceDir, "bank-package-en-lock.json");
  await fs.writeFile(lockPath, `${JSON.stringify(lock, null, 2)}\n`);
  const manifest = {
    schemaVersion: 2,
    generatedFromPublicDataOnly: true,
    release: {
      id: release.id,
      version: release.version,
      publishedAt: release.publishedAt,
    },
    asOf: changelog.asOf,
    cadence: packageCadence,
    languages: ["en", "fi"],
    publicBoundary: {
      en: "Independent public evidence summary. Not Pixan Oy's official position; not an audit, valuation, legal opinion, investment recommendation or lending recommendation.",
      fi: "Riippumaton julkinen evidenssikooste. Ei Pixan Oy:n virallinen kanta; ei tilintarkastus, arvonmääritys, oikeudellinen lausunto, sijoitussuositus tai lainasuositus.",
    },
    templateInputs,
    inputs: [
      ...reviewedInputs,
      {
        path: "source/bank-package-en-lock.json",
        sha256: sha256(lockPath),
      },
    ],
    artifacts: artifactOrder.map((id) => artifactManifestEntry(id, artifacts[id])),
  };
  await fs.writeFile(
    path.join(dataDir, "bank-package-manifest.json"),
    `${JSON.stringify(manifest, null, 2)}\n`,
  );
  return { lock, manifest };
}

async function main() {
  await assertDailyBuildWindow();
  await fs.mkdir(qaDir, { recursive: true });
  await fs.mkdir(renderRoot, { recursive: true });
  const market = JSON.parse(await fs.readFile(path.join(dataDir, "market-values.json"), "utf8"));
  const scenarios = JSON.parse(await fs.readFile(path.join(dataDir, "country-scenarios.json"), "utf8"));
  const globalBase = JSON.parse(await fs.readFile(path.join(dataDir, "global-base-layer.json"), "utf8"));
  const vendorControl = JSON.parse(await fs.readFile(path.join(dataDir, "vendor-response-control.json"), "utf8"));
  const publicFx = JSON.parse(await fs.readFile(path.join(dataDir, "fx-rates.json"), "utf8"));
  const sourceFx = JSON.parse(await fs.readFile(path.join(sourceDir, "fx-rates.json"), "utf8"));
  const publicThirdDonorScreen = JSON.parse(await fs.readFile(path.join(dataDir, "third-donor-screen.json"), "utf8"));
  const sourceThirdDonorScreen = JSON.parse(await fs.readFile(path.join(sourceDir, "third-donor-screen.json"), "utf8"));
  validateV27MarketEvidence(market);
  validateGlobalBase(globalBase);
  validateVendorGateBoundary(vendorControl);
  validateReviewedFx(publicFx, sourceFx);
  validateThirdDonorScreen(publicThirdDonorScreen, sourceThirdDonorScreen);
  const publicFxSchemaPath = path.join(repo, "site", "schemas", "fx-rates.schema.json");
  const sourceFxSchemaPath = path.join(sourceDir, "schemas", "fx-rates.schema.json");
  if (!fsSync.readFileSync(publicFxSchemaPath).equals(fsSync.readFileSync(sourceFxSchemaPath))) {
    throw new Error("Public FX schema differs from the reviewed source schema");
  }
  const publicGlobalBaseSchemaPath = path.join(repo, "site", "schemas", "global-base-layer.schema.json");
  const sourceGlobalBaseSchemaPath = path.join(sourceDir, "schemas", "global-base-layer.schema.json");
  if (!fsSync.readFileSync(publicGlobalBaseSchemaPath).equals(fsSync.readFileSync(sourceGlobalBaseSchemaPath))) {
    throw new Error("Public global-base schema differs from the reviewed source schema");
  }
  const publicThirdDonorSchemaPath = path.join(repo, "site", "schemas", "third-donor-screen.schema.json");
  const sourceThirdDonorSchemaPath = path.join(sourceDir, "schemas", "third-donor-screen.schema.json");
  if (!fsSync.readFileSync(publicThirdDonorSchemaPath).equals(fsSync.readFileSync(sourceThirdDonorSchemaPath))) {
    throw new Error("Public third-donor schema differs from the reviewed source schema");
  }
  const eurRows = buildEurEquivalentRows(market, scenarios, publicFx);
  const fxSourceUrls = [
    publicFx.provider.datasetUrl,
    publicFx.provider.methodologyUrl,
    ...publicFx.rates.map((rate) => rate.sourceUrl),
  ];
  const fiCsvPath = path.join(dataDir, "bank-evidence-register.csv");
  const enCsvPath = path.join(dataDir, "bank-evidence-register-en.csv");
  const fiCsv = parseCsv((await fs.readFile(fiCsvPath, "utf8")).replace(/^\uFEFF/, ""));
  const enCsv = parseCsv((await fs.readFile(enCsvPath, "utf8")).replace(/^\uFEFF/, ""));
  if (JSON.stringify(fiCsv[0]) !== JSON.stringify(FI_HEADERS)) throw new Error("Finnish register headers differ");
  if (JSON.stringify(enCsv[0]) !== JSON.stringify(EN_HEADERS)) throw new Error("English register headers differ");
  const fiRows = upgradeRegister(fiCsv.slice(1), "fi");
  const enRows = upgradeRegister(enCsv.slice(1), "en");
  assertRegister(fiRows, FI_HEADERS, new Set(["Vahvistettu", "Tuettu", "Oletus", "Puuttuu"]));
  assertRegister(enRows, EN_HEADERS, new Set(["Confirmed", "Supported", "Assumption", "Missing"]));

  const fiSourceRows = ensureSourceCoverage(
    await readSourceRows(workbookSeedPath("fi"), "Lähteet"),
    fiRows,
    fxSourceUrls,
  );
  const enSourceRows = ensureSourceCoverage(
    await readSourceRows(workbookSeedPath("en"), "Sources"),
    enRows,
    fxSourceUrls,
  );

  await fs.writeFile(fiCsvPath, csvText(FI_HEADERS, fiRows));
  await fs.writeFile(enCsvPath, csvText(EN_HEADERS, enRows));
  await fs.writeFile(
    path.join(sourceDir, "bank-evidence-register-en.json"),
    `${JSON.stringify({ headers: EN_HEADERS, rows: enRows }, null, 2)}\n`,
  );

  const artifacts = {};
  for (const language of ["en", "fi"]) {
    for (const deckName of publicDeckNames) {
      artifacts[`${deckName}-deck-${language}`] = await buildDeck(
        language,
        deckName,
        market,
        scenarios,
        publicFx,
      );
    }
  }
  artifacts["evidence-register-fi"] = await buildWorkbook("fi", fiRows, fiSourceRows, eurRows);
  artifacts["evidence-register-en"] = await buildWorkbook("en", enRows, enSourceRows, eurRows);
  for (const artifact of Object.values(artifacts)) {
    await fs.rm(`${artifact.path}.inspect.ndjson`, { force: true });
  }
  const releaseLocks = await writeReleaseLocks(artifacts);
  const qa = {
    artifacts,
    release: releaseLocks.manifest.release,
    artifactToolVersion,
    templateInputs: releaseLocks.manifest.templateInputs,
    manifestSha256: sha256(path.join(dataDir, "bank-package-manifest.json")),
    lockSha256: sha256(path.join(sourceDir, "bank-package-en-lock.json")),
  };
  await fs.writeFile(path.join(qaDir, "artifact-build.json"), `${JSON.stringify(qa, null, 2)}\n`);
  process.stdout.write(`${JSON.stringify(qa, null, 2)}\n`);
}

await main();
