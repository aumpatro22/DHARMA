/**
 * PROJECT D.H.A.R.M.A. — FORENSIC INTELLIGENCE & CRIME ANALYTICS
 * Clean, real-time client script for incident analysis, modus operandi extraction,
 * Mapbox GL JS spatial radar, and forensic hypotheses.
 */

const MAPBOX_TOKEN = window.MAPBOX_TOKEN || localStorage.getItem('MAPBOX_TOKEN') || '';

let PRESETS_DATA = [];
let CURRENT_RESULT = null;

// Mapbox Globals
let map = null;
let incidentMarker = null;
let snappedMarker = null;
let hotspotMarkers = [];

// DOM Elements
const narrativeInput = document.getElementById("narrativeInput");
const charCount = document.getElementById("charCount");
const btnClearText = document.getElementById("btnClearText");
const citySelect = document.getElementById("citySelect");
const inputLat = document.getElementById("inputLat");
const inputLon = document.getElementById("inputLon");
const btnAnalyze = document.getElementById("btnAnalyze");
const presetContainer = document.getElementById("presetContainer");
const toast = document.getElementById("toastNotification");

// Ticker Elements
const tickerStatus = document.getElementById("tickerStatus");
const tickerLatency = document.getElementById("tickerLatency");

// Tab Navigation
const tabButtons = document.querySelectorAll(".tab-btn");
const tabPanes = document.querySelectorAll(".tab-pane");

// Initialize on Load
document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupTextarea();
  initMapbox();
  loadPresets();
  setupEventListeners();
  checkHealth();
});

// Setup Tab Switching
function setupTabs() {
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTabId = btn.getAttribute("data-tab");
      tabButtons.forEach(b => b.classList.remove("active"));
      tabPanes.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const targetPane = document.getElementById(targetTabId);
      if (targetPane) targetPane.classList.add("active");

      // Invalidate Mapbox size when opening spatial tab
      if (targetTabId === "tab-spatial" && map) {
        setTimeout(() => map.resize(), 150);
      }
    });
  });
}

// ---------------------------------------------------------------------------
// Mapbox GL JS Initialization & Geospatial Map
// ---------------------------------------------------------------------------
function initMapbox() {
  const mapContainer = document.getElementById("mapboxMap");
  if (!mapContainer || typeof mapboxgl === "undefined") {
    console.warn("Mapbox GL JS container or library not available.");
    return;
  }

  mapboxgl.accessToken = MAPBOX_TOKEN;

  try {
    map = new mapboxgl.Map({
      container: "mapboxMap",
      style: "mapbox://styles/mapbox/light-v11",
      center: [-87.6231, 41.8818], // Chicago downtown center
      zoom: 12.5,
      pitch: 45,
      bearing: -17.6,
      antialias: true
    });

    map.addControl(new mapboxgl.NavigationControl(), "top-right");

    // Click on map to sample coordinates
    map.on("click", (e) => {
      const { lng, lat } = e.lngLat;
      if (inputLat) inputLat.value = lat.toFixed(4);
      if (inputLon) inputLon.value = lng.toFixed(4);
      updateIncidentMarker(lat, lng);
      showToast(`Selected coordinates: Lat ${lat.toFixed(4)}, Lon ${lng.toFixed(4)}`);
    });

    map.on("load", () => {
      const lat = parseFloat(inputLat?.value || "41.8818");
      const lon = parseFloat(inputLon?.value || "-87.6231");
      if (!isNaN(lat) && !isNaN(lon)) {
        updateIncidentMarker(lat, lon);
      }
    });

    // Map control buttons
    document.getElementById("btnRecenterMap")?.addEventListener("click", () => {
      const lat = parseFloat(inputLat?.value);
      const lon = parseFloat(inputLon?.value);
      if (!isNaN(lat) && !isNaN(lon) && map) {
        map.flyTo({ center: [lon, lat], zoom: 14, pitch: 45, duration: 1500 });
      }
    });

    document.getElementById("btnFlyChicago")?.addEventListener("click", () => {
      if (citySelect) citySelect.value = "chicago";
      if (inputLat) inputLat.value = "41.8818";
      if (inputLon) inputLon.value = "-87.6231";
      updateIncidentMarker(41.8818, -87.6231);
      if (map) map.flyTo({ center: [-87.6231, 41.8818], zoom: 13, pitch: 45, duration: 1800 });
      showToast("Centered map on Chicago, IL");
    });

    document.getElementById("btnFlySF")?.addEventListener("click", () => {
      if (citySelect) citySelect.value = "sf";
      if (inputLat) inputLat.value = "37.7749";
      if (inputLon) inputLon.value = "-122.4194";
      updateIncidentMarker(37.7749, -122.4194);
      if (map) map.flyTo({ center: [-122.4194, 37.7749], zoom: 13, pitch: 45, duration: 1800 });
      showToast("Centered map on San Francisco, CA");
    });

  } catch (err) {
    console.error("Mapbox initialization error:", err);
  }
}

