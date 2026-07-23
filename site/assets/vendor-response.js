"use strict";

(() => {
  const root = document.querySelector("[data-vendor-response]");
  if (!root) return;

  const EXPECTED_STATES = new Map([
    ["ecig-global-market-database", ["request_sent", "pending"]],
    ["euromonitor-passport-nicotine", ["request_sent", "pending"]],
    ["niq-rms-pilot", ["not_submitted_terms_gate", "not_submitted"]],
    ["circana-us-tobacco-pilot", ["submission_confirmed", "pending"]]
  ]);
  const EXPECTED_CRITERIA = new Map([
    ["annualCountrySeriesFit", 0.20],
    ["metricScopeClarity", 0.15],
    ["coverage", 0.15],
    ["methodTransparency", 0.15],
    ["auditability", 0.10],
    ["transactionLicenceFit", 0.15],
    ["commercialClarity", 0.10]
  ]);
  const EXPECTED_EVIDENCE = new Set([
    "sample",
    "methodology",
    "coverageMatrix",
    "quote",
    "officialAnchorReconciliation",
    "transactionUseRights",
    "totalCostTerms"
  ]);
  const MANDATORY_EVIDENCE = new Set([
    "sample",
    "methodology",
    "coverageMatrix",
    "officialAnchorReconciliation",
    "transactionUseRights",
    "totalCostTerms"
  ]);
  let control = null;

  function isFi() {
    return window.SiteI18n?.isFinnish?.() ?? document.documentElement.lang === "fi";
  }

  function l(fi, en) {
    return window.SiteI18n?.pick?.(fi, en) ?? (isFi() ? fi : en);
  }

  function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function validDate(value) {
    if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
    const [year, month, day] = value.split("-").map(Number);
    const parsed = new Date(Date.UTC(year, month - 1, day));
    return parsed.getUTCFullYear() === year
      && parsed.getUTCMonth() === month - 1
      && parsed.getUTCDate() === day;
  }

  function objectKeysEqual(value, expected) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return false;
    const keys = Object.keys(value);
    return keys.length === expected.size && keys.every((key) => expected.has(key));
  }

  function validate(raw) {
    if (!raw || raw.schemaVersion !== 1
      || raw.controlId !== "vendor-response-control-public"
      || raw.status !== "public_status_only_no_purchase_authorised"
      || raw.version !== "2026.07.23-13"
      || !validDate(raw.asOf)
      || raw.scoreScale?.minimum !== 0
      || raw.scoreScale?.maximum !== 5
      || raw.scoreScale?.missingValue !== "not_scored") {
      throw new Error("unsupported vendor-response control");
    }
    if (!Array.isArray(raw.criteria) || raw.criteria.length !== EXPECTED_CRITERIA.size
      || Math.abs(raw.criteria.reduce((sum, criterion) => sum + Number(criterion.weight), 0) - 1) > 1e-9) {
      throw new Error("invalid vendor-response criteria");
    }
    const criterionIds = new Set();
    for (const criterion of raw.criteria) {
      if (!EXPECTED_CRITERIA.has(criterion.id)
        || criterionIds.has(criterion.id)
        || Math.abs(Number(criterion.weight) - EXPECTED_CRITERIA.get(criterion.id)) > 1e-9
        || typeof criterion.labelEn !== "string" || !criterion.labelEn.trim()
        || typeof criterion.labelFi !== "string" || !criterion.labelFi.trim()
        || typeof criterion.descriptionEn !== "string" || !criterion.descriptionEn.trim()
        || typeof criterion.descriptionFi !== "string" || !criterion.descriptionFi.trim()) {
        throw new Error("invalid vendor-response criterion");
      }
      criterionIds.add(criterion.id);
    }
    if (!Array.isArray(raw.evidenceTypes) || raw.evidenceTypes.length !== EXPECTED_EVIDENCE.size
      || new Set(raw.evidenceTypes.map((item) => item.key)).size !== EXPECTED_EVIDENCE.size
      || raw.evidenceTypes.some((item) => !EXPECTED_EVIDENCE.has(item.key))) {
      throw new Error("invalid vendor evidence types");
    }
    if (!Array.isArray(raw.mandatoryGates) || raw.mandatoryGates.length !== MANDATORY_EVIDENCE.size
      || new Set(raw.mandatoryGates.map((gate) => gate.evidenceKey)).size !== MANDATORY_EVIDENCE.size
      || raw.mandatoryGates.some((gate) =>
        gate.id !== gate.evidenceKey || !MANDATORY_EVIDENCE.has(gate.evidenceKey))) {
      throw new Error("invalid mandatory evidence gates");
    }
    if (!Array.isArray(raw.vendors) || raw.vendors.length !== EXPECTED_STATES.size) {
      throw new Error("expected four vendor records");
    }
    const vendorIds = new Set();
    for (const vendor of raw.vendors) {
      const expected = EXPECTED_STATES.get(vendor.vendorId);
      if (!expected || vendorIds.has(vendor.vendorId)
        || vendor.requestState !== expected[0] || vendor.responseState !== expected[1]
        || typeof vendor.vendor !== "string" || !vendor.vendor.trim()
        || typeof vendor.product !== "string" || !vendor.product.trim()
        || !objectKeysEqual(vendor.receivedEvidence, EXPECTED_EVIDENCE)
        || Object.values(vendor.receivedEvidence).some((value) => value !== false)
        || !objectKeysEqual(vendor.criterionScores, new Set(EXPECTED_CRITERIA.keys()))
        || Object.values(vendor.criterionScores).some((value) => value !== null)
        || vendor.scoringState !== "not_scored"
        || vendor.weightedScore !== null
        || vendor.purchaseAuthorised !== false
        || vendor.evidenceReceivedCount !== 0
        || vendor.mandatoryGatePassCount !== 0) {
        throw new Error("vendor record differs from the reviewed public state");
      }
      vendorIds.add(vendor.vendorId);
    }
    if (!raw.summary
      || raw.summary.trackedVendors !== 4
      || raw.summary.substantiveResponses !== 0
      || raw.summary.scoredVendors !== 0
      || raw.summary.purchaseAuthorisations !== 0) {
      throw new Error("vendor-response summary differs");
    }
    return raw;
  }

  function setStaticText() {
    const values = {
      "[data-vendor-response-kicker]": l(
        "Toimittajaevidenssin vastaanotto · julkinen tilanne",
        "Vendor evidence intake · public status"
      ),
      "[data-vendor-response-title]": l(
        "Toimittajavastausten valvonta",
        "Vendor response control"
      ),
      "[data-vendor-response-intro]": l(
        "Näkymä erottaa yhteydenottotilan vastaanotetusta evidenssistä ja pisteytyksestä, jotta puuttuva vastaus ei näytä heikolta tulokselta.",
        "This view separates outreach status from received evidence and scoring so a missing response never looks like a poor result."
      ),
      "[data-vendor-response-boundary-title]": l(
        "Yhtään sisällöllistä toimittajavastausta ei ole vielä vastaanotettu",
        "No substantive vendor response has been received"
      ),
      "[data-vendor-response-boundary-copy]": l(
        "Julkinen näkymä ei sisällä viestejä, henkilötietoja, toimittajatiedostoja, lisensoimatonta dataa tai luottamuksellisia ehtoja. Osto-, tilaus-, NDA- tai automaattisen uusinnan valtuutusta ei ole.",
        "The public view contains no messages, personal data, vendor files, unlicensed data or confidential terms. No purchase, subscription, NDA or auto-renewal is authorised."
      ),
      "[data-vendor-response-criteria-kicker]": l(
        "Läpinäkyvä arviointimalli",
        "Transparent evaluation model"
      ),
      "[data-vendor-response-criteria-title]": l(
        "Seitsemän pisteytyskriteeriä ja kuusi pakollista porttia",
        "Seven scoring criteria and six mandatory gates"
      ),
      "[data-vendor-response-criteria-copy]": l(
        "Pistemäärä syntyy vasta, kun kaikki pakollinen evidenssi on olemassa. Puuttuva tieto on EI PISTEYTETTY, ei 0/5.",
        "A score exists only after all mandatory evidence is present. Missing information is NOT SCORED, not 0/5."
      ),
      "[data-vendor-response-download-workbook]": l(
        "Lataa päätöstyökirja XLSX",
        "Download decision workbook XLSX"
      ),
      "[data-vendor-response-download-csv]": l(
        "Lataa julkinen tilanne CSV",
        "Download public status CSV"
      ),
      "[data-vendor-response-download-json]": l(
        "Lataa lähde JSON",
        "Download source JSON"
      ),
      "[data-vendor-response-note]": l(
        "Tila osoittaa vain tämän julkisen tarkistuspisteen. Se ei todista viestin toimitusta, toimittajan kiinnostusta, datan laatua tai ostokelpoisuutta.",
        "Status reflects only this public checkpoint. It does not establish message delivery, vendor interest, data quality or purchase readiness."
      )
    };
    for (const [selector, value] of Object.entries(values)) {
      const element = root.querySelector(selector);
      if (element) element.textContent = value;
    }
    const boundary = root.querySelector("[data-vendor-response-boundary]");
    if (boundary) {
      boundary.setAttribute(
        "aria-label",
        l("Toimittajavastausten julkinen rajaus", "Public vendor-response boundary")
      );
    }
  }

  function summaryCard(value, labelFi, labelEn, detailFi, detailEn, tone) {
    const card = node("article", `vendor-response-summary-card vendor-response-summary-${tone}`);
    card.append(
      node("strong", "", String(value)),
      node("span", "", l(labelFi, labelEn)),
      node("small", "", l(detailFi, detailEn))
    );
    return card;
  }

  function renderSummary() {
    const summary = root.querySelector("[data-vendor-response-summary]");
    summary.replaceChildren(
      summaryCard(
        control.summary.trackedVendors,
        "seurattua toimittajaa",
        "vendors tracked",
        "julkinen tilarekisteri",
        "public status register",
        "neutral"
      ),
      summaryCard(
        control.summary.substantiveResponses,
        "sisällöllistä vastausta",
        "substantive responses",
        "ei vielä arvioitavaa aineistoa",
        "no evidence to evaluate yet",
        "pending"
      ),
      summaryCard(
        control.summary.scoredVendors,
        "pisteytettyä toimittajanäytettä",
        "vendor samples scored",
        "puuttuva ei ole nolla",
        "missing is not zero",
        "pending"
      ),
      summaryCard(
        control.summary.purchaseAuthorisations,
        "ostovaltuutusta",
        "purchase authorisations",
        "kaikki hankinnat portilla",
        "all procurement remains gated",
        "stop"
      )
    );
    summary.hidden = false;
  }

  function renderEvidenceItem(item, received, mandatory) {
    const element = node(
      "li",
      `vendor-response-evidence-item ${received ? "is-received" : "is-missing"}`
    );
    const mark = node("span", "vendor-response-evidence-mark", received ? "✓" : "—");
    mark.setAttribute("aria-hidden", "true");
    const label = node("span", "", isFi() ? item.labelFi : item.labelEn);
    if (mandatory) {
      label.append(node("small", "", l("pakollinen", "mandatory")));
    }
    const state = node(
      "strong",
      "",
      received ? l("Vastaanotettu", "Received") : l("Puuttuu", "Missing")
    );
    element.append(mark, label, state);
    return element;
  }

  function renderVendor(vendor) {
    const card = node("article", "vendor-response-card");
    card.dataset.vendorState = vendor.requestState;
    const header = node("div", "vendor-response-card-head");
    const name = node("div", "");
    name.append(node("h3", "", vendor.vendor), node("p", "", vendor.product));
    const status = node(
      "span",
      `vendor-response-state vendor-response-state-${vendor.requestState}`,
      isFi() ? vendor.publicStatusFi : vendor.publicStatusEn
    );
    header.append(name, status);

    const score = node("div", "vendor-response-score");
    const scoreCopy = node("div", "");
    scoreCopy.append(
      node("span", "", l("Arviointitila", "Evaluation state")),
      node("strong", "", l("EI PISTEYTETTY", "NOT SCORED"))
    );
    const progress = node("div", "vendor-response-progress");
    progress.append(
      node("span", "", l("Evidenssi", "Evidence")),
      node("strong", "", `${vendor.evidenceReceivedCount}/${control.evidenceTypes.length}`)
    );
    score.append(scoreCopy, progress);

    const evidence = node("ul", "vendor-response-evidence");
    for (const item of control.evidenceTypes) {
      evidence.append(
        renderEvidenceItem(
          item,
          vendor.receivedEvidence[item.key],
          MANDATORY_EVIDENCE.has(item.key)
        )
      );
    }
    card.append(header, score, evidence);
    return card;
  }

  function renderVendors() {
    const container = root.querySelector("[data-vendor-response-vendors]");
    container.replaceChildren(...control.vendors.map(renderVendor));
    container.hidden = false;
  }

  function renderCriteria() {
    const criteria = root.querySelector("[data-vendor-response-criteria]");
    criteria.replaceChildren(...control.criteria.map((criterion, index) => {
      const item = node("article", "vendor-response-criterion");
      const heading = node("div", "vendor-response-criterion-heading");
      heading.append(
        node("span", "vendor-response-criterion-number", String(index + 1).padStart(2, "0")),
        node("h4", "", isFi() ? criterion.labelFi : criterion.labelEn),
        node("strong", "", `${Math.round(criterion.weight * 100)}%`)
      );
      item.append(
        heading,
        node("p", "", isFi() ? criterion.descriptionFi : criterion.descriptionEn)
      );
      return item;
    }));
    criteria.hidden = false;

    const gates = root.querySelector("[data-vendor-response-gates]");
    gates.replaceChildren(...control.mandatoryGates.map((gate) => {
      const item = node("li", "vendor-response-gate");
      item.append(
        node("span", "vendor-response-gate-mark", "GATE"),
        node("strong", "", isFi() ? gate.labelFi : gate.labelEn),
        node("p", "", isFi() ? gate.descriptionFi : gate.descriptionEn)
      );
      return item;
    }));
    gates.hidden = false;
  }

  function renderReady() {
    setStaticText();
    renderSummary();
    renderVendors();
    renderCriteria();
    root.querySelector("[data-vendor-response-actions]").hidden = false;
    root.querySelector("[data-vendor-response-note]").hidden = false;
    const meta = root.querySelector("[data-vendor-response-meta]");
    meta.textContent = `${control.version} · ${control.asOf}`;
    const status = root.querySelector("[data-vendor-response-status]");
    status.className = "bank-package-status bank-package-status-ready";
    status.replaceChildren(
      node("span", "bank-package-status-dot", ""),
      node("span", "", l(
        "4 toimittajaa seurannassa · 0 sisällöllistä vastausta · 0 pisteytettyä toimittajanäytettä · 0 ostovaltuutusta.",
        "4 vendors tracked · 0 substantive responses · 0 vendor samples scored · 0 purchase authorisations."
      ))
    );
    status.firstElementChild.setAttribute("aria-hidden", "true");
    root.setAttribute("aria-busy", "false");
  }

  function renderFailure() {
    setStaticText();
    for (const selector of [
      "[data-vendor-response-summary]",
      "[data-vendor-response-vendors]",
      "[data-vendor-response-criteria]",
      "[data-vendor-response-gates]",
      "[data-vendor-response-actions]",
      "[data-vendor-response-note]"
    ]) {
      const element = root.querySelector(selector);
      if (element) element.hidden = true;
    }
    const status = root.querySelector("[data-vendor-response-status]");
    status.className = "bank-package-status bank-package-status-error";
    status.replaceChildren(
      node("span", "bank-package-status-dot", ""),
      node("strong", "", l(
        "Toimittajavastausten julkista tilannetta ei voitu ladata.",
        "The public vendor-response control could not be loaded."
      ))
    );
    status.firstElementChild.setAttribute("aria-hidden", "true");
    root.setAttribute("aria-busy", "false");
  }

  async function init() {
    try {
      const response = await fetch("data/vendor-response-control.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      control = validate(await response.json());
      renderReady();
    } catch (error) {
      console.warn("Vendor-response control unavailable", error);
      renderFailure();
    }
  }

  document.addEventListener("pixan:languagechange", () => {
    if (control) renderReady();
    else setStaticText();
  });
  setStaticText();
  init();
})();
