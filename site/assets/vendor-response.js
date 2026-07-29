"use strict";

(() => {
  const root = document.querySelector("[data-vendor-response]");
  if (!root) return;

  const EXPECTED_STATES = new Map([
    ["ecig-global-market-database", ["request_sent", "pending_no_acknowledgement"]],
    ["euromonitor-passport-nicotine", ["request_sent", "substantive_response_received"]],
    ["niq-rms-pilot", ["not_submitted_terms_gate", "not_submitted"]],
    ["circana-us-tobacco-pilot", ["submission_confirmed", "commercial_qualification_response_received"]]
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
  const EXPECTED_GATE_CODES = new Map([
    ["G1", "sample"],
    ["G2", "methodology"],
    ["G3", "coverageMatrix"],
    ["G4", "officialAnchorReconciliation"],
    ["G5", "transactionUseRights"],
    ["G6", "totalCostTerms"]
  ]);
  const VALID_GATE_STATUSES = new Set(["pass", "fail", "not_testable", "missing"]);
  const EXPECTED_GATE_STATUSES = new Map([
    ["ecig-global-market-database", ["missing", "missing", "missing", "missing", "missing", "missing"]],
    ["euromonitor-passport-nicotine", ["not_testable", "fail", "fail", "not_testable", "fail", "fail"]],
    ["niq-rms-pilot", ["missing", "missing", "missing", "missing", "missing", "missing"]],
    ["circana-us-tobacco-pilot", ["missing", "missing", "missing", "missing", "missing", "missing"]]
  ]);
  const EXPECTED_QUOTE_RECEIVED = new Map([
    ["ecig-global-market-database", false],
    ["euromonitor-passport-nicotine", true],
    ["niq-rms-pilot", false],
    ["circana-us-tobacco-pilot", false]
  ]);
  const EXPECTED_RECEIPTS = new Map([
    ["ecig-global-market-database", {
      sample: false,
      methodology: false,
      coverageMatrix: false,
      quote: false,
      officialAnchorReconciliation: false,
      transactionUseRights: false,
      totalCostTerms: false
    }],
    ["euromonitor-passport-nicotine", {
      sample: true,
      methodology: true,
      coverageMatrix: true,
      quote: true,
      officialAnchorReconciliation: false,
      transactionUseRights: true,
      totalCostTerms: true
    }],
    ["niq-rms-pilot", {
      sample: false,
      methodology: false,
      coverageMatrix: false,
      quote: false,
      officialAnchorReconciliation: false,
      transactionUseRights: false,
      totalCostTerms: false
    }],
    ["circana-us-tobacco-pilot", {
      sample: false,
      methodology: false,
      coverageMatrix: false,
      quote: false,
      officialAnchorReconciliation: false,
      transactionUseRights: false,
      totalCostTerms: false
    }]
  ]);
  const EXPECTED_GERMANY_ANCHORS = new Map([
    [2023, ["DE-2023-TAXED-LIQUID-VOLUME-L", 1241000, "final", "pass_test"]],
    [2024, ["DE-2024-TAXED-LIQUID-VOLUME-L", 1284000, "final", "pass_test"]],
    [2025, ["DE-2025-TAXED-LIQUID-VOLUME-L", 1518000, "provisional", "context_only"]]
  ]);
  const EXPECTED_GERMANY_REQUIREMENTS = new Set([
    "productSplits",
    "definitions",
    "taxBasis",
    "methodology",
    "brandFields",
    "transactionUseRights",
    "commercialTerms"
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

  function validateGermanyBenchmark(benchmark) {
    if (!benchmark
      || benchmark.benchmarkId !== "de-taxed-e-liquid-volume-vendor-gate"
      || benchmark.countryIso2 !== "DE"
      || benchmark.unit !== "litre"
      || benchmark.status !== "not_testable"
      || benchmark.vendorPassDoesNotEstablishDonorPass !== true
      || benchmark.donorGateEffect !== "none"
      || typeof benchmark.scopeEn !== "string" || !benchmark.scopeEn.trim()
      || typeof benchmark.scopeFi !== "string" || !benchmark.scopeFi.trim()
      || typeof benchmark.statusReasonEn !== "string" || !benchmark.statusReasonEn.trim()
      || typeof benchmark.statusReasonFi !== "string" || !benchmark.statusReasonFi.trim()
      || typeof benchmark.donorBoundaryEn !== "string" || !benchmark.donorBoundaryEn.includes("0/3")
      || typeof benchmark.donorBoundaryFi !== "string" || !benchmark.donorBoundaryFi.includes("0/3")) {
      throw new Error("invalid Germany benchmark boundary");
    }
    if (!Array.isArray(benchmark.officialAnchors)
      || benchmark.officialAnchors.length !== EXPECTED_GERMANY_ANCHORS.size) {
      throw new Error("invalid Germany official anchors");
    }
    const anchorYears = new Set();
    for (const anchor of benchmark.officialAnchors) {
      const expected = EXPECTED_GERMANY_ANCHORS.get(anchor.year);
      if (!expected || anchorYears.has(anchor.year)
        || anchor.observationId !== expected[0]
        || anchor.sourceId !== "DE-DESTATIS-73411-0003"
        || anchor.value !== expected[1]
        || anchor.unit !== "litre"
        || anchor.finality !== expected[2]
        || anchor.role !== expected[3]) {
        throw new Error("Germany official anchor differs");
      }
      anchorYears.add(anchor.year);
    }
    const annual = benchmark.thresholds?.annualDeviation;
    const cumulative = benchmark.thresholds?.twoYearCumulativeDeviation;
    if (annual?.maximumPct !== 15
      || JSON.stringify(annual?.years) !== "[2023,2024]"
      || typeof annual?.formulaEn !== "string" || !annual.formulaEn.trim()
      || typeof annual?.formulaFi !== "string" || !annual.formulaFi.trim()
      || cumulative?.maximumPct !== 10
      || JSON.stringify(cumulative?.years) !== "[2023,2024]"
      || typeof cumulative?.formulaEn !== "string" || !cumulative.formulaEn.trim()
      || typeof cumulative?.formulaFi !== "string" || !cumulative.formulaFi.trim()) {
      throw new Error("Germany benchmark thresholds differ");
    }
    if (!Array.isArray(benchmark.requiredEvidence)
      || benchmark.requiredEvidence.length !== EXPECTED_GERMANY_REQUIREMENTS.size
      || new Set(benchmark.requiredEvidence.map((item) => item.id)).size
        !== EXPECTED_GERMANY_REQUIREMENTS.size
      || benchmark.requiredEvidence.some((item) =>
        !EXPECTED_GERMANY_REQUIREMENTS.has(item.id)
        || typeof item.labelEn !== "string" || !item.labelEn.trim()
        || typeof item.labelFi !== "string" || !item.labelFi.trim()
        || typeof item.descriptionEn !== "string" || !item.descriptionEn.trim()
        || typeof item.descriptionFi !== "string" || !item.descriptionFi.trim())) {
      throw new Error("Germany benchmark required evidence differs");
    }
  }

  function validate(raw) {
    if (!raw || raw.schemaVersion !== 2
      || raw.controlId !== "vendor-response-control-public"
      || raw.status !== "public_status_only_no_purchase_authorised"
      || typeof raw.version !== "string"
      || !/^2026\.\d{2}\.\d{2}-\d+$/.test(raw.version)
      || !validDate(raw.asOf)
      || raw.scoreScale?.minimum !== 0
      || raw.scoreScale?.maximum !== 5
      || raw.scoreScale?.missingValue !== "not_scored") {
      throw new Error("unsupported vendor-response control");
    }
    validateGermanyBenchmark(raw.germanyBenchmark);
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
    if (!Array.isArray(raw.mandatoryGates) || raw.mandatoryGates.length !== EXPECTED_GATE_CODES.size
      || new Set(raw.mandatoryGates.map((gate) => gate.evidenceKey)).size !== MANDATORY_EVIDENCE.size
      || new Set(raw.mandatoryGates.map((gate) => gate.gateCode)).size !== EXPECTED_GATE_CODES.size
      || raw.mandatoryGates.some((gate) =>
        gate.id !== gate.evidenceKey
        || EXPECTED_GATE_CODES.get(gate.gateCode) !== gate.evidenceKey
        || typeof gate.labelEn !== "string" || !gate.labelEn.trim()
        || typeof gate.labelFi !== "string" || !gate.labelFi.trim()
        || typeof gate.descriptionEn !== "string" || !gate.descriptionEn.trim()
        || typeof gate.descriptionFi !== "string" || !gate.descriptionFi.trim())) {
      throw new Error("invalid mandatory evidence gates");
    }
    if (!Array.isArray(raw.vendors) || raw.vendors.length !== EXPECTED_STATES.size) {
      throw new Error("expected four vendor records");
    }
    const vendorIds = new Set();
    for (const vendor of raw.vendors) {
      const expected = EXPECTED_STATES.get(vendor.vendorId);
      const expectedGateStatuses = EXPECTED_GATE_STATUSES.get(vendor.vendorId);
      const expectedQuoteReceived = EXPECTED_QUOTE_RECEIVED.get(vendor.vendorId);
      const expectedReceipts = EXPECTED_RECEIPTS.get(vendor.vendorId);
      const gateCodes = [...EXPECTED_GATE_CODES.keys()];
      if (!expected || vendorIds.has(vendor.vendorId)
        || vendor.requestState !== expected[0] || vendor.responseState !== expected[1]
        || typeof vendor.vendor !== "string" || !vendor.vendor.trim()
        || typeof vendor.product !== "string" || !vendor.product.trim()
        || typeof vendor.publicStatusEn !== "string" || !vendor.publicStatusEn.trim()
        || typeof vendor.publicStatusFi !== "string" || !vendor.publicStatusFi.trim()
        || vendor.quoteReceived !== expectedQuoteReceived
        || !objectKeysEqual(vendor.gateResults, new Set(gateCodes))
        || !expectedGateStatuses
        || gateCodes.some((gateCode, index) => {
          const result = vendor.gateResults[gateCode];
          return !result
            || !VALID_GATE_STATUSES.has(result.status)
            || result.status !== expectedGateStatuses[index]
            || !Array.isArray(result.reasonCodes)
            || result.reasonCodes.length === 0
            || result.reasonCodes.some((reason) =>
              typeof reason !== "string" || !/^[A-Z0-9_]+$/.test(reason));
        })
        || !objectKeysEqual(vendor.receivedEvidence, EXPECTED_EVIDENCE)
        || !expectedReceipts
        || vendor.receivedEvidence.quote !== vendor.quoteReceived
        || [...EXPECTED_EVIDENCE].some((key) =>
          typeof vendor.receivedEvidence[key] !== "boolean"
          || vendor.receivedEvidence[key] !== expectedReceipts[key])
        || raw.mandatoryGates.some((gate) =>
          vendor.gateResults[gate.gateCode].status === "pass"
            && vendor.receivedEvidence[gate.evidenceKey] !== true)
        || !objectKeysEqual(vendor.criterionScores, new Set(EXPECTED_CRITERIA.keys()))
        || Object.values(vendor.criterionScores).some((value) => value !== null)
        || vendor.scoringState !== "not_scored"
        || vendor.weightedScore !== null
        || vendor.purchaseAuthorised !== false
        || vendor.evidenceReceivedCount
          !== Object.values(vendor.receivedEvidence).filter((value) => value === true).length
        || vendor.evaluatedGateCount
          !== gateCodes.filter((gateCode) => vendor.gateResults[gateCode].status !== "missing").length
        || vendor.mandatoryGatePassCount
          !== gateCodes.filter((gateCode) => vendor.gateResults[gateCode].status === "pass").length) {
        throw new Error("vendor record differs from the reviewed public state");
      }
      vendorIds.add(vendor.vendorId);
    }
    if (!raw.summary
      || raw.summary.trackedVendors !== 4
      || raw.summary.substantiveResponses !== 1
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
        "Ehdollinen maksullinen Saksa-ote tarjottu · ei hyväksytty · 0/6 pakollista porttia läpäisty",
        "Conditional paid Germany extract offered · not accepted · 0/6 mandatory gates passed"
      ),
      "[data-vendor-response-boundary-copy]": l(
        "Osittainen työkirja osoittaa arviointikenttien olemassaolon, mutta se ei ole edustava näyte eikä mahdollista Saksan viranomaisankkuritestiä. Yleinen menetelmä ja kaksi suuntaa-antavaa vuosipakettitarjousta on saatu, mutta täsmällinen peitto, täydelliset kaupalliset ehdot ja kirjalliset transaktiokäyttöoikeudet puuttuvat. Julkisessa näkymässä ei näytetä täsmällisiä hintoja, lisensoituja arvoja tai toimittajaliitteitä. EI PISTEYTETTY; ostoa, tilausta, maksua, NDA:ta tai automaattista uusintaa ei ole valtuutettu.",
        "The expanded sample and 78-market list materially improve the review, but current fields, the exact country-product-year-measure matrix, the official tax/stage/scope bridge, complete commercial terms and written transaction-use rights remain unresolved. This public view discloses no exact prices, licensed values or vendor attachments. All 6 gates are evaluated; 0 pass. NOT SCORED; no purchase, subscription, fee, NDA or auto-renewal is authorised."
      ),
      "[data-vendor-response-germany-kicker]": l(
        "Saksa · toimittajanäytteen kontrollimarkkina",
        "Germany · vendor-sample control market"
      ),
      "[data-vendor-response-germany-title]": l(
        "Virallinen määräankkuri ja ennalta määrätty läpäisyraja",
        "Official volume anchor and pre-set pass thresholds"
      ),
      "[data-vendor-response-germany-copy]": l(
        "Vuosien 2023–2024 lopulliset verotetun nestemäärän luvut testaavat toimittajan Saksa-näytteen. Vuosi 2025 on alustava konteksti, ei läpäisytesti.",
        "Final 2023–2024 taxed-liquid volumes test a vendor's Germany sample. The provisional 2025 value is context, not a pass-test year."
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
        "Tila perustuu varmennettuun julkiseen tarkistuspisteeseen. Tarjouksen vastaanotto ei osoita edustavaa näytettä, varmennettua dataa, täydellisiä ehtoja tai ostokelpoisuutta.",
        "Status reflects a verified public checkpoint. Receipt of a quote does not establish a representative sample, verified data, complete terms or purchase readiness."
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
        "toimittajareittiä, joilla sisällöllisiä vastauksia",
        "vendor routes with substantive responses",
        "ehdollinen maksullinen Saksa-ote tarjottu · ei hyväksytty · 0/6 porttia läpäisty",
        "conditional paid Germany extract offered · not accepted · 0/6 gates passed",
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

  function gateStatusMeta(status) {
    const states = {
      pass: {
        mark: "✓",
        label: l("Läpäisty", "Pass")
      },
      fail: {
        mark: "×",
        label: l("Hylätty", "Fail")
      },
      not_testable: {
        mark: "?",
        label: l("Ei testattavissa", "Not testable")
      },
      missing: {
        mark: "—",
        label: l("Puuttuu", "Missing")
      }
    };
    return states[status];
  }

  function renderGateResult(gate, result) {
    const meta = gateStatusMeta(result.status);
    const element = node(
      "li",
      `vendor-response-evidence-item vendor-response-gate-result is-gate-${result.status}`
    );
    const mark = node("span", "vendor-response-evidence-mark", meta.mark);
    mark.setAttribute("aria-hidden", "true");
    const label = node(
      "span",
      "vendor-response-evidence-label",
      isFi() ? gate.labelFi : gate.labelEn
    );
    label.append(
      node("small", "", `${gate.gateCode} · ${l("pakollinen", "mandatory")}`),
      node("small", "vendor-response-gate-reasons", result.reasonCodes.join(" · "))
    );
    const state = node("strong", "", meta.label);
    element.append(mark, label, state);
    return element;
  }

  function renderQuoteIndicator(vendor) {
    const received = vendor.quoteReceived === true;
    const element = node(
      "div",
      `vendor-response-quote ${received ? "is-received" : "is-missing"}`
    );
    const copy = node("div", "");
    copy.append(
      node("span", "", l("Kaupallinen syöte", "Commercial input")),
      node("strong", "", received ? l("Tarjous vastaanotettu", "Quote received") : l("Tarjous puuttuu", "Quote missing"))
    );
    element.append(
      copy,
      node(
        "small",
        "",
        l(
          "Tarjous kirjataan erikseen eikä se läpäise mitään G1–G6-porttia.",
          "A quote is tracked separately and does not pass any G1–G6 gate."
        )
      )
    );
    return element;
  }

  function receiptLabel(evidenceType) {
    const labels = {
      sample: ["Näyteaineisto", "Sample material"],
      methodology: ["Menetelmäaineisto", "Method material"],
      coverageMatrix: ["Peittoaineisto", "Coverage material"],
      quote: ["Tarjousasiakirja", "Quote document"],
      officialAnchorReconciliation: [
        "Viranomaistäsmäytystä koskeva aineisto",
        "Official-reconciliation material"
      ],
      transactionUseRights: [
        "Transaktio-oikeuksia koskeva aineisto",
        "Rights-related material"
      ],
      totalCostTerms: [
        "Kaupallisia ehtoja koskeva aineisto",
        "Commercial-terms material"
      ]
    };
    const label = labels[evidenceType.key];
    return label ? l(label[0], label[1]) : l(evidenceType.labelFi, evidenceType.labelEn);
  }

  function renderReceiptLedger(vendor) {
    const ledger = node("section", "vendor-response-receipts");
    const header = node("div", "vendor-response-receipts-head");
    const heading = node("div", "");
    heading.append(
      node("span", "", l("Vastaanottorekisteri", "Receipt ledger")),
      node(
        "h4",
        "",
        `${l("Aineistoa saatu", "Material received")} · ${
          vendor.evidenceReceivedCount
        }/${control.evidenceTypes.length}`
      )
    );
    header.append(
      heading,
      node(
        "p",
        "",
        l(
          "Aineiston vastaanotto ei osoita täydellisyyttä eikä portin läpäisyä.",
          "Material receipt does not establish completeness or gate passage."
        )
      )
    );

    const list = node("ul", "vendor-response-receipt-list");
    for (const evidenceType of control.evidenceTypes) {
      const received = vendor.receivedEvidence[evidenceType.key] === true;
      const item = node(
        "li",
        `vendor-response-receipt-item ${received ? "is-received" : "is-missing"}`
      );
      item.dataset.evidenceKey = evidenceType.key;
      const mark = node(
        "span",
        "vendor-response-receipt-mark",
        received ? "✓" : "—"
      );
      mark.setAttribute("aria-hidden", "true");
      item.append(
        mark,
        node(
          "span",
          "vendor-response-receipt-label",
          receiptLabel(evidenceType)
        ),
        node(
          "strong",
          "",
          received ? l("Aineistoa saatu", "Material received") : l("Ei aineistoa", "No material")
        )
      );
      list.append(item);
    }
    ledger.append(header, list);
    return ledger;
  }

  function renderVendor(vendor) {
    const card = node("article", "vendor-response-card");
    card.dataset.vendorState = vendor.requestState;
    const header = node("div", "vendor-response-card-head");
    const name = node("div", "");
    name.append(node("h3", "", vendor.vendor), node("p", "", vendor.product));
    const statusLabel = vendor.vendorId === "euromonitor-passport-nicotine"
      ? l("OSITTAINEN NÄYTE · TARJOUS SAATU", "PARTIAL SAMPLE · QUOTE RECEIVED")
      : vendor.responseState === "commercial_qualification_response_received"
        ? l("KAUPALLINEN RAJAUS · NÄYTE + TARJOUS ODOTTAVAT", "COMMERCIAL QUALIFICATION · SAMPLE + QUOTE PENDING")
      : vendor.responseState === "substantive_response_received"
        ? l("VASTAUKSIA · NÄYTE PUUTTUU", "RESPONSES · SAMPLE PENDING")
      : vendor.requestState === "not_submitted_terms_gate"
        ? l("EI LÄHETETTY · EHTOPORTTI", "NOT SUBMITTED · TERMS GATE")
        : vendor.requestState === "submission_confirmed"
          ? l("LÄHETYS VAHVISTETTU", "SUBMISSION CONFIRMED")
          : l("LÄHETETTY · VASTAUS PUUTTUU", "SENT · NO RESPONSE");
    const status = node(
      "span",
      `vendor-response-state vendor-response-state-${vendor.requestState}`,
      statusLabel
    );
    header.append(name, status);
    const narrative = node(
      "p",
      "vendor-response-narrative",
      isFi() ? vendor.publicStatusFi : vendor.publicStatusEn
    );

    const score = node("div", "vendor-response-score");
    const scoreCopy = node("div", "");
    scoreCopy.append(
      node("span", "", l("Arviointitila", "Evaluation state")),
      node("strong", "", l("EI PISTEYTETTY", "NOT SCORED"))
    );
    const progress = node("div", "vendor-response-progress");
    progress.append(
      node("span", "", l("Pakolliset portit", "Mandatory gates")),
      node(
        "strong",
        "",
        `${vendor.mandatoryGatePassCount}/${control.mandatoryGates.length} ${l("läpäisty", "passed")}`
      ),
      node(
        "small",
        "",
        `${vendor.evaluatedGateCount}/${control.mandatoryGates.length} ${l("arvioitu", "evaluated")}`
      )
    );
    score.append(scoreCopy, progress);

    const evidence = node("ul", "vendor-response-evidence vendor-response-gate-results");
    for (const gate of control.mandatoryGates) {
      evidence.append(
        renderGateResult(gate, vendor.gateResults[gate.gateCode])
      );
    }
    card.append(
      header,
      narrative,
      renderReceiptLedger(vendor),
      score,
      renderQuoteIndicator(vendor),
      evidence
    );
    return card;
  }

  function renderVendors() {
    const container = root.querySelector("[data-vendor-response-vendors]");
    container.replaceChildren(...control.vendors.map(renderVendor));
    container.hidden = false;
  }

  function formatVolume(value) {
    return new Intl.NumberFormat(isFi() ? "fi-FI" : "en-GB").format(value);
  }

  function renderGermanyBenchmark() {
    const benchmark = control.germanyBenchmark;
    const anchors = root.querySelector("[data-vendor-response-germany-anchors]");
    anchors.replaceChildren(...benchmark.officialAnchors.map((anchor) => {
      const item = node("article", "vendor-response-criterion");
      const heading = node("div", "vendor-response-criterion-heading");
      const role = anchor.role === "pass_test"
        ? l("TESTIVUOSI", "PASS YEAR")
        : l("KONTEKSTI", "CONTEXT");
      heading.append(
        node("span", "vendor-response-criterion-number", String(anchor.year)),
        node("h4", "", `${formatVolume(anchor.value)} L`),
        node("strong", "", anchor.finality === "final" ? l("LOPULLINEN", "FINAL") : l("ALUSTAVA", "PROVISIONAL"))
      );
      item.append(
        heading,
        node("p", "", `${role} · ${anchor.observationId}`)
      );
      return item;
    }));
    anchors.hidden = false;

    const requirements = root.querySelector("[data-vendor-response-germany-requirements]");
    const thresholdItems = [
      {
        labelFi: "Vuosittainen poikkeama ≤15 %",
        labelEn: "Annual deviation ≤15%",
        copyFi: benchmark.thresholds.annualDeviation.formulaFi,
        copyEn: benchmark.thresholds.annualDeviation.formulaEn
      },
      {
        labelFi: "Vuosien 2023–2024 yhteispoikkeama ≤10 %",
        labelEn: "2023–2024 cumulative deviation ≤10%",
        copyFi: benchmark.thresholds.twoYearCumulativeDeviation.formulaFi,
        copyEn: benchmark.thresholds.twoYearCumulativeDeviation.formulaEn
      }
    ];
    requirements.replaceChildren(
      ...thresholdItems.map((threshold) => {
        const item = node("li", "vendor-response-gate");
        item.append(
          node("span", "vendor-response-gate-mark", "TEST"),
          node("strong", "", l(threshold.labelFi, threshold.labelEn)),
          node("p", "", l(threshold.copyFi, threshold.copyEn))
        );
        return item;
      }),
      ...benchmark.requiredEvidence.map((requirement) => {
        const item = node("li", "vendor-response-gate");
        item.append(
          node("span", "vendor-response-gate-mark", l("VAAT.", "REQ.")),
          node("strong", "", isFi() ? requirement.labelFi : requirement.labelEn),
          node("p", "", isFi() ? requirement.descriptionFi : requirement.descriptionEn)
        );
        return item;
      })
    );
    requirements.hidden = false;

    const panel = root.querySelector("[data-vendor-response-germany-benchmark]");
    panel.hidden = false;
    const note = root.querySelector("[data-vendor-response-germany-note]");
    note.textContent = `${l("EI TESTATTAVISSA", "NOT TESTABLE")} · ${
      isFi() ? benchmark.statusReasonFi : benchmark.statusReasonEn
    } ${isFi() ? benchmark.donorBoundaryFi : benchmark.donorBoundaryEn}`;
    note.hidden = false;
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
        node("span", "vendor-response-gate-mark", gate.gateCode),
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
    renderGermanyBenchmark();
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
        "4 toimittajaa seurannassa · Euromonitor 0/6 läpäistyä porttia · 0 pisteytettyä toimittajanäytettä · 0 ostovaltuutusta.",
        "4 vendors tracked · Euromonitor 0/6 gates passed · 0 vendor samples scored · 0 purchase authorisations."
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
      "[data-vendor-response-germany-benchmark]",
      "[data-vendor-response-germany-anchors]",
      "[data-vendor-response-germany-requirements]",
      "[data-vendor-response-germany-note]",
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
