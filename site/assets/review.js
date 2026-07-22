"use strict";

const REVIEW_DIMENSIONS = {
  officialSales: "Official sales / deliveries",
  officialVolume: "Official taxable volume",
  taxRevenue: "Realised tax revenue",
  customs: "Official customs route",
  regulation: "Regulatory route",
  patent: "Patent / court route"
};

const REVIEW_BLOCKER_TRANSLATIONS = {
  "Useimmista maista puuttuu virallinen vuosittainen laite- ja nestemyynti": "Most countries still lack a verified annual official series for device and e-liquid sales.",
  "Markkinaevidenssiä ei ole vielä sidottu maakohtaiseen patenttistatukseen ja claim charteihin": "Market evidence has not yet been reconciled with country-level patent status and product claim charts.",
  "Aineisto ei sisällä riippumatonta IVS-arvonmääritystä eikä realisoitunutta lisenssi- tai vahingonkorvauskassavirtaa": "The dataset does not include an independent IVS valuation or realised licensing or damages cash flow."
};

const REVIEW_LEGAL_SUMMARIES = {
  "EP-3032975-B2": "The European Patent Office publication service contains the official EP 3 032 975 B2 patent specification. Publication alone does not establish current national validation, renewal status, infringement or monetary value.",
  "DE-BPATG-8NI18-24-JUDGMENT": "The Federal Patent Court judgment dated 14 January 2026 dismissed the nullity action. The official record notes that an appeal has been lodged with the Federal Court of Justice under docket X ZR 21/26, so the judgment is not final.",
  "DE-LGMUC-7O3341-24-JUDGMENT": "The Munich Regional Court I judgment dated 2 April 2026 found infringement by the products examined in case 7 O 3341/24 and ordered the remedies listed in that judgment. The record does not by itself establish finality, enforcement, damages paid or relevance to other products or countries."
};

const reviewById = (id) => document.getElementById(id);

function reviewNode(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined && text !== null) element.textContent = String(text);
  return element;
}

function reviewUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "https:" ? url.href : null;
  } catch (_) {
    return null;
  }
}

function reviewStatus(value) {
  const status = String(value || "").toLowerCase();
  if (["verified", "confirmed", "official"].includes(status)) return "verified";
  if (["partial", "proxy", "modeled", "modelled"].includes(status)) return "partial";
  return "missing";
}

function renderReviewMetrics(data) {
  const countries = data.countries;
  const grades = countries.reduce((counts, country) => {
    const grade = ["A", "B", "C", "D"].includes(country.bestEvidence) ? country.bestEvidence : "D";
    counts[grade] = (counts[grade] || 0) + 1;
    return counts;
  }, {});
  const metrics = [
    ["Country universe", countries.length, "UN 193 + Holy See + State of Palestine"],
    ["Direct official anchor", grades.A || 0, "At least one direct official sales, volume or tax observation"],
    ["Sourced route", (grades.A || 0) + (grades.B || 0) + (grades.C || 0), "A, B or C evidence; not necessarily annual retail sales"],
    ["Evidence records", data.evidence.length, "Each record retains a public source link and claim type"]
  ];
  const host = reviewById("review-metrics");
  host.replaceChildren(...metrics.map(([label, value, note]) => {
    const card = reviewNode("article", "metric-card");
    card.append(reviewNode("span", "", label), reviewNode("strong", "", value), reviewNode("small", "", note));
    return card;
  }));
}

