"use strict";

const I18N = window.SiteI18n;
const l = (fi, en) => I18N.pick(fi, en);
const isFi = () => I18N.isFinnish();

const DIMENSION_LABELS = {
  officialSales: ["Virallinen myynti / toimitus", "Official sales / deliveries"],
  officialVolume: ["Virallinen volyymi", "Official taxable volume"],
  taxRevenue: ["Toteutunut vero", "Realised tax revenue"],
  customs: ["Tullivirta", "Official customs flow"],
  model: ["Mallinnus", "Modelled estimate"],
  regulation: ["Sääntelytila", "Regulatory status"],
  patent: ["Patenttistatus", "Patent status"]
};

const DIMENSION_HELP = {
  officialSales: ["suora myynti tai valmistaja-/maahantuojatoimitus", "direct consumer sales or manufacturer/importer deliveries"],
  officialVolume: ["verotettu tai viranomaiselle raportoitu määrä", "taxable or authority-reported volume"],
  taxRevenue: ["toteutunut verokertymä; ei pelkkä verokanta × määrä", "realised tax revenue; not merely rate × volume"],
  customs: ["virallinen rajavirta; ei kuluttajamyynti", "official border flow; not consumer sales"],
  model: ["julkaistu tai auditoitava laskennallinen arvio", "published or auditable calculated estimate"],
  regulation: ["ajantasainen oikeudellinen markkinastatus", "current official legal market status"],
  patent: ["virallisen maarekisterin voimassaolotarkistus", "validity check in an official national register"]
};

const FALLBACK_METHODS = {
  fi: [
    { title: "Virallinen myynti", text: "Haetaan viranomaisen julkaisema kuluttajamyynti tai toimitusmyynti ja säilytetään alkuperäinen mittarityyppi." },
    { title: "Vero ja volyymi", text: "Täsmäytetään valmisteveron määrä, litrat tai millilitrat ja tuoteryhmän tarkka rajaus." },
    { title: "Tullireitti", text: "Käsitellään laitteet ja inhaloitavat tuotteet HS/CN/HTS-koodeittain, vienti ja jälleenvienti erotellen." },
    { title: "Mallinnettu alue", text: "Vasta viimeisenä yhdistetään käyttäjät, kulutus ja hinnat; oletukset ja herkkyys julkaistaan tuloksen mukana." }
  ],
  en: [
    { title: "Official sales", text: "Retrieve authority-published consumer sales or delivery sales and retain the original measure type." },
    { title: "Tax and volume", text: "Reconcile excise revenue, litres or millilitres and the exact product scope." },
    { title: "Customs route", text: "Treat devices and inhalable products by HS/CN/HTS code, separating exports and re-exports." },
    { title: "Modelled range", text: "Only then combine users, consumption and prices; publish assumptions and sensitivity with the result." }
  ]
};

const FALLBACK_RULES = {
  fi: [
    "Puuttuva havainto ei saa muuttua nollaksi.",
    "Tullivirtaa tai verokantaa ei saa nimetä kuluttajamyynniksi.",
    "Jokaisella numerolla on oltava maa, vuosi, yksikkö, tuoterajaus ja lähde.",
    "Laskettu vero erotetaan toteutuneesta verokertymästä.",
    "Yhdistettyä nikotiinituoteluokkaa ei nimetä e-nesteeksi ilman erittelyä.",
    "Saapuvaa tiedostoa ei julkaista ennen turvallisuus- ja lähdeauditointia.",
    "Patenttistatus vaatii maakohtaisen virallisen rekisteritarkistuksen.",
    "Revisio säilyttää historian eikä kirjoita aikaisempaa havaintoa näkymättömästi yli."
  ],
  en: [
    "A missing observation must never become zero.",
    "A customs flow or tax rate must not be labelled consumer sales.",
    "Every number must retain country, year, unit, product scope and source.",
    "Calculated tax must remain separate from realised tax revenue.",
    "A combined nicotine-products category must not be labelled e-liquid without a breakdown.",
    "Incoming files must not be published before safety and source review.",
    "Patent status requires a country-level check in an official register.",
    "A revision must preserve history and never silently overwrite an earlier observation."
  ]
};

const REGIONS_FI = {
  Africa: "Afrikka", Americas: "Amerikat", Asia: "Aasia", Europe: "Eurooppa", Oceania: "Oseania"
};

const EVIDENCE_TITLES_EN = {
  "MARNET-001": "Health Canada · Vaping sales",
  "MARNET-002": "Statistics Canada · CIMT 2025",
  "MARNET-003": "Destatis · tobacco tax statistics",
  "MARNET-004": "Finnish Tax Administration · excise statistics",
  "MARNET-005": "German Tobacco Tax Act §2",
  "MARNET-006": "EU Tobacco Products Directive 20(7)",
  "MARNET-007": "UN Comtrade",
  "MARNET-008": "U.S. Census · Merchandise Trade Imports 2025",
  "MARNET-009": "Eurostat Comext DS-045409",
  "MARNET-010": "Japan Customs / MOF · 2025 revised",
  "MARNET-011": "Korea Customs Service · 2025 HS6 / HSK10",
  "MARNET-012": "FTC E-Cigarette Report 2021",
  "MARNET-013": "Japan Customs methodology",
  "MARNET-014": "China Customs · official statistics service",
  "MARNET-015": "Italy ADM · PLI-PAT and monthly reporting template",
  "MARNET-016": "Italy ADM · 2025 PLI tax rates",
  "MARNET-017": "Italian Parliament · budget report table 17",
  "MARNET-018": "Spain AEAT · realised 2025 tax revenue",
  "MARNET-019": "Spain BOE · Modelo 573",
  "MARNET-020": "France Douane · National 2025 import/export",
  "MARNET-021": "ANSES · vaping notification register",
  "MARNET-022": "ANSES · sales-reporting coverage audit",
  "MARNET-023": "Polish Ministry of Finance · ZEFIR2/AIS excise flow",
  "MARNET-024": "Polish Ministry of Finance · realised 2025 excise revenue",
  "MARNET-025": "Polish KAS · targeted enforcement 2025",
  "MARNET-026": "Swedish Ministry of Finance · Beräkningskonventioner 2026",
  "MARNET-027": "Swedish Tax Agency · nicotine tax",
  "MARNET-028": "Swedish Public Health Agency · annual EU-CEG sales reporting",
  "MARNET-029": "Eurostat Comext · Sweden 2025",
  "MARNET-030": "Danish Ministry of Taxation · revenue list 2025",
  "MARNET-031": "Denmark · EU-CEG annual reporting and product register",
  "MARNET-032": "Danish Tax Agency · risk-based enforcement",
  "MARNET-033": "Eurostat Comext · Denmark 2025",
  "MARNET-034": "VWS / Bureau Beke · Donkere wolken",
  "MARNET-035": "CBS StatLine · e-cigarette use 2024",
  "MARNET-036": "Trimbos ScholierenMonitor · ages 12–16",
  "MARNET-037": "Eurostat Comext · Netherlands 2025"
};

