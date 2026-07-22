"use strict";

const DIMENSION_LABELS = {
  officialSales: "Virallinen myynti / toimitus",
  officialVolume: "Virallinen volyymi",
  taxRevenue: "Toteutunut vero",
  customs: "Tullivirta",
  model: "Mallinnus",
  regulation: "Sääntelytila",
  patent: "Patenttistatus"
};

const DIMENSION_HELP = {
  officialSales: "suora myynti tai valmistaja-/maahantuojatoimitus",
  officialVolume: "verotettu tai viranomaiselle raportoitu määrä",
  taxRevenue: "toteutunut verokertymä; ei pelkkä verokanta × määrä",
  customs: "virallinen rajavirta; ei kuluttajamyynti",
  model: "julkaistu tai auditoitava laskennallinen arvio",
  regulation: "ajantasainen oikeudellinen markkinastatus",
  patent: "virallisen maarekisterin voimassaolotarkistus"
};

const FALLBACK_METHODS = [
  { title: "Virallinen myynti", text: "Haetaan viranomaisen julkaisema kuluttajamyynti tai toimitusmyynti ja säilytetään alkuperäinen mittarityyppi." },
  { title: "Vero ja volyymi", text: "Täsmäytetään valmisteveron määrä, litrat tai millilitrat ja tuoteryhmän tarkka rajaus." },
  { title: "Tullireitti", text: "Käsitellään laitteet ja inhaloitavat tuotteet HS/CN/HTS-koodeittain, vienti ja jälleenvienti erotellen." },
  { title: "Mallinnettu alue", text: "Vasta viimeisenä yhdistetään käyttäjät, kulutus ja hinnat; oletukset ja herkkyys julkaistaan tuloksen mukana." }
];

const FALLBACK_RULES = [
  "Puuttuva havainto ei saa muuttua nollaksi.",
  "Tullivirtaa tai verokantaa ei saa nimetä kuluttajamyynniksi.",
  "Jokaisella numerolla on oltava maa, vuosi, yksikkö, tuoterajaus ja lähde.",
  "Laskettu vero erotetaan toteutuneesta verokertymästä.",
  "Yhdistettyä nikotiinituoteluokkaa ei nimetä e-nesteeksi ilman erittelyä.",
  "Saapuvaa tiedostoa ei julkaista ennen turvallisuus- ja lähdeauditointia.",
  "Patenttistatus vaatii maakohtaisen virallisen rekisteritarkistuksen.",
  "Revisio säilyttää historian eikä kirjoita aikaisempaa havaintoa näkymättömästi yli."
];

const state = {
  data: null,
  tab: "overview",
  countryQuery: "",
  region: "",
  grade: "",
  evidenceQuery: "",
  evidenceGrade: ""
};

const byId = (id) => document.getElementById(id);

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined && text !== null) element.textContent = String(text);
  return element;
}

function safeExternalUrl(value) {
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) ? url.href : null;
  } catch (_) {
    return null;
  }
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("fi-FI", { year: "numeric", month: "long", day: "numeric" }).format(date);
}

function valueAt(source, paths, fallback = undefined) {
  for (const path of paths) {
    const value = path.split(".").reduce((item, key) => item?.[key], source);
    if (value !== undefined && value !== null) return value;
  }
  return fallback;
}

function countries() {
  return Array.isArray(state.data?.countries) ? state.data.countries : [];
}

function evidenceItems() {
  return Array.isArray(state.data?.evidence) ? state.data.evidence : [];
}

function gradeOf(country) {
  const grade = String(country.bestEvidence || country.grade || "D").toUpperCase();
  return ["A", "B", "C", "D"].includes(grade) ? grade : "D";
}

function gradeBadge(grade) {
  return node("span", `grade grade-${grade.toLowerCase()}`, grade);
}

function coverageOf(country) {
  const explicit = Number(country.coveragePercent);
  if (Number.isFinite(explicit)) return Math.max(0, Math.min(100, Math.round(explicit)));
  const dimensions = country.dimensions || {};
  const keys = Object.keys(DIMENSION_LABELS);
  const points = keys.reduce((sum, key) => {
    const status = normalizeDimension(dimensions[key]);
    return sum + (status === "confirmed" ? 1 : status === "partial" ? .5 : 0);
  }, 0);
  return Math.round((points / keys.length) * 100);
}

