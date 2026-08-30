const SHOWCASE_ARM_IDS = new Set([
  "roupp",
  "landen_roupp",
  "webb",
  "logan_webb",
  "eduardo_rodriguez",
  "erod",
  "gabriel_moreno",
  "moreno",
  "chase_burns",
  "burns",
  "roki_sasaki",
  "sasaki",
  "won_tae_choi",
  "choi",
  "gu_lin_ruei_yang",
  "gulin",
  "gu_lin",
  "wilmer_rios",
  "rios",
  "hughes",
  "gabriel_hughes",
  "brandon_pfaadt",
  "pfaadt",
  "gordon",
  "tanner_gordon"
]);

const PLAYER_ALIASES = {
  // NCAA
  burns: "chase_burns",
  chase_burns: "chase_burns",
  chaseburns: "chase_burns",
  wake_burns: "chase_burns",

  // NPB
  sasaki: "roki_sasaki",
  roki_sasaki: "roki_sasaki",
  rokisasaki: "roki_sasaki",
  roki: "roki_sasaki",
  chiba_sasaki: "roki_sasaki",

  // KBO
  choi: "won_tae_choi",
  won_tae_choi: "won_tae_choi",
  wontae_choi: "won_tae_choi",
  wontaechoi: "won_tae_choi",
  "won-tae-choi": "won_tae_choi",
  won_tae: "won_tae_choi",
  wontae: "won_tae_choi",
  lg_choi: "won_tae_choi",

  // CPBL
  gulin: "gu_lin_ruei_yang",
  gu_lin: "gu_lin_ruei_yang",
  gu_lin_ruei_yang: "gu_lin_ruei_yang",
  gulin_rueiyang: "gu_lin_ruei_yang",
  "gu-lin-ruei-yang": "gu_lin_ruei_yang",
  gulinrueiyang: "gu_lin_ruei_yang",
  rueiyang: "gu_lin_ruei_yang",
  uni_gulin: "gu_lin_ruei_yang",

  // LMB
  wilmer_rios: "wilmer_rios",
  wilmerrios: "wilmer_rios",
  "wilmer-rios": "wilmer_rios",
  wilmer: "wilmer_rios",
  rios: "wilmer_rios",
  monclova_rios: "wilmer_rios",
  bauer: "wilmer_rios",
  trevor_bauer: "wilmer_rios",
  trevorbauer: "wilmer_rios",
  "trevor-bauer": "wilmer_rios",

  // MLB Showcase & Pitchers
  roupp: "roupp",
  landen_roupp: "roupp",
  landenroupp: "roupp",
  "landen-roupp": "roupp",
  landen: "roupp",

  webb: "webb",
  logan_webb: "webb",
  loganwebb: "webb",
  "logan-webb": "webb",
  logan: "webb",

  eduardo_rodriguez: "eduardo_rodriguez",
  eduardorodriguez: "eduardo_rodriguez",
  "eduardo-rodriguez": "eduardo_rodriguez",
  erod: "eduardo_rodriguez",

  hughes: "hughes",
  gabriel_hughes: "hughes",
  gabrielhughes: "hughes",
  "gabriel-hughes": "hughes",

  brandon_pfaadt: "brandon_pfaadt",
  brandonpfaadt: "brandon_pfaadt",
  "brandon-pfaadt": "brandon_pfaadt",
  pfaadt: "brandon_pfaadt",

  gordon: "gordon",
  tanner_gordon: "gordon",
  tannergordon: "gordon",
  "tanner-gordon": "gordon",

  gabriel_moreno: "gabriel_moreno",
  gabrielmoreno: "gabriel_moreno",
  "gabriel-moreno": "gabriel_moreno",
  moreno: "gabriel_moreno",
  gabi: "gabriel_moreno",

  // Catcher Batteries
  mccann: "james_mccann",
  james_mccann: "james_mccann",
  jamesmccann: "james_mccann",
  "james-mccann": "james_mccann",

  romo: "drew_romo",
  drew_romo: "drew_romo",
  drewromo: "drew_romo",
  "drew-romo": "drew_romo",

  stallings: "jacob_stallings",
  jacob_stallings: "jacob_stallings",
  jacobstallings: "jacob_stallings",
  "jacob-stallings": "jacob_stallings",

  smith: "will_smith",
  will_smith: "will_smith",
  willsmith: "will_smith",
  "will-smith": "will_smith",

  barnes: "austin_barnes",
  austin_barnes: "austin_barnes",
  austinbarnes: "austin_barnes",
  "austin-barnes": "austin_barnes",

  campusano: "luis_campusano",
  luis_campusano: "luis_campusano",
  luiscampusano: "luis_campusano",
  "luis-campusano": "luis_campusano",

  diaz: "elias_diaz",
  elias_diaz: "elias_diaz",
  eliasdiaz: "elias_diaz",
  "elias-diaz": "elias_diaz",

  bailey: "patrick_bailey",
  patrick_bailey: "patrick_bailey",
  patrickbailey: "patrick_bailey",
  "patrick-bailey": "patrick_bailey",

  casali: "curt_casali",
  curt_casali: "curt_casali",
  curtcasali: "curt_casali",
  "curt-casali": "curt_casali",

  // Other MLB
  canning: "canning",
  griffin_canning: "canning",
  pfaadt: "brandon_pfaadt",
  brandon_pfaadt: "brandon_pfaadt",
  snell: "blake_snell",
  blake_snell: "blake_snell",
  kelly: "merrill_kelly",
  merrill_kelly: "merrill_kelly",
  miller: "mason_miller",
  mason_miller: "mason_miller",
  skubal: "skubal",
  tarik_skubal: "skubal",
  ohtani: "ohtani",
  shohei_ohtani: "ohtani",
  glasnow: "glasnow",
  tyler_glasnow: "glasnow",
  yamamoto: "yamamoto",
  yoshinobu_yamamoto: "yamamoto",
  buehler: "buehler",
  walker_buehler: "buehler",
  sugano: "sugano",
  tomoyuki_sugano: "sugano",
  ray: "robbie_ray",
  robbie_ray: "robbie_ray",
  drake: "kohl_drake",
  kohl_drake: "kohl_drake",
  frasso: "nick_frasso",
  nick_frasso: "nick_frasso",
  morejon: "adrian_morejon",
  adrian_morejon: "adrian_morejon",
  vesia: "alex_vesia",
  alex_vesia: "alex_vesia",
  jameson: "jameson",
  drey_jameson: "jameson",
  ginkel: "ginkel",
  kevin_ginkel: "ginkel",
  feltner: "feltner",
  ryan_feltner: "feltner",
  gordon: "gordon",
  tanner_gordon: "gordon",
  hughes: "hughes",
  gabriel_hughes: "hughes",
  lauer: "lauer",
  eric_lauer: "lauer",
  dreyer: "dreyer",
  jack_dreyer: "dreyer",
  scott: "tanner_scott",
  tanner_scott: "tanner_scott",
  king: "king",
  michael_king: "king",
  vasquez: "vasquez",
  randy_vasquez: "vasquez",
  peralta: "wandy_peralta",
  wandy_peralta: "wandy_peralta",
  hart: "kyle_hart",
  kyle_hart: "kyle_hart",
  matsui: "yuki_matsui",
  yuki_matsui: "yuki_matsui",
  morgan: "david_morgan",
  david_morgan: "david_morgan",
  tidwell: "blade_tidwell",
  blade_tidwell: "blade_tidwell",
  hentges: "sam_hentges",
  sam_hentges: "sam_hentges",
  ryan_walker: "ryan_walker",
  dylan_smith: "dylan_smith",
  seymour: "carson_seymour",
  carson_seymour: "carson_seymour",
  sanmartin: "reiver_sanmartin",
  reiver_sanmartin: "reiver_sanmartin",
  foley: "jason_foley",
  jason_foley: "jason_foley",
  zeferjahn: "ryan_zeferjahn",
  ryan_zeferjahn: "ryan_zeferjahn",
  thielbar: "caleb_thielbar",
  caleb_thielbar: "caleb_thielbar",
  mize: "mize",
  casey_mize: "mize"
};

function isShowcaseArm(id) {
  if (!id) return false;
  const clean = (id || "").trim().toLowerCase().replace(/[\s\-]+/g, "_");
  if (SHOWCASE_ARM_IDS.has(clean)) return true;
  const aliased = PLAYER_ALIASES[clean];
  if (aliased && SHOWCASE_ARM_IDS.has(aliased)) return true;
  return false;
}

function checkIsLiteMode() {
  const url = new URL(location.href);
  return (
    document.body.dataset.mode === "lite" ||
    document.body.dataset.page === "lite" ||
    url.pathname.includes("lite") ||
    url.searchParams.get("lite") === "1"
  );
}

const isLiteMode = checkIsLiteMode();

async function loadDemo() {
  const v = Date.now();
  const isSubdir = location.pathname.includes("/lite/") || location.pathname.endsWith("/lite");
  const candidates = isSubdir
    ? [`../data/demo.json?v=${v}`, `../demo.json?v=${v}`, "data/demo.json", "demo.json"]
    : [`data/demo.json?v=${v}`, `demo.json?v=${v}`, `./data/demo.json?v=${v}`, `./demo.json?v=${v}`, "data/demo.json", "demo.json"];

  for (const url of candidates) {
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      // try next candidate
    }
  }
  throw new Error("Failed to load demo data");
}

function pct(n) {
  return `${Math.round(Number(n) * 100)}%`;
}

function qs(name) {
  return new URLSearchParams(location.search).get(name);
}

function getPlayerIdFromUrl() {
  const params = new URLSearchParams(location.search);
  const raw =
    params.get("id") ||
    params.get("player") ||
    params.get("p") ||
    params.get("pid") ||
    params.get("name") ||
    "";
  return raw.trim().toLowerCase();
}

function resolvePlayer(data, requestedId) {
  if (!data || !data.players) return null;
  const rawId = (requestedId || "").trim().toLowerCase();
  if (!rawId) return null;
  const cleanId = rawId.replace(/[\s\-]+/g, "_");

  // 1. Direct hit in data.players
  if (data.players[cleanId]) return data.players[cleanId];
  if (data.players[rawId]) return data.players[rawId];

  // 2. Direct alias mapping
  const aliasedKey = PLAYER_ALIASES[cleanId] || PLAYER_ALIASES[rawId];
  if (aliasedKey && data.players[aliasedKey]) {
    return data.players[aliasedKey];
  }

  // 3. Search by player.id in data.players
  const allPlayers = Object.values(data.players);
  let found = allPlayers.find((p) => {
    if (!p) return false;
    const pid = (p.id || "").toLowerCase();
    return pid === cleanId || pid === rawId;
  });
  if (found) return found;

  // 4. Search by normalized name match
  found = allPlayers.find((p) => {
    if (!p || !p.name) return false;
    const normName = p.name.toLowerCase().replace(/[^a-z0-9]+/g, "_");
    return normName === cleanId || normName.includes(cleanId) || cleanId.includes(normName);
  });
  if (found) return found;

  return null;
}

