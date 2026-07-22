"use strict";

const REVIEW_I18N = window.SiteI18n;
const reviewL = (fi, en) => REVIEW_I18N.pick(fi, en);
const reviewIsFi = () => REVIEW_I18N.isFinnish();

const REVIEW_DIMENSIONS = {
  officialSales: ["Virallinen myynti / toimitus", "Official sales / deliveries"],
  officialVolume: ["Virallinen verollinen määrä", "Official taxable volume"],
  taxRevenue: ["Toteutunut verotuotto", "Realised tax revenue"],
  customs: ["Virallinen tullireitti", "Official customs route"],
  regulation: ["Sääntelyreitti", "Regulatory route"],
  patent: ["Patentti- / tuomioistuinreitti", "Patent / court route"]
};

const REVIEW_BLOCKER_TRANSLATIONS = {
  "Useimmista maista puuttuu virallinen vuosittainen laite- ja nestemyynti": "Most countries still lack a verified annual official series for device and e-liquid sales.",
  "Markkinaevidenssiä ei ole vielä sidottu maakohtaiseen patenttistatukseen ja claim charteihin": "Market evidence has not yet been reconciled with country-level patent status and product claim charts.",
  "Aineisto ei sisällä riippumatonta IVS-arvonmääritystä eikä realisoitunutta lisenssi- tai vahingonkorvauskassavirtaa": "The dataset does not include an independent IVS valuation or realised licensing or damages cash flow."
};

const REVIEW_BLOCKER_FI = {
  "Useimmista maista puuttuu virallinen vuosittainen laite- ja nestemyynti": "Useimmista maista puuttuu edelleen vahvistettu virallinen vuosittainen laite- ja e-nestemyyntisarja.",
  "Markkinaevidenssiä ei ole vielä sidottu maakohtaiseen patenttistatukseen ja claim charteihin": "Markkinaevidenssiä ei ole vielä täsmäytetty maakohtaiseen patenttistatukseen ja tuotekohtaisiin claim charteihin.",
  "Aineisto ei sisällä riippumatonta IVS-arvonmääritystä eikä realisoitunutta lisenssi- tai vahingonkorvauskassavirtaa": "Aineisto ei sisällä riippumatonta IVS-arvonmääritystä eikä toteutunutta lisenssi- tai vahingonkorvauskassavirtaa."
};

const REVIEW_LEGAL_SUMMARIES = {
  "EP-3032975-B2": "The European Patent Office publication service contains the official EP 3 032 975 B2 patent specification. Publication alone does not establish current national validation, renewal status, infringement or monetary value.",
  "DE-BPATG-8NI18-24-JUDGMENT": "The Federal Patent Court judgment dated 14 January 2026 dismissed the nullity action. The official record notes that an appeal has been lodged with the Federal Court of Justice under docket X ZR 21/26, so the judgment is not final.",
  "DE-LGMUC-7O3341-24-JUDGMENT": "The Munich Regional Court I judgment dated 2 April 2026 found infringement by the products examined in case 7 O 3341/24 and ordered the remedies listed in that judgment. The record does not by itself establish finality, enforcement, damages paid or relevance to other products or countries."
};

let reviewData = null;
let reviewMarketData = null;
let reviewChangelog = null;
let reviewChangeView = null;

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

function reviewFormatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat(reviewIsFi() ? "fi-FI" : "en-GB", { year: "numeric", month: "long", day: "numeric" }).format(date);
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
    [reviewL("Maauniversumi", "Country universe"), countries.length, reviewL("UN 193 + Pyhä istuin + Palestiinan valtio", "UN 193 + Holy See + State of Palestine")],
    [reviewL("Suora viranomaisankkuri", "Direct official anchor"), grades.A || 0, reviewL("Vähintään yksi suora virallinen myynti-, määrä- tai verohavainto", "At least one direct official sales, volume or tax observation")],
    [reviewL("Lähteistetty reitti", "Sourced route"), (grades.A || 0) + (grades.B || 0) + (grades.C || 0), reviewL("A-, B- tai C-evidenssi; ei välttämättä vuosittaista vähittäismyyntiä", "A, B or C evidence; not necessarily annual retail sales")],
    [reviewL("Evidenssihavainnot", "Evidence records"), data.evidence.length, reviewL("Jokainen havainto säilyttää julkisen lähdelinkin ja väitetyypin", "Each record retains a public source link and claim type")]
  ];
  const host = reviewById("review-metrics");
  host.replaceChildren(...metrics.map(([label, value, note]) => {
    const card = reviewNode("article", "metric-card");
    card.append(reviewNode("span", "", label), reviewNode("strong", "", value), reviewNode("small", "", note));
    return card;
  }));
}

function reviewMarketFormat(value, currency) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  return new Intl.NumberFormat(reviewIsFi() ? "fi-FI" : "en-GB", {
    style: "currency",
    currency,
    currencyDisplay: "code",
    notation: "compact",
    maximumFractionDigits: 3
  }).format(number);
}

function renderReviewMarket(market) {
  const observations = Array.isArray(market?.observations) ? market.observations : [];
  const models = Array.isArray(market?.models) ? market.models : [];
  const commercial = observations.filter((item) => item.metric === "commercial_market_estimate" && item.currency === "USD" && Number(item.year) === 2025);
  const low = commercial.length ? Math.min(...commercial.map((item) => Number(item.value))) : null;
  const high = commercial.length ? Math.max(...commercial.map((item) => Number(item.value))) : null;
  const canada = observations.find((item) => item.observationId === "CA-2024-MANUFACTURER-IMPORTER-SHIPMENTS-VALUE");
  const germany = models.find((item) => item.modelId === "DE-2025-LIQUID-RETAIL-EQUIVALENT-RANGE");
  const cards = [
    {
      label: reviewL("Ulkoinen maailmanmarkkinahaarukka · 2025", "External global range · 2025"),
      value: low !== null && high !== null ? `${reviewMarketFormat(low, "USD")}–${reviewMarketFormat(high, "USD")}` : "—",
      note: reviewL("Kolme kaupallista arviota; eri rajaukset, ei atlaksen arvio", "Three commercial estimates; different scopes, not the atlas estimate")
    },
    {
      label: reviewL("Kanada · 2024 virallinen toimitusarvo", "Canada · 2024 official shipment value"),
      value: canada ? reviewMarketFormat(canada.value, canada.currency) : "—",
      note: reviewL("Valmistaja-/maahantuojatoimitukset tukulle ja vähittäiskaupalle; ei kuluttajamyynti", "Manufacturer/importer shipments to wholesale and retail; not consumer sales")
    },
    {
      label: reviewL("Saksa · 2025 nestemalli", "Germany · 2025 liquid model"),
      value: germany ? `${reviewMarketFormat(germany.low, germany.currency)}–${reviewMarketFormat(germany.high, germany.currency)}` : "—",
      note: reviewL("Verotettu neste × 2026 hintakori; matala luottamus, ei laitteita", "Taxed liquid × 2026 price basket; low confidence, excludes devices")
    }
  ];
  const host = reviewById("review-market-metrics");
  host.replaceChildren(...cards.map((item) => {
    const card = reviewNode("article", "panel review-market-card");
    card.append(reviewNode("span", "kicker", item.label), reviewNode("strong", "", item.value), reviewNode("small", "", item.note));
    return card;
  }));

  const readiness = market?.meta?.modelReadiness || {};
  const note = reviewById("review-market-note");
  const status = reviewNode("span", "market-status-chip market-status-caution", reviewL("Ei vielä maailmanestimaattia", "No atlas global estimate yet"));
  const explanation = reviewNode("p", "", reviewIsFi()
    ? readiness.reasonFi || "Vahvistettuja, vertailukelpoisia koko vuoden luovuttajamarkkinoita ei vielä ole riittävästi maailmanestimaatin julkaisemiseen."
    : readiness.reasonEn || "There are not yet enough verified, comparable full-year donor markets to release a global atlas estimate.");
  const rule = reviewNode("p", "muted", reviewIsFi()
    ? "Raha, verot, fyysiset määrät ja mallinnetut vaihteluvälit näytetään erikseen eikä niitä summata."
    : "Monetary observations, excise, physical quantities and modelled ranges remain separate and are never added together.");
  note.replaceChildren(status, explanation, rule);
}