function normalizeDimension(value) {
  if (value === true) return "confirmed";
  if (value === false || value === null || value === undefined) return "missing";
  if (typeof value === "object") value = value.status || value.value;
  const status = String(value || "").toLowerCase();
  if (["confirmed", "verified", "official", "observed", "complete", "yes"].includes(status)) return "confirmed";
  if (["partial", "proxy", "modeled", "modelled", "forecast", "mixed"].includes(status)) return "partial";
  if (["not_applicable", "n/a", "na"].includes(status)) return "not_applicable";
  return "missing";
}

function statusLabel(status) {
  return ({ confirmed: "vahvistettu", partial: "osittainen", missing: "puuttuu", not_applicable: "ei sovellu" })[status] || "puuttuu";
}

function sourceLinksOf(country) {
  const links = Array.isArray(country.sourceLinks) ? country.sourceLinks : [];
  return links.map((item) => {
    if (typeof item === "string") {
      const url = safeExternalUrl(item);
      return { label: url ? new URL(url).hostname : "Lähde", url: item };
    }
    return { label: item.label || item.title || item.source || "Lähde", url: item.url };
  }).filter((item) => safeExternalUrl(item.url));
}

function renderMetrics() {
  const list = countries();
  const grades = list.reduce((acc, country) => {
    const grade = gradeOf(country);
    acc[grade] = (acc[grade] || 0) + 1;
    return acc;
  }, {});
  const official = list.filter((country) => ["confirmed", "partial"].includes(normalizeDimension(country.dimensions?.officialSales)) || normalizeDimension(country.dimensions?.officialVolume) === "confirmed" || normalizeDimension(country.dimensions?.taxRevenue) === "confirmed").length;
  const sourced = list.filter((country) => gradeOf(country) !== "D").length;
  const metrics = [
    { label: "Maailman universumi", value: list.length, note: "UN 193 + Pyhä istuin + Palestiina" },
    { label: "Viranomaisankkuri", value: grades.A || 0, note: "A-lähde ei tarkoita täydellistä markkinapeittoa" },
    { label: "Numeerinen reitti", value: sourced, note: "A-, B- tai C-tason havainto" },
    { label: "Myynti / vero / volyymi", value: official, note: "Vähintään osittainen viranomaisreitti" }
  ];
  const grid = byId("metric-grid");
  grid.replaceChildren();
  for (const metric of metrics) {
    const card = node("article", "metric-card");
    card.append(node("span", "", metric.label), node("strong", "", metric.value), node("small", "", metric.note));
    grid.append(card);
  }
}

function renderCoverageBars() {
  const list = countries();
  const host = byId("coverage-bars");
  host.replaceChildren();
  for (const [key, label] of Object.entries(DIMENSION_LABELS)) {
    const count = list.filter((country) => ["confirmed", "partial"].includes(normalizeDimension(country.dimensions?.[key]))).length;
    const confirmed = list.filter((country) => normalizeDimension(country.dimensions?.[key]) === "confirmed").length;
    const percent = list.length ? (count / list.length) * 100 : 0;
    const row = node("div", "coverage-row");
    const labelBox = node("div", "coverage-label");
    labelBox.append(node("strong", "", label), node("small", "", DIMENSION_HELP[key]));
    const track = node("div", "coverage-track");
    const fill = node("div", "coverage-fill");
    fill.style.width = `${percent}%`;
    track.append(fill);
    row.append(labelBox, track, node("span", "coverage-number", `${count} / ${list.length}`));
    row.title = `${confirmed} vahvistettua, ${count - confirmed} osittaista`;
    host.append(row);
  }
}

