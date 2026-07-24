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
const REVIEW_STRUCTURAL_RESPONSE_COUNTRIES = new Set(["SE"]);

let reviewData = null;
let reviewMarketData = null;
let reviewDonorCockpit = null;
let reviewCountryScenarios = null;
let reviewFxData = null;
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

const REVIEW_VIEWS = new Set(["review", "operations"]);

function currentReviewView() {
  const requested = new URL(location.href).searchParams.get("view");
  return REVIEW_VIEWS.has(requested) ? requested : "review";
}

function applyReviewView() {
  const view = currentReviewView();
  document.body.dataset.reviewView = view;

  for (const section of document.querySelectorAll("[data-review-surface]")) {
    const surface = section.dataset.reviewSurface;
    section.hidden = surface !== "shared" && surface !== view;
  }

  for (const link of document.querySelectorAll("[data-review-view-link]")) {
    const active = link.dataset.reviewViewLink === view;
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }

  const url = new URL(location.href);
  if (url.searchParams.get("view") !== view) {
    url.searchParams.set("view", view);
    history.replaceState(history.state, "", `${url.pathname}${url.search}${url.hash}`);
  }

  const isOperations = view === "operations";
  document.title = isOperations
    ? reviewL("Tutkimusoperaatiot | Pixan Global Market Evidence", "Research Operations | Pixan Global Market Evidence")
    : reviewL("Lainanantajan ja ostajan tarkistus | Pixan Global Market Evidence", "Lender & Buyer Review | Pixan Global Market Evidence");
  const description = document.querySelector('meta[name="description"]');
  if (description) {
    description.content = isOperations
      ? reviewL(
        "Riippumaton tutkimusoperaatioiden näkymä Pixaniin liittyvän globaalin sähkötupakkamarkkinan evidenssin hankintaan.",
        "Independent research-operations view for acquiring Pixan-related global vaping-market evidence."
      )
      : reviewL(
        "Riippumaton, lähteistetty tarkistusmuistio Pixaniin liittyvästä maailmanlaajuisesta sähkötupakkamarkkinaevidenssistä.",
        "Independent, source-linked review brief for Pixan-related global vaping-market evidence."
      );
  }
}

function reviewNumber(value, maximumFractionDigits = 2) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  return new Intl.NumberFormat(reviewIsFi() ? "fi-FI" : "en-GB", {
    maximumFractionDigits
  }).format(number);
}

function reviewOfficialMarketSummary() {
  const observations = Array.isArray(reviewMarketData?.observations) ? reviewMarketData.observations : [];
  const official = observations.filter((item) => String(item.evidenceStatus || "").startsWith("official_"));
  const numericCountries = new Set(official.map((item) => item.countryIso2).filter(Boolean));
  const officialRetailCountries = new Set(
    official
      .filter((item) => ["consumer_retail_market_value", "statcan_rcs_vaping_retail_sales"].includes(item.metric))
      .map((item) => item.countryIso2)
      .filter(Boolean)
  );
  const officialRetailLowerBoundCountries = new Set(
    official
      .filter((item) => item.metric === "official_specialist_retail_sales_lower_bound")
      .map((item) => item.countryIso2)
      .filter(Boolean)
  );
  return { official, numericCountries, officialRetailCountries, officialRetailLowerBoundCountries };
}

function assessReviewDonorLedger(market = reviewMarketData) {
  const protocol = market?.donorProtocol;
  const criteria = Array.isArray(protocol?.criteria) ? protocol.criteria : [];
  const criterionIds = criteria.map((item) => String(item?.criterionId || "").trim());
  const protocolValid = Boolean(
    protocol
    && String(protocol.protocolVersion || "").trim()
    && criteria.length
    && criterionIds.every(Boolean)
    && new Set(criterionIds).size === criterionIds.length
    && criteria.every((item) => String(item.titleEn || "").trim() && String(item.titleFi || "").trim()
      && String(item.requirementEn || "").trim() && String(item.requirementFi || "").trim())
  );
  const knownIds = new Set(criterionIds);
  const sources = new Map((market?.sources || []).map((item) => [item.sourceId, item]));
  const observations = new Set((market?.observations || []).map((item) => item.observationId));
  const models = new Set((market?.models || []).map((item) => item.modelId));
  const candidates = (Array.isArray(market?.donorCandidates) ? market.donorCandidates : []).map((candidate) => {
    const passedRaw = Array.isArray(candidate?.passedCriteria) ? candidate.passedCriteria : [];
    const failedRaw = Array.isArray(candidate?.failedCriteria) ? candidate.failedCriteria : [];
    const openRaw = Array.isArray(candidate?.openCriteria) ? candidate.openCriteria : [];
    const passed = new Set(passedRaw);
    const failed = new Set(failedRaw);
    const open = new Set(openRaw);
    const allReportedIds = [...passedRaw, ...failedRaw, ...openRaw];
    const duplicateIds = [...new Set(allReportedIds.filter((id, index) => allReportedIds.indexOf(id) !== index))];
    const unknownIds = [...new Set(allReportedIds.filter((id) => !knownIds.has(id)))];
    const conflictingIds = criterionIds.filter((id) => [passed.has(id), failed.has(id), open.has(id)].filter(Boolean).length > 1);
    const criterionResults = criteria.map((criterion) => {
      const id = criterion.criterionId;
      const status = failed.has(id) ? "failed" : open.has(id) ? "open" : passed.has(id) ? "passed" : "open";
      return { criterion, status };
    });
    const allCriteriaPassed = protocolValid
      && criterionResults.length === criteria.length
      && criterionResults.every((item) => item.status === "passed")
      && !duplicateIds.length
      && !unknownIds.length
      && !conflictingIds.length;
    const referenceValid = candidate?.referenceType === "observation"
      ? observations.has(candidate.referenceId)
      : candidate?.referenceType === "model"
        ? models.has(candidate.referenceId)
        : false;
    const sourceIds = Array.isArray(candidate?.sourceIds) ? [...new Set(candidate.sourceIds.filter(Boolean))] : [];
    const sourcesResolve = sourceIds.length > 0 && sourceIds.every((sourceId) => {
      const source = sources.get(sourceId);
      return Boolean(source && reviewUrl(source.pageUrl || source.downloadUrl));
    });
    const recordValid = Boolean(
      String(candidate?.candidateId || "").trim()
      && String(candidate?.geography || "").trim()
      && Number.isFinite(Number(candidate?.year))
      && ["accepted", "not_accepted"].includes(candidate?.decision)
      && Array.isArray(candidate?.passedCriteria)
      && Array.isArray(candidate?.failedCriteria)
      && Array.isArray(candidate?.openCriteria)
      && referenceValid
      && sourcesResolve
    );
    const accepted = protocolValid && recordValid && candidate.decision === "accepted" && allCriteriaPassed;
    return {
      candidate,
      criterionResults,
      duplicateIds,
      unknownIds,
      conflictingIds,
      referenceValid,
      sourcesResolve,
      recordValid,
      allCriteriaPassed,
      accepted
    };
  });
  return {
    protocol,
    criteria,
    protocolValid,
    candidates,
    accepted: candidates.filter((item) => item.accepted),
    sources
  };
}

function reviewRequestSummary() {
  const routes = Array.isArray(reviewRequestData?.routes) ? reviewRequestData.routes : [];
  const sent = routes.filter((route) => route.status === "sent").length;
  const drafts = routes.filter((route) => route.status === "draft_not_sent").length;
  const responseRecorded = (route) => {
    const state = route.dispatch?.responseState;
    return typeof state === "string" && !["not_publicly_recorded", "not_applicable"].includes(state);
  };
  const officialStructuralResponses = routes.filter(
    (route) => route.status === "sent"
      && responseRecorded(route)
      && REVIEW_STRUCTURAL_RESPONSE_COUNTRIES.has(route.countryIso2)
  ).length;
  const processResponses = routes.filter((route) => {
    return responseRecorded(route)
      && !REVIEW_STRUCTURAL_RESPONSE_COUNTRIES.has(route.countryIso2);
  }).length;
  const germanSupplements = (reviewRequestData?.supplementaryRequests || []).filter(
    (request) => request.countryIso2 === "DE"
      && request.status === "sent"
      && request.countsTowardCountryQueue === false
  ).length;
  return {
    routes: routes.length,
    sent,
    drafts,
    germanSupplements,
    processResponses,
    officialStructuralResponses,
    salesResponses: 0
  };
}