function renderReviewMarketUnavailable() {
  const host = reviewById("review-market-metrics");
  const card = reviewNode("article", "panel review-market-card review-market-unavailable");
  card.append(
    reviewNode("span", "kicker", reviewL("Markkina-arvodata", "Market-value data")),
    reviewNode("strong", "", reviewL("Ei saatavilla", "Unavailable")),
    reviewNode("small", "", reviewL("Muu 195 maan evidenssi on edelleen tarkistettavissa.", "The rest of the 195-country evidence remains reviewable."))
  );
  host.replaceChildren(card);
  reviewById("review-market-note").replaceChildren(reviewNode("p", "muted", reviewL("Markkina-arvon apuaineistoa ei voitu ladata.", "The market-value supporting dataset could not be loaded.")));
}

const REVIEW_CHANGE_STORAGE_KEY = "pixan-global-market-evidence-last-seen-release-v4";
const reviewReleaseToken = (release) => release ? `${release.id}:${release.version || "unversioned"}` : "";

function prepareReviewChangeView() {
  const releases = Array.isArray(reviewChangelog?.releases)
    ? [...reviewChangelog.releases].sort((a, b) => String(b.publishedAt).localeCompare(String(a.publishedAt)))
    : [];
  const current = releases[0] || null;
  let lastSeen = null;
  try { lastSeen = localStorage.getItem(REVIEW_CHANGE_STORAGE_KEY); } catch (_) { /* local storage may be disabled */ }
  let mode = reviewChangelog ? "none" : "unavailable";
  let visible = [];
  if (current && !lastSeen) {
    mode = "first";
    visible = [current];
  } else if (current && lastSeen !== reviewReleaseToken(current)) {
    const previousIndex = releases.findIndex((release) => reviewReleaseToken(release) === lastSeen);
    mode = "new";
    visible = previousIndex > 0 ? releases.slice(0, previousIndex) : [current];
  }
  reviewChangeView = { current, mode, releases: visible };
}

function markReviewChangesSeen() {
  const view = reviewChangeView;
  if (!view?.current || ["none", "unavailable"].includes(view.mode)) return;
  try { localStorage.setItem(REVIEW_CHANGE_STORAGE_KEY, reviewReleaseToken(view.current)); } catch (_) { /* cross-visit memory is optional */ }
  reviewChangeView = { current: view.current, mode: "none", releases: [] };
  renderReviewChanges();
}