function renderReviewGrades(data) {
  const grades = { A: 0, B: 0, C: 0, D: 0 };
  data.countries.forEach((country) => {
    const grade = country.bestEvidence;
    if (grade in grades) grades[grade] += 1;
  });
  const descriptions = {
    A: "direct official market, volume or tax observation",
    B: "official proxy, administrative or legal anchor",
    C: "model or supporting source",
    D: "no accepted country-specific numeric anchor yet"
  };
  const host = reviewById("review-grade-bars");
  host.replaceChildren(...Object.entries(grades).map(([grade, count]) => {
    const row = reviewNode("div", "review-grade-row");
    const label = reviewNode("div", "review-grade-label");
    label.append(reviewNode("span", `grade grade-${grade.toLowerCase()}`, grade), reviewNode("p", "", descriptions[grade]));
    const track = reviewNode("div", "review-grade-track");
    const fill = reviewNode("span", `review-grade-fill review-grade-${grade.toLowerCase()}`);
    fill.style.width = `${(count / data.countries.length) * 100}%`;
    track.append(fill);
    row.append(label, track, reviewNode("strong", "review-grade-count", count));
    return row;
  }));
}

function renderReviewDimensions(data) {
  const host = reviewById("review-dimension-table");
  const rows = Object.entries(REVIEW_DIMENSIONS).map(([key, label]) => {
    const verified = data.countries.filter((country) => reviewStatus(country.dimensions?.[key]) === "verified").length;
    const partial = data.countries.filter((country) => reviewStatus(country.dimensions?.[key]) === "partial").length;
    const row = reviewNode("div", "review-dimension-row");
    row.append(
      reviewNode("strong", "", label),
      reviewNode("span", "review-verified", `${verified} verified`),
      reviewNode("span", "review-partial", `${partial} partial`)
    );
    return row;
  });
  host.replaceChildren(...rows);
}

function renderReviewBlockers(data) {
  const blockers = Array.isArray(data.readiness?.blockers) ? data.readiness.blockers : [];
  const host = reviewById("review-blockers");
  host.replaceChildren(...blockers.slice(0, 4).map((text) => {
    const row = reviewNode("div", "readiness-item");
    row.append(reviewNode("span", "readiness-dot readiness-open", ""), reviewNode("p", "", REVIEW_BLOCKER_TRANSLATIONS[text] || text));
    return row;
  }));
  if (!blockers.length) host.append(reviewNode("p", "muted", "No readiness record was available."));
}

function renderReviewLegal(data) {
  const host = reviewById("review-legal");
  const items = Array.isArray(data.legal) ? data.legal : [];
  host.replaceChildren(...items.map((item) => {
    const li = reviewNode("li");
    li.append(
      reviewNode("time", "", item.eventDate || "Official record"),
      reviewNode("strong", "", item.reference || item.authority),
      reviewNode("p", "", REVIEW_LEGAL_SUMMARIES[item.legalId] || item.statement || "")
    );
    const url = reviewUrl(item.sourceUrl);
    if (url) {
      const link = reviewNode("a", "", "Open official source →");
      link.href = url;
      link.target = "_blank";
      link.rel = "noreferrer";
      li.append(link);
    }
    return li;
  }));
}

function renderReviewMeta(data) {
  const asOf = data.meta?.asOf || data.meta?.generatedAt || "";
  const time = reviewById("review-as-of");
  time.textContent = asOf || "—";
  time.dateTime = asOf;
  reviewById("review-source-commit").textContent = String(data.meta?.legacySourceCommit || "—").slice(0, 9);
}

async function copyReviewLink() {
  const status = reviewById("copy-review-status");
  try {
    await navigator.clipboard.writeText(location.href.split("#")[0]);
    status.textContent = "Review link copied.";
  } catch (_) {
    status.textContent = `Share this URL: ${location.href.split("#")[0]}`;
  }
}

async function initReview() {
  reviewById("copy-review-link").addEventListener("click", copyReviewLink);
  reviewById("print-review").addEventListener("click", () => window.print());
  try {
    const response = await fetch("data/atlas.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (!Array.isArray(data.countries) || data.countries.length !== 195 || !Array.isArray(data.evidence)) {
      throw new Error("Reviewed dataset validation failed");
    }
    renderReviewMeta(data);
    renderReviewMetrics(data);
    renderReviewGrades(data);
    renderReviewDimensions(data);
    renderReviewBlockers(data);
    renderReviewLegal(data);
  } catch (error) {
    console.error(error);
    reviewById("review-load-error").hidden = false;
  }
}

initReview();