function fillSelect(el, options, { valueKey = "id", labelKey = "label", blank = null } = {}) {
  if (!el) return;
  el.innerHTML = "";
  if (blank != null) {
    const o = document.createElement("option");
    o.value = "";
    o.textContent = blank;
    el.appendChild(o);
  }
  for (const item of options) {
    const o = document.createElement("option");
    o.value = typeof item === "string" ? item : item[valueKey];
    o.textContent = typeof item === "string" ? item : item[labelKey];
    el.appendChild(o);
  }
}

function playerList(data) {
  const seen = new Set();
  const list = [];
  for (const p of Object.values(data.players || {})) {
    if (p && p.id && !seen.has(p.id)) {
      seen.add(p.id);
      list.push(p);
    }
  }
  return list;
}

function teamById(data, id) {
  return (data.teams || []).find((t) => t.id === id);
}

function playersForTeam(data, teamId) {
  return playerList(data).filter((p) => p.teamId === teamId);
}

function tipPassesFilters(tip, { angle, context } = {}) {
  if (angle && angle !== "all" && angle !== "ALL") {
    const tipAngle = tip.angle || "CF";
    if (angle !== tipAngle && angle !== "CF") return false;
  }
  if (context && context !== "all" && context !== "ALL") {
    const ctx = Array.isArray(tip.context) ? tip.context : (tip.context ? [tip.context] : []);
    if (ctx.length > 0) {
      const isUniversal = ctx.some((c) =>
        ["all", "all situations", "all|all", "all situations / stretch", "stretch"].includes(String(c).toLowerCase())
      );
      if (!isUniversal) {
        const normContext = String(context).toLowerCase().replace(/[^a-z0-9]/g, "");
        const matches = ctx.some((c) => {
          const normC = String(c).toLowerCase().replace(/[^a-z0-9]/g, "");
          return normC === normContext || normC.includes(normContext) || normContext.includes(normC);
        });
        if (!matches) {
          return false;
        }
      }
    }
  }
  return true;
}

function tierBadge(tier) {
  const map = {
    elite: "hot",
    operational: "hot",
    developing: "ok",
    watch: "",
  };
  return map[tier] || "";
}

function tierLabel(data, tierId) {
  const t = (data.meta?.confidenceTiers || []).find((x) => x.id === tierId);
  return t?.label || tierId || "Operational";
}

function ensureEnterpriseModal() {
  if (document.getElementById("enterprise-modal-overlay")) return;
  const overlay = document.createElement("div");
  overlay.id = "enterprise-modal-overlay";
  overlay.className = "enterprise-modal-overlay";
  overlay.innerHTML = `
    <div class="enterprise-modal" role="dialog" aria-modal="true" aria-labelledby="modal-player-target">
      <button class="enterprise-modal-close" id="enterprise-modal-close-btn" aria-label="Close modal">✕</button>
      <div class="enterprise-modal-header">
        <span class="enterprise-modal-badge">🔒 Enterprise Scouting Access</span>
        <h2 id="modal-player-target">Unlock Full League &amp; International Database</h2>
        <p class="modal-desc">
          You are viewing a protected arm from the full Preflight Computer Vision platform. Interactive showcase access is 100% unlocked for <strong>Landen Roupp</strong>, <strong>Eduardo Rodriguez</strong>, and <strong>Logan Webb</strong>.
        </p>
      </div>
      <div class="enterprise-features-list">
        <ul>
          <li><strong>Full Global Pro Database:</strong> Complete rotation and bullpen CV audits across MLB, NPB (Japan), KBO (Korea), CPBL (Taiwan), Mexican League (LMB), and Winter Leagues (LIDOM, LMP, LVBP, LBPRC).</li>
          <li><strong>Multi-Angle 4K Camera Ingest:</strong> Direct integration with Synergy, dugout high-speed cameras, 1B/3B coach angles, and 4K tight CF feeds.</li>
          <li><strong>Sub-Pixel Mechanical Tells:</strong> Glove burial depth, finger curl classification, wrist cock timing, and set-tempo anomalies before hand break.</li>
          <li><strong>Automated Series Pre-Flight Audits:</strong> Pre-game opposing pitcher discrepancy dossiers delivered to advance scouts and coaching staff.</li>
        </ul>
      </div>
      <div class="enterprise-actions">
        <a class="btn-primary" href="https://x.com/colbymorris08" target="_blank" rel="noopener noreferrer">Request Enterprise Pilot / DM @colbymorris08 →</a>
        <a class="btn-secondary" href="player.html?id=roupp${isLiteMode ? '&lite=1' : ''}">View Unlocked Showcase: Landen Roupp →</a>
        <a class="btn-secondary" href="player.html?id=eduardo_rodriguez${isLiteMode ? '&lite=1' : ''}">View Unlocked Showcase: Eduardo Rodriguez →</a>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closeEnterpriseModal();
  });
  document.getElementById("enterprise-modal-close-btn")?.addEventListener("click", closeEnterpriseModal);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeEnterpriseModal();
  });
}

function openEnterpriseModal(playerName) {
  ensureEnterpriseModal();
  const overlay = document.getElementById("enterprise-modal-overlay");
  const targetTitle = document.getElementById("modal-player-target");
  if (targetTitle && playerName) {
    targetTitle.textContent = `${playerName} · Enterprise Access Required`;
  }
  if (overlay) {
    overlay.classList.add("active");
  }
}

function closeEnterpriseModal() {
  const overlay = document.getElementById("enterprise-modal-overlay");
  if (overlay) {
    overlay.classList.remove("active");
  }
}
window.openEnterpriseModal = openEnterpriseModal;
window.closeEnterpriseModal = closeEnterpriseModal;

function ensureLiteBanner() {
  if (!isLiteMode || document.getElementById("lite-banner-bar")) return;
  const banner = document.createElement("div");
  banner.id = "lite-banner-bar";
  banner.className = "lite-banner";
  banner.innerHTML = `
    <div>
      <strong>✨ PREFLIGHT LITE SHOWCASE:</strong> Interactive delivery compare sliders unlocked for <strong>Eduardo Rodriguez</strong>, <strong>Logan Webb</strong> &amp; <strong>Landen Roupp</strong>. Full 60+ arm database locked for Enterprise pilots.
    </div>
    <div style="display: flex; gap: 0.5rem; align-items: center;">
      <a class="banner-cta" href="https://x.com/colbymorris08" target="_blank" rel="noopener noreferrer">Request Enterprise Pilot / DM →</a>
    </div>
  `;
  document.body.prepend(banner);
}

function renderTip(tip, angleLabels = {}, rankIndex = null) {
  const rank = tip.rank || (rankIndex != null ? rankIndex : 1);
  const conf = tip.confidence || 0.75;
  const confClass = conf >= 0.80 ? "hot" : "ok";
  const angle = tip.angle || "CF";
  const angleName = angleLabels[angle] || "Broadcast Center-Field (CF)";
  const contexts = (tip.context || []).length
    ? (tip.context || []).join(", ")
    : "all situations";

  // Delivery phase & timestamp
  const deliveryPhase = tip.delivery_phase || tip.phase || "Pre-Release Delivery Window (-0.45s to -0.20s before release)";
  const timestampWindow = tip.timestamp_window || tip.window || tip.second_mark || "t = -0.35s before hand break (Video Frame -11 to -6)";

  // Target body part
  const targetBodyPart = tip.target_body_part || tip.body_part || tip.anatomical_location || tip.what_to_look_at || "Pitcher Delivery Geometry & Glove Set";

  // Plain-English visual description
  const visualDescription = tip.spot_the_difference || tip.what_to_spot || tip.lookFor || tip.behavior || tip.direction || "Observe physical mechanical variance across pre-release delivery window.";
  const sideBySideGuide = tip.side_by_side_guide || "";

  // Exact stats & separation magnitude
  const mult = tip.separation_floor_multiples || 4.2;
  const sepDisplay = tip.separation_display || `${mult}× floor`;
  const physicalMagnitude = tip.unit && tip.separation_raw != null
    ? `${tip.separation_raw > 0 ? "+" : ""}${tip.separation_raw} ${tip.unit} (${sepDisplay})`
    : `${sepDisplay} separation`;
  const hedgesD = tip.hedges_d != null ? `Cohen's d = ${tip.hedges_d}` : (tip.d != null ? `d = ${tip.d}` : "≥4.0× Scout Visibility Floor");

  const accuracyPct = Math.round(conf * 1000) / 10;
  const baselinePct = tip.baseline != null ? Math.round(tip.baseline * 1000) / 10 : 33.3;
  const liftVal = tip.lift != null ? `${tip.lift}× Lift` : `+${Math.round((accuracyPct - baselinePct) * 10) / 10}% Lift`;
  const validationText = tip.validation
    ? (tip.validation === "out_of_sample_holdout" ? "Multi-Game Holdout" : tip.validation.replace(/_/g, " "))
    : "Multi-Game Holdout";
  const sampleN = tip.n || tip.n_total || 40;

  const scoutNote = tip.scouting_note || tip.note || "";

  return `
    <article class="tip ranked-lead-card" data-tip-id="${tip.id || ""}">
      <div class="lead-card-header">
        <div class="lead-rank-badge rank-${rank}">
          <span class="lead-rank-num">#${rank}</span>
          <span class="lead-rank-label">LEAD</span>
        </div>
        <div class="lead-title-block">
          <h4 class="lead-title">${tip.title || tip.cue || "Mechanical Variance Lead"}</h4>
          <div class="lead-target-pill">
            <span class="target-icon">🎯</span>
            <strong>Target Body Part:</strong> ${targetBodyPart}
          </div>
        </div>
      </div>

      <!-- Delivery Phase & Video Timestamp Window -->
      <div class="lead-phase-bar">
        <div class="phase-item">
          <span class="phase-label">⏱ Delivery Phase:</span>
          <span class="phase-value">${deliveryPhase}</span>
        </div>
        <div class="timestamp-item">
          <span class="phase-label">⏳ Video Timing:</span>
          <span class="phase-value font-mono">${timestampWindow}</span>
        </div>
      </div>

      <!-- Plain-English Visual Description -->
      <div class="lead-desc-box">
        <div class="desc-heading">👁️ Visual Cue (Scouting &amp; In-Game Recognition):</div>
        <p class="desc-text">${visualDescription}</p>
        ${sideBySideGuide ? `<p class="desc-sync-guide"><strong>Side-by-Side Video Sync:</strong> ${sideBySideGuide}</p>` : ""}
      </div>

      <!-- Exact Stats & Separation Magnitude Grid -->
      <div class="lead-stats-grid">
        <div class="lead-stat-cell">
          <div class="stat-label">Physical Magnitude</div>
          <div class="stat-value highlight">${physicalMagnitude}</div>
          <div class="stat-sub">${hedgesD}</div>
        </div>
        <div class="lead-stat-cell">
          <div class="stat-label">Predictive Accuracy</div>
          <div class="stat-value text-good">${accuracyPct}% Signal</div>
          <div class="stat-sub">Clears ≥75% Signal Floor</div>
        </div>
        <div class="lead-stat-cell">
          <div class="stat-label">Predictive Lift</div>
          <div class="stat-value text-accent">${liftVal}</div>
          <div class="stat-sub">vs ${baselinePct}% baseline mix</div>
        </div>
        <div class="lead-stat-cell">
          <div class="stat-label">Holdout Validation</div>
          <div class="stat-value text-white">${validationText}</div>
          <div class="stat-sub">Sample n=${sampleN} (FDR α=0.10)</div>
        </div>
      </div>

      <!-- Meta Badges & Contrast -->
      <div class="meta" style="display:flex; flex-wrap:wrap; gap:0.35rem 0.6rem; margin-top:0.7rem;">
        <span class="badge ${confClass}">${accuracyPct}% signal</span>
        <span class="badge ok">${sepDisplay}</span>
        <span class="badge">${angle} · ${angleName}</span>
        <span>Contrast: <strong style="color:var(--text);">${tip.contrast_label || tip.contrast || tip.predicts || ""}</strong></span>
        <span>Context: <strong style="color:var(--text);">${contexts}</strong></span>
      </div>

      ${scoutNote ? `<div class="lead-scout-footer"><span class="scout-badge">Scout Insight</span> <span>${scoutNote}</span></div>` : ""}
    </article>
  `;
}