function renderReviewChanges() {
  const host = reviewById("review-changes-since-visit");
  const badge = reviewById("review-changes-badge");
  const markButton = reviewById("review-changes-mark-seen");
  if (!host || !badge || !markButton) return;
  const view = reviewChangeView || { mode: "none", releases: [] };
  const itemCount = view.releases.reduce((sum, release) => sum + (Array.isArray(release.items) ? release.items.length : 0), 0);
  badge.dataset.state = ["none", "unavailable"].includes(view.mode) ? "none" : "new";
  badge.textContent = view.mode === "unavailable"
    ? reviewL("Ei saatavilla", "Unavailable")
    : view.mode === "none"
    ? reviewL("Ajan tasalla", "Up to date")
    : view.mode === "first"
      ? reviewL("Uusin julkaisu", "Latest release")
      : reviewIsFi() ? `${itemCount} uutta muutosta` : `${itemCount} new changes`;
  markButton.hidden = !view.releases.length || ["none", "unavailable"].includes(view.mode);
  host.replaceChildren();
  if (view.mode === "unavailable") {
    host.append(reviewNode("p", "change-empty", reviewL("Julkaisuhistoriaa ei voitu ladata. Tämä ei estä muun aineiston käyttöä.", "Release history could not be loaded. The rest of the evidence remains available.")));
    return;
  }
  if (!view.releases.length) {
    host.append(reviewNode("p", "change-empty", reviewL("Ei uusia julkaisuja viimeksi nähdyksi merkitsemäsi julkaisun jälkeen.", "No new releases since the last release you marked as seen.")));
    return;
  }
  for (const release of view.releases) {
    const article = reviewNode("article", "change-release");
    const meta = reviewNode("div");
    const time = reviewNode("time", "", new Intl.DateTimeFormat(reviewIsFi() ? "fi-FI" : "en-GB", { year: "numeric", month: "long", day: "numeric" }).format(new Date(release.publishedAt)));
    meta.append(reviewNode("span", "market-status-chip", release.version || release.id), time);
    const copy = reviewNode("div");
    copy.append(reviewNode("h3", "", reviewIsFi() ? release.titleFi : release.titleEn));
    const list = reviewNode("ul");
    for (const item of release.items || []) list.append(reviewNode("li", "", reviewIsFi() ? item.textFi : item.textEn));
    copy.append(list);
    article.append(meta, copy);
    host.append(article);
  }
}

