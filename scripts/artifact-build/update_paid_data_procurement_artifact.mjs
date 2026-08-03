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
const temporaryPath = `${workbookPath}.v43.tmp`;
const qaDir = path.join(repo, "tmp", "paid-data-v43", "renders");
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
    "REQUEST + FOLLOW-UP SENT · RESPONSE PENDING · NOT SCORED\n"
      + "FI: PYYNTÖ + SEURANTA LÄHETETTY · VASTAUS ODOTTAA · EI PISTEYTETTY",
  ],
];
const ecigBoundary = [
  [
    "Status only. Request sent 2026-07-23 and first follow-up sent 2026-07-28. "
      + "No response, sample, quote, data, method, coverage, licence, price or commitment "
      + "is recorded. NOT SCORED; no purchase is authorised.",
  ],
];
const euromonitorState = [
  [
    "GERMANY EXTRACT DELIVERED + PRIVATE AUDIT COMPLETE · 1/6 GATES PASS · "
      + "WIDER PACKAGE HOLD · NOT SCORED\n"
      + "FI: SAKSA-OTE TOIMITETTU + YKSITYINEN AUDITOINTI VALMIS · "
      + "1/6 PORTTIA LÄPÄISTY · LAAJEMPI PAKETTI HOLD · EI PISTEYTETTY",
  ],
];
const euromonitorBoundary = [
  [
    "Status only. The Germany extract was delivered and audited privately. The three "
      + "preregistered numerical proximity tests passed, but licensed values remain withheld and "
      + "scope, lineage, rights and all-in terms remain open. NOT SCORED; 1/6 gates pass; "
      + "the wider package remains HOLD.",
  ],
];
const circanaState = [
  [
    "FOLLOW-UP SENT 2026-07-28 · SAMPLE + QUOTE PENDING · NOT SCORED\n"
      + "FI: SEURANTA LÄHETETTY 28.7.2026 · NÄYTE + TARJOUS ODOTTAVAT · EI PISTEYTETTY",
  ],
];
const circanaBoundary = [
  [
    "Status only. A direct follow-up requested a United States retail sample, channel and "
      + "method details, a non-binding minimum configuration and transaction-use rights. "
      + "A substantive sample and quote remain pending. NOT SCORED; no purchase or other "
      + "commitment is authorised.",
  ],
];

