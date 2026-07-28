"use strict";

(() => {
  const usRoot = document.querySelector("[data-us-benchmark-control]");
  const waveRoot = document.querySelector("[data-open-extraction-wave]");
  if (!usRoot && !waveRoot) return;

  let usControl = null;
  let extractionWave = null;
  let usLoadFailed = false;
  let waveLoadFailed = false;
  const US_GATE_FI = {
    G1: {
      label: "Täytetty tarkistusnäyte",
      passLogic: "Vähintään 24 täydellistä kuukautta todellisia arvo- ja volyymirivejä sekä vähintään yksi FTC:n virallisen aggregaatin kanssa päällekkäinen jakso."
    },
    G2: {
      label: "Datamäärittely ja menetelmä",
      passLogic: "Kentät, keruu, otos tai projektio, painot, puuttuvat tiedot, revisiot ja rivikohtainen havaittu/raportoitu/mallinnettu-tila on dokumentoitu."
    },
    G3: {
      label: "Tuote- ja kanavapeitto",
      passLogic: "Laitteet, kertakäyttöiset, podit/patruunat ja pullonesteet on erotettu, ja fyysisten sekä verkkokanavien sisältyminen tai puuttuminen on määrällistetty."
    },
    G4: {
      label: "Täsmäytys viranomaisankkuriin",
      passLogic: "Saman vuoden FTC-osajoukko sekä tapahtumavaihe- ja verosilta ovat toistettavia; jaksot täsmäävät vuositasoon ja selittämätön jäännös alittaa ennalta asetetun rajan."
    },
    G5: {
      label: "Transaktiokäyttöoikeudet",
      passLogic: "Kirjalliset oikeudet kattavat johdetut asiakastuotokset sekä hallitun lainanantaja-, ostaja-, neuvonantaja-, tarkastaja- ja datahuonekäytön."
    },
    G6: {
      label: "Täydelliset kaupalliset ehdot",
      passLogic: "Kokonaishinta, verot, käyttäjät, viennit, päivitykset, säilytys, peruutus, uusiminen ja automaattisen uusinnan puuttuminen on kuvattu."
    }
  };
  const ROUTE_COPY = {
    ES_AEAT_2025_MODEL573_AGGREGATE_RECEIPTS: {
      roleCode: "official_fiscal_observation",
      roleFi: "Virallinen fiskaalinen havainto",
      roleEn: "Official fiscal observation",
      limitationsFi: [
        "30 miljoonaa euroa on koko Model 573 -veron kassakertymä, ei kuluttajavähittäismyyntiä.",
        "Julkaistu summa ei erottele neljää veroluokkaa, joten sitä ei nimetä e-nesteiden kokonaismääräksi.",
        "Ensimmäinen jakso alkaa huhtikuusta 2025 ja sisältää siirtymävarastoja; se ei ole vertailukelpoinen täysi vuosi.",
        "Laitteet eivät kuulu tähän veroaggregaattiin."
      ],
      limitationsEn: [
        "The EUR 30 million is aggregate Model 573 tax cash receipts, not consumer retail sales.",
        "The published aggregate does not split the four epigraphs, so it cannot be labelled e-liquid-only.",
        "The first-year observation begins in April 2025 and includes transitional stock rules; it is not a full-year comparable.",
        "Devices are outside this fiscal aggregate."
      ]
    },
    ES_AEAT_MODEL573_EPIGRAPH_QUANTITIES: {
      roleCode: "quantity_and_scope_closure",
      roleFi: "Määrä- ja tuoterajauksen sulkeminen",
      roleEn: "Quantity and scope closure",
      limitationsFi: [
        "Julkista kansallista veroluokka- ja määrätaulukkoa ei löytynyt.",
        "Tuotemäärää ei johdeta kokonaisverosta, kun veroluokkien jakauma on tuntematon."
      ],
      limitationsEn: [
        "No public national epigraph-level aggregate or quantity table was located.",
        "Do not backsolve a product quantity from aggregate receipts while the epigraph mix is unknown."
      ]
    },
    KR_KCS_ITEMTRADE_HSK10: {
      roleCode: "official_customs_proxy",
      roleFi: "Virallinen tulliproxy",
      roleEn: "Official customs proxy",
      limitationsFi: [
        "API-palveluavain vaaditaan.",
        "Avoin kooditiedosto vahvistaa vuoden 2026; vuosien 2022–2025 historialliset HSK10-versiot on varmennettava.",
        "KCS-arvot ovat rajailmoituksia: tuonti ilmoitetaan CIF- ja vienti FOB-arvona.",
        "Tullivirrat eivät ole kuluttajavähittäismyyntiä, eikä niitä netoteta retail-markkinaksi ilman kotimaisen tuotannon, varastojen ja päällekkäisyyksien kontrollia.",
        "Laajat muut- ja osakoodit eivät ole sähkötupakkaan yksiselitteisesti rajattuja."
      ],
      limitationsEn: [
        "An API service key is required.",
        "The open code file verifies 2026 only; exact historical HSK10 versions must be validated before 2022–2025 extraction.",
        "KCS values are border declarations: imports are CIF and exports are FOB.",
        "Customs flows are not consumer retail sales and must not be netted into a retail market without domestic production, inventory and overlap controls.",
        "Broad other and parts codes are not vaping-only."
      ]
    },
    JP_MOF_ESTAT_COMMODITY_BY_COUNTRY_IMPORT: {
      roleCode: "official_customs_proxy",
      roleFi: "Virallinen tulliproxy",
      roleEn: "Official customs proxy",
      limitationsFi: [
        "CSV mittaa yhdeksännumeroisen koodin mukaista tuontia alkuperämaittain, ei kuluttajavähittäismyyntiä.",
        "Laajat koodit 240419100 ja 240419200 jäävät pois kaikesta vape-koonnista.",
        "Koodi 240412000 kattaa säädellyn nikotiinia sisältävän polttamattoman tuoteryhmän, ei yksin e-nesteitä.",
        "Nikotiinituotteiden tuontilupa on oikeudellinen rajaus, ei markkinalukua muuttava laskentaoikaisu.",
        "Vienti, kotimainen tuotanto, varastot, laiton tarjonta ja vähittäiskaupan katteet puuttuvat."
      ],
      limitationsEn: [
        "The CSV records customs imports by 9-digit code and country of origin, not consumer retail sell-through.",
        "Codes 240419100 and 240419200 are broader than vaping and remain excluded from any vaping roll-up.",
        "Code 240412000 is a regulated nicotine-containing non-combustion category, not an e-liquid-only code.",
        "The nicotine permission boundary is legal context, not a numerical market adjustment.",
        "Exports, domestic production, inventory, illicit supply and retail mark-ups are not covered."
      ]
    }
  };
  const EXPECTED_ROUTE_IDS = Object.freeze(Object.keys(ROUTE_COPY));
  const EXPECTED_HIGHLIGHT_IDS = Object.freeze([
    "US-FTC-2021-CARTRIDGE-DISPOSABLE-SALES",
    "US-CDC-2024-JUNE-FOUR-WEEK-RETAIL-SALES-USD",
    "US-CDC-2024-JUNE-FOUR-WEEK-RETAIL-UNITS",
    "US-WI-FY2025-TAXABLE-VAPOR-ML",
    "US-NC-FY2024-DERIVED-TAXABLE-VAPOR-ML"
  ]);
  const ROUTE_STATE_LABELS = Object.freeze({
    ready_with_scope_blocker: ["Valmis, mutta rajauseste avoin", "Ready with a scope blocker"],
    auth_and_historical_codebook_required: ["Tunniste ja historiallinen koodisto vaaditaan", "Authentication and historical codebook required"],
    ready_customs_proxy_with_permission_separation: ["Tulliproxy valmis, lupa- ja markkinarajaus erillään", "Customs proxy ready with permission boundary kept separate"]
  });
  const TRANSACTION_STAGE_LABELS = Object.freeze({
    realised_excise_cash_receipts: ["Toteutunut valmisteverokassakertymä", "Realised excise cash receipts"],
    taxpayer_self_assessed_excise_base: ["Verovelvollisen itse ilmoittama valmisteveropohja", "Taxpayer self-assessed excise base"],
    customs_border_declaration: ["Tulli-ilmoitus rajalla", "Customs border declaration"],
    customs_import_declaration: ["Tuonnin tulli-ilmoitus", "Customs import declaration"]
  });
  const FEE_STATUS_LABELS = Object.freeze({
    free: ["Maksuton", "Free"],
    not_applicable: ["Ei sovellu", "Not applicable"],
    fee_required: ["Maksullinen", "Fee required"]
  });
  const ROUTE_STATUSES = new Set(["ready", "blocked", "auth_required"]);

  function isFi() {
    return window.SiteI18n?.isFinnish?.() ?? document.documentElement.lang === "fi";
  }

  function l(fi, en) {
    return window.SiteI18n?.pick?.(fi, en) ?? (isFi() ? fi : en);
  }

  function node(tag, className = "", text = "") {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== "") element.textContent = String(text);
    return element;
  }

  function safeUrl(value) {
    try {
      const url = new URL(value, location.href);
      return url.protocol === "https:" ? url.href : null;
    } catch (_) {
      return null;
    }
  }

  function formatNumber(value, maximumFractionDigits = 0) {
    return new Intl.NumberFormat(isFi() ? "fi-FI" : "en-US", {
      maximumFractionDigits
    }).format(value);
  }

  function formatMoney(value, currency) {
    return new Intl.NumberFormat(isFi() ? "fi-FI" : "en-US", {
      style: "currency",
      currency,
      notation: value >= 100000000 ? "compact" : "standard",
      maximumFractionDigits: value >= 100000000 ? 3 : 0
    }).format(value);
  }

  function setText(root, selector, fi, en) {
    const target = root?.querySelector(selector);
    if (target) target.textContent = l(fi, en);
  }

  function hasOwnLabel(labels, value) {
    return Object.prototype.hasOwnProperty.call(labels, value);
  }

  function enumLabel(labels, value) {
    const pair = hasOwnLabel(labels, value) ? labels[value] : null;
    if (pair) return l(pair[0], pair[1]);
    return String(value || "—").replaceAll("_", " ");
  }

  function isIsoDate(value) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(String(value || ""))) return false;
    const parsed = new Date(`${value}T00:00:00Z`);
    return !Number.isNaN(parsed.valueOf()) && parsed.toISOString().slice(0, 10) === value;
  }

  function formatDate(value) {
    return new Intl.DateTimeFormat(isFi() ? "fi-FI" : "en-GB", {
      day: "numeric",
      month: isFi() ? "numeric" : "long",
      year: "numeric",
      timeZone: "UTC"
    }).format(new Date(`${value}T00:00:00Z`));
  }

  function validateUs(raw) {
    if (!raw
      || raw.schemaVersion !== "1.0"
      || raw.controlId !== "US-INDEPENDENT-BENCHMARK-CONTROL-20260728"
      || !isIsoDate(raw.asOf)
      || !Array.isArray(raw.sources)
      || raw.sources.length !== 7
      || !Array.isArray(raw.observations)
      || raw.observations.length !== 19
      || raw.outputs?.unitedStatesRetailMarketValue !== null
      || raw.outputs?.globalMarketValue !== null
      || raw.outputs?.acceptedDonorIncrement !== 0
      || raw.publicBoundary?.changesMarketTotals !== false
      || raw.publicBoundary?.changesDonorStatus !== false
      || raw.publicBoundary?.purchaseAuthorised !== false
      || raw.sampleAcceptance?.currentEvaluation?.sampleId !== null
      || raw.sampleAcceptance?.currentEvaluation?.scorable !== false
      || !Array.isArray(raw.sampleAcceptance?.gates)) {
      throw new Error("unsupported United States benchmark control");
    }
    const sourceIds = raw.sources.map((source) => source.sourceId);
    if (sourceIds.some((sourceId) => typeof sourceId !== "string" || !sourceId)
      || new Set(sourceIds).size !== sourceIds.length
      || raw.sources.some((source) => (
        typeof source.publisher !== "string"
        || !source.publisher
        || !safeUrl(source.pageUrl || source.url)
      ))) {
      throw new Error("United States benchmark source set differs");
    }
    const gateIds = (raw.sampleAcceptance.gates || []).map((gate) => gate.id);
    if (gateIds.join(",") !== "G1,G2,G3,G4,G5,G6"
      || raw.sampleAcceptance.gates.some((gate) => (
        typeof gate.label !== "string"
        || !gate.label
        || typeof gate.passLogic !== "string"
        || !gate.passLogic
        || raw.sampleAcceptance.currentEvaluation[gate.id] !== "not_evaluated"
      ))) {
      throw new Error("United States benchmark gate set differs");
    }
    const recordIds = raw.observations.map((item) => item.recordId);
    if (recordIds.some((recordId) => typeof recordId !== "string" || !recordId)
      || new Set(recordIds).size !== recordIds.length
      || EXPECTED_HIGHLIGHT_IDS.some((recordId) => !recordIds.includes(recordId))
      || raw.observations.some((item) => (
        item.retailSalesEligible !== false
        || !Number.isFinite(item.value)
        || item.value < 0
        || !sourceIds.includes(item.sourceId)
      ))) {
      throw new Error("United States benchmark contains a retail-rollup-eligible observation");
    }
    return raw;
  }

  function validateWave(raw) {
    if (!raw
      || raw.schemaVersion !== "1.0"
      || raw.waveId !== "ES_KR_JP_OPEN_OFFICIAL_2026_07_28"
      || !isIsoDate(raw.asOf)
      || !Array.isArray(raw.countries)
      || raw.countryCount !== raw.countries.length
      || raw.countries.length !== 3
      || raw.countries.map((item) => item.countryIso2).join(",") !== "ES,KR,JP") {
      throw new Error("unsupported open-data extraction wave");
    }
    const routeIds = [];
    for (const country of raw.countries) {
      if (country.marketValueStatus !== "not_computed"
        || typeof country.countryFi !== "string"
        || !country.countryFi
        || typeof country.countryEn !== "string"
        || !country.countryEn
        || !hasOwnLabel(ROUTE_STATE_LABELS, country.routeState)
        || !Array.isArray(country.routes)
        || country.routes.length === 0) {
        throw new Error("open-data country boundary differs");
      }
      for (const route of country.routes) {
        routeIds.push(route.routeId);
        const routeCopy = ROUTE_COPY[route.routeId];
        if (!routeCopy
          || route.role !== routeCopy.roleCode
          || !ROUTE_STATUSES.has(route.status)
          || !hasOwnLabel(TRANSACTION_STAGE_LABELS, route.transactionStage)
          || !hasOwnLabel(FEE_STATUS_LABELS, route.feeStatus)
          || route.retailSalesEligible !== false
          || route.globalRollupEligible !== false
          || !Array.isArray(route.sources)
          || route.sources.length === 0
          || route.sources.some((source) => !safeUrl(source.url || source.pageUrl))
          || (route.blockers !== null && route.blockers !== undefined && !Array.isArray(route.blockers))
          || (route.limitations !== null && route.limitations !== undefined && !Array.isArray(route.limitations))) {
          throw new Error("open-data route boundary differs");
        }
      }
      if (country.routes.some((route) => (
        route.retailSalesEligible !== false || route.globalRollupEligible !== false
      ))) {
        throw new Error("open-data route is incorrectly roll-up eligible");
      }
    }
    if (routeIds.join(",") !== EXPECTED_ROUTE_IDS.join(",")) {
      throw new Error("open-data route set differs");
    }
    return raw;
  }

  function summaryCard(label, value, note) {
    const card = node("div", "donor-summary-item");
    card.append(
      node("span", "", label),
      node("strong", "", value),
      node("small", "", note)
    );
    return card;
  }

  function sourceLinks(sources) {
    const wrap = node("div", "donor-source-links");
    for (const source of sources || []) {
      const href = safeUrl(source.pageUrl || source.url);
      if (!href) continue;
      const link = node("a", "", source.publisher || source.title || source.sourceId);
      link.href = href;
      link.target = "_blank";
      link.rel = "noreferrer";
      wrap.append(link);
    }
    return wrap;
  }

  function usObservation(id) {
    return usControl.observations.find((item) => item.recordId === id);
  }

  function usHighlight(title, value, stage, note, sourceId) {
    const card = node("article", "request-program-stack-card");
    card.append(
      node("span", "request-program-stack-order", stage),
      node("h4", "", title),
      node("strong", "", value),
      node("p", "", note)
    );
    const source = usControl.sources.find((item) => item.sourceId === sourceId);
    if (source) card.append(sourceLinks([source]));
    return card;
  }

  function renderUs() {
    if (!usRoot || !usControl) return;
    const sourceCount = usControl.sources.length;
    const observationCount = usControl.observations.length;
    const gateCount = usControl.sampleAcceptance.gates.length;
    const gatesPassed = usControl.sampleAcceptance.gates.filter(
      (gate) => usControl.sampleAcceptance.currentEvaluation[gate.id] === "pass"
    ).length;
    setText(usRoot, "[data-us-kicker]", "Yhdysvallat · riippumaton kontrollipaneeli", "United States · independent control panel");
    setText(usRoot, "[data-us-title]", "Viranomaisankkurit toimittajanäytteen testaamiseen", "Official anchors for testing a vendor sample");
    setText(
      usRoot,
      "[data-us-intro]",
      "Valmistajamyynti, neljän viikon vähittäispiste, osavaltioiden veropohjat ja tullireitti pysyvät erillisinä. Paneeli ei muodosta Yhdysvaltain markkina-arvoa.",
      "Manufacturer sales, a four-week retail checkpoint, state tax bases and the customs route remain separate. The panel does not produce a United States market value."
    );
    setText(
      usRoot,
      "[data-us-boundary-title]",
      `${observationCount} kontrollihavaintoa · kansallista vähittäisarvoa ei laskettu`,
      `${observationCount} control observations · national retail value not computed`
    );
    setText(
      usRoot,
      "[data-us-boundary-copy]",
      "Mitään tapahtumavaiheita ei lasketa mekaanisesti yhteen. Yhdysvallat pysyy donor-portin ulkopuolella, toimittajanäyte ei ole vielä pisteytettävissä eikä ostoa ole valtuutettu.",
      "No transaction stages are mechanically added. The United States remains outside the donor gate, no vendor sample is yet scorable and no purchase is authorised."
    );

    const summary = usRoot.querySelector("[data-us-summary]");
    summary.replaceChildren(
      summaryCard(l("Viralliset lähteet", "Official sources"), String(sourceCount), l("FTC · CDC · WI · NC · Census · USITC", "FTC · CDC · WI · NC · Census · USITC")),
      summaryCard(l("Kontrollihavainnot", "Control observations"), String(observationCount), l("Kaikki roll-up-kelvottomia", "All ineligible for roll-up")),
      summaryCard(l("Näyteportit", "Sample gates"), `${gatesPassed}/${gateCount}`, l("Ei arvioitu ilman näytettä", "Not evaluated without a sample")),
      summaryCard(l("Yhdysvaltain vähittäisarvo", "US retail value"), l("EI LASKETTU", "NOT COMPUTED"), l("Donor-lisäys 0", "Donor increment 0"))
    );

    const latestFtc = usObservation("US-FTC-2021-CARTRIDGE-DISPOSABLE-SALES");
    const cdcValue = usObservation("US-CDC-2024-JUNE-FOUR-WEEK-RETAIL-SALES-USD");
    const cdcUnits = usObservation("US-CDC-2024-JUNE-FOUR-WEEK-RETAIL-UNITS");
    const wi = usObservation("US-WI-FY2025-TAXABLE-VAPOR-ML");
    const nc = usObservation("US-NC-FY2024-DERIVED-TAXABLE-VAPOR-ML");
    const highlights = usRoot.querySelector("[data-us-highlights]");
    highlights.replaceChildren(
      usHighlight(
        l("FTC 2021 · suljetut järjestelmät + kertakäyttöiset", "FTC 2021 · cartridge systems + disposables"),
        formatMoney(latestFtc.value, "USD"),
        l("VALMISTAJAVAIHE", "MANUFACTURER STAGE"),
        l("Yhdeksän johtavaa valmistajaa; open-system-tuotteet ja täydellinen retail-peitto puuttuvat.", "Nine leading manufacturers; open-system products and complete retail coverage are excluded."),
        latestFtc.sourceId
      ),
      usHighlight(
        l("CDC kesäkuu 2024 · neljän viikon vähittäispiste", "CDC June 2024 · four-week retail checkpoint"),
        `${formatMoney(cdcValue.value, "USD")} · ${formatNumber(cdcUnits.value)} ${l("yksikköä", "units")}`,
        l("OSITTAINEN RETAIL", "PARTIAL RETAIL"),
        l("Kivijalkaskanneri; verkko- ja tupakkaerikoisliikkeet puuttuvat. Lukua ei vuositasoisteta.", "Brick-and-mortar scanner data; online and tobacco-specialty stores are missing. The value is not annualised."),
        cdcValue.sourceId
      ),
      usHighlight(
        l("Wisconsin FY2025 · verotettu höyrytuotetilavuus", "Wisconsin FY2025 · taxable vapor volume"),
        `${formatNumber(wi.value)} ml`,
        l("OSAVALTION VEROVAIHE", "STATE TAX STAGE"),
        l("Fyysinen veropohja, ei kansallinen määrä eikä vähittäisarvo.", "Physical tax base, not a national volume or retail value."),
        wi.sourceId
      ),
      usHighlight(
        l("North Carolina FY2024 · johdettu verotettu tilavuus", "North Carolina FY2024 · derived taxable volume"),
        `${formatNumber(nc.value)} ml`,
        l("OSAVALTION VEROVAIHE", "STATE TAX STAGE"),
        l("Johdettu virallisesta verotuotosta kaavalla verotuotto ÷ 0,05 USD/ml.", "Derived from official receipts as tax receipts ÷ USD 0.05/ml."),
        nc.sourceId
      )
    );

    const gates = usRoot.querySelector("[data-us-gates]");
    gates.replaceChildren(...usControl.sampleAcceptance.gates.map((gate) => {
      const translated = US_GATE_FI[gate.id];
      const item = node("li", "vendor-response-gate");
      item.append(
        node("span", "vendor-response-gate-mark", gate.id),
        node("strong", "", isFi() ? translated.label : gate.label),
        node("p", "", isFi() ? translated.passLogic : gate.passLogic)
      );
      return item;
    }));

    const method = usRoot.querySelector("[data-us-method]");
    if (method) method.hidden = false;
    const actions = usRoot.querySelector("[data-us-actions]");
    actions.hidden = false;
    const status = usRoot.querySelector("[data-us-status]");
    status.dataset.state = "ready";
    status.textContent = l(
      `Varmennettu ${formatDate(usControl.asOf)} · ${sourceCount} lähdettä · ${observationCount} kontrollihavaintoa · vähittäisarvoa ei laskettu`,
      `Verified ${formatDate(usControl.asOf)} · ${sourceCount} sources · ${observationCount} control observations · retail value not computed`
    );
    usRoot.setAttribute("aria-busy", "false");
  }

  function routeStatusLabel(value) {
    const labels = {
      ready: [l("VALMIS", "READY"), "sent"],
      blocked: [l("ESTE", "BLOCKED"), ""],
      auth_required: [l("TUNNISTE VAADITAAN", "AUTH REQUIRED"), ""]
    };
    return labels[value] || [String(value || "—").replaceAll("_", " ").toUpperCase(), ""];
  }

  function renderRoute(route) {
    const translated = ROUTE_COPY[route.routeId];
    const block = node("article", "request-program-supplement");
    const [statusText, statusClass] = routeStatusLabel(route.status);
    const head = node("div", "request-program-supplement-head");
    const headingId = `route-title-${route.routeId.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
    const roleHeading = node("strong", "", isFi() ? translated.roleFi : translated.roleEn);
    roleHeading.id = headingId;
    roleHeading.setAttribute("role", "heading");
    roleHeading.setAttribute("aria-level", "4");
    block.setAttribute("aria-labelledby", headingId);
    head.append(
      node("span", "request-program-supplement-label", route.routeId),
      node("span", `request-program-status ${statusClass ? `request-program-status-${statusClass}` : ""}`.trim(), statusText)
    );
    block.append(
      head,
      roleHeading,
      node(
        "p",
        "request-program-supplement-purpose",
        `${l("Tapahtumavaihe", "Transaction stage")}: ${enumLabel(TRANSACTION_STAGE_LABELS, route.transactionStage)} · ${l("Maksu", "Fee")}: ${enumLabel(FEE_STATUS_LABELS, route.feeStatus)}`
      )
    );
    const limitations = isFi() ? translated.limitationsFi : translated.limitationsEn;
    const list = node("ul", "request-program-supplement-list");
    for (const limitation of limitations) list.append(node("li", "", limitation));
    block.append(list, sourceLinks(route.sources));
    return block;
  }

  function renderWave() {
    if (!waveRoot || !extractionWave) return;
    const countryCount = extractionWave.countries.length;
    const routes = extractionWave.countries.flatMap((country) => country.routes);
    const ready = routes.filter((route) => route.status === "ready").length;
    const gated = routes.length - ready;
    setText(waveRoot, "[data-wave-kicker]", "Avoimen viranomaisdatan poiminta-aalto", "Open official-data extraction wave");
    setText(waveRoot, "[data-wave-title]", "Espanja, Etelä-Korea ja Japani ilman odottamista", "Spain, South Korea and Japan without waiting");
    setText(
      waveRoot,
      "[data-wave-intro]",
      "Reitit määrittävät tarkat lähteet, koodit, kentät, käyttöesteet ja tapahtumavaiheet. Poiminta ei muuta tullia tai veroa vähittäismyynniksi.",
      "The routes define exact sources, codes, fields, access blockers and transaction stages. Extraction does not turn customs or tax evidence into retail sales."
    );
    setText(
      waveRoot,
      "[data-wave-boundary-title]",
      `${countryCount} maata · ${routes.length} reittiä · 0 laskettua vähittäisarvoa`,
      `${countryCount} countries · ${routes.length} routes · 0 computed retail values`
    );
    setText(
      waveRoot,
      "[data-wave-boundary-copy]",
      "Espanjan ensimmäinen verovuosi on osavuosi ja tuoteryhmäjako puuttuu. Korea tarvitsee API-avaimen ja historialliset HSK10-koodistot. Japanin avoin tullipoiminta on valmis, mutta nikotiini- ja laiterajat pidetään erillään.",
      "Spain's first tax year is partial and lacks an epigraph split. Korea requires an API key and historical HSK10 codebooks. Japan's open customs extraction is ready, while nicotine and device boundaries remain separate."
    );

    const summary = waveRoot.querySelector("[data-wave-summary]");
    summary.replaceChildren(
      summaryCard(l("Maat", "Countries"), String(countryCount), "ES · KR · JP"),
      summaryCard(l("Reitit", "Routes"), String(routes.length), l("Vero- ja tullivaiheet", "Tax and customs stages")),
      summaryCard(l("Heti valmiit", "Ready now"), String(ready), l(`${gated} estettyä tai tunnisteellista`, `${gated} blocked or credential-gated`)),
      summaryCard(l("Vähittäisarvot", "Retail values"), "0", l("Kaikkien tila: ei laskettu", "All remain uncomputed"))
    );

    const countries = waveRoot.querySelector("[data-wave-countries]");
    countries.replaceChildren(...extractionWave.countries.map((country) => {
      const card = node("article", "request-program-card");
      const head = node("div", "request-program-card-head");
      head.append(
        node("span", "request-program-rank", country.countryIso2),
        node("span", "request-program-status", l("EI LASKETTU", "NOT COMPUTED"))
      );
      card.append(
        head,
        node("h3", "", isFi() ? country.countryFi : country.countryEn),
        node("p", "request-program-rationale", `${l("Reittitila", "Route state")}: ${enumLabel(ROUTE_STATE_LABELS, country.routeState)}`)
      );
      for (const route of country.routes) card.append(renderRoute(route));
      return card;
    }));

    const actions = waveRoot.querySelector("[data-wave-actions]");
    actions.hidden = false;
    const status = waveRoot.querySelector("[data-wave-status]");
    status.dataset.state = "ready";
    status.textContent = l(
      `Poimintakontrolli varmennettu ${formatDate(extractionWave.asOf)} · puuttuva tunniste, koodisto tai tuoteryhmä säilyy esteenä eikä muutu nollaksi`,
      `Extraction control verified ${formatDate(extractionWave.asOf)} · a missing credential, codebook or product split remains blocked and never becomes zero`
    );
    waveRoot.setAttribute("aria-busy", "false");
  }

  function clearChildren(root, selector) {
    root.querySelector(selector)?.replaceChildren();
  }

  function renderError(root, kind) {
    if (!root) return;
    root.setAttribute("aria-busy", "false");
    const isUsControl = kind === "us";
    const prefix = isUsControl ? "us" : "wave";
    setText(
      root,
      `[data-${prefix}-boundary-title]`,
      isUsControl ? "Yhdysvaltain kontrollia ei saatavilla" : "Poimintakontrollia ei saatavilla",
      isUsControl ? "United States control unavailable" : "Extraction control unavailable"
    );
    setText(
      root,
      `[data-${prefix}-boundary-copy]`,
      isUsControl
        ? "Lähdedataa ei voitu varmentaa. Kontrollihavaintoja, näyteportteja tai vähittäisarvoa ei näytetä ennen kuin aineisto läpäisee tarkistukset."
        : "Reittidataa ei voitu varmentaa. Maita, reittejä tai niiden tiloja ei näytetä ennen kuin aineisto läpäisee tarkistukset.",
      isUsControl
        ? "The source data could not be verified. Control observations, sample gates and retail value are withheld until the data passes validation."
        : "The route data could not be verified. Countries, routes and their states are withheld until the data passes validation."
    );
    const selectors = isUsControl
      ? ["[data-us-summary]", "[data-us-highlights]", "[data-us-gates]"]
      : ["[data-wave-summary]", "[data-wave-countries]"];
    for (const selector of selectors) clearChildren(root, selector);
    if (isUsControl) {
      const method = root.querySelector("[data-us-method]");
      if (method) method.hidden = true;
    }
    const actions = root.querySelector(`[data-${prefix}-actions]`);
    if (actions) actions.hidden = true;
    const status = root.querySelector(`[data-${prefix}-status]`);
    if (status) {
      status.dataset.state = "error";
      status.textContent = l(
        isUsControl
          ? "Yhdysvaltain kontrollia ei voitu varmentaa. Älä käytä tämän osion lukuja."
          : "Poiminta-aaltoa ei voitu varmentaa. Älä käytä tämän osion reittitietoja.",
        isUsControl
          ? "The United States control could not be verified. Do not use figures from this section."
          : "The extraction wave could not be verified. Do not use route information from this section."
      );
    }
  }

  async function load() {
    const [usResult, waveResult] = await Promise.allSettled([
      fetch("data/us-independent-benchmark-control.json", { cache: "no-store" }),
      fetch("data/open-official-extraction-wave-es-kr-jp.json", { cache: "no-store" })
    ]);
    try {
      if (usResult.status !== "fulfilled" || !usResult.value.ok) throw new Error("US control unavailable");
      usControl = validateUs(await usResult.value.json());
      usLoadFailed = false;
      renderUs();
    } catch (error) {
      console.warn("Independent US benchmark unavailable", error);
      usControl = null;
      usLoadFailed = true;
      renderError(usRoot, "us");
    }
    try {
      if (waveResult.status !== "fulfilled" || !waveResult.value.ok) throw new Error("extraction wave unavailable");
      extractionWave = validateWave(await waveResult.value.json());
      waveLoadFailed = false;
      renderWave();
    } catch (error) {
      console.warn("Open official-data extraction wave unavailable", error);
      extractionWave = null;
      waveLoadFailed = true;
      renderError(waveRoot, "wave");
    }
  }

  document.addEventListener("pixan:languagechange", () => {
    if (usControl) renderUs();
    else if (usLoadFailed) renderError(usRoot, "us");
    if (extractionWave) renderWave();
    else if (waveLoadFailed) renderError(waveRoot, "wave");
  });

  load();
})();
