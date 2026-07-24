"use strict";

(() => {
  const root = document.querySelector("[data-request-program]");
  if (!root) return;

  const OFFICIAL_HOSTS = {
    DE: ["bund.de", "destatis.de", "gesetze-im-internet.de", "zoll.de"],
    CA: ["canada.ca", "statcan.gc.ca"],
    US: ["ftc.gov", "usitc.gov", "fda.gov", "cbp.gov"],
    CN: ["stats.gov.cn", "customs.gov.cn", "samr.gov.cn"],
    PL: ["gov.pl"],
    GB: ["gov.uk", "mhra.gov.uk"],
    SE: ["folkhalsomyndigheten.se", "skatteverket.se", "tullverket.se"],
    IT: ["adm.gov.it", "salute.gov.it"],
    FR: ["anses.fr", "cada.fr", "gouv.fr", "insee.fr"],
    ES: ["gob.es"],
    NL: ["rijksoverheid.nl", "rivm.nl", "belastingdienst.nl"],
    FI: ["lvv.fi", "suomi.fi", "vero.fi", "finlex.fi", "tulli.fi"],
    DK: ["erhvervsstyrelsen.dk", "sik.dk", "skat.dk"],
    JP: ["mof.go.jp", "customs.go.jp", "mhlw.go.jp"],
    KR: ["customs.go.kr", "open.go.kr", "go.kr"],
    AU: ["tga.gov.au", "homeaffairs.gov.au", "oaic.gov.au", "abs.gov.au"],
    RU: ["nalog.gov.ru", "rosstat.gov.ru", "customs.gov.ru"],
    BR: ["gov.br"],
    ID: ["beacukai.go.id", "kemenkeu.go.id", "bps.go.id"],
    PH: ["foi.gov.ph", "bir.gov.ph", "customs.gov.ph", "psa.gov.ph"]
  };
  const SENSITIVE_QUERY_KEYS = new Set([
    "access_token", "api_key", "apikey", "authorization", "key", "password",
    "secret", "sig", "signature", "token", "x-amz-credential", "x-amz-signature"
  ]);
  const PRIVATE_METADATA_KEYS = new Set([
    "acknowledgedon", "acknowledgementon", "acknowledgmenton", "bcc", "body", "cc",
    "conversationid", "correspondence", "deliveredon", "email", "emailaddress", "from",
    "gmailid", "header", "headers", "messageid", "missiveid", "mobile", "phone",
    "phonenumber", "receivedon", "recipient", "recipientemail", "recipientidentity",
    "recipientname", "sender", "senderemail", "senderidentity", "sendername", "senttime",
    "senttimestamp", "subject", "telephone", "threadid", "to"
  ]);
  const PROCESS_RESPONSE_LABELS = {
    receipt_and_ifg_forwarding_confirmed: {
      en: "Receipt and forwarding to the competent IFG unit confirmed — process only; no data received",
      fi: "Vastaanotto ja ohjaus toimivaltaiseen IFG-yksikköön vahvistettu — vain prosessitieto; ei dataa"
    },
    registered_and_processing_confirmed: {
      en: "Formally registered and under processing — process only; no data received",
      fi: "Muodollisesti rekisteröity ja käsittelyssä — vain prosessitieto; ei dataa"
    },
    registered_processing_notice_received: {
      en: "Registered; delay / possible-fee notice received — no fee accepted; no data received",
      fi: "Kirjattu diaariin; viive-/mahdollinen maksu -ilmoitus saatu — maksua ei hyväksytty; ei dataa"
    },
    automated_receipt_acknowledged: {
      en: "Automated receipt acknowledgement — process only; no data received",
      fi: "Automaattinen vastaanottokuittaus — vain prosessitieto; ei dataa"
    },
    automated_route_correction_received: {
      en: "Automated route correction — public-record service identified; no data received",
      fi: "Automaattinen reittikorjaus — julkisuuspyyntöpalvelu tunnistettu; ei dataa"
    }
  };
  const EXPECTED_DISPATCH = {
    DE: {
      state: "sent",
      sentOn: "2026-07-23",
      publicAuthorityReference: null,
      responseState: "registered_and_processing_confirmed"
    },
    CA: {
      state: "sent",
      sentOn: "2026-07-23",
      publicAuthorityReference: null,
      responseState: "not_publicly_recorded"
    },
    US: {
      state: "sent",
      sentOn: "2026-07-24",
      publicAuthorityReference: null,
      responseState: "not_publicly_recorded"
    },
    GB: {
      state: "sent",
      sentOn: "2026-07-16",
      publicAuthorityReference: "CEC 261515",
      responseState: "not_publicly_recorded"
    },
    FI: {
      state: "sent",
      sentOn: "2026-07-22",
      publicAuthorityReference: null,
      responseState: "registered_processing_notice_received"
    },
    PL: {
      state: "sent",
      sentOn: "2026-07-22",
      publicAuthorityReference: null,
      responseState: "not_publicly_recorded"
    },
    SE: {
      state: "sent",
      sentOn: "2026-07-23",
      publicAuthorityReference: null,
      responseState: "automated_route_correction_received"
    },
    IT: {
      state: "sent",
      sentOn: "2026-07-23",
      publicAuthorityReference: null,
      responseState: "not_publicly_recorded"
    },
    FR: {
      state: "sent",
      sentOn: "2026-07-23",
      publicAuthorityReference: null,
      responseState: "not_publicly_recorded"
    },
    NL: {
      state: "sent",
      sentOn: "2026-07-23",
      publicAuthorityReference: null,
      responseState: "not_publicly_recorded"
    },
    DK: {
      state: "sent",
      sentOn: "2026-07-23",
      publicAuthorityReference: null,
      responseState: "automated_receipt_acknowledged"
    },
    AU: {
      state: "sent",
      sentOn: "2026-07-23",
      publicAuthorityReference: null,
      responseState: "not_publicly_recorded"
    }
  };
  const EXPECTED_EVIDENCE_LAYER_IDS = [
    "statutory_sales",
    "excise_domestic_release",
    "customs_net_imports",
    "retail_or_shipments",
    "price_channel_bridge",
    "enforcement_signal"
  ];
  const EXPECTED_BVL_CHANNEL_URL = "https://www.bvl.bund.de/DE/Service/07_Kontakt/einleitung.html";
  const EXPECTED_BVL_GUIDANCE_URL = "https://www.bvl.bund.de/DE/Arbeitsbereiche/03_Verbraucherprodukte/03_AntragstellerUnternehmen/04_Tabakerzeugnisse_E-Zigaretten/01_Mitteilungspflicht/bgs_tabakerzeugnisse_mitteilungspflicht_node.html?thema=Mitteilungspflicht";
  const EXPECTED_TABAKERZV_25_URL = "https://www.gesetze-im-internet.de/tabakerzv/__25.html";
  const EXPECTED_SUPPLEMENTARY_DISPATCH = {
    "DE-BVL-TABAKERZV25-ANNUAL-SALES": {
      countryIso2: "DE",
      state: "sent",
      sentOn: "2026-07-24",
      publicAuthorityReference: null,
      responseState: "not_publicly_recorded"
    }
  };

  let programme = null;

  function isFi() {
    return window.SiteI18n?.isFinnish?.() ?? document.documentElement.lang === "fi";
  }

  function l(fi, en) {
    return window.SiteI18n?.pick?.(fi, en) ?? (isFi() ? fi : en);
  }

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function validOfficialHttps(value, allowedHosts) {
    try {
      const url = new URL(value);
      const hostname = url.hostname.toLowerCase();
      const officialHost = allowedHosts.some((suffix) => hostname === suffix || hostname.endsWith(`.${suffix}`));
      const sensitiveQuery = [...url.searchParams.keys()].some((key) => SENSITIVE_QUERY_KEYS.has(key.toLowerCase()));
      return url.protocol === "https:" && Boolean(hostname) && !url.username && !url.password
        && officialHost && !sensitiveQuery;
    } catch (_) {
      return false;
    }
  }

  function containsPrivateMetadataKey(value) {
    if (Array.isArray(value)) return value.some(containsPrivateMetadataKey);
    if (!value || typeof value !== "object") return false;
    return Object.entries(value).some(([key, item]) => {
      const normalized = key.toLowerCase().replace(/[^a-z]/g, "");
      return PRIVATE_METADATA_KEYS.has(normalized) || containsPrivateMetadataKey(item);
    });
  }

  function containsEmailAddress(value) {
    if (typeof value === "string") {
      return /\b[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+\b/i.test(value);
    }
    if (Array.isArray(value)) return value.some(containsEmailAddress);
    if (!value || typeof value !== "object") return false;
    return Object.values(value).some(containsEmailAddress);
  }

  function validIsoDate(value) {
    if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
    const [year, month, day] = value.split("-").map(Number);
    const parsed = new Date(Date.UTC(year, month - 1, day));
    return parsed.getUTCFullYear() === year
      && parsed.getUTCMonth() === month - 1
      && parsed.getUTCDate() === day;
  }

  function exactKeys(value, expected, label) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      throw new Error(`${label} must be an object`);
    }
    const actual = Object.keys(value).sort();
    const wanted = [...expected].sort();
    if (actual.length !== wanted.length || actual.some((key, index) => key !== wanted[index])) {
      throw new Error(`${label} has an unsupported schema`);
    }
  }

  function nonEmptyText(value) {
    return typeof value === "string" && Boolean(value.trim());
  }

  function textArray(value) {
    return Array.isArray(value) && value.length > 0 && value.every(nonEmptyText);
  }

  function validate(raw) {
    exactKeys(raw, [
      "schemaVersion", "programmeId", "verificationDate", "status",
      "independenceNoticeEn", "independenceNoticeFi", "ranking", "scope",
      "evidenceStack", "supplementaryRequests", "routes"
    ], "programme");
    if (!raw || raw.schemaVersion !== 3
      || raw.programmeId !== "pixan-independent-top20-official-data-request-programme-v3"
      || raw.status !== "partially_dispatched") {
      throw new Error("unsupported request programme");
    }
    if (!validIsoDate(raw.verificationDate)) {
      throw new Error("invalid verification date");
    }
    if (!raw.ranking || raw.ranking.type !== "operational_evidence_acquisition_order"
      || raw.ranking.isMarketSizeRanking !== false) {
      throw new Error("ranking boundary missing");
    }
    exactKeys(raw.ranking, ["type", "isMarketSizeRanking", "statementEn", "statementFi"], "ranking");
    exactKeys(raw.scope, [
      "period", "provisional2026En", "provisional2026Fi", "preferredFormats",
      "requestPrinciplesEn", "requestPrinciplesFi", "commonFieldsEn", "commonFieldsFi"
    ], "scope");
    if (![raw.programmeId, raw.independenceNoticeEn, raw.independenceNoticeFi,
      raw.scope.period, raw.scope.provisional2026En, raw.scope.provisional2026Fi].every(nonEmptyText)
      || ![raw.scope.preferredFormats, raw.scope.requestPrinciplesEn, raw.scope.requestPrinciplesFi,
        raw.scope.commonFieldsEn, raw.scope.commonFieldsFi].every(textArray)) {
      throw new Error("programme metadata has invalid field types");
    }
    if (containsPrivateMetadataKey(raw)) throw new Error("private correspondence metadata is forbidden");
    if (containsEmailAddress(raw)) throw new Error("email addresses are forbidden in public request tracking");
    const publicNotices = `${raw.independenceNoticeEn}\n${raw.independenceNoticeFi}`.toLowerCase();
    if (publicNotices.includes("no request has been sent")
      || publicNotices.includes("yhtäkään pyyntöä ei ole lähetetty")) {
      throw new Error("false all-draft claim");
    }
    if (!raw.independenceNoticeEn.toLowerCase().includes("privacy-safe categorical process state")
      || !raw.independenceNoticeEn.toLowerCase().includes("substantive data")
      || !raw.independenceNoticeEn.toLowerCase().includes("fee commitment")
      || !raw.independenceNoticeFi.toLowerCase().includes("tietosuojatun kategorisen prosessitilan")
      || !raw.independenceNoticeFi.toLowerCase().includes("sisällöllisenä datana")
      || !raw.independenceNoticeFi.toLowerCase().includes("maksusitoumuksena")) {
      throw new Error("process-response boundary is missing");
    }

    exactKeys(raw.evidenceStack, [
      "stateUniverseCount", "stateUniverseEn", "stateUniverseFi",
      "methodBoundaryEn", "methodBoundaryFi", "layers"
    ], "evidence stack");
    if (raw.evidenceStack.stateUniverseCount !== 195
      || ![raw.evidenceStack.stateUniverseEn, raw.evidenceStack.stateUniverseFi,
        raw.evidenceStack.methodBoundaryEn, raw.evidenceStack.methodBoundaryFi].every(nonEmptyText)
      || !Array.isArray(raw.evidenceStack.layers)
      || raw.evidenceStack.layers.length !== 6) {
      throw new Error("invalid 195-state evidence stack");
    }
    if (!raw.evidenceStack.methodBoundaryEn.toLowerCase().includes("locked to one evidence group")
      || !raw.evidenceStack.methodBoundaryEn.toLowerCase().includes("never mechanically added")
      || !raw.evidenceStack.methodBoundaryEn.toLowerCase().includes("reconciliation, uncertainty and confidence sit above all six layers")
      || !raw.evidenceStack.methodBoundaryEn.toLowerCase().includes("never converted to zero")
      || !raw.evidenceStack.methodBoundaryFi.toLowerCase().includes("lukitaan yhteen evidenssiryhmään")
      || !raw.evidenceStack.methodBoundaryFi.toLowerCase().includes("koskaan lasketa mekaanisesti yhteen")
      || !raw.evidenceStack.methodBoundaryFi.toLowerCase().includes("täsmäytys, epävarmuus ja luottamus ovat kaikkien kuuden kerroksen yläpuolinen menetelmä")
      || !raw.evidenceStack.methodBoundaryFi.toLowerCase().includes("eikä muutu nollaksi")) {
      throw new Error("evidence-stack reconciliation boundary is missing");
    }
    for (const [index, layer] of raw.evidenceStack.layers.entries()) {
      exactKeys(layer, [
        "order", "layerId", "titleEn", "titleFi", "purposeEn", "purposeFi",
        "outputEn", "outputFi"
      ], "evidence layer");
      if (layer.order !== index + 1 || layer.layerId !== EXPECTED_EVIDENCE_LAYER_IDS[index]
        || ![layer.titleEn, layer.titleFi, layer.purposeEn, layer.purposeFi,
          layer.outputEn, layer.outputFi].every(nonEmptyText)) {
        throw new Error("evidence-stack layer differs from the approved method");
      }
    }

    if (!Array.isArray(raw.supplementaryRequests)
      || raw.supplementaryRequests.length !== Object.keys(EXPECTED_SUPPLEMENTARY_DISPATCH).length) {
      throw new Error("supplementary request set differs from the approved public record");
    }
    const supplementaryIds = new Set();
    for (const request of raw.supplementaryRequests) {
      exactKeys(request, [
        "requestId", "countryIso2", "countsTowardCountryQueue", "status", "dispatch",
        "authority", "purposeEn", "purposeFi", "queueBoundaryEn", "queueBoundaryFi",
        "recordsRequestedEn", "recordsRequestedFi", "requestChannel", "legalBasis",
        "officialSources"
      ], "supplementary request");
      const expected = EXPECTED_SUPPLEMENTARY_DISPATCH[request.requestId];
      if (!expected || supplementaryIds.has(request.requestId)
        || request.countryIso2 !== expected.countryIso2
        || request.countsTowardCountryQueue !== false
        || request.status !== "sent") {
        throw new Error("unapproved supplementary request");
      }
      supplementaryIds.add(request.requestId);
      exactKeys(request.dispatch, ["state", "sentOn", "publicAuthorityReference", "responseState"], "supplementary dispatch");
      if (request.dispatch.state !== expected.state
        || request.dispatch.sentOn !== expected.sentOn
        || request.dispatch.publicAuthorityReference !== expected.publicAuthorityReference
        || request.dispatch.responseState !== expected.responseState
        || request.dispatch.state !== request.status
        || !validIsoDate(request.dispatch.sentOn)
        || request.dispatch.sentOn > raw.verificationDate) {
        throw new Error("supplementary dispatch differs from the approved public record");
      }
      exactKeys(request.authority, ["nameEn", "nameFi"], "supplementary authority");
      exactKeys(request.requestChannel, ["nameEn", "nameFi", "url"], "supplementary request channel");
      exactKeys(request.legalBasis, ["nameEn", "nameFi"], "supplementary legal basis");
      if (![request.requestId, request.countryIso2, request.purposeEn, request.purposeFi,
        request.queueBoundaryEn, request.queueBoundaryFi].every(nonEmptyText)
        || ![request.recordsRequestedEn, request.recordsRequestedFi].every(textArray)
        || !Object.values(request.authority).every(nonEmptyText)
        || !Object.values(request.requestChannel).every(nonEmptyText)
        || !Object.values(request.legalBasis).every(nonEmptyText)) {
        throw new Error("supplementary request metadata has invalid field types");
      }
      if (!request.queueBoundaryEn.toLowerCase().includes("adds no country")
        || !request.queueBoundaryEn.toLowerCase().includes("12-sent/8-draft")
        || !request.queueBoundaryFi.toLowerCase().includes("ei lisää maata")
        || !request.queueBoundaryFi.toLowerCase().includes("12 lähetetyn ja 8 luonnoksen")) {
        throw new Error("supplementary country-count boundary is missing");
      }
      const allowedHosts = OFFICIAL_HOSTS[request.countryIso2];
      if (!allowedHosts || !validOfficialHttps(request.requestChannel.url, allowedHosts)
        || !Array.isArray(request.officialSources) || request.officialSources.length < 2) {
        throw new Error("supplementary request lacks official source routes");
      }
      if (request.requestChannel.url !== EXPECTED_BVL_CHANNEL_URL) {
        throw new Error("BVL contact route differs from the verified source");
      }
      const sourceHosts = new Set([new URL(request.requestChannel.url).hostname.toLowerCase()]);
      const sourceUrls = new Set();
      for (const source of request.officialSources) {
        exactKeys(source, ["labelEn", "labelFi", "url", "verifiedOn"], "supplementary official source");
        if (![source.labelEn, source.labelFi, source.url, source.verifiedOn].every(nonEmptyText)
          || !validIsoDate(source.verifiedOn)
          || source.verifiedOn > raw.verificationDate
          || !validOfficialHttps(source.url, allowedHosts)) {
          throw new Error("invalid supplementary official source");
        }
        sourceHosts.add(new URL(source.url).hostname.toLowerCase());
        sourceUrls.add(source.url);
      }
      if (![...sourceHosts].some((host) => host === "bvl.bund.de" || host.endsWith(".bvl.bund.de"))
        || !sourceHosts.has("www.gesetze-im-internet.de")
        || sourceUrls.size !== 2
        || !sourceUrls.has(EXPECTED_BVL_GUIDANCE_URL)
        || !sourceUrls.has(EXPECTED_TABAKERZV_25_URL)) {
        throw new Error("BVL and section 25 official sources are required");
      }
    }
    if (!Array.isArray(raw.routes) || raw.routes.length !== 20) {
      throw new Error("expected exactly 20 routes");
    }

    const countries = new Set();
    const ranks = new Set();
    const sentCountries = new Set();
    const processResponseCountries = new Set();
    for (const route of raw.routes) {
      exactKeys(route, [
        "operationalRank", "priorityCode", "wave", "countryIso2", "countryEn", "countryFi",
        "status", "dispatch", "rationaleEn", "rationaleFi", "primaryAuthority", "recordsRequestedEn",
        "recordsRequestedFi", "requestChannel", "legalBasis", "languages",
        "requesterEligibility", "fallbackAuthority", "officialSources"
      ], "route");
      if (!route || !["sent", "draft_not_sent"].includes(route.status)
        || !/^[A-Z]{2}$/.test(route.countryIso2 || "")) {
        throw new Error("invalid route status or country");
      }
      exactKeys(route.dispatch, ["state", "sentOn", "publicAuthorityReference", "responseState"], "dispatch");
      const expectedDispatch = EXPECTED_DISPATCH[route.countryIso2] || {
        state: "draft_not_sent",
        sentOn: null,
        publicAuthorityReference: null,
        responseState: "not_applicable"
      };
      if (route.status !== route.dispatch.state
        || route.dispatch.state !== expectedDispatch.state
        || route.dispatch.sentOn !== expectedDispatch.sentOn
        || route.dispatch.publicAuthorityReference !== expectedDispatch.publicAuthorityReference
        || route.dispatch.responseState !== expectedDispatch.responseState) {
        throw new Error("dispatch tracking differs from the approved public record");
      }
      if (Object.hasOwn(PROCESS_RESPONSE_LABELS, route.dispatch.responseState)) {
        processResponseCountries.add(route.countryIso2);
        if (route.dispatch.publicAuthorityReference !== null) {
          throw new Error("process response cannot expose a correspondence reference");
        }
      }
      if (route.status === "sent") {
        sentCountries.add(route.countryIso2);
        if (!validIsoDate(route.dispatch.sentOn) || route.dispatch.sentOn > raw.verificationDate) {
          throw new Error("invalid public dispatch date");
        }
        if (route.dispatch.publicAuthorityReference !== null
          && !/^[A-Z0-9][A-Z0-9 ./_-]{2,39}$/.test(route.dispatch.publicAuthorityReference)) {
          throw new Error("unsafe public authority reference");
        }
      }
      if (!Number.isInteger(route.operationalRank) || route.operationalRank < 1 || route.operationalRank > 20) {
        throw new Error("invalid operational rank");
      }
      if (countries.has(route.countryIso2) || ranks.has(route.operationalRank)) {
        throw new Error("duplicate country or rank");
      }
      countries.add(route.countryIso2);
      ranks.add(route.operationalRank);
      const allowedHosts = OFFICIAL_HOSTS[route.countryIso2];
      if (!allowedHosts) throw new Error("country is outside the official-domain allowlist");
      exactKeys(route.primaryAuthority, ["nameEn", "nameFi"], "primary authority");
      exactKeys(route.requestChannel, ["nameEn", "nameFi", "url"], "request channel");
      exactKeys(route.legalBasis, ["nameEn", "nameFi"], "legal basis");
      exactKeys(route.requesterEligibility, ["localRequester", "caveatEn", "caveatFi"], "requester eligibility");
      exactKeys(route.fallbackAuthority, ["nameEn", "nameFi", "url"], "fallback authority");
      if (![route.priorityCode, route.wave, route.countryIso2, route.countryEn, route.countryFi,
        route.rationaleEn, route.rationaleFi].every(nonEmptyText)
        || ![route.recordsRequestedEn, route.recordsRequestedFi, route.languages].every(textArray)
        || !Object.values(route.primaryAuthority).every(nonEmptyText)
        || !Object.values(route.requestChannel).every(nonEmptyText)
        || !Object.values(route.legalBasis).every(nonEmptyText)
        || !Object.values(route.fallbackAuthority).every(nonEmptyText)
        || !Object.values(route.requesterEligibility).every(nonEmptyText)) {
        throw new Error("route metadata has invalid field types");
      }
      if (!route.requestChannel || !validOfficialHttps(route.requestChannel.url, allowedHosts)) {
        throw new Error("route lacks an official HTTPS channel");
      }
      if (!route.requesterEligibility
        || !["not_required", "recommended", "conditional", "required"].includes(route.requesterEligibility.localRequester)) {
        throw new Error("route has an unsupported requester-eligibility value");
      }
      if (!Array.isArray(route.officialSources) || route.officialSources.length === 0) {
        throw new Error("route lacks official sources");
      }
      const relatedUrls = [
        route.fallbackAuthority?.url,
        ...(route.officialSources || []).map((source) => source.url)
      ];
      if (!relatedUrls.length || relatedUrls.some((url) => !validOfficialHttps(url, allowedHosts))) {
        throw new Error("route lacks verified HTTPS fallback or source links");
      }
      for (const source of route.officialSources || []) {
        exactKeys(source, ["labelEn", "labelFi", "url", "verifiedOn"], "official source");
        if (!Object.values(source).every(nonEmptyText)) throw new Error("official source has invalid field types");
        if (!validIsoDate(source.verifiedOn) || source.verifiedOn > raw.verificationDate) {
          throw new Error("official source verification date is invalid or after programme verification");
        }
      }
    }
    if (countries.size !== Object.keys(OFFICIAL_HOSTS).length
      || Object.keys(OFFICIAL_HOSTS).some((iso) => !countries.has(iso))) {
      throw new Error("country set differs from the official-domain allowlist");
    }
    if (sentCountries.size !== 12 || Object.keys(EXPECTED_DISPATCH).some((iso) => !sentCountries.has(iso))) {
      throw new Error("sent country set differs from the approved 12-country public record");
    }
    if (processResponseCountries.size !== 4
      || !["DE", "FI", "DK", "SE"].every((iso) => processResponseCountries.has(iso))) {
      throw new Error("process-response country set differs from the approved four-country record");
    }
    return raw;
  }

  function metadata(label, value) {
    const row = element("li");
    row.append(element("span", "", label), element("strong", "", value));
    return row;
  }

  function processStatusText(responseState) {
    const label = PROCESS_RESPONSE_LABELS[responseState];
    if (label) return isFi() ? label.fi : label.en;
    return l("Ei julkista prosessivastausta kirjattu", "No public process response recorded");
  }

  function renderEvidenceStack() {
    const container = root.querySelector("[data-request-program-stack]");
    const stack = programme.evidenceStack;
    const header = element("div", "request-program-stack-head");
    const heading = element("div");
    heading.append(
      element("p", "eyebrow", l(
        "Maailmanlaajuinen tutkimusarkkitehtuuri",
        "Global research architecture"
      )),
      element("h3", "", l(
        `${stack.stateUniverseCount} valtiota · kuusi evidenssikerrosta`,
        `${stack.stateUniverseCount} states · six evidence layers`
      ))
    );
    header.append(
      heading,
      element("p", "", isFi() ? stack.stateUniverseFi : stack.stateUniverseEn)
    );

    const grid = element("div", "request-program-stack-grid");
    for (const layer of stack.layers) {
      const card = element("article", "request-program-stack-card");
      card.append(
        element("span", "request-program-stack-order", String(layer.order).padStart(2, "0")),
        element("h4", "", isFi() ? layer.titleFi : layer.titleEn),
        element("p", "", isFi() ? layer.purposeFi : layer.purposeEn),
        element("small", "", isFi() ? layer.outputFi : layer.outputEn)
      );
      grid.append(card);
    }

    const boundary = element(
      "p",
      "request-program-stack-boundary",
      isFi() ? stack.methodBoundaryFi : stack.methodBoundaryEn
    );
    container.replaceChildren(header, grid, boundary);
    container.hidden = false;
  }

  function renderSupplementaryRequest(request) {
    const panel = element("aside", "request-program-supplement");
    const head = element("div", "request-program-supplement-head");
    head.append(
      element("span", "request-program-supplement-label", l(
        "Täydentävä viranomaisreitti",
        "Supplementary authority route"
      )),
      element("span", "request-program-status request-program-status-sent", l("Lähetetty", "Sent"))
    );
    panel.append(
      head,
      element("strong", "", isFi() ? request.authority.nameFi : request.authority.nameEn),
      element("p", "request-program-supplement-purpose", isFi() ? request.purposeFi : request.purposeEn)
    );

    const meta = element("ul", "request-program-meta request-program-supplement-meta");
    meta.append(
      metadata(l("Lähetyspäivä", "Sent on"), request.dispatch.sentOn),
      metadata(
        l("Vaikutus maajonoon", "Country-queue effect"),
        l("Ei lisää maata tai muuta 12/8-laskureita", "Adds no country and does not change 12/8 counts")
      ),
      metadata(
        l("Vastaustila", "Response state"),
        processStatusText(request.dispatch.responseState)
      ),
      metadata(
        l("Oikeusperusta", "Legal basis"),
        isFi() ? request.legalBasis.nameFi : request.legalBasis.nameEn
      )
    );
    panel.append(meta);

    const records = element("details", "request-program-sources request-program-supplement-records");
    records.append(element("summary", "", l("Pyydetyt aggregaatit", "Requested aggregates")));
    const list = element("ul", "request-program-supplement-list");
    const requested = isFi() ? request.recordsRequestedFi : request.recordsRequestedEn;
    for (const item of requested) list.append(element("li", "", item));
    records.append(list);
    panel.append(records);

    const sources = element("details", "request-program-sources");
    sources.append(element("summary", "", l("Viralliset BVL- ja lakilähteet", "Official BVL and law sources")));
    const sourceLinks = element("div", "request-program-source-links");
    for (const source of request.officialSources) {
      const sourceLink = element("a", "", isFi() ? source.labelFi : source.labelEn);
      sourceLink.href = source.url;
      sourceLink.target = "_blank";
      sourceLink.rel = "noopener noreferrer";
      sourceLinks.append(sourceLink);
    }
    sources.append(sourceLinks);
    panel.append(sources);

    panel.append(element(
      "p",
      "request-program-caveat",
      isFi() ? request.queueBoundaryFi : request.queueBoundaryEn
    ));
    const channel = element(
      "a",
      "button button-secondary button-small request-program-link",
      l("Avaa BVL:n virallinen kanava", "Open BVL official channel")
    );
    channel.href = request.requestChannel.url;
    channel.target = "_blank";
    channel.rel = "noopener noreferrer";
    panel.append(channel);
    return panel;
  }

  function renderRoute(route) {
    const card = element("article", "request-program-card");
    card.dataset.wave = route.wave || "";
    card.dataset.local = route.requesterEligibility?.localRequester || "";
    card.dataset.status = route.status;

    const head = element("div", "request-program-card-head");
    const sent = route.status === "sent";
    head.append(
      element("span", "request-program-rank", `#${String(route.operationalRank).padStart(2, "0")} · ${route.priorityCode}`),
      element(
        "span",
        sent ? "request-program-status request-program-status-sent" : "request-program-status",
        sent ? l("Lähetetty", "Sent") : l("Luonnos — ei lähetetty", "Draft — not sent")
      )
    );

    const title = element("h3", "", isFi() ? route.countryFi : route.countryEn);
    const rationale = element("p", "request-program-rationale", isFi() ? route.rationaleFi : route.rationaleEn);
    const meta = element("ul", "request-program-meta");
    meta.append(
      metadata(
        l("Suunniteltu ensisijainen viranomainen", "Planned primary authority"),
        isFi() ? route.primaryAuthority.nameFi : route.primaryAuthority.nameEn
      ),
      metadata(
        l("Suunniteltu virallinen kanava", "Planned official channel"),
        isFi() ? route.requestChannel.nameFi : route.requestChannel.nameEn
      ),
      metadata(
        l("Pyyntökelpoisuus", "Requester eligibility"),
        route.requesterEligibility.localRequester === "required"
          ? l("Paikallinen pyytäjä vaaditaan", "Local requester required")
          : route.requesterEligibility.localRequester === "conditional"
            ? l("Kelpoisuus on rajattu", "Eligibility is restricted")
            : route.requesterEligibility.localRequester === "recommended"
              ? l("Paikallinen pyytäjä on suositeltava", "Local requester recommended")
              : l("Paikallista pyytäjää ei tunnistettu vaadittavan", "No local-requester requirement identified")
      )
    );
    if (sent) {
      meta.append(metadata(l("Julkinen lähetystieto", "Public dispatch record"), route.dispatch.sentOn));
      meta.append(metadata(
        l("Julkinen prosessitila", "Public process status"),
        processStatusText(route.dispatch.responseState)
      ));
      if (route.dispatch.publicAuthorityReference) {
        meta.append(metadata(
          l("Julkinen viranomaisviite", "Public authority reference"),
          route.dispatch.publicAuthorityReference
        ));
      }
    }

    const caveat = element(
      "p",
      "request-program-caveat",
      isFi() ? route.requesterEligibility.caveatFi : route.requesterEligibility.caveatEn
    );
    const sources = element("details", "request-program-sources");
    sources.append(element("summary", "", l("Lähteet ja varareitti", "Sources and fallback")));
    const sourceLinks = element("div", "request-program-source-links");
    const fallback = element(
      "a",
      "",
      isFi() ? route.fallbackAuthority.nameFi : route.fallbackAuthority.nameEn
    );
    fallback.href = route.fallbackAuthority.url;
    fallback.target = "_blank";
    fallback.rel = "noopener noreferrer";
    sourceLinks.append(fallback);
    for (const source of route.officialSources) {
      const sourceLink = element("a", "", isFi() ? source.labelFi : source.labelEn);
      sourceLink.href = source.url;
      sourceLink.target = "_blank";
      sourceLink.rel = "noopener noreferrer";
      sourceLinks.append(sourceLink);
    }
    sources.append(sourceLinks);
    const link = element(
      "a",
      "button button-secondary button-small request-program-link",
      l("Avaa suunniteltu virallinen kanava", "Open planned official channel")
    );
    link.href = route.requestChannel.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";

    const supplements = programme.supplementaryRequests.filter(
      (request) => request.countryIso2 === route.countryIso2
    );
    card.append(head, title, rationale, meta, caveat);
    card.append(...supplements.map(renderSupplementaryRequest), sources, link);
    return card;
  }

  function renderSectionCopy(routes) {
    const sentCount = routes.filter((route) => route.status === "sent").length;
    const draftCount = routes.length - sentCount;
    const processResponseCount = routes.filter(
      (route) => Object.hasOwn(PROCESS_RESPONSE_LABELS, route.dispatch.responseState)
    ).length;
    const supplementarySentCount = programme.supplementaryRequests.filter(
      (request) => request.status === "sent"
    ).length;
    root.querySelector("[data-request-program-kicker]").textContent = l(
      "Maailmanlaajuinen evidenssihankinta · julkinen reittiseuranta",
      "Global evidence acquisition · public route tracking"
    );
    root.querySelector("[data-request-program-title]").textContent = l(
      "195 valtion evidenssipino ja 20 maan tietopyyntöjono",
      "195-state evidence stack and 20-country request queue"
    );
    root.querySelector("[data-request-program-intro]").textContent = l(
      "Kaikille suvereeneille valtioille uudelleenkäytettävä kuusikerroksinen menetelmä sekä ensimmäiset 20 maareittiä priorisoituina evidenssin operatiivisen saatavuuden, ei markkinakoon, mukaan.",
      "A reusable six-layer method for all sovereign states, with the first 20 country routes prioritised for operational evidence access—not national market size."
    );
    const boundary = root.querySelector("[data-request-program-boundary]");
    boundary.setAttribute(
      "aria-label",
      l("Tietopyyntöjen tilaraja", "Data-request status boundary")
    );
    root.querySelector("[data-request-program-boundary-mark]").textContent = l("TILA", "STATUS");
    root.querySelector("[data-request-program-boundary-summary]").textContent = l(
      `${sentCount} maareittiä lähetetty · ${draftCount} maaluonnosta · ${supplementarySentCount} täydentävä Saksan reitti lähetetty · ${processResponseCount} prosessivastausta · 0 sisällöllistä viranomaisdatavastausta`,
      `${sentCount} country routes sent · ${draftCount} country drafts · ${supplementarySentCount} supplementary German route sent · ${processResponseCount} process responses · 0 substantive authority-data responses`
    );
    root.querySelector("[data-request-program-boundary-copy]").textContent = l(
      "Täydentävä BVL-pyyntö kuuluu Saksaan eikä lisää maata tai korvaa tullin/Destatisin prosessitietoa. Julkiset kategoriset prosessitilat eivät ole sisällöllisiä datavastauksia eivätkä osoita markkina-arvoa. Maksua ei ole hyväksytty. Ladattavat mallipohjat säilyvät LUONNOS — EI LÄHETETTY -tilassa.",
      "The supplementary BVL request is part of Germany and does not add a country or replace the Customs/Destatis process record. Public categorical process states are not substantive data responses and establish no market value. No fee has been accepted. Downloadable templates remain DRAFT — NOT SENT."
    );
    root.querySelector("[data-request-program-note]").textContent = l(
      "Kuusi evidenssikerrosta ovat vaihtoehtoisia ja toisiaan tarkistavia. Vero-, myynti-, tulli-, toimitus- ja takavarikkosarjoja ei saa laskea mekaanisesti yhteen; takavarikot eivät ole laillista myyntiä.",
      "The six evidence layers are alternatives and cross-checks. Tax, sales, customs, shipment and seizure series must not be added mechanically; seizures are not lawful sales."
    );
  }

  function renderReady() {
    root.querySelector("[data-request-program-boundary]").hidden = false;
    root.querySelector("[data-request-program-actions]").hidden = false;
    root.querySelector("[data-request-program-note]").hidden = false;
    const routes = [...programme.routes].sort((left, right) => left.operationalRank - right.operationalRank);
    renderSectionCopy(routes);
    renderEvidenceStack();
    const grid = root.querySelector("[data-request-program-routes]");
    grid.replaceChildren(...routes.map(renderRoute));
    grid.hidden = false;

    const status = root.querySelector("[data-request-program-status]");
    const sentCount = routes.filter((route) => route.status === "sent").length;
    const draftCount = routes.length - sentCount;
    const processResponseCount = routes.filter(
      (route) => Object.hasOwn(PROCESS_RESPONSE_LABELS, route.dispatch.responseState)
    ).length;
    const supplementarySentCount = programme.supplementaryRequests.filter(
      (request) => request.status === "sent"
    ).length;
    status.className = "bank-package-status bank-package-status-ready";
    status.replaceChildren(
      element("span", "bank-package-status-dot", ""),
      element("span", "", l(
        `${sentCount} maareittiä lähetetty · ${draftCount} maaluonnosta · ${supplementarySentCount} täydentävä pyyntö lähetetty · ${processResponseCount} prosessivastausta · 0 sisällöllistä datavastausta · tarkistettu ${programme.verificationDate}.`,
        `${sentCount} country routes sent · ${draftCount} country drafts · ${supplementarySentCount} supplementary request sent · ${processResponseCount} process responses · 0 substantive data responses · verified ${programme.verificationDate}.`
      ))
    );
    status.firstElementChild.setAttribute("aria-hidden", "true");
    root.setAttribute("aria-busy", "false");
  }

  function renderFailure() {
    root.querySelector("[data-request-program-boundary]").hidden = true;
    root.querySelector("[data-request-program-actions]").hidden = true;
    root.querySelector("[data-request-program-note]").hidden = true;
    root.querySelector("[data-request-program-stack]").hidden = true;
    const status = root.querySelector("[data-request-program-status]");
    status.className = "bank-package-status bank-package-status-error";
    status.replaceChildren(
      element("span", "bank-package-status-dot", ""),
      element("strong", "", l("Virallisia reittejä ei voitu ladata.", "Official request routes could not be loaded."))
    );
    status.firstElementChild.setAttribute("aria-hidden", "true");
    root.querySelector("[data-request-program-routes]").hidden = true;
    root.setAttribute("aria-busy", "false");
  }

  async function init() {
    try {
      const response = await fetch("data/top20-data-request-routes.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      programme = validate(await response.json());
      renderReady();
    } catch (error) {
      console.warn("Official data-request programme unavailable", error);
      renderFailure();
    }
  }

  document.addEventListener("pixan:languagechange", () => {
    if (programme) renderReady();
  });
  init();
})();
