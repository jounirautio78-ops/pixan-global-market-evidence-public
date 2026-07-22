"use strict";

(() => {
  const root = document.querySelector("[data-request-program]");
  if (!root) return;

  const OFFICIAL_HOSTS = {
    DE: ["bund.de", "destatis.de", "zoll.de"],
    CA: ["canada.ca"],
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
  const EXPECTED_DISPATCH = {
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
      responseState: "not_publicly_recorded"
    },
    PL: {
      state: "sent",
      sentOn: "2026-07-22",
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
      "independenceNoticeEn", "independenceNoticeFi", "ranking", "scope", "routes"
    ], "programme");
    if (!raw || raw.schemaVersion !== 2 || raw.status !== "partially_dispatched") {
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
    const publicNotices = `${raw.independenceNoticeEn}\n${raw.independenceNoticeFi}`.toLowerCase();
    if (publicNotices.includes("no request has been sent")
      || publicNotices.includes("yhtäkään pyyntöä ei ole lähetetty")) {
      throw new Error("false all-draft claim");
    }
    if (!Array.isArray(raw.routes) || raw.routes.length !== 20) {
      throw new Error("expected exactly 20 routes");
    }

    const countries = new Set();
    const ranks = new Set();
    const sentCountries = new Set();
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
        if (source.verifiedOn !== raw.verificationDate) throw new Error("official source verification date differs");
      }
    }
    if (countries.size !== Object.keys(OFFICIAL_HOSTS).length
      || Object.keys(OFFICIAL_HOSTS).some((iso) => !countries.has(iso))) {
      throw new Error("country set differs from the official-domain allowlist");
    }
    if (sentCountries.size !== 3 || Object.keys(EXPECTED_DISPATCH).some((iso) => !sentCountries.has(iso))) {
      throw new Error("sent country set must be exactly FI, GB and PL");
    }
    return raw;
  }

  function metadata(label, value) {
    const row = element("li");
    row.append(element("span", "", label), element("strong", "", value));
    return row;
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

    card.append(head, title, rationale, meta, caveat, sources, link);
    return card;
  }

  function renderReady() {
    root.querySelector("[data-request-program-boundary]").hidden = false;
    root.querySelector("[data-request-program-actions]").hidden = false;
    root.querySelector("[data-request-program-note]").hidden = false;
    const grid = root.querySelector("[data-request-program-routes]");
    const routes = [...programme.routes].sort((left, right) => left.operationalRank - right.operationalRank);
    grid.replaceChildren(...routes.map(renderRoute));
    grid.hidden = false;

    const status = root.querySelector("[data-request-program-status]");
    const sentCount = routes.filter((route) => route.status === "sent").length;
    const draftCount = routes.length - sentCount;
    status.className = "bank-package-status bank-package-status-ready";
    status.replaceChildren(
      element("span", "bank-package-status-dot", ""),
      element("span", "", l(
        `${sentCount} lähetetty · ${draftCount} luonnosta · tarkistettu ${programme.verificationDate}.`,
        `${sentCount} sent · ${draftCount} drafts · verified ${programme.verificationDate}.`
      ))
    );
    status.firstElementChild.setAttribute("aria-hidden", "true");
    root.setAttribute("aria-busy", "false");
  }

  function renderFailure() {
    root.querySelector("[data-request-program-boundary]").hidden = true;
    root.querySelector("[data-request-program-actions]").hidden = true;
    root.querySelector("[data-request-program-note]").hidden = true;
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
