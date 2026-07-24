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
const qaDir = path.join(repo, "tmp", "bank-v18", "qa");
const renderRoot = path.join(repo, "tmp", "bank-v18", "renders");
const releaseVersion = "2026.07.24-18";
const artifactToolPackageUrl = new URL("../package.json", import.meta.resolve("@oai/artifact-tool"));
const artifactToolPackage = JSON.parse(await fs.readFile(artifactToolPackageUrl, "utf8"));
if (
  artifactToolPackage.name !== "@oai/artifact-tool"
  || !/^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$/.test(String(artifactToolPackage.version ?? ""))
) {
  throw new Error("Unable to resolve the active @oai/artifact-tool package version");
}
const artifactToolVersion = artifactToolPackage.version;

const seedPaths = [
  "scripts/artifact-build/seeds/v17/pixan-bank-deck-short-en.pptx",
  "scripts/artifact-build/seeds/v17/pixan-bank-deck-medium-en.pptx",
  "scripts/artifact-build/seeds/v17/pixan-bank-deck-large-en.pptx",
  "scripts/artifact-build/seeds/v17/pixan-bank-evidence-register-en.xlsx",
  "scripts/artifact-build/seeds/v17/pixan-bank-deck-short-fi.pptx",
  "scripts/artifact-build/seeds/v17/pixan-bank-deck-medium-fi.pptx",
  "scripts/artifact-build/seeds/v17/pixan-bank-deck-large-fi.pptx",
  "scripts/artifact-build/seeds/v17/pixan-bank-evidence-register-fi.xlsx",
];