function renderDecisionCockpit(data) {
  const root = reviewById("decision-cockpit");
  const state = reviewById("decision-cockpit-state");
  const supportedHost = reviewById("cockpit-supported-list");
  const unsupportedHost = reviewById("cockpit-not-supported-list");
  const gatesHost = reviewById("cockpit-gates-list");
  if (!root || !state || !supportedHost || !unsupportedHost || !gatesHost) return;

  const market = reviewOfficialMarketSummary();
  const request = reviewRequestSummary();
  const nationalRights = (reviewPatentData?.familyMembers || []).filter(
    (item) => item.verificationLevel === "official_national_record"
  ).length;
  const evidenceCount = Array.isArray(data.evidence) ? data.evidence.length : null;
  const familyCount = reviewPatentData?.summary?.familyRecordCount;
  const blockers = Array.isArray(data.readiness?.blockers) ? data.readiness.blockers.slice(0, 3) : [];
  const lenderReady = data.readiness?.lenderReady === true;

  state.dataset.state = lenderReady ? "review" : "hold";
  state.textContent = lenderReady
    ? reviewL("VALMIS RIIPPUMATTOMAAN TARKASTUKSEEN", "READY FOR INDEPENDENT REVIEW")
    : reviewL("HOLD · tutkimusaineisto, ei arvonmääritys", "HOLD · research dataset, not a valuation");

  const supported = [
    reviewL(
      `${data.countries.length} maan tutkimusuniversumi ja ${evidenceCount ?? "—"} lähteistettyä evidenssiriviä; peitto ei tarkoita mitattua markkinaa.`,
      `${data.countries.length}-country research universe and ${evidenceCount ?? "—"} source-linked evidence records; coverage is not a measured market.`
    ),
    reviewMarketData
      ? reviewL(
        `Virallista vuosittaista numeerista evidenssiä ${market.numericCountries.size} maasta; täydellisiä virallisia kuluttajavähittäisarvoja ${market.officialRetailCountries.size} ja virallisia vähittäismyynnin alaraja-ankkureita ${market.officialRetailLowerBoundCountries.size}.`,
        `Official annual numeric evidence across ${market.numericCountries.size} countries; ${market.officialRetailCountries.size} complete official consumer-retail values and ${market.officialRetailLowerBoundCountries.size} official retail lower-bound anchors.`
      )
      : reviewL("Markkina-arvon tukiaineisto ei ole saatavilla.", "The market-value supporting dataset is unavailable."),
    reviewPatentData
      ? reviewL(
        `${familyCount ?? "—"} patenttiperheriviä ja ${nationalRights} kansallisesti vahvistettua statustietuetta, erillään prosessi- ja arvoväitteistä.`,
        `${familyCount ?? "—"} patent-family records and ${nationalRights} nationally verified status records, kept separate from proceeding and value claims.`
      )
      : reviewL("Patenttihistorian tukiaineisto ei ole saatavilla.", "The patent-history supporting dataset is unavailable."),
    reviewRequestData
      ? reviewL(
        `${request.routes} viranomaisreittiä: ${request.sent} lähetetty, ${request.drafts} luonnosta, ${request.germanSupplements} täydentävä Saksan reitti, ${request.processResponses} vain prosessivastausta, ${request.officialStructuralResponses} virallinen rakennevastaus ja ${request.salesResponses} myyntidatavastausta.`,
        `${request.routes} authority routes: ${request.sent} sent, ${request.drafts} drafts, ${request.germanSupplements} supplementary German route, ${request.processResponses} process-only responses, ${request.officialStructuralResponses} official structural response and ${request.salesResponses} sales-data responses.`
      )
      : reviewL("Viranomaisreittien tukiaineisto ei ole saatavilla.", "The authority-route supporting dataset is unavailable.")
  ];
  supportedHost.replaceChildren(...supported.map((text) => reviewNode("li", "", text)));

  const unsupported = [
    reviewL("Täydellinen maailmanlaajuinen vuosittainen kuluttajavähittäismyynti.", "A complete global annual consumer-retail sales total."),
    reviewL("Pixanin yritys-, osake-, vakuus- tai patenttiarvo.", "Pixan's enterprise, equity, collateral or patent value."),
    reviewL("Loukkaukset viitattujen ratkaisujen osapuolten, tuotteiden, alueiden tai ajanjaksojen ulkopuolella.", "Infringement outside the parties, products, territories or periods addressed by the cited decisions."),
    reviewL("Perittävissä olevat korvaukset, lisenssituotot tai toteutunut kassavirta.", "Recoverable damages, licensing revenue or realised cash flow.")
  ];
  unsupportedHost.replaceChildren(...unsupported.map((text) => reviewNode("li", "", text)));

  gatesHost.replaceChildren();
  if (blockers.length === 3) {
    for (const blocker of blockers) {
      const label = reviewIsFi()
        ? REVIEW_BLOCKER_FI[blocker] || blocker
        : REVIEW_BLOCKER_TRANSLATIONS[blocker] || reviewL("Avoin evidenssiportti.", "Open evidence gate.");
      gatesHost.append(reviewNode("li", "", label));
    }
  } else {
    gatesHost.append(reviewNode("li", "", reviewL("Valmiusportteja ei voitu vahvistaa aineistosta.", "Readiness gates could not be verified from the dataset.")));
  }

  const meta = reviewById("cockpit-meta");
  if (meta) {
    const donorAssessment = assessReviewDonorLedger();
    const donors = donorAssessment.protocolValid ? donorAssessment.accepted.length : 0;
    const required = reviewMarketData?.meta?.modelReadiness?.minimumRequiredDonors;
    meta.textContent = reviewMarketData
      ? reviewL(
        `Maailmanestimaatin luovuttajaportti ${donors}/${required} · maailmanestimaattia ei julkaistu`,
        `Global-estimate donor gate ${donors}/${required} · no global estimate published`
      )
      : reviewL("Luovuttajaportti ei ole saatavilla.", "Donor gate unavailable.");
  }

  root.setAttribute("aria-busy", "false");
  const live = reviewById("decision-cockpit-status");
  if (live) live.textContent = reviewL("Päätöksentekonäkymä päivitetty tarkistetusta aineistosta.", "Decision Cockpit updated from the reviewed dataset.");
}

function renderResearchOperationsOverview() {
  const host = reviewById("research-operations-metrics");
  if (!host) return;
  if (!reviewRequestData) {
    const unavailable = reviewNode("article", "metric-card");
    unavailable.append(
      reviewNode("span", "", reviewL("Viranomaisreitit", "Authority routes")),
      reviewNode("strong", "", reviewL("Ei saatavilla", "Unavailable")),
      reviewNode("small", "", reviewL("Puuttuvaa tilaa ei käsitellä nollana.", "Missing status is not treated as zero."))
    );
    host.replaceChildren(unavailable);
    return;
  }
  const request = reviewRequestSummary();
  const metrics = [
    [reviewL("Lähetetty / luonnos", "Sent / draft"), `${request.sent} / ${request.drafts}`, reviewL("20 maan priorisoitu tutkimusjono", "Prioritised 20-country research queue")],
    [reviewL("Täydentävä Saksan reitti", "German supplementary route"), request.germanSupplements, reviewL("Ei lisää maata 12/8-laskureihin", "Adds no country to the 12/8 counts")],
    [reviewL("Vain prosessi / rakenne / myynti", "Process-only / structural / sales"), `${request.processResponses} / ${request.officialStructuralResponses} / ${request.salesResponses}`, reviewL("Ruotsin rakennetieto ei ole myyntiä, arvoa tai volyymia", "Sweden structural evidence is not sales, value or volume")],
    [reviewL("Ostovaltuudet", "Purchase authorisations"), 0, reviewL("Ei ostoa, tilausta tai automaattista ulkoista toimintoa", "No purchase, subscription or automatic external action")]
  ];
  host.replaceChildren(...metrics.map(([label, value, note]) => {
    const card = reviewNode("article", "metric-card");
    card.append(reviewNode("span", "", label), reviewNode("strong", "", value), reviewNode("small", "", note));
    return card;
  }));
}

const REVIEW_EXCLUSION_LABELS = {
  devices: ["laitteet", "devices"],
  pods_and_cartridges_as_separate_hardware_value: ["podit ja patruunat erillisenä laitearvona", "pods and cartridges as separate hardware value"],
  illicit_and_untaxed_sales: ["laiton ja verottamaton myynti", "illicit and untaxed sales"],
  nicotine_free_products_where_not_taxed: ["nikotiinittomat tuotteet silloin, kun niitä ei veroteta", "nicotine-free products where untaxed"],
  wholesale_retail_margin_mix: ["tukku- ja vähittäiskatteen jakauma", "wholesale and retail margin mix"],
  discount_and_channel_mix: ["alennus- ja kanavajakauma", "discount and channel mix"]
};

function reviewObservationLink(observation, sourceMap) {
  const wrap = reviewNode("span", "calculation-source-links");
  for (const sourceId of observation?.sourceIds || []) {
    const source = sourceMap.get(sourceId);
    const url = reviewUrl(source?.pageUrl);
    if (!url) continue;
    const link = reviewNode("a", "", sourceId);
    link.href = url;
    link.target = "_blank";
    link.rel = "noreferrer";
    wrap.append(link);
  }
  return wrap;
}