function updateIncidentMarker(lat, lon) {
  if (!map) return;
  if (incidentMarker) incidentMarker.remove();

  const el = document.createElement("div");
  el.className = "marker-incident";
  el.innerHTML = '<div class="marker-incident-inner"></div>';

  const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
    <div class="map-popup-title">🎯 Incident Location</div>
    <div class="map-popup-stat">Latitude: <strong>${lat.toFixed(4)}</strong></div>
    <div class="map-popup-stat">Longitude: <strong>${lon.toFixed(4)}</strong></div>
  `);

  incidentMarker = new mapboxgl.Marker(el)
    .setLngLat([lon, lat])
    .setPopup(popup)
    .addTo(map);
}

function updateMapWithSpatialData(spatial) {
  if (!map || !spatial || !spatial.supported) return;

  const lat = spatial.query_lat;
  const lon = spatial.query_lon;

  // 1. Update Incident Marker
  updateIncidentMarker(lat, lon);

  // 2. Update Snapped Road Node Marker
  if (snappedMarker) snappedMarker.remove();
  const snapEl = document.createElement("div");
  snapEl.className = "marker-snapped";
  snapEl.innerHTML = '<div class="marker-snapped-inner"></div>';

  const snapPopup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
    <div class="map-popup-title">📍 Nearest Intersection</div>
    <div class="map-popup-stat">Intersection ID: <strong>#${spatial.snapped_node_id}</strong></div>
    <div class="map-popup-stat">Distance: <strong>${spatial.snapped_distance_m} m</strong></div>
    <div class="map-popup-stat">Threat Level: <span style="color: var(--cyan-primary)">${spatial.threat_level}</span></div>
    <div class="map-popup-stat">Risk Score: <strong>${spatial.predicted_risk}</strong></div>
  `);

  snappedMarker = new mapboxgl.Marker(snapEl)
    .setLngLat([spatial.snapped_lon, spatial.snapped_lat])
    .setPopup(snapPopup)
    .addTo(map);

  // 3. Clear and Render Top Hotspot Markers
  hotspotMarkers.forEach(m => m.remove());
  hotspotMarkers = [];

  if (spatial.top_hotspots && spatial.top_hotspots.length > 0) {
    spatial.top_hotspots.forEach(h => {
      const hEl = document.createElement("div");
      hEl.className = "marker-hotspot";
      hEl.textContent = `#${h.rank}`;

      const hPopup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
        <div class="map-popup-title">🔥 High-Risk Hotspot #${h.rank}</div>
        <div class="map-popup-stat">Intersection ID: <strong>#${h.node_id}</strong></div>
        <div class="map-popup-stat">Risk Score: <strong style="color: var(--rose-danger)">${h.risk_score}</strong></div>
        <div class="map-popup-stat">Coords: ${h.latitude}, ${h.longitude}</div>
      `);

      const marker = new mapboxgl.Marker(hEl)
        .setLngLat([h.longitude, h.latitude])
        .setPopup(hPopup)
        .addTo(map);

      hotspotMarkers.push(marker);
    });
  }

  // 4. Smooth Flight to Incident Point
  map.flyTo({
    center: [lon, lat],
    zoom: 13.8,
    pitch: 50,
    bearing: -15,
    duration: 2000
  });
}

// ---------------------------------------------------------------------------
// Setup Textarea & Shortcuts
// ---------------------------------------------------------------------------
function setupTextarea() {
  if (narrativeInput && charCount) {
    narrativeInput.addEventListener("input", () => {
      const len = narrativeInput.value.length;
      charCount.textContent = `${len} character${len === 1 ? "" : "s"}`;
    });

    narrativeInput.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        runAnalysis();
      }
    });
  }

  if (btnClearText && narrativeInput && charCount) {
    btnClearText.addEventListener("click", () => {
      narrativeInput.value = "";
      charCount.textContent = "0 characters";
      narrativeInput.focus();
    });
  }

  const btnRandom = document.getElementById("btnRandomNarrative");
  if (btnRandom) {
    btnRandom.addEventListener("click", async () => {
      btnRandom.disabled = true;
      btnRandom.textContent = "🎲 Loading...";
      try {
        const res = await fetch("/api/narrative/random");
        if (!res.ok) throw new Error("Could not fetch random narrative");
        const data = await res.json();
        narrativeInput.value = data.narrative;
        charCount.textContent = `${data.narrative.length} characters`;
        if (data.city && citySelect) citySelect.value = data.city;
        if (data.lat && inputLat) inputLat.value = data.lat;
        if (data.lon && inputLon) inputLon.value = data.lon;
        if (data.lat && data.lon && map) {
          updateIncidentMarker(data.lat, data.lon);
          map.flyTo({ center: [data.lon, data.lat], zoom: 13, pitch: 45, duration: 1200 });
        }
        showToast(`Loaded: ${data.title}`);
      } catch (err) {
        console.error(err);
        showToast("Error loading random scenario.");
      } finally {
        btnRandom.disabled = false;
        btnRandom.textContent = "🎲 Random Example";
      }
    });
  }
}

// Fetch Presets & Health
async function loadPresets() {
  try {
    const res = await fetch("/api/presets");
    if (!res.ok) return;
    PRESETS_DATA = await res.json();
    renderPresets();
  } catch (err) {
    console.warn("Could not load presets from server:", err);
  }
}

async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    if (!res.ok) return;
  } catch (err) {
    console.log("Health check note:", err);
  }
}

function renderPresets() {
  if (!presetContainer || PRESETS_DATA.length === 0) return;
  presetContainer.innerHTML = "";
  PRESETS_DATA.forEach((preset) => {
    const btn = document.createElement("button");
    btn.className = "preset-pill";
    btn.textContent = preset.title;
    btn.setAttribute("data-preset", preset.id);
    btn.addEventListener("click", () => {
      document.querySelectorAll(".preset-pill").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      applyPreset(preset.id, false);
      showToast(`Loaded template: ${preset.title}`);
    });
    presetContainer.appendChild(btn);
  });
}

function applyPreset(presetId, autoAnalyze = false) {
  const p = PRESETS_DATA.find(item => item.id === presetId);
  if (!p) return;
  if (narrativeInput) narrativeInput.value = p.narrative;
  if (charCount) charCount.textContent = `${p.narrative.length} characters`;
  if (p.city && citySelect) citySelect.value = p.city;
  if (p.lat && inputLat) inputLat.value = p.lat;
  if (p.lon && inputLon) inputLon.value = p.lon;

  // Move Mapbox incident marker to preset coords
  if (p.lat && p.lon && map) {
    updateIncidentMarker(p.lat, p.lon);
    map.flyTo({ center: [p.lon, p.lat], zoom: 13, pitch: 45, duration: 1500 });
  }

  if (autoAnalyze) {
    runAnalysis();
  }
}

// Event Listeners
function setupEventListeners() {
  if (btnAnalyze) {
    btnAnalyze.addEventListener("click", runAnalysis);
  }

  document.getElementById("btnCopyRaw")?.addEventListener("click", () => {
    const raw = document.getElementById("textOriginal")?.innerText || "";
    copyToClipboard(raw, "Original narrative copied to clipboard!");
  });

  document.getElementById("btnCopyScrubbed")?.addEventListener("click", () => {
    const scrubbed = document.getElementById("textAnonymized")?.innerText || "";
    copyToClipboard(scrubbed, "Sanitized narrative copied to clipboard!");
  });

  document.getElementById("btnCopyBrief")?.addEventListener("click", copyFullPoliceBrief);
  document.getElementById("btnPrintBrief")?.addEventListener("click", () => window.print());
}

// ---------------------------------------------------------------------------
// Run Analysis
// ---------------------------------------------------------------------------
async function runAnalysis() {
  const text = narrativeInput?.value.trim();
  if (!text) {
    showToast("Please enter an incident narrative to analyze.");
    narrativeInput?.focus();
    return;
  }

  if (btnAnalyze) {
    btnAnalyze.disabled = true;
    const btnText = btnAnalyze.querySelector(".btn-text");
    if (btnText) btnText.textContent = "Analyzing Incident...";
  }

  if (tickerStatus) {
    tickerStatus.textContent = "PROCESSING...";
    tickerStatus.style.color = "var(--amber-warning)";
  }

  const latVal = parseFloat(inputLat?.value);
  const lonVal = parseFloat(inputLon?.value);
  const payload = {
    narrative: text,
    city: citySelect?.value !== "none" ? citySelect?.value : null,
    lat: (!isNaN(latVal) && citySelect?.value !== "none") ? latVal : null,
    lon: (!isNaN(lonVal) && citySelect?.value !== "none") ? lonVal : null,
  };

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Analysis request failed");
    }

    const data = await res.json();
    CURRENT_RESULT = data;
    renderResults(data);
    showToast(`Analysis complete in ${data.meta.total_latency_ms} ms!`);
  } catch (err) {
    console.error("Error during analysis:", err);
    showToast(`Error: ${err.message}`);
    if (tickerStatus) {
      tickerStatus.textContent = "ERROR";
      tickerStatus.style.color = "var(--rose-danger)";
    }
  } finally {
    if (btnAnalyze) {
      btnAnalyze.disabled = false;
      const btnText = btnAnalyze.querySelector(".btn-text");
      if (btnText) btnText.textContent = "Analyze Incident";
    }
  }
}

// ---------------------------------------------------------------------------
// Render Results Across All Tabs
// ---------------------------------------------------------------------------
function renderResults(data) {
  if (tickerStatus) {
    tickerStatus.textContent = "COMPLETE";
    tickerStatus.style.color = "var(--emerald-success)";
  }
  if (tickerLatency) {
    tickerLatency.textContent = `${data.meta.total_latency_ms} ms`;
  }

  renderMOMatrix(data.modus_operandi, data.forensic_intelligence);
  renderAccuracyVerification(data.math_proof);
  renderTacticalChecklist(data.forensic_intelligence.tactical_checklist);
  renderSpatialRisk(data.spatial_risk);
  renderReasoningEngine(data.forensic_intelligence, data.modus_operandi);
  renderPrivacyAudit(data.privacy);

  const contentArea = document.querySelector(".tab-content-area");
  if (contentArea) {
    contentArea.classList.remove("pulse-update");
    void contentArea.offsetWidth;
    contentArea.classList.add("pulse-update");
  }
}

// ---------------------------------------------------------------------------
// Tab 2: Render Accuracy & Verification
// ---------------------------------------------------------------------------
function renderAccuracyVerification(mathProof) {
  const container = document.getElementById("mathProofContainer");
  if (!container) return;

  if (!mathProof || Object.keys(mathProof).length === 0) {
    container.innerHTML = `<p class="empty-state-text">No accuracy verification data available.</p>`;
    return;
  }

  container.innerHTML = "";

  for (const [headKey, proof] of Object.entries(mathProof)) {
    const card = document.createElement("div");
    card.className = "math-head-card";

    let verdictClass = "verdict-emerald";
    if (proof.verdict_color === "cyan") verdictClass = "verdict-cyan";
    if (proof.verdict_color === "amber") verdictClass = "verdict-amber";

    let triggersHtml = "";
    if (proof.detected_triggers && proof.detected_triggers.length > 0) {
      const tags = proof.detected_triggers.map(t => 
        `<span class="trigger-tag">🎯 Trigger Evidence: "${t.matched_words.join(", ")}" &rarr; ${formatLabel(t.matched_class)}</span>`
      ).join(" ");
      triggersHtml = `<div class="mhc-triggers-row">${tags}</div>`;
    } else {
      triggersHtml = `<div class="mhc-triggers-row"><span class="mhc-meta-item" style="font-size:0.75rem; font-style:italic">Identified via latent contextual narrative features.</span></div>`;
    }

    let rowsHtml = "";
    let sumExp = proof.exp_sum || 0;
    let sumProb = 0;
    let sumEntropy = proof.shannon_entropy_bits || 0;

    (proof.classes_calculation_table || []).forEach((row, idx) => {
      const isDominant = idx === 0;
      sumProb += row.probability_pct;
      rowsHtml += `
        <tr class="${isDominant ? "dominant-row" : ""}">
          <td><strong>${formatLabel(row.class_name)}</strong></td>
          <td><code>${row.raw_logit_zk.toFixed(3)}</code></td>
          <td><code>${row.exp_zk.toFixed(4)}</code></td>
          <td><strong>${row.probability_pct.toFixed(2)}%</strong></td>
          <td><code>${row.entropy_term_bits.toFixed(4)} bits</code></td>
        </tr>
      `;
    });

    const calcTableHtml = `
      <div class="table-responsive" style="margin-top:8px">
        <table class="calc-table">
          <thead>
            <tr>
              <th>Class Label (k)</th>
              <th>Raw Logit (z<sub>k</sub>)</th>
              <th>Exp (e<sup>z<sub>k</sub> - z<sub>max</sub></sup>)</th>
              <th>Softmax Likelihood P(y=k)</th>
              <th>Entropy Term -P log<sub>2</sub>(P)</th>
            </tr>
          </thead>
          <tbody>
            ${rowsHtml}
            <tr style="border-top:1px solid var(--border-subtle); font-weight:700; color:var(--text-primary); background:rgba(255,255,255,0.02)">
              <td><strong>TOTAL / NORMALIZED SUM</strong></td>
              <td><code>--</code></td>
              <td><code>&sum; = ${sumExp.toFixed(4)}</code></td>
              <td><code>${sumProb.toFixed(1)}%</code></td>
              <td><code>H(P) = ${sumEntropy.toFixed(3)} bits</code></td>
            </tr>
          </tbody>
        </table>
      </div>
    `;

    card.innerHTML = `
      <div class="mhc-header">
        <h4 class="mhc-title">${proof.head_title}</h4>
        <div style="display:flex; gap:10px; align-items:center;">
          <span class="mhc-verdict-badge ${verdictClass}">${proof.reliability_verdict}</span>
          <span class="mhc-meta-item" style="font-size:0.75rem; color:var(--cyan-primary)">Benchmark: <strong>${proof.historical_accuracy_pct}% Accuracy</strong></span>
        </div>
      </div>

      <div class="mhc-meta-bar">
        <span class="mhc-meta-item">Top Prediction: <strong>${formatLabel(proof.dominant_class)} (${proof.dominant_probability.toFixed(1)}%)</strong></span>
        <span class="mhc-meta-item">Runner-Up: <strong>${formatLabel(proof.runner_up_class)} (${proof.runner_up_probability.toFixed(1)}%)</strong></span>
        <span class="mhc-meta-item">Separation Margin: <strong style="color:var(--cyan-primary)">+${proof.top2_margin_pct.toFixed(1)}%</strong></span>
        <span class="mhc-meta-item">Model Accuracy: <strong style="color:var(--emerald-success)">${proof.historical_accuracy_pct}%</strong></span>
      </div>

      ${triggersHtml}

      <div style="font-size:0.78rem; color:var(--text-secondary); line-height:1.5; background:#eff6ff; padding:10px 14px; border-radius:6px; border-left:3px solid var(--cyan-primary)">
        <strong>Accuracy &amp; Reliability Assessment:</strong> ${proof.verdict_explanation}
      </div>

      ${calcTableHtml}
    `;

    container.appendChild(card);
  }
}


// ---------------------------------------------------------------------------
// Tab 1: Render M.O. Classification
// ---------------------------------------------------------------------------
function renderMOMatrix(mo, fi) {
  renderHeadCard(
    "cardWeapon", "valWeapon", "badgeWeapon", "distWeapon",
    mo.top_possibilities.weapon_classification,
    mo.prob_distributions.weapon_classification
  );

  renderHeadCard(
    "cardEntry", "valEntry", "badgeEntry", "distEntry",
    mo.top_possibilities.point_of_entry,
    mo.prob_distributions.point_of_entry
  );

  renderHeadCard(
    "cardTarget", "valTarget", "badgeTarget", "distTarget",
    mo.top_possibilities.target_profile,
    mo.prob_distributions.target_profile
  );

  renderHeadCard(
    "cardSuspect", "valSuspect", "badgeSuspect", "distSuspect",
    mo.top_possibilities.suspect_count_estimate,
    mo.prob_distributions.suspect_count_estimate
  );

  // Populate Key Findings Summary Banner
  const topW = mo.top_possibilities.weapon_classification[0];
  const topE = mo.top_possibilities.point_of_entry[0];
  const topT = mo.top_possibilities.target_profile[0];
  const topS = mo.top_possibilities.suspect_count_estimate[0];

  const sumWeapon = document.getElementById("summaryWeapon");
  if (sumWeapon) sumWeapon.textContent = `${formatLabel(topW[0])} (${(topW[1] * 100).toFixed(0)}%)`;

  const sumEntry = document.getElementById("summaryEntry");
  if (sumEntry) sumEntry.textContent = `${formatLabel(topE[0])} (${(topE[1] * 100).toFixed(0)}%)`;

  const sumTarget = document.getElementById("summaryTarget");
  if (sumTarget) sumTarget.textContent = `${formatLabel(topT[0])} (${(topT[1] * 100).toFixed(0)}%)`;

  const sumSuspect = document.getElementById("summarySuspect");
  if (sumSuspect) sumSuspect.textContent = `${formatLabel(topS[0])} (${(topS[1] * 100).toFixed(0)}%)`;

  const sumHypo = document.getElementById("summaryHypothesis");
  if (sumHypo && fi && fi.scenarios && fi.scenarios.length > 0) {
    sumHypo.textContent = fi.scenarios[0].description || fi.scenarios[0].patrol_directive;
  }
}

function renderHeadCard(cardId, valId, badgeId, distId, topList, fullDist) {
  const top = topList[0];
  const topClass = top[0];
  const topProb = (top[1] * 100).toFixed(1);

  const valEl = document.getElementById(valId);
  if (valEl) valEl.textContent = formatLabel(topClass);

  const badgeEl = document.getElementById(badgeId);
  if (badgeEl) badgeEl.textContent = `${topProb}% CONFIDENCE`;

  const distContainer = document.getElementById(distId);
  if (!distContainer) return;
  distContainer.innerHTML = "";

  fullDist.forEach(([clsName, prob], idx) => {
    const pct = (prob * 100).toFixed(1);
    const isDominant = idx === 0;

    const row = document.createElement("div");
    row.className = "prob-row";
    row.innerHTML = `
      <div class="prob-meta">
        <span class="prob-class-name ${isDominant ? "dominant" : ""}">${formatLabel(clsName)}</span>
        <span class="prob-pct ${isDominant ? "dominant" : ""}">${pct}%</span>
      </div>
      <div class="prob-track">
        <div class="prob-fill ${isDominant ? "" : "alt"}" style="width: ${Math.max(prob * 100, 2)}%"></div>
      </div>
    `;
    distContainer.appendChild(row);
  });
}

function formatLabel(str) {
  if (!str) return "";
  return str.replace(/_/g, " ").toUpperCase();
}

// ---------------------------------------------------------------------------
// Tab 2: Render Tactical Action Plan
// ---------------------------------------------------------------------------
function renderTacticalChecklist(checklist) {
  const container = document.getElementById("checklistItems");
  if (!container) return;
  container.innerHTML = "";

  if (!checklist || checklist.length === 0) {
    container.innerHTML = `<p class="empty-state-text">No checklist items generated.</p>`;
    return;
  }

  checklist.forEach((itemText, idx) => {
    const item = document.createElement("div");
    item.className = "checklist-item";
    item.innerHTML = `
      <input type="checkbox" id="chk_${idx}" class="checklist-checkbox">
      <label for="chk_${idx}" class="checklist-text">${itemText}</label>
    `;
    container.appendChild(item);
  });
}

// ---------------------------------------------------------------------------
// Tab 3: Render Incident Map & Hotspots
// ---------------------------------------------------------------------------
function renderSpatialRisk(spatial) {
  const spCityEl = document.getElementById("spCity");
  const spNodeEl = document.getElementById("spNode");
  const spDistEl = document.getElementById("spDistance");
  const spThreatEl = document.getElementById("spThreatLevel");
  const tbody = document.getElementById("hotspotsTableBody");

  if (!spatial || !spatial.supported) {
    if (spatial && spatial.error_type === "GEOGRAPHIC_OUT_OF_BOUNDS") {
      if (spCityEl) spCityEl.textContent = `${spatial.city.toUpperCase()} (OUT OF BOUNDS)`;
      if (spNodeEl) spNodeEl.textContent = `Offset: ${spatial.distance_km} km`;
      if (spDistEl) spDistEl.textContent = `${spatial.distance_km} km`;
      if (spThreatEl) {
        spThreatEl.textContent = "OUT OF BOUNDS";
        spThreatEl.className = "sp-val val-red";
      }
      if (tbody) {
        tbody.innerHTML = `
          <tr><td colspan="6" class="empty-state-text" style="color: #f87171 !important; text-align: left; padding: 1.5rem;">
            ⚠️ <strong>Geographic Alert:</strong> ${spatial.message}<br><br>
            🧭 <em>Directive:</em> ${spatial.resolution_directive}
          </td></tr>
        `;
      }
      return;
    }
    if (spCityEl) spCityEl.textContent = spatial?.city ? spatial.city.toUpperCase() : "Optional / Disabled";
    if (spNodeEl) spNodeEl.textContent = "--";
    if (spDistEl) spDistEl.textContent = "--";
    if (spThreatEl) spThreatEl.textContent = "N/A";
    if (tbody) {
      tbody.innerHTML = `
        <tr><td colspan="6" class="empty-state-text">Select Chicago or San Francisco in Location Settings to enable crime hotspots radar.</td></tr>
      `;
    }
    return;
  }

  const cityName = spatial.city === "chicago" ? "Chicago, IL" : (spatial.city === "sf" ? "San Francisco, CA" : spatial.city.toUpperCase());
  if (spCityEl) spCityEl.textContent = cityName;
  if (spNodeEl) spNodeEl.textContent = `Intersection #${spatial.snapped_node_id}`;
  if (spDistEl) spDistEl.textContent = `${spatial.snapped_distance_m} m`;
  if (spThreatEl) {
    spThreatEl.textContent = spatial.threat_level;
    spThreatEl.className = `sp-val val-${spatial.badge_color || "cyan"}`;
  }

  // Update Mapbox Markers and Camera
  updateMapWithSpatialData(spatial);

  // Hotspots Table
  if (tbody) {
    tbody.innerHTML = "";
    (spatial.top_hotspots || []).forEach(h => {
      const tr = document.createElement("tr");
      tr.style.cursor = "pointer";
      tr.title = "Click to fly to this hotspot on map";
      tr.addEventListener("click", () => {
        if (map) {
          map.flyTo({ center: [h.longitude, h.latitude], zoom: 15.5, pitch: 55, duration: 1800 });
          showToast(`Viewing Hotspot #${h.rank} (#${h.node_id})`);
        }
      });

      tr.innerHTML = `
        <td style="font-weight: 700; color: var(--rose-danger)">#${h.rank}</td>
        <td>#${h.node_id}</td>
        <td>${h.latitude}</td>
        <td>${h.longitude}</td>
        <td style="font-weight: 700; color: #ffffff">${h.risk_score}</td>
        <td>
          <div style="background: rgba(255,255,255,0.05); height: 5px; border-radius: 3px; width: 80px; overflow: hidden">
            <div style="height: 100%; width: ${Math.min((h.risk_score / 6.5) * 100, 100)}%; background: var(--rose-danger)"></div>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }
}

// ---------------------------------------------------------------------------
// Tab 4: Render Forensic Leads & Scenarios
// ---------------------------------------------------------------------------
function renderReasoningEngine(fi, mo) {
  const emContainer = document.getElementById("entropyMetersContainer");
  if (emContainer) {
    emContainer.innerHTML = "";
    const entropies = mo.entropy_scores || {};
    let maxEntropy = 0;

    for (const [head, score] of Object.entries(entropies)) {
      if (score > maxEntropy) maxEntropy = score;
      const isCertain = score < 0.35;
      const isModerate = score >= 0.35 && score <= 0.85;

      let ratingText = isCertain ? "HIGH CERTAINTY" : (isModerate ? "MODERATE SPREAD" : "AMBIGUITY FLAGGED");
      let ratingColor = isCertain ? "var(--emerald-success)" : (isModerate ? "var(--cyan-primary)" : "var(--amber-warning)");
      const certaintyPct = Math.max(10, Math.min(100, Math.round((1 - Math.min(score, 1.5) / 1.5) * 100)));

      const box = document.createElement("div");
      box.className = "entropy-meter-box";
      box.innerHTML = `
        <span class="em-title">${formatLabel(head)}</span>
        <div class="em-score-row">
          <span class="em-val">${certaintyPct}% <span style="font-size: 0.7rem; color: var(--text-muted)">Certainty</span></span>
          <span class="em-label" style="color: ${ratingColor}">${ratingText}</span>
        </div>
        <div class="em-track">
          <div class="em-fill" style="width: ${certaintyPct}%; background: ${ratingColor}"></div>
        </div>
      `;
      emContainer.appendChild(box);
    }

    const overallBadge = document.getElementById("overallCertaintyBadge");
    if (overallBadge) {
      if (maxEntropy < 0.5) {
        overallBadge.textContent = "HIGH CERTAINTY PROFILE";
        overallBadge.style.color = "#15803d";
        overallBadge.style.borderColor = "#bbf7d0";
        overallBadge.style.background = "#f0fdf4";
      } else if (maxEntropy < 1.0) {
        overallBadge.textContent = "MODERATE CONFIDENCE";
        overallBadge.style.color = "var(--cyan-primary)";
        overallBadge.style.borderColor = "#bfdbfe";
        overallBadge.style.background = "#eff6ff";
      } else {
        overallBadge.textContent = "AMBIGUOUS / MULTI-HYPOTHESIS";
        overallBadge.style.color = "var(--amber-warning)";
        overallBadge.style.borderColor = "#fde68a";
        overallBadge.style.background = "#fffbeb";
      }
    }
  }

  const scContainer = document.getElementById("scenariosContainer");
  if (scContainer) {
    scContainer.innerHTML = "";
    (fi.scenarios || []).forEach((sc, idx) => {
      const isPrimary = idx === 0;
      const card = document.createElement("div");
      card.className = `scenario-card ${isPrimary ? "primary" : ""}`;
      card.innerHTML = `
        <div class="scenario-card-header">
          <span class="scenario-rank-badge">HYPOTHESIS #${sc.rank}</span>
          <span class="scenario-conf">${sc.confidence_composite || (sc.threat_level ? `THREAT: ${sc.threat_level}` : "")}</span>
        </div>
        <h4 class="scenario-title">${sc.title}</h4>
        <p class="scenario-desc">${sc.description || sc.patrol_directive}</p>
        <div class="scenario-meta-tags">
          ${sc.weapon ? `<span class="sc-tag">⚔️ ${formatLabel(sc.weapon)}</span>` : ""}
          ${sc.entry ? `<span class="sc-tag">🚪 ${formatLabel(sc.entry)}</span>` : ""}
          ${sc.target ? `<span class="sc-tag">🏢 ${formatLabel(sc.target)}</span>` : ""}
          ${sc.suspects ? `<span class="sc-tag">👥 ${formatLabel(sc.suspects)}</span>` : ""}
        </div>
      `;
      scContainer.appendChild(card);
    });
  }
}

// ---------------------------------------------------------------------------
// Tab 5: Render Privacy & Redaction
// ---------------------------------------------------------------------------
function renderPrivacyAudit(privacy) {
  const statRedact = document.getElementById("statRedactions");
  if (statRedact) statRedact.textContent = privacy.redactions_count;

  const entityCount = Object.keys(privacy.entity_map || {}).length;
  const statEnt = document.getElementById("statEntities");
  if (statEnt) statEnt.textContent = entityCount;

  const redBadge = document.getElementById("redactionBadge");
  if (redBadge) redBadge.textContent = `${privacy.redactions_count} Redactions`;

  const origEl = document.getElementById("textOriginal");
  if (origEl) origEl.textContent = privacy.original_narrative;

  const anonEl = document.getElementById("textAnonymized");
  if (anonEl) {
    let scrubbedHtml = escapeHtml(privacy.anonymized_narrative || "");
    for (const [token, etype] of Object.entries(privacy.entity_map || {})) {
      const regex = new RegExp(`\\b${token}\\b`, "g");
      scrubbedHtml = scrubbedHtml.replace(
        regex,
        `<span class="entity-token" title="Entity Type: ${etype}">${token}</span>`
      );
    }
    anonEl.innerHTML = scrubbedHtml;
  }

  const chipsContainer = document.getElementById("entityChips");
  if (chipsContainer) {
    chipsContainer.innerHTML = "";
    if (entityCount === 0) {
      chipsContainer.innerHTML = `<span class="empty-state-text">No sensitive personal identifiers detected in this narrative.</span>`;
    } else {
      for (const [token, etype] of Object.entries(privacy.entity_map || {})) {
        const chip = document.createElement("div");
        chip.className = "entity-chip";
        chip.innerHTML = `
          <span class="entity-chip-name">${token}</span>
          <span class="entity-chip-arrow">&rarr;</span>
          <span class="entity-chip-type">${etype}</span>
        `;
        chipsContainer.appendChild(chip);
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Utility Functions
// ---------------------------------------------------------------------------
function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function showToast(msg) {
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3200);
}

function copyToClipboard(text, successMsg) {
  navigator.clipboard.writeText(text).then(() => {
    showToast(successMsg);
  }).catch(() => {
    showToast("Clipboard access denied.");
  });
}

function copyFullPoliceBrief() {
  if (!CURRENT_RESULT) {
    showToast("Please run analysis first.");
    return;
  }

  const mo = CURRENT_RESULT.modus_operandi.top_possibilities;
  const w = mo.weapon_classification[0];
  const e = mo.point_of_entry[0];
  const t = mo.target_profile[0];
  const s = mo.suspect_count_estimate[0];

  const brief = `
================================================================================
POLICE DISPATCH & FORENSIC INTELLIGENCE BRIEF
PROJECT D.H.A.R.M.A. // CRIME ANALYTICS
================================================================================
TIMESTAMP: ${new Date().toISOString()}
EXECUTION TIME: ${CURRENT_RESULT.meta.total_latency_ms} ms (Local Secure Mode)

1. MODUS OPERANDI CLASSIFICATION:
- Weapon Profile:   ${formatLabel(w[0])} (${(w[1]*100).toFixed(1)}% Confidence)
- Point of Entry:   ${formatLabel(e[0])} (${(e[1]*100).toFixed(1)}% Confidence)
- Target Profile:   ${formatLabel(t[0])} (${(t[1]*100).toFixed(1)}% Confidence)
- Suspect Estimate: ${formatLabel(s[0])} (${(s[1]*100).toFixed(1)}% Confidence)

2. PRIMARY INVESTIGATIVE HYPOTHESIS:
${CURRENT_RESULT.forensic_intelligence.scenarios[0].description}

3. TACTICAL ACTION CHECKLIST:
${CURRENT_RESULT.forensic_intelligence.tactical_checklist.map((c, i) => `[ ] ${i+1}. ${c}`).join("\n")}

4. SANITIZED INCIDENT TEXT:
${CURRENT_RESULT.privacy.anonymized_narrative}
================================================================================
`.trim();

  copyToClipboard(brief, "Police Dispatch Brief copied to clipboard!");
}