const EVIDENCE_USE_EN = {
  delivery_sales: "Official delivery-sales anchor; verify the measure, year and coverage in the original source.",
  customs: "Border-trade or customs-flow anchor; does not alone establish domestic consumer sales.",
  official_volume: "Official volume anchor; verify the unit, year and tax base in the original source.",
  official_volume_tax: "Official volume and tax anchor; keep volume and realised revenue as separate measures.",
  tax_rate: "Official tax-rate anchor; a rate alone is not realised revenue or consumer sales.",
  reporting_rule: "Official reporting requirement; establishes a data route, not a complete published sales series.",
  historical_sales: "Historical sales observation; verify product scope and do not carry it forward as a current-year total.",
  methodology: "Official methodology route; use it to reproduce a compatible extraction.",
  official_access_route: "Official access route; query parameters and resulting observations still require review.",
  reporting_schema: "Official reporting schema; establishes the collection structure, not published market size.",
  official_forecast: "Official forecast or budget estimate; keep it separate from realised revenue.",
  combined_tax_actual: "Realised combined tax observation; product-category separation must be checked.",
  registry: "Official registry route; registrations or notifications do not equal sales.",
  coverage_audit: "Coverage audit; use it to qualify reporting completeness.",
  tax_actual: "Realised tax-revenue anchor; verify product scope and period.",
  enforcement_sample: "Targeted enforcement sample; not representative consumer sales.",
  reporting_registry: "Official reporting and registry route; not itself an annual sales total.",
  model: "Modelled estimate; retain assumptions, uncertainty and separation from observations.",
  prevalence: "Prevalence observation; user counts do not equal annual market value."
};

const LEGAL_EN = {
  "EP-3032975-B2": "The European Patent Office publication service contains the official EP 3 032 975 B2 patent specification. Publication alone does not establish current national validation, renewal status, infringement or monetary value.",
  "DE-BPATG-8NI18-24-JUDGMENT": "The Federal Patent Court judgment dated 14 January 2026 dismissed the nullity action. The official record notes that an appeal has been lodged with the Federal Court of Justice under docket X ZR 21/26, so the judgment is not final.",
  "DE-LGMUC-7O3341-24-JUDGMENT": "The Munich Regional Court I judgment dated 2 April 2026 found infringement by the products examined in case 7 O 3341/24 and ordered the remedies listed in that judgment. The record does not by itself establish finality, enforcement, damages paid or relevance to other products or countries."
};

const READINESS_EN = {
  "195 maan muuttumaton master-universumi": "Fixed 195-country master universe",
  "Legacy-lähteiden whitelistattu public-importti": "Allowlisted public import of legacy sources",
  "Virallinen, proxy- ja mallinäyttö erotettu toisistaan": "Official, proxy and model evidence kept separate",
  "Useimmista maista puuttuu virallinen vuosittainen laite- ja nestemyynti": "Most countries still lack a verified annual official series for device and e-liquid sales.",
  "Markkinaevidenssiä ei ole vielä sidottu maakohtaiseen patenttistatukseen ja claim charteihin": "Market evidence has not yet been reconciled with country-level patent status and product claim charts.",
  "Aineisto ei sisällä riippumatonta IVS-arvonmääritystä eikä realisoitunutta lisenssi- tai vahingonkorvauskassavirtaa": "The dataset does not include an independent IVS valuation or realised licensing or damages cash flow."
};

const MEASURE_LABELS = {
  official_sales: ["Virallinen myynti tai toimitus", "Official sales or deliveries"],
  tax_or_volume: ["Vero tai verovolyymi", "Tax or taxable volume"],
  customs: ["Tullituonti tai -vienti", "Customs imports or exports"],
  price_sample: ["Hintaotos", "Price sample"],
  prevalence: ["Käyttäjä- tai prevalenssitutkimus", "User or prevalence study"],
  regulatory_or_patent: ["Sääntely- tai patenttiasiakirja", "Regulatory or patent document"],
  model: ["Malli tai kaupallinen arvio", "Model or commercial estimate"],
  other: ["Muu aineisto", "Other material"]
};

const state = {
  data: null,
  marketData: null,
  changelog: null,
  changeView: null,
  tab: "overview",
  countryQuery: "",
  region: "",
  grade: "",
  evidenceQuery: "",
  evidenceGrade: "",
  openCountry: null
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
  return new Intl.DateTimeFormat(isFi() ? "fi-FI" : "en-GB", { year: "numeric", month: "long", day: "numeric" }).format(date);
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
  const labels = isFi()
    ? { confirmed: "vahvistettu", partial: "osittainen", missing: "puuttuu", not_applicable: "ei sovellu" }
    : { confirmed: "verified", partial: "partial", missing: "missing", not_applicable: "not applicable" };
  return labels[status] || labels.missing;
}