function renderReadiness() {
  const fallback = [
    { title: "195 maan tietorunko", detail: "Master-universumi ja puuttuvien havaintojen näkyvyys", state: "ready", label: "valmis" },
    { title: "Myynti-, vero- ja tullisarjojen peitto", detail: "Maakohtainen hankinta jatkuu", state: "partial", label: "osittainen" },
    { title: "Patenttien live-status maittain", detail: "Kansalliset rekisterit tarkistettava", state: "open", label: "avoin" },
    { title: "Riippumaton vakuusarvo", detail: "Markkina-atlas ei yksin ole arvonmääritys", state: "open", label: "avoin" }
  ];
  let items = Array.isArray(state.data?.readiness) ? state.data.readiness : null;
  if (!items && state.data?.readiness && typeof state.data.readiness === "object") {
    const ready = (state.data.readiness.completed || []).map((title) => ({ title, detail: "Rakenteellinen julkaisuedellytys", state: "ready", label: "valmis" }));
    const open = (state.data.readiness.blockers || []).map((title) => ({ title, detail: "Vaatii lisänäyttöä ennen lender-grade-johtopäätöstä", state: "open", label: "avoin" }));
    items = [...ready, ...open];
  }
  if (!items?.length) items = fallback;
  const host = byId("readiness-list");
  host.replaceChildren();
  for (const item of items) {
    const row = node("div", "readiness-item");
    const status = String(item.state || item.status || "partial").toLowerCase();
    row.dataset.state = status;
    const copy = node("div");
    copy.append(node("strong", "", item.title || item.label), node("small", "", item.detail || item.description || ""));
    row.append(node("span", "readiness-dot"), copy, node("span", "state-label", item.label || status));
    host.append(row);
  }
}

function populateRegions() {
  const select = byId("region-filter");
  const regions = [...new Set(countries().map((country) => country.region).filter(Boolean))].sort((a, b) => a.localeCompare(b, "fi"));
  for (const region of regions) {
    const option = node("option", "", region);
    option.value = region;
    select.append(option);
  }
}

function currentSummary(country) {
  const value = String(country.current || country.headline || "").trim();
  return value || "Ei vielä hyväksyttyä numeerista markkina-ankkuria.";
}

function filteredCountries() {
  const query = state.countryQuery.trim().toLocaleLowerCase("fi");
  return countries().filter((country) => {
    const names = [country.name, country.nameFi, country.iso2, country.iso3].filter(Boolean).join(" ").toLocaleLowerCase("fi");
    return (!query || names.includes(query)) && (!state.region || country.region === state.region) && (!state.grade || gradeOf(country) === state.grade);
  });
}

function renderCountries() {
  const list = filteredCountries();
  const body = byId("country-rows");
  body.replaceChildren();
  for (const country of list) {
    const row = node("tr");
    row.tabIndex = 0;
    row.setAttribute("aria-label", `Avaa ${country.nameFi || country.name} tiedot`);
    row.addEventListener("click", () => openCountry(country));
    row.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openCountry(country);
      }
    });

    const nameCell = node("td");
    const nameBox = node("div", "country-name");
    const nameCopy = node("span");
    nameCopy.append(node("strong", "", country.nameFi || country.name), node("small", "", country.name && country.name !== country.nameFi ? country.name : country.iso3 || ""));
    nameBox.append(node("span", "country-code", country.iso2 || "—"), nameCopy);
    nameCell.append(nameBox);

    const gradeCell = node("td");
    const gradeWrap = node("span", "table-grade");
    gradeWrap.append(gradeBadge(gradeOf(country)), node("span", "", gradeOf(country) === "D" ? "tutkimusjono" : "käytettävissä"));
    gradeCell.append(gradeWrap);

    const coverageCell = node("td");
    const coverage = coverageOf(country);
    const coverageWrap = node("span", "coverage-mini");
    const coverageTrack = node("span");
    const coverageFill = node("i");
    coverageFill.style.width = `${coverage}%`;
    coverageTrack.append(coverageFill);
    coverageWrap.append(coverageTrack, node("b", "", `${coverage}%`));
    coverageCell.append(coverageWrap);

    const actionCell = node("td");
    actionCell.append(node("button", "row-action", "→"));
    row.append(nameCell, node("td", "", country.region || "—"), gradeCell, coverageCell, node("td", "", currentSummary(country)), actionCell);
    body.append(row);
  }
  byId("country-count").textContent = `${list.length} / ${countries().length} maata`;
  byId("country-empty").hidden = list.length !== 0;
}