function renderReviewGrades(data) {
  const grades = { A: 0, B: 0, C: 0, D: 0 };
  data.countries.forEach((country) => {
    const grade = country.bestEvidence;
    if (grade in grades) grades[grade] += 1;
  });
  const descriptions = {
    A: reviewL("suora virallinen markkina-, määrä- tai verohavainto", "direct official market, volume or tax observation"),
    B: reviewL("virallinen proxy, hallinnollinen tai oikeudellinen ankkuri", "official proxy, administrative or legal anchor"),
    C: reviewL("malli tai täydentävä lähde", "model or supporting source"),
    D: reviewL("ei vielä hyväksyttyä maakohtaista numeerista ankkuria", "no accepted country-specific numeric anchor yet")
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
  const rows = Object.entries(REVIEW_DIMENSIONS).map(([key, labels]) => {
    const verified = data.countries.filter((country) => reviewStatus(country.dimensions?.[key]) === "verified").length;
    const partial = data.countries.filter((country) => reviewStatus(country.dimensions?.[key]) === "partial").length;
    const row = reviewNode("div", "review-dimension-row");
    row.append(
      reviewNode("strong", "", reviewL(...labels)),
      reviewNode("span", "review-verified", reviewIsFi() ? `${verified} vahvistettu` : `${verified} verified`),
      reviewNode("span", "review-partial", reviewIsFi() ? `${partial} osittainen` : `${partial} partial`)
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
    const label = reviewIsFi() ? REVIEW_BLOCKER_FI[text] || text : REVIEW_BLOCKER_TRANSLATIONS[text] || "Open evidence gap requiring further review.";
    row.append(reviewNode("span", "readiness-dot readiness-open", ""), reviewNode("p", "", label));
    return row;
  }));
  if (!blockers.length) host.append(reviewNode("p", "muted", reviewL("Valmiustietoa ei ollut saatavilla.", "No readiness record was available.")));
}

function renderReviewLegal(data) {
  const host = reviewById("review-legal");
  const items = Array.isArray(data.legal) ? data.legal : [];
  host.replaceChildren(...items.map((item) => {
    const li = reviewNode("li");
    li.append(
      reviewNode("time", "", item.eventDate || reviewL("Virallinen asiakirja", "Official record")),
      reviewNode("strong", "", item.reference || item.authority),
      reviewNode("p", "", reviewIsFi() ? item.statement || "" : REVIEW_LEGAL_SUMMARIES[item.legalId] || "Official legal record; verify its current status and scope.")
    );
    const url = reviewUrl(item.sourceUrl);
    if (url) {
      const link = reviewNode("a", "", reviewL("Avaa virallinen lähde →", "Open official source →"));
      link.href = url;
      link.target = "_blank";
      link.rel = "noreferrer";
      li.append(link);
    }
    return li;
  }));
}

function renderReviewMeta(data) {
  const latestRelease = Array.isArray(reviewChangelog?.releases)
    ? [...reviewChangelog.releases].sort((a, b) => String(b.publishedAt).localeCompare(String(a.publishedAt)))[0]
    : null;
  const asOf = latestRelease?.publishedAt || data.meta?.asOf || data.meta?.generatedAt || "";
  const time = reviewById("review-as-of");
  time.textContent = reviewFormatDate(asOf);
  time.dateTime = asOf;
  reviewById("review-site-version").textContent = latestRelease?.version || "—";
  reviewById("review-source-commit").textContent = String(data.meta?.legacySourceCommit || "—").slice(0, 9);
}

async function copyReviewLink() {
  const status = reviewById("copy-review-status");
  try {
    await navigator.clipboard.writeText(location.href.split("#")[0]);
    status.textContent = reviewL("Tarkistuslinkki kopioitu.", "Review link copied.");
  } catch (_) {
    status.textContent = reviewIsFi() ? `Jaa tämä osoite: ${location.href.split("#")[0]}` : `Share this URL: ${location.href.split("#")[0]}`;
  }
}

function renderReview(data) {
  renderReviewMeta(data);
  renderReviewMetrics(data);
  renderReviewGrades(data);
  renderReviewDimensions(data);
  renderReviewBlockers(data);
  renderReviewLegal(data);
  if (reviewMarketData) renderReviewMarket(reviewMarketData);
  else renderReviewMarketUnavailable();
  renderReviewChanges();
}

async function initReview() {
  reviewById("copy-review-link").addEventListener("click", copyReviewLink);
  reviewById("print-review").addEventListener("click", () => window.print());
  reviewById("review-changes-mark-seen").addEventListener("click", markReviewChangesSeen);
  document.addEventListener("pixan:languagechange", () => {
    reviewById("copy-review-status").textContent = "";
    if (reviewData) renderReview(reviewData);
  });
  try {
    const [atlasResult, marketResult, changelogResult] = await Promise.allSettled([
      fetch("data/atlas.json", { cache: "no-store" }),
      fetch("data/market-values.json", { cache: "no-store" }),
      fetch("data/changelog.json", { cache: "no-store" })
    ]);
    if (atlasResult.status !== "fulfilled" || !atlasResult.value.ok) throw new Error(`Atlas HTTP ${atlasResult.status === "fulfilled" ? atlasResult.value.status : "network error"}`);
    const data = await atlasResult.value.json();
    if (!Array.isArray(data.countries) || data.countries.length !== 195 || !Array.isArray(data.evidence)) {
      throw new Error("Reviewed dataset validation failed");
    }
    reviewData = data;

    try {
      if (marketResult.status !== "fulfilled" || !marketResult.value.ok) throw new Error(`HTTP ${marketResult.status === "fulfilled" ? marketResult.value.status : "network error"}`);
      const marketData = await marketResult.value.json();
      if (!Array.isArray(marketData.observations) || !Array.isArray(marketData.models)) throw new Error("schema validation failed");
      reviewMarketData = marketData;
    } catch (error) {
      reviewMarketData = null;
      console.warn("Optional market-value dataset unavailable", error);
    }

    try {
      if (changelogResult.status !== "fulfilled" || !changelogResult.value.ok) throw new Error(`HTTP ${changelogResult.status === "fulfilled" ? changelogResult.value.status : "network error"}`);
      const changelog = await changelogResult.value.json();
      if (!Array.isArray(changelog.releases) || !changelog.releases.length) throw new Error("schema validation failed");
      reviewChangelog = changelog;
    } catch (error) {
      reviewChangelog = null;
      console.warn("Optional changelog unavailable", error);
    }
    prepareReviewChangeView();
    renderReview(data);
  } catch (error) {
    console.error(error);
    reviewById("review-load-error").hidden = false;
  }
}

initReview();