function sourceLinksOf(country) {
  const links = Array.isArray(country.sourceLinks) ? country.sourceLinks : [];
  return links.map((item) => {
    if (typeof item === "string") {
      const url = safeExternalUrl(item);
      return { label: url ? new URL(url).hostname : l("Lähde", "Source"), url: item };
    }
    return { label: item.label || item.title || item.source || l("Lähde", "Source"), url: item.url };
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
    { label: l("Maailman universumi", "Country universe"), value: list.length, note: l("UN 193 + Pyhä istuin + Palestiina", "UN 193 + Holy See + State of Palestine") },
    { label: l("Viranomaisankkuri", "Direct official anchor"), value: grades.A || 0, note: l("A-lähde ei tarkoita täydellistä markkinapeittoa", "Grade A does not mean complete market coverage") },
    { label: l("Numeerinen reitti", "Sourced numeric route"), value: sourced, note: l("A-, B- tai C-tason havainto", "Grade A, B or C evidence") },
    { label: l("Myynti / vero / volyymi", "Sales / tax / volume"), value: official, note: l("Vähintään osittainen viranomaisreitti", "At least a partial official route") }
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
  for (const [key, labels] of Object.entries(DIMENSION_LABELS)) {
    const count = list.filter((country) => ["confirmed", "partial"].includes(normalizeDimension(country.dimensions?.[key]))).length;
    const confirmed = list.filter((country) => normalizeDimension(country.dimensions?.[key]) === "confirmed").length;
    const percent = list.length ? (count / list.length) * 100 : 0;
    const row = node("div", "coverage-row");
    const labelBox = node("div", "coverage-label");
    labelBox.append(node("strong", "", l(...labels)), node("small", "", l(...DIMENSION_HELP[key])));
    const track = node("div", "coverage-track");
    const fill = node("div", "coverage-fill");
    fill.style.width = `${percent}%`;
    track.append(fill);
    row.append(labelBox, track, node("span", "coverage-number", `${count} / ${list.length}`));
    row.title = isFi() ? `${confirmed} vahvistettua, ${count - confirmed} osittaista` : `${confirmed} verified, ${count - confirmed} partial`;
    host.append(row);
  }
}

function renderReadiness() {
  const fallback = [
    { title: l("195 maan tietorunko", "195-country data structure"), detail: l("Master-universumi ja puuttuvien havaintojen näkyvyys", "Master universe with visible missing observations"), state: "ready", label: l("valmis", "ready") },
    { title: l("Myynti-, vero- ja tullisarjojen peitto", "Sales, tax and customs coverage"), detail: l("Maakohtainen hankinta jatkuu", "Country-level acquisition continues"), state: "partial", label: l("osittainen", "partial") },
    { title: l("Patenttien live-status maittain", "Live patent status by country"), detail: l("Kansalliset rekisterit tarkistettava", "National registers require verification"), state: "open", label: l("avoin", "open") },
    { title: l("Riippumaton vakuusarvo", "Independent collateral value"), detail: l("Markkina-atlas ei yksin ole arvonmääritys", "The market atlas is not itself a valuation"), state: "open", label: l("avoin", "open") }
  ];
  let items = Array.isArray(state.data?.readiness) ? state.data.readiness : null;
  if (!items && state.data?.readiness && typeof state.data.readiness === "object") {
    const ready = (state.data.readiness.completed || []).map((title) => ({ title: isFi() ? title : READINESS_EN[title] || l("Valmis tutkimusrakenne", "Completed research structure"), detail: l("Rakenteellinen julkaisuedellytys", "Structural publication prerequisite"), state: "ready", label: l("valmis", "ready") }));
    const open = (state.data.readiness.blockers || []).map((title) => ({ title: isFi() ? title : READINESS_EN[title] || l("Avoin evidenssiaukko", "Open evidence gap"), detail: l("Vaatii lisänäyttöä ennen lender-grade-johtopäätöstä", "Requires further evidence before a lender-grade conclusion"), state: "open", label: l("avoin", "open") }));
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

const MARKET_METHODS = {
  fi: [
    { code: "01", title: "Suora virallinen rahamäärä", text: "Viranomaisen julkaisema vähittäismyynti tai valmistaja-/maahantuojatoimitus. Mittarin alkuperäinen taso säilytetään." },
    { code: "02", title: "Verotettu määrä × hintakori", text: "Litra-, millilitra-, podi- tai laitemäärä kerrotaan dokumentoidulla low/base/high-hintakorilla." },
    { code: "03", title: "Verotulo ÷ verokanta", text: "Toteutuneesta verosta johdetaan verollinen määrä ja siitä hintakorilla markkina-arvon vaihteluväli." },
    { code: "04", title: "Näennäiskulutus", text: "Kotimainen tuotanto + tuonti − vienti ± varastomuutos, erikseen laitteille ja nesteille, sitten kanavakohtainen kate." },
    { code: "05", title: "Käyttäjät × vuosikulutus", text: "Aktiiviset käyttäjät kerrotaan vuotuisella kulutuksella tai rahankäytöllä ja oikaistaan PPP:llä sekä valuuttakurssilla." },
    { code: "06", title: "Tuoteintensiteetti", text: "Käyttäjät × ml-, podi- ja laitekulutus × hinnat. Laillinen ja laiton osuus sekä saatavuus käsitellään erillisinä oletuksina." }
  ],
  en: [
    { code: "01", title: "Direct official monetary value", text: "Authority-published retail sales or manufacturer/importer shipments, retaining the original transaction level." },
    { code: "02", title: "Taxed quantity × price basket", text: "Litres, millilitres, pods or devices multiplied by a documented low/base/high retail price basket." },
    { code: "03", title: "Excise receipts ÷ tax rate", text: "Infer the taxed quantity from realised receipts, then apply a price basket to produce a value range." },
    { code: "04", title: "Apparent consumption", text: "Domestic production + imports − exports ± inventory change, separately for devices and liquids, followed by channel mark-ups." },
    { code: "05", title: "Users × annual spend", text: "Active users multiplied by annual consumption or spend, adjusted with purchasing-power and exchange-rate inputs." },
    { code: "06", title: "Product-intensity model", text: "Users × annual ml, pod and device intensity × prices, with legal, illicit and availability shares as separate assumptions." }
  ]
};

const MARKET_EVIDENCE_LABELS = {
  official_observed: ["Virallinen havainto", "Official observation"],
  official_provisional: ["Virallinen · alustava", "Official · provisional"],
  commercial_estimate: ["Kaupallinen arvio", "Commercial estimate"],
  published_price_input: ["Julkaistu hintasyöte", "Published price input"],
  modelled: ["Mallinnettu", "Modelled"]
};

const MARKET_EXCLUSION_LABELS = {
  devices: ["laitteet", "devices"],
  pods_and_cartridges_as_separate_hardware_value: ["podien ja patruunoiden erillinen laitteistoarvo", "pods and cartridges as separate hardware value"],
  illicit_and_untaxed_sales: ["laiton ja verottamaton myynti", "illicit and untaxed sales"],
  nicotine_free_products_where_not_taxed: ["nikotiinittomat tuotteet silloin, kun niitä ei veroteta", "nicotine-free products where they are not taxed"],
  wholesale_retail_margin_mix: ["tukku- ja vähittäiskatteiden jakauma", "wholesale and retail margin mix"],
  discount_and_channel_mix: ["alennus- ja myyntikanavajakauma", "discount and channel mix"]
};

function marketSources() {
  return new Map((state.marketData?.sources || []).map((source) => [source.sourceId, source]));
}

function marketObservations() {
  return Array.isArray(state.marketData?.observations) ? state.marketData.observations : [];
}

function marketModels() {
  return Array.isArray(state.marketData?.models) ? state.marketData.models : [];
}

function formatMarketValue(value, currency, unit, compact = true) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  const locale = isFi() ? "fi-FI" : "en-GB";
  if (currency) {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency,
      currencyDisplay: "code",
      notation: compact ? "compact" : "standard",
      maximumFractionDigits: compact && Math.abs(number) >= 1e9 ? 3 : 2
    }).format(number);
  }
  if (unit === "litre") {
    return `${new Intl.NumberFormat(locale, { notation: compact ? "compact" : "standard", maximumFractionDigits: 3 }).format(number)} ${l("l", "L")}`;
  }
  if (unit === "unit") {
    return `${new Intl.NumberFormat(locale, { notation: compact ? "compact" : "standard", maximumFractionDigits: 2 }).format(number)} ${l("kpl", "units")}`;
  }
  if (unit === "EUR_per_ml") return `${new Intl.NumberFormat(locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(number)} EUR/ml`;
  return `${new Intl.NumberFormat(locale, { notation: compact ? "compact" : "standard", maximumFractionDigits: 3 }).format(number)}${unit ? ` ${unit}` : ""}`;
}

function marketGeography(record) {
  if (record.countryIso2) {
    const country = countries().find((item) => item.iso2 === record.countryIso2);
    if (country) return isFi() ? country.nameFi || country.name : country.name || country.nameFi;
  }
  if (record.geography === "Global") return l("Maailma", "Global");
  if (record.geography === "Germany") return l("Saksa", "Germany");
  if (record.geography === "Canada") return l("Kanada", "Canada");
  return record.geography || "—";
}

function marketSourceLink(record, label = l("Lähde ↗", "Source ↗")) {
  const source = marketSources().get(record.sourceIds?.[0]);
  const url = safeExternalUrl(source?.pageUrl);
  if (!source || !url) return null;
  const link = node("a", "market-source-link", label);
  link.href = url;
  link.target = "_blank";
  link.rel = "noreferrer";
  link.title = source.publisher;
  return link;
}

function renderMarketMetrics() {
  const readiness = state.marketData?.meta?.modelReadiness || {};
  const commercial = marketObservations().filter((item) => item.metric === "commercial_market_estimate" && item.currency === "USD" && Number(item.year) === 2025);
  const low = commercial.length ? Math.min(...commercial.map((item) => Number(item.value))) : null;
  const high = commercial.length ? Math.max(...commercial.map((item) => Number(item.value))) : null;
  const official = marketObservations().filter((item) => String(item.evidenceStatus).startsWith("official_"));
  const metrics = [
    [l("Atlaksen maailmanarvio", "Atlas global estimate"), l("Ei vielä julkaistu", "Not yet released"), l("Evidenssiraja ei vielä täyty", "Evidence threshold is not yet met")],
    [l("Ulkoinen 2025-haarukka", "External 2025 range"), low !== null && high !== null ? `${formatMarketValue(low, "USD", "USD")}–${formatMarketValue(high, "USD", "USD")}` : "—", l("3 kaupallista, eri tavoin rajattua arviota", "3 commercial estimates with different scopes")],
    [l("Vertailukelpoiset luovuttajamarkkinat", "Comparable donor markets"), `${readiness.comparableFullYearMarketValueDonors || 0} / ${readiness.minimumRequiredDonors || 3}`, l("Vaatimus ennen maiden välistä estimaattia", "Required before cross-country estimation")],
    [l("Viralliset määrälliset havainnot", "Official quantitative records"), official.length, l("Raha, määrä ja vero pidetään erillään", "Money, quantity and tax remain separate")]
  ];
  const host = byId("market-metrics");
  host.replaceChildren(...metrics.map(([label, value, note]) => {
    const card = node("article", "metric-card");
    card.append(node("span", "", label), node("strong", "", value), node("small", "", note));
    return card;
  }));
}

function renderMarketGlobalRange() {
  const host = byId("market-global-range");
  const records = marketObservations()
    .filter((item) => item.metric === "commercial_market_estimate" && Number(item.year) === 2025)
    .sort((a, b) => Number(a.value) - Number(b.value));
  host.replaceChildren();
  for (const record of records) {
    const source = marketSources().get(record.sourceIds?.[0]);
    const card = node("article", "market-range-item");
    card.append(node("span", "", source?.publisher || l("Ulkoinen arvio", "External estimate")), node("strong", "", formatMarketValue(record.value, record.currency, record.unit)));
    const link = marketSourceLink(record);
    if (link) card.append(link);
    host.append(card);
  }
  if (!records.length) host.append(node("p", "muted", l("Kaupallisia vertailuarvioita ei voitu ladata.", "Commercial reference estimates could not be loaded.")));
}

function renderMarketReadiness() {
  const readiness = state.marketData?.meta?.modelReadiness || {};
  const current = Number(readiness.comparableFullYearMarketValueDonors || 0);
  const required = Number(readiness.minimumRequiredDonors || 3);
  byId("market-readiness-title").textContent = l("Ei vielä estimaattivalmis", "Not yet estimate-ready");
  const host = byId("market-readiness");
  const progress = node("div", "market-readiness-progress");
  const track = node("span", "market-readiness-track");
  const fill = node("i");
  fill.style.width = `${Math.min(100, required ? current / required * 100 : 0)}%`;
  track.append(fill);
  progress.append(track, node("strong", "", `${current} / ${required}`));
  host.replaceChildren(progress, node("p", "", isFi() ? readiness.reasonFi || "" : readiness.reasonEn || ""));
}

function renderMarketObservations() {
  const records = marketObservations()
    .filter((item) => item.metric !== "commercial_market_estimate" && item.metric !== "retail_price_input")
    .sort((a, b) => String(a.countryIso2 || "").localeCompare(String(b.countryIso2 || "")) || Number(b.year) - Number(a.year) || String(a.metric).localeCompare(String(b.metric)));
  const body = byId("market-observation-rows");
  body.replaceChildren();
  for (const record of records) {
    const row = node("tr");
    const valueCell = node("td");
    const compact = node("strong", "market-value-number", formatMarketValue(record.value, record.currency, record.unit));
    compact.title = formatMarketValue(record.value, record.currency, record.unit, false);
    valueCell.append(compact);
    const statusCell = node("td");
    const labels = MARKET_EVIDENCE_LABELS[record.evidenceStatus] || ["Muu havainto", "Other record"];
    statusCell.append(node("span", `market-evidence-chip market-evidence-${String(record.evidenceStatus || "other").replace(/[^a-z0-9_-]/gi, "-")}`, l(...labels)));
    const scopeCell = node("td", "market-scope", isFi() ? record.limitationFi : record.limitationEn);
    const sourceCell = node("td");
    const link = marketSourceLink(record);
    if (link) sourceCell.append(link);
    row.append(
      node("td", "", marketGeography(record)),
      node("td", "", record.year),
      node("td", "", isFi() ? record.labelFi : record.labelEn),
      valueCell,
      statusCell,
      scopeCell,
      sourceCell
    );
    body.append(row);
  }
  byId("market-empty").hidden = records.length !== 0;
}

function renderMarketMethods() {
  const host = byId("market-methods");
  const methods = isFi() ? MARKET_METHODS.fi : MARKET_METHODS.en;
  host.replaceChildren(...methods.map((item) => {
    const card = node("article", "market-method-card");
    card.append(node("span", "", item.code), node("h3", "", item.title), node("p", "", item.text));
    return card;
  }));
}

function renderMarketModels() {
  const host = byId("market-models");
  host.replaceChildren();
  const observationsById = new Map(marketObservations().map((item) => [item.observationId, item]));
  for (const model of marketModels()) {
    const card = node("article", "panel market-model-card");
    const heading = node("div", "panel-heading");
    const title = node("div");
    title.append(node("p", "kicker", `${marketGeography(model)} · ${model.year}`), node("h3", "", isFi() ? model.labelFi : model.labelEn));
    heading.append(title, node("span", "market-status-chip market-status-modelled", l("Mallinnettu · matala luottamus", "Modelled · low confidence")));
    const range = node("div", "market-model-range");
    [[l("Alaraja", "Low"), model.low], [l("Keskipiste", "Base"), model.central], [l("Yläraja", "High"), model.high]].forEach(([label, value]) => {
      const item = node("div");
      item.append(node("span", "", label), node("strong", "", formatMarketValue(value, model.currency, model.currency)));
      range.append(item);
    });
    const caveat = node("p", "market-model-limit", isFi() ? model.limitationFi : model.limitationEn);
    const audit = node("section", "market-model-audit");
    audit.append(node("h4", "", l("Mallin syötteet", "Model inputs")));
    const inputs = node("ul", "market-model-inputs");
    for (const inputId of model.inputIds || []) {
      const input = observationsById.get(inputId);
      const item = node("li");
      if (!input) {
        item.append(node("code", "", inputId), node("span", "", l("Syöte puuttuu", "Input missing")));
      } else {
        const label = node("div");
        label.append(node("strong", "", isFi() ? input.labelFi : input.labelEn), node("small", "", `${input.year} · ${input.observationId}`));
        const value = node("span", "market-model-input-value", formatMarketValue(input.value, input.currency, input.unit));
        const sourceLink = marketSourceLink(input);
        item.append(label, value);
        if (sourceLink) item.append(sourceLink);
      }
      inputs.append(item);
    }
    audit.append(inputs, node("h4", "", l("Kaava", "Formula")), node("code", "market-formula", String(model.formula || "")));
    const exclusions = node("div", "market-model-exclusions");
    exclusions.append(node("h4", "", l("Pois rajattu tästä mallista", "Excluded from this model")));
    const exclusionList = node("ul");
    for (const exclusion of model.exclusions || []) {
      const labels = MARKET_EXCLUSION_LABELS[exclusion] || [exclusion, exclusion];
      exclusionList.append(node("li", "", l(...labels)));
    }
    exclusions.append(exclusionList);
    audit.append(exclusions);
    card.append(heading, range, caveat, audit);
    host.append(card);
  }
  if (!marketModels().length) host.append(node("p", "empty-state", l("Julkaistavia mallinnettuja vaihteluvälejä ei vielä ole.", "No modelled ranges are ready for publication.")));
}

function renderMarket() {
  if (!state.marketData) {
    const metrics = byId("market-metrics");
    const card = node("article", "metric-card market-data-unavailable");
    card.append(node("span", "", l("Markkina-arvodata", "Market-value data")), node("strong", "", l("Ei saatavilla", "Unavailable")), node("small", "", l("Muu 195 maan atlas toimii edelleen.", "The rest of the 195-country atlas remains available.")));
    metrics.replaceChildren(card);
    byId("market-global-range").replaceChildren(node("p", "muted", l("Markkina-arvon apuaineistoa ei voitu ladata.", "The market-value supporting dataset could not be loaded.")));
    byId("market-readiness").replaceChildren(node("p", "muted", l("Valmiustieto ei ole saatavilla.", "Readiness data is unavailable.")));
    byId("market-observation-rows").replaceChildren();
    byId("market-empty").hidden = false;
    renderMarketMethods();
    byId("market-models").replaceChildren(node("p", "empty-state", l("Mallinnettua aineistoa ei voitu ladata.", "Modelled data could not be loaded.")));
    return;
  }
  renderMarketMetrics();
  renderMarketGlobalRange();
  renderMarketReadiness();
  renderMarketObservations();
  renderMarketMethods();
  renderMarketModels();
}

const CHANGE_STORAGE_KEY = "pixan-global-market-evidence-last-seen-release-v4";
const releaseToken = (release) => release ? `${release.id}:${release.version || "unversioned"}` : "";

function prepareChangeView() {
  const releases = Array.isArray(state.changelog?.releases)
    ? [...state.changelog.releases].sort((a, b) => String(b.publishedAt).localeCompare(String(a.publishedAt)))
    : [];
  const current = releases[0] || null;
  let lastSeen = null;
  try { lastSeen = localStorage.getItem(CHANGE_STORAGE_KEY); } catch (_) { /* local storage may be disabled */ }
  let mode = state.changelog ? "none" : "unavailable";
  let visible = [];
  if (current && !lastSeen) {
    mode = "first";
    visible = [current];
  } else if (current && lastSeen !== releaseToken(current)) {
    const previousIndex = releases.findIndex((release) => releaseToken(release) === lastSeen);
    mode = "new";
    visible = previousIndex > 0 ? releases.slice(0, previousIndex) : [current];
  }
  state.changeView = { current, mode, releases: visible };
}

function markChangesSeen() {
  const view = state.changeView;
  if (!view?.current || ["none", "unavailable"].includes(view.mode)) return;
  try { localStorage.setItem(CHANGE_STORAGE_KEY, releaseToken(view.current)); } catch (_) { /* cross-visit memory is optional */ }
  state.changeView = { current: view.current, mode: "none", releases: [] };
  renderChangesSinceVisit();
}

function renderChangesSinceVisit() {
  const host = byId("changes-since-visit");
  const badge = byId("changes-badge");
  const markButton = byId("changes-mark-seen");
  if (!host || !badge || !markButton) return;
  const view = state.changeView || { mode: "none", releases: [] };
  const itemCount = view.releases.reduce((sum, release) => sum + (Array.isArray(release.items) ? release.items.length : 0), 0);
  badge.dataset.state = ["none", "unavailable"].includes(view.mode) ? "none" : "new";
  badge.textContent = view.mode === "unavailable"
    ? l("Ei saatavilla", "Unavailable")
    : view.mode === "none"
    ? l("Ajan tasalla", "Up to date")
    : view.mode === "first"
      ? l("Uusin julkaisu", "Latest release")
      : isFi() ? `${itemCount} uutta muutosta` : `${itemCount} new changes`;
  markButton.hidden = !view.releases.length || ["none", "unavailable"].includes(view.mode);
  host.replaceChildren();
  if (view.mode === "unavailable") {
    host.append(node("p", "change-empty", l("Julkaisuhistoriaa ei voitu ladata. Tämä ei estä muun aineiston käyttöä.", "Release history could not be loaded. The rest of the evidence remains available.")));
    return;
  }
  if (!view.releases.length) {
    host.append(node("p", "change-empty", l("Ei uusia julkaisuja viimeksi nähdyksi merkitsemäsi julkaisun jälkeen.", "No new releases since the last release you marked as seen.")));
    return;
  }
  for (const release of view.releases) {
    const article = node("article", "change-release");
    const meta = node("div");
    meta.append(node("span", "market-status-chip", release.version || release.id), node("time", "", formatDate(release.publishedAt)));
    const copy = node("div");
    copy.append(node("h3", "", isFi() ? release.titleFi : release.titleEn));
    const list = node("ul");
    for (const item of release.items || []) list.append(node("li", "", isFi() ? item.textFi : item.textEn));
    copy.append(list);
    article.append(meta, copy);
    host.append(article);
  }
}

function populateRegions() {
  const select = byId("region-filter");
  const selected = state.region;
  const regions = [...new Set(countries().map((country) => country.region).filter(Boolean))].sort((a, b) => a.localeCompare(b, isFi() ? "fi" : "en"));
  select.replaceChildren();
  const all = node("option", "", l("Kaikki alueet", "All regions"));
  all.value = "";
  select.append(all);
  for (const region of regions) {
    const option = node("option", "", isFi() ? REGIONS_FI[region] || region : region);
    option.value = region;
    select.append(option);
  }
  select.value = selected;
}

function currentSummary(country) {
  if (!isFi()) {
    const grade = gradeOf(country);
    const hasRoute = coverageOf(country) > 0 || sourceLinksOf(country).length > 0;
    if (grade === "D" && !hasRoute) return "No accepted country-specific numeric market anchor has been transferred yet.";
    if (grade === "D") return "A public regulatory or source route is identified, but no verified annual market-sales series has been transferred.";
    return `Grade ${grade} public evidence is available, but it does not by itself establish complete annual device and e-liquid retail sales.`;
  }
  const value = String(country.current || country.headline || "").trim();
  return value || "Ei vielä hyväksyttyä numeerista markkina-ankkuria.";
}

function filteredCountries() {
  const query = state.countryQuery.trim().toLocaleLowerCase(isFi() ? "fi" : "en");
  return countries().filter((country) => {
    const names = [country.name, country.nameFi, country.iso2, country.iso3].filter(Boolean).join(" ").toLocaleLowerCase(isFi() ? "fi" : "en");
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
    const displayName = isFi() ? country.nameFi || country.name : country.name || country.nameFi;
    row.setAttribute("aria-label", isFi() ? `Avaa maan ${displayName} tiedot` : `Open evidence for ${displayName}`);
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
    const secondaryName = isFi()
      ? (country.name && country.name !== country.nameFi ? country.name : country.iso3 || "")
      : (country.nameFi && country.nameFi !== country.name ? country.nameFi : country.iso3 || "");
    nameCopy.append(node("strong", "", displayName), node("small", "", secondaryName));
    nameBox.append(node("span", "country-code", country.iso2 || "—"), nameCopy);
    nameCell.append(nameBox);

    const gradeCell = node("td");
    const gradeWrap = node("span", "table-grade");
    gradeWrap.append(gradeBadge(gradeOf(country)), node("span", "", gradeOf(country) === "D" ? l("tutkimusjono", "research queue") : l("käytettävissä", "available")));
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
    row.append(nameCell, node("td", "", isFi() ? REGIONS_FI[country.region] || country.region || "—" : country.region || "—"), gradeCell, coverageCell, node("td", "", currentSummary(country)), actionCell);
    body.append(row);
  }
  byId("country-count").textContent = isFi() ? `${list.length} / ${countries().length} maata` : `${list.length} / ${countries().length} countries`;
  byId("country-empty").hidden = list.length !== 0;
}

function openCountry(country) {
  state.openCountry = country;
  const region = isFi() ? REGIONS_FI[country.region] || country.region || "Alue puuttuu" : country.region || "Region missing";
  byId("dialog-country-meta").textContent = isFi()
    ? `${country.iso2 || "—"} · ${region} · evidenssi ${gradeOf(country)}`
    : `${country.iso2 || "—"} · ${region} · evidence ${gradeOf(country)}`;
  byId("dialog-country-name").textContent = isFi() ? country.nameFi || country.name : country.name || country.nameFi;
  const body = byId("dialog-country-body");
  body.replaceChildren();

  const summary = node("div", "dialog-summary");
  summary.append(gradeBadge(gradeOf(country)), node("p", "", currentSummary(country)));
  body.append(summary);

  const dimensionsSection = node("section", "dialog-section");
  dimensionsSection.append(node("h3", "", l("Kattavuus mittareittain", "Coverage by measure")));
  const dimensions = node("div", "dimension-grid");
  for (const [key, labels] of Object.entries(DIMENSION_LABELS)) {
    const status = normalizeDimension(country.dimensions?.[key]);
    const item = node("div", "dimension");
    item.dataset.status = status;
    item.append(node("span", "", l(...labels)), node("span", "", statusLabel(status)));
    dimensions.append(item);
  }
  dimensionsSection.append(dimensions);
  body.append(dimensionsSection);

  const missingSection = node("section", "dialog-section");
  const missing = isFi()
    ? country.missing || "Täydellinen laite-, podi-, neste-, kotimaisen tuotannon ja laittoman markkinan sarja puuttuu."
    : "A verified annual series for devices and e-liquids, taxable volume, realised tax revenue and cross-source market reconciliation remains outstanding.";
  missingSection.append(node("h3", "", l("Keskeiset puutteet", "Key gaps")), node("p", "", missing));
  body.append(missingSection);

  const route = country.nextStep || country.how || country.researchRoute;
  if (route || !isFi()) {
    const routeSection = node("section", "dialog-section");
    const routeText = isFi() ? route : "Reproduce the strongest official sales, excise or customs dataset for a consistent year and product scope, then document query parameters and archive the source.";
    routeSection.append(node("h3", "", l("Seuraava varmennusreitti", "Next verification route")), node("p", "", routeText));
    body.append(routeSection);
  }

  const links = sourceLinksOf(country);
  const sourcesSection = node("section", "dialog-section");
  sourcesSection.append(node("h3", "", isFi() ? `Julkiset lähteet (${links.length})` : `Public sources (${links.length})`));
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
    sourcesSection.append(node("p", "", l("Ei vielä maakohtaista hyväksyttyä lähdelinkkiä.", "No accepted country-specific public source link yet.")));
  }
  body.append(sourcesSection);

  const dialog = byId("country-dialog");
  if (!dialog.open && typeof dialog.showModal === "function") dialog.showModal();
}

function filteredEvidence() {
  const query = state.evidenceQuery.trim().toLocaleLowerCase(isFi() ? "fi" : "en");
  return evidenceItems().filter((item) => {
    const localized = [evidenceTitle(item), evidenceCoverage(item), evidenceUse(item)];
    const haystack = [item.title, item.coverage, item.use, item.market, item.source, ...localized].filter(Boolean).join(" ").toLocaleLowerCase(isFi() ? "fi" : "en");
    const grade = String(item.grade || "").toUpperCase();
    return (!query || haystack.includes(query)) && (!state.evidenceGrade || grade === state.evidenceGrade);
  });
}

function evidenceTitle(item) {
  return isFi() ? item.title || "Nimetön lähde" : EVIDENCE_TITLES_EN[item.evidenceId] || "Untitled source";
}

function evidenceCoverage(item) {
  if (isFi()) return item.coverage || item.detail || "";
  const codes = Array.isArray(item.countries) ? item.countries : [];
  const names = codes.map((code) => countries().find((country) => country.iso2 === code)?.name || code);
  return `Curated country coverage (${codes.length}): ${names.join(", ") || "not specified"}.`;
}

function evidenceUse(item) {
  if (isFi()) return item.use || item.limit || "";
  return EVIDENCE_USE_EN[item.claimType] || "Supporting public source; verify the measure, period, scope and limitations before use.";
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
    top.append(node("span", "source-host", url ? new URL(url).hostname : l("lähde puuttuu", "source missing")));
    card.append(top, node("h3", "", evidenceTitle(item)), node("p", "", evidenceCoverage(item)), node("p", "evidence-use", evidenceUse(item)));
    if (url) {
      const link = node("a", "", l("Avaa alkuperäinen lähde →", "Open original source →"));
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
      node("p", "", isFi() ? item.detail || item.description || item.statement || "" : LEGAL_EN[item.legalId] || "Official legal record; verify its current procedural status and jurisdictional scope before reliance.")
    );
    const url = safeExternalUrl(item.url || item.sourceUrl);
    if (url) {
      const link = node("a", "", l("Virallinen lähde →", "Official source →"));
      link.href = url;
      link.target = "_blank";
      link.rel = "noreferrer";
      li.append(link);
    }
    host.append(li);
  }
  if (!timeline.length) host.append(node("li", "", l("Prosessitietoa ei voitu ladata.", "Procedural records could not be loaded.")));

  const gates = isFi() ? [
    { label: "Saksan mitättömyysasia", status: "valitus vireillä" },
    { label: "Loukkaustuomio", status: "vahvistettu" },
    { label: "Euromääräinen korvaus", status: "ei julkinen" },
    { label: "Toteutunut kassavirta", status: "ei vahvistettu" }
  ] : [
    { label: "German nullity action", status: "appeal pending" },
    { label: "Infringement judgment", status: "verified record" },
    { label: "Monetary damages", status: "not public" },
    { label: "Realised cash flow", status: "not verified" }
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
  const methods = isFi() ? FALLBACK_METHODS.fi : FALLBACK_METHODS.en;
  const host = byId("method-cards");
  host.replaceChildren();
  methods.slice(0, 8).forEach((item, index) => {
    const card = node("article", "method-card");
    card.append(node("span", "", String(index + 1).padStart(2, "0")), node("h3", "", item.title || item.name), node("p", "", item.text || item.description));
    host.append(card);
  });
  const rules = isFi() ? FALLBACK_RULES.fi : FALLBACK_RULES.en;
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
  if (whatsappUrl) byId("whatsapp-link").href = `${whatsappUrl}?text=${encodeURIComponent(l("Hei Jouni, minulla on uutta lähdeaineistoa Pixanin markkina-analyysiin.", "Hi Jouni, I have new source material for the Pixan market analysis."))}`;
  const emailUrl = /^mailto:/.test(email || "") ? email : email ? `mailto:${email}` : null;
  if (emailUrl) byId("email-link").href = `${emailUrl}${emailUrl.includes("?") ? "&" : "?"}subject=${encodeURIComponent(l("Pixan-markkina-analyysi – uusi lähdeaineisto", "Pixan market analysis – new source material"))}`;
}

function createCoverNote(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const status = byId("cover-note-status");
  if (!form.reportValidity()) {
    status.textContent = l("Täytä tähdellä merkityt kentät ja vahvista toimitusoikeus.", "Complete the required fields and confirm your right to submit the material.");
    return;
  }
  const values = Object.fromEntries(new FormData(form).entries());
  const measure = MEASURE_LABELS[values.measure] ? l(...MEASURE_LABELS[values.measure]) : values.measure;
  const lines = isFi() ? [
    "PIXAN GLOBAL MARKET EVIDENCE – AINEISTON SAATE", "",
    `Luotu: ${new Date().toISOString()}`, `Maa tai alue: ${values.country}`, `Ajanjakso: ${values.period}`,
    `Julkaisija: ${values.publisher}`, `Lähde-URL: ${values.sourceUrl || "ei ilmoitettu"}`,
    `Mittarityyppi: ${measure}`, `Lähettäjä / organisaatio: ${values.sender || "ei ilmoitettu"}`, "",
    "KUVAUS, TODISTUSARVO JA RAJAT", values.description, "", "TOIMITUSOIKEUS",
    "Lähettäjä on vahvistanut, että aineiston saa toimittaa tarkistettavaksi.",
    "Aineistoa ei hyväksytä eikä julkaista automaattisesti.", "",
    "Lisää tämä TXT-tiedosto samaan Dropbox-lähetykseen alkuperäisten tiedostojen kanssa."
  ] : [
    "PIXAN GLOBAL MARKET EVIDENCE – MATERIAL COVER NOTE", "",
    `Created: ${new Date().toISOString()}`, `Country or region: ${values.country}`, `Period: ${values.period}`,
    `Publisher: ${values.publisher}`, `Source URL: ${values.sourceUrl || "not provided"}`,
    `Measure type: ${measure}`, `Sender / organisation: ${values.sender || "not provided"}`, "",
    "DESCRIPTION, EVIDENCE VALUE AND LIMITS", values.description, "", "RIGHT TO SUBMIT",
    "The sender has confirmed that the material may be submitted for review.",
    "The material is not accepted or published automatically.", "",
    "Include this TXT file in the same Dropbox submission as the original files."
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
  const link = document.createElement("a");
  const slug = String(values.country).normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-zA-Z0-9]+/g, "-").replace(/^-|-$/g, "").toUpperCase() || "AINEISTO";
  link.href = URL.createObjectURL(blob);
  link.download = isFi() ? `PIXAN_AINEISTON_SAATE_${slug}.txt` : `PIXAN_MATERIAL_COVER_NOTE_${slug}.txt`;
  link.click();
  URL.revokeObjectURL(link.href);
  status.textContent = l("Saate ladattu. Lisää se tiedostojen kanssa Dropbox-lähetykseen.", "Cover note downloaded. Include it with the files in your Dropbox submission.");
}