function openCountry(country) {
  byId("dialog-country-meta").textContent = `${country.iso2 || "—"} · ${country.region || "Alue puuttuu"} · evidenssi ${gradeOf(country)}`;
  byId("dialog-country-name").textContent = country.nameFi || country.name;
  const body = byId("dialog-country-body");
  body.replaceChildren();

  const summary = node("div", "dialog-summary");
  summary.append(gradeBadge(gradeOf(country)), node("p", "", currentSummary(country)));
  body.append(summary);

  const dimensionsSection = node("section", "dialog-section");
  dimensionsSection.append(node("h3", "", "Kattavuus mittareittain"));
  const dimensions = node("div", "dimension-grid");
  for (const [key, label] of Object.entries(DIMENSION_LABELS)) {
    const status = normalizeDimension(country.dimensions?.[key]);
    const item = node("div", "dimension");
    item.dataset.status = status;
    item.append(node("span", "", label), node("span", "", statusLabel(status)));
    dimensions.append(item);
  }
  dimensionsSection.append(dimensions);
  body.append(dimensionsSection);

  const missingSection = node("section", "dialog-section");
  missingSection.append(node("h3", "", "Keskeiset puutteet"), node("p", "", country.missing || "Täydellinen laite-, podi-, neste-, kotimaisen tuotannon ja laittoman markkinan sarja puuttuu."));
  body.append(missingSection);

  const route = country.nextStep || country.how || country.researchRoute;
  if (route) {
    const routeSection = node("section", "dialog-section");
    routeSection.append(node("h3", "", "Seuraava varmennusreitti"), node("p", "", route));
    body.append(routeSection);
  }

  const links = sourceLinksOf(country);
  const sourcesSection = node("section", "dialog-section");
  sourcesSection.append(node("h3", "", `Julkiset lähteet (${links.length})`));
  if (links.length) {
    const list = node("ul", "source-list");
    for (const item of links) {
      const link = node("a");
      link.href = safeExternalUrl(item.url);
      link.target = "_blank";
      link.rel = "noreferrer";
      link.append(node("span", "", item.label), node("small", "", new URL(item.url).hostname));
      const li = node("li");
      li.append(link);
      list.append(li);
    }
    sourcesSection.append(list);
  } else {
    sourcesSection.append(node("p", "", "Ei vielä maakohtaista hyväksyttyä lähdelinkkiä."));
  }
  body.append(sourcesSection);

  const dialog = byId("country-dialog");
  if (typeof dialog.showModal === "function") dialog.showModal();
}

function filteredEvidence() {
  const query = state.evidenceQuery.trim().toLocaleLowerCase("fi");
  return evidenceItems().filter((item) => {
    const haystack = [item.title, item.coverage, item.use, item.market, item.source].filter(Boolean).join(" ").toLocaleLowerCase("fi");
    const grade = String(item.grade || "").toUpperCase();
    return (!query || haystack.includes(query)) && (!state.evidenceGrade || grade === state.evidenceGrade);
  });
}

function renderEvidence() {
  const list = filteredEvidence();
  const host = byId("evidence-list");
  host.replaceChildren();
  for (const item of list) {
    const grade = ["A", "B", "C"].includes(String(item.grade).toUpperCase()) ? String(item.grade).toUpperCase() : "C";
    const card = node("article", "evidence-card");
    const top = node("div", "evidence-top");
    top.append(gradeBadge(grade));
    const url = safeExternalUrl(item.url || item.sourceUrl);
    top.append(node("span", "source-host", url ? new URL(url).hostname : "lähde puuttuu"));
    card.append(top, node("h3", "", item.title || "Nimetön lähde"), node("p", "", item.coverage || item.detail || ""), node("p", "evidence-use", item.use || item.limit || ""));
    if (url) {
      const link = node("a", "", "Avaa alkuperäinen lähde →");
      link.href = url;
      link.target = "_blank";
      link.rel = "noreferrer";
      card.append(link);
    }
    host.append(card);
  }
  byId("evidence-empty").hidden = list.length !== 0;
}