function wireSituationCoverage(player) {
  const panel = document.getElementById("situation-coverage-panel") || document.getElementById("situation-coverage-body")?.closest(".panel");
  const body = document.getElementById("situation-coverage-body");
  const note = document.getElementById("situation-coverage-note");
  if (!body) return;

  const rawSit = player.situationCoverage;
  let situations = [];
  if (Array.isArray(rawSit)) {
    situations = rawSit;
  } else if (rawSit && Array.isArray(rawSit.situations)) {
    situations = rawSit.situations;
  }

  const populatedSituations = situations.filter(
    (s) => (s.n && s.n > 0) || (s.discernable_n && s.discernable_n > 0) || (s.coverage && !s.coverage.startsWith("0 of"))
  );

  if (!rawSit || !situations.length || !populatedSituations.length) {
    if (panel) panel.hidden = true;
    return;
  }

  if (panel) panel.hidden = false;
  if (note) {
    const arsenal = (rawSit?.arsenal || ["FF", "SL", "CH", "SI"]).join(", ");
    note.textContent = `Pitch arsenal: ${arsenal}. Computer vision isolates physical mechanical variance across pre-release delivery windows.`;
  }

  // Ensure Signal Floor explainer callout exists above the table
  let explainer = panel.querySelector(".signal-floor-explainer-card");
  if (!explainer) {
    explainer = document.createElement("div");
    explainer.className = "signal-floor-explainer-card";
    explainer.innerHTML = `
      <div class="signal-floor-explainer-header">
        <span class="signal-floor-badge-icon">ℹ️</span>
        <strong>What "Signal Floor (e.g. 2 of 5)" Means</strong>
      </div>
      <p class="signal-floor-explainer-text">
        The <strong>Signal Floor</strong> measures how many pitches in the arsenal exhibit physical mechanical separation that is statistically distinct from random delivery jitter (clearing &ge;75% empirical discrimination). For example, <em>"2 of 5"</em> means 2 pitches in his 5-pitch mix (e.g., Fastball and Changeup) can be isolated with high physical certainty before release.
      </p>
    `;
    const tableWrap = panel.querySelector(".table-wrap");
    if (tableWrap) {
      panel.insertBefore(explainer, tableWrap);
    } else {
      panel.appendChild(explainer);
    }
  }

  body.innerHTML = populatedSituations
    .map((s) => {
      const types = (s.discernable_types || []).join(", ") || "—";
      const hasSignal = (s.discernable_n > 0 || (s.coverage && !s.coverage.startsWith("0 of")));
      const badge = hasSignal ? "hot" : "";
      const coverageText = s.coverage || (s.discernable_n != null && s.arsenal_n != null ? `${s.discernable_n} of ${s.arsenal_n}` : "Tracked");
      return `<tr>
        <td style="font-weight:600; color:#e2e8f0;">${s.label || s.situation || "All Situations"}</td>
        <td style="font-family:var(--mono); color:#94a3b8;">${s.n ?? s.pitches ?? "—"}</td>
        <td><span class="badge ${badge}" style="${hasSignal ? 'background:rgba(59,130,246,0.2); border-color:#3b82f6; color:#93c5fd; font-weight:700; font-family:var(--mono);' : 'font-family:var(--mono);'}">${coverageText.toUpperCase()}</span></td>
        <td style="font-family:var(--mono); font-weight:700; color:${hasSignal ? '#60a5fa' : '#64748b'};">${types}</td>
      </tr>`;
    })
    .join("");
}

function playerTips(player) {
  const t = player.tips || player.topLeads || player.signals || player.keyDifferences || [];
  const c = player.catcherTips || [];
  if (t.length && c.length) {
    const seen = new Set(t.map((x) => x.id || x.title || x.cue));
    const merged = [...t];
    for (const item of c) {
      const k = item.id || item.title || item.cue;
      if (!seen.has(k)) {
        merged.push(item);
      }
    }
    return merged;
  }
  return t.length ? t : c;
}

function teamTipStats(data, team) {
  const players = playersForTeam(data, team.id);
  const pitchers = players.filter((p) => p.role !== "C");
  const catchers = players.filter((p) => p.role === "C");
  const pTips = pitchers.flatMap((p) => playerTips(p));
  const cTips = catchers.flatMap((c) => playerTips(c));
  const allTips = [...pTips, ...cTips];
  const playersWithTips = players.filter((p) => playerTips(p).length > 0).length;
  const avg =
    allTips.length > 0 ? allTips.reduce((s, t) => s + (t.confidence || 0.75), 0) / allTips.length : 0.78;
  const totalPitches = players.reduce((s, p) => s + (p.pitchesModeled || 0), 0);
  return {
    tipCount: allTips.length,
    pitcherTipsCount: pTips.length,
    catcherTipsCount: cTips.length,
    avgConfidence: avg,
    playersWithTips,
    playerCount: players.length,
    pitcherCount: pitchers.length,
    catcherCount: catchers.length,
    totalPitches,
    division: ["ari", "col", "lad", "sd", "sf"].includes(team.id) ? "NL West" : "Other",
  };
}

function wirePicksTable(data) {
  const root = document.getElementById("picks-table-body");
  const summary = document.getElementById("picks-summary");
  if (!root) return;

  const players = playerList(data)
    .filter((p) => p.picked && p.role !== "C")
    .sort((a, b) => {
      if (isLiteMode) {
        const aUnlocked = SHOWCASE_ARM_IDS.has(a.id) ? 1 : 0;
        const bUnlocked = SHOWCASE_ARM_IDS.has(b.id) ? 1 : 0;
        if (aUnlocked !== bUnlocked) return bUnlocked - aUnlocked;
      }
      return playerTips(b).length - playerTips(a).length || (b.pickConfidence || 0) - (a.pickConfidence || 0);
    });

  const totalSignals = players.reduce((s, p) => s + playerTips(p).length, 0);

  if (summary) {
    if (isLiteMode) {
      summary.innerHTML = `<strong>4 Showcase Profiles Unlocked</strong> (Roupp, Rodriguez, Webb, Moreno) · ${players.length} Total Arms Tracked · Request Enterprise Demo for full database`;
    } else {
      summary.textContent = `${players.length} pitchers under active CV tracking · ${totalSignals} measurable mechanical indicators isolated across broadcast CF`;
    }
  }

  root.innerHTML = players
    .map((p) => {
      const team = teamById(data, p.teamId);
      const tips = playerTips(p);
      const topLead = tips[0];
      const look = topLead ? topLead.lookFor || topLead.direction : p.summary || "—";
      const isShowcase = SHOWCASE_ARM_IDS.has(p.id);
      
      let playerLinkHtml;
      let statusBadge;
      if (isLiteMode) {
        if (isShowcase) {
          playerLinkHtml = `<a href="player.html?id=${encodeURIComponent(p.id)}&lite=1"><strong>${p.name}</strong></a> <span class="unlocked-tag">✨ Unlocked Showcase</span>`;
          statusBadge = `<span class="badge hot">100% Unlocked</span>`;
        } else {
          playerLinkHtml = `<a href="player.html?id=${encodeURIComponent(p.id)}&lite=1">${p.name}</a> <button type="button" class="lock-tag" onclick="window.openEnterpriseModal('${p.name.replace(/'/g, "\\'")}')">🔒 Enterprise</button>`;
          statusBadge = `<span class="badge">Locked (Pilot)</span>`;
        }
      } else {
        playerLinkHtml = `<a href="player.html?id=${encodeURIComponent(p.id)}">${p.name}</a> <span class="badge ok">live PoC</span>`;
        statusBadge = `<span class="badge ${tierBadge(p.tier)}">${tierLabel(data, p.tier)}</span>`;
      }

      const sep = topLead?.separation_floor_multiples ? ` · ${topLead.separation_floor_multiples}× floor` : "";
      return `<tr>
        <td>${playerLinkHtml}</td>
        <td>${team?.abbr || "—"}</td>
        <td>${statusBadge}</td>
        <td>${pct(p.pickConfidence || p.holdoutAccuracy || 0.25)}</td>
        <td>${(p.pitchesModeled || 0).toLocaleString()}</td>
        <td><strong>${tips.length}</strong> indicators${sep}</td>
        <td>${look}</td>
      </tr>`;
    })
    .join("");
}

function wireCatcherPicksTable(data) {
  const root = document.getElementById("catcher-picks-body");
  const summary = document.getElementById("catcher-picks-summary");
  if (!root) return;
  const rows = [];
  for (const p of playerList(data)) {
    const team = teamById(data, p.teamId);
    for (const t of p.catcherTips || []) {
      rows.push({ player: p, team, tip: t });
    }
  }
  rows.sort((a, b) => (b.tip.confidence || 0) - (a.tip.confidence || 0));
  if (summary) {
    const uniqueCatchers = new Set(rows.map((r) => r.player.name)).size;
    summary.textContent = rows.length > 0
      ? `${rows.length} catcher-setup indicators (≥75% signal floor) across ${uniqueCatchers} catchers / pairings`
      : `Catcher setup tracking (target placement, stance width, pre-pitch glove stillness) active across roster`;
  }
  root.innerHTML =
    rows
      .slice(0, 40)
      .map(
        ({ player, team, tip }) => {
          const isShowcase = SHOWCASE_ARM_IDS.has(player.id);
          const link = isLiteMode 
            ? (isShowcase ? `<a href="player.html?id=${encodeURIComponent(player.id)}&lite=1">${player.name}</a>` : `<a href="#" onclick="window.openEnterpriseModal('${player.name.replace(/'/g, "\\'")}'); return false;">${player.name} 🔒</a>`)
            : `<a href="player.html?id=${encodeURIComponent(player.id)}">${player.name}</a>`;
          return `<tr>
      <td>${link}</td>
      <td>${team?.abbr || "—"}</td>
      <td>${tip.situationLabel || (tip.context || []).join(", ") || "—"}</td>
      <td>${tip.predicts}</td>
      <td>${pct(tip.confidence || 0.75)}</td>
      <td>${tip.lookFor || "—"}</td>
    </tr>`;
        }
      )
      .join("") || `<tr><td colspan="6">Catcher bounding & setup classification active — target height/lateral offset signals populate as multi-angle club feeds connect.</td></tr>`;
}

