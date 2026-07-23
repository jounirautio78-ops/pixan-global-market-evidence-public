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

const REVIEW_TRANSACTION_PATHS = [
  {
    code: "01",
    title: ["Osakepanttirahoitus", "Share-backed financing"],
    purpose: [
      "Arvioi, voidaanko rahoitus rakentaa vahvistetun osakeomistuksen, takaisinmaksukyvyn ja realisoitavan vakuuspolun varaan.",
      "Tests whether financing can be supported by verified share title, repayment capacity and a realisable collateral path."
    ],
    gates: [
      ["Ajantasainen osakeluettelo, omistusketju sekä siirto- ja panttausrajoitukset on vahvistettu hallitussa yksityisessä tarkastuksessa.", "Current cap table, title chain and transfer or pledge restrictions verified in controlled private diligence."],
      ["Auditoidut taloustiedot, rahoitustarve ja ensisijainen takaisinmaksulähde on dokumentoitu.", "Audited financial information, funding need and primary repayment source documented."],
      ["Riippumaton arvonmääritys sekä lainanantajan downside-, likviditeetti- ja toteutettavuusanalyysi on tehty.", "Independent valuation plus lender downside, liquidity and realisation analysis completed."],
      ["Ehdot, vakuusasiakirjat ja hyväksynnät on käsitelty hallitussa datahuoneessa.", "Terms, security documents and approvals reviewed in a controlled data room."]
    ]
  },
  {
    code: "02",
    title: ["IP-vakuudellinen yritysrahoitus", "IP-backed corporate financing"],
    purpose: [
      "Arvioi, onko patenttioikeuksilla tai todennettavalla IP-kassavirralla lainanantajalle käyttökelpoinen downside-arvo.",
      "Tests whether patent rights or documented IP cash flow can support a lender-relevant downside case."
    ],
    gates: [
      ["Asiantuntijan allekirjoittama maakohtainen oikeus-, omistus-, rasite-, maksu- ja vaatimusmatriisi on valmis.", "Counsel-signed country matrix for rights, title, encumbrances, fees and operative claims completed."],
      ["Priorisoiduista tuotteista on hallussapitoketju, tekninen purku, riippumaton mittaus ja asiantuntijan tarkastama claim chart.", "Prioritised products have chain of custody, teardown, independent measurement and counsel-reviewed claim charts."],
      ["Toteutunut tai sopimuspohjainen kassavirta ja riippumaton IP-arvonmääritys on dokumentoitu.", "Realised or contract-based cash flow and an independent IP valuation documented."],
      ["Vakuuden perustaminen, etusija, täytäntöönpano ja realisointikulut on vahvistettu soveltuvissa valtioissa.", "Perfection, priority, enforcement and realisation costs confirmed in the relevant jurisdictions."]
    ]
  },
  {
    code: "03",
    title: ["Strateginen myynti tai lisensointi", "Strategic sale or licensing"],
    purpose: [
      "Arvioi, voidaanko oikeuksista ja niiden kaupallisesta merkityksestä rakentaa ostajalle tai lisenssinsaajalle tarkistettava tapaus.",
      "Tests whether the rights and their commercial relevance can form a reviewable case for a buyer or licensee."
    ],
    gates: [
      ["Transaktiovaltuus, myytävä tai lisensoitava oikeuspaketti ja maantieteellinen laajuus on vahvistettu.", "Transaction authority, rights package and geographic scope verified."],
      ["Maa-, tuote- ja vaatimuskohtainen yhteys perustuu ajantasaisiin rekistereihin ja tuotekohtaiseen näyttöön.", "Country, product and claim mapping is grounded in current registers and product-specific evidence."],
      ["Asiakas-, sopimus-, lisenssi-, vahingonkorvaus- tai vertailukauppanäyttö on dokumentoitu eikä oletettu.", "Customer, contract, licence, damages or comparable-transaction evidence is documented rather than assumed."],
      ["Yhteydenotot, salassapito, kilpailuoikeus ja neuvotteluaineisto on hyväksytty hallitussa prosessissa.", "Outreach, confidentiality, competition-law and negotiation materials approved through a controlled process."]
    ]
  }
];