const source = JSON.parse(await fs.readFile(sourcePath, "utf8"));
if (
  source?.version !== "2026.08.03-43"
  || source?.status !== "decision_support_only_broader_purchase_not_authorised"
) {
  throw new Error("Canonical paid-data source is not the reviewed v43 wider-package-HOLD release");
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
  "Independent decision support · Germany extract delivered · Wider package HOLD · "
    + "Version 2026.08.03-43 · Verified 2026-08-03",
]];
decision.getRange("A5").values = [[
  "DECISION STATUS: NO WIDER-PACKAGE SPEND AUTHORISED\n"
    + "The one-country Germany extract was accepted and delivered. Do not place a 25/50/78-country "
    + "order before the remaining method, scope, rights and commercial gates are closed.\n"
    + "PÄÄTÖSTILA: LAAJEMMAN PAKETIN OSTOVALTUUTTA EI OLE. Yhden maan Saksa-ote hyväksyttiin ja "
    + "toimitettiin. Älä tilaa 25/50/78 maan pakettia ennen jäljellä olevien menetelmä-, rajaus-, "
    + "käyttöoikeus- ja kaupallisten porttien sulkemista.",
]];
decision.getRange("A10").values = [[
  "1) The Germany evaluation extract has been received and privately audited. "
    + "2) Keep the wider 25/50/78-country subscription on HOLD until product, tax, channel and "
    + "transaction-stage scope; source and record-status lineage; lender/buyer NDA data-room "
    + "rights; and complete all-in commercial terms are confirmed in writing. "
    + "3) Treat the numerical pass as coherence evidence, not final accuracy or donor acceptance.\n\n"
    + "FI: 1) Saksan arviointiote on vastaanotettu ja auditoitu yksityisesti. "
    + "2) Pidä laajempi 25/50/78 maan tilaus HOLD-tilassa, kunnes tuote-, vero-, kanava- ja "
    + "tapahtumavaiheen rajaus, lähde- ja tietueiden tilalinja, lainanantaja-/ostaja-NDA-"
    + "datahuoneoikeudet sekä täydelliset kaikki kustannukset kattavat kaupalliset ehdot on "
    + "vahvistettu kirjallisesti. 3) Käsittele numeerista läpäisyä johdonmukaisuusnäyttönä, "
    + "ei lopullisena tarkkuutena tai donor-hyväksyntänä.",
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
    + "1 GERMANY EVALUATION EXTRACT RECEIVED · 0 SCORED · 0 WIDER PACKAGES AUTHORISED\n"
    + "Keep every score blank until all six mandatory gates read PASS. "
    + "A missing input is NOT SCORED, never a zero.\n"
    + "FI: NYKYJULKAISU: 4 TOIMITTAJAA SEURANNASSA · 1 TOIMITTAJAREITILLÄ SISÄLLÖLLISIÄ VASTAUKSIA · "
    + "1 SAKSA-ARVIOINTIOTE VASTAANOTETTU · 0 PISTEYTETTY · 0 LAAJEMMAN PAKETIN OSTOVALTUUTTA. Pidä pisteet tyhjinä, kunnes kaikki kuusi "
    + "pakollista porttia ovat PASS-tilassa. Puuttuva tieto tarkoittaa EI PISTEYTETTY, ei nollaa.",
]];
scorecard.getRange("D14").values = ecigState;
scorecard.getRange("X14").values = ecigBoundary;
scorecard.getRange("D15").values = euromonitorState;
scorecard.getRange("X15").values = euromonitorBoundary;
scorecard.getRange("E15").values = [["PASS"]];
scorecard.getRange("D17").values = circanaState;
scorecard.getRange("X17").values = circanaBoundary;
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
        || values[row][column] === "2026.07.27-30"
        || values[row][column] === "2026.07.27-31"
        || values[row][column] === "2026.07.28-32"
        || values[row][column] === "2026.07.28-33"
        || values[row][column] === "2026.07.28-34"
        || values[row][column] === "2026.07.29-35"
        || values[row][column] === "2026.07.30-36"
        || values[row][column] === "2026.07.31-37"
      ) {
        sheet.getRangeByIndexes(row, column, 1, 1).values = [["2026.08.03-43"]];
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
  authorityBoundary: reopenedDecision.getRange("A5").values,
  recommendation: reopenedDecision.getRange("A10").values,
  recommendedPackagePrice: reopenedDecision.getRange("M17").values,
  recommendedPackageUnknowns: reopenedDecision.getRange("O17").values,
  euromonitorPriorityPrice: reopenedPriorities.getRange("F7").values,
  euromonitorPriorityDecision: reopenedPriorities.getRange("G7").values,
  ecigState: reopenedScorecard.getRange("D14").values,
  ecigBoundary: reopenedScorecard.getRange("X14").values,
  euromonitorState: reopenedScorecard.getRange("D15").values,
  euromonitorBoundary: reopenedScorecard.getRange("X15").values,
  circanaState: reopenedScorecard.getRange("D17").values,
  circanaBoundary: reopenedScorecard.getRange("X17").values,
  ecigSourceFormula: reopenedScorecard.getRange("W14").formulas,
  euromonitorSourceFormula: reopenedScorecard.getRange("W15").formulas,
  gateFormulas: reopenedScorecard.getRange("R14:U15").formulas,
};
if (
  reviewed.release[0][0] !== (
    "Independent decision support · Germany extract delivered · Wider package HOLD · "
      + "Version 2026.08.03-43 · Verified 2026-08-03"
  )
  || reviewed.authorityBoundary[0][0] !== (
    "DECISION STATUS: NO WIDER-PACKAGE SPEND AUTHORISED\n"
      + "The one-country Germany extract was accepted and delivered. Do not place a 25/50/78-country "
      + "order before the remaining method, scope, rights and commercial gates are closed.\n"
      + "PÄÄTÖSTILA: LAAJEMMAN PAKETIN OSTOVALTUUTTA EI OLE. Yhden maan Saksa-ote hyväksyttiin ja "
      + "toimitettiin. Älä tilaa 25/50/78 maan pakettia ennen jäljellä olevien menetelmä-, rajaus-, "
      + "käyttöoikeus- ja kaupallisten porttien sulkemista."
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
  || JSON.stringify(reviewed.circanaState) !== JSON.stringify(circanaState)
  || JSON.stringify(reviewed.circanaBoundary) !== JSON.stringify(circanaBoundary)
  || reviewed.ecigSourceFormula[0][0] !== "='Sources'!C6"
  || reviewed.euromonitorSourceFormula[0][0] !== "='Sources'!C9"
) {
  throw new Error("Reopened paid-data workbook differs from the reviewed v43 state");
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
  path.join(repo, "tmp", "paid-data-v43", "artifact-build.json"),
  `${JSON.stringify(
    {
      release: "2026.08.03-43",
      workbook: "site/downloads/pixan-paid-data-procurement-fi-en.xlsx",
      renderedSheets: sheetNames,
      reviewed,
    },
    null,
    2,
  )}\n`,
  "utf8",
);
console.log(`Updated and rendered paid-data workbook for 2026.08.03-43: ${workbookPath}`);
