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
const temporaryPath = `${workbookPath}.v20.tmp`;
const qaDir = path.join(repo, "tmp", "paid-data-v20", "renders");
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
    "TWO WRITTEN RESPONSES + BROCHURE RECEIVED · GERMANY SAMPLE + PRICING PENDING · "
      + "ROLE/ACCESS CLARIFICATION PENDING · NOT SENT\n"
      + "FI: KAKSI KIRJALLISTA VASTAUSTA + ESITE SAATU · SAKSA-NÄYTE + HINNOITTELU ODOTTAVAT · "
      + "ROOLI-/KÄYTTÖMALLIN TÄSMENNYS ODOTTAA · EI LÄHETETTY",
  ],
];
const euromonitorBoundary = [
  [
    "Status only. Euromonitor says it can provide samples, detailed answers and pricing after "
      + "the role/access model is clarified. The role/access clarification is pending and has not "
      + "been sent. The brochure and vendor statement about expanded granularity are "
      + "not numerical market evidence. The Germany sample, written brand confirmation, itemised "
      + "price, detailed method, coverage, licence and written derived-output rights remain pending. "
      + "No usable data, purchase, fee or commitment.",
  ],
];

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const decision = workbook.worksheets.getItem("Decision");
decision.getRange("A3").values = [[
  "Independent decision support · No purchase authorised · "
    + "Version 2026.07.24-20 · Verified 2026-07-24",
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

for (const sheetName of sheetNames) {
  const sheet = workbook.worksheets.getItem(sheetName);
  const values = sheet.getRange("A1:X100").values;
  for (let row = 0; row < values.length; row += 1) {
    for (let column = 0; column < values[row].length; column += 1) {
      if (
        values[row][column] === "2026.07.23-3"
        || values[row][column] === "2026.07.24-19"
      ) {
        sheet.getRangeByIndexes(row, column, 1, 1).values = [["2026.07.24-20"]];
      }
    }
  }
}

await (await SpreadsheetFile.exportXlsx(workbook)).save(temporaryPath);
const reopened = await SpreadsheetFile.importXlsx(await FileBlob.load(temporaryPath));
const reopenedScorecard = reopened.worksheets.getItem("Response Scorecard");
const reviewed = {
  ecigState: reopenedScorecard.getRange("D14").values,
  ecigBoundary: reopenedScorecard.getRange("X14").values,
  euromonitorState: reopenedScorecard.getRange("D15").values,
  euromonitorBoundary: reopenedScorecard.getRange("X15").values,
  ecigSourceFormula: reopenedScorecard.getRange("W14").formulas,
  euromonitorSourceFormula: reopenedScorecard.getRange("W15").formulas,
  gateFormulas: reopenedScorecard.getRange("R14:U15").formulas,
};
if (
  JSON.stringify(reviewed.ecigState) !== JSON.stringify(ecigState)
  || JSON.stringify(reviewed.ecigBoundary) !== JSON.stringify(ecigBoundary)
  || JSON.stringify(reviewed.euromonitorState) !== JSON.stringify(euromonitorState)
  || JSON.stringify(reviewed.euromonitorBoundary) !== JSON.stringify(euromonitorBoundary)
  || reviewed.ecigSourceFormula[0][0] !== "='Sources'!C6"
  || reviewed.euromonitorSourceFormula[0][0] !== "='Sources'!C9"
) {
  throw new Error("Reopened paid-data workbook differs from the reviewed v20 state");
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
await fs.writeFile(
  path.join(repo, "tmp", "paid-data-v20", "artifact-build.json"),
  `${JSON.stringify(
    {
      release: "2026.07.24-20",
      workbook: "site/downloads/pixan-paid-data-procurement-fi-en.xlsx",
      renderedSheets: sheetNames,
      reviewed,
    },
    null,
    2,
  )}\n`,
  "utf8",
);
console.log(`Updated and rendered paid-data workbook for 2026.07.24-20: ${workbookPath}`);