function renderReviewCalculationAudit(market) {
  const root = reviewById("review-calculation-audit");
  const status = reviewById("review-calculation-audit-status");
  const summary = reviewById("review-calculation-audit-summary");
  const steps = reviewById("review-calculation-audit-steps");
  if (!root || !status || !summary || !steps) return;

  const observations = Array.isArray(market?.observations) ? market.observations : [];
  const observationMap = new Map(observations.map((item) => [item.observationId, item]));
  const sourceMap = new Map((market?.sources || []).map((item) => [item.sourceId, item]));
  const model = (market?.models || []).find((item) => item.modelId === "DE-2025-LIQUID-RETAIL-EQUIVALENT-RANGE");
  const canadaRetail = observationMap.get("CA-2024-STATCAN-RCS-VAPING-RETAIL-SALES");
  const canadaShipment = observationMap.get("CA-2024-MANUFACTURER-IMPORTER-SHIPMENTS-VALUE");
  const volume = observationMap.get("DE-2025-TAXED-LIQUID-VOLUME-L");
  const scenarios = ["low", "central", "high"].map((name) => {
    const inputId = model?.rangeInputMap?.[name];
    return { name, observation: observationMap.get(inputId) };
  });
  const exactFormula = model?.formula === "volume_litres * 1000 * retail_price_eur_per_ml";
  const inputsResolve = model && volume && scenarios.every((item) => item.observation);
  const computed = inputsResolve
    ? Object.fromEntries(scenarios.map((item) => [item.name, Number(volume.value) * 1000 * Number(item.observation.value)]))
    : {};
  const arithmeticPass = exactFormula
    && inputsResolve
    && scenarios.every(
      (item) => Number.isFinite(computed[item.name])
        && Math.abs(computed[item.name] - Number(model[item.name])) < 0.01
    )
    && model.yearMismatch === true
    && Number(volume.year) !== Number(scenarios[0].observation.year);

  root.setAttribute("aria-busy", "false");
  summary.replaceChildren();
  steps.replaceChildren();
  if (!arithmeticPass) {
    status.dataset.state = "error";
    status.textContent = reviewL("Laskentaketju hylätty: syötteet, kaava tai julkaistut tulokset eivät täsmää.", "Calculation waterfall rejected: inputs, formula or published outputs do not reconcile.");
    summary.append(reviewNode("p", "review-audit-error", reviewL("Älä käytä mallin tuloksia ennen lähdedatan korjaamista ja uutta validointia.", "Do not use the model outputs until the source data is corrected and revalidated.")));
    return;
  }

  status.dataset.state = "caution";
  status.textContent = reviewL("Laskenta täsmää · mallinnettu, ei havaittu myynti · matala luottamus", "Arithmetic reconciles · modelled, not observed sales · low confidence");

  const boundary = reviewNode("article", "calculation-boundary");
  boundary.append(
    reviewNode("span", "kicker", reviewL("Johtopäätöksen tila", "Claim state")),
    reviewNode("strong", "", reviewL("Vähittäismyyntivastaavuuden suuntaa-antava vaihteluväli", "Retail-equivalent plausibility range")),
    reviewNode("p", "", reviewIsFi() ? model.limitationFi : model.limitationEn)
  );
  const donor = reviewNode("article", "calculation-boundary");
  donor.append(
    reviewNode("span", "kicker", reviewL("Maailmanestimaatin portti", "Global-estimate gate")),
    reviewNode("strong", "", `${market.meta.modelReadiness.comparableFullYearMarketValueDonors}/${market.meta.modelReadiness.minimumRequiredDonors}`),
    reviewNode("p", "", reviewL("Saksan malli ei ole vertailukelpoinen luovuttajamarkkina eikä sitä summata muihin mittareihin.", "The Germany model is not a comparable donor market and is not added to other measures."))
  );
  summary.append(boundary, donor);

  if (canadaRetail && canadaShipment) {
    const bridgeDifference = Number(canadaRetail.value) - Number(canadaShipment.value);
    const bridgeRatio = Number(canadaRetail.value) / Number(canadaShipment.value);
    const direct = reviewNode("article", "panel calculation-audit-card calculation-audit-facts");
    direct.append(
      reviewNode("span", "calculation-kind", reviewL("FAKTA + LASKELMA · kaksi riippumatonta viranomaisreittiä", "FACT + CALCULATION · two independent official routes")),
      reviewNode("h3", "", reviewL("Kanada 2024 · retail–toimitus-silta", "Canada 2024 · retail-to-shipment bridge")),
      reviewNode("strong", "", `${reviewMarketFormat(canadaRetail.value, canadaRetail.currency)} − ${reviewMarketFormat(canadaShipment.value, canadaShipment.currency)} = ${reviewMarketFormat(bridgeDifference, canadaRetail.currency)}`),
      reviewNode("code", "", `RCS / Health Canada = ${bridgeRatio.toFixed(6)} · +${((bridgeRatio - 1) * 100).toFixed(2)}%`)
    );
    const canadaEur = reviewEurEquivalentNode(canadaRetail);
    if (canadaEur) direct.append(canadaEur);
    direct.append(
      reviewNode("p", "", reviewL(
        "RCS mittaa kuluttajavähittäismyyntiä ja Health Canada valmistaja-/maahantuojatoimituksia. 5,03 prosentin ero on riippumaton kontrolli, ei valmis täsmäytys: kate, varasto, palautukset, ajoitus, tuoterajaus ja verokäsittely ovat vielä avoimia.",
        "RCS measures consumer retail sales and Health Canada measures manufacturer/importer shipments. The 5.03% difference is an independent control, not a completed reconciliation: margin, inventory, returns, timing, product scope and tax treatment remain open."
      )),
      reviewObservationLink(canadaRetail, sourceMap),
      reviewObservationLink(canadaShipment, sourceMap)
    );
    steps.append(direct);
  }

  const volumeStep = reviewNode("article", "panel calculation-audit-card calculation-audit-facts");
  volumeStep.append(
    reviewNode("span", "calculation-kind", reviewL("FAKTA · havaittu syöte", "FACT · observed input")),
    reviewNode("h3", "", reviewL("1. Verotettu nestemäärä", "1. Taxed liquid volume")),
    reviewNode("strong", "", `${reviewNumber(volume.value, 0)} L · ${volume.year}`),
    reviewNode("p", "", reviewIsFi() ? volume.limitationFi : volume.limitationEn),
    reviewObservationLink(volume, sourceMap)
  );

  const conversionStep = reviewNode("article", "panel calculation-audit-card calculation-audit-formula");
  conversionStep.append(
    reviewNode("span", "calculation-kind", reviewL("LASKELMA · yksikkömuunnos", "CALCULATION · unit conversion")),
    reviewNode("h3", "", reviewL("2. Litrat millilitroiksi", "2. Litres to millilitres")),
    reviewNode("code", "", `${reviewNumber(volume.value, 0)} × 1,000 = ${reviewNumber(Number(volume.value) * 1000, 0)} ml`),
    reviewNode("p", "", reviewL("Muunnoskerroin 1 000; muita numeerisia oikaisukertoimia ei ole lähdemallissa.", "Conversion factor 1,000; the source model contains no other numeric adjustment factors."))
  );

  const priceStep = reviewNode("article", "panel calculation-audit-card calculation-audit-assumptions");
  priceStep.append(
    reviewNode("span", "calculation-kind", reviewL("JULKAISTUT SYÖTTEET · eivät markkinakeskiarvo", "PUBLISHED INPUTS · not a market average")),
    reviewNode("h3", "", reviewL("3. Kolme vuoden 2026 verkkokauppahintaa", "3. Three 2026 online retail prices"))
  );
  const priceList = reviewNode("ul", "calculation-price-list");
  for (const item of scenarios) {
    const label = item.name === "low"
      ? reviewL("Matala", "Low")
      : item.name === "central" ? reviewL("Keskipiste", "Central") : reviewL("Korkea", "High");
    const row = reviewNode("li");
    row.append(
      reviewNode("strong", "", `${label}: EUR ${reviewNumber(item.observation.value, 2)}/ml`),
      reviewNode("span", "", reviewIsFi() ? item.observation.limitationFi : item.observation.limitationEn),
      reviewObservationLink(item.observation, sourceMap)
    );
    priceList.append(row);
  }
  priceStep.append(priceList);

  const resultStep = reviewNode("article", "panel calculation-audit-card calculation-audit-formula");
  resultStep.append(
    reviewNode("span", "calculation-kind", reviewL("LASKELMA · täsmäytetty tulos", "CALCULATION · reconciled output")),
    reviewNode("h3", "", reviewL("4. Vähittäismyyntivastaavuuden vaihteluväli", "4. Retail-equivalent range")),
    reviewNode("code", "", model.formula),
    reviewNode("strong", "", `${reviewMarketFormat(model.low, model.currency)} · ${reviewMarketFormat(model.central, model.currency)} · ${reviewMarketFormat(model.high, model.currency)}`),
    reviewNode("p", "", reviewL("Matala · keskipiste · korkea. Kaikki kolme tulosta toistuvat täsmälleen julkaistuista syötteistä.", "Low · central · high. All three outputs reproduce exactly from the published inputs."))
  );

  const limits = reviewNode("article", "panel calculation-audit-card calculation-audit-exclusions");
  limits.append(
    reviewNode("span", "calculation-kind", reviewL("RAJAUKSET · ei nollaoikaisuja", "EXCLUSIONS · not zero adjustments")),
    reviewNode("h3", "", reviewL("Mitä laskelma ei sisällä", "What the calculation does not include"))
  );
  const exclusionList = reviewNode("ul");
  for (const exclusion of model.exclusions || []) {
    const labels = REVIEW_EXCLUSION_LABELS[exclusion] || [exclusion, exclusion];
    exclusionList.append(reviewNode("li", "", reviewL(...labels)));
  }
  limits.append(
    exclusionList,
    reviewNode("p", "", reviewL(
      "Näille rajauksille ei ole lähdemallissa euromääräisiä tai prosentuaalisia oikaisuja. Kolme yksittäistä hintaa eivät muodosta painotettua, edustavaa hintakoria.",
      "The source model contains no euro or percentage adjustments for these exclusions. Three individual prices do not form a weighted, representative price basket."
    ))
  );

  steps.append(volumeStep, conversionStep, priceStep, resultStep, limits);
}

function renderReviewCalculationAuditUnavailable() {
  const root = reviewById("review-calculation-audit");
  const status = reviewById("review-calculation-audit-status");
  const summary = reviewById("review-calculation-audit-summary");
  const steps = reviewById("review-calculation-audit-steps");
  if (!root || !status || !summary || !steps) return;
  root.setAttribute("aria-busy", "false");
  status.dataset.state = "error";
  status.textContent = reviewL("Laskentaketju ei ole saatavilla.", "Calculation audit trail unavailable.");
  summary.replaceChildren(reviewNode("p", "", reviewL("Mallinnettua tulosta ei saa käyttää ilman lähdesyötteitä.", "Do not use a modelled result without its source inputs.")));
  steps.replaceChildren();
}

function reviewObservationPeriodState(latestYear, referenceYear) {
  if (!Number.isFinite(latestYear)) return "undated";
  if (latestYear >= referenceYear - 1) return "latest_period";
  if (latestYear === referenceYear - 2) return "previous_full_year";
  return "historical_only";
}

