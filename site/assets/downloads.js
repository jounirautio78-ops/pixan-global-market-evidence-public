"use strict";

(() => {
  const roots = [...document.querySelectorAll("[data-bank-package]")];
  if (!roots.length) return;

  const EXPECTED = [
    {
      id: "short-deck",
      path: "downloads/pixan-bank-deck-short-fi.pptx",
      countKey: "slideCount",
      expectedCount: 6,
      marker: "06"
    },
    {
      id: "medium-deck",
      path: "downloads/pixan-bank-deck-medium-fi.pptx",
      countKey: "slideCount",
      expectedCount: 12,
      marker: "12"
    },
    {
      id: "large-deck",
      path: "downloads/pixan-bank-deck-large-fi.pptx",
      countKey: "slideCount",
      marker: "L"
    },
    {
      id: "evidence-register",
      path: "downloads/pixan-bank-evidence-register-fi.xlsx",
      countKey: "rowCount",
      marker: "XLSX"
    }
  ];
  const EXPECTED_BY_PATH = new Map(EXPECTED.map((item) => [item.path, item]));
  let manifest = null;
  let loadError = null;

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

  function nonEmpty(value) {
    return typeof value === "string" && Boolean(value.trim());
  }

  function positiveInteger(value) {
    return Number.isInteger(value) && value > 0;
  }

  function normalizePath(value) {
    if (!nonEmpty(value)) return "";
    return value.trim().replace(/^\.\//, "");
  }

  function normalizeArtifact(raw) {
    if (!raw || typeof raw !== "object") throw new Error("invalid artifact");
    const path = normalizePath(raw.path || raw.href || raw.url);
    const expected = EXPECTED_BY_PATH.get(path);
    const id = nonEmpty(raw.id) ? raw.id.trim() : expected?.id;
    if (!expected || id !== expected.id) throw new Error("unexpected artifact path or ID");

    const sha256 = String(raw.sha256 || raw.sha || "").trim().toLowerCase();
    const bytes = Number(raw.bytes ?? raw.size);
    const count = Number(raw[expected.countKey]);
    const fileName = String(raw.fileName || path.split("/").pop() || "").trim();
    if (!/^[a-f0-9]{64}$/.test(sha256)) throw new Error("invalid artifact hash");
    if (!positiveInteger(bytes)) throw new Error("invalid artifact size");
    if (!positiveInteger(count)) throw new Error("invalid artifact count");
    if (expected.expectedCount && count !== expected.expectedCount) throw new Error("unexpected slide count");
    if (fileName !== path.split("/").pop()) throw new Error("artifact filename mismatch");

    return {
      ...raw,
      id,
      path,
      fileName,
      sha256,
      bytes,
      [expected.countKey]: count,
      marker: expected.marker,
      countKey: expected.countKey
    };
  }

  function normalizeManifest(raw) {
    if (!raw || typeof raw !== "object") throw new Error("invalid manifest");
    if (raw.schemaVersion !== 1 || raw.generatedFromPublicDataOnly !== true) {
      throw new Error("unsupported manifest boundary");
    }

    const releaseObject = raw.release && typeof raw.release === "object" ? raw.release : {};
    const release = {
      id: releaseObject.id || raw.releaseId || "",
      version: releaseObject.version || raw.version || raw.releaseVersion || "",
      publishedAt: releaseObject.publishedAt || raw.publishedAt || raw.asOf || ""
    };
    if (![release.id, release.version, release.publishedAt].every(nonEmpty)) throw new Error("invalid release metadata");
    if (Number.isNaN(new Date(release.publishedAt).valueOf())) throw new Error("invalid release timestamp");
    if (!nonEmpty(raw.asOf) || !/^\d{4}-\d{2}-\d{2}$/.test(raw.asOf)) throw new Error("invalid dataset date");
    if (Number.isNaN(new Date(`${raw.asOf}T12:00:00Z`).valueOf())) throw new Error("invalid dataset date");
    if (raw.language !== "fi") throw new Error("unexpected package language");
    if (!raw.publicBoundary || !nonEmpty(raw.publicBoundary.fi) || !nonEmpty(raw.publicBoundary.en)) {
      throw new Error("missing public boundary");
    }
    if (!Array.isArray(raw.inputs) || !raw.inputs.length || raw.inputs.some((input) => (
      !input || typeof input !== "object" || !nonEmpty(input.path) || /(?:^|\/)\.\.(?:\/|$)/.test(input.path)
      || !/^[a-f0-9]{64}$/i.test(String(input.sha256 || ""))
    ))) throw new Error("invalid public input inventory");

    const rawArtifacts = raw.artifacts || raw.files || raw.outputs;
    if (!Array.isArray(rawArtifacts)) throw new Error("missing artifacts");
    const byId = new Map(rawArtifacts.map((item) => {
      const normalized = normalizeArtifact(item);
      return [normalized.id, normalized];
    }));
    if (byId.size !== EXPECTED.length || EXPECTED.some((item) => !byId.has(item.id))) {
      throw new Error("incomplete artifact set");
    }

    return {
      ...raw,
      release,
      artifacts: EXPECTED.map((item) => byId.get(item.id))
    };
  }

  function formatDate(value) {
    const date = /^\d{4}-\d{2}-\d{2}$/.test(value)
      ? new Date(`${value}T12:00:00Z`)
      : new Date(value);
    if (Number.isNaN(date.valueOf())) return value;
    return new Intl.DateTimeFormat(isFi() ? "fi-FI" : "en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
      timeZone: "UTC"
    }).format(date);
  }

  function formatBytes(bytes) {
    const units = ["B", "KB", "MB", "GB"];
    let value = bytes;
    let unitIndex = 0;
    while (value >= 1000 && unitIndex < units.length - 1) {
      value /= 1000;
      unitIndex += 1;
    }
    const digits = unitIndex === 0 || value >= 10 ? 0 : 1;
    return `${new Intl.NumberFormat(isFi() ? "fi-FI" : "en-GB", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits
    }).format(value)} ${units[unitIndex]}`;
  }

  function artifactTitle(artifact) {
    const title = isFi() ? artifact.titleFi : artifact.titleEn;
    if (nonEmpty(title)) return title;
    const fallback = {
      "short-deck": l("Suppea pankkidekki", "Concise bank deck"),
      "medium-deck": l("Keskikokoinen pankkidekki", "Core bank deck"),
      "large-deck": l("Laaja pankkidekki", "Extended bank deck"),
      "evidence-register": "Evidence Register"
    };
    return fallback[artifact.id];
  }

  function artifactDescription(artifact) {
    const descriptions = {
      "short-deck": l(
        "Nopea johdon, lainanantajan tai ostajan yleiskuva.",
        "A rapid overview for management, lenders or prospective buyers."
      ),
      "medium-deck": l(
        "12 dian rahoitusrakenne: teesi, IP, markkina, näyttö, malli ja riskit.",
        "A 12-slide financing narrative covering thesis, IP, market, evidence, model and risks."
      ),
      "large-deck": l(
        "Laajin julkinen tarkistusversio lähteineen, rajoineen ja jatkotoimineen.",
        "The fullest public review version, including sources, limits and next actions."
      ),
      "evidence-register": l(
        "Väitekohtainen näyttö, lähde, laskentatapa, oletukset, luottamustaso ja puutteet.",
        "Claim-level evidence, sources, calculations, assumptions, confidence and gaps."
      )
    };
    return descriptions[artifact.id];
  }

  function countLabel(artifact) {
    if (artifact.countKey === "slideCount") {
      return isFi() ? `${artifact.slideCount} diaa` : `${artifact.slideCount} slides`;
    }
    return isFi() ? `${artifact.rowCount} evidenssiriviä` : `${artifact.rowCount} evidence rows`;
  }

  function metadataRow(label, value, className = "") {
    const row = element("li", className);
    row.append(element("span", "", label), element("strong", "", value));
    return row;
  }

  function renderArtifact(artifact) {
    const card = element("article", "bank-package-card");
    card.setAttribute("role", "listitem");

    const top = element("div", "bank-package-card-top");
    const marker = element("span", "bank-package-card-marker", artifact.marker);
    marker.setAttribute("aria-hidden", "true");
    const badges = element("div", "bank-package-badges");
    badges.append(
      element("span", "bank-package-format", artifact.path.endsWith(".xlsx") ? "XLSX" : "PPTX"),
      element("span", "bank-package-language", l("Suomeksi", "Finnish"))
    );
    top.append(marker, badges);

    const heading = element("h3", "", artifactTitle(artifact));
    const description = element("p", "bank-package-card-description", artifactDescription(artifact));
    const metadata = element("ul", "bank-package-card-meta");
    metadata.append(
      metadataRow(l("Sisältö", "Contents"), countLabel(artifact)),
      metadataRow(l("Tiedostokoko", "File size"), formatBytes(artifact.bytes))
    );
    const hashRow = element("li", "bank-package-hash");
    const hashLabel = element("span", "", "SHA-256");
    const hash = element("code", "", `${artifact.sha256.slice(0, 12)}…`);
    hash.title = artifact.sha256;
    hashRow.append(hashLabel, hash);
    metadata.append(hashRow);

    const url = new URL(artifact.path, document.baseURI);
    url.searchParams.set("sha", artifact.sha256.slice(0, 16));
    const link = element(
      "a",
      "button button-primary bank-package-download",
      artifact.id === "evidence-register" ? l("Lataa Evidence Register", "Download Evidence Register") : l("Lataa dekki", "Download deck")
    );
    link.href = url.href;
    link.download = artifact.fileName;
    link.setAttribute("aria-label", `${link.textContent}: ${artifactTitle(artifact)}, ${countLabel(artifact)}`);
    const filename = element("small", "bank-package-filename", artifact.fileName);

    card.append(top, heading, description, metadata, link, filename);
    return card;
  }

  function renderReady(root) {
    const release = root.querySelector("[data-bank-package-release]");
    root.querySelector("[data-bank-package-version]").textContent = manifest.release.version;
    root.querySelector("[data-bank-package-as-of]").textContent = formatDate(manifest.asOf);
    root.querySelector("[data-bank-package-count]").textContent = String(manifest.artifacts.length);
    release.hidden = false;

    const boundary = root.querySelector("[data-bank-package-boundary]");
    boundary.textContent = isFi() ? manifest.publicBoundary.fi : manifest.publicBoundary.en;

    const grid = root.querySelector("[data-bank-package-artifacts]");
    grid.replaceChildren(...manifest.artifacts.map(renderArtifact));
    grid.hidden = false;

    const note = root.querySelector("[data-bank-package-note]");
    note.hidden = false;

    const status = root.querySelector("[data-bank-package-status]");
    status.className = "bank-package-status bank-package-status-ready";
    status.replaceChildren(
      element("span", "bank-package-status-dot", ""),
      element("span", "", l(
        `${manifest.artifacts.length} tiedostoa tarkistettu julkaisumanifestia vasten.`,
        `${manifest.artifacts.length} files verified against the release manifest.`
      ))
    );
    status.firstElementChild.setAttribute("aria-hidden", "true");
    root.dataset.bankPackageState = "ready";
    root.setAttribute("aria-busy", "false");
  }

  function renderFailure(root) {
    root.querySelector("[data-bank-package-release]").hidden = true;
    root.querySelector("[data-bank-package-artifacts]").replaceChildren();
    root.querySelector("[data-bank-package-artifacts]").hidden = true;
    root.querySelector("[data-bank-package-note]").hidden = true;

    const status = root.querySelector("[data-bank-package-status]");
    status.className = "bank-package-status bank-package-status-error";
    const copy = element("div", "");
    copy.append(
      element("strong", "", l("Lataukset eivät ole juuri nyt varmennettavissa", "Downloads cannot be verified right now")),
      element("p", "", l(
        "Pakettimanifestia ei voitu ladata tai se ei läpäissyt tarkistusta. Vanhentuneita tiedostoja ei tarjota. Yritä myöhemmin uudelleen tai käytä sivuston lähdeaineistoja.",
        "The package manifest could not be loaded or did not pass validation. Stale files are not offered. Try again later or use the source datasets on this site."
      ))
    );
    status.replaceChildren(element("span", "bank-package-status-dot", ""), copy);
    status.firstElementChild.setAttribute("aria-hidden", "true");
    root.dataset.bankPackageState = "error";
    root.setAttribute("aria-busy", "false");
  }

  function render() {
    roots.forEach((root) => {
      if (manifest) renderReady(root);
      else if (loadError) renderFailure(root);
    });
  }

  async function load() {
    try {
      const response = await fetch("data/bank-package-manifest.json", {
        cache: "no-store",
        credentials: "same-origin"
      });
      if (!response.ok) throw new Error(`Bank package manifest HTTP ${response.status}`);
      manifest = normalizeManifest(await response.json());
    } catch (error) {
      loadError = error;
      console.warn("Bank package downloads unavailable", error);
    }
    render();
  }

  document.addEventListener("pixan:languagechange", render);
  load();
})();
