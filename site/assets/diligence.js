"use strict";

(() => {
  const tierRoot = document.querySelector("#diligence-tier-grid");
  if (!tierRoot) return;

  const EXPECTED_CONTROL_ID = "pixan-investor-disclosure-control-2026-07-28";
  const EXPECTED_TIERS = Object.freeze([
    "public",
    "nda",
    "restricted_clean_team_counsel",
    "board_counsel"
  ]);
  const dynamicRoots = Object.freeze([
    tierRoot,
    document.querySelector("#diligence-audience-grid"),
    document.querySelector("#diligence-reuse-grid"),
    document.querySelector("#diligence-material-facts"),
    document.querySelector("#diligence-hard-gates")
  ]);
  let control = null;

  function isFi() {
    return window.SiteI18n?.isFinnish?.() ?? document.documentElement.lang === "fi";
  }

  function l(fi, en) {
    return window.SiteI18n?.pick?.(fi, en) ?? (isFi() ? fi : en);
  }

  function field(item, base) {
    return String(item?.[`${base}${isFi() ? "Fi" : "En"}`] || "");
  }

  function node(tag, className = "", text = "") {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== "") element.textContent = String(text);
    return element;
  }

  function isNonEmptyString(value) {
    return typeof value === "string" && value.trim().length > 0;
  }

  function hasBilingualFields(item, fields) {
    return fields.every((base) => isNonEmptyString(item?.[`${base}En`]) && isNonEmptyString(item?.[`${base}Fi`]));
  }

  function hasUniqueIds(items, fieldName) {
    if (!Array.isArray(items) || items.length === 0) return false;
    const ids = items.map((item) => item?.[fieldName]);
    return ids.every(isNonEmptyString) && new Set(ids).size === ids.length;
  }

  function isIsoDate(value) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(String(value || ""))) return false;
    const parsed = new Date(`${value}T00:00:00Z`);
    return !Number.isNaN(parsed.valueOf()) && parsed.toISOString().slice(0, 10) === value;
  }

  function isSafePublicPath(value) {
    return typeof value === "string"
      && value.startsWith("site/")
      && !value.includes("..")
      && !value.includes("\\")
      && !/[\u0000-\u001f]/.test(value);
  }

  function validate(raw) {
    const tierIds = raw?.accessTiers?.map((tier) => tier.tierId);
    const tiersValid = Array.isArray(tierIds)
      && tierIds.length === EXPECTED_TIERS.length
      && EXPECTED_TIERS.every((tierId, index) => tierIds[index] === tierId)
      && raw.accessTiers.every((tier, index) =>
        tier.order === index + 1
        && hasBilingualFields(tier, ["title", "purpose", "permittedContent", "excludedContent", "releaseRule"])
        && tier.sensitiveMaterialEmbeddedInThisControl === false
      );
    const audiencesValid = hasUniqueIds(raw?.audiences, "audienceId")
      && raw.audiences.every((audience) =>
        hasBilingualFields(audience, ["title", "legitimateUse", "constraint"])
        && EXPECTED_TIERS.includes(audience.defaultTier)
        && Array.isArray(audience.potentialDeeperTiers)
        && audience.potentialDeeperTiers.every((tierId) => EXPECTED_TIERS.includes(tierId))
      );
    const factsValid = hasUniqueIds(raw?.materialFactsThatMustNotBeHidden, "factId")
      && raw.materialFactsThatMustNotBeHidden.every((fact) =>
        hasBilingualFields(fact, ["title", "statement"])
        && fact.mustNotBeOmitted === true
        && EXPECTED_TIERS.includes(fact.minimumDisclosureTier)
        && Array.isArray(fact.publicEvidencePaths)
        && fact.publicEvidencePaths.every(isSafePublicPath)
      );
    const assetsValid = hasUniqueIds(raw?.publicAssetMapping, "assetGroupId")
      && raw.publicAssetMapping.every((asset) =>
        hasBilingualFields(asset, ["title", "publicUse", "limitations"])
        && asset.tierId === "public"
        && isNonEmptyString(asset.versionOrAsOf)
        && Array.isArray(asset.paths)
        && asset.paths.length > 0
        && asset.paths.every(isSafePublicPath)
      );
    const gatesValid = hasUniqueIds(raw?.hardGates, "gateId")
      && raw.hardGates.every((gate) =>
        hasBilingualFields(gate, ["title", "requirement", "evidenceRequired", "failureAction"])
        && Array.isArray(gate.requiredForTiers)
        && gate.requiredForTiers.length > 0
        && gate.requiredForTiers.every((tierId) => EXPECTED_TIERS.includes(tierId) && tierId !== "public")
      );
    const prohibitedValid = hasUniqueIds(raw?.prohibitedPublicItems, "itemId")
      && raw.prohibitedPublicItems.every((item) => hasBilingualFields(item, ["title", "rule"]));
    const safeguardsValid = hasUniqueIds(raw?.safeguards, "safeguardId")
      && raw.safeguards.every((item) =>
        hasBilingualFields(item, ["title"])
        && Array.isArray(item.controlsEn)
        && item.controlsEn.length > 0
        && Array.isArray(item.controlsFi)
        && item.controlsFi.length === item.controlsEn.length
        && item.controlsEn.every(isNonEmptyString)
        && item.controlsFi.every(isNonEmptyString)
      );

    if (!raw
      || raw.schemaVersion !== "1.0"
      || raw.controlId !== EXPECTED_CONTROL_ID
      || !isIsoDate(raw.asOf)
      || raw.controlState !== "fail_closed"
      || !Array.isArray(raw.languages)
      || !raw.languages.includes("en")
      || !raw.languages.includes("fi")
      || raw.publicBoundary?.defaultTier !== "public"
      || raw.publicBoundary?.deeperAccessIsNotGrantedByThisControl !== true
      || !hasBilingualFields(raw.publicBoundary, ["statement", "failClosedRule"])
      || raw.decisionRule?.defaultTier !== "public"
      || raw.decisionRule?.gateLogic !== "all_applicable_gates_must_pass"
      || raw.decisionRule?.noAutomaticPromotion !== true
      || raw.decisionRule?.noPartialOverride !== true
      || raw.decisionRule?.controlGrantsAccess !== false
      || raw.decisionRule?.restrictedMaterialEmbeddedOrLinked !== false
      || !hasBilingualFields(raw.decisionRule, ["decision"])
      || !tiersValid
      || !audiencesValid
      || !factsValid
      || !assetsValid
      || !gatesValid
      || !prohibitedValid
      || !safeguardsValid) {
      throw new Error("Disclosure control failed structural validation.");
    }
    return raw;
  }

  function formatDate(value) {
    return new Intl.DateTimeFormat(isFi() ? "fi-FI" : "en-GB", {
      day: "numeric",
      month: isFi() ? "numeric" : "long",
      year: "numeric",
      timeZone: "UTC"
    }).format(new Date(`${value}T00:00:00Z`));
  }

  function publicHref(path) {
    return path.slice("site/".length);
  }

  function humanPath(path) {
    return path.split("/").pop() || path;
  }

  function tierTitle(tierId) {
    const tier = control.accessTiers.find((candidate) => candidate.tierId === tierId);
    return tier ? field(tier, "title") : tierId;
  }

  function localizeStaticCopy() {
    document.querySelectorAll("[data-copy-en][data-copy-fi]").forEach((element) => {
      element.textContent = element.dataset[isFi() ? "copyFi" : "copyEn"];
    });
    document.querySelectorAll("[data-label-en][data-label-fi]").forEach((element) => {
      element.setAttribute("aria-label", element.dataset[isFi() ? "labelFi" : "labelEn"]);
    });
    document.documentElement.lang = isFi() ? "fi" : "en";
  }

  function renderTiers() {
    const fragment = document.createDocumentFragment();
    control.accessTiers.forEach((tier) => {
      const card = node("article", "diligence-tier-card");
      card.dataset.tier = tier.tierId;
      card.dataset.tierNumber = String(tier.order - 1).padStart(2, "0");
      card.append(node("span", "diligence-tier-badge", `${l("Taso", "Tier")} ${tier.order - 1}`));
      card.append(node("h3", "", field(tier, "title")));
      card.append(node("p", "diligence-tier-purpose", field(tier, "purpose")));

      const permitted = node("div", "diligence-tier-field");
      permitted.append(node("strong", "", l("Sallittu aineisto", "Permitted content")));
      permitted.append(node("p", "", field(tier, "permittedContent")));
      card.append(permitted);

      const excluded = node("div", "diligence-tier-field");
      excluded.append(node("strong", "", l("Rajattu pois", "Excluded")));
      excluded.append(node("p", "", field(tier, "excludedContent")));
      card.append(excluded);

      const release = node("div", "diligence-tier-field diligence-tier-release");
      release.append(node("strong", "", l("Luovutussääntö", "Release rule")));
      release.append(node("p", "", field(tier, "releaseRule")));
      card.append(release);
      fragment.append(card);
    });
    tierRoot.replaceChildren(fragment);
  }

  function renderAudiences() {
    const root = document.querySelector("#diligence-audience-grid");
    const fragment = document.createDocumentFragment();
    control.audiences.forEach((audience) => {
      const card = node("article", "diligence-audience-card");
      const body = node("div");
      body.append(node("h3", "", field(audience, "title")));
      body.append(node("p", "", field(audience, "legitimateUse")));
      card.append(body);
      card.append(node("span", "diligence-audience-tier", `${l("Oletus", "Default")}: ${tierTitle(audience.defaultTier)}`));
      card.append(node("p", "diligence-audience-constraint", field(audience, "constraint")));
      fragment.append(card);
    });
    root.replaceChildren(fragment);
  }

  function renderReuse() {
    const root = document.querySelector("#diligence-reuse-grid");
    const fragment = document.createDocumentFragment();
    control.publicAssetMapping.forEach((asset) => {
      const card = node("article", "diligence-reuse-card");
      card.append(node("code", "", `${asset.assetGroupId} · ${asset.versionOrAsOf}`));
      card.append(node("h3", "", field(asset, "title")));
      card.append(node("p", "", field(asset, "publicUse")));
      card.append(node("p", "diligence-reuse-limit", field(asset, "limitations")));
      const links = node("div", "diligence-reuse-links");
      asset.paths.forEach((path) => {
        const link = node("a", "", humanPath(path));
        link.href = publicHref(path);
        link.setAttribute("aria-label", `${field(asset, "title")}: ${humanPath(path)}`);
        links.append(link);
      });
      card.append(links);
      fragment.append(card);
    });
    root.replaceChildren(fragment);
  }

  function renderFacts() {
    const root = document.querySelector("#diligence-material-facts");
    const fragment = document.createDocumentFragment();
    control.materialFactsThatMustNotBeHidden.forEach((fact) => {
      const item = node("li");
      item.append(node("strong", "", field(fact, "title")));
      item.append(node("p", "", field(fact, "statement")));
      fragment.append(item);
    });
    root.replaceChildren(fragment);
  }

  function renderGates() {
    const root = document.querySelector("#diligence-hard-gates");
    const fragment = document.createDocumentFragment();
    control.hardGates.forEach((gate) => {
      const item = node("li");
      item.append(node("strong", "", field(gate, "title")));
      item.append(node("p", "", field(gate, "requirement")));
      item.append(node("p", "", `${l("Vaadittu näyttö", "Evidence required")}: ${field(gate, "evidenceRequired")}`));
      fragment.append(item);
    });
    root.replaceChildren(fragment);
  }

  function renderRequestLink() {
    const link = document.querySelector("#diligence-request-email");
    const subject = l("Pixan due diligence -pääsypyyntö", "Pixan diligence access request");
    const body = isFi()
      ? [
        "Organisaatio:",
        "Rooli ja toimeksiantaja:",
        "Tarkistuksen tarkoitus:",
        "Päätös tai transaktio, jota tarkistus tukee:",
        "Toivottu aikataulu:",
        "Pyydetyt evidenssiluokat:",
        "Nimetyt vastaanottajat ja neuvonantajat:",
        "Valmius NDA:han: kyllä / ei",
        "",
        "En liitä tähän viestiin luottamuksellista, lisensoitua, henkilötietoja sisältävää tai asianajosalaisuuden alaista aineistoa. Ymmärrän, ettei tämä pyyntö myönnä pääsyä."
      ]
      : [
        "Organisation:",
        "Role and appointing principal:",
        "Review purpose:",
        "Decision or transaction supported:",
        "Expected timetable:",
        "Requested evidence categories:",
        "Named recipients and advisers:",
        "NDA readiness: yes / no",
        "",
        "I am not attaching confidential, licensed, personal or privileged material to this email. I understand that this request does not grant access."
      ];
    const href = `mailto:jouni.rautio78@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body.join("\n"))}`;
    link.href = href;
    link.dataset.i18nBaseHref = href;
    link.hidden = false;
  }

  function render() {
    localizeStaticCopy();
    renderTiers();
    renderAudiences();
    renderReuse();
    renderFacts();
    renderGates();
    renderRequestLink();
    document.querySelector("#diligence-control-version").textContent = `${control.schemaVersion} · ${control.controlState}`;
    const date = document.querySelector("#diligence-control-date");
    date.dateTime = control.asOf;
    date.textContent = formatDate(control.asOf);
    document.querySelector("#diligence-load-error").hidden = true;
    window.SiteI18n?.localizeLinks?.(document);
  }

  function failClosed() {
    control = null;
    dynamicRoots.forEach((root) => root?.replaceChildren());
    localizeStaticCopy();
    document.querySelector("#diligence-control-version").textContent = l("varmennus epäonnistui", "verification failed");
    document.querySelector("#diligence-control-date").textContent = "—";
    document.querySelector("#diligence-load-error").hidden = false;
    const requestLink = document.querySelector("#diligence-request-email");
    requestLink.hidden = true;
  }

  async function load() {
    try {
      const response = await fetch("data/investor-disclosure-control.json", {
        cache: "no-store",
        headers: { Accept: "application/json" }
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      control = validate(await response.json());
      render();
    } catch (error) {
      console.error("Diligence disclosure control unavailable:", error);
      failClosed();
    }
  }

  document.addEventListener("pixan:languagechange", () => {
    if (control) render();
    else failClosed();
  });

  load();
})();