function renderReviewSourceFreshness(market, atlas) {
  const root = reviewById("review-source-freshness");
  const status = reviewById("review-source-freshness-status");
  const summary = reviewById("review-source-freshness-summary");
  const list = reviewById("review-source-freshness-list");
  if (!root || !status || !summary || !list) return;

  const sources = Array.isArray(market?.sources) ? market.sources : [];
  const observations = Array.isArray(market?.observations) ? market.observations : [];
  const referenceDate = String(market?.meta?.asOf || "");
  const referenceYear = Number(referenceDate.slice(0, 4));
  const yearsBySource = new Map();
  for (const observation of observations) {
    for (const sourceId of observation.sourceIds || []) {
      if (!yearsBySource.has(sourceId)) yearsBySource.set(sourceId, []);
      if (Number.isFinite(Number(observation.year))) yearsBySource.get(sourceId).push(Number(observation.year));
    }
  }

  const ledger = sources.map((source) => {
    const years = yearsBySource.get(source.sourceId) || [];
    const latestYear = years.length ? Math.max(...years) : null;
    const retrievalState = !/^\d{4}-\d{2}-\d{2}$/.test(String(source.retrievedAt || ""))
      ? "undated"
      : source.retrievedAt > referenceDate ? "invalid_future_date"
        : source.retrievedAt === referenceDate ? "verified_on_as_of" : "verified_before_as_of";
    return {
      ...source,
      latestYear,
      observationPeriodState: reviewObservationPeriodState(latestYear, referenceYear),
      retrievalState
    };
  });
  const invalid = ledger.some((item) => item.retrievalState === "invalid_future_date");
  const counts = {
    latest: ledger.filter((item) => item.observationPeriodState === "latest_period").length,
    previous: ledger.filter((item) => item.observationPeriodState === "previous_full_year").length,
    historical: ledger.filter((item) => item.observationPeriodState === "historical_only").length,
    undated: ledger.filter((item) => item.observationPeriodState === "undated").length
  };

  root.setAttribute("aria-busy", "false");
  status.dataset.state = invalid ? "error" : "caution";
  status.textContent = invalid
    ? reviewL("Lähderekisteri hylätty: hakupäivä on aineistopäivän jälkeen.", "Source ledger rejected: a retrieval date is later than the dataset date.")
    : reviewL(
      `${ledger.length}/${ledger.length} markkinalähteen hakupäivä kirjattu · sisällöllistä vanhentumista ei voida arvioida ilman tarkistusrytmiä`,
      `${ledger.length}/${ledger.length} market-source retrieval dates recorded · substantive staleness is not assessable without a review cadence`
    );

  const summaryItems = [
    [reviewL("Markkinalähteet", "Market sources"), ledger.length, reviewL(`Hakupäivän vertailupiste ${referenceDate}`, `Retrieval reference date ${referenceDate}`)],
    [reviewL("Uusin / nykyinen havaintojakso", "Latest / current observation period"), counts.latest, reviewL("Havaintovuosi 2025–2026", "Observation year 2025–2026")],
    [reviewL("Edellinen täysi vuosi", "Previous full year"), counts.previous, reviewL("Havaintovuosi 2024", "Observation year 2024")],
    [reviewL("Vain historiallinen havainto", "Historical observation only"), counts.historical, reviewL("Havaintovuosi 2023 tai vanhempi", "Observation year 2023 or earlier")]
  ];
  summary.replaceChildren(...summaryItems.map(([label, value, note]) => {
    const card = reviewNode("article", "freshness-summary-card");
    card.append(reviewNode("span", "", label), reviewNode("strong", "", value), reviewNode("small", "", note));
    return card;
  }));
  const atlasNote = reviewNode("article", "freshness-atlas-boundary");
  atlasNote.append(
    reviewNode("strong", "", reviewL(
      `${atlas.evidence.length} atlaksen evidenssiriviä · erätason tarkistuspäivä ei ole kirjattu`,
      `${atlas.evidence.length} atlas evidence records · item-level verification date not recorded`
    )),
    reviewNode("p", "", reviewL(
      `Atlaksen ${atlas.meta.generatedAt} lähdesnapshot vahvistaa käytetyn upstream-tiedoston identiteetin, ei jokaisen linkitetyn lähteen nykyistä sisältöä tai ajantasaisuutta.`,
      `The atlas source snapshot dated ${atlas.meta.generatedAt} verifies the identity of the upstream file used, not the current content or currency of every linked source.`
    ))
  );
  summary.append(atlasNote);

  list.replaceChildren();
  for (const item of ledger) {
    const observationLabel = item.observationPeriodState === "latest_period"
      ? reviewL("uusin / nykyinen jakso", "latest / current period")
      : item.observationPeriodState === "previous_full_year"
        ? reviewL("edellinen täysi vuosi", "previous full year")
        : item.observationPeriodState === "historical_only"
          ? reviewL("vain historiallinen", "historical only")
          : reviewL("ei päivättyä havaintoa", "no dated observation");
    const retrievalLabel = item.retrievalState === "verified_on_as_of"
      ? reviewL("haettu aineistopäivänä", "retrieved on dataset date")
      : item.retrievalState === "verified_before_as_of"
        ? reviewL("haettu ennen aineistopäivää", "retrieved before dataset date")
        : item.retrievalState === "invalid_future_date"
          ? reviewL("virheellinen tuleva päivä", "invalid future date")
          : reviewL("hakupäivä puuttuu", "retrieval date missing");
    const row = document.createElement(list.tagName === "TBODY" ? "tr" : "article");
    if (list.tagName === "TBODY") {
      const sourceCell = reviewNode("td");
      sourceCell.append(reviewNode("strong", "", item.publisher), reviewNode("code", "", item.sourceId));
      const sourceUrl = reviewUrl(item.pageUrl);
      if (sourceUrl) {
        const link = reviewNode("a", "", reviewL("Avaa lähde", "Open source"));
        link.href = sourceUrl;
        link.target = "_blank";
        link.rel = "noreferrer";
        sourceCell.append(link);
      }
      const typeCell = reviewNode("td");
      typeCell.append(
        reviewNode("strong", "", String(item.sourceKind || "—").replaceAll("_", " ")),
        reviewNode("small", "", reviewL("Lähdeluokka; ei tarkkuuspiste", "Source class; not an accuracy score"))
      );
      const observationCell = reviewNode("td");
      observationCell.append(reviewNode("strong", "", item.latestYear || "—"), reviewNode("small", "", observationLabel));
      const retrievedCell = reviewNode("td");
      retrievedCell.append(reviewNode("time", "", item.retrievedAt || "—"), reviewNode("small", "", retrievalLabel));
      const assessmentCell = reviewNode("td");
      assessmentCell.append(
        reviewNode("strong", "", reviewL("Ei arvioitavissa", "Not assessable")),
        reviewNode("small", "", reviewL("Hakupäivä ei osoita sisällön nykyisyyttä.", "Retrieval does not prove substantive currency."))
      );
      const reviewGateCell = reviewNode("td");
      reviewGateCell.append(
        reviewNode("strong", "", reviewL("Tarkistusrytmi puuttuu", "Review cadence missing")),
        reviewNode("small", "", reviewL("Vahvista lähde ja määritelmä ennen seuraavaa päätöskäyttöä.", "Re-verify the source and definition before the next decision use."))
      );
      row.append(sourceCell, typeCell, observationCell, retrievedCell, assessmentCell, reviewGateCell);
    } else {
      row.className = "freshness-ledger-item";
      row.append(
        reviewNode("strong", "", item.publisher),
        reviewNode("code", "", item.sourceId),
        reviewNode("span", "", `${item.retrievedAt || "—"} · ${retrievalLabel}`),
        reviewNode("span", "", `${item.latestYear || "—"} · ${observationLabel}`),
        reviewNode("small", "", reviewL("Sisällöllinen vanhentuminen: ei arvioitavissa.", "Substantive staleness: not assessable."))
      );
    }
    list.append(row);
  }
}

function renderReviewSourceFreshnessUnavailable() {
  const root = reviewById("review-source-freshness");
  const status = reviewById("review-source-freshness-status");
  const summary = reviewById("review-source-freshness-summary");
  const list = reviewById("review-source-freshness-list");
  if (!root || !status || !summary || !list) return;
  root.setAttribute("aria-busy", "false");
  status.dataset.state = "error";
  status.textContent = reviewL("Lähteiden tuoreusrekisteri ei ole saatavilla.", "Source-freshness ledger unavailable.");
  summary.replaceChildren(reviewNode("p", "", reviewL("Puuttuvaa lähdetietoa ei käsitellä ajantasaisena.", "Missing source information is not treated as current.")));
  list.replaceChildren();
}

