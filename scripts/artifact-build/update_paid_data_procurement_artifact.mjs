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
const temporaryPath = `${workbookPath}.v24.tmp`;
const qaDir = path.join(repo, "tmp", "paid-data-v24", "renders");
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
    "GERMANY SAMPLE + METHOD + TWO QUOTES RECEIVED · 0/6 GATES PASS · NOT SCORED\n"
      + "FI: SAKSA-NÄYTE + MENETELMÄ + KAKSI TARJOUSTA SAATU · "
      + "0/6 PORTTIA LÄPÄISTY · EI PISTEYTETTY",
  ],
];
const euromonitorBoundary = [
  [
    "Status only. A sparse Germany sample, generic methodology and two indicative quotes were "
      + "received. The workbook does not satisfy the representative-sample gate; all six mandatory "
      + "gates remain OPEN. No licensed values are published. NOT SCORED; no purchase, fee or "
      + "commitment.",
  ],
];

const source = JSON.parse(await fs.readFile(sourcePath, "utf8"));
if (
  source?.version !== "2026.07.25-24"
  || source?.status !== "decision_support_only_no_purchase_authorised"
) {
  throw new Error("Canonical paid-data source is not the reviewed v24 no-purchase release");
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
    + "Version 2026.07.25-24 · Verified 2026-07-25",
]];
decision.getRange("A10").values = [[
  "1) Continue sample and transaction-rights evaluation with ECigIntelligence and Euromonitor "
    + "in parallel. 2) Buy at most one global master. Do not buy Euromonitor before a full "
    + "Germany sample, exact coverage matrix, category-specific method and written Pixan, lender, "
    + "buyer, adviser, data-room and audit-archive rights pass review. 3) Add a tightly scoped "
    + "NIQ/Circana POS pilot only as a validation layer for Germany, the United States and the "
    + "United Kingdom.\n\n"
    + "FI: 1) Jatka ECigIntelligencen ja Euromonitorin näyte- ja transaktio-oikeuksien arviointia "
    + "rinnakkain. 2) Osta enintään yksi globaali pääaineisto. Älä osta Euromonitoria ennen kuin "
    + "täysi Saksa-näyte, täsmällinen peittomatriisi, kategoriakohtainen menetelmä sekä kirjalliset "
    + "Pixan-, lainanantaja-, ostaja-, neuvonantaja-, datahuone- ja tarkastusarkisto-oikeudet "
    + "läpäisevät tarkistuksen. 3) Lisää rajattu NIQ/Circana-POS-pilotti vain varmennuskerrokseksi "
    + "Saksaan, Yhdysvaltoihin ja Britanniaan.",
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
      ) {
        sheet.getRangeByIndexes(row, column, 1, 1).values = [["2026.07.25-24"]];
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
      + "Version 2026.07.25-24 · Verified 2026-07-25"
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
  throw new Error("Reopened paid-data workbook differs from the reviewed v24 state");
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
  path.join(repo, "tmp", "paid-data-v24", "artifact-build.json"),
  `${JSON.stringify(
    {
      release: "2026.07.25-24",
      workbook: "site/downloads/pixan-paid-data-procurement-fi-en.xlsx",
      renderedSheets: sheetNames,
      reviewed,
    },
    null,
    2,
  )}\n`,
  "utf8",
);
console.log(`Updated and rendered paid-data workbook for 2026.07.25-24: ${workbookPath}`);