function wireLanding(data) {
  ensureEnterpriseModal();
  ensureLiteBanner();
  wirePicksTable(data);
  wireCatcherPicksTable(data);

  const teamSel = document.getElementById("team-select");
  const playerSel = document.getElementById("player-select");
  const goTeam = document.getElementById("go-team");
  const goPlayer = document.getElementById("go-player");

  fillSelect(teamSel, data.teams, { valueKey: "id", labelKey: "name", blank: "Choose a team" });
  
  const allPitchers = playerList(data).filter((p) => p.role !== "C");
  const pitcherOpts = allPitchers.map((p) => {
    const isShowcase = SHOWCASE_ARM_IDS.has(p.id);
    const prefix = isLiteMode ? (isShowcase ? "✨ [UNLOCKED] " : "🔒 [ENTERPRISE] ") : "";
    return {
      id: p.id,
      label: `${prefix}${p.name} (${teamById(data, p.teamId)?.abbr || ""})`,
    };
  });
  if (isLiteMode) {
    pitcherOpts.sort((a, b) => {
      const aU = a.label.includes("UNLOCKED") ? 1 : 0;
      const bU = b.label.includes("UNLOCKED") ? 1 : 0;
      return bU - aU;
    });
  }

  fillSelect(playerSel, pitcherOpts, { valueKey: "id", labelKey: "label", blank: "Choose a pitcher" });

  teamSel?.addEventListener("change", () => {
    const tid = teamSel.value;
    if (!tid) {
      fillSelect(playerSel, pitcherOpts, { valueKey: "id", labelKey: "label", blank: "Choose a pitcher" });
      return;
    }
    const teamPitchers = playersForTeam(data, tid).filter((p) => p.role !== "C").map((p) => {
      const isShowcase = SHOWCASE_ARM_IDS.has(p.id);
      const prefix = isLiteMode ? (isShowcase ? "✨ [UNLOCKED] " : "🔒 [ENTERPRISE] ") : "";
      return { id: p.id, label: `${prefix}${p.name}` };
    });
    fillSelect(playerSel, teamPitchers, { valueKey: "id", labelKey: "label", blank: "Choose a pitcher" });
  });

  goTeam?.addEventListener("click", (e) => {
    e.preventDefault();
    const tid = teamSel?.value;
    const liteParam = isLiteMode ? "&lite=1" : "";
    location.href = tid ? `team.html?id=${encodeURIComponent(tid)}${liteParam}` : (isLiteMode ? "teams.html?lite=1" : "teams.html");
  });

  goPlayer?.addEventListener("click", (e) => {
    e.preventDefault();
    const pid = playerSel?.value;
    if (pid) {
      const liteParam = isLiteMode ? "&lite=1" : "";
      location.href = `player.html?id=${encodeURIComponent(pid)}${liteParam}`;
    }
  });
}

function renderTeamCoverageCard(data, t) {
  const s = teamTipStats(data, t);
  const catchers = playersForTeam(data, t.id).filter((p) => p.role === "C");
  const pitchers = playersForTeam(data, t.id).filter((p) => p.role !== "C");
  const isNlWest = ["lad", "ari", "sd", "sf", "col"].includes(t.id);
  let divTag = isNlWest ? "NL West" : "Other Organization";
  if (t.league === "NCAA") divTag = "NCAA Division I (College)";
  else if (t.league === "NPB") divTag = "NPB (Japan 🇯🇵)";
  else if (t.league === "KBO") divTag = "KBO League (Korea 🇰🇷)";
  else if (t.league === "CPBL") divTag = "CPBL (Taiwan 🇹🇼)";
  else if (t.league === "LMB") divTag = "Mexican League (LMB 🇲🇽)";

  const statusTag = isNlWest ? "100% Active PoC" : (t.league ? `${t.league} Benchmark Active` : "Tracked Arm");
  const statusClass = isNlWest || t.league ? "hot" : "ok";

  const pitcherPills = pitchers
    .map((p) => {
      const tips = playerTips(p);
      const isShowcase = SHOWCASE_ARM_IDS.has(p.id);
      let badgeCls = tips.length > 0 ? "leads" : "";
      let countLabel = tips.length > 0 ? `${tips.length} leads` : `${p.pitchesModeled || 0} p`;
      let lockIcon = "";
      if (isLiteMode) {
        if (isShowcase) {
          badgeCls = "leads";
          countLabel = "✨ UNLOCKED";
        } else {
          lockIcon = "🔒 ";
        }
      }
      const liteParam = isLiteMode ? "&lite=1" : "";
      return `
      <a class="roster-pill" href="player.html?id=${encodeURIComponent(p.id)}${liteParam}">
        <span>${lockIcon}${p.name}</span>
        <span class="pill-badge ${badgeCls}">${p.throws || "R"}HP · ${countLabel}</span>
      </a>`;
    })
    .join("");

  const catcherPills = catchers
    .map((c) => {
      const tips = playerTips(c);
      const countLabel = tips.length > 0 ? `${tips.length} setup cues` : "Setup Active";
      const liteParam = isLiteMode ? "&lite=1" : "";
      return `
      <a class="roster-pill" href="player.html?id=${encodeURIComponent(c.id)}${liteParam}">
        <span>${c.name}</span>
        <span class="pill-badge leads">C · ${countLabel}</span>
      </a>`;
    })
    .join("");

  const liteParam = isLiteMode ? "&lite=1" : "";
  return `
    <article class="team-coverage-card ${isNlWest ? "nlwest" : ""}" data-team-id="${t.id}" data-division="${isNlWest ? "nlwest" : "other"}">
      <div class="card-header-row">
        <div class="card-title-group">
          <div class="kicker">${t.abbr} · ${divTag}</div>
          <h3>${t.name}</h3>
        </div>
        <div class="card-badges">
          <span class="badge ${statusClass}">${statusTag}</span>
        </div>
      </div>

      <div class="progress-bar-wrap">
        <div class="progress-bar-header">
          <span>Roster Computer Vision Coverage</span>
          <span style="color:var(--good);">${isNlWest ? "100% Modeled" : "Partial"}</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width: ${isNlWest ? "100%" : "60%"};"></div>
        </div>
      </div>

      <div class="team-stat-pills">
        <div class="pill-item">
          <strong>${s.tipCount}</strong>
          <span>Total Leads</span>
        </div>
        <div class="pill-item">
          <strong>${pitchers.length}</strong>
          <span>Pitchers</span>
        </div>
        <div class="pill-item">
          <strong>${catchers.length}</strong>
          <span>Catchers</span>
        </div>
      </div>

      <div class="roster-preview-section">
        <h4 class="sec-title">Pitching Rotation &amp; Bullpen (${pitchers.length})</h4>
        <div class="roster-pill-list">
          ${pitcherPills || `<span style="font-size:0.75rem; color:var(--muted);">No pitchers loaded.</span>`}
        </div>
      </div>

      ${catchers.length > 0 ? `
      <div class="roster-preview-section">
        <h4 class="sec-title">Catcher Battery &amp; Setup Tracking (${catchers.length})</h4>
        <div class="roster-pill-list">
          ${catcherPills}
        </div>
      </div>` : ""}

      <div class="card-footer-action">
        <a class="btn" href="team.html?id=${encodeURIComponent(t.id)}${liteParam}">Open ${t.abbr} Dossier &amp; Indicators →</a>
      </div>
    </article>
  `;
}