const REVIEW_MATRIX_DIMENSIONS = {
  officialSales: ["myynti", "sales"],
  officialVolume: ["määrä", "volume"],
  taxRevenue: ["vero", "tax"],
  customs: ["tulli", "customs"]
};

let reviewData = null;
let reviewMarketData = null;
let reviewPatentData = null;
let reviewChangelog = null;
let reviewRequestData = null;
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
  const options = { year: "numeric", month: "long", day: "numeric" };
  if (/^\d{4}-\d{2}-\d{2}$/.test(String(value))) options.timeZone = "UTC";
  return new Intl.DateTimeFormat(reviewIsFi() ? "fi-FI" : "en-GB", options).format(date);
}

function reviewStatus(value) {
  const status = String(value || "").toLowerCase();
  if (["verified", "confirmed", "official"].includes(status)) return "verified";
  if (["partial", "proxy", "modeled", "modelled"].includes(status)) return "partial";
  return "missing";
}

function renderReviewMetrics(data) {
  const countries = data.countries;
  const observations = Array.isArray(reviewMarketData?.observations) ? reviewMarketData.observations : [];
  const official = observations.filter((item) => String(item.evidenceStatus || "").startsWith("official_"));
  const quantified = new Set(official.map((item) => item.countryIso2).filter(Boolean));
  const officialRetail = new Set(official.filter((item) => item.metric === "consumer_retail_market_value").map((item) => item.countryIso2).filter(Boolean));
  const modelled = new Set((reviewMarketData?.models || []).map((item) => item.countryIso2).filter(Boolean));
  const metrics = [
    [reviewL("Tutkimusmaailma", "Research universe"), `${countries.length} / 195`, reviewL("Suvereenit valtiot indeksoitu; ei 195 mitattua markkinaa", "Sovereign states indexed; not 195 measured markets")],
    [reviewL("Määrällisiä vuosihavaintoja", "Countries with annual numeric data"), `${quantified.size} / 195`, reviewL("Raha-, vero- tai määräarvoja; mittarit pidetään erillään", "Monetary, tax or volume records; measures remain separate")],
    [reviewL("Virallinen kuluttajavähittäisarvo", "Official consumer-retail value"), `${officialRetail.size} / 195`, reviewL("Toimitusarvo ei ole kuluttajamyyntiä", "Shipment value is not consumer retail")],
    [reviewL("Atlaksen maamalli", "Atlas country model"), `${modelled.size} / 195`, reviewL("Saksan nesteskenaario; matala luottamus", "Germany liquid scenario; low confidence")]
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
  const canada = observations.find((item) => item.observationId === "CA-2024-MANUFACTURER-IMPORTER-SHIPMENTS-VALUE");
  const germany = models.find((item) => item.modelId === "DE-2025-LIQUID-RETAIL-EQUIVALENT-RANGE");
  const sourceMap = new Map((market?.sources || []).map((source) => [source.sourceId, source]));
  const cards = commercial.map((item) => ({
    label: reviewIsFi() ? item.labelFi : item.labelEn,
    value: reviewMarketFormat(item.value, item.currency),
    note: reviewIsFi() ? item.limitationFi : item.limitationEn,
    url: reviewUrl(sourceMap.get(item.sourceIds?.[0])?.pageUrl)
  }));
  cards.push(
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
  );
  const host = reviewById("review-market-metrics");
  host.replaceChildren(...cards.map((item) => {
    const card = reviewNode("article", "panel review-market-card");
    card.append(reviewNode("span", "kicker", item.label), reviewNode("strong", "", item.value), reviewNode("small", "", item.note));
    if (item.url) {
      const link = reviewNode("a", "", reviewL("Avaa julkaisijan lähde →", "Open publisher source →"));
      link.href = item.url;
      link.target = "_blank";
      link.rel = "noreferrer";
      card.append(link);
    }
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

function renderReviewTransactionPaths() {
  const host = reviewById("review-transaction-paths");
  if (!host) return;
  host.replaceChildren(...REVIEW_TRANSACTION_PATHS.map((path) => {
    const card = reviewNode("article", "transaction-path-card");
    const head = reviewNode("div", "transaction-path-head");
    head.append(
      reviewNode("span", "transaction-path-code", path.code),
      reviewNode("span", "transaction-path-status", "HOLD")
    );
    const gates = reviewNode("ul", "transaction-path-gates");
    for (const gate of path.gates) gates.append(reviewNode("li", "", reviewL(...gate)));
    card.append(
      head,
      reviewNode("h3", "", reviewL(...path.title)),
      reviewNode("p", "transaction-path-purpose", reviewL(...path.purpose)),
      reviewNode("strong", "transaction-path-gate-label", reviewL("Vapautusportit", "Release gates")),
      gates,
      reviewNode(
        "p",
        "transaction-path-foot",
        reviewL(
          "Julkinen tila: HOLD. Tämä sivu ei tallenna yksityisen tarkastuksen tulosta tai transaktiotilaa.",
          "Public status: HOLD. This page does not record private-diligence outcomes or transaction status."
        )
      )
    );
    return card;
  }));
}

function reviewMatrixEvidenceCell(country) {
  const cell = reviewNode("td", "bankability-market-cell");
  if (!country) {
    cell.append(reviewNode("strong", "", reviewL("Ei maadatariviä", "No country-data row")));
    return cell;
  }
  const headline = reviewNode("div", "bankability-market-head");
  headline.append(
    reviewNode("span", `grade grade-${String(country.bestEvidence || "D").toLowerCase()}`, country.bestEvidence || "D"),
    reviewNode("strong", "", `${Number(country.coveragePercent) || 0}%`)
  );
  const chips = reviewNode("div", "bankability-dimension-chips");
  for (const [key, labels] of Object.entries(REVIEW_MATRIX_DIMENSIONS)) {
    const status = reviewStatus(country.dimensions?.[key]);
    const chip = reviewNode("span", `bankability-dimension-chip bankability-dimension-${status}`);
    chip.append(
      reviewNode("i", "", ""),
      document.createTextNode(`${reviewL(...labels)} · ${reviewL(
        status === "verified" ? "vahvistettu" : status === "partial" ? "osittainen" : "puuttuu",
        status === "verified" ? "verified" : status === "partial" ? "partial" : "missing"
      )}`)
    );
    chips.append(chip);
  }
  cell.append(
    headline,
    reviewNode("small", "", reviewL("Evidenssivalmius; ei markkinaosuus", "Evidence readiness; not market share")),
    chips
  );
  return cell;
}

function reviewMatrixRequestCell(route) {
  const cell = reviewNode("td", "bankability-request-cell");
  const sent = route.status === "sent";
  cell.append(
    reviewNode(
      "span",
      sent ? "request-program-status request-program-status-sent" : "request-program-status",
      sent ? reviewL("Lähetetty", "Sent") : reviewL("Luonnos — ei lähetetty", "Draft — not sent")
    ),
    reviewNode("strong", "", reviewIsFi() ? route.primaryAuthority.nameFi : route.primaryAuthority.nameEn)
  );
  if (sent) {
    cell.append(reviewNode("small", "", `${reviewL("Julkinen päivä", "Public date")}: ${route.dispatch.sentOn}`));
    if (route.dispatch.publicAuthorityReference) {
      cell.append(reviewNode("code", "", `${reviewL("Viite", "Reference")}: ${route.dispatch.publicAuthorityReference}`));
    }
  } else {
    cell.append(reviewNode("small", "", reviewL("Tämä sivu ei hyväksy tai lähetä pyyntöä.", "This page does not approve or send the request.")));
  }
  return cell;
}

function reviewMatrixRightCell(route, familyMember, proceedings) {
  const cell = reviewNode("td", "bankability-right-cell");
  if (route.countryIso2 === "DE" && proceedings.length) {
    cell.append(
      reviewNode("strong", "", "EP3032975B2 · DE"),
      reviewNode(
        "p",
        "",
        reviewL(
          "Saksan osa yksilöidään virallisissa kansallisissa ratkaisuissa. Nykyistä kansallista rekisteritilaa, omistusta, maksuja ja rasitteita ei ole tässä vahvistettu.",
          "The German part is identified in official national decisions. Current national register status, title, fees and encumbrances are not established here."
        )
      ),
      reviewNode("small", "", reviewL("Tuomioistuinasiakirja ei ole kansallinen voimassaolotodistus tai arvonmääritys.", "A court record is not a national-status certificate or valuation."))
    );
    return cell;
  }
  if (!familyMember) {
    cell.append(
      reviewNode("strong", "", reviewL("Ei vahvistettu", "Not established")),
      reviewNode(
        "p",
        "",
        reviewL(
          "Nykyisessä julkisessa perheinventaariossa ei ole tämän maan riviä. Tämä ei osoita, ettei oikeutta ole.",
          "The current public family inventory has no row for this country. This is not evidence that no right exists."
        )
      )
    );
    return cell;
  }
  cell.append(
    reviewNode("strong", "", familyMember.publicationNumber || familyMember.applicationNumber || route.countryIso2),
    reviewNode("p", "", reviewPatentText(familyMember, "currentNationalStatus") || reviewL("Nykyinen kansallinen tila vahvistamatta.", "Current national status not verified.")),
    reviewNode("small", "", reviewPatentText(familyMember, "limitation"))
  );
  return cell;
}

function reviewMatrixClaimCell(route, proceedings) {
  const cell = reviewNode("td", "bankability-claim-cell");
  if (route.countryIso2 === "DE" && proceedings.length) {
    cell.append(
      reviewNode("strong", "", reviewL("Viralliset kansalliset ratkaisut", "Official national decisions")),
      reviewNode(
        "p",
        "",
        reviewL(
          "Ratkaisut koskevat käsiteltyjä tuotteita ja Saksan aluetta. Julkinen tuote–vaatimusvertailu puuttuu; lainvoimaisuus, täytäntöönpano ja maksetut korvaukset eivät ole kokonaan vahvistettuja.",
          "The decisions concern the examined products and Germany. A public product-to-claim chart is missing; finality, enforcement and damages paid are not fully established."
        )
      )
    );
    return cell;
  }
  if (route.countryIso2 === "CN" && proceedings.length) {
    cell.append(
      reviewNode("strong", "", reviewL("Hakijapuolen uudelleentarkastus", "Applicant-side re-examination")),
      reviewNode(
        "p",
        "",
        reviewL(
          "Ei loukkausasia. Virallisen päätöksen perustelut ja julkinen tuote–vaatimusvertailu puuttuvat.",
          "Not an infringement case. The official decision reasoning and a public product-to-claim chart are missing."
        )
      )
    );
    return cell;
  }
  cell.append(
    reviewNode("strong", "", reviewL("Puuttuu", "Missing")),
    reviewNode(
      "p",
      "",
      reviewL(
        "Julkinen aineisto ei sisällä maakohtaista tuotteen ja vaatimusten kartoitusta tai täytäntöönpanojohtopäätöstä.",
        "The public evidence contains no country-specific product-to-claim mapping or enforcement conclusion."
      )
    )
  );
  return cell;
}

function reviewMatrixNextGateCell(route, familyMember, proceedings) {
  const cell = reviewNode("td", "bankability-next-gate");
  const marketAction = route.status === "sent"
    ? reviewL(
      "Kirjaa ja tarkista mahdollinen viranomaisvastaus, määritelmät, kattavuus, puutteet ja revisiot ennen julkista käyttöä.",
      "Record and review any authority response, definitions, coverage, missingness and revisions before public use."
    )
    : reviewL(
      `Tee ihmistarkistus suunnitellulle ${route.primaryAuthority.nameFi} -pyynnölle; tämä sivu ei lähetä sitä.`,
      `Human-review the planned ${route.primaryAuthority.nameEn} request; this page does not send it.`
    );
  let rightsAction;
  if (route.countryIso2 === "DE" && proceedings.length) {
    rightsAction = reviewL(
      "Hanki tuore Saksan oikeus-, omistus-, maksu- ja prosessin lopullisuustarkistus sekä asiantuntijan tarkastama tuotekohtainen claim chart.",
      "Obtain a fresh German rights, title, fee and proceeding-finality check plus a counsel-reviewed product claim chart."
    );
  } else if (familyMember) {
    rightsAction = reviewL(
      "Hanki tuore virallinen kansallinen ote voimassaolosta, omistuksesta, maksuista, rasitteista ja käytettävistä vaatimuksista.",
      "Obtain a fresh official national extract covering status, title, fees, encumbrances and operative claims."
    );
  } else {
    rightsAction = reviewL(
      "Vahvista ensin virallisesta kansallisesta rekisteristä, onko nykyinen oikeus olemassa, ennen markkinaevidenssin kohdistamista.",
      "First establish from the official national register whether a current right exists before attributing market evidence."
    );
  }
  const market = reviewNode("p");
  market.append(reviewNode("strong", "", reviewL("Markkina: ", "Market: ")), document.createTextNode(marketAction));
  const rights = reviewNode("p");
  rights.append(reviewNode("strong", "", reviewL("Oikeus: ", "Right: ")), document.createTextNode(rightsAction));
  cell.append(market, rights);
  return cell;
}

function renderReviewTop10Matrix() {
  const status = reviewById("review-top10-matrix-status");
  const wrap = reviewById("review-top10-matrix-wrap");
  const host = reviewById("review-top10-matrix");
  if (!status || !wrap || !host) return;
  const routes = Array.isArray(reviewRequestData?.routes)
    ? [...reviewRequestData.routes].sort((a, b) => a.operationalRank - b.operationalRank).slice(0, 10)
    : [];
  if (!reviewData || routes.length !== 10) {
    host.replaceChildren();
    wrap.hidden = true;
    status.dataset.state = "error";
    status.textContent = reviewL("Top 10 -matriisia ei voitu muodostaa tarkistetusta aineistosta.", "The Top 10 matrix could not be built from the reviewed data.");
    return;
  }
  const countryMap = new Map(reviewData.countries.map((country) => [country.iso2, country]));
  const familyMap = new Map((reviewPatentData?.familyMembers || []).map((item) => [item.jurisdictionCode, item]));
  const proceedingsMap = new Map();
  for (const proceeding of reviewPatentData?.proceedings || []) {
    if (!proceedingsMap.has(proceeding.jurisdictionCode)) proceedingsMap.set(proceeding.jurisdictionCode, []);
    proceedingsMap.get(proceeding.jurisdictionCode).push(proceeding);
  }

  const rows = routes.map((route) => {
    const row = reviewNode("tr");
    const priority = reviewNode("td", "bankability-country-cell");
    priority.append(
      reviewNode("span", "bankability-rank", `#${String(route.operationalRank).padStart(2, "0")} · ${route.priorityCode}`),
      reviewNode("strong", "", reviewIsFi() ? route.countryFi : route.countryEn),
      reviewNode("code", "", route.countryIso2)
    );
    const familyMember = familyMap.get(route.countryIso2);
    const proceedings = proceedingsMap.get(route.countryIso2) || [];
    row.append(
      priority,
      reviewMatrixEvidenceCell(countryMap.get(route.countryIso2)),
      reviewMatrixRequestCell(route),
      reviewMatrixRightCell(route, familyMember, proceedings),
      reviewMatrixClaimCell(route, proceedings),
      reviewMatrixNextGateCell(route, familyMember, proceedings)
    );
    return row;
  });
  host.replaceChildren(...rows);
  wrap.hidden = false;
  status.dataset.state = reviewPatentData ? "ready" : "caution";
  status.textContent = reviewPatentData
    ? reviewL("10 reittiä yhdistetty · puuttuva näyttö säilytetty puuttuvana", "10 routes joined · missing evidence preserved as missing")
    : reviewL("Markkina- ja pyyntödata yhdistetty; patenttiaineisto ei ollut saatavilla.", "Market and request data joined; patent data was unavailable.");
}

function reviewPatentText(item, key) {
  if (!item) return "";
  return reviewIsFi() ? item[`${key}Fi`] || item[key] || item[`${key}En`] || "" : item[`${key}En`] || item[key] || item[`${key}Fi`] || "";
}

function reviewPatentLinks(host, sourceIds) {
  const map = new Map((reviewPatentData?.sources || []).map((source) => [source.sourceId, source]));
  const wrap = reviewNode("div", "patent-source-links patent-source-links-compact");
  for (const sourceId of sourceIds || []) {
    const source = map.get(sourceId);
    const url = reviewUrl(source?.url);
    if (!source || !url) continue;
    const link = reviewNode("a", "", sourceId);
    link.href = url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.title = reviewPatentText(source, "limitation");
    wrap.append(link);
  }
  if (wrap.childElementCount) host.append(wrap);
}

function renderReviewPatent() {
  const data = reviewPatentData;
  const metricsHost = reviewById("review-patent-metrics");
  const statusHost = reviewById("review-patent-status");
  const alertsHost = reviewById("review-patent-alerts");
  const proceedingsHost = reviewById("review-patent-proceedings");
  if (!data) {
    const unavailable = reviewNode("article", "panel review-market-card");
    unavailable.append(reviewNode("span", "kicker", reviewL("Patenttiaineisto", "Patent data")), reviewNode("strong", "", reviewL("Ei saatavilla", "Unavailable")), reviewNode("small", "", reviewL("Käytä koko atlaksen virallisia Saksan ankkureita ja tarkista rekisterit suoraan.", "Use the full atlas's official German anchors and check registers directly.")));
    metricsHost.replaceChildren(unavailable);
    statusHost.replaceChildren();
    alertsHost.replaceChildren();
    proceedingsHost.replaceChildren();
    return;
  }

  const verifiedNational = (data.familyMembers || []).filter((item) => item.verificationLevel === "official_national_record");
  const metrics = [
    [reviewL("Perhejulkaisut", "Family publication records"), data.summary?.familyRecordCount || 0, reviewL("Julkaisu ei yksin ole nykyinen kansallinen oikeus", "A publication alone is not a current national right")],
    [reviewL("Kansallisesti vahvistetut", "National status verified"), verifiedNational.length, reviewL("Suomi, Australia, Etelä-Korea ja Venäjä tässä julkaisussa", "Finland, Australia, South Korea and Russia in this release")],
    [reviewL("Avoimet määräpäivät", "Open diligence alerts"), data.summary?.diligenceAlertCount || 0, reviewL(`${data.summary?.unresolvedProceedingCount || 0} prosessin lopputulos tai lainvoimaisuus avoin`, `${data.summary?.unresolvedProceedingCount || 0} proceeding outcomes or finality points remain open`)]
  ];
  metricsHost.replaceChildren(...metrics.map(([label, value, note]) => {
    const card = reviewNode("article", "panel review-market-card");
    card.append(reviewNode("span", "kicker", label), reviewNode("strong", "", value), reviewNode("small", "", note));
    return card;
  }));

  statusHost.replaceChildren(...verifiedNational.map((item) => {
    const row = reviewNode("article", "review-patent-status-item");
    row.append(reviewNode("strong", "", `${reviewPatentText(item, "jurisdiction")} · ${item.publicationNumber}`), reviewNode("p", "", reviewPatentText(item, "currentNationalStatus")), reviewNode("small", "", reviewPatentText(item, "limitation")));
    reviewPatentLinks(row, item.sourceIds);
    return row;
  }));

  alertsHost.replaceChildren(...(data.diligenceAlerts || []).map((item) => {
    const row = reviewNode("article", `review-patent-alert review-patent-alert-${item.priority}`);
    const meta = reviewNode("div", "review-patent-alert-meta");
    meta.append(reviewNode("strong", "", item.jurisdictionCode), reviewNode("time", "", reviewFormatDate(item.targetDate)), reviewNode("span", "", String(item.priority).toUpperCase()));
    row.append(meta, reviewNode("h4", "", reviewPatentText(item, "title")), reviewNode("p", "", reviewPatentText(item, "detail")), reviewNode("small", "", reviewPatentText(item, "limitation")));
    reviewPatentLinks(row, item.sourceIds);
    return row;
  }));

  proceedingsHost.replaceChildren(...(data.proceedings || []).map((item) => {
    const row = reviewNode("article", "review-patent-proceeding");
    row.append(reviewNode("span", "kicker", `${item.jurisdictionCode} · ${item.reference}`), reviewNode("h4", "", reviewPatentText(item, "title")), reviewNode("p", "", reviewPatentText(item, "detail")));
    const finality = reviewNode("p", "review-patent-finality");
    finality.append(reviewNode("strong", "", reviewL("Lopullisuus: ", "Finality: ")), document.createTextNode(reviewPatentText(item, "finality")));
    row.append(finality, reviewNode("small", "", reviewPatentText(item, "limitation")));
    reviewPatentLinks(row, item.sourceIds);
    return row;
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
  renderReviewTransactionPaths();
  renderReviewTop10Matrix();
  if (reviewMarketData) renderReviewMarket(reviewMarketData);
  else renderReviewMarketUnavailable();
  renderReviewPatent();
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
    const [atlasResult, marketResult, patentResult, changelogResult, requestResult] = await Promise.allSettled([
      fetch("data/atlas.json", { cache: "no-store" }),
      fetch("data/market-values.json", { cache: "no-store" }),
      fetch("data/patent-history.json", { cache: "no-store" }),
      fetch("data/changelog.json", { cache: "no-store" }),
      fetch("data/top20-data-request-routes.json", { cache: "no-store" })
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
      if (patentResult.status !== "fulfilled" || !patentResult.value.ok) throw new Error(`HTTP ${patentResult.status === "fulfilled" ? patentResult.value.status : "network error"}`);
      const patentData = await patentResult.value.json();
      if (!Array.isArray(patentData.familyMembers) || !Array.isArray(patentData.proceedings) || !Array.isArray(patentData.diligenceAlerts) || !Array.isArray(patentData.sources)) throw new Error("schema validation failed");
      reviewPatentData = patentData;
    } catch (error) {
      reviewPatentData = null;
      console.warn("Optional patent-history dataset unavailable", error);
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

    try {
      if (requestResult.status !== "fulfilled" || !requestResult.value.ok) throw new Error(`HTTP ${requestResult.status === "fulfilled" ? requestResult.value.status : "network error"}`);
      const requestData = await requestResult.value.json();
      const routes = Array.isArray(requestData.routes) ? requestData.routes : [];
      const ranked = [...routes].sort((a, b) => a.operationalRank - b.operationalRank);
      const uniqueCountries = new Set(routes.map((route) => route.countryIso2));
      if (requestData.schemaVersion !== 2 || routes.length !== 20 || uniqueCountries.size !== 20
        || ranked.slice(0, 10).some((route, index) => route.operationalRank !== index + 1)) {
        throw new Error("schema validation failed");
      }
      reviewRequestData = requestData;
    } catch (error) {
      reviewRequestData = null;
      console.warn("Optional request-programme dataset unavailable", error);
    }
    prepareReviewChangeView();
    renderReview(data);
  } catch (error) {
    console.error(error);
    reviewById("review-load-error").hidden = false;
  }
}

initReview();