function renderLegal() {
  const timeline = Array.isArray(state.data?.legal?.timeline) ? state.data.legal.timeline : Array.isArray(state.data?.legal) ? state.data.legal : [];
  const host = byId("legal-timeline");
  host.replaceChildren();
  for (const item of timeline) {
    const li = node("li");
    li.append(
      node("time", "", item.date || item.eventDate || item.period || "—"),
      node("strong", "", item.title || item.event || item.reference || item.authority || ""),
      node("p", "", item.detail || item.description || item.statement || "")
    );
    const url = safeExternalUrl(item.url || item.sourceUrl);
    if (url) {
      const link = node("a", "", "Virallinen lähde →");
      link.href = url;
      link.target = "_blank";
      link.rel = "noreferrer";
      li.append(link);
    }
    host.append(li);
  }
  if (!timeline.length) host.append(node("li", "", "Prosessitietoa ei voitu ladata."));

  const gates = Array.isArray(state.data?.legal?.gates) ? state.data.legal.gates : [
    { label: "Saksan mitättömyysasia", status: "valitus vireillä" },
    { label: "Loukkaustuomio", status: "vahvistettu" },
    { label: "Euromääräinen korvaus", status: "ei julkinen" },
    { label: "Toteutunut kassavirta", status: "ei vahvistettu" }
  ];
  const gatesHost = byId("legal-gates");
  gatesHost.replaceChildren();
  for (const gate of gates) {
    const row = node("div", "legal-gate");
    row.append(node("span", "", gate.label || gate.title), node("span", "", gate.status || gate.state));
    gatesHost.append(row);
  }
}

function renderMethod() {
  const methods = Array.isArray(state.data?.methodology?.steps) ? state.data.methodology.steps : Array.isArray(state.data?.methodology) ? state.data.methodology : FALLBACK_METHODS;
  const host = byId("method-cards");
  host.replaceChildren();
  methods.slice(0, 8).forEach((item, index) => {
    const card = node("article", "method-card");
    card.append(node("span", "", String(index + 1).padStart(2, "0")), node("h3", "", item.title || item.name), node("p", "", item.text || item.description));
    host.append(card);
  });
  const rules = Array.isArray(state.data?.methodology?.validationRules) ? state.data.methodology.validationRules : FALLBACK_RULES;
  const rulesHost = byId("validation-rules");
  rulesHost.replaceChildren(...rules.map((item) => node("li", "", typeof item === "string" ? item : item.text || item.description)));
}

function renderSubmission() {
  const submission = state.data?.submission || {};
  const dropbox = safeExternalUrl(submission.dropbox || submission.dropboxUrl || submission.dropboxRequestUrl);
  const whatsapp = submission.whatsapp || submission.whatsappUrl;
  const email = submission.email || submission.emailUrl;
  if (dropbox) byId("dropbox-link").href = dropbox;
  const whatsappUrl = /^https:\/\/wa\.me\//.test(whatsapp || "") ? whatsapp : submission.whatsappUrl;
  if (whatsappUrl) byId("whatsapp-link").href = `${whatsappUrl}?text=${encodeURIComponent("Hei Jouni, minulla on uutta lähdeaineistoa Pixanin markkina-analyysiin.")}`;
  const emailUrl = /^mailto:/.test(email || "") ? email : email ? `mailto:${email}` : null;
  if (emailUrl) byId("email-link").href = `${emailUrl}${emailUrl.includes("?") ? "&" : "?"}subject=${encodeURIComponent("Pixan-markkina-analyysi – uusi lähdeaineisto")}`;
}