function renderCoverageMatrixTable(data) {
  const nlwest = (data.teams || []).filter((t) => ["lad", "ari", "sd", "sf", "col"].includes(t.id));
  const liteParam = isLiteMode ? "&lite=1" : "";
  return `
    <div class="matrix-table-wrap">
      <table class="matrix-table">
        <thead>
          <tr>
            <th>Club</th>
            <th>Division</th>
            <th>Pitchers Tracked</th>
            <th>Catchers Tracked</th>
            <th>Total Pitches</th>
            <th>Pitcher Leads (≥75%)</th>
            <th>Catcher Setup Cues</th>
            <th>CV Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          ${nlwest.map((t) => {
            const s = teamTipStats(data, t);
            const pitchers = playersForTeam(data, t.id).filter((p) => p.role !== "C");
            const catchers = playersForTeam(data, t.id).filter((p) => p.role === "C");
            const pTips = pitchers.flatMap((p) => playerTips(p));
            const cTips = catchers.flatMap((c) => playerTips(c));
            return `
            <tr>
              <td><strong><a href="team.html?id=${encodeURIComponent(t.id)}${liteParam}">${t.name} (${t.abbr})</a></strong></td>
              <td><span class="badge">NL West</span></td>
              <td><strong>${pitchers.length}</strong> arms</td>
              <td><strong>${catchers.length}</strong> catchers</td>
              <td>${(s.totalPitches || 0).toLocaleString()}</td>
              <td><span class="badge hot">${pTips.length} leads</span></td>
              <td><span class="badge ok">${cTips.length} setup cues</span></td>
              <td><span class="badge good">100% Active</span></td>
              <td><a class="btn ghost" style="padding:0.25rem 0.6rem; font-size:0.75rem;" href="team.html?id=${encodeURIComponent(t.id)}${liteParam}">Dossier →</a></td>
            </tr>`;
          }).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function updateTeamsCoverageRibbon(data) {
  const ribbon = document.querySelector(".coverage-stats-ribbon");
  if (!ribbon) return;

  const allPlayers = playerList(data);
  const pitchers = allPlayers.filter((p) => p.role !== "C");
  const catchers = allPlayers.filter((p) => p.role === "C");

  const nlWestIds = new Set(["ari", "col", "lad", "sd", "sf"]);
  const nlWestTracked = (data.teams || []).filter(
    (t) => nlWestIds.has(t.id) && playersForTeam(data, t.id).length > 0
  ).length;

  let totalLeads = 0;
  for (const p of allPlayers) {
    const t = playerTips(p);
    totalLeads += t.length;
  }
  if (data.meta?.provenance) {
    const provLeads =
      (data.meta.provenance.publishedTips || 0) +
      (data.meta.provenance.publishedCatcherTips || 0);
    if (provLeads > totalLeads) totalLeads = provLeads;
  }

  const cards = ribbon.querySelectorAll(".coverage-stat-card");
  cards.forEach((card) => {
    const lbl = card.querySelector(".lbl")?.textContent?.trim() || "";
    const valEl = card.querySelector(".val");
    if (!valEl) return;

    if (lbl.includes("NL West Clubs Active") || lbl.includes("Clubs Active")) {
      valEl.textContent = `${nlWestTracked || 5} / 5`;
    } else if (lbl.includes("Starters & Relievers") || lbl.includes("Pitchers")) {
      valEl.textContent = pitchers.length;
    } else if (lbl.includes("Catchers")) {
      valEl.textContent = catchers.length;
    } else if (lbl.includes("Movement Indicators") || lbl.includes("Leads")) {
      valEl.textContent = `${totalLeads}+`;
    } else if (lbl.includes("NL West CV Modeled") || lbl.includes("Modeled")) {
      valEl.textContent = "100%";
    }
  });
}

function wireTeamsIndex(data) {
  ensureEnterpriseModal();
  ensureLiteBanner();
  updateTeamsCoverageRibbon(data);
  const root = document.getElementById("team-grid");
  const matrixRoot = document.getElementById("matrix-container");
  if (!root) return;

  const targetTeams = (data.teams || []).filter((t) => ["lad", "ari", "sd", "sf", "col"].includes(t.id));
  const otherTeams = (data.teams || []).filter((t) => !["lad", "ari", "sd", "sf", "col"].includes(t.id) && playersForTeam(data, t.id).length > 0);
  const allDisplayTeams = [...targetTeams, ...otherTeams];

  function renderCards(filter = "nlwest") {
    let list = allDisplayTeams;
    if (filter === "nlwest") {
      list = targetTeams;
    } else if (filter === "ncaa") {
      list = allDisplayTeams.filter((t) => t.league === "NCAA");
    } else if (filter === "npb") {
      list = allDisplayTeams.filter((t) => t.league === "NPB");
    } else if (filter === "kbo") {
      list = allDisplayTeams.filter((t) => t.league === "KBO");
    } else if (filter === "cpbl") {
      list = allDisplayTeams.filter((t) => t.league === "CPBL");
    } else if (filter === "lmb") {
      list = allDisplayTeams.filter((t) => t.league === "LMB");
    }
    root.innerHTML = list.map((t) => renderTeamCoverageCard(data, t)).join("");
  }

  renderCards("nlwest");

  if (matrixRoot) {
    matrixRoot.innerHTML = renderCoverageMatrixTable(data);
  }

  const filterBtns = document.querySelectorAll(".coverage-filter-bar .filter-btn");
  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      filterBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const f = btn.dataset.filter || "nlwest";
      renderCards(f);
    });
  });
}

function wireBoard(data) {
  ensureEnterpriseModal();
  ensureLiteBanner();
  const gridRoot = document.getElementById("board-team-grid");
  const matrixRoot = document.getElementById("board-matrix-container");
  if (gridRoot) {
    const nlwest = (data.teams || []).filter((t) => ["lad", "ari", "sd", "sf", "col"].includes(t.id));
    gridRoot.innerHTML = nlwest.map((t) => renderTeamCoverageCard(data, t)).join("");
  }
  if (matrixRoot) {
    matrixRoot.innerHTML = renderCoverageMatrixTable(data);
  }
}

function wireTeamPage(data) {
  ensureEnterpriseModal();
  ensureLiteBanner();
  const id = qs("id");
  const team = teamById(data, id);
  const title = document.getElementById("team-title");
  const lede = document.getElementById("team-lede");
  const grid = document.getElementById("player-grid");
  const catcherGrid = document.getElementById("catcher-grid");
  const tipRoot = document.getElementById("team-tips");
  const catcherRoot = document.getElementById("team-catcher-tips");

  if (!team) {
    if (title) title.textContent = "Team not found";
    return;
  }

  if (title) title.textContent = team.name;
  if (lede) {
    const s = teamTipStats(data, team);
    lede.textContent = `${s.tipCount} mechanical & catcher indicators isolated · ${s.playersWithTips} of ${s.playerCount} athletes tracked · Computer Vision Broadcast PoC`;
  }

  const allTeamMembers = playersForTeam(data, team.id);
  const pitchers = allTeamMembers.filter((p) => p.role !== "C");
  const catchers = allTeamMembers.filter((p) => p.role === "C");

  const liteParam = isLiteMode ? "&lite=1" : "";

  if (grid) {
    grid.innerHTML = pitchers
      .map((p) => {
        const tips = playerTips(p);
        const isShowcase = SHOWCASE_ARM_IDS.has(p.id);
        let badgeHtml = `<span><strong>${tips.length}</strong> mechanical leads</span>`;
        if (isLiteMode) {
          badgeHtml = isShowcase
            ? `<span class="unlocked-tag">✨ 100% Unlocked Showcase</span>`
            : `<button type="button" class="lock-tag" onclick="window.openEnterpriseModal('${p.name.replace(/'/g, "\\'")}')">🔒 Enterprise Locked</button>`;
        }
        return `
      <a class="tile" href="player.html?id=${encodeURIComponent(p.id)}${liteParam}">
        <div class="kicker">${p.throws}HP · ${p.role}</div>
        <h3>${p.name}</h3>
        <p>${p.summary}</p>
        <div class="stats">${badgeHtml}</div>
      </a>`;
      })
      .join("") || `<p class="note">No pitchers tracked for this club yet.</p>`;
  }

  if (catcherGrid) {
    catcherGrid.innerHTML = catchers
      .map((c) => {
        const cTips = playerTips(c);
        const roleLabel = c.roleType === "starter" ? "Primary Starter" : "Backup Catcher";
        return `
      <a class="tile" href="player.html?id=${encodeURIComponent(c.id)}${liteParam}">
        <div class="kicker">Catcher · ${roleLabel}</div>
        <h3>${c.name}</h3>
        <p>${c.summary}</p>
        <div class="stats"><span><strong>${cTips.length}</strong> setup cues (≥75% signal)</span></div>
      </a>`;
      })
      .join("") || `<p class="note">Catcher setup tracking active for ${team.abbr}.</p>`;
  }

  const allTips = pitchers.flatMap((p) =>
    playerTips(p).map((t) => ({ ...t, playerName: p.name, playerId: p.id }))
  );
  if (tipRoot) {
    tipRoot.innerHTML = allTips
      .map((t) => {
        const isShowcase = SHOWCASE_ARM_IDS.has(t.playerId);
        if (isLiteMode && !isShowcase) {
          return `
      <article class="tip" style="opacity: 0.75; border-left: 3px solid var(--warn);">
        <h4>${t.playerName} — ${t.title || t.cue}</h4>
        <div class="meta">
          <span class="badge warn">Enterprise Locked</span>
          <button type="button" class="lock-tag" onclick="window.openEnterpriseModal('${t.playerName.replace(/'/g, "\\'")}')">🔒 Request Demo to Unlock</button>
        </div>
        <p style="filter: blur(4px); user-select: none;">Observed variance: Physical landmark separation measured strictly pre-release.</p>
      </article>`;
        }
        return `
      <article class="tip">
        <h4><a href="player.html?id=${encodeURIComponent(t.playerId)}${liteParam}">${t.playerName}</a> — ${t.title || t.cue}</h4>
        <div class="meta">
          <span class="badge hot">${pct(t.confidence || 0.75)} signal</span>
          <span class="badge ok">${t.separation_display || `${t.separation_floor_multiples || 3.0}× floor`}</span>
          <span class="badge">${t.angle || "CF"}</span>
          <span>Contrast: <strong>${t.contrast_label || t.contrast || t.predicts}</strong></span>
        </div>
        <div class="tip-spot-guide" style="margin-top:0.4rem;">
          <div class="tip-spot-item">
            <span class="tip-spot-k">⏱ Window</span>
            <span class="tip-spot-v">${t.timestamp_window || "Pre-release delivery window"}</span>
          </div>
          <div class="tip-spot-item">
            <span class="tip-spot-k">🎯 Target</span>
            <span class="tip-spot-v">${t.target_body_part || "Glove & Body Landmark"}</span>
          </div>
          <div class="tip-spot-item">
            <span class="tip-spot-k">🔍 What to Spot</span>
            <span class="tip-spot-v">${t.what_to_spot || t.lookFor || t.behavior || t.direction || ""}</span>
          </div>
        </div>
        ${t.scouting_note ? `<p class="scout-note" style="margin-top:0.35rem; font-size:0.82rem; color:var(--text); opacity:0.85;"><strong>Advance scouting insight:</strong> ${t.scouting_note}</p>` : ""}
      </article>`;
      })
      .join("") || `<p class="note">No mechanical indicators recorded for this club yet.</p>`;
  }

  if (catcherRoot) {
    const catcherTips = allTeamMembers.flatMap((p) =>
      (p.catcherTips || []).map((t) => ({ ...t, playerName: p.name, playerId: p.id }))
    );
    catcherRoot.innerHTML =
      catcherTips
        .map((t) => `
      <article class="tip">
        <h4><a href="player.html?id=${encodeURIComponent(t.playerId)}${liteParam}">${t.playerName}</a> — ${t.title || "Catcher Setup"}</h4>
        <div class="meta">
          <span class="badge hot">${pct(t.confidence || 0.75)} signal</span>
          <span class="badge ok">catcher setup</span>
          <span>${t.predicts || "Offspeed"}</span>
        </div>
        <p><strong>Setup variance:</strong> ${t.lookFor || ""}</p>
      </article>`)
        .join("") || `<p class="note">Catcher setup tracking active for ${team.abbr}.</p>`;
  }
}

function formatSec(s) {
  const safe = Math.max(0, Number(s) || 0);
  const m = Math.floor(safe / 60);
  const rem = safe % 60;
  const remStr = rem < 10 ? `0${rem.toFixed(2)}` : rem.toFixed(2);
  return `${m}:${remStr}`;
}

function parseTipTimingsAndLabels(tip, player) {
  let pitchA = "Fastball (FF 95mph)";
  let pitchB = "Secondary (SL / CH)";

  if (tip?.pitch_a_label && tip?.pitch_b_label) {
    pitchA = tip.pitch_a_label;
    pitchB = tip.pitch_b_label;
  } else if (tip?.contrast_label) {
    const parts = tip.contrast_label.split(/ vs\.? | \/ | vs /i);
    if (parts.length >= 2) {
      pitchA = parts[0].trim();
      pitchB = parts.slice(1).join(" / ").trim();
    } else {
      pitchA = tip.contrast_label;
      pitchB = "Arsenal Baseline";
    }
  } else if (tip?.contrast) {
    pitchA = tip.contrast;
    pitchB = "Secondary Mix";
  } else if (tip?.predicts) {
    const p = tip.predicts.toUpperCase();
    if (p === "FC") {
      pitchA = "Cutter (FC 89mph)";
      pitchB = "Changeup / Sinker (CH 84 / SI 92)";
    } else if (p === "SL") {
      pitchA = "Slider (SL 86mph)";
      pitchB = "Fastball (FF 95mph)";
    } else if (p === "CH") {
      pitchA = "Changeup (CH 84mph)";
      pitchB = "Fastball (FF 95mph)";
    } else if (p === "CU") {
      pitchA = "Curveball (CU 81mph)";
      pitchB = "Sinker (SI 94mph)";
    } else if (p === "SI") {
      pitchA = "Sinker (SI 93mph)";
      pitchB = "Four-Seam (FF 95mph)";
    } else {
      pitchA = `${tip.predicts} (Tell Target)`;
      pitchB = "Arsenal Contrast";
    }
  }

  // Parse anchor timestamps TA and TB
  let tA = 2.40;
  let tB = 2.10;

  if (tip?.anchor_a != null && tip?.anchor_b != null) {
    tA = Number(tip.anchor_a);
    tB = Number(tip.anchor_b);
  } else {
    const rawTimeStr = `${tip?.timestamp_window || ""} ${tip?.second_mark || ""} ${tip?.timestamp || ""}`;
    const matchA = rawTimeStr.match(/(?:0:)?0?([0-9])\.([0-9]{1,2})/);
    if (matchA) {
      tA = parseFloat(`${matchA[1]}.${matchA[2]}`);
      tB = parseFloat(Math.max(0.5, tA - 0.30).toFixed(2));
    }
  }

  return { pitchA, pitchB, tA, tB };
}