const DECK_SOURCE_URLS = [
  "https://register.epo.org/application?number=EP14836345&lng=en&tab=main",
  "https://data.epo.org/publication-server/rest/v1.2/patents/EP3032975NWB2/document.pdf",
  "https://www.rechtsprechung-im-internet.de/jportal/?quelle=jlink&docid=JURE269032275&psml=bsjrsprod.psml",
  "https://www.gesetze-bayern.de/Content/Document/Y-300-Z-BECKRS-B-2026-N-14206",
  "https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2024",
  "https://www.ftc.gov/reports/e-cigarette-report-2021",
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
        "sh/doj29oba": "Julkinen riippumaton evidenssikooste · 2026.07.24-18 · 2026-07-24 · Lähteet: Health Canada; New Zealand Ministry of Health; Destatis; Vero; Sejm; Ruotsin hallitus; FTC; European Commission; IMARC; GVR; Fortune",
        "sh/0ba143al": "Globaali markkina-arvo ei ole vielä tuettu",
        "sh/ih8ju9sn": "27",
        "sh/kbm987y5": "virallista vuosihavaintoa 7 maasta",
        "sh/i94r6xgz": "533,7–731,2 milj. NZD",
        "sh/jadsz2xk": "Uusi-Seelanti 2024: tuettu vähittäisherkkyys",
        "sh/v6tsv2xo": "5/5 ehdokasta jäi D1–D10-portin ulkopuolelle; hyväksytty donor-portti on 0/3.",
        "sh/p0batw72": "NZ 2024: 533,7–731,2 milj. NZD on tuettu malli. FTC 2021: 2,763 mrd USD on valmistajaraportointia. EU- ja kaupallisia lukuja ei summata.",
      },
    },
    medium: {
      shapes: {
        "sh/ml07i9sv": "Julkinen riippumaton evidenssikooste · 2026.07.24-18 · 2026-07-24 · Lähteet: Market-values; FTC; IMARC; GVR; Fortune; European Commission",
        "sh/zi98nu94": "Markkinakoko on haarukka — ei yksi luku",
        "sh/pc76hkr2": "27",
        "sh/h4bupgn6": "virallista vuosihavaintoa 7 maasta",
        "sh/v2tcn650": "533,7–731,2 milj. NZD",
        "sh/u1kbu1ov": "Uusi-Seelanti 2024: tuettu vähittäisherkkyys",
        "sh/i54bylor": "5/5 ehdokasta jäi D1–D10-portin ulkopuolelle; hyväksytty donor-portti on 0/3.",
        "sh/cbe5g3ih": "NZ 2024: 533,7–731,2 milj. NZD on tuettu malli. FTC 2021: 2,763 mrd USD on valmistajaraportointia. EU- ja kaupallisia lukuja ei summata.",
      },
      tables: {
        "tb/nq547y9g": [[3, 2, "7 maan viralliset reitit"]],
        "tb/rexkf2d4": [[1, 2, "0/3 retail-luovuttajaa; 5 ehdokasta jäi D1–D10-portin ulkopuolelle"]],
      },
    },
    large: {
      shapes: {
        "sh/21gnuts7": "Julkinen riippumaton evidenssikooste · 2026.07.24-18 · 2026-07-24 · Lähteet: Health Canada; New Zealand Ministry of Health; Destatis; Vero; Sejm; FTC",
        "sh/q5wjelsz": "•  EPO:n muutettu EP3032975B2 ja Saksan kaksi virallista ratkaisua muodostavat oikeusnäytön ankkurin.\n•  Markkina-aineistossa on 27 virallista vuosihavaintoa 7 maasta, mutta luovuttajaportti on 0/3.\n•  Rahoitusrakenne tarvitsee kansalliset oikeudet, claim-mapped sales -sillan, kassavirran ja riippumattoman arvonmäärityksen.",
        "sh/bq9orito": "Valitut viralliset reitit: 27 havaintoa 7 maasta",
        "sh/6hw3y9sb": "Nykyinen hyväksytty donor-portti on 0/3; kaikki 5 ehdokasta jäivät ulkopuolelle.",
        "sh/rip4retw": "•  Jokaisen ehdokkaan on läpäistävä kaikki 10 ehtoa (D1–D10).\n•  Uuden-Seelannin 533,7–731,2 milj. NZD vähittäisherkkyys on tuettu malli; FTC:n 2,763 mrd USD vuoden 2021 reitti on valmistajaraportointia. Kumpikaan ei ole täydellinen kuluttajavähittäisarvo tai hyväksytty donor.\n•  Alue- ja sääntelytyyppien peitto sekä suora validointi suurissa talouksissa vaaditaan vielä.",
      },
      tables: {
        "tb/m983m983": [
          [0, 2, "Virallinen havainto / tuettu malli"],
          [4, 2, "virallinen raakareitti 280,685 milj. NZD; tunnistetun vaping-vähittäismyynnin tuettu herkkyys 533,7–731,2 milj. NZD, ei havaittu markkina-arvo"],
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
        "sh/doj29oba": "Independent public evidence summary · 2026.07.24-18 · 2026-07-24 · Sources: Health Canada; New Zealand Ministry of Health; Destatis; Vero; Sejm; Swedish Government; FTC; European Commission; IMARC; GVR; Fortune",
        "sh/0ba143al": "Market evidence is transparent; a global value is not yet supported",
        "sh/ih8ju9sn": "27",
        "sh/kbm987y5": "official annual observations from 7 countries",
        "sh/i94r6xgz": "NZD 533.7–731.2m",
        "sh/jadsz2xk": "New Zealand 2024: supported retail sensitivity",
        "sh/v6tsv2xo": "5/5 candidates remain outside the D1–D10 gate; the accepted-donor count is 0/3.",
        "sh/p0batw72": "NZ 2024: NZD 533.7–731.2m is a supported model. FTC 2021: USD 2.763bn is manufacturer reporting. EU and commercial figures are not summed.",
      },
    },
    medium: {
      shapes: {
        "sh/ml07i9sv": "Independent public evidence summary · 2026.07.24-18 · 2026-07-24 · Sources: Market-values; FTC; IMARC; GVR; Fortune; European Commission",
        "sh/zi98nu94": "Market size remains a range — not a single value",
        "sh/pc76hkr2": "27",
        "sh/h4bupgn6": "official annual observations from 7 countries",
        "sh/v2tcn650": "NZD 533.7–731.2m",
        "sh/u1kbu1ov": "New Zealand 2024: supported retail sensitivity",
        "sh/i54bylor": "5/5 candidates remain outside the D1–D10 gate; the accepted-donor count is 0/3.",
        "sh/cbe5g3ih": "NZ 2024: NZD 533.7–731.2m is a supported model. FTC 2021: USD 2.763bn is manufacturer reporting. EU and commercial figures are not summed.",
      },
      tables: {
        "tb/nq547y9g": [[3, 2, "official routes from 7 countries"]],
        "tb/rexkf2d4": [[1, 2, "0/3 retail-value donors; 5 candidates remain outside the D1–D10 gate"]],
      },
    },
    large: {
      shapes: {
        "sh/21gnuts7": "Independent public evidence summary · 2026.07.24-18 · 2026-07-24 · Sources: Health Canada; New Zealand Ministry of Health; Destatis; Vero; Sejm; FTC",
        "sh/q5wjelsz": "•  The amended EP3032975B2 and two official German decisions anchor the legal evidence.\n•  The market dataset contains 27 official annual observations from 7 countries, but the donor gate is 0/3.\n•  A financing structure requires national rights, a claim-mapped-sales bridge, cash flow and an independent valuation.",
        "sh/bq9orito": "Selected official routes: 27 observations across 7 countries",
        "sh/6hw3y9sb": "The current accepted-donor gate is 0/3; all 5 candidates remain outside the count.",
        "sh/rip4retw": "•  Every candidate must pass all 10 criteria (D1–D10).\n•  New Zealand's NZD 533.7–731.2m retail sensitivity is a supported model; the FTC's 2021 USD 2.763bn route is manufacturer reporting. Neither is complete consumer-retail value or an accepted donor.\n•  Coverage across regions and regulatory types, plus direct validation in major economies, is still required.",
      },
      tables: {
        "tb/m983m983": [
          [0, 2, "Official observation / supported model"],
          [4, 2, "official raw route NZD 280.685m; supported identified-vaping retail sensitivity NZD 533.7–731.2m, not an observed market value"],
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
      "Uuden-Seelannin vuoden 2024 tunnistetun sähkötupakkavähittäismyynnin tuettu herkkyysväli on 533 662 383,68–731 175 792,50 NZD ja perusskenaario 641 811 687,89 NZD.",
      "Markkinakoko",
      "Matalan, perus- ja korkean skenaarion yhdistetyt arvot ovat 533 662 383,68 / 641 811 687,89 / 731 175 792,50 NZD. Malli yhdistää erikoisvähittäiskaupan ankkurin yleisvähittäiskaupan määrä- ja hintamalliin.",
      "https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2024 ; source/NZ_2024_RPS_RETAIL_VALUE_SENSITIVITY.md",
      "2026-07-24",
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
      "2026-07-24",
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
      "site/data/evidence-lanes.json ; site/data/donor-cockpit.json ; site/data/country-scenarios.json",
      "2026-07-24",
      "Fail-closed-portit: puuttuva tai virheellinen syöte tuottaa tilan not_computed eikä nollaa.",
      "Vain tarkistetut julkiset koontitiedot ja menetelmät ovat julkisella kaistalla; lisensoitu ja yksityinen aineisto eivät siirry repositorioon.",
      "Vahvistettu",
      "Maailmanarvo pysyy laskematta, kunnes vähintään kolme donoria sekä molemmat peittoportit hyväksytään.",
    ],
  ],
  en: [
    [
      "New Zealand's supported 2024 identified-vaping retail sensitivity is NZD 533,662,383.68–731,175,792.50, with a base case of NZD 641,811,687.89.",
      "Market size",
      "The combined low, base and high cases are NZD 533,662,383.68 / 641,811,687.89 / 731,175,792.50. The model combines the specialist-retailer anchor with a general-retailer quantity-and-price model.",
      "https://www.health.govt.nz/regulation-legislation/vaping-herbal-smoking-and-smokeless-tobacco/requirements/complete-a-notifiable-product-annual-return/annual-returns-2024 ; source/NZ_2024_RPS_RETAIL_VALUE_SENSITIVITY.md",
      "2026-07-24",
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
      "2026-07-24",
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
      "site/data/evidence-lanes.json ; site/data/donor-cockpit.json ; site/data/country-scenarios.json",
      "2026-07-24",
      "Fail-closed gates: a missing or invalid input returns not_computed rather than zero.",
      "Only reviewed public aggregates and methods enter the public lane; licensed and private material do not enter the repository.",
      "Confirmed",
      "The global value remains uncomputed until at least three donors and both coverage gates are accepted.",
    ],
  ],
};

function sha256(filePath) {
  return crypto.createHash("sha256").update(fsSync.readFileSync(filePath)).digest("hex");
}

function sha256Text(value) {
  return crypto.createHash("sha256").update(String(value)).digest("hex");
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
  if (!nzRate || !usRate) throw new Error("Deck FX source rates are unavailable");
  const sourceUrls = [
    ...DECK_SOURCE_URLS,
    fxData.provider.datasetUrl,
    fxData.provider.methodologyUrl,
    nzRate.sourceUrl,
    usRate.sourceUrl,
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
    output.push([sourceId, publisher, sourceClass, url, "2026-07-24"]);
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

function formatDeckNumber(value, digits, language) {
  const output = Number(value).toFixed(digits);
  return language === "fi" ? output.replace(".", ",") : output;
}

function prominentDeckFxPhrases(language, market, scenarios, fxData) {
  const nz = (scenarios?.countryYearScenarios ?? []).find(
    (item) => item.scenarioId === "NZ-2024-RETAIL-RANGE",
  );
  const ftc = (market?.observations ?? []).find(
    (item) => item.observationId === "US-2021-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES",
  );
  const nzLow = assessArtifactEur({
    value: nz?.inputs?.low?.value,
    currency: nz?.currency,
    unit: nz?.currency,
    year: nz?.year,
    period: "calendar_year",
  }, fxData);
  const nzHigh = assessArtifactEur({
    value: nz?.inputs?.high?.value,
    currency: nz?.currency,
    unit: nz?.currency,
    year: nz?.year,
    period: "calendar_year",
  }, fxData);
  const ftcEur = assessArtifactEur(ftc, fxData);
  const nzComputed = nzLow.status === "computed" && nzHigh.status === "computed";
  const ftcComputed = ftcEur.status === "computed";
  const nzEurLow = nzComputed ? Number(nz.inputs.low.value) / nzLow.rateValue : null;
  const nzEurHigh = nzComputed ? Number(nz.inputs.high.value) / nzHigh.rateValue : null;
  const ftcEurValue = ftcComputed ? Number(ftc.value) / ftcEur.rateValue : null;
  if (language === "fi") {
    return {
      nzOriginal: "533,7–731,2 milj. NZD",
      nzReplacement: nzComputed
        ? `533,7–731,2 milj. NZD (≈${formatDeckNumber(nzEurLow / 1e6, 1, language)}–${formatDeckNumber(nzEurHigh / 1e6, 1, language)} milj. EUR; ECB 2024)`
        : "533,7–731,2 milj. NZD (EUR not_computed)",
      nzCardSubtitle: nzComputed
        ? `≈${formatDeckNumber(nzEurLow / 1e6, 1, language)}–${formatDeckNumber(nzEurHigh / 1e6, 1, language)} milj. EUR · ECB 2024`
        : "EUR not_computed · NZ 2024",
      ftcOriginal: "2,763 mrd USD",
      ftcReplacement: ftcComputed
        ? `2,763 mrd USD (≈${formatDeckNumber(ftcEurValue / 1e9, 3, language)} mrd EUR; ECB 2021)`
        : "2,763 mrd USD (EUR not_computed)",
    };
  }
  return {
    nzOriginal: "NZD 533.7–731.2m",
    nzReplacement: nzComputed
      ? `NZD 533.7–731.2m (≈EUR ${formatDeckNumber(nzEurLow / 1e6, 1, language)}–${formatDeckNumber(nzEurHigh / 1e6, 1, language)}m; ECB 2024)`
      : "NZD 533.7–731.2m (EUR not_computed)",
    nzCardSubtitle: nzComputed
      ? `≈EUR ${formatDeckNumber(nzEurLow / 1e6, 1, language)}–${formatDeckNumber(nzEurHigh / 1e6, 1, language)}m · ECB 2024`
      : "EUR not_computed · NZ 2024",
    ftcOriginal: "USD 2.763bn",
    ftcReplacement: ftcComputed
      ? `USD 2.763bn (≈EUR ${formatDeckNumber(ftcEurValue / 1e9, 3, language)}bn; ECB 2021)`
      : "USD 2.763bn (EUR not_computed)",
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
  if (rows.length !== 53) throw new Error(`Evidence Register must contain 53 rows, got ${rows.length}`);
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
  ));
  if (countIndex < 0) throw new Error(`${language}: official-observation row not found`);
  output[countIndex] = language === "fi"
    ? [
      "Julkinen paketti sisältää 27 virallisista reiteistä johdettua vuosihavaintoa 7 maasta.",
      "Markkinakoko",
      "Maat ovat Kanada, Saksa, Suomi, Uusi-Seelanti, Puola, Ruotsi ja Yhdysvallat. Havaintojen transaktiotasot, valuutat ja tuoterajaukset eroavat.",
      "site/data/market-values.json (julkisen sivuston koneellisesti luettava lähdetiedosto)",
      "2026-07-24",
      "Niiden vuosihavaintojen määrä, joiden evidenceStatus alkaa official_-tunnisteella.",
      "Virallinen julkaisu ei tee mittareista automaattisesti yhteismitallisia.",
      "Vahvistettu",
      "Lisämaista tarvitaan yhteismitalliset vuotuiset laite- ja nestemäisen kuluttajavähittäisarvon sarjat.",
    ]
    : [
      "The public package contains 27 annual observations sourced from official routes across seven countries.",
      "Market size",
      "The countries are Canada, Germany, Finland, New Zealand, Poland, Sweden and the United States. Transaction levels, currencies and product scopes differ.",
      "site/data/market-values.json (machine-readable source file of the public site)",
      "2026-07-24",
      "Count of annual observations whose evidenceStatus begins official_.",
      "Official publication does not make the metrics automatically comparable.",
      "Confirmed",
      "Comparable annual device and liquid consumer-retail-value series are required from additional countries.",
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
      "2026-07-24",
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
      "2026-07-24",
      "A candidate enters the donor count only when D1–D10 all pass; a failed or open criterion keeps it outside the count.",
      "Official lower bounds, institutional benchmarks, shipment values, tax receipts, physical volumes and models are not relabelled as complete consumer-retail value.",
      "Confirmed",
      "At least three accepted donors are required, with regional and regulatory-archetype coverage.",
    ];

  const existingAddition = output.findIndex((row) => row[0].startsWith(language === "fi"
    ? "Uuden-Seelannin vuoden 2024 tunnistetun"
    : "New Zealand's supported 2024 identified"));
  if (existingAddition < 0) {
    const anchor = output.findIndex((row) => row[0].startsWith(language === "fi"
      ? "Varovainen tekstiluokitus"
      : "A conservative text classification"));
    if (anchor < 0) throw new Error(`${language}: New Zealand insertion anchor not found`);
    output.splice(anchor + 1, 0, ...registerAdditions[language]);
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
      "2026-07-24",
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
      "2026-07-24",
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
    if (typeof record.text !== "string" || !record.text.includes("2026.07.24-17")) continue;
    rewriteText(presentation.resolve(record.id), record.text.replaceAll("2026.07.24-17", releaseVersion));
  }
  const update = deckUpdates[language][deckName];
  const fxPhrases = prominentDeckFxPhrases(language, market, scenarios, fxData);
  const nzCardValueShapeIds = new Set(["sh/i94r6xgz", "sh/v2tcn650"]);
  const nzCardSubtitleShapeIds = new Set(["sh/jadsz2xk", "sh/u1kbu1ov"]);
  let nzFxMarkers = 0;
  let ftcFxMarkers = 0;
  const withFxEquivalents = (text) => {
    let output = String(text);
    if (output.includes(fxPhrases.nzOriginal)) {
      nzFxMarkers += 1;
      output = output.replaceAll(fxPhrases.nzOriginal, fxPhrases.nzReplacement);
    }
    if (output.includes(fxPhrases.ftcOriginal)) {
      ftcFxMarkers += 1;
      output = output.replaceAll(fxPhrases.ftcOriginal, fxPhrases.ftcReplacement);
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
    rewriteText(presentation.resolve(shapeId), withFxEquivalents(text));
  }
  for (const [tableId, changes] of Object.entries(update.tables ?? {})) {
    const table = presentation.resolve(tableId);
    for (const [row, column, value] of changes) {
      table.cells.set(row, column, withFxEquivalents(value));
    }
  }
  if (nzFxMarkers < 1 || ftcFxMarkers < 1) {
    throw new Error(`${language}/${deckName}: prominent NZ or FTC FX marker is missing`);
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
    ? "Uuden-Seelannin vuoden 2024 tunnistetun"
    : "New Zealand's supported 2024 identified"));
  if (nzAdditionIndex < 0) throw new Error(`${language}: New Zealand supported-model row is missing`);
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
    isFi ? "Pixan · julkisen evidenssipaketin yhteenveto" : "Pixan · public evidence package summary",
    isFi
      ? "Riippumaton julkinen evidenssikooste. Ei Pixan Oy:n virallinen kanta; ei tilintarkastus, arvonmääritys, oikeudellinen lausunto, sijoitussuositus tai lainasuositus."
      : "Independent public evidence summary. Not Pixan Oy's official position; not an audit, valuation, legal opinion, investment recommendation or lending recommendation.",
  );
  summary.getRange("A5:B8").values = [
    [isFi ? "Versio" : "Version", releaseVersion],
    [isFi ? "Päivitetty" : "Updated", "2026-07-24"],
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
    "medium-deck-en": ["Keskikokoinen pankkidekki (englanti)", "Core bank deck (English)"],
    "large-deck-en": ["Laaja pankkidekki (englanti)", "Extended bank deck (English)"],
    "evidence-register-en": ["Evidence Register (englanti)", "Evidence Register (English)"],
    "short-deck-fi": ["Suppea pankkidekki (suomi)", "Concise bank deck (Finnish)"],
    "medium-deck-fi": ["Keskikokoinen pankkidekki (suomi)", "Core bank deck (Finnish)"],
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
    if (!["short", "medium", "large"].includes(deckName)) throw new Error(`Unknown deck id ${id}`);
    entry.slideCount = artifact.slideCount;
  }
  return entry;
}

async function writeReleaseLocks(artifacts) {
  const changelog = JSON.parse(await fs.readFile(path.join(dataDir, "changelog.json"), "utf8"));
  const release = changelog.releases?.[0];
  if (
    release?.id !== "2026-07-24-donor-conversion-cockpit-v18"
    || release?.version !== releaseVersion
    || changelog.asOf !== "2026-07-24"
  ) {
    throw new Error("The public changelog is not locked to the reviewed v18 release");
  }
  const artifactOrder = [
    "short-deck-en",
    "medium-deck-en",
    "large-deck-en",
    "evidence-register-en",
    "short-deck-fi",
    "medium-deck-fi",
    "large-deck-fi",
    "evidence-register-fi",
  ];
  const reviewedInputPaths = [
    "scripts/artifact-build/build_bank_package_artifacts.mjs",
    ...seedPaths,
    "site/data/atlas.json",
    "site/data/changelog.json",
    "site/data/market-values.json",
    "site/data/patent-history.json",
    "site/data/donor-cockpit.json",
    "site/data/country-scenarios.json",
    "site/data/evidence-lanes.json",
    "site/data/fx-rates.json",
    "site/schemas/fx-rates.schema.json",
    "source/bank-evidence-register-en.json",
    "source/fx-rates.json",
    "source/schemas/fx-rates.schema.json",
    "source/NZ_2024_ANNUAL_RETURNS_RECONCILIATION.md",
    "source/NZ_2024_RPS_RETAIL_VALUE_SENSITIVITY.md",
    "source/NZ_2023_ANNUAL_RETURNS_FAIL_CLOSED.md",
    "source/US_FTC_2015_2021_REPORTED_SALES.md",
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
      executionNote: "Both language versions were authored and rendered from reviewed public aggregates. The 53-row bilingual registers, 27 official observations across seven countries, five donor candidates, New Zealand retail sensitivity and FTC route share one v18 release boundary.",
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
  await fs.mkdir(qaDir, { recursive: true });
  await fs.mkdir(renderRoot, { recursive: true });
  const market = JSON.parse(await fs.readFile(path.join(dataDir, "market-values.json"), "utf8"));
  const scenarios = JSON.parse(await fs.readFile(path.join(dataDir, "country-scenarios.json"), "utf8"));
  const publicFx = JSON.parse(await fs.readFile(path.join(dataDir, "fx-rates.json"), "utf8"));
  const sourceFx = JSON.parse(await fs.readFile(path.join(sourceDir, "fx-rates.json"), "utf8"));
  validateReviewedFx(publicFx, sourceFx);
  const publicFxSchemaPath = path.join(repo, "site", "schemas", "fx-rates.schema.json");
  const sourceFxSchemaPath = path.join(sourceDir, "schemas", "fx-rates.schema.json");
  if (!fsSync.readFileSync(publicFxSchemaPath).equals(fsSync.readFileSync(sourceFxSchemaPath))) {
    throw new Error("Public FX schema differs from the reviewed source schema");
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
    for (const deckName of ["short", "medium", "large"]) {
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