function createCoverNote(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const status = byId("cover-note-status");
  if (!form.reportValidity()) {
    status.textContent = "Täytä tähdellä merkityt kentät ja vahvista toimitusoikeus.";
    return;
  }
  const values = Object.fromEntries(new FormData(form).entries());
  const lines = [
    "PIXAN GLOBAL MARKET EVIDENCE – AINEISTON SAATE",
    "",
    `Luotu: ${new Date().toISOString()}`,
    `Maa tai alue: ${values.country}`,
    `Ajanjakso: ${values.period}`,
    `Julkaisija: ${values.publisher}`,
    `Lähde-URL: ${values.sourceUrl || "ei ilmoitettu"}`,
    `Mittarityyppi: ${values.measure}`,
    `Lähettäjä / organisaatio: ${values.sender || "ei ilmoitettu"}`,
    "",
    "KUVAUS, TODISTUSARVO JA RAJAT",
    values.description,
    "",
    "TOIMITUSOIKEUS",
    "Lähettäjä on vahvistanut, että aineiston saa toimittaa tarkistettavaksi.",
    "Aineistoa ei hyväksytä eikä julkaista automaattisesti.",
    "",
    "Lisää tämä TXT-tiedosto samaan Dropbox-lähetykseen alkuperäisten tiedostojen kanssa."
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
  const link = document.createElement("a");
  const slug = String(values.country).normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-zA-Z0-9]+/g, "-").replace(/^-|-$/g, "").toUpperCase() || "AINEISTO";
  link.href = URL.createObjectURL(blob);
  link.download = `PIXAN_AINEISTON_SAATE_${slug}.txt`;
  link.click();
  URL.revokeObjectURL(link.href);
  status.textContent = "Saate ladattu. Lisää se tiedostojen kanssa Dropbox-lähetykseen.";
}

function setTab(tab, options = {}) {
  const allowed = new Set(["overview", "countries", "evidence", "legal", "method", "submit"]);
  state.tab = allowed.has(tab) ? tab : "overview";
  document.querySelectorAll("[data-panel]").forEach((panel) => { panel.hidden = panel.dataset.panel !== state.tab; });
  document.querySelectorAll("[data-tab]").forEach((link) => link.setAttribute("aria-selected", String(link.dataset.tab === state.tab)));
  if (options.updateHash !== false) history.replaceState(null, "", `#${state.tab}`);
  if (options.scroll) byId(`panel-${state.tab}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function bindEvents() {
  document.querySelectorAll("[data-tab]").forEach((link) => link.addEventListener("click", (event) => {
    event.preventDefault();
    setTab(link.dataset.tab, { scroll: true });
  }));
  document.querySelectorAll('a[href="#countries"], a[href="#submit"]').forEach((link) => link.addEventListener("click", (event) => {
    event.preventDefault();
    setTab(link.getAttribute("href").slice(1), { scroll: true });
  }));
  byId("country-search").addEventListener("input", (event) => { state.countryQuery = event.target.value; renderCountries(); });
  byId("region-filter").addEventListener("change", (event) => { state.region = event.target.value; renderCountries(); });
  byId("grade-filter").addEventListener("change", (event) => { state.grade = event.target.value; renderCountries(); });
  byId("evidence-search").addEventListener("input", (event) => { state.evidenceQuery = event.target.value; renderEvidence(); });
  byId("evidence-grade-filter").addEventListener("change", (event) => { state.evidenceGrade = event.target.value; renderEvidence(); });
  byId("cover-note-form").addEventListener("submit", createCoverNote);
  byId("country-dialog").querySelector(".dialog-close").addEventListener("click", () => byId("country-dialog").close());
  byId("country-dialog").addEventListener("click", (event) => {
    if (event.target === byId("country-dialog")) byId("country-dialog").close();
  });
  window.addEventListener("hashchange", () => setTab(location.hash.slice(1), { updateHash: false }));
}

function renderMeta() {
  const snapshot = valueAt(state.data, ["meta.generatedAt", "meta.snapshotDate", "meta.updatedAt"], "");
  const sourceCommit = valueAt(state.data, ["meta.sourceCommit", "meta.legacySourceCommit", "sourceAttribution.commit"], "—");
  byId("snapshot-date").textContent = formatDate(snapshot);
  byId("snapshot-date").dateTime = snapshot;
  byId("source-commit").textContent = String(sourceCommit).slice(0, 9);
}

async function loadData() {
  const response = await fetch("data/atlas.json", { cache: "no-store" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();
  if (!Array.isArray(data.countries) || data.countries.length !== 195) throw new Error("Country universe validation failed");
  state.data = data;
}

async function init() {
  bindEvents();
  try {
    await loadData();
    renderMeta();
    renderMetrics();
    renderCoverageBars();
    renderReadiness();
    populateRegions();
    renderCountries();
    renderEvidence();
    renderLegal();
    renderMethod();
    renderSubmission();
    setTab(location.hash.slice(1) || "overview", { updateHash: false });
  } catch (error) {
    console.error(error);
    byId("load-error").hidden = false;
  }
}

init();
