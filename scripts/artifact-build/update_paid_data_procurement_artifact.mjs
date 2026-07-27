import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  FileBlob,
  SpreadsheetFile,
} from "@oai/artifact-tool";

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const workbookPath = path.join(
  repo,
  "site",
  "downloads",
  "pixan-paid-data-procurement-fi-en.xlsx",
);
const sourcePath = path.join(repo, "source", "paid-data-procurement.json");
const temporaryPath = `${workbookPath}.v30.tmp`;
const qaDir = path.join(repo, "tmp", "paid-data-v30", "renders");
const sheetNames = [
  "Decision",
  "Priorities",
  "RFP Gate",
  "Avoid",
  "Sources",
  "Response Scorecard",
  "Intake Template",
  "Checks",
];

const ecigState = [
  [
    "REQUEST SENT · NO RESPONSE OR AUTO-ACK · FOLLOW-UP 2026-07-28\n"
      + "FI: PYYNTÖ LÄHETETTY · EI VASTAUSTA TAI AUTOMAATTIKUITTAUSTA · SEURANTA 2026-07-28",
  ],
];
const ecigBoundary = [
  [
    "Status only. Request sent 2026-07-23; no bounce, automated acknowledgement, "
      + "response content or unlicensed data. First follow-up due 2026-07-28 if unanswered.",
  ],
];
const euromonitorState = [
  [
    "EXPANDED SAMPLE + 78-MARKET LIST + 95-GEOGRAPHY SCHEMA + THREE QUOTES RECEIVED · "
      + "0/6 GATES PASS · NOT SCORED\n"
      + "FI: LAAJENNETTU NÄYTE + 78 MARKKINAN LISTA + 95 MAANTIETEEN SKEEMA + "
      + "KOLME TARJOUSTA SAATU · "
      + "0/6 PORTTIA LÄPÄISTY · EI PISTEYTETTY",
  ],
];
const euromonitorBoundary = [
  [
    "Status only. An expanded Germany sample, 78-market list, generic methodology, standard terms, "
      + "three indicative quotes and a later blank-value 95-geography schema were received. "
      + "All six mandatory gates remain OPEN. No licensed values or private quote amounts are "
      + "published. NOT SCORED; no purchase, fee or commitment.",
  ],
];

const source = JSON.parse(await fs.readFile(sourcePath, "utf8"));
if (
  source?.version !== "2026.07.27-30"
  || source?.status !== "decision_support_only_no_purchase_authorised"
) {
  throw new Error("Canonical paid-data source is not the reviewed v30 no-purchase release");
}
const euromonitorItem = source.items.find(
  (item) => item.itemId === "euromonitor-passport-nicotine",
);
const recommendedPackage = source.packageOptions.find((item) => item.id === "recommended");
if (!euromonitorItem || !recommendedPackage) {
  throw new Error("Canonical paid-data source lacks the reviewed Euromonitor or package record");
}
const euromonitorDecision = [
  euromonitorItem.decisionEn,
  euromonitorItem.conditionsEn,
  "",
  `FI: ${euromonitorItem.decisionFi}`,
  euromonitorItem.conditionsFi,
].join("\n");

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const decision = workbook.worksheets.getItem("Decision");
decision.getRange("A3").values = [[
  "Independent decision support · No purchase authorised · "
    + "Version 2026.07.27-30 · Verified 2026-07-27",
]];
decision.getRange("A10").values = [[
  "1) Continue sample and transaction-rights evaluation with ECigIntelligence and Euromonitor "
    + "in parallel. 2) Buy at most one global master; do not buy before a populated 2022–2025 "
    + "Germany test, reconciled 78/95 country-product-field-year coverage, record-level status "
    + "flags, a legally approved NDA data-room Special Condition and complete all-in commercial "
    + "terms pass review. 3) Consider a tightly scoped NIQ/Circana POS pilot only as a later "
    + "validation layer for selected countries.\n\n"
    + "FI: 1) Jatka ECigIntelligencen ja Euromonitorin näyte- ja transaktio-oikeuksien arviointia "
    + "rinnakkain. 2) Osta enintään yksi globaali pääaineisto; älä osta ennen kuin täytetty "
    + "Saksan 2022–2025-testi, täsmäytetty 78/95 maan maa–tuote–kenttä–vuosi-peitto, "
    + "tietuetason tilamerkinnät, legal-tiimin hyväksymä NDA-datahuone-erityisehto ja täydelliset "
    + "kaikki kustannukset kattavat kaupalliset ehdot läpäisevät tarkistuksen. 3) Harkitse rajattua "
    + "NIQ/Circana-POS-pilottia vasta myöhempänä varmennuskerroksena valituille maille.",
]];
decision.getRange("M17").values = [[recommendedPackage.knownPrice]];
decision.getRange("O17").values = [[
  `${recommendedPackage.unknownComponentsEn}\n\nFI: ${recommendedPackage.unknownComponentsFi}`,
]];
const scorecard = workbook.worksheets.getItem("Response Scorecard");
scorecard.getRange("A3").values = [[
  "Evidence-gated comparison · Missing evidence is not zero · "
    + "A response is not a score or purchase",
]];
scorecard.getRange("A5").values = [[
  "CURRENT RELEASE: 4 VENDORS TRACKED · 1 VENDOR ROUTE WITH SUBSTANTIVE RESPONSES · "
    + "0 SCORED · 0 PURCHASES AUTHORISED\n"
    + "Keep every score blank until all six mandatory gates read PASS. "
    + "A missing input is NOT SCORED, never a zero.\n"
    + "FI: NYKYJULKAISU: 4 TOIMITTAJAA SEURANNASSA · 1 TOIMITTAJAREITILLÄ SISÄLLÖLLISIÄ VASTAUKSIA · "
    + "0 PISTEYTETTY · 0 OSTOVALTUUTTA. Pidä pisteet tyhjinä, kunnes kaikki kuusi "
    + "pakollista porttia ovat PASS-tilassa. Puuttuva tieto tarkoittaa EI PISTEYTETTY, ei nollaa.",
]];
scorecard.getRange("D14").values = ecigState;
scorecard.getRange("X14").values = ecigBoundary;
scorecard.getRange("D15").values = euromonitorState;
scorecard.getRange("X15").values = euromonitorBoundary;
const priorities = workbook.worksheets.getItem("Priorities");
priorities.getRange("F7").values = [[euromonitorItem.priceDisplay]];
priorities.getRange("G7").values = [[euromonitorDecision]];
priorities.getRange("A7:P7").format.rowHeightPx = 360;