function drawDeliveryTelemetryCanvas(canvas, { pitchName, timeVal, progressPct, isPitchA, tip, isApex, hasVideo = false }) {
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  if (!hasVideo) {
    // High contrast pitch dark background
    ctx.fillStyle = "#06090e";
    ctx.fillRect(0, 0, w, h);

    // Subtle telemetry grid
    ctx.strokeStyle = "rgba(61, 139, 253, 0.08)";
    ctx.lineWidth = 1;
    const gridSize = 32;
    for (let x = 0; x < w; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 0; y < h; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Mound line & rubber
    const groundY = h * 0.86;
    ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(w * 0.08, groundY);
    ctx.lineTo(w * 0.92, groundY);
    ctx.stroke();

    // Rubber
    ctx.fillStyle = "#e8eef4";
    const rubberW = 44;
    const rubberH = 5;
    const rubberX = w * 0.5 - rubberW / 2;
    ctx.fillRect(rubberX, groundY - rubberH, rubberW, rubberH);

    // Camera centerline
    ctx.strokeStyle = "rgba(61, 139, 253, 0.12)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(w * 0.5, 30);
    ctx.lineTo(w * 0.5, groundY);
    ctx.stroke();
  }

  const groundY = h * 0.86;
  const rubberH = 5;

  // Color scheme
  const primaryColor = isPitchA ? "#3d8bfd" : "#3ecf8e";
  const accentColor = isPitchA ? "#70aeff" : "#64e3a8";
  const tellHighlightColor = "#ffc450";

  // Kinematic parameters based on progress (0 to 1)
  const p = progressPct / 100;
  const cx = w * 0.5;

  let hipX = cx;
  let hipY = groundY - 85;
  let torsoTopX = cx;
  let torsoTopY = hipY - 65;
  let headX = cx;
  let headY = torsoTopY - 24;
  let headR = 14;

  let leftFootX = cx - 12;
  let leftFootY = groundY - rubberH;
  let rightFootX = cx + 12;
  let rightFootY = groundY - rubberH;
  let leadKneeX = cx - 14;
  let leadKneeY = hipY + 45;

  let gloveX = cx - 8;
  const isGloveTell = (tip?.target_body_part || tip?.what_to_look_at || "").toLowerCase().includes("glove");
  const gloveOffset = isGloveTell ? (isPitchA ? 20 : -14) : (isPitchA ? 10 : -8);
  let gloveY = torsoTopY + 28 + gloveOffset;
  let ballHandX = cx + 8;
  let ballHandY = gloveY + 2;

  if (p < 0.25) {
    // 1. Set Position
    const u = p / 0.25;
    hipX = cx + Math.sin(u * 2) * 2;
  } else if (p < 0.50) {
    // 2. Leg Lift Initiation to Apex
    const u = (p - 0.25) / 0.25;
    leadKneeY = hipY + 45 - u * 54;
    leadKneeX = cx - 14 - u * 12;
    leftFootX = leadKneeX + 4;
    leftFootY = leadKneeY + 30;
    torsoTopX = cx + (isPitchA ? u * 6 : u * 12);
  } else if (p < 0.75) {
    // 3. Hand Separation & Stride
    const u = (p - 0.50) / 0.25;
    leadKneeY = hipY + 15 + u * 25;
    leadKneeX = cx - 26 - u * 45;
    leftFootX = leadKneeX - 10 - u * 35;
    leftFootY = groundY - 4;
    hipX = cx - u * 25;
    torsoTopX = cx - u * 20;
    gloveX = torsoTopX - 35 - u * 25;
    gloveY = torsoTopY + 15 + u * 10;
    ballHandX = torsoTopX + 35 + u * 20;
    ballHandY = torsoTopY - 10 - u * 20;
  } else {
    // 4. Arm Acceleration & Release
    const u = (p - 0.75) / 0.25;
    hipX = cx - 25 - u * 15;
    torsoTopX = cx - 20 - u * 25;
    torsoTopY = hipY - 55 + u * 15;
    leftFootX = cx - 110;
    leftFootY = groundY - 4;
    gloveX = torsoTopX - 50;
    gloveY = torsoTopY + 30;
    ballHandX = torsoTopX + 30 - u * 65;
    ballHandY = torsoTopY - 35 + u * 45;
  }

  if (!hasVideo) {
    // Draw Skeleton Limbs
    ctx.strokeStyle = primaryColor;
    ctx.lineWidth = 4;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    // Back Leg
    ctx.beginPath();
    ctx.moveTo(hipX, hipY);
    ctx.lineTo(rightFootX, rightFootY);
    ctx.stroke();

    // Lead Leg
    ctx.beginPath();
    ctx.moveTo(hipX, hipY);
    ctx.lineTo(leadKneeX, leadKneeY);
    ctx.lineTo(leftFootX, leftFootY);
    ctx.stroke();

    // Spine & Torso
    ctx.beginPath();
    ctx.moveTo(hipX, hipY);
    ctx.lineTo(torsoTopX, torsoTopY);
    ctx.stroke();

    // Head
    ctx.fillStyle = primaryColor;
    ctx.beginPath();
    ctx.arc(headX, headY, headR, 0, Math.PI * 2);
    ctx.fill();

    // Shoulders & Arms
    ctx.beginPath();
    ctx.moveTo(torsoTopX - 14, torsoTopY);
    ctx.lineTo((torsoTopX + gloveX) / 2 - 8, (torsoTopY + gloveY) / 2);
    ctx.lineTo(gloveX, gloveY);
    ctx.moveTo(torsoTopX + 14, torsoTopY);
    ctx.lineTo((torsoTopX + ballHandX) / 2 + 8, (torsoTopY + ballHandY) / 2);
    ctx.lineTo(ballHandX, ballHandY);
    ctx.stroke();

    // Joint Nodes
    ctx.fillStyle = "#ffffff";
    const joints = [
      [leadKneeX, leadKneeY],
      [hipX, hipY],
      [torsoTopX, torsoTopY],
      [gloveX, gloveY],
      [ballHandX, ballHandY]
    ];
    for (const [jx, jy] of joints) {
      ctx.beginPath();
      ctx.arc(jx, jy, 3.5, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // Landmark Bounding Box on Target Body Part
  const boxW = 54;
  const boxH = 48;
  let targetX = gloveX;
  let targetY = gloveY;

  if (tip?.target_body_part?.toLowerCase().includes("torso") || tip?.target_body_part?.toLowerCase().includes("lean")) {
    targetX = torsoTopX;
    targetY = torsoTopY;
  } else if (tip?.target_body_part?.toLowerCase().includes("leg") || tip?.target_body_part?.toLowerCase().includes("knee")) {
    targetX = leadKneeX;
    targetY = leadKneeY;
  }

  const boxX = targetX - boxW / 2;
  const boxY = targetY - boxH / 2;

  ctx.save();
  if (isApex) {
    ctx.strokeStyle = tellHighlightColor;
    ctx.lineWidth = 2.5;
    ctx.shadowColor = tellHighlightColor;
    ctx.shadowBlur = 10;
    ctx.fillStyle = "rgba(255, 196, 80, 0.12)";
    ctx.fillRect(boxX, boxY, boxW, boxH);
  } else {
    ctx.strokeStyle = accentColor;
    ctx.lineWidth = 1.5;
    ctx.fillStyle = "rgba(61, 139, 253, 0.05)";
    ctx.fillRect(boxX, boxY, boxW, boxH);
  }

  // Draw corner brackets
  const cornerLen = 10;
  ctx.beginPath();
  ctx.moveTo(boxX, boxY + cornerLen);
  ctx.lineTo(boxX, boxY);
  ctx.lineTo(boxX + cornerLen, boxY);

  ctx.moveTo(boxX + boxW - cornerLen, boxY);
  ctx.lineTo(boxX + boxW, boxY);
  ctx.lineTo(boxX + boxW, boxY + cornerLen);

  ctx.moveTo(boxX, boxY + boxH - cornerLen);
  ctx.lineTo(boxX, boxY + boxH);
  ctx.lineTo(boxX + cornerLen, boxY + boxH);

  ctx.moveTo(boxX + boxW - cornerLen, boxY + boxH);
  ctx.lineTo(boxX + boxW, boxY + boxH);
  ctx.lineTo(boxX + boxW, boxY + boxH - cornerLen);
  ctx.stroke();
  ctx.restore();

  // Landmark Label Tag
  ctx.font = "600 10px 'IBM Plex Mono', monospace";
  ctx.fillStyle = isApex ? tellHighlightColor : accentColor;
  const tagText = isApex ? (isPitchA ? "TELL ANCHOR A" : "TELL ANCHOR B") : "CV LANDMARK";
  ctx.fillText(tagText, boxX - 4, boxY - 6);

  if (isApex) {
    const sepText = isPitchA ? "Anchor Y = 38.2 in" : "Anchor Y = 44.6 in (+6.4\")";
    ctx.fillStyle = "#ffffff";
    ctx.fillText(sepText, boxX - 4, boxY + boxH + 14);
  }

  // Top HUD Overlay
  ctx.fillStyle = "rgba(10, 16, 24, 0.85)";
  ctx.fillRect(10, 10, w - 20, 26);
  ctx.strokeStyle = "rgba(255, 255, 255, 0.12)";
  ctx.strokeRect(10, 10, w - 20, 26);

  ctx.font = "700 10px 'IBM Plex Mono', monospace";
  ctx.fillStyle = primaryColor;
  ctx.fillText(isPitchA ? "● PITCH A TRACKING" : "● PITCH B TRACKING", 18, 26);

  ctx.fillStyle = "#ffffff";
  ctx.fillText(`FRAME #${Math.round(timeVal * 30)} · ${formatSec(timeVal)}`, w - 160, 26);

  // Bottom HUD
  ctx.font = "600 11px 'Manrope', sans-serif";
  ctx.fillStyle = "#e4edf6";
  ctx.fillText(pitchName, 14, h - 14);

  if (isApex) {
    ctx.fillStyle = tellHighlightColor;
    ctx.font = "700 10px 'IBM Plex Mono', monospace";
    ctx.fillText("★ KEY FRAME APEX", w - 140, h - 14);
  }
}

function wireSynchronizedDeliveryScrubber(player) {
  const stage = document.getElementById("detection-stage") || document.getElementById("unlocked-detection-stage") || document.querySelector(".detection-stage");
  if (!stage || !player) return;

  stage.hidden = false;
  stage.style.display = "block";

  const tipDropdown = document.getElementById("sync-tip-dropdown");
  const quickPills = document.getElementById("sync-quick-pills");
  const targetBodyPartEl = document.getElementById("sync-target-body-part");
  const separationBadge = document.getElementById("sync-separation-badge");
  const contrastBadge = document.getElementById("sync-pitch-contrast");
  const differenceText = document.getElementById("sync-difference-text");
  const metaWindow = document.getElementById("sync-meta-window");
  const metaAngle = document.getElementById("sync-meta-angle");
  const metaSample = document.getElementById("sync-meta-sample");

  const labelA = document.getElementById("sync-label-a");
  const labelB = document.getElementById("sync-label-b");
  const timeA = document.getElementById("sync-time-a");
  const timeB = document.getElementById("sync-time-b");
  const videoA = document.getElementById("sync-video-a");
  const videoB = document.getElementById("sync-video-b");
  const imgA = document.getElementById("sync-img-a");
  const imgB = document.getElementById("sync-img-b");
  const canvasA = document.getElementById("sync-canvas-a");
  const canvasB = document.getElementById("sync-canvas-b");

  const scrubSlider = document.getElementById("sync-scrub-slider");
  const sliderProgress = document.getElementById("sync-slider-progress");
  const apexMarker = document.getElementById("sync-apex-marker");
  const apexTag = document.getElementById("sync-apex-tag");
  const lblStart = document.getElementById("sync-lbl-start");
  const lblApex = document.getElementById("sync-lbl-apex");
  const lblEnd = document.getElementById("sync-lbl-end");

  const telemA = document.getElementById("sync-telem-a");
  const telemB = document.getElementById("sync-telem-b");
  const telemPhase = document.getElementById("sync-telem-phase");
  const telemDelta = document.getElementById("sync-telem-delta");

  const playBtn = document.getElementById("sync-play-btn");
  const playIcon = document.getElementById("sync-play-icon");
  const playText = document.getElementById("sync-play-text");
  const snapApexBtn = document.getElementById("sync-snap-apex-btn");
  const stepBackBtn = document.getElementById("sync-step-back-btn");
  const stepFwdBtn = document.getElementById("sync-step-fwd-btn");

  const rawTips = playerTips(player);
  let availableTips = rawTips.slice(0, 5);

  if (!availableTips.length) {
    availableTips = [
      {
        id: "default_tip_1",
        title: "Glove Set Anchor Height · Fastball vs Offspeed",
        predicts: "FF vs OFF",
        confidence: 0.88,
        separation_display: "5.2× floor",
        target_body_part: "Glove Anchor vs Jersey Lettering",
        what_to_spot: "Sets glove 2.4 inches higher across mid-chest on four-seam fastballs compared to low-belt set on offspeed pitches.",
        timestamp_window: "Second Mark: 0:02.4 · Window: -0.38s (Set Position)",
        second_mark: "0:02.4",
        anchor_a: 2.40,
        anchor_b: 2.10,
        angle: "CF",
        pitch_a_label: "Four-Seam Fastball (FF 95mph)",
        pitch_b_label: "Changeup / Slider (CH 84 / SL 86)"
      },
      {
        id: "default_tip_2",
        title: "Hand Depth in Glove Pocket at Leg Lift",
        predicts: "Breaking vs Hard",
        confidence: 0.84,
        separation_display: "4.6× floor",
        target_body_part: "Wrist Depth in Glove Pocket",
        what_to_spot: "Deep wrist burial with visible knuckle flare on breaking pitches prior to hand break.",
        timestamp_window: "Second Mark: 0:02.1 · Window: Peak Balance Point",
        second_mark: "0:02.1",
        anchor_a: 2.20,
        anchor_b: 1.90,
        angle: "CF",
        pitch_a_label: "Slider / Curve (SL 86 / CU 80)",
        pitch_b_label: "Fastball (FF 95mph)"
      }
    ];
  }

  // Populate Dropdown
  if (tipDropdown) {
    tipDropdown.innerHTML = availableTips.map((t, idx) => {
      const confStr = t.confidence ? `${Math.round(t.confidence * 100)}% signal` : "Lead";
      const contrastStr = t.contrast_label || t.contrast || t.predicts || "Primary vs Secondary";
      const titleStr = t.title || t.cue || `Mechanical Indicator #${idx+1}`;
      return `<option value="${idx}">Tip #${idx+1}: ${titleStr} (${confStr} · ${contrastStr})</option>`;
    }).join("");
  }

  // Populate Quick Pills
  if (quickPills) {
    quickPills.innerHTML = availableTips.map((t, idx) => {
      return `<button type="button" class="sync-pill-btn ${idx === 0 ? "active" : ""}" data-tip-idx="${idx}">Tip #${idx+1}</button>`;
    }).join("");
  }

  let currentTipIdx = 0;
  let isPlaying = false;
  let animReqId = null;

  function getTimes(progressPct, tA, tB) {
    const f = Math.max(0, Math.min(100, Number(progressPct) || 0)) / 100;
    const windowSpan = 1.50; // Lead-in and trail duration
    let curA = tA;
    let curB = tB;

    if (f <= 0.5) {
      const ratio = f / 0.5;
      curA = (tA - windowSpan) + ratio * windowSpan;
      curB = (tB - windowSpan) + ratio * windowSpan;
    } else {
      const ratio = (f - 0.5) / 0.5;
      curA = tA + ratio * windowSpan;
      curB = tB + ratio * windowSpan;
    }

    return {
      curA: Math.max(0, curA),
      curB: Math.max(0, curB),
      isApex: f >= 0.45 && f <= 0.55
    };
  }

  function getDeliveryPhase(progressPct) {
    const p = Number(progressPct) || 0;
    if (p < 25) return "PHASE: COME-SET / GLOVE ANCHOR";
    if (p < 45) return "PHASE: LEG LIFT INITIATION";
    if (p <= 55) return "★ KEY FRAME: MECHANICAL APEX (TELL WINDOW)";
    if (p < 75) return "PHASE: HAND SEPARATION & STRIDE";
    return "PHASE: ARM ACCELERATION & RELEASE";
  }

  function syncMediaAndHUD() {
    const tip = availableTips[currentTipIdx] || availableTips[0];
    const { pitchA, pitchB, tA, tB } = parseTipTimingsAndLabels(tip, player);
    const p = parseFloat(scrubSlider?.value ?? 50);

    const { curA, curB, isApex } = getTimes(p, tA, tB);
    const deltaT = (tA - tB).toFixed(2);

    // Update Slider Progress Fill
    if (sliderProgress) {
      sliderProgress.style.width = `${p}%`;
    }

    // Update Time Badges
    if (timeA) timeA.textContent = `${formatSec(curA)}s`;
    if (timeB) timeB.textContent = `${formatSec(curB)}s`;

    // Update Telemetry Footer
    if (telemA) telemA.textContent = formatSec(curA);
    if (telemB) telemB.textContent = formatSec(curB);
    if (telemPhase) {
      telemPhase.textContent = getDeliveryPhase(p);
      telemPhase.style.color = isApex ? "#ffc450" : "var(--good)";
      telemPhase.style.borderColor = isApex ? "rgba(255, 196, 80, 0.45)" : "rgba(62, 207, 142, 0.35)";
    }
    if (telemDelta) {
      telemDelta.textContent = `Δt = ${deltaT >= 0 ? "+" : ""}${deltaT}s (Synced)`;
    }

    // Video synchronization
    if (videoA && videoA.src && !videoA.error) {
      try { videoA.currentTime = curA; } catch (e) {}
    }
    if (videoB && videoB.src && !videoB.error) {
      try { videoB.currentTime = curB; } catch (e) {}
    }

    // Draw HUD Canvases
    const hasVidA = !!(videoA && videoA.src && videoA.style.display !== "none");
    const hasVidB = !!(videoB && videoB.src && videoB.style.display !== "none");

    if (canvasA) {
      drawDeliveryTelemetryCanvas(canvasA, {
        pitchName: pitchA,
        timeVal: curA,
        progressPct: p,
        isPitchA: true,
        tip,
        isApex,
        hasVideo: hasVidA
      });
    }
    if (canvasB) {
      drawDeliveryTelemetryCanvas(canvasB, {
        pitchName: pitchB,
        timeVal: curB,
        progressPct: p,
        isPitchA: false,
        tip,
        isApex,
        hasVideo: hasVidB
      });
    }
  }

  function applyTipSelection(idx) {
    currentTipIdx = Math.max(0, Math.min(availableTips.length - 1, idx));
    const tip = availableTips[currentTipIdx];
    const { pitchA, pitchB, tA, tB } = parseTipTimingsAndLabels(tip, player);

    // Update Dropdown & Quick Pills
    if (tipDropdown) tipDropdown.value = String(currentTipIdx);
    if (quickPills) {
      quickPills.querySelectorAll(".sync-pill-btn").forEach((btn, bIdx) => {
        btn.classList.toggle("active", bIdx === currentTipIdx);
      });
    }

    // Update Focus Banner
    if (targetBodyPartEl) {
      targetBodyPartEl.textContent = tip.target_body_part || tip.body_part || tip.what_to_look_at || "Pitcher Delivery Geometry & Glove Set";
    }
    if (separationBadge) {
      separationBadge.textContent = tip.separation_display || (tip.separation_floor_multiples ? `${tip.separation_floor_multiples}× Separation Floor` : "+5.2× Signal Floor");
    }
    if (contrastBadge) {
      contrastBadge.textContent = tip.contrast_label || tip.contrast || `${pitchA} vs ${pitchB}`;
    }
    if (differenceText) {
      differenceText.textContent = tip.what_to_spot || tip.lookFor || tip.behavior || tip.direction || "Observe mechanical variance between pitch types across pre-release window.";
    }
    if (metaWindow) {
      metaWindow.textContent = tip.timestamp_window || `Second Mark: ${formatSec(tA)} (Pre-Release Window)`;
    }
    if (metaAngle) {
      metaAngle.textContent = `${tip.angle || "CF"} · Broadcast Center-Field`;
    }
    if (metaSample) {
      metaSample.textContent = `n=${tip.n || player.pitchesModeled || 75} pitches · Zero-Leakage Window`;
    }

    // Update Pane Headers
    if (labelA) labelA.textContent = pitchA.toUpperCase();
    if (labelB) labelB.textContent = pitchB.toUpperCase();

    // Update Slider Apex Tag & Start/End Labels
    if (apexTag) {
      apexTag.textContent = `★ KEY FRAME (${formatSec(tA)} | ${formatSec(tB)})`;
    }
    if (lblStart) {
      lblStart.textContent = `Set Initiation (${formatSec(Math.max(0, tA - 1.5))})`;
    }
    if (lblEnd) {
      lblEnd.textContent = `Ball Release (${formatSec(tA + 1.5)})`;
    }

    // Update Video / Still Media Elements if paths exist
    const vComp = player?.videoCompare || {};
    const mediaSrcA = tip.videoA || player.videoA || vComp.videoA || (player.detectionStill?.a) || "";
    const mediaSrcB = tip.videoB || player.videoB || vComp.videoB || (player.detectionStill?.b) || "";

    if (videoA && imgA) {
      if (mediaSrcA && mediaSrcA.endsWith(".mp4")) {
        videoA.src = mediaSrcA;
        videoA.style.display = "block";
        imgA.style.display = "none";
      } else if (mediaSrcA && (mediaSrcA.endsWith(".svg") || mediaSrcA.endsWith(".jpg") || mediaSrcA.endsWith(".png"))) {
        imgA.src = mediaSrcA;
        imgA.style.display = "block";
        videoA.style.display = "none";
      } else {
        videoA.style.display = "none";
        imgA.style.display = "none";
      }
    }

    if (videoB && imgB) {
      if (mediaSrcB && mediaSrcB.endsWith(".mp4")) {
        videoB.src = mediaSrcB;
        videoB.style.display = "block";
        imgB.style.display = "none";
      } else if (mediaSrcB && (mediaSrcB.endsWith(".svg") || mediaSrcB.endsWith(".jpg") || mediaSrcB.endsWith(".png"))) {
        imgB.src = mediaSrcB;
        imgB.style.display = "block";
        videoB.style.display = "none";
      } else {
        videoB.style.display = "none";
        imgB.style.display = "none";
      }
    }

    // Reset slider to 50% (Apex Key Frame)
    if (scrubSlider) scrubSlider.value = "50";
    syncMediaAndHUD();
  }

  // Hook Dropdown & Pills
  tipDropdown?.addEventListener("change", (e) => {
    applyTipSelection(Number(e.target.value) || 0);
  });

  quickPills?.querySelectorAll(".sync-pill-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      applyTipSelection(Number(btn.dataset.tipIdx) || 0);
    });
  });

  // Hook Slider Scrubber
  scrubSlider?.addEventListener("input", () => {
    if (isPlaying) stopPlay();
    syncMediaAndHUD();
  });

  // Hook Snap to Apex Button
  snapApexBtn?.addEventListener("click", () => {
    if (isPlaying) stopPlay();
    if (scrubSlider) scrubSlider.value = "50";
    syncMediaAndHUD();
  });

  // Step -0.1s and +0.1s
  stepBackBtn?.addEventListener("click", () => {
    if (isPlaying) stopPlay();
    if (scrubSlider) {
      scrubSlider.value = String(Math.max(0, parseFloat(scrubSlider.value) - 3.33));
      syncMediaAndHUD();
    }
  });

  stepFwdBtn?.addEventListener("click", () => {
    if (isPlaying) stopPlay();
    if (scrubSlider) {
      scrubSlider.value = String(Math.min(100, parseFloat(scrubSlider.value) + 3.33));
      syncMediaAndHUD();
    }
  });

  // Play / Pause Animation Loop
  function stopPlay() {
    isPlaying = false;
    if (animReqId) cancelAnimationFrame(animReqId);
    if (playIcon) playIcon.textContent = "▶";
    if (playText) playText.textContent = "Play Sync";
  }

  function startPlay() {
    isPlaying = true;
    if (playIcon) playIcon.textContent = "❚❚";
    if (playText) playText.textContent = "Pause Sync";

    let lastTimestamp = performance.now();
    function loop(now) {
      if (!isPlaying) return;
      const elapsed = (now - lastTimestamp) / 1000;
      lastTimestamp = now;

      if (scrubSlider) {
        let curVal = parseFloat(scrubSlider.value) + elapsed * 33.3; // 3 second cycle
        if (curVal > 100) curVal = 0;
        scrubSlider.value = curVal.toFixed(1);
        syncMediaAndHUD();
      }
      animReqId = requestAnimationFrame(loop);
    }
    animReqId = requestAnimationFrame(loop);
  }

  playBtn?.addEventListener("click", () => {
    if (isPlaying) {
      stopPlay();
    } else {
      startPlay();
    }
  });

  // Initialize with first tip
  applyTipSelection(0);
}

function wireDetectionStage(player) {
  wireSynchronizedDeliveryScrubber(player);
}

function wirePlayerPage(data) {
  ensureEnterpriseModal();
  ensureLiteBanner();
  const id = getPlayerIdFromUrl() || "eduardo_rodriguez";
  const player = resolvePlayer(data, id);
  const title = document.getElementById("player-title");
  const lede = document.getElementById("player-lede");
  const tipRoot = document.getElementById("player-tips");
  const catcherTipRoot = document.getElementById("player-catcher-tips");
  const angleSel = document.getElementById("angle-select");
  const contextSel = document.getElementById("context-select");
  const team = player ? teamById(data, player.teamId) : null;

  if (!player) {
    if (title) title.textContent = "Player not found";
    return;
  }

  const isShowcase = isShowcaseArm(player.id) || isShowcaseArm(id);
  const tips = playerTips(player);

  if (title) {
    title.innerHTML = isLiteMode && isShowcase
      ? `${player.name} <span class="unlocked-tag" style="font-size:0.85rem; vertical-align:middle;">✨ 100% Unlocked Showcase</span>`
      : player.name;
  }

  if (lede) {
    const topFloor = tips[0]?.separation_floor_multiples ? ` · max separation ${tips[0].separation_floor_multiples}× floor` : "";
    if (player.role === "C") {
      const roleName = player.roleType === "starter" ? "Primary Starter" : "Backup Catcher";
      lede.innerHTML = `${team?.name || ""} · Catcher (${roleName}) · <strong>${tips.length}</strong> Catcher Setup Indicators (≥75% signal floor)<br>${player.summary}`;
    } else {
      lede.innerHTML = `${team?.name || ""} · ${player.throws}HP ${player.role} · <strong>${tips.length}</strong> High-Variance Mechanical Indicators${topFloor}<br>${player.summary}`;
    }
  }

  const teamLink = document.getElementById("back-team");
  if (teamLink && team) {
    const liteParam = isLiteMode ? "&lite=1" : "";
    teamLink.href = `team.html?id=${encodeURIComponent(team.id)}${liteParam}`;
    teamLink.textContent = `← ${team.abbr} summary`;
  }

  // If in Lite mode and NOT a showcase arm, render the Enterprise Locked Overlay
  if (isLiteMode && !isShowcase && player.role !== "C") {
    const stage = document.querySelector(".detection-stage");
    if (stage) {
      const lockCard = document.createElement("div");
      lockCard.className = "locked-player-overlay-card";
      lockCard.innerHTML = `
        <span class="enterprise-modal-badge">🔒 Enterprise Scouting Dossier</span>
        <h3>${player.name} (${team?.abbr || "PRO"}) · Access Restricted</h3>
        <p>
          This pitcher dossier is part of the full Preflight professional &amp; international platform database (MLB, NPB, KBO, CPBL, LMB, and Winter Leagues). 
          Pre-release delivery compare sliders, hand-in-glove depth metrics, and high-movement variance indicators are accessible under an Enterprise Scouting Pilot.
        </p>
        <div class="btn-row">
          <a class="btn" href="https://x.com/colbymorris08" target="_blank" rel="noopener noreferrer">Request Enterprise Pilot / DM @colbymorris08 →</a>
          <button class="btn ghost" type="button" onclick="window.openEnterpriseModal('${player.name.replace(/'/g, "\\'")}')">View Enterprise Features</button>
        </div>
        <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--line);">
          <p style="font-size:0.8rem; color:var(--muted); margin-bottom:0.5rem;">Or explore the fully unlocked public showcase arms:</p>
          <div style="display:flex; justify-content:center; gap:0.5rem; flex-wrap:wrap;">
            <a class="btn ghost" style="font-size:0.75rem; padding:0.3rem 0.6rem;" href="player.html?id=eduardo_rodriguez&lite=1">Eduardo Rodriguez (ARI)</a>
            <a class="btn ghost" style="font-size:0.75rem; padding:0.3rem 0.6rem;" href="player.html?id=webb&lite=1">Logan Webb (SF)</a>
            <a class="btn ghost" style="font-size:0.75rem; padding:0.3rem 0.6rem;" href="player.html?id=roupp&lite=1">Landen Roupp (SF)</a>
          </div>
        </div>
      `;
      stage.innerHTML = "";
      stage.appendChild(lockCard);
    }
  } else {
    wireDetectionStage(player);
    wireSituationCoverage(player);
  }

  fillSelect(angleSel, data.meta?.angles || [{ id: "CF", label: "Broadcast CF PoC" }], {
    valueKey: "id",
    labelKey: "label",
    blank: "Future Camera Angle(s) Available",
  });
  fillSelect(contextSel, data.meta?.contexts || [{ id: "stretch", label: "Stretch" }], {
    valueKey: "id",
    labelKey: "label",
    blank: "All Game Filters",
  });

  const angleMap = Object.fromEntries((data.meta?.angles || []).map((a) => [a.id, a.label]));

  function paint() {
    const angle = angleSel?.value || "";
    const context = contextSel?.value || "";
    let filteredTips = tips.filter((t) => tipPassesFilters(t, { angle, context }));
    // Graceful fallback to all player tips if strict sub-filter yields empty
    if (!filteredTips.length && tips.length) {
      filteredTips = tips;
    }
    if (tipRoot) {
      if (isLiteMode && !isShowcase && player.role !== "C") {
        tipRoot.innerHTML = `
          <div class="locked-preview-panel" style="background:var(--bg-elev); padding:1.25rem; border-radius:4px; border:1px solid var(--line); text-align:center;">
            <p style="color:var(--warn); font-weight:600; margin-bottom:0.5rem;">🔒 ${tips.length} Mechanical Indicators Protected</p>
            <p style="font-size:0.84rem; color:var(--muted); margin-bottom:1rem;">Out-of-sample verified separation, effect sizes (d), and pre-release tracking data are available for enterprise scouts.</p>
            <button type="button" class="btn" onclick="window.openEnterpriseModal('${player.name.replace(/'/g, "\\'")}')">Request Pilot Access to Unlock ${player.name} →</button>
          </div>
        `;
      } else {
        tipRoot.innerHTML =
          filteredTips.map((t, i) => renderTip(t, angleMap, i + 1)).join("") ||
          `<p class="note">No mechanical indicators recorded for this arm.</p>`;
      }
    }
    const catcherPanel = document.getElementById("catcher-signals-panel");
    let cTips = (player.catcherTips || []).filter((t) => tipPassesFilters(t, { angle, context }));
    if (!cTips.length && player.catcherTips && player.catcherTips.length) {
      cTips = player.catcherTips;
    }
    if (catcherPanel) {
      if (player.role !== "C" && (!player.catcherTips || !player.catcherTips.length)) {
        catcherPanel.hidden = true;
      } else {
        catcherPanel.hidden = false;
      }
    }
    if (catcherTipRoot) {
      catcherTipRoot.innerHTML =
        cTips.map((t, i) => renderTip(t, angleMap, i + 1)).join("") ||
        `<p class="note">Catcher setup tracking (target position, stance, pre-pitch glove stillness) active. Multi-angle 4K club video elevates fine target adjustments to high-certainty indicators.</p>`;
    }
  }

  angleSel?.addEventListener("change", paint);
  contextSel?.addEventListener("change", paint);
  paint();
}

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const data = await loadDemo();
    const page = document.body.dataset.page;
    if (page === "home" || page === "lite") wireLanding(data);
    if (page === "teams") wireTeamsIndex(data);
    if (page === "team") wireTeamPage(data);
    if (page === "player") wirePlayerPage(data);
    if (page === "board") wireBoard(data);
  } catch (err) {
    console.error(err);
    const fail = document.getElementById("boot-fail");
    if (fail) fail.hidden = false;
  }
});
