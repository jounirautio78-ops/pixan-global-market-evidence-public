"use strict";

(() => {
  const root = document.querySelector("[data-paid-data]");
  if (!root) return;

  const EXPECTED_OUTREACH = new Map([
    ["ecig-global-market-database", "sent"],
    ["euromonitor-passport-nicotine", "sent"],
    ["niq-rms-pilot", "blocked_not_submitted"],
    ["circana-us-tobacco-pilot", "submitted_confirmation_received"]
  ]);
  let programme = null;

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

  function validHttps(value) {
    try {
      const url = new URL(value);
      return url.protocol === "https:" && Boolean(url.hostname) && !url.username && !url.password;
    } catch (_) {
      return false;
    }
  }

  function validate(raw) {
    if (!raw || raw.schemaVersion !== 1
      || raw.status !== "decision_support_only_no_purchase_authorised"
      || raw.version !== "2026.07.23-2"
      || !validDate(raw.asOf)) {
      throw new Error("unsupported procurement programme");
    }
    if (!Array.isArray(raw.weights) || raw.weights.length !== 6
      || Math.abs(raw.weights.reduce((sum, item) => sum + Number(item.weight), 0) - 1) > 1e-9) {
      throw new Error("invalid transparent score weights");
    }
    if (!Array.isArray(raw.packageOptions) || raw.packageOptions.length !== 3
      || !Array.isArray(raw.goCriteria) || raw.goCriteria.length < 5
      || !Array.isArray(raw.stopCriteria) || raw.stopCriteria.length < 5) {
      throw new Error("invalid procurement gates");
    }
    if (!Array.isArray(raw.items) || raw.items.length !== 11) {
      throw new Error("expected 11 paid-data items");
    }
    const ranks = new Set();
    const itemIds = new Set();
    for (const item of raw.items) {
      if (!Number.isInteger(item.rank) || item.rank < 1 || item.rank > 11 || ranks.has(item.rank)) {
        throw new Error("invalid procurement rank");
      }
      ranks.add(item.rank);
      if (typeof item.itemId !== "string" || !item.itemId.trim() || itemIds.has(item.itemId)) {
        throw new Error("invalid procurement item ID");
      }
      itemIds.add(item.itemId);
      if (!["public_list_price", "vendor_quote"].includes(item.priceType)
        || typeof item.vendor !== "string" || !item.vendor.trim()
        || typeof item.product !== "string" || !item.product.trim()
        || typeof item.priceDisplay !== "string" || !item.priceDisplay.trim()
        || !Number.isFinite(item.weightedScore) || item.weightedScore < 1 || item.weightedScore > 5
        || !Array.isArray(item.sourceUrls) || !item.sourceUrls.length
        || item.sourceUrls.some((url) => !validHttps(url))) {
        throw new Error("invalid procurement item");
      }
      if (item.priceType === "vendor_quote"
        && (item.priceAmount !== null || item.currency !== null || !/quote/i.test(item.priceDisplay))) {
        throw new Error("quote-only item exposes an unsupported price");
      }
    }
    if (!Array.isArray(raw.outreach) || raw.outreach.length !== EXPECTED_OUTREACH.size) {
      throw new Error("invalid outreach record count");
    }
    const outreachIds = new Set();
    for (const record of raw.outreach) {
      const keys = Object.keys(record || {}).sort();
      const expectedKeys = ["itemId", "noteEn", "noteFi", "recordedOn", "state"];
      if (keys.length !== expectedKeys.length
        || keys.some((key, index) => key !== expectedKeys[index])
        || !itemIds.has(record.itemId)
        || outreachIds.has(record.itemId)
        || record.state !== EXPECTED_OUTREACH.get(record.itemId)
        || !validDate(record.recordedOn)
        || record.recordedOn > raw.asOf
        || typeof record.noteEn !== "string" || !record.noteEn.trim()
        || typeof record.noteFi !== "string" || !record.noteFi.trim()) {
        throw new Error("invalid public outreach record");
      }
      outreachIds.add(record.itemId);
    }
    if ([...EXPECTED_OUTREACH.keys()].some((itemId) => !outreachIds.has(itemId))) {
      throw new Error("outreach item set differs");
    }
    return raw;
  }

  function outreachLabel(state) {
    const labels = {
      sent: l("Pyyntö lähetetty", "Request sent"),
      blocked_not_submitted: l("Ei lähetetty · ehtoraja", "Not submitted · terms gate"),
      submitted_confirmation_received: l("Vastaanotto vahvistettu", "Submission confirmed")
    };
    return labels[state] || l("Ei aloitettu", "Not started");
  }

  function renderPackages() {
    const container = root.querySelector("[data-paid-data-packages]");
    container.replaceChildren(...programme.packageOptions.map((option, index) => {
      const card = node("article", "paid-data-package");
      card.append(
        node("span", "paid-data-package-rank", String(index + 1).padStart(2, "0")),
        node("h3", "", isFi() ? option.nameFi : option.nameEn),
        node("p", "", isFi() ? option.contentsFi : option.contentsEn),
        node("strong", "", option.knownPrice),
        node("small", "", isFi() ? option.unknownComponentsFi : option.unknownComponentsEn)
      );
      return card;
    }));
    container.hidden = false;
  }

  function renderItems() {
    const tbody = root.querySelector("[data-paid-data-items]");
    const rows = [...programme.items].sort((left, right) => left.rank - right.rank);
    tbody.replaceChildren(...rows.map((item) => {
      const outreach = programme.outreach.find((record) => record.itemId === item.itemId);
      const row = document.createElement("tr");
      const priority = node("td", "paid-data-priority");
      priority.append(
        node("span", "bankability-rank", `#${String(item.rank).padStart(2, "0")} · ${item.priorityCode}`),
        node("strong", "", `${item.vendor}`),
        node("small", "", item.product)
      );
      if (outreach) {
        priority.append(
          node(
            "span",
            `paid-data-outreach paid-data-outreach-${outreach.state}`,
            outreachLabel(outreach.state)
          ),
          node("small", "paid-data-outreach-date", outreach.recordedOn)
        );
      }
      const role = node("td", "");
      role.append(
        node("strong", "", isFi() ? item.roleFi : item.roleEn),
        node("p", "", isFi() ? item.coverageFi : item.coverageEn)
      );
      const price = node("td", "");
      price.append(
        node("strong", "paid-data-price", item.priceDisplay),
        node("small", "", item.priceType === "vendor_quote"
          ? l("Tarjous vaaditaan", "Vendor quote required")
          : l("Julkinen listahavainto", "Public list-price observation"))
      );
      const decision = node("td", "");
      decision.append(
        node("p", "", isFi() ? item.decisionFi : item.decisionEn),
        node("small", "", isFi() ? item.conditionsFi : item.conditionsEn)
      );
      const score = node("td", "paid-data-score");
      score.append(
        node("strong", "", item.weightedScore.toFixed(2)),
        node("small", "", l("asteikko 1–5", "scale 1–5"))
      );
      const source = node("td", "");
      const link = node("a", "market-source-link", l("Toimittajasivu", "Vendor page"));
      link.href = item.sourceUrls[0];
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      source.append(link, node("small", "", `${l("Tarkistettu", "Verified")} ${item.verifiedOn}`));
      row.append(priority, role, price, decision, score, source);
      return row;
    }));
    root.querySelector("[data-paid-data-table]").hidden = false;
  }

  function renderReady() {
    renderPackages();
    renderItems();
    root.querySelector("[data-paid-data-actions]").hidden = false;
    root.querySelector("[data-paid-data-note]").hidden = false;
    const publicPrices = programme.items.filter((item) => item.priceType === "public_list_price").length;
    const quotes = programme.items.length - publicPrices;
    const submitted = programme.outreach.filter((item) =>
      ["sent", "submitted_confirmation_received"].includes(item.state)).length;
    const blocked = programme.outreach.filter((item) => item.state === "blocked_not_submitted").length;
    const status = root.querySelector("[data-paid-data-status]");
    status.className = "bank-package-status bank-package-status-ready";
    status.replaceChildren(
      node("span", "bank-package-status-dot", ""),
      node("span", "", l(
        `${programme.items.length} hankintakohdetta · ${submitted} pyyntöä kirjattu · ${blocked} estynyt · ei ostovaltuutta.`,
        `${programme.items.length} procurement items · ${submitted} requests recorded · ${blocked} blocked · no purchase authorised.`
      ))
    );
    status.firstElementChild.setAttribute("aria-hidden", "true");
    const meta = root.querySelector("[data-paid-data-meta]");
    meta.textContent = `${programme.version} · ${programme.asOf}`;
    root.setAttribute("aria-busy", "false");
  }

  function renderFailure() {
    root.querySelector("[data-paid-data-packages]").hidden = true;
    root.querySelector("[data-paid-data-actions]").hidden = true;
    root.querySelector("[data-paid-data-table]").hidden = true;
    root.querySelector("[data-paid-data-note]").hidden = true;
    const status = root.querySelector("[data-paid-data-status]");
    status.className = "bank-package-status bank-package-status-error";
    status.replaceChildren(
      node("span", "bank-package-status-dot", ""),
      node("strong", "", l(
        "Maksullisten lähteiden hankintalistaa ei voitu ladata.",
        "The paid-data procurement shortlist could not be loaded."
      ))
    );
    status.firstElementChild.setAttribute("aria-hidden", "true");
    root.setAttribute("aria-busy", "false");
  }

  async function init() {
    try {
      const response = await fetch("data/paid-data-procurement.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      programme = validate(await response.json());
      renderReady();
    } catch (error) {
      console.warn("Paid-data procurement shortlist unavailable", error);
      renderFailure();
    }
  }

  document.addEventListener("pixan:languagechange", () => {
    if (programme) renderReady();
  });
  init();
})();