for (const sheetName of sheetNames) {
  const sheet = workbook.worksheets.getItem(sheetName);
  const values = sheet.getRange("A1:X100").values;
  for (let row = 0; row < values.length; row += 1) {
    for (let column = 0; column < values[row].length; column += 1) {
      if (
        values[row][column] === "2026.07.23-3"
        || values[row][column] === "2026.07.24-19"
        || values[row][column] === "2026.07.24-20"
        || values[row][column] === "2026.07.24-21"
        || values[row][column] === "2026.07.24-22"
        || values[row][column] === "2026.07.25-24"
        || values[row][column] === "2026.07.27-29"
      ) {
        sheet.getRangeByIndexes(row, column, 1, 1).values = [["2026.07.27-30"]];
      }
    }
  }
}

await (await SpreadsheetFile.exportXlsx(workbook)).save(temporaryPath);
const reopened = await SpreadsheetFile.importXlsx(await FileBlob.load(temporaryPath));
const reopenedScorecard = reopened.worksheets.getItem("Response Scorecard");
const reopenedDecision = reopened.worksheets.getItem("Decision");
const reopenedPriorities = reopened.worksheets.getItem("Priorities");
const reviewed = {
  release: reopenedDecision.getRange("A3").values,
  recommendation: reopenedDecision.getRange("A10").values,
  recommendedPackagePrice: reopenedDecision.getRange("M17").values,
  recommendedPackageUnknowns: reopenedDecision.getRange("O17").values,
  euromonitorPriorityPrice: reopenedPriorities.getRange("F7").values,
  euromonitorPriorityDecision: reopenedPriorities.getRange("G7").values,
  ecigState: reopenedScorecard.getRange("D14").values,
  ecigBoundary: reopenedScorecard.getRange("X14").values,
  euromonitorState: reopenedScorecard.getRange("D15").values,
  euromonitorBoundary: reopenedScorecard.getRange("X15").values,
  ecigSourceFormula: reopenedScorecard.getRange("W14").formulas,
  euromonitorSourceFormula: reopenedScorecard.getRange("W15").formulas,
  gateFormulas: reopenedScorecard.getRange("R14:U15").formulas,
};
if (
  reviewed.release[0][0] !== (
    "Independent decision support · No purchase authorised · "
      + "Version 2026.07.27-30 · Verified 2026-07-27"
  )
  || reviewed.recommendedPackagePrice[0][0] !== recommendedPackage.knownPrice
  || reviewed.recommendedPackageUnknowns[0][0] !== (
    `${recommendedPackage.unknownComponentsEn}\n\nFI: ${recommendedPackage.unknownComponentsFi}`
  )
  || reviewed.euromonitorPriorityPrice[0][0] !== euromonitorItem.priceDisplay
  || reviewed.euromonitorPriorityDecision[0][0] !== euromonitorDecision
  || JSON.stringify(reviewed.ecigState) !== JSON.stringify(ecigState)
  || JSON.stringify(reviewed.ecigBoundary) !== JSON.stringify(ecigBoundary)
  || JSON.stringify(reviewed.euromonitorState) !== JSON.stringify(euromonitorState)
  || JSON.stringify(reviewed.euromonitorBoundary) !== JSON.stringify(euromonitorBoundary)
  || reviewed.ecigSourceFormula[0][0] !== "='Sources'!C6"
  || reviewed.euromonitorSourceFormula[0][0] !== "='Sources'!C9"
) {
  throw new Error("Reopened paid-data workbook differs from the reviewed v30 state");
}

await fs.mkdir(qaDir, { recursive: true });
for (const sheetName of sheetNames) {
  const preview = await reopened.render({
    sheetName,
    autoCrop: "all",
    scale: 0.8,
    format: "png",
  });
  const safeName = sheetName.toLowerCase().replace(/[^a-z0-9]+/g, "-");
  await fs.writeFile(
    path.join(qaDir, `${safeName}.png`),
    new Uint8Array(await preview.arrayBuffer()),
  );
}

await fs.rename(temporaryPath, workbookPath);
await fs.rm(`${temporaryPath}.inspect.ndjson`, { force: true });
await fs.writeFile(
  path.join(repo, "tmp", "paid-data-v30", "artifact-build.json"),
  `${JSON.stringify(
    {
      release: "2026.07.27-30",
      workbook: "site/downloads/pixan-paid-data-procurement-fi-en.xlsx",
      renderedSheets: sheetNames,
      reviewed,
    },
    null,
    2,
  )}\n`,
  "utf8",
);
console.log(`Updated and rendered paid-data workbook for 2026.07.27-30: ${workbookPath}`);