function renderReviewMetrics(data) {
  const countries = data.countries;
  const observations = Array.isArray(reviewMarketData?.observations) ? reviewMarketData.observations : [];
  const official = observations.filter((item) => String(item.evidenceStatus || "").startsWith("official_"));
  const quantified = new Set(official.map((item) => item.countryIso2).filter(Boolean));
  const officialRetail = new Set(official.filter((item) => item.metric === "consumer_retail_market_value").map((item) => item.countryIso2).filter(Boolean));
  const officialRetailLowerBound = new Set(official.filter((item) => item.metric === "official_specialist_retail_sales_lower_bound").map((item) => item.countryIso2).filter(Boolean));
  const modelled = new Set((reviewMarketData?.models || []).map((item) => item.countryIso2).filter(Boolean));
  const metrics = [
    [reviewL("Tutkimusmaailma", "Research universe"), `${countries.length} / 195`, reviewL("Suvereenit valtiot indeksoitu; ei 195 mitattua markkinaa", "Sovereign states indexed; not 195 measured markets")],
    [reviewL("Määrällisiä vuosihavaintoja", "Countries with annual numeric data"), `${quantified.size} / 195`, reviewL("Raha-, vero- tai määräarvoja; mittarit pidetään erillään", "Monetary, tax or volume records; measures remain separate")],
    [reviewL("Virallinen vähittäismyynnin alaraja-ankkuri", "Official retail lower-bound anchor"), `${officialRetailLowerBound.size} / 195`, reviewL(`${officialRetail.size} täydellistä virallista kuluttajamarkkina-arvoa; alaraja ei ole luovuttajamarkkina`, `${officialRetail.size} complete official consumer-retail values; a lower bound is not a donor market`)],
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

function assessReviewFxRates(data = reviewFxData) {
  const policy = data?.calculationPolicy || {};
  const datasetUrl = reviewUrl(data?.provider?.datasetUrl);
  const methodologyUrl = reviewUrl(data?.provider?.methodologyUrl);
  const eligiblePeriods = Array.isArray(policy.eligibleRecordPeriods)
    ? policy.eligibleRecordPeriods
    : [];
  const policyValid = Boolean(
    data?.schemaVersion === "1.0"
    && data?.targetCurrency === "EUR"
    && data?.provider?.name === "European Central Bank"
    && datasetUrl
    && new URL(datasetUrl).hostname === "data.ecb.europa.eu"
    && methodologyUrl
    && new URL(methodologyUrl).hostname === "www.ecb.europa.eu"
    && eligiblePeriods.length === 2
    && eligiblePeriods[0] === "calendar_year"
    && eligiblePeriods[1] === "calendar_year_estimate"
    && policy.eligibleUnitRule === "currency_must_equal_unit"
    && policy.rateType === "annual_average_reference_rate"
    && policy.quoteConvention === "currency_units_per_eur"
    && policy.formulaMachine === "eur_equivalent = original_amount / currency_units_per_eur"
    && policy.missingRateStatus === "not_computed"
  );
  const rateMap = new Map();
  let recordsValid = Array.isArray(data?.rates) && data.rates.length > 0;
  for (const rate of data?.rates || []) {
    const currency = String(rate?.currency || "");
    const year = Number(rate?.year);
    const value = Number(rate?.currencyUnitsPerEur);
    const sourceUrl = reviewUrl(rate?.sourceUrl);
    const key = `${currency}:${year}`;
    const valid = Boolean(
      /^[A-Z]{3}$/.test(currency)
      && currency !== "EUR"
      && Number.isInteger(year)
      && Number.isFinite(value)
      && value > 0
      && rate?.seriesKey === `EXR.A.${currency}.EUR.SP00.A`
      && rate?.rateId === `ECB-EXR-A-${currency}-EUR-SP00-A-${year}`
      && rate?.rateType === "annual_average_reference_rate"
      && rate?.status === "available"
      && sourceUrl
      && new URL(sourceUrl).hostname === "data-api.ecb.europa.eu"
      && !rateMap.has(key)
    );
    if (!valid) {
      recordsValid = false;
      continue;
    }
    rateMap.set(key, { ...rate, sourceUrl });
  }
  return {
    valid: policyValid && recordsValid,
    eligiblePeriods: new Set(eligiblePeriods),
    rateMap: policyValid && recordsValid ? rateMap : new Map()
  };
}

function assessReviewEurEquivalent(record) {
  const value = Number(record?.value);
  const currency = String(record?.currency || "");
  const unit = String(record?.unit || "");
  const year = Number(record?.year);
  const period = String(record?.period || "");
  if (!Number.isFinite(value) || value <= 0 || !/^[A-Z]{3}$/.test(currency) || unit !== currency) {
    return { status: "ineligible", reason: "not_a_positive_monetary_total" };
  }
  if (currency === "EUR") return { status: "already_eur", eurValue: value };
  const fx = assessReviewFxRates();
  if (!fx.valid) return { status: "not_computed", reason: "fx_dataset_invalid_or_unavailable" };
  if (!Number.isInteger(year) || !fx.eligiblePeriods.has(period)) {
    return { status: "not_computed", reason: "period_not_compatible_with_annual_average" };
  }
  const rate = fx.rateMap.get(`${currency}:${year}`);
  if (!rate) return { status: "not_computed", reason: "compatible_ecb_rate_missing" };
  const eurValue = value / Number(rate.currencyUnitsPerEur);
  if (!Number.isFinite(eurValue) || eurValue <= 0) {
    return { status: "not_computed", reason: "conversion_not_finite" };
  }
  return { status: "computed", eurValue, rate };
}

function reviewEurEquivalentNode(record, prefix = "") {
  const assessment = assessReviewEurEquivalent(record);
  if (assessment.status === "ineligible" || assessment.status === "already_eur") return null;
  const line = reviewNode("small", "eur-equivalent-line");
  line.dataset.status = assessment.status;
  const prefixText = prefix ? `${prefix}: ` : "";
  if (assessment.status !== "computed") {
    line.textContent = `${prefixText}${reviewL("EUR-vasta-arvo: not_computed", "EUR equivalent: not_computed")}`;
    line.title = assessment.reason;
    return line;
  }
  line.append(document.createTextNode(
    `${prefixText}≈ ${reviewMarketFormat(assessment.eurValue, "EUR")} · `
  ));
  const source = reviewNode(
    "a",
    "eur-rate-link",
    reviewL(`ECB-vuosikeskiarvo ${assessment.rate.year} ↗`, `ECB annual average ${assessment.rate.year} ↗`)
  );
  source.href = assessment.rate.sourceUrl;
  source.target = "_blank";
  source.rel = "noreferrer";
  source.title = reviewL(
    `${record.currency} per EUR ${Number(assessment.rate.currencyUnitsPerEur).toFixed(4)} · alkuperäinen määrä ÷ kurssi`,
    `${record.currency} per EUR ${Number(assessment.rate.currencyUnitsPerEur).toFixed(4)} · original amount ÷ rate`
  );
  line.append(source);
  return line;
}

function reviewFxDisclosureNode() {
  const fx = assessReviewFxRates();
  const box = reviewNode("div", "review-fx-disclosure");
  if (!fx.valid) {
    box.dataset.state = "error";
    box.append(
      reviewNode("strong", "", reviewL("EUR-vasta-arvot: not_computed", "EUR equivalents: not_computed")),
      reviewNode("small", "", reviewL(
        "ECB:n kurssiaineistoa ei voitu vahvistaa. Alkuperäisiä valuuttoja ei korvata eikä puuttuvia kursseja arvata.",
        "The ECB rate dataset could not be verified. Original currencies are not replaced and missing rates are not inferred."
      ))
    );
    return box;
  }
  box.dataset.state = "ready";
  box.append(
    reviewNode("strong", "", reviewL("EUR-vertailukerros", "EUR comparison layer")),
    reviewNode("small", "", reviewL(
      "Alkuperäinen valuutta on ensisijainen. EUR = alkuperäinen rahamäärä ÷ ECB:n vuosikeskiarvo (valuuttayksikköä per euro). Fyysisiä määriä, verokantoja ja yksikköhintoja ei muunneta; puuttuva kurssi merkitään not_computed.",
      "Original currency is primary. EUR = original monetary amount ÷ ECB annual average (currency units per euro). Physical volumes, tax rates and unit prices are not converted; a missing rate is marked not_computed."
    ))
  );
  const links = reviewNode("span", "review-fx-links");
  for (const [label, url] of [
    [reviewL("ECB EXR -aineisto ↗", "ECB EXR dataset ↗"), reviewFxData.provider.datasetUrl],
    [reviewL("ECB:n viitekurssimenetelmä ↗", "ECB reference-rate method ↗"), reviewFxData.provider.methodologyUrl]
  ]) {
    const link = reviewNode("a", "", label);
    link.href = url;
    link.target = "_blank";
    link.rel = "noreferrer";
    links.append(link);
  }
  box.append(links);
  return box;
}

function reviewScenarioComponentNode(record, scenarioKey) {
  const component = record?.componentBreakdown?.[scenarioKey];
  if (!component) return null;
  const labels = {
    low: reviewL("Matala", "Low"),
    base: reviewL("Perus", "Base"),
    high: reviewL("Korkea", "High")
  };
  const monetaryRecord = (value) => ({
    value,
    currency: record.currency,
    unit: record.currency,
    year: record.year,
    period: "calendar_year"
  });
  const specialist = assessReviewEurEquivalent(monetaryRecord(component.specialistRetailNzd));
  const general = assessReviewEurEquivalent(monetaryRecord(component.generalRetailRpsNzd));
  const combined = assessReviewEurEquivalent(monetaryRecord(component.combinedNzd));
  const group = reviewNode("div", "review-scenario-component");
  group.append(reviewNode(
    "code",
    "",
    `${labels[scenarioKey]}: ${record.currency} ${reviewNumber(component.specialistRetailNzd, 2)} + ${record.currency} ${reviewNumber(component.generalRetailRpsNzd, 2)} = ${record.currency} ${reviewNumber(component.combinedNzd, 2)}`
  ));
  if ([specialist, general, combined].some((item) => item.status !== "computed")) {
    const line = reviewNode(
      "small",
      "eur-equivalent-line",
      reviewL("EUR-komponentit: not_computed", "EUR components: not_computed")
    );
    line.dataset.status = "not_computed";
    group.append(line);
    return group;
  }
  const line = reviewNode("small", "eur-equivalent-line");
  line.dataset.status = "computed";
  line.append(document.createTextNode(
    `≈ EUR ${reviewNumber(specialist.eurValue, 2)} + EUR ${reviewNumber(general.eurValue, 2)} = EUR ${reviewNumber(combined.eurValue, 2)} · `
  ));
  const source = reviewNode(
    "a",
    "eur-rate-link",
    reviewL(`ECB-vuosikeskiarvo ${combined.rate.year} ↗`, `ECB annual average ${combined.rate.year} ↗`)
  );
  source.href = combined.rate.sourceUrl;
  source.target = "_blank";
  source.rel = "noreferrer";
  line.append(source);
  group.append(line);
  return group;
}

function reviewDonorGeography(candidate) {
  const country = (reviewData?.countries || []).find((item) => item.iso2 === candidate?.countryIso2);
  if (country) return reviewIsFi() ? country.nameFi || country.name : country.name || country.nameFi;
  if (candidate?.geography === "Germany") return reviewL("Saksa", "Germany");
  if (candidate?.geography === "New Zealand") return reviewL("Uusi-Seelanti", "New Zealand");
  if (candidate?.geography === "European Union") return reviewL("Euroopan unioni", "European Union");
  return candidate?.geography || "—";
}

function reviewClosureLabel(kind, value) {
  const labels = {
    owner: {
      independent_research_team: ["Riippumaton tutkimusryhmä", "Independent research team"],
      public_authority: ["Viranomainen", "Public authority"],
      data_supplier: ["Datatoimittaja", "Data supplier"],
      rights_review: ["Käyttöoikeustarkistus", "Rights review"],
      independent_validator: ["Riippumaton validoija", "Independent validator"]
    },
    route: {
      public_source_reconstruction: ["Julkisen lähteen rekonstruktio", "Public-source reconstruction"],
      official_aggregate_request: ["Virallinen koontitietopyyntö", "Official aggregate request"],
      tax_customs_reconciliation: ["Vero- ja tullitäsmäytys", "Tax and customs reconciliation"],
      rights_cleared_retail_data: ["Käyttöoikeuksiltaan selvä retail-data", "Rights-cleared retail data"],
      independent_reconciliation: ["Riippumaton täsmäytys", "Independent reconciliation"]
    },
    status: {
      queued: ["Jonossa", "Queued"],
      in_progress: ["Työn alla", "In progress"],
      request_sent: ["Pyyntö lähetetty", "Request sent"],
      awaiting_response: ["Odottaa vastausta", "Awaiting response"],
      response_under_review: ["Vastaus tarkistuksessa", "Response under review"],
      evidence_ready_for_validation: ["Näyttö valmis validointiin", "Evidence ready for validation"],
      blocked_external: ["Ulkoinen este", "Blocked externally"]
    }
  };
  return labels[kind]?.[value] ? reviewL(...labels[kind][value]) : String(value || "—").replaceAll("_", " ");
}

function renderReviewDonorClosureUnavailable(message) {
  const body = reviewById("review-donor-closure-body");
  const status = reviewById("review-donor-closure-status");
  if (!body || !status) return;
  body.replaceChildren();
  const row = reviewNode("tr");
  const cell = reviewNode("td", "empty-state", message);
  cell.colSpan = 7;
  row.append(cell);
  body.append(row);
  status.dataset.state = "error";
  status.textContent = reviewL(
    "Fail-closed: sulkemistoimet eivät vaikuta 0/3-porttiin ilman ehjää kriteerikarttaa.",
    "Fail closed: closure actions cannot affect the 0/3 gate without a valid criterion map."
  );
}

function renderReviewDonorClosureBoard(cockpit = reviewDonorCockpit) {
  const body = reviewById("review-donor-closure-body");
  const status = reviewById("review-donor-closure-status");
  if (!body || !status) return;
  const criteria = Array.isArray(cockpit?.protocol?.criteria) ? cockpit.protocol.criteria : [];
  const criterionIds = criteria.map((item) => item?.criterionId);
  const protocolValid = cockpit?.schemaVersion === "1.1"
    && cockpit?.protocol?.protocolVersion === "1.0"
    && criterionIds.length === 10
    && criterionIds.every((id, index) => id === `D${index + 1}`);
  const candidates = Array.isArray(cockpit?.candidates) ? cockpit.candidates : [];
  const rows = [];
  let recordsValid = protocolValid && candidates.length > 0;
  for (const candidate of candidates) {
    const statusById = new Map(
      (Array.isArray(candidate?.criterionStatuses) ? candidate.criterionStatuses : [])
        .map((item) => [item?.criterionId, item?.status])
    );
    const blockingIds = criterionIds.filter((id) => statusById.get(id) !== "passed");
    const actions = Array.isArray(candidate?.closureActions) ? candidate.closureActions : [];
    const targetedIds = actions.flatMap((action) => Array.isArray(action?.criterionIds) ? action.criterionIds : []);
    const candidateValid = blockingIds.length === targetedIds.length
      && blockingIds.every((id) => targetedIds.filter((target) => target === id).length === 1)
      && actions.every((action) => (
        String(action?.actionId || "").trim()
        && Array.isArray(action?.criterionIds)
        && action.criterionIds.length > 0
        && String(action?.routeEn || "").trim()
        && String(action?.routeFi || "").trim()
        && String(action?.evidenceTargetEn || "").trim()
        && String(action?.evidenceTargetFi || "").trim()
        && /^\d{4}-\d{2}-\d{2}$/.test(String(action?.nextFollowUpOn || ""))
      ));
    recordsValid = recordsValid && candidateValid;
    for (const action of actions) rows.push({ candidate, action });
  }
  if (!recordsValid) {
    renderReviewDonorClosureUnavailable(reviewL(
      "Sulkemistaulun rakennetarkistus epäonnistui.",
      "The closure-board structure could not be verified."
    ));
    return;
  }
  body.replaceChildren();
  for (const { candidate, action } of rows) {
    const row = reviewNode("tr");
    const identity = reviewNode("td", "donor-control-identity");
    identity.append(
      reviewNode("strong", "", `${candidate.countryIso2 || reviewL("Alue", "Region")} · ${candidate.year || "—"}`),
      reviewNode("small", "", reviewIsFi() ? candidate.headlineFi : candidate.headlineEn)
    );
    const ownerRoute = reviewNode("td");
    ownerRoute.append(
      reviewNode("strong", "", reviewClosureLabel("owner", action.ownerRole)),
      reviewNode("small", "", `${reviewClosureLabel("route", action.routeType)} · ${reviewIsFi() ? action.routeFi : action.routeEn}`)
    );
    const statusCell = reviewNode("td");
    const statusChip = reviewNode("span", "donor-decision-chip", reviewClosureLabel("status", action.publicStatus));
    statusChip.dataset.decision = action.publicStatus === "evidence_ready_for_validation" ? "accepted" : "not_accepted";
    statusCell.append(statusChip);
    row.append(
      identity,
      reviewNode("td", "", action.criterionIds.join(", ")),
      ownerRoute,
      reviewNode("td", "", reviewIsFi() ? action.evidenceTargetFi : action.evidenceTargetEn),
      statusCell,
      reviewNode("td", "", reviewFormatDate(action.nextFollowUpOn)),
      reviewNode("td", "", reviewL(
        "Ei muuta kriteeriä ennen lähteistettyä validointia.",
        "No criterion changes before source-linked validation."
      ))
    );
    body.append(row);
  }
  status.dataset.state = "ready";
  status.textContent = reviewL(
    `${rows.length} sulkemistoimea · jokainen avoin tai hylätty D1–D10-kriteeri katettu kerran.`,
    `${rows.length} closure actions · every open or failed D1–D10 criterion covered once.`
  );
}

function renderReviewDonorLedgerUnavailable(message) {
  const root = reviewById("review-donor-ledger");
  if (!root) return;
  root.setAttribute("aria-busy", "false");
  reviewById("review-donor-protocol-version").textContent = reviewL("Protokolla —", "Protocol —");
  reviewById("review-donor-gate-rule").textContent = reviewL(
    "0/3 muuttuu vain, kun ehdokas läpäisee jokaisen kriteerin.",
    "The 0/3 gate changes only when a candidate passes every criterion."
  );
  reviewById("review-donor-rule").textContent = reviewL(
    "Hyväksyntäprotokollaa ei voitu vahvistaa. Luovuttajamarkkinoiden määrä pidetään nollassa.",
    "The acceptance protocol could not be verified. The donor-market count is held at zero."
  );
  reviewById("review-donor-summary").replaceChildren();
  renderReviewDonorClosureUnavailable(message);
  reviewById("review-donor-candidates").replaceChildren(reviewNode("p", "empty-state", message));
  const status = reviewById("review-donor-status");
  status.dataset.state = "error";
  status.textContent = reviewL(
    "Fail-closed: yksikään ehdokas ei voi vaikuttaa 0/3-porttiin ilman ehjää protokollaa.",
    "Fail closed: no candidate can affect the 0/3 gate without a valid protocol."
  );
}

function renderReviewDonorLedger(market) {
  const root = reviewById("review-donor-ledger");
  if (!root) return;
  const assessment = assessReviewDonorLedger(market);
  const protocol = assessment.protocol || {};
  const readiness = market?.meta?.modelReadiness || {};
  const required = Number(readiness.minimumRequiredDonors || 3);
  const recorded = Number(readiness.comparableFullYearMarketValueDonors);
  const effectiveCount = assessment.protocolValid ? assessment.accepted.length : 0;
  const protocolLabel = String(protocol.protocolVersion || "").trim() || "—";
  reviewById("review-donor-protocol-version").textContent = `${reviewL("Protokolla", "Protocol")} ${protocolLabel}`;
  reviewById("review-donor-gate-rule").textContent = reviewL(
    `${effectiveCount}/${required} muuttuu vain, kun ehdokas läpäisee jokaisen kriteerin.`,
    `The ${effectiveCount}/${required} gate changes only when a candidate passes every criterion.`
  );
  reviewById("review-donor-rule").textContent = reviewIsFi()
    ? protocol.acceptanceRuleFi || "Kaikkien julkaistujen kriteerien on läpäistävä tarkistus ennen kuin ehdokas voidaan laskea luovuttajamarkkinaksi."
    : protocol.acceptanceRuleEn || "Every published criterion must pass before a candidate can count as a donor market.";

  const summaryItems = [
    [
      reviewL("Hyväksytty porttiin", "Accepted into gate"),
      `${effectiveCount} / ${required}`,
      reviewL("Laskettu fail-closed ehdokastietueista", "Calculated fail closed from candidate records")
    ],
    [
      reviewL("Tarkastellut ehdokkaat", "Candidates reviewed"),
      assessment.candidates.length,
      reviewL("Hyväksytyt ja hylätyt näkyvät samalla säännöllä", "Accepted and rejected candidates use the same rule")
    ],
    [
      reviewL("Pakolliset kriteerit", "Mandatory criteria"),
      assessment.criteria.length || "—",
      reviewL("Yksikin avoin tai hylätty kriteeri estää hyväksynnän", "One open or failed criterion blocks acceptance")
    ]
  ];
  reviewById("review-donor-summary").replaceChildren(...summaryItems.map(([label, value, note]) => {
    const item = reviewNode("div", "donor-summary-item");
    item.append(reviewNode("span", "", label), reviewNode("strong", "", value), reviewNode("small", "", note));
    return item;
  }));
  renderReviewDonorClosureBoard();

  const candidatesHost = reviewById("review-donor-candidates");
  candidatesHost.replaceChildren();
  for (const result of assessment.candidates) {
    const candidate = result.candidate || {};
    const card = reviewNode("article", "donor-candidate-card");
    card.dataset.decision = result.accepted ? "accepted" : "not_accepted";
    const head = reviewNode("div", "donor-candidate-head");
    const identity = reviewNode("div");
    const geography = reviewDonorGeography(candidate);
    const referenceType = candidate.referenceType === "observation"
      ? reviewL("havainto", "observation")
      : candidate.referenceType === "model"
        ? reviewL("malli", "model")
        : "—";
    identity.append(
      reviewNode("p", "donor-candidate-meta", `${candidate.countryIso2 || geography || "—"} · ${candidate.year || "—"} · ${referenceType} · ${candidate.referenceId || "—"}`),
      reviewNode("h4", "", (reviewIsFi() ? candidate.headlineFi : candidate.headlineEn) || candidate.candidateId || reviewL("Nimeämätön ehdokas", "Unnamed candidate"))
    );
    const decision = reviewNode("span", "donor-decision-chip", result.accepted ? reviewL("Hyväksytty", "Accepted") : reviewL("Ei hyväksytty", "Not accepted"));
    decision.dataset.decision = result.accepted ? "accepted" : "not_accepted";
    head.append(identity, decision);

    const passedCount = result.criterionResults.filter((item) => item.status === "passed").length;
    const failedCount = result.criterionResults.filter((item) => item.status === "failed").length;
    const openCount = result.criterionResults.length - passedCount - failedCount;
    const counts = reviewNode("div", "donor-candidate-counts");
    counts.append(
      reviewNode("span", "donor-count-chip donor-count-passed", reviewL(`${passedCount} läpäisty`, `${passedCount} passed`)),
      reviewNode("span", "donor-count-chip donor-count-failed", reviewL(`${failedCount} hylätty`, `${failedCount} failed`)),
      reviewNode("span", "donor-count-chip donor-count-open", reviewL(`${openCount} avoin`, `${openCount} open`))
    );

    const reason = reviewNode("p", "donor-candidate-copy");
    reason.append(reviewNode("strong", "", reviewL("Päätösperuste: ", "Decision basis: ")), document.createTextNode((reviewIsFi() ? candidate.decisionReasonFi : candidate.decisionReasonEn) || reviewL("Ei dokumentoitua perustetta.", "No documented reason.")));
    const next = reviewNode("p", "donor-candidate-copy");
    next.append(reviewNode("strong", "", reviewL("Tarvittava seuraava näyttö: ", "Next evidence needed: ")), document.createTextNode((reviewIsFi() ? candidate.nextEvidenceFi : candidate.nextEvidenceEn) || reviewL("Ei dokumentoitu.", "Not documented.")));
    card.append(head, counts, reason, next);

    const issues = [];
    if (!assessment.protocolValid) issues.push(reviewL("hyväksyntäprotokolla ei ole ehjä", "acceptance protocol is invalid"));
    if (!result.referenceValid) issues.push(reviewL("viitattu havainto tai malli ei ratkea", "referenced observation or model does not resolve"));
    if (!result.sourcesResolve) issues.push(reviewL("kaikilla lähteillä ei ole ratkaistavaa julkista linkkiä", "not every source resolves to a public link"));
    if (result.duplicateIds.length) issues.push(reviewL("toistuvia kriteeritunnuksia", "duplicate criterion identifiers"));
    if (result.unknownIds.length) issues.push(reviewL("tuntemattomia kriteeritunnuksia", "unknown criterion identifiers"));
    if (result.conflictingIds.length) issues.push(reviewL("ristiriitaisia kriteeritiloja", "conflicting criterion states"));
    if (candidate.decision === "accepted" && !result.accepted) issues.push(reviewL("ilmoitettu hyväksyntä hylättiin fail-closed-tarkistuksessa", "declared acceptance was rejected by the fail-closed check"));
    if (issues.length) {
      card.append(reviewNode("p", "donor-candidate-copy donor-record-warning", `${reviewL("Tietuevaroitus", "Record warning")}: ${issues.join("; ")}.`));
    }

    const sourceLinks = reviewNode("div", "donor-source-links");
    const sourceIds = Array.isArray(candidate.sourceIds) ? [...new Set(candidate.sourceIds.filter(Boolean))] : [];
    if (!sourceIds.length) sourceLinks.append(reviewNode("span", "donor-source-missing", reviewL("Ei lähdeviitteitä", "No source references")));
    for (const sourceId of sourceIds) {
      const source = assessment.sources.get(sourceId);
      const url = reviewUrl(source?.pageUrl || source?.downloadUrl);
      if (!url) {
        sourceLinks.append(reviewNode("span", "donor-source-missing", `${sourceId} · ${reviewL("linkki puuttuu", "link unavailable")}`));
        continue;
      }
      const link = reviewNode("a", "", `${source?.publisher || sourceId} ↗`);
      link.href = url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.title = `${sourceId} · ${reviewL("Avaa alkuperäinen lähde", "Open original source")}`;
      sourceLinks.append(link);
    }
    card.append(sourceLinks);

    const details = reviewNode("details", "donor-criteria-details");
    const detailsSummary = reviewNode("summary", "", reviewL(`Kriteeritulokset · ${passedCount}/${result.criterionResults.length} läpäisty`, `Criterion results · ${passedCount}/${result.criterionResults.length} passed`));
    const list = reviewNode("div", "donor-criteria-list");
    for (const item of result.criterionResults) {
      const row = reviewNode("div", "donor-criterion-row");
      row.dataset.status = item.status;
      const mark = reviewNode("span", "donor-criterion-mark", item.status === "passed" ? "✓" : item.status === "failed" ? "×" : "?");
      mark.setAttribute("aria-hidden", "true");
      const copy = reviewNode("div");
      const statusLabel = item.status === "passed" ? reviewL("Läpäisty", "Passed") : item.status === "failed" ? reviewL("Hylätty", "Failed") : reviewL("Avoin", "Open");
      copy.append(
        reviewNode("strong", "", (reviewIsFi() ? item.criterion.titleFi : item.criterion.titleEn) || item.criterion.criterionId),
        reviewNode("small", "", `${statusLabel} · ${(reviewIsFi() ? item.criterion.requirementFi : item.criterion.requirementEn) || "—"}`)
      );
      row.setAttribute("aria-label", `${statusLabel}: ${(reviewIsFi() ? item.criterion.titleFi : item.criterion.titleEn) || item.criterion.criterionId}`);
      row.append(mark, copy);
      list.append(row);
    }
    if (!result.criterionResults.length) list.append(reviewNode("p", "empty-state", reviewL("Kriteerejä ei voitu vahvistaa.", "Criteria could not be verified.")));
    details.append(detailsSummary, list);
    card.append(details);
    candidatesHost.append(card);
  }
  if (!assessment.candidates.length) {
    candidatesHost.append(reviewNode("p", "empty-state", reviewL("Luovuttajamarkkinaehdokkaita ei ole julkaistu.", "No donor-market candidates have been published.")));
  }

  const status = reviewById("review-donor-status");
  const mismatch = Number.isFinite(recorded) && recorded !== effectiveCount;
  status.dataset.state = assessment.protocolValid && !mismatch ? "ready" : "error";
  status.textContent = !assessment.protocolValid
    ? reviewL("Fail-closed: protokolla ei läpäissyt rakennetarkistusta, joten portti pidetään nollassa.", "Fail closed: the protocol failed structural validation, so the gate is held at zero.")
    : mismatch
      ? reviewL(`Fail-closed: metatiedon portti ${recorded}/${required} ei täsmää kriteereistä laskettuun ${effectiveCount}/${required}-tulokseen.`, `Fail closed: the metadata gate ${recorded}/${required} does not match the criterion-derived ${effectiveCount}/${required} result.`)
      : reviewL(`${assessment.candidates.length} ehdokasta tarkistettu samalla protokollalla · ${effectiveCount}/${required} hyväksytty.`, `${assessment.candidates.length} candidates checked under one protocol · ${effectiveCount}/${required} accepted.`);
  root.setAttribute("aria-busy", "false");
}

function reviewScenarioRange(record) {
  const values = Object.fromEntries(["low", "base", "high"].map((key) => [
    key,
    Number(record?.inputs?.[key]?.value)
  ]));
  const sourcesValid = ["low", "base", "high"].every((key) => (
    Array.isArray(record?.inputs?.[key]?.sourceIds)
    && record.inputs[key].sourceIds.length > 0
  ));
  const valuesValid = ["low", "base", "high"].every(
    (key) => Number.isFinite(values[key]) && values[key] > 0
  );
  const componentsValid = ["low", "base", "high"].every((key) => {
    const component = record?.componentBreakdown?.[key];
    const specialist = Number(component?.specialistRetailNzd);
    const general = Number(component?.generalRetailRpsNzd);
    const combined = Number(component?.combinedNzd);
    return [specialist, general, combined].every((value) => Number.isFinite(value) && value > 0)
      && Math.abs((specialist + general) - combined) < 0.01
      && Math.abs(combined - values[key]) < 0.01;
  });
  return record?.declaredStatus === "computed"
    && record?.evidenceStatus === "supported_model_not_observed_national_value"
    && record?.accepted === false
    && valuesValid
    && componentsValid
    && sourcesValid
    && values.low <= values.base
    && values.base <= values.high
    ? values
    : null;
}

function renderReviewMarket(market) {
  const observations = Array.isArray(market?.observations) ? market.observations : [];
  const models = Array.isArray(market?.models) ? market.models : [];
  const commercial = observations.filter((item) => item.metric === "commercial_market_estimate" && item.currency === "USD" && Number(item.year) === 2025);
  const newZealandLowerBound = observations.find((item) => item.observationId === "NZ-2024-SPECIALIST-RETAIL-SALES-LOWER-BOUND");
  const newZealandRawSum = observations.find((item) => item.observationId === "NZ-2024-SPECIALIST-RETAIL-PRODUCT-SALES-RAW-FILE-SUM");
  const newZealandScenarioRecord = (reviewCountryScenarios?.countryYearScenarios || []).find(
    (item) => item.scenarioId === "NZ-2024-RETAIL-RANGE"
  );
  const newZealandScenario = reviewScenarioRange(newZealandScenarioRecord);
  const ftc2021 = observations.find((item) => item.observationId === "US-2021-FTC-CARTRIDGE-DISPOSABLE-REPORTED-SALES");
  const euBenchmark = observations.find((item) => item.observationId === "EU-2023-EC-E-CIGARETTE-MARKET-BENCHMARK");
  const canada = observations.find((item) => item.observationId === "CA-2024-STATCAN-RCS-VAPING-RETAIL-SALES");
  const canadaShipment = observations.find((item) => item.observationId === "CA-2024-MANUFACTURER-IMPORTER-SHIPMENTS-VALUE");
  const germany = models.find((item) => item.modelId === "DE-2025-LIQUID-RETAIL-EQUIVALENT-RANGE");
  const sourceMap = new Map((market?.sources || []).map((source) => [source.sourceId, source]));
  const cards = [];
  if (newZealandScenario) {
    cards.push({
      label: reviewL("Uusi-Seelanti · 2024 tuettu vähittäisherkkyys", "New Zealand · 2024 supported retail sensitivity"),
      value: `${reviewMarketFormat(newZealandScenario.low, newZealandScenarioRecord.currency)}–${reviewMarketFormat(newZealandScenario.high, newZealandScenarioRecord.currency)} · ${reviewL("perus", "base")} ${reviewMarketFormat(newZealandScenario.base, newZealandScenarioRecord.currency)}`,
      note: reviewL(
        "Tunnistettu sähkötupakkamyynti: erikoisvähittäiskaupan ankkuri + yleisvähittäiskaupan RPS-määrä- ja hintamalli. Tuettu malli, ei havaittu täydellinen kansallinen arvo eikä hyväksytty donor; GST, peitto ja riippumaton täsmäytys ovat avoimia.",
        "Identified-vaping sales: specialist-retailer anchor plus a general-retailer RPS quantity-and-price model. Supported model—not an observed complete national value or accepted donor; GST, coverage and independent reconciliation remain open."
      ),
      scenarioComponents: newZealandScenarioRecord,
      url: reviewUrl(sourceMap.get(newZealandScenarioRecord.sourceIds?.[0])?.pageUrl),
      methodUrl: "https://github.com/jounirautio78-ops/pixan-global-market-evidence-public/blob/main/source/NZ_2024_RPS_RETAIL_VALUE_SENSITIVITY.md"
    });
  }
  if (ftc2021) {
    cards.push({
      label: reviewL("Yhdysvallat · 2021 FTC:n taulukoista johdettu reitti", "United States · 2021 FTC table-derived route"),
      value: reviewMarketFormat(ftc2021.value, ftc2021.currency),
      note: reviewL(
        "Suljettujen järjestelmien ja kertakäyttötuotteiden valmistajaraportointi yhdeksältä johtavalta valmistajalta. Open-system-tuotteet puuttuvat, veroperustaa ei ilmoiteta eikä luku ole täydellinen kuluttajavähittäismyynti tai hyväksytty donor.",
        "Manufacturer-reported cartridge-system and disposable sales from nine leading manufacturers. Open-system products are excluded, the tax basis is unstated, and the figure is neither complete consumer-retail sell-through nor an accepted donor."
      ),
      eurRecords: [{ record: ftc2021 }],
      url: reviewUrl(sourceMap.get(ftc2021.sourceIds?.[0])?.pageUrl),
      methodUrl: "https://github.com/jounirautio78-ops/pixan-global-market-evidence-public/blob/main/source/US_FTC_2015_2021_REPORTED_SALES.md"
    });
  }
  cards.push(
    {
      label: reviewL("Uusi-Seelanti · 2024 virallisten tiedostojen täsmäytys", "New Zealand · 2024 official-file reconciliation"),
      value: newZealandRawSum ? reviewMarketFormat(newZealandRawSum.value, newZealandRawSum.currency) : "—",
      note: reviewL("29 virallista tiedostoa · raakasumma 280,685 milj. NZD täsmää viralliseen ≥280 milj. otsikkolukuun · toistuvien rivien herkkyys 264,561 milj. NZD; ei puhdistettu kansallinen arvo eikä luovuttajamarkkina", "29 official files · raw sum NZD 280.685m reconciles the official ≥NZD 280m headline · repeated-row sensitivity NZD 264.561m; not a cleaned national value or donor market"),
      eurRecords: newZealandRawSum ? [{ record: newZealandRawSum }] : [],
      url: reviewUrl(sourceMap.get(newZealandLowerBound?.sourceIds?.[0])?.pageUrl),
      methodUrl: "https://github.com/jounirautio78-ops/pixan-global-market-evidence-public/blob/main/source/NZ_2024_ANNUAL_RETURNS_RECONCILIATION.md"
    },
    {
      label: reviewL("Euroopan unioni · 2023 komission julkaisema vertailuarvo", "European Union · 2023 Commission-published benchmark"),
      value: euBenchmark ? reviewMarketFormat(euBenchmark.value, euBenchmark.currency) : "—",
      note: reviewL("Euromonitoriin ja ulkopuoliseen tutkimukseen perustuva toissijainen koonti; liitteen maadata ei kata Kyprosta, Luxemburgia ja Maltaa; ei virallinen havaittu luovuttajamarkkina", "Secondary compilation based on Euromonitor and an external study; the annex country data do not cover Cyprus, Luxembourg or Malta; not an official observed donor market"),
      eurRecords: euBenchmark ? [{ record: euBenchmark }] : [],
      url: reviewUrl(sourceMap.get(euBenchmark?.sourceIds?.[0])?.pageUrl),
      methodUrl: "https://github.com/jounirautio78-ops/pixan-global-market-evidence-public/blob/main/source/EU_2023_E_CIGARETTE_BENCHMARK_RECONCILIATION.md"
    },
    {
      label: reviewL("Kanada · 2019–2025 virallinen vähittäismyyntisarja", "Canada · 2019–2025 official retail-sales series"),
      value: canada ? reviewMarketFormat(canada.value, canada.currency) : "—",
      note: reviewL(
        `Vuoden 2024 kuluttajavähittäismyynti; seitsemän vuosiarvoa 2019–2025. Kaikki vuoden 2024 neljännekset ovat E-laatua. Health Canadan toimitusarvo ${canadaShipment ? reviewMarketFormat(canadaShipment.value, canadaShipment.currency) : "—"} on 5,03 % alempi; silta ei ole vielä validoitu.`,
        `2024 consumer retail sales; seven annual values from 2019 to 2025. Every 2024 quarter is quality E. The Health Canada shipment value of ${canadaShipment ? reviewMarketFormat(canadaShipment.value, canadaShipment.currency) : "—"} is 5.03% lower; the bridge is not yet validated.`
      ),
      eurRecords: canada ? [{ record: canada }] : [],
      url: reviewUrl(sourceMap.get(canada?.sourceIds?.[0])?.pageUrl),
      methodUrl: "https://github.com/jounirautio78-ops/pixan-global-market-evidence-public/blob/main/source/CANADA_RCS_2019_2025_RETAIL_SALES.md"
    },
    {
      label: reviewL("Saksa · 2025 nestemalli", "Germany · 2025 liquid model"),
      value: germany ? `${reviewMarketFormat(germany.low, germany.currency)}–${reviewMarketFormat(germany.high, germany.currency)}` : "—",
      note: reviewL("Verotettu neste × 2026 hintakori; matala luottamus, ei laitteita", "Taxed liquid × 2026 price basket; low confidence, excludes devices"),
      eurRecords: []
    }
  );
  cards.push(...commercial.map((item) => ({
    label: reviewIsFi() ? item.labelFi : item.labelEn,
    value: reviewMarketFormat(item.value, item.currency),
    note: reviewIsFi() ? item.limitationFi : item.limitationEn,
    eurRecords: [{ record: item }],
    url: reviewUrl(sourceMap.get(item.sourceIds?.[0])?.pageUrl)
  })));
  const host = reviewById("review-market-metrics");
  host.replaceChildren(...cards.map((item) => {
    const card = reviewNode("article", "panel review-market-card");
    card.append(reviewNode("span", "kicker", item.label), reviewNode("strong", "", item.value));
    for (const descriptor of item.eurRecords || []) {
      const eurLine = reviewEurEquivalentNode(descriptor.record, descriptor.label || "");
      if (eurLine) card.append(eurLine);
    }
    if (item.scenarioComponents) {
      const components = reviewNode("div", "review-scenario-components");
      for (const key of ["low", "base", "high"]) {
        const component = reviewScenarioComponentNode(item.scenarioComponents, key);
        if (component) components.append(component);
      }
      card.append(components);
    }
    card.append(reviewNode("small", "", item.note));
    if (item.url) {
      const link = reviewNode("a", "", reviewL("Avaa julkaisijan lähde →", "Open publisher source →"));
      link.href = item.url;
      link.target = "_blank";
      link.rel = "noreferrer";
      card.append(link);
    }
    if (item.methodUrl) {
      const methodLink = reviewNode("a", "", reviewL("Avaa täsmäytysmenetelmä →", "Open reconciliation method →"));
      methodLink.href = item.methodUrl;
      methodLink.target = "_blank";
      methodLink.rel = "noreferrer";
      card.append(methodLink);
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
    ? "Raha, verot, fyysiset määrät ja mallinnetut vaihteluvälit näytetään erikseen eikä niitä summata. Alkuperäinen valuutta säilyy ensisijaisena; EUR-vastine on ECB:n vuosikeskiarvolla laskettu vertailuluku, ei spot-arvo."
    : "Monetary observations, excise, physical quantities and modelled ranges remain separate and are never added together. Original currency remains primary; the EUR equivalent uses the ECB annual average and is not a spot value.");
  note.replaceChildren(status, explanation, rule, reviewFxDisclosureNode());
  renderReviewDonorLedger(market);
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
  renderReviewDonorLedgerUnavailable(reviewL("Luovuttajamarkkinadataa ei voitu ladata.", "Donor-market data could not be loaded."));
}

const REVIEW_CHANGE_STORAGE_KEY = "pixan-global-market-evidence-last-seen-release-v4";
const reviewReleaseToken = (release) => release ? `${release.id}:${release.version || "unversioned"}` : "";

function reviewPublicReleases() {
  const releases = Array.isArray(reviewChangelog?.releases)
    ? [...reviewChangelog.releases].sort((a, b) => String(b.publishedAt).localeCompare(String(a.publishedAt)))
    : [];
  if (releases.length) return releases;
  const uiRelease = window.PixanUiRelease;
  return uiRelease ? [uiRelease] : [];
}

function prepareReviewChangeView() {
  const releases = reviewPublicReleases();
  const current = releases[0] || null;
  let lastSeen = null;
  try { lastSeen = localStorage.getItem(REVIEW_CHANGE_STORAGE_KEY); } catch (_) { /* local storage may be disabled */ }
  let mode = releases.length ? "none" : "unavailable";
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
  const latestRelease = reviewPublicReleases()[0] || null;
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
  applyReviewView();
  renderReviewMeta(data);
  renderDecisionCockpit(data);
  renderResearchOperationsOverview();
  renderReviewMetrics(data);
  renderReviewGrades(data);
  renderReviewDimensions(data);
  renderReviewBlockers(data);
  renderReviewTransactionPaths();
  renderReviewTop10Matrix();
  if (reviewMarketData) {
    renderReviewMarket(reviewMarketData);
    renderReviewCalculationAudit(reviewMarketData);
    renderReviewSourceFreshness(reviewMarketData, data);
  } else {
    renderReviewMarketUnavailable();
    renderReviewCalculationAuditUnavailable();
    renderReviewSourceFreshnessUnavailable();
  }
  renderReviewPatent();
  renderReviewChanges();
}

async function initReview() {
  applyReviewView();
  reviewById("copy-review-link")?.addEventListener("click", copyReviewLink);
  reviewById("print-review")?.addEventListener("click", () => window.print());
  reviewById("review-changes-mark-seen")?.addEventListener("click", markReviewChangesSeen);
  document.addEventListener("pixan:languagechange", () => {
    applyReviewView();
    const copyStatus = reviewById("copy-review-status");
    if (copyStatus) copyStatus.textContent = "";
    if (reviewData) renderReview(reviewData);
  });
  try {
    const [atlasResult, marketResult, donorResult, scenarioResult, fxResult, patentResult, changelogResult, requestResult] = await Promise.allSettled([
      fetch("data/atlas.json", { cache: "no-store" }),
      fetch("data/market-values.json", { cache: "no-store" }),
      fetch("data/donor-cockpit.json", { cache: "no-store" }),
      fetch("data/country-scenarios.json", { cache: "no-store" }),
      fetch("data/fx-rates.json", { cache: "no-store" }),
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
      if (donorResult.status !== "fulfilled" || !donorResult.value.ok) throw new Error(`HTTP ${donorResult.status === "fulfilled" ? donorResult.value.status : "network error"}`);
      const donorData = await donorResult.value.json();
      if (donorData.schemaVersion !== "1.1" || !Array.isArray(donorData.candidates)) throw new Error("schema validation failed");
      reviewDonorCockpit = donorData;
    } catch (error) {
      reviewDonorCockpit = null;
      console.warn("Optional donor-closure dataset unavailable", error);
    }

    try {
      if (scenarioResult.status !== "fulfilled" || !scenarioResult.value.ok) throw new Error(`HTTP ${scenarioResult.status === "fulfilled" ? scenarioResult.value.status : "network error"}`);
      const scenarioData = await scenarioResult.value.json();
      if (!Array.isArray(scenarioData.countryYearScenarios)) throw new Error("schema validation failed");
      reviewCountryScenarios = scenarioData;
    } catch (error) {
      reviewCountryScenarios = null;
      console.warn("Optional country-scenario dataset unavailable", error);
    }

    try {
      if (fxResult.status !== "fulfilled" || !fxResult.value.ok) throw new Error(`HTTP ${fxResult.status === "fulfilled" ? fxResult.value.status : "network error"}`);
      const fxData = await fxResult.value.json();
      if (!assessReviewFxRates(fxData).valid) throw new Error("schema validation failed");
      reviewFxData = fxData;
    } catch (error) {
      reviewFxData = null;
      console.warn("Optional ECB FX dataset unavailable", error);
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
      const expectedLayerIds = [
        "statutory_sales",
        "excise_domestic_release",
        "customs_net_imports",
        "retail_or_shipments",
        "price_channel_bridge",
        "enforcement_signal"
      ];
      const evidenceLayers = Array.isArray(requestData.evidenceStack?.layers)
        ? requestData.evidenceStack.layers
        : [];
      const supplements = Array.isArray(requestData.supplementaryRequests)
        ? requestData.supplementaryRequests
        : [];
      const bvlSupplement = supplements[0];
      if (requestData.schemaVersion !== 3
        || routes.length !== 20
        || uniqueCountries.size !== 20
        || ranked.slice(0, 10).some((route, index) => route.operationalRank !== index + 1)
        || requestData.evidenceStack?.stateUniverseCount !== 195
        || evidenceLayers.length !== 6
        || evidenceLayers.some((layer, index) =>
          layer.order !== index + 1 || layer.layerId !== expectedLayerIds[index])
        || supplements.length !== 1
        || bvlSupplement?.requestId !== "DE-BVL-TABAKERZV25-ANNUAL-SALES"
        || bvlSupplement?.countryIso2 !== "DE"
        || bvlSupplement?.countsTowardCountryQueue !== false
        || bvlSupplement?.status !== "sent"
        || bvlSupplement?.dispatch?.state !== "sent"
        || bvlSupplement?.dispatch?.sentOn !== "2026-07-24"
        || bvlSupplement?.dispatch?.publicAuthorityReference !== null
        || bvlSupplement?.dispatch?.responseState !== "not_publicly_recorded") {
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