function setTab(tab, options = {}) {
  const allowed = new Set(["overview", "market", "countries", "evidence", "legal", "method", "submit"]);
  state.tab = allowed.has(tab) ? tab : "overview";
  document.querySelectorAll("[data-panel]").forEach((panel) => { panel.hidden = panel.dataset.panel !== state.tab; });
  document.querySelectorAll("[data-tab]").forEach((link) => link.setAttribute("aria-selected", String(link.dataset.tab === state.tab)));
  if (options.updateHash !== false) {
    const url = new URL(location.href);
    url.hash = state.tab;
    history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
  }
  if (options.scroll) byId(`panel-${state.tab}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function bindEvents() {
  document.querySelectorAll("[data-tab]").forEach((link) => link.addEventListener("click", (event) => {
    event.preventDefault();
    setTab(link.dataset.tab, { scroll: true });
  }));
  document.querySelectorAll('a[href="#market"], a[href="#countries"], a[href="#submit"]').forEach((link) => link.addEventListener("click", (event) => {
    event.preventDefault();
    setTab(link.getAttribute("href").slice(1), { scroll: true });
  }));
  byId("country-search").addEventListener("input", (event) => { state.countryQuery = event.target.value; renderCountries(); });
  byId("region-filter").addEventListener("change", (event) => { state.region = event.target.value; renderCountries(); });
  byId("grade-filter").addEventListener("change", (event) => { state.grade = event.target.value; renderCountries(); });
  byId("evidence-search").addEventListener("input", (event) => { state.evidenceQuery = event.target.value; renderEvidence(); });
  byId("evidence-grade-filter").addEventListener("change", (event) => { state.evidenceGrade = event.target.value; renderEvidence(); });
  byId("cover-note-form").addEventListener("submit", createCoverNote);
  byId("changes-mark-seen").addEventListener("click", markChangesSeen);
  byId("country-dialog").querySelector(".dialog-close").addEventListener("click", () => { state.openCountry = null; byId("country-dialog").close(); });
  byId("country-dialog").addEventListener("click", (event) => {
    if (event.target === byId("country-dialog")) { state.openCountry = null; byId("country-dialog").close(); }
  });
  byId("country-dialog").addEventListener("cancel", () => { state.openCountry = null; });
  byId("country-dialog").addEventListener("keydown", (event) => {
    if (event.key === "Escape") state.openCountry = null;
  });
  byId("country-dialog").addEventListener("close", () => { state.openCountry = null; });
  window.addEventListener("hashchange", () => setTab(location.hash.slice(1), { updateHash: false, scroll: true }));
  document.addEventListener("pixan:languagechange", () => {
    if (!state.data) return;
    renderLocalizedView();
  });
}

function renderLocalizedView() {
  renderMeta();
  renderMetrics();
  renderCoverageBars();
  renderReadiness();
  renderMarket();
  renderChangesSinceVisit();
  populateRegions();
  renderCountries();
  renderEvidence();
  renderLegal();
  renderMethod();
  renderSubmission();
  if (state.openCountry) openCountry(state.openCountry);
}

function renderMeta() {
  const snapshot = valueAt(state.data, ["meta.generatedAt", "meta.snapshotDate", "meta.updatedAt"], "");
  const sourceCommit = valueAt(state.data, ["meta.sourceCommit", "meta.legacySourceCommit", "sourceAttribution.commit"], "—");
  byId("snapshot-date").textContent = formatDate(snapshot);
  byId("snapshot-date").dateTime = snapshot;
  byId("source-commit").textContent = String(sourceCommit).slice(0, 9);
}

async function loadData() {
  const [atlasResult, marketResult, changelogResult] = await Promise.allSettled([
    fetch("data/atlas.json", { cache: "no-store" }),
    fetch("data/market-values.json", { cache: "no-store" }),
    fetch("data/changelog.json", { cache: "no-store" })
  ]);
  if (atlasResult.status !== "fulfilled" || !atlasResult.value.ok) throw new Error(`Atlas HTTP ${atlasResult.status === "fulfilled" ? atlasResult.value.status : "network error"}`);
  const data = await atlasResult.value.json();
  if (!Array.isArray(data.countries) || data.countries.length !== 195) throw new Error("Country universe validation failed");
  state.data = data;

  try {
    if (marketResult.status !== "fulfilled" || !marketResult.value.ok) throw new Error(`HTTP ${marketResult.status === "fulfilled" ? marketResult.value.status : "network error"}`);
    const marketData = await marketResult.value.json();
    if (!Array.isArray(marketData.observations) || !Array.isArray(marketData.sources) || !Array.isArray(marketData.models)) throw new Error("schema validation failed");
    state.marketData = marketData;
  } catch (error) {
    state.marketData = null;
    console.warn("Optional market-value dataset unavailable", error);
  }

  try {
    if (changelogResult.status !== "fulfilled" || !changelogResult.value.ok) throw new Error(`HTTP ${changelogResult.status === "fulfilled" ? changelogResult.value.status : "network error"}`);
    const changelog = await changelogResult.value.json();
    if (!Array.isArray(changelog.releases) || !changelog.releases.length) throw new Error("schema validation failed");
    state.changelog = changelog;
  } catch (error) {
    state.changelog = null;
    console.warn("Optional changelog unavailable", error);
  }
  prepareChangeView();
}

async function init() {
  bindEvents();
  try {
    await loadData();
    renderLocalizedView();
    const initialTab = location.hash.slice(1) || "overview";
    setTab(initialTab, { updateHash: false });
    if (location.hash) requestAnimationFrame(() => byId(`panel-${state.tab}`)?.scrollIntoView({ behavior: "auto", block: "start" }));
  } catch (error) {
    console.error(error);
    byId("load-error").hidden = false;
  }
}

init();
