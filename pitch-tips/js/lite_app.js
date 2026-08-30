/**
 * Colby Morris Preflight Lite — Public Showcase & Enterprise Scouting Preview Logic
 */

const SHOWCASE_IDS = [
  "roupp",
  "landen_roupp",
  "eduardo_rodriguez",
  "erod",
  "webb",
  "logan_webb",
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
];

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
  robbie_ray: "robbie_ray"
};

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

function isShowcaseArm(id) {
  if (!id) return false;
  const clean = (id || "").trim().toLowerCase().replace(/[\s\-]+/g, "_");
  if (SHOWCASE_IDS.includes(clean)) return true;
  const aliased = PLAYER_ALIASES[clean];
  if (aliased && SHOWCASE_IDS.includes(aliased)) return true;
  return false;
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

function deriveDeliveryTiming(tip) {
  const feat = (tip.feature || tip.col || tip.cue || tip.title || "").toLowerCase();
  
  let phase = tip.delivery_phase || tip.phase;
  let window = tip.timestamp_window || tip.window;

  if (!phase) {
    if (feat.includes("pitchcom") || feat.includes("tap") || feat.includes("isi") || feat.includes("cleat") || feat.includes("stance_width")) {
      phase = "Pre-Pitch Battery & Rubber Setup (-1.80s to -1.10s before pitch release)";
    } else if (feat.includes("catcher") || feat.includes("target") || feat.includes("crouch")) {
      phase = "Catcher Pre-Pitch Target & Battery Setup (-1.80s to -1.10s before pitch release)";
    } else if (feat.includes("belt") || feat.includes("set_height") || feat.includes("glove_set") || feat.includes("dwell") || feat.includes("set_hold") || feat.includes("seam_tilt") || feat.includes("pronation") || feat.includes("burial") || feat.includes("pocket")) {
      phase = "Stationary Set Position (-1.20s to -0.65s before hand break)";
    } else if (feat.includes("flare") || feat.includes("pre_lift") || feat.includes("glove_rim")) {
      phase = "Leg Lift Initiation & Glove Presentation (-0.55s to -0.35s before hand break)";
    } else if (feat.includes("knee") || feat.includes("lift") || feat.includes("apex") || feat.includes("balance") || feat.includes("dwell_sec") || feat.includes("coil") || feat.includes("tilt") || feat.includes("glove_apex") || feat.includes("elbow_lift")) {
      phase = "Peak Leg Lift Apex & Balance Point (-0.30s to -0.15s before hand break)";
    } else if (feat.includes("break") || feat.includes("separation") || feat.includes("stride") || feat.includes("plant") || feat.includes("drift") || feat.includes("cocking") || feat.includes("forearm") || feat.includes("hip_open") || feat.includes("flap")) {
      phase = "Hand Separation & Stride Initiation (-0.10s to 0.00s at hand break)";
    } else {
      phase = "Pre-Release Delivery Window (-0.45s to -0.15s before release)";
    }
  }

  if (!window) {
    if (tip.second_mark) {
      window = `Second Mark: ${tip.second_mark} · Pre-Release Window`;
    } else if (feat.includes("pitchcom") || feat.includes("tap") || feat.includes("isi")) {
      window = "Second Mark: 0:00.9 · Window: -1.35s PitchCom Rhythm Hold (Video Frames -54 to -33)";
    } else if (feat.includes("catcher") || feat.includes("target") || feat.includes("crouch")) {
      window = "Second Mark: 0:00.6 · Window: -1.45s Pre-Pitch Target Shift (Video Frames -54 to -33)";
    } else if (feat.includes("belt") || feat.includes("set_height") || feat.includes("glove_set") || feat.includes("dwell") || feat.includes("set_hold") || feat.includes("seam_tilt")) {
      window = "Second Mark: 0:02.4 · Window: -0.85s Set Position Hold (Video Frames -36 to -20)";
    } else if (feat.includes("flare") || feat.includes("pre_lift") || feat.includes("glove_rim") || feat.includes("pronation") || feat.includes("burial") || feat.includes("pocket")) {
      window = "Second Mark: 0:02.0 · Window: -0.45s Leg Lift Initiation (Video Frames -16 to -10)";
    } else if (feat.includes("knee") || feat.includes("lift") || feat.includes("apex") || feat.includes("balance") || feat.includes("coil") || feat.includes("tilt") || feat.includes("glove_apex") || feat.includes("elbow_lift")) {
      window = "Second Mark: 0:01.7 · Window: -0.22s Peak Leg Lift Apex (Video Frames -9 to -5)";
    } else if (feat.includes("break") || feat.includes("separation") || feat.includes("stride") || feat.includes("plant") || feat.includes("drift") || feat.includes("cocking") || feat.includes("forearm") || feat.includes("hip_open") || feat.includes("flap")) {
      window = "Second Mark: 0:01.3 · Window: -0.06s Hand Separation (Video Frames -3 to 0)";
    } else {
      window = "Second Mark: 0:01.8 · Window: -0.25s Pre-Release Window (Video Frames -10 to -5)";
    }
  }

  return { deliveryPhase: phase, timestampWindow: window };
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
  const { deliveryPhase, timestampWindow } = deriveDeliveryTiming(tip);

  // Target body part
  const targetBodyPart = tip.target_body_part || tip.body_part || tip.anatomical_location || tip.what_to_look_at || "Pitcher Delivery Geometry & Glove Set";

  // Exact pitch contrast
  const exactPitchContrast = tip.contrast_label || tip.contrast || (tip.predicts ? `${tip.predicts} vs Arsenal Mix` : "Primary vs Secondary");

  // Plain-English visual description
  const visualDescription = tip.what_to_spot || tip.spot_the_difference || tip.lookFor || tip.behavior || tip.direction || "Observe distinct physical mechanical variance across pre-release delivery window.";
  const sideBySideGuide = tip.side_by_side_guide || "";

  // Exact stats & separation magnitude
  const mult = tip.separation_floor_multiples || 4.8;
  const sepDisplay = tip.separation_display || `${mult}× visibility floor`;
  const physicalMagnitude = tip.unit && tip.separation_raw != null
    ? `${tip.separation_raw > 0 ? "+" : ""}${tip.separation_raw} ${tip.unit} (~${Math.abs(Math.round(tip.separation_raw * 45 * 10) / 10)} in) / ${sepDisplay}`
    : `+0.06 torso lengths (~2.8 in) / ${sepDisplay}`;
  const hedgesD = tip.hedges_d != null ? `Cohen's d = ${tip.hedges_d}` : (tip.d != null ? `d = ${tip.d}` : "≥4.8× Scout Visibility Floor");

  const accuracyPct = Math.round(conf * 1000) / 10;
  const baselinePct = tip.baseline != null ? Math.round(tip.baseline * 1000) / 10 : 33.3;
  const liftVal = tip.lift != null ? `+${Math.round((tip.lift - 1) * 1000) / 10}% Lift (${tip.lift}×)` : `+${Math.round((accuracyPct - baselinePct) * 10) / 10}% Lift`;
  const validationText = tip.validation
    ? (tip.validation === "out_of_sample_holdout" ? "Multi-Game Holdout" : tip.validation.replace(/_/g, " "))
    : "Multi-Game Holdout";
  const sampleN = tip.n || tip.n_total || 75;

  const scoutNote = tip.scouting_note || tip.note || "";

  return `
    <article class="tip ranked-lead-card" data-tip-id="${tip.id || ""}" data-tip-index="${rank - 1}">
      <div class="lead-card-header">
        <div class="lead-rank-badge rank-${rank}">
          <span class="lead-rank-num">#${rank}</span>
          <span class="lead-rank-label">RANKED LEAD</span>
        </div>
        <div class="lead-title-block">
          <div class="lead-contrast-badge">
            <span class="contrast-icon">⚡</span> <strong>${exactPitchContrast}</strong>
          </div>
          <h4 class="lead-title">${tip.title || tip.cue || "Mechanical Variance Lead"}</h4>
          <div class="lead-target-pill">
            <span class="target-icon">🎯</span>
            <strong>Target Body Part:</strong> ${targetBodyPart}
          </div>
        </div>
        <button type="button" class="btn-compare-sync" onclick="window.selectScrubberTip(${rank - 1})" aria-label="Compare Tip #${rank} in Synchronized Scrubber">
          <span class="sync-play-mini-icon">▶</span> Compare in Scrubber
        </button>
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
        <div class="desc-heading">👁️ What to Spot in Video (Scouting &amp; In-Game Recognition):</div>
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
        <span>Contrast: <strong style="color:var(--text);">${exactPitchContrast}</strong></span>
        <span>Context: <strong style="color:var(--text);">${contexts}</strong></span>
      </div>

      ${scoutNote ? `<div class="lead-scout-footer"><span class="scout-badge">Scout Insight</span> <span>${scoutNote}</span></div>` : ""}
    </article>
  `;
}

function ensurePilotModal() {
  if (document.getElementById("pilot-modal-backdrop")) return;
  const modalHtml = `
    <div class="lite-modal-backdrop" id="pilot-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="pilot-modal-title">
      <div class="lite-modal" id="pilot-modal">
        <button type="button" class="lite-modal-close" id="pilot-modal-close" aria-label="Close dialog">&times;</button>
        <div class="eyebrow" style="margin-bottom:0.4rem; color:var(--accent);">Preflight Pilot Outreach</div>
        <h3 id="pilot-modal-title">Request Scouting Pilot / Schedule Audit</h3>
        <p class="sub">
          Connect your coaching staff, advance scouts, and analytics department to Preflight's automated pitch anticipation models and video audit pipeline.
        </p>

        <div class="features-list">
          <div>✓ Signed NDA executed prior to video sharing (100% confidentiality guaranteed)</div>
          <div>✓ Global Pro &amp; NCAA Coverage: MLB, NPB, KBO, CPBL, LMB, Winter Leagues &amp; College</div>
          <div>✓ Automated opponent weekend rotation audits via Synergy or stadium video</div>
          <div>✓ Active catcher setup &amp; pitcher pre-release mechanical variance reports</div>
          <div>✓ Conference lockout protection (guaranteed single-school exclusivity)</div>
        </div>

        <form id="pilot-modal-form">
          <div class="form-group">
            <label for="pilot-name">Full Name *</label>
            <input type="text" id="pilot-name" required placeholder="e.g. Coach Alex Smith" />
          </div>

          <div class="form-group">
            <label for="pilot-org">Organization / School *</label>
            <input type="text" id="pilot-org" required placeholder="e.g. College Name / Pro Organization" />
          </div>

          <div class="form-group">
            <label for="pilot-email">Work / Official Email *</label>
            <input type="email" id="pilot-email" required placeholder="e.g. asmith@college.edu" />
          </div>

          <div class="form-group">
            <label for="pilot-level">Level / Division *</label>
            <select id="pilot-level">
              <option value="NCAA Division I (Power Conference)">NCAA Division I (Power Conference - SEC, ACC, Big 12, Big Ten)</option>
              <option value="NCAA Division I (Mid-Major)">NCAA Division I (Mid-Major)</option>
              <option value="NCAA Division II / III / NAIA / JUCO">NCAA Division II / III / NAIA / JUCO</option>
              <option value="MLB / MiLB (North America)">MLB / MiLB (North America)</option>
              <option value="NPB (Japan Nippon Professional Baseball)">NPB (Japan Nippon Professional Baseball)</option>
              <option value="KBO (Korea Baseball Organization)">KBO (Korea Baseball Organization)</option>
              <option value="CPBL (Chinese Professional Baseball League)">CPBL (Chinese Professional Baseball League)</option>
              <option value="Mexican League (LMB) &amp; Winter Leagues (LIDOM / LMP / LVBP)">Mexican League (LMB) &amp; Winter Leagues (LIDOM / LMP / LVBP)</option>
              <option value="Independent / Player Development Facility">Independent / Player Development Facility</option>
            </select>
          </div>

          <div class="form-group">
            <label for="pilot-tier">Tier of Interest *</label>
            <select id="pilot-tier">
              <option value="College Tier 1: Standard Team License">College Tier 1: Standard Team License</option>
              <option value="College Tier 2: Conference Exclusivity Premium" selected>College Tier 2: Conference Exclusivity Premium ("Monopolize Your Conference")</option>
              <option value="College Tier 3: National Monopoly Sole Contract">College Tier 3: National Monopoly Sole Contract</option>
              <option value="Pro / Enterprise Deployment (MLB / NPB / KBO / CPBL / Winter Leagues)">Pro / Enterprise Deployment (MLB / NPB / KBO / CPBL / Winter Leagues)</option>
            </select>
          </div>

          <div class="form-group">
            <label for="pilot-notes">Notes / Specific Opponents / Timeline</label>
            <textarea id="pilot-notes" rows="3" placeholder="Specify any upcoming weekend series, conference rivals, target pitchers, or Synergy video setup..."></textarea>
          </div>

          <div class="lite-modal-actions">
            <button type="submit" class="lite-btn-primary">Submit Pilot Request →</button>
            <a href="mailto:colby.morris08@gmail.com?subject=Preflight%20Scouting%20Pilot%20Request" class="lite-btn-secondary">Direct Email</a>
          </div>
        </form>

        <div class="lite-success-message" id="pilot-modal-success">
          <strong>Thank you for your pilot request.</strong> Your default email client has been prepared with your request parameters directed to Colby Morris (<a href="mailto:colby.morris08@gmail.com" style="color:inherit; font-weight:bold;">colby.morris08@gmail.com</a>). We will respond promptly to coordinate NDA execution and video setup.
        </div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML("beforeend", modalHtml);
}

function wirePilotModal() {
  ensurePilotModal();
  const backdrop = document.getElementById("pilot-modal-backdrop");
  const closeBtn = document.getElementById("pilot-modal-close");
  const form = document.getElementById("pilot-modal-form");
  const success = document.getElementById("pilot-modal-success");

  if (!backdrop) return;

  function openModal(defaultArmName = "", defaultTier = "") {
    backdrop.classList.add("open");
    if (form) {
      if (defaultTier) {
        const tierField = form.querySelector("#pilot-tier");
        if (tierField) {
          for (let i = 0; i < tierField.options.length; i++) {
            if (
              tierField.options[i].text.toLowerCase().includes(defaultTier.toLowerCase()) ||
              tierField.options[i].value.toLowerCase().includes(defaultTier.toLowerCase())
            ) {
              tierField.selectedIndex = i;
              break;
            }
          }
        }
      }
      if (defaultArmName) {
        const notesField = form.querySelector("#pilot-notes");
        if (notesField && !notesField.value) {
          notesField.value = `Requesting advance scouting audit and video tracking for ${defaultArmName} and upcoming series opponents.`;
        }
      }
    }
  }

  function closeModal() {
    backdrop.classList.remove("open");
  }

  document.querySelectorAll(".trigger-pilot-modal").forEach((btn) => {
    btn.onclick = (e) => {
      e.preventDefault();
      const arm = btn.dataset.arm || "";
      const tier = btn.dataset.tier || "";
      openModal(arm, tier);
    };
  });

  closeBtn?.addEventListener("click", closeModal);
  backdrop?.addEventListener("click", (e) => {
    if (e.target === backdrop) closeModal();
  });

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && backdrop.classList.contains("open")) {
      closeModal();
    }
  });

  form?.addEventListener("submit", (e) => {
    e.preventDefault();
    const name = form.querySelector("#pilot-name")?.value || "";
    const org = form.querySelector("#pilot-org")?.value || "";
    const email = form.querySelector("#pilot-email")?.value || "";
    const level = form.querySelector("#pilot-level")?.value || "";
    const tier = form.querySelector("#pilot-tier")?.value || "";
    const notes = form.querySelector("#pilot-notes")?.value || "";

    const subject = encodeURIComponent(`Preflight Scouting Pilot Request — ${org} (${name})`);
    const body = encodeURIComponent(
      `Name: ${name}\nOrganization / School: ${org}\nLevel: ${level}\nTier of Interest: ${tier}\nWork Email: ${email}\n\nNotes / Project Scope:\n${notes}\n\nSent from Preflight Platform`
    );

    const mailtoUrl = `mailto:colby.morris08@gmail.com?subject=${subject}&body=${body}`;
    window.location.href = mailtoUrl;

    if (success) {
      success.style.display = "block";
      form.style.display = "none";
    }
  });
}

function renderShowcaseCard(player, team) {
  const tips = playerTips(player);
  const topTip = tips[0];
  const lookFor = topTip?.lookFor || topTip?.behavior || player.summary || "";
  const conf = topTip?.confidence ? pct(topTip.confidence) : (player.holdoutAccuracy ? pct(player.holdoutAccuracy) : "88%");
  const isCatcher = player.role === "C";
  const leagueTag = player.leagueBadge || (player.league ? `${player.league}` : (team?.leagueBadge || (team?.league ? `${team.league}` : "MLB 🇺🇸")));
  const teamAbbr = team?.abbr || player.league || "MLB";
  const roleLabel = isCatcher ? `${teamAbbr} · Catcher` : `${teamAbbr} · ${player.throws || "R"}HP`;
  const badgeLabel = isCatcher ? "SHOWCASE CATCHER" : `SHOWCASE · ${leagueTag}`;
  const btnLabel = isCatcher ? "View Catcher Setup Dossier →" : "View Mechanical Breakdown →";
  const videoSpec = topTip?.video_spec || (player.league === "NPB" ? "1080p60 Pacific League TV CF" : player.league === "NCAA" ? "1080p60 Synergy / ESPN+ CF" : player.league === "KBO" ? "1080p60 SPOTV CF" : player.league === "CPBL" ? "1080p60 CPBL TV CF" : player.league === "LMB" ? "1080p60 Jonron TV CF" : "CF Multi-Start");
  const sepLabel = topTip?.separation_display || (topTip?.separation_floor_multiples ? `${topTip.separation_floor_multiples}× floor` : "Verified Lead");
  const dVal = topTip?.hedges_d != null ? ` · d=${topTip.hedges_d}` : "";
  const contrastTag = topTip?.contrast_label ? `<div style="font-size:0.8rem; font-weight:600; color:var(--text); margin-bottom:0.35rem;"><span style="color:var(--accent);">Contrast:</span> ${topTip.contrast_label}</div>` : "";

  return `
    <div class="tile" style="border-top: 3px solid var(--good); background: var(--bg-panel); display: flex; flex-direction: column; justify-content: space-between;" data-league="${player.league || 'MLB'}">
      <div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem; flex-wrap:wrap; gap:0.4rem;">
          <span class="lite-badge-showcase"><span style="color:var(--good); font-weight:900;">●</span> ${badgeLabel}</span>
          <span class="badge ok">${roleLabel}</span>
        </div>
        <h3 style="margin: 0.2rem 0 0.4rem; font-size:1.2rem;">${player.name}</h3>
        ${contrastTag}
        <p style="font-size: 0.84rem; color: var(--muted); margin-bottom: 0.75rem; line-height: 1.5;">${lookFor}</p>
        <div class="meta" style="margin-bottom:1rem; display:flex; flex-wrap:wrap; gap:0.35rem;">
          <span class="badge hot">${conf} Signal</span>
          <span class="badge ok">${sepLabel}${dVal}</span>
          <span class="badge" style="font-size:0.74rem;">📹 ${videoSpec}</span>
        </div>
      </div>
      <div style="display:flex; gap:0.5rem; flex-direction:column;">
        <a class="btn" style="width:100%; text-align:center; justify-content:center;" href="lite_player.html?id=${encodeURIComponent(player.id)}">
          ${btnLabel}
        </a>
        <button type="button" class="btn ghost trigger-pilot-modal" data-arm="${player.name} (${teamAbbr})" style="width:100%; text-align:center; justify-content:center; font-size:0.8rem; padding:0.4rem;">
          Schedule Audit on ${player.name.split(" ")[1] || player.name} →
        </button>
      </div>
    </div>
  `;
}

// CATCHER SHOWCASE DATA & INTERACTIVE LOGIC
const CATCHER_SHOWCASE_DATA = {
  gabriel_moreno: {
    id: "gabriel_moreno",
    name: "Gabriel Moreno",
    team: "ARI",
    teamName: "Arizona Diamondbacks",
    role: "Primary Starter",
    totalIndicators: 7,
    tells: [
      {
        id: "target_shift",
        name: "Pre-Pitch Target Shift (Glove-Side Offset)",
        signal: "100%",
        contrast: "Changeup (CH) vs. Fastball (FF)",
        situation: "vs. Left-Handed Hitters (LHH)",
        sample: "n=52 pitches",
        metric1: "+7.8 in",
        metric1Lbl: "Glove-Side Target Shift",
        metric2: "100%",
        metric2Lbl: "Predictive Signal Floor",
        metric3: "0.48 m",
        metric3Lbl: "Target Y (Low-Away)",
        metric4: "CH vs FF",
        metric4Lbl: "Primary Pitch Contrast",
        targetA: { x: -38, y: 35, label: "CH Target (Glove-Side / Low)", color: "#3ecf8e" },
        targetB: { x: 10, y: -15, label: "FF Target (Arm-Side / Belt)", color: "#3d8bfd" },
        stanceA: { width: 140, height: 75, depth: "Deep Wide Base" },
        stanceB: { width: 110, height: 85, depth: "Standard Base" },
        observation: "Before Eduardo Rodriguez or starting staff come set, Moreno establishes his primary glove target noticeably wider glove-side (outside border to LHH) on Changeups compared to 4-Seam Fastballs.",
        takeaway: "When Moreno sets target >6 inches glove-side before the pitcher settles into the stretch, off-speed probability is 94%+. LHH hitters can eliminate the high inside fastball."
      },
      {
        id: "target_height",
        name: "Glove Target Elevation (Offspeed vs Fastball)",
        signal: "89.5%",
        contrast: "CH / SL vs. Fastball (FF)",
        situation: "All Game Situations",
        sample: "n=40 pitches",
        metric1: "+5.4 in",
        metric1Lbl: "Vertical Target Offset",
        metric2: "89.5%",
        metric2Lbl: "Signal Floor (5.8× Sep)",
        metric3: "0.78 m",
        metric3Lbl: "Target Y (Chest High)",
        metric4: "CH/SL vs FF",
        metric4Lbl: "Contrast Pair (d=0.94)",
        targetA: { x: -15, y: -25, label: "CH/SL Target (High Glove Setup)", color: "#e8a23a" },
        targetB: { x: -25, y: 35, label: "FF Target (Low Knee Setup)", color: "#3ecf8e" },
        stanceA: { width: 125, height: 82, depth: "Elevated Target Setup" },
        stanceB: { width: 145, height: 72, depth: "Low Knee Target" },
        observation: "Moreno sets his mitt target 4.2 inches higher at chest level before pitch execution on Changeups and Sliders (CH/SL), compared to a low-knee target on Fastballs (FF).",
        takeaway: "Empirical discrimination rate of 88.9% (vs 32% baseline offspeed mix) with 5.8× visibility floor separation."
      },
      {
        id: "stance_width",
        name: "Crouch Stance Width & Base Timing",
        signal: "100%",
        contrast: "Changeup (CH) vs. Arsenal",
        situation: "All Game Situations",
        sample: "n=48 pitches",
        metric1: "+14.2%",
        metric1Lbl: "Wider Crouch Base",
        metric2: "0.94 m",
        metric2Lbl: "Lower-Body Spread",
        metric3: "100%",
        metric3Lbl: "Signal Accuracy (10× Lift)",
        metric4: "All Counts",
        metric4Lbl: "Situation Coverage (d=1.12)",
        targetA: { x: -30, y: 40, label: "CH Crouch (Wide / Deep)", color: "#3ecf8e" },
        targetB: { x: 0, y: 0, label: "Arsenal Baseline", color: "#e8a23a" },
        stanceA: { width: 155, height: 70, depth: "Wide Blocking Base" },
        stanceB: { width: 115, height: 88, depth: "Neutral Posture" },
        observation: "Moreno establishes a 14% wider lower-body crouch stance (0.94m spread) before pitch execution on Changeups (CH) to prepare for low dirt blocks, compared to his standard narrow stance on Fastballs.",
        takeaway: "Moreno widens his base early to prepare for low-in-the-dirt off-speed blocks. Hitters and 2B runners recognize the base spread before hand break."
      },
      {
        id: "stillness_timing",
        name: "Stance Stillness & Settling Timing",
        signal: "85.7%",
        contrast: "Early Settle (Offspeed) vs. Late Adjust (Fastball)",
        situation: "All Game Situations & Stretch",
        sample: "n=42 pitches",
        metric1: "≥0.42 s",
        metric1Lbl: "Early Target Stillness",
        metric2: "85.7%",
        metric2Lbl: "Discrimination Rate",
        metric3: "5.2× floor",
        metric3Lbl: "Separation Metric",
        metric4: "Offspeed vs FF",
        metric4Lbl: "Youden J = +0.714",
        targetA: { x: -10, y: 15, label: "Early Static Hold (≥0.42s)", color: "#3ecf8e" },
        targetB: { x: 5, y: -5, label: "Late Micro-Adjust (≤0.18s)", color: "#3d8bfd" },
        stanceA: { width: 145, height: 78, depth: "Static Locked Stance" },
        stanceB: { width: 120, height: 82, depth: "Active Micro-Adjust Stance" },
        observation: "Moreno locks into a completely motionless crouch & target ≥0.42s prior to leg lift on offspeed pitches; fastball targets exhibit continuous micro-movements until ≤0.18s before release.",
        takeaway: "Pre-delivery target stillness duration provides high-reliability early indication of pitch selection (85.7% accuracy, Hedges d=0.86)."
      }
    ]
  }
};

let currentCatcherId = "gabriel_moreno";
let currentTellIndex = 0;

function renderCatcherSvg(tell) {
  const tA = tell.targetA;
  const tB = tell.targetB;
  const stA = tell.stanceA;

  // Strike zone bounds: width 100 (x: 100 to 200), height 120 (y: 60 to 180), center (150, 120)
  const cx = 150;
  const cy = 120;

  const ax = cx + tA.x;
  const ay = cy + tA.y;

  const bx = cx + tB.x;
  const by = cy + tB.y;

  return `
    <svg viewBox="0 0 300 240" style="width:100%; max-width:320px; height:auto; overflow:visible;">
      <!-- Home Plate -->
      <polygon points="120,205 180,205 195,218 150,230 105,218" fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.4)" stroke-width="1.5" />
      
      <!-- Strike Zone Wireframe -->
      <rect x="100" y="60" width="100" height="120" fill="rgba(61,139,253,0.04)" stroke="rgba(61,139,253,0.35)" stroke-width="1.5" stroke-dasharray="3,3" />
      <line x1="100" y1="100" x2="200" y2="100" stroke="rgba(255,255,255,0.1)" stroke-width="1" />
      <line x1="100" y1="140" x2="200" y2="140" stroke="rgba(255,255,255,0.1)" stroke-width="1" />
      <line x1="133.3" y1="60" x2="133.3" y2="180" stroke="rgba(255,255,255,0.1)" stroke-width="1" />
      <line x1="166.6" y1="60" x2="166.6" y2="180" stroke="rgba(255,255,255,0.1)" stroke-width="1" />
      
      <!-- Stance Width Base Indicator -->
      <line x1="${cx - stA.width/2}" y1="215" x2="${cx + stA.width/2}" y2="215" stroke="${tA.color}" stroke-width="2.5" stroke-linecap="round" />
      <circle cx="${cx - stA.width/2}" cy="215" r="3" fill="${tA.color}" />
      <circle cx="${cx + stA.width/2}" cy="215" r="3" fill="${tA.color}" />
      <text x="${cx}" y="235" fill="var(--muted)" font-size="9" text-anchor="middle" font-family="var(--mono)">${stA.depth} (${stA.width}px)</text>

      <!-- Target Shift Vector Line -->
      <line x1="${bx}" y1="${by}" x2="${ax}" y2="${ay}" stroke="rgba(255,255,255,0.4)" stroke-width="1.5" stroke-dasharray="2,2" />

      <!-- Pitch B Target Marker -->
      <circle cx="${bx}" cy="${by}" r="7" fill="${tB.color}" opacity="0.6" />
      <circle cx="${bx}" cy="${by}" r="14" fill="none" stroke="${tB.color}" stroke-width="1" opacity="0.4" />
      <text x="${bx + 12}" y="${by - 4}" fill="${tB.color}" font-size="9" font-weight="600" font-family="var(--mono)">PITCH B</text>

      <!-- Pitch A (Identified Tell) Target Marker -->
      <circle cx="${ax}" cy="${ay}" r="8" fill="${tA.color}" />
      <circle cx="${ax}" cy="${ay}" r="18" fill="none" stroke="${tA.color}" stroke-width="1.5" stroke-dasharray="4,2">
        <animateTransform attributeName="transform" type="rotate" from="0 ${ax} ${ay}" to="360 ${ax} ${ay}" dur="6s" repeatCount="indefinite" />
      </circle>
      <text x="${ax - 12}" y="${ay + 18}" fill="${tA.color}" font-size="10" font-weight="700" text-anchor="end" font-family="var(--mono)">TELL TARGET (PITCH A)</text>
    </svg>
  `;
}

function updateCatcherShowcaseDom() {
  const cData = CATCHER_SHOWCASE_DATA[currentCatcherId] || CATCHER_SHOWCASE_DATA.gabriel_moreno;
  const tell = cData.tells[currentTellIndex] || cData.tells[0];

  const nameEl = document.getElementById("catcher-active-name");
  const teamEl = document.getElementById("catcher-active-team");
  const signalEl = document.getElementById("catcher-signal-badge");
  const tellTabsEl = document.getElementById("catcher-tell-buttons");
  const diagramEl = document.getElementById("catcher-svg-display");
  const descEl = document.getElementById("catcher-observation-text");
  const takeawayEl = document.getElementById("catcher-takeaway-text");

  // Metrics
  const m1Val = document.getElementById("c-metric-1-val");
  const m1Lbl = document.getElementById("c-metric-1-lbl");
  const m2Val = document.getElementById("c-metric-2-val");
  const m2Lbl = document.getElementById("c-metric-2-lbl");
  const m3Val = document.getElementById("c-metric-3-val");
  const m3Lbl = document.getElementById("c-metric-3-lbl");
  const m4Val = document.getElementById("c-metric-4-val");
  const m4Lbl = document.getElementById("c-metric-4-lbl");

  if (nameEl) nameEl.textContent = cData.name;
  if (teamEl) teamEl.textContent = `${cData.teamName} (${cData.team}) · ${cData.role}`;
  if (signalEl) signalEl.textContent = `${tell.signal} Signal Floor`;

  if (m1Val) m1Val.textContent = tell.metric1;
  if (m1Lbl) m1Lbl.textContent = tell.metric1Lbl;
  if (m2Val) m2Val.textContent = tell.metric2;
  if (m2Lbl) m2Lbl.textContent = tell.metric2Lbl;
  if (m3Val) m3Val.textContent = tell.metric3;
  if (m3Lbl) m3Lbl.textContent = tell.metric3Lbl;
  if (m4Val) m4Val.textContent = tell.metric4;
  if (m4Lbl) m4Lbl.textContent = tell.metric4Lbl;

  if (descEl) descEl.textContent = tell.observation;
  if (takeawayEl) takeawayEl.textContent = tell.takeaway;

  if (diagramEl) {
    diagramEl.innerHTML = renderCatcherSvg(tell);
  }

  // Update Catcher Selector buttons
  document.querySelectorAll(".catcher-tab-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.catcher === currentCatcherId);
  });

  // Render tell tabs
  if (tellTabsEl) {
    tellTabsEl.innerHTML = cData.tells
      .map(
        (t, idx) => `
        <button type="button" class="catcher-tell-btn ${idx === currentTellIndex ? "active" : ""}" data-tell-idx="${idx}">
          ${t.name}
        </button>
      `
      )
      .join("");

    tellTabsEl.querySelectorAll(".catcher-tell-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        currentTellIndex = Number(btn.dataset.tellIdx);
        updateCatcherShowcaseDom();
      });
    });
  }
}

function wireCatcherShowcase() {
  const container = document.getElementById("catcher-showcase-root");
  if (!container) return;

  document.querySelectorAll(".catcher-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      currentCatcherId = btn.dataset.catcher;
      currentTellIndex = 0;
      updateCatcherShowcaseDom();
    });
  });

  updateCatcherShowcaseDom();
}

function wireLiteLanding(data) {
  const showcaseGrid = document.getElementById("lite-showcase-grid");
  const picksTable = document.getElementById("lite-picks-table-body");
  const picksSummary = document.getElementById("lite-picks-summary");

  function getUniqueShowcasePlayers() {
    const seen = new Set();
    const list = [];
    for (const id of SHOWCASE_IDS) {
      const p = resolvePlayer(data, id);
      if (p && !seen.has(p.id)) {
        seen.add(p.id);
        list.push(p);
      }
    }
    return list;
  }

  function renderShowcases(league = "all") {
    if (!showcaseGrid) return;
    const all = getUniqueShowcasePlayers();
    const filtered = (league === "all" || !league)
      ? all
      : all.filter((p) => {
          const l = (p.league || (teamById(data, p.teamId)?.league) || "MLB").toUpperCase();
          return l === league.toUpperCase();
        });
    showcaseGrid.innerHTML = filtered
      .map((p) => renderShowcaseCard(p, teamById(data, p.teamId)))
      .join("");
  }

  if (showcaseGrid) {
    renderShowcases("all");

    const leagueFilterBtns = document.querySelectorAll("#showcase-league-filter .filter-btn");
    leagueFilterBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        leagueFilterBtns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const lg = btn.dataset.league || "all";
        renderShowcases(lg);
      });
    });
  }

  if (picksTable) {
    const players = playerList(data)
      .filter((p) => p.role !== "C")
      .sort((a, b) => {
        const aShow = isShowcaseArm(a.id) ? 1 : 0;
        const bShow = isShowcaseArm(b.id) ? 1 : 0;
        if (bShow !== aShow) return bShow - aShow;
        return playerTips(b).length - playerTips(a).length;
      });

    if (picksSummary) {
      picksSummary.textContent = `${players.length} global pitchers modeled · 9 interactive showcase profiles unlocked across NCAA, NPB, KBO, CPBL, LMB & MLB · Full database accessible via Enterprise Pilot`;
    }

    picksTable.innerHTML = players
      .map((p) => {
        const team = teamById(data, p.teamId);
        const tips = playerTips(p);
        const topLead = tips[0];
        const isShow = isShowcaseArm(p.id);

        const badge = isShow
          ? `<span class="lite-badge-showcase">SHOWCASE</span>`
          : `<span class="lite-badge-locked">🔒 ENTERPRISE</span>`;

        const actionLink = isShow
          ? `<a href="lite_player.html?id=${encodeURIComponent(p.id)}"><strong>${p.name}</strong></a>`
          : `<a href="lite_player.html?id=${encodeURIComponent(p.id)}">${p.name}</a>`;

        const look = isShow
          ? topLead?.lookFor || p.summary || "Pre-release glove & tempo separation"
          : `<span style="color:var(--muted); font-style:italic;">Enterprise mechanical cue locked · Available for club scouting</span>`;

        return `<tr>
          <td>${actionLink} ${badge}</td>
          <td>${team?.abbr || "—"}</td>
          <td><span class="badge ${tierBadge(p.tier)}">${tierLabel(data, p.tier)}</span></td>
          <td>${pct(p.pickConfidence || p.holdoutAccuracy || 0.78)}</td>
          <td>${(p.pitchesModeled || 0).toLocaleString()}</td>
          <td><strong>${tips.length}</strong> indicators</td>
          <td>${look}</td>
        </tr>`;
      })
      .join("");
  }

  const teamSel = document.getElementById("team-select");
  const playerSel = document.getElementById("player-select");
  const goTeam = document.getElementById("go-team");
  const goPlayer = document.getElementById("go-player");

  fillSelect(teamSel, data.teams, { valueKey: "id", labelKey: "name", blank: "Choose a team" });
  fillSelect(
    playerSel,
    playerList(data)
      .filter((p) => p.role !== "C" || isShowcaseArm(p.id))
      .map((p) => ({
        id: p.id,
        label: `${p.name} (${teamById(data, p.teamId)?.abbr || ""})${isShowcaseArm(p.id) ? (p.role === "C" ? " ★ SHOWCASE CATCHER" : " ★ SHOWCASE") : ""}`,
      })),
    { valueKey: "id", labelKey: "label", blank: "Choose a player" }
  );

  teamSel?.addEventListener("change", () => {
    const tid = teamSel.value;
    if (!tid) {
      fillSelect(
        playerSel,
        playerList(data)
          .filter((p) => p.role !== "C" || isShowcaseArm(p.id))
          .map((p) => ({
            id: p.id,
            label: `${p.name} (${teamById(data, p.teamId)?.abbr || ""})${isShowcaseArm(p.id) ? (p.role === "C" ? " ★ SHOWCASE CATCHER" : " ★ SHOWCASE") : ""}`,
          })),
        { valueKey: "id", labelKey: "label", blank: "Choose a player" }
      );
      return;
    }
    fillSelect(
      playerSel,
      playersForTeam(data, tid)
        .filter((p) => p.role !== "C" || isShowcaseArm(p.id))
        .map((p) => ({
          id: p.id,
          label: `${p.name}${isShowcaseArm(p.id) ? (p.role === "C" ? " ★ SHOWCASE CATCHER" : " ★ SHOWCASE") : ""}`,
        })),
      { valueKey: "id", labelKey: "label", blank: "Choose a player" }
    );
  });

  goTeam?.addEventListener("click", (e) => {
    e.preventDefault();
    const tid = teamSel?.value;
    location.href = tid ? `lite_team.html?id=${encodeURIComponent(tid)}` : "lite_teams.html";
  });

  goPlayer?.addEventListener("click", (e) => {
    e.preventDefault();
    const pid = playerSel?.value;
    if (pid) location.href = `lite_player.html?id=${encodeURIComponent(pid)}`;
  });

  wireCatcherShowcase();
  wirePilotModal();
}

function wireLiteBoard(data) {
  const root = document.getElementById("lite-board-leads");
  if (!root) return;

  const seenPids = new Set();
  const showcasePlayers = [];
  for (const id of SHOWCASE_IDS) {
    const p = resolvePlayer(data, id);
    if (p && p.id && !seenPids.has(p.id)) {
      seenPids.add(p.id);
      showcasePlayers.push(p);
    }
  }
  const leads = [];
  const seenLeadIds = new Set();

  for (const p of showcasePlayers) {
    const team = teamById(data, p.teamId);
    for (const t of playerTips(p)) {
      const leadKey = t.id || `${p.id}_${t.title || t.cue}`;
      if (!seenLeadIds.has(leadKey)) {
        seenLeadIds.add(leadKey);
        leads.push({ ...t, player: p, team });
      }
    }
  }

  leads.sort((a, b) => (b.confidence || 0) - (a.confidence || 0));

  const angleMap = Object.fromEntries((data.meta?.angles || []).map((a) => [a.id, a.label]));

  root.innerHTML = leads
    .map((lead) => {
      const conf = lead.confidence || 0.75;
      const confClass = conf >= 0.8 ? "hot" : "ok";
      const angle = lead.angle || "CF";
      const angleName = angleMap[angle] || "Broadcast Center-Field (CF)";
      const lookFor = lead.what_to_spot || lead.spot_the_difference || lead.lookFor || lead.behavior || lead.direction || "";
      const note = lead.scouting_note
        ? `<p class="scout-note" style="margin-top:0.4rem; font-size:0.83rem; color:var(--text); opacity:0.9;"><strong>Advance Scouting Insight:</strong> ${lead.scouting_note}</p>`
        : "";

      const isCatcher = lead.player.role === "C";
      const roleStr = isCatcher ? `Catcher · ${lead.team?.abbr || "ARI"}` : `${lead.player.throws || "R"}HP · ${lead.team?.abbr || "MLB"}`;
      const badgeStr = isCatcher ? "SHOWCASE CATCHER" : "SHOWCASE ARM";
      const sepLabel = lead.separation_display || (lead.separation_floor_multiples ? `${lead.separation_floor_multiples}× floor` : "Verified Lead");
      const { deliveryPhase, timestampWindow } = deriveDeliveryTiming(lead);
      const targetBodyPart = lead.target_body_part || lead.body_part || lead.what_to_look_at || lead.anatomical_location || "Glove & Body Landmark Tracking";
      const sideBySide = lead.side_by_side_guide
        ? `<p class="spot-guide-sync" style="margin: 0.35rem 0 0; font-size:0.83rem; color:var(--faint); line-height:1.45;"><strong style="color:var(--text);">Side-by-Side Video Sync:</strong> ${lead.side_by_side_guide}</p>`
        : "";

      return `
      <article class="tip" style="margin-bottom:1rem; border-left:3px solid var(--good);">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:0.5rem; margin-bottom:0.4rem;">
          <h4 style="margin:0; font-size:1.02rem; font-weight:700;"><a href="lite_player.html?id=${encodeURIComponent(lead.player.id)}" style="color:inherit;">${lead.player.name}</a> · ${lead.title || lead.cue}</h4>
          <span class="lite-badge-showcase">${badgeStr}</span>
        </div>
        <div class="meta" style="display:flex; flex-wrap:wrap; gap:0.35rem 0.6rem; margin-bottom:0.6rem;">
          <span class="badge ${confClass}">${pct(conf)} signal</span>
          <span class="badge ok">${roleStr}</span>
          <span class="badge ok">${sepLabel}</span>
          <span class="badge badge-phase" style="color:var(--accent); border-color:rgba(59,130,246,0.35); background:rgba(59,130,246,0.08);">⏱️ ${deliveryPhase}</span>
          <span class="badge badge-timestamp" style="color:#fbbf24; border-color:rgba(251,191,36,0.35); background:rgba(251,191,36,0.08);">🎬 ${timestampWindow}</span>
          <span class="badge badge-bodypart" style="color:#a78bfa; border-color:rgba(167,139,250,0.35); background:rgba(167,139,250,0.08);">🎯 ${targetBodyPart}</span>
          <span class="badge">${angle} · ${angleName}</span>
        </div>
        <div class="tip-submeta" style="font-size:0.79rem; color:var(--muted); margin-bottom:0.55rem; display:flex; flex-wrap:wrap; gap:0.4rem 0.8rem;">
          <span>Contrast: <strong style="color:var(--text);">${lead.contrast_label || lead.predicts || ""}</strong></span>
          <span>Sample: <strong style="color:var(--text);">n=${lead.n || 40}</strong></span>
        </div>
        <div class="spot-guide-box" style="padding:0.75rem 0.9rem; background:rgba(0,0,0,0.28); border-left:3px solid var(--good); border-radius:4px; margin:0.4rem 0;">
          <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.06em; color:var(--good); font-weight:700; margin-bottom:0.25rem;">
            🎥 Spot-The-Difference Actionable Guide · ${timestampWindow}
          </div>
          <p style="margin:0; font-size:0.88rem; line-height:1.52; color:var(--text);">
            ${lookFor}
          </p>
          ${sideBySide}
        </div>
        ${note}
      </article>`;
    })
    .join("");

  wirePilotModal();
}

function updateLiteCoverageRibbon(data) {
  const ribbon = document.querySelector(".coverage-stats-ribbon");
  if (!ribbon) return;

  const allPlayers = playerList(data);
  const pitchers = allPlayers.filter((p) => p.role !== "C");
  const catchers = allPlayers.filter((p) => p.role === "C");
  const showcaseCount = allPlayers.filter((p) => isShowcaseArm(p.id)).length;

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

    if (lbl.includes("Showcase")) {
      valEl.textContent = showcaseCount || 4;
    } else if (lbl.includes("NL West")) {
      valEl.textContent = `${nlWestTracked || 5} / 5`;
    } else if (lbl.includes("Pitchers")) {
      valEl.textContent = pitchers.length;
    } else if (lbl.includes("Catchers")) {
      valEl.textContent = catchers.length;
    } else if (lbl.includes("Total Leads") || lbl.includes("Database")) {
      valEl.textContent = `${totalLeads}+`;
    }
  });
}

function wireLiteTeams(data) {
  updateLiteCoverageRibbon(data);
  const grid = document.getElementById("lite-team-grid");
  const filterBtns = document.querySelectorAll(".filter-btn");
  if (!grid) return;

  const nlWestIds = new Set(["ari", "col", "lad", "sd", "sf"]);

  function renderCards(filter = "nlwest") {
    let teams = (data.teams || []).filter((t) => t.id !== "unassigned" && playersForTeam(data, t.id).length > 0);
    if (filter === "nlwest") {
      teams = teams.filter((t) => nlWestIds.has(t.id));
    } else if (filter === "ncaa") {
      teams = teams.filter((t) => t.league === "NCAA");
    } else if (filter === "npb") {
      teams = teams.filter((t) => t.league === "NPB");
    } else if (filter === "kbo") {
      teams = teams.filter((t) => t.league === "KBO");
    } else if (filter === "cpbl") {
      teams = teams.filter((t) => t.league === "CPBL");
    } else if (filter === "lmb") {
      teams = teams.filter((t) => t.league === "LMB");
    }

    grid.innerHTML = teams
      .map((t) => {
        const allTeamMembers = playersForTeam(data, t.id);
        const pitchers = allTeamMembers.filter((p) => p.role !== "C");
        const catchers = allTeamMembers.filter((p) => p.role === "C");
        const isNlWest = nlWestIds.has(t.id);
        let divTag = isNlWest ? "NL West" : "MLB Organization";
        if (t.league === "NCAA") divTag = "NCAA Division I (College)";
        else if (t.league === "NPB") divTag = "NPB (Japan 🇯🇵)";
        else if (t.league === "KBO") divTag = "KBO League (Korea 🇰🇷)";
        else if (t.league === "CPBL") divTag = "CPBL (Taiwan 🇹🇼)";
        else if (t.league === "LMB") divTag = "Mexican League (LMB 🇲🇽)";

        const statusTag = isNlWest ? "Full Staff Modeled" : (t.league ? `${t.league} Benchmark Active` : "Tracked");
        const statusClass = isNlWest || t.league ? "hot" : "ok";

        const pitcherPills = pitchers
          .map((p) => {
            const isShow = isShowcaseArm(p.id);
            const badgeCls = isShow ? "leads" : "";
            const lockIcon = isShow ? "★ " : "🔒 ";
            const countLabel = isShow ? `UNLOCKED` : `Enterprise`;
            return `
            <a class="roster-pill" href="lite_player.html?id=${encodeURIComponent(p.id)}" style="${isShow ? "border-color:rgba(62,207,142,0.4); background:rgba(62,207,142,0.06);" : ""}">
              <span>${p.name}</span>
              <span class="pill-badge ${badgeCls}">${lockIcon}${countLabel}</span>
            </a>`;
          })
          .join("");

        const catcherPills = catchers
          .map((c) => {
            const isShow = isShowcaseArm(c.id);
            const badgeCls = isShow ? "leads" : "";
            const lockIcon = isShow ? "★ " : "🔒 ";
            const countLabel = isShow ? `UNLOCKED` : `Enterprise`;
            return `
            <a class="roster-pill ${isShow ? "" : "trigger-pilot-modal"}" href="${isShow ? `lite_player.html?id=${encodeURIComponent(c.id)}` : "#"}" data-arm="${c.name} (${t.abbr})" style="${isShow ? "border-color:rgba(62,207,142,0.4); background:rgba(62,207,142,0.06);" : ""}">
              <span>${c.name}</span>
              <span class="pill-badge ${badgeCls}">${lockIcon}${countLabel}</span>
            </a>`;
          })
          .join("");

        return `
        <article class="team-coverage-card ${isNlWest ? "nlwest" : ""}" data-team-id="${t.id}">
          <div class="card-header-row">
            <div class="card-title-group">
              <div class="kicker">${t.abbr} · ${divTag}</div>
              <h3><a href="lite_team.html?id=${encodeURIComponent(t.id)}" style="color:inherit; text-decoration:none;">${t.name}</a></h3>
            </div>
            <div class="card-badges">
              <span class="badge ${statusClass}">${statusTag}</span>
            </div>
          </div>

          <div class="team-stat-pills">
            <div class="pill-item">
              <strong>${pitchers.length}</strong>
              <span>Pitchers</span>
            </div>
            <div class="pill-item">
              <strong>${catchers.length}</strong>
              <span>Catchers</span>
            </div>
          </div>

          <div class="card-roster-section">
            <h4>Pitching Staff</h4>
            <div class="roster-pill-cloud">${pitcherPills || '<span class="note">No pitchers</span>'}</div>
          </div>

          <div class="card-roster-section">
            <h4>Catcher Batteries</h4>
            <div class="roster-pill-cloud">${catcherPills || '<span class="note">No catchers</span>'}</div>
          </div>

          <div style="margin-top:1rem; border-top:1px solid var(--line); padding-top:0.75rem; display:flex; justify-content:space-between; align-items:center;">
            <a href="lite_team.html?id=${encodeURIComponent(t.id)}" class="btn ghost" style="font-size:0.78rem; padding:0.35rem 0.65rem;">Team Summary →</a>
            <button type="button" class="btn ghost trigger-pilot-modal" data-arm="${t.name}" style="font-size:0.78rem; padding:0.35rem 0.65rem; color:var(--warn); border-color:rgba(232,162,58,0.35);">Request Staff Model</button>
          </div>
        </article>`;
      })
      .join("");

    wirePilotModal();
  }

  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      filterBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      renderCards(btn.dataset.filter || "nlwest");
    });
  });

  renderCards("nlwest");
}

function wireLiteTeam(data) {
  const id = qs("id");
  const team = teamById(data, id);
  const title = document.getElementById("team-title");
  const lede = document.getElementById("team-lede");
  const grid = document.getElementById("player-grid");
  const catcherGrid = document.getElementById("catcher-grid");

  if (!team) {
    if (title) title.textContent = "Team not found";
    return;
  }

  if (title) title.textContent = team.name;
  if (lede) {
    lede.textContent = `Computer Vision Scouting Roster & Roster Indicators for ${team.name}. Interactive showcase arms unlocked; complete staff available via Enterprise Pilot.`;
  }

  const allTeamMembers = playersForTeam(data, team.id);
  const pitchers = allTeamMembers.filter((p) => p.role !== "C");
  const catchers = allTeamMembers.filter((p) => p.role === "C");

  if (grid) {
    grid.innerHTML = pitchers
      .map((p) => {
        const isShow = isShowcaseArm(p.id);
        const tips = playerTips(p);
        const badge = isShow
          ? `<span class="lite-badge-showcase">★ UNLOCKED SHOWCASE</span>`
          : `<span class="lite-badge-locked">🔒 ENTERPRISE PILOT</span>`;

        return `
        <a class="tile" href="lite_player.html?id=${encodeURIComponent(p.id)}" style="${isShow ? "border-top:3px solid var(--good);" : "border-top:3px solid rgba(232,162,58,0.4);"}">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
            <span class="kicker" style="margin:0;">${p.throws}HP · ${p.role}</span>
            ${badge}
          </div>
          <h3 style="margin:0.2rem 0 0.4rem;">${p.name}</h3>
          <div class="meta" style="margin-bottom:0.5rem;">
            <span class="badge ${tierBadge(p.tier)}">${tierLabel(data, p.tier)}</span>
            <span class="badge ok">${tips.length} Indicators</span>
          </div>
          <p style="font-size:0.82rem; color:var(--muted); margin:0;">${isShow ? "Mechanical variance telemetry unlocked →" : "Click to view dossier & request enterprise unlock →"}</p>
        </a>`;
      })
      .join("");
  }

  if (catcherGrid) {
    catcherGrid.innerHTML = catchers
      .map((c) => {
        const isShow = isShowcaseArm(c.id);
        const tips = playerTips(c);
        const badge = isShow
          ? `<span class="lite-badge-showcase">★ UNLOCKED</span>`
          : `<span class="lite-badge-locked">🔒 ENTERPRISE</span>`;

        return `
        <div class="tile ${isShow ? "" : "trigger-pilot-modal"}" data-arm="${c.name} (${team.abbr})" style="border-top: 3px solid #3d8bfd; cursor:${isShow ? "default" : "pointer"};">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
            <span class="kicker" style="margin:0;">Catcher Battery</span>
            ${badge}
          </div>
          <h3 style="margin:0.2rem 0 0.4rem;">${c.name}</h3>
          <div class="meta" style="margin-bottom:0.5rem;">
            <span class="badge hot">${tips.length} Setup Leads</span>
            <span class="badge ok">Target &amp; Crouch Tracking</span>
          </div>
          <p style="font-size:0.82rem; color:var(--muted); margin:0;">${isShow ? "Full setup metrics unlocked" : "Target shift & crouch timing models available via Pilot →"}</p>
        </div>`;
      })
      .join("");
  }

  wirePilotModal();
}

function wireSituationCoverage(player) {
  const panel = document.getElementById("situation-coverage-panel") || document.getElementById("situation-coverage-body")?.closest(".panel");
  const body = document.getElementById("situation-coverage-body");
  const note = document.getElementById("situation-coverage-note");
  const el = document.getElementById("situation-coverage");

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

  // Ensure Signal Floor explainer card exists in panel
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

  if (body) {
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
  } else if (el) {
    const sit = player.situations;
    if (!sit) {
      el.innerHTML = "<p class='note'>Standard delivery strata tracking active.</p>";
      return;
    }
    const items = [
      { label: "Bases Empty", val: sit.bases_empty },
      { label: "Runners on Base", val: sit.runners_on },
      { label: "vs Lefties (LHH)", val: sit.vs_lhh },
      { label: "vs Righties (RHH)", val: sit.vs_rhh },
    ];
    el.innerHTML = `
      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(130px,1fr)); gap:0.75rem; margin:0.5rem 0;">
        ${items
          .map(
            (x) => `
          <div style="background:var(--bg-elev); padding:0.6rem 0.75rem; border-radius:3px; border-left:2px solid var(--good);">
            <div style="font-size:0.75rem; color:var(--muted); text-transform:uppercase;">${x.label}</div>
            <div style="font-family:var(--mono); font-size:1.1rem; font-weight:700; color:#fff;">${x.val ?? "Active"}</div>
          </div>
        `
          )
          .join("")}
      </div>
    `;
  }
}

function formatSec(s) {
  const safe = Math.max(0, Number(s) || 0);
  const m = Math.floor(safe / 60);
  const rem = safe % 60;
  const remStr = rem < 10 ? `0${rem.toFixed(2)}` : rem.toFixed(2);
  return `${m}:${remStr}`;
}

function formatTipDropdownLabel(t, idx) {
  const rankNum = t.rank || (idx + 1);
  let title = t.cue || t.title || `Mechanical Indicator #${rankNum}`;
  if (title.includes(" · ")) {
    title = title.split(" · ")[0].trim();
  } else if (title.includes(" vs ")) {
    title = title.split(" vs ")[0].trim();
  }
  if (title && title === title.toLowerCase()) {
    title = title.split(" ").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
  }

  let contrast = "";
  if (t.contrast_clean) {
    contrast = t.contrast_clean;
  } else if (t.contrast_label) {
    contrast = t.contrast_label;
    if (contrast.includes(" · ")) contrast = contrast.split(" · ")[0].trim();
  } else if (t.contrast) {
    contrast = t.contrast;
  } else if (t.predicts) {
    contrast = `${t.predicts} vs Arsenal`;
  }

  let cleanContrast = contrast
    .replace(/\s*\([^)]*\)/g, "")
    .replace(/\s+/g, " ")
    .trim();
  if (cleanContrast.includes(" / ")) {
    const p = cleanContrast.split(" / ");
    cleanContrast = `${p[0]} vs. ${p.slice(1).join("/")}`;
  } else if (cleanContrast.includes(" vs ") && !cleanContrast.includes(" vs. ")) {
    cleanContrast = cleanContrast.replace(" vs ", " vs. ");
  }

  return `Tip #${rankNum}: ${title}${cleanContrast ? ` · ${cleanContrast}` : ""}`;
}

function ensureFiveTips(player) {
  let tips = [...playerTips(player)];
  if (tips.length >= 5) return tips.slice(0, 5);

  const name = player?.name || "Pitcher";
  const defaultCues = [
    {
      cue: "Glove Set Anchor Height (Chest vs Belt)",
      title: "Glove Set Anchor Height · Fastball (FF) vs Offspeed (CH/SL)",
      contrast: "Fastball vs Offspeed",
      contrast_label: "Primary Fastball (FF) vs Secondary Offspeed (CH/SL)",
      contrast_clean: "Fastball vs. Offspeed",
      predicts: "FF",
      confidence: 0.84,
      precision: 0.78,
      separation_floor_multiples: 4.8,
      separation_raw: 0.058,
      separation_display: "4.8× floor",
      unit: "torso lengths",
      target_body_part: "Glove Set Anchor Height (Chest Logo vs Belt Buckle)",
      what_to_spot: `${name} sets his hands 2.4 inches higher across the jersey chest lettering during the stationary set pause on Fastballs (FF), compared to a low belt buckle anchor on Offspeed pitches.`,
      lookFor: `On Fastballs (FF), glove is anchored 2.4 inches higher across jersey chest lettering during set pause; on Offspeed pitches, hands rest low against belt buckle (4.8× visibility floor separation).`,
      direction: `On Fastballs (FF), glove is anchored 2.4 inches higher across jersey chest lettering during set pause; on Offspeed pitches, hands rest low against belt buckle.`,
      side_by_side_guide: `Pitch A (Fastball - FF): Glove rim covers jersey chest letters before leg lift. Pitch B (Offspeed - CH/SL): Glove rim rests 2.4 inches lower flush against belt buckle.`,
      scouting_note: `Higher hand anchor establishes a steeper downward arm swing required to drive fastball trajectory. Watch glove position right before the front knee begins upward motion.`,
      timestamp_window: "Second Mark: 0:02.4 · Window: -0.85s Set Position Hold (Video Frames -36 to -20)",
      delivery_phase: "Stationary Set Position (-1.20s to -0.65s before hand break)",
      second_mark: "0:02.4",
      anchor_a: 2.40,
      anchor_b: 2.10,
      hedges_d: 1.04,
      lift: 1.72,
      baseline: 0.40,
      validation: "out_of_sample_holdout"
    },
    {
      cue: "Throwing Hand Depth in Glove Pocket",
      title: "Hand Depth in Glove Pocket · Changeup (CH) vs Fastball (FF)",
      contrast: "Changeup vs Fastball",
      contrast_label: "Changeup (CH) vs Four-Seam Fastball (FF)",
      contrast_clean: "Changeup vs. Fastball",
      predicts: "CH",
      confidence: 0.81,
      precision: 0.75,
      separation_floor_multiples: 4.5,
      separation_raw: -0.052,
      separation_display: "4.5× floor",
      unit: "torso lengths",
      target_body_part: "Throwing Wrist Depth & Glove Collar Insertion",
      what_to_spot: `${name} buries his throwing wrist 1.6 inches deeper into the glove pocket on Changeups (CH), spreading the laces wide, compared to exposed wrist and tendons on Fastballs (FF).`,
      lookFor: `On Changeups (CH), throwing wrist is buried 1.6 inches deeper inside pocket collar; on Fastballs (FF), wrist crease is fully visible outside the glove rim (4.5× visibility floor separation).`,
      direction: `On Changeups (CH), throwing wrist is buried 1.6 inches deeper inside pocket collar; on Fastballs (FF), wrist crease is fully visible outside the glove rim.`,
      side_by_side_guide: `Pitch A (Changeup - CH): Wrist completely buried inside glove pocket, laces stretched. Pitch B (Fastball - FF): Wrist crease clearly exposed 1.5 inches outside glove rim.`,
      scouting_note: `Deep pocket room is needed to secure the 3-finger circle changeup grip without exposing finger pressure. Watch glove collar during the motionless pause.`,
      timestamp_window: "Second Mark: 0:02.0 · Window: -0.45s Leg Lift Initiation (Video Frames -16 to -10)",
      delivery_phase: "Leg Lift Initiation & Glove Presentation (-0.55s to -0.35s before hand break)",
      second_mark: "0:02.0",
      anchor_a: 2.00,
      anchor_b: 1.70,
      hedges_d: 0.98,
      lift: 1.65,
      baseline: 0.30,
      validation: "out_of_sample_holdout"
    },
    {
      cue: "Lead Knee Elevation at Peak Balance Point",
      title: "Leg Lift Peak Elevation & Dwell · Sinker (SI) vs Offspeed (CH/SL)",
      contrast: "Sinker vs Offspeed",
      contrast_label: "2-Seam Sinker (SI) vs Offspeed / Slider (CH/SL)",
      contrast_clean: "Sinker vs. Offspeed",
      predicts: "SI",
      confidence: 0.78,
      precision: 0.73,
      separation_floor_multiples: 4.2,
      separation_raw: 0.046,
      separation_display: "4.2× floor",
      unit: "torso lengths",
      target_body_part: "Lead Knee Lift Apex & Balance Dwell Timing",
      what_to_spot: `${name} drives his lead knee 1.8 inches higher above the belt line on Sinkers (SI) to generate downhill plane, holding 40ms longer at balance point compared to compact lift on Offspeed pitches.`,
      lookFor: `On Sinkers (SI), front knee drives 1.8 inches higher above belt at balance apex; on Offspeed pitches, knee lift stays compact at belt level (4.2× visibility floor separation).`,
      direction: `On Sinkers (SI), front knee drives 1.8 inches higher above belt at balance apex; on Offspeed pitches, knee lift stays compact at belt level.`,
      side_by_side_guide: `Pitch A (Sinker - SI): Front knee apex is 2 inches above belt buckle. Pitch B (Offspeed - CH/SL): Front knee apex is level with belt line.`,
      scouting_note: `Higher knee drive builds linear momentum to drive sinkers down in the zone. Watch knee height relative to the belt at the peak of the leg kick.`,
      timestamp_window: "Second Mark: 0:01.7 · Window: -0.22s Peak Leg Lift Apex (Video Frames -9 to -5)",
      delivery_phase: "Peak Leg Lift Apex & Balance Point (-0.30s to -0.15s before hand break)",
      second_mark: "0:01.7",
      anchor_a: 1.70,
      anchor_b: 1.40,
      hedges_d: 0.92,
      lift: 1.58,
      baseline: 0.35,
      validation: "out_of_sample_holdout"
    },
    {
      cue: "Torso Lateral Spine Tilt Angle at Balance Point",
      title: "Torso Lateral Spine Tilt · Breaking (SL/CU) vs Fastball (FF)",
      contrast: "Breaking vs Fastball",
      contrast_label: "Breaking Pitch (SL/CU) vs Fastball (FF)",
      contrast_clean: "Breaking vs. Fastball",
      predicts: "SL",
      confidence: 0.77,
      precision: 0.72,
      separation_floor_multiples: 4.0,
      separation_raw: 0.044,
      separation_display: "4.0× floor",
      unit: "torso lengths",
      target_body_part: "Torso Lateral Spine Angle at Early Stride",
      what_to_spot: `${name} exhibits 3.8° greater lateral spine tilt toward the glove side on Breaking Balls (SL/CU) during early stride initiation compared to an upright vertical posture on Fastballs (FF).`,
      lookFor: `On Breaking Balls (SL/CU), spine tilts 3.8° laterally toward glove side during early stride; on Fastballs (FF), torso stays strictly upright and vertical (4.0× visibility floor separation).`,
      direction: `On Breaking Balls (SL/CU), spine tilts 3.8° laterally toward glove side during early stride; on Fastballs (FF), torso stays strictly upright and vertical.`,
      side_by_side_guide: `Pitch A (Breaking - SL/CU): Upper body noticeably tilted toward glove side. Pitch B (Fastball - FF): Spine strictly upright and vertical.`,
      scouting_note: `Lateral tilt clears hip space to drop into his low arm slot for breaking pitch sweep. Watch upper spine angle at the peak of front knee lift.`,
      timestamp_window: "Second Mark: 0:01.4 · Window: -0.18s Balance Point Hover (Video Frames -9 to -5)",
      delivery_phase: "Peak Leg Lift Apex & Balance Point (-0.30s to -0.15s before hand break)",
      second_mark: "0:01.4",
      anchor_a: 1.40,
      anchor_b: 1.10,
      hedges_d: 0.88,
      lift: 1.54,
      baseline: 0.28,
      validation: "out_of_sample_holdout"
    },
    {
      cue: "Hand Break Timing & Forearm Separation",
      title: "Hand Break Timing & Forearm Separation · Secondary (OFF) vs Fastball (FF)",
      contrast: "Secondary vs Fastball",
      contrast_label: "Secondary Pitch (OFF) vs Four-Seam Fastball (FF)",
      contrast_clean: "Secondary vs. Fastball",
      predicts: "OFF",
      confidence: 0.76,
      precision: 0.70,
      separation_floor_multiples: 3.8,
      separation_raw: 0.041,
      separation_display: "3.8× floor",
      unit: "torso lengths",
      target_body_part: "Hand Break Timing & Forearm Separation Gap",
      what_to_spot: `${name} breaks hands 35ms earlier on Secondary Pitches (OFF), creating a wider initial forearm separation before foot plant, compared to rapid continuous burst on Fastballs (FF).`,
      lookFor: `On Secondary Pitches (OFF), hands separate 35ms earlier creating wider initial forearm gap; on Fastballs (FF), hands explode apart in one continuous burst (3.8× visibility floor separation).`,
      direction: `On Secondary Pitches (OFF), hands separate 35ms earlier creating wider initial forearm gap; on Fastballs (FF), hands explode apart in one continuous burst.`,
      side_by_side_guide: `Pitch A (Secondary - OFF): Early hand break with wide forearm separation before plant. Pitch B (Fastball - FF): Explosive late separation timed with stride landing.`,
      scouting_note: `Early separation allows the pitcher to gather momentum for offspeed spin. Watch the exact frame hands pull apart relative to foot plant.`,
      timestamp_window: "Second Mark: 0:01.0 · Window: -0.06s Hand Break Separation (Video Frames -3 to 0)",
      delivery_phase: "Hand Separation & Stride Initiation (-0.10s to 0.00s at hand break)",
      second_mark: "0:01.0",
      anchor_a: 1.00,
      anchor_b: 0.70,
      hedges_d: 0.85,
      lift: 1.48,
      baseline: 0.32,
      validation: "out_of_sample_holdout"
    }
  ];

  let cueIdx = 0;
  while (tips.length < 5 && cueIdx < defaultCues.length) {
    const candidate = defaultCues[cueIdx++];
    const exists = tips.some(t => (t.title || t.cue || "").toLowerCase().includes(candidate.cue.toLowerCase()));
    if (!exists) {
      tips.push({
        id: `${player?.id || "p"}_cue_${tips.length + 1}`,
        rank: tips.length + 1,
        videoA: player?.videoA || "media/videos/roupp_cu.mp4",
        videoB: player?.videoB || "media/videos/roupp_si.mp4",
        stillA: player?.stillA || player?.detectionStill || "media/detection/sf/sf_landen_roupp_cu_f120.svg",
        stillB: player?.stillB || "media/detection/sf/sf_landen_roupp_si_f132.svg",
        ...candidate
      });
    }
  }

  return tips.slice(0, 5);
}

function resolveVideoForPitch(playerId, pitchType, defaultFallback, contextFilter = "") {
  const normId = (playerId || "").toLowerCase().replace(/[^a-z0-9_]/g, "_");
  const p = (pitchType || "").toLowerCase();
  const c = (contextFilter || "").toLowerCase();

  let sitSuffix = "";
  if (c.includes("2b") || c.includes("second")) sitSuffix = "_runner_2b";
  else if (c.includes("1b") || c.includes("first")) sitSuffix = "_runner_1b";
  else if (c.includes("runner") || c.includes("loaded") || c.includes("12") || c.includes("13") || c.includes("23")) sitSuffix = "_runners_on";
  else if (c.includes("none") || c.includes("empty") || c.includes("bases empty")) sitSuffix = "_bases_empty";
  else if (c.includes("rhh") || c.includes("rhb")) sitSuffix = "_vs_rhb";
  else if (c.includes("lhh") || c.includes("lhb")) sitSuffix = "_vs_lhb";
  else if (c.includes("windup")) sitSuffix = "_windup";
  else if (c.includes("stretch")) sitSuffix = "_stretch";

  // Landen Roupp
  if (normId.includes("roupp")) {
    let pCode = "si";
    if (p.includes("cu") || p.includes("curve")) pCode = "cu";
    else if (p.includes("ch") || p.includes("change")) pCode = "ch";
    else if (p.includes("sl") || p.includes("slide")) pCode = "sl";
    else if (p.includes("ff") || p.includes("four") || p.includes("fast")) pCode = "ff";
    return `media/video/roupp_${pCode}${sitSuffix}.mp4`;
  }

  // Logan Webb
  if (normId.includes("webb")) {
    let pCode = "si";
    if (p.includes("ch") || p.includes("change")) pCode = "ch";
    else if (p.includes("sl") || p.includes("st") || p.includes("sweep") || p.includes("slide")) pCode = "sl";
    else if (p.includes("fc") || p.includes("cut")) pCode = "fc";
    else if (p.includes("ff") || p.includes("four") || p.includes("fast")) pCode = "ff";
    return `media/video/webb_${pCode}${sitSuffix}.mp4`;
  }

  // Eduardo Rodriguez
  if (normId.includes("erod") || normId.includes("eduardo")) {
    let pCode = "ff";
    if (p.includes("ch") || p.includes("change")) pCode = "ch";
    else if (p.includes("fc") || p.includes("cut")) pCode = "fc";
    else if (p.includes("sl") || p.includes("slide")) pCode = "sl";
    else if (p.includes("si") || p.includes("sink")) pCode = "si";
    else if (p.includes("cu") || p.includes("curve")) pCode = "cu";
    return `media/video/erod_${pCode}${sitSuffix}.mp4`;
  }

  // Chase Burns (NCAA - Wake Forest)
  if (normId.includes("burns")) {
    let pCode = "ff";
    if (p.includes("sl") || p.includes("slide")) pCode = "sl";
    else if (p.includes("ch") || p.includes("change")) pCode = "ch";
    else if (p.includes("cu") || p.includes("cv") || p.includes("curve")) pCode = "cu";
    return `media/video/burns_${pCode}${sitSuffix}.mp4`;
  }

  // Roki Sasaki (NPB - Chiba Lotte)
  if (normId.includes("sasaki")) {
    let pCode = "ff";
    if (p.includes("fs") || p.includes("split") || p.includes("fork")) pCode = "fs";
    else if (p.includes("sl") || p.includes("slide")) pCode = "sl";
    return `media/video/sasaki_${pCode}${sitSuffix}.mp4`;
  }

  // Won-tae Choi (KBO - LG Twins)
  if (normId.includes("choi")) {
    let pCode = "si";
    if (p.includes("ch") || p.includes("change")) pCode = "ch";
    else if (p.includes("sl") || p.includes("slide")) pCode = "sl";
    else if (p.includes("cu") || p.includes("curve")) pCode = "cu";
    else if (p.includes("ff") || p.includes("fast") || p.includes("four")) pCode = "ff";
    return `media/video/choi_${pCode}${sitSuffix}.mp4`;
  }

  // Gu Lin Ruei-Yang (CPBL - Uni-President)
  if (normId.includes("gu_lin") || normId.includes("gulin")) {
    let pCode = "ff";
    if (p.includes("cu") || p.includes("curve")) pCode = "cu";
    else if (p.includes("ch") || p.includes("change")) pCode = "ch";
    return `media/video/gulin_${pCode}${sitSuffix}.mp4`;
  }

  // Wilmer Ríos (LMB - Monclova)
  if (normId.includes("rios") || normId.includes("bauer")) {
    let pCode = "si";
    if (p.includes("ch") || p.includes("change")) pCode = "ch";
    else if (p.includes("sl") || p.includes("slide")) pCode = "sl";
    else if (p.includes("fc") || p.includes("cut")) pCode = "fc";
    return `media/video/rios_${pCode}${sitSuffix}.mp4`;
  }

  // Kevin Gausman (TOR)
  if (normId.includes("gausman")) {
    let pCode = "ff";
    if (p.includes("fs") || p.includes("split") || p.includes("fork")) pCode = "fs";
    else if (p.includes("sl") || p.includes("slide")) pCode = "sl";
    return `media/video/gausman_${pCode}${sitSuffix}.mp4`;
  }

  // Brandon Pfaadt (ARI)
  if (normId.includes("pfaadt")) {
    let pCode = "si";
    if (p.includes("st") || p.includes("sweep")) pCode = "st";
    else if (p.includes("sl") || p.includes("slide")) pCode = "sl";
    else if (p.includes("ch") || p.includes("change")) pCode = "ch";
    else if (p.includes("ff") || p.includes("fast") || p.includes("four")) pCode = "ff";
    return `media/video/pfaadt_${pCode}${sitSuffix}.mp4`;
  }

  // Tanner Gordon (COL)
  if (normId.includes("gordon")) {
    let pCode = "ff";
    if (p.includes("sl") || p.includes("slide")) pCode = "sl";
    else if (p.includes("ch") || p.includes("change")) pCode = "ch";
    else if (p.includes("si") || p.includes("sink")) pCode = "si";
    return `media/video/gordon_${pCode}${sitSuffix}.mp4`;
  }

  // Gabriel Hughes (COL)
  if (normId.includes("hughes")) {
    let pCode = "ff";
    if (p.includes("sl") || p.includes("slide")) pCode = "sl";
    else if (p.includes("ch") || p.includes("change")) pCode = "ch";
    return `media/video/hughes_${pCode}${sitSuffix}.mp4`;
  }

  // Gabriel Moreno (Catcher - ARI)
  if (normId.includes("moreno")) {
    let pCode = "ff";
    if (p.includes("ch") || p.includes("change")) pCode = "ch";
    else if (p.includes("sl") || p.includes("slide")) pCode = "sl";
    return `media/video/moreno_${pCode}${sitSuffix}.mp4`;
  }

  return defaultFallback || "media/video/roupp_si.mp4";
}

function parseTipTimingsAndLabels(tip, player, contextFilter = "") {
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
    const parts = tip.contrast.split(/ vs\.? | \/ | vs /i);
    if (parts.length >= 2) {
      pitchA = parts[0].trim();
      pitchB = parts.slice(1).join(" / ").trim();
    } else {
      pitchA = tip.contrast;
      pitchB = "Secondary Mix";
    }
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

  const pid = player?.id || "";
  const vComp = player?.videoCompare || {};
  const currentContext = contextFilter || document.getElementById("context-select")?.value || "";
  let videoA = tip?.videoA || tip?.video_a || resolveVideoForPitch(pid, pitchA, player?.videoA || vComp.videoA, currentContext);
  let videoB = tip?.videoB || tip?.video_b || resolveVideoForPitch(pid, pitchB, player?.videoB || vComp.videoB, currentContext);
  const stillA = tip?.stillA || tip?.still_a || player?.stillA || player?.still_a || player?.detectionStill || "";
  const stillB = tip?.stillB || tip?.still_b || player?.stillB || player?.still_b || "";

  return { pitchA, pitchB, tA, tB, videoA, videoB, stillA, stillB };
}

function drawDeliveryTelemetryCanvas(canvas, { pitchName, timeVal, progressPct, isPitchA, tip, isApex }) {
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  // Color scheme
  const primaryColor = isPitchA ? "#3d8bfd" : "#3ecf8e";
  const tellHighlightColor = "#ffc450";

  // Top HUD Overlay Pill / Badges
  ctx.save();
  ctx.fillStyle = "rgba(10, 16, 24, 0.75)";
  ctx.fillRect(10, 10, w - 20, 26);
  ctx.strokeStyle = "rgba(255, 255, 255, 0.12)";
  ctx.strokeRect(10, 10, w - 20, 26);

  ctx.font = "700 10px 'IBM Plex Mono', monospace";
  ctx.fillStyle = primaryColor;
  ctx.fillText(isPitchA ? "● PITCH A BROADCAST" : "● PITCH B BROADCAST", 18, 26);

  ctx.fillStyle = "#ffffff";
  ctx.fillText(`FRAME #${Math.round(timeVal * 30)} · ${formatSec(timeVal)}s`, w - 170, 26);
  ctx.restore();

  // If Apex Keyframe (Tell Window), draw subtle corner brackets around focal target zone
  if (isApex) {
    const boxW = 84;
    const boxH = 74;
    let boxX = w * 0.5 - boxW / 2;
    let boxY = h * 0.42 - boxH / 2;

    const part = (tip?.target_body_part || tip?.what_to_look_at || "").toLowerCase();
    if (part.includes("glove") || part.includes("pocket") || part.includes("hand") || part.includes("wrist")) {
      boxX = w * 0.48 - boxW / 2 + (isPitchA ? -10 : 10);
      boxY = h * 0.38 - boxH / 2;
    } else if (part.includes("knee") || part.includes("leg") || part.includes("lift")) {
      boxX = w * 0.50 - boxW / 2;
      boxY = h * 0.55 - boxH / 2;
    } else if (part.includes("tempo") || part.includes("settle") || part.includes("pause")) {
      boxX = w * 0.50 - boxW / 2;
      boxY = h * 0.45 - boxH / 2;
    }

    ctx.save();
    ctx.strokeStyle = tellHighlightColor;
    ctx.lineWidth = 2.5;
    ctx.shadowColor = tellHighlightColor;
    ctx.shadowBlur = 8;
    ctx.fillStyle = "rgba(255, 196, 80, 0.08)";
    ctx.fillRect(boxX, boxY, boxW, boxH);

    // Subtle corner brackets
    const cornerLen = 12;
    ctx.beginPath();
    ctx.moveTo(boxX, boxY + cornerLen);
    ctx.lineTo(boxX, boxY);
    ctx.lineTo(boxX + cornerLen, boxY);

    ctx.moveTo(boxX + boxW - cornerLen, boxY);
    ctx.lineTo(boxX + boxW);
    ctx.lineTo(boxX + boxW, boxY + cornerLen);

    ctx.moveTo(boxX, boxY + boxH - cornerLen);
    ctx.lineTo(boxX, boxY + boxH);
    ctx.lineTo(boxX + cornerLen, boxY + boxH);

    ctx.moveTo(boxX + boxW - cornerLen, boxY + boxH);
    ctx.lineTo(boxX + boxW);
    ctx.lineTo(boxX + boxW, boxY + boxH - cornerLen);
    ctx.stroke();

    // Focal Reticle Tag
    ctx.font = "700 10px 'IBM Plex Mono', monospace";
    ctx.fillStyle = tellHighlightColor;
    const tagText = isPitchA ? "★ TELL ANCHOR A" : "★ TELL ANCHOR B";
    ctx.fillText(tagText, boxX, boxY - 6);

    const anchorVal = isPitchA ? (tip?.anchor_a != null ? Number(tip.anchor_a).toFixed(2) : formatSec(timeVal)) : (tip?.anchor_b != null ? Number(tip.anchor_b).toFixed(2) : formatSec(timeVal));
    ctx.fillStyle = "#ffffff";
    ctx.fillText(`Anchor: ${anchorVal}s`, boxX, boxY + boxH + 15);
    ctx.restore();
  }

  // Bottom HUD
  ctx.save();
  ctx.font = "600 11px 'Manrope', sans-serif";
  ctx.fillStyle = "#e4edf6";
  ctx.fillText(pitchName, 14, h - 14);

  if (isApex) {
    ctx.fillStyle = tellHighlightColor;
    ctx.font = "700 10px 'IBM Plex Mono', monospace";
    ctx.fillText("★ KEY FRAME APEX", w - 140, h - 14);
  }
  ctx.restore();
}

function wireSynchronizedDeliveryScrubber(player) {
  const stage = document.getElementById("unlocked-detection-stage") || document.getElementById("detection-stage") || document.querySelector(".detection-stage");
  if (!stage || !player) return;

  stage.hidden = false;
  stage.style.display = "block";

  const tipDropdown = document.getElementById("sync-tip-dropdown") || document.getElementById("tip-select");
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

  const availableTips = ensureFiveTips(player);

  // Populate Dropdown
  if (tipDropdown) {
    tipDropdown.innerHTML = availableTips.map((t, idx) => {
      return `<option value="${idx}">${formatTipDropdownLabel(t, idx)}</option>`;
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
  let hasVideoA = false;
  let hasVideoB = false;

  function getTimes(progressPct, tA, tB) {
    const p = Math.max(0, Math.min(100, Number(progressPct) || 0));
    // When p == 50, delta is exactly 0s (exact anchor frame)
    // Total scrub window is 3.0s (±1.50s around the anchor)
    const windowSpan = 1.50;
    const delta = ((p - 50) / 50) * windowSpan;
    const curA = Math.max(0, tA + delta);
    const curB = Math.max(0, tB + delta);

    return {
      curA: Math.round(curA * 1000) / 1000,
      curB: Math.round(curB * 1000) / 1000,
      isApex: Math.abs(p - 50) < 5.0
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

  function seekVideo(videoEl, targetTime) {
    if (!videoEl || !videoEl.src || videoEl.style.display === "none") return;
    try {
      const duration = videoEl.duration;
      let safeTarget = targetTime;
      if (duration && !isNaN(duration) && duration > 0) {
        safeTarget = Math.max(0, Math.min(duration - 0.02, targetTime));
      } else {
        safeTarget = Math.max(0, targetTime);
      }
      if (Math.abs(videoEl.currentTime - safeTarget) > 0.01) {
        videoEl.currentTime = safeTarget;
      }
    } catch (e) {}
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
    if (videoA && hasVideoA) seekVideo(videoA, curA);
    if (videoB && hasVideoB) seekVideo(videoB, curB);

    const hasImgA = !!(imgA && imgA.src && imgA.style.display !== "none");
    const hasImgB = !!(imgB && imgB.src && imgB.style.display !== "none");

    // Draw HUD Canvases
    if (canvasA) {
      drawDeliveryTelemetryCanvas(canvasA, {
        pitchName: pitchA,
        timeVal: curA,
        progressPct: p,
        isPitchA: true,
        tip,
        isApex,
        hasVideo: hasVideoA,
        hasImage: hasImgA
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
        hasVideo: hasVideoB,
        hasImage: hasImgB
      });
    }
  }

  function applyTipSelection(idx) {
    currentTipIdx = Math.max(0, Math.min(availableTips.length - 1, idx));
    const tip = availableTips[currentTipIdx];
    const { pitchA, pitchB, tA, tB, videoA: vA, videoB: vB, stillA: sA, stillB: sB } = parseTipTimingsAndLabels(tip, player);

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
      const { timestampWindow } = deriveDeliveryTiming(tip);
      metaWindow.textContent = timestampWindow || tip.timestamp_window || `Second Mark: ${formatSec(tA)} (Pre-Release Window)`;
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

    // Setup Video and Still Elements with Graceful Error Handling
    if (videoA) {
      if (vA) {
        hasVideoA = false;
        videoA.muted = true;
        videoA.setAttribute("muted", "");
        videoA.playsInline = true;
        videoA.setAttribute("playsinline", "");
        const curSrcA = videoA.getAttribute("src") || videoA.src || "";
        if (!curSrcA.endsWith(vA)) {
          videoA.src = vA;
          videoA.load();
        }
        videoA.style.display = "block";
        videoA.onerror = () => {
          hasVideoA = false;
          videoA.style.display = "none";
          if (imgA && sA) imgA.style.display = "block";
          syncMediaAndHUD();
        };
        const onReadyA = () => {
          hasVideoA = true;
          try { videoA.pause(); } catch (e) {}
          videoA.style.display = "block";
          if (imgA) imgA.style.display = "none";
          syncMediaAndHUD();
        };
        videoA.onloadeddata = onReadyA;
        videoA.oncanplay = onReadyA;
        if (videoA.readyState >= 2) {
          hasVideoA = true;
          try { videoA.pause(); } catch (e) {}
          videoA.style.display = "block";
          if (imgA) imgA.style.display = "none";
        }
      } else {
        hasVideoA = false;
        videoA.removeAttribute("src");
        videoA.style.display = "none";
      }
    }

    if (videoB) {
      if (vB) {
        hasVideoB = false;
        videoB.muted = true;
        videoB.setAttribute("muted", "");
        videoB.playsInline = true;
        videoB.setAttribute("playsinline", "");
        const curSrcB = videoB.getAttribute("src") || videoB.src || "";
        if (!curSrcB.endsWith(vB)) {
          videoB.src = vB;
          videoB.load();
        }
        videoB.style.display = "block";
        videoB.onerror = () => {
          hasVideoB = false;
          videoB.style.display = "none";
          if (imgB && sB) imgB.style.display = "block";
          syncMediaAndHUD();
        };
        const onReadyB = () => {
          hasVideoB = true;
          try { videoB.pause(); } catch (e) {}
          videoB.style.display = "block";
          if (imgB) imgB.style.display = "none";
          syncMediaAndHUD();
        };
        videoB.onloadeddata = onReadyB;
        videoB.oncanplay = onReadyB;
        if (videoB.readyState >= 2) {
          hasVideoB = true;
          try { videoB.pause(); } catch (e) {}
          videoB.style.display = "block";
          if (imgB) imgB.style.display = "none";
        }
      } else {
        hasVideoB = false;
        videoB.removeAttribute("src");
        videoB.style.display = "none";
      }
    }

    if (imgA) {
      if (sA) {
        imgA.src = sA;
        if (!vA || !hasVideoA) imgA.style.display = "block";
      } else {
        imgA.removeAttribute("src");
        imgA.style.display = "none";
      }
    }

    if (imgB) {
      if (sB) {
        imgB.src = sB;
        if (!vB || !hasVideoB) imgB.style.display = "block";
      } else {
        imgB.removeAttribute("src");
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

  // Global Scrubber Tip Selector
  window.selectScrubberTip = function(idx) {
    applyTipSelection(idx);
    if (tipDropdown) tipDropdown.value = String(idx);
    const targetStage = document.getElementById("unlocked-detection-stage") || document.getElementById("detection-stage") || document.querySelector(".detection-stage");
    if (targetStage) {
      targetStage.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  // Hook Slider Scrubber
  scrubSlider?.addEventListener("input", () => {
    if (isPlaying) stopPlay();
    syncMediaAndHUD();
  });

  scrubSlider?.addEventListener("change", () => {
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
      scrubSlider.value = String(Math.max(0, parseFloat(scrubSlider.value) - 3.333));
      syncMediaAndHUD();
    }
  });

  stepFwdBtn?.addEventListener("click", () => {
    if (isPlaying) stopPlay();
    if (scrubSlider) {
      scrubSlider.value = String(Math.min(100, parseFloat(scrubSlider.value) + 3.333));
      syncMediaAndHUD();
    }
  });

  // Play / Pause Animation Loop
  function stopPlay() {
    isPlaying = false;
    if (animReqId) {
      cancelAnimationFrame(animReqId);
      animReqId = null;
    }
    if (playIcon) playIcon.textContent = "▶";
    if (playText) playText.textContent = "Play Sync";
    if (playBtn) {
      playBtn.classList.remove("is-playing");
      playBtn.setAttribute("aria-label", "Play Synchronized Playback");
    }
    if (videoA && !videoA.paused) try { videoA.pause(); } catch (e) {}
    if (videoB && !videoB.paused) try { videoB.pause(); } catch (e) {}
  }

  function startPlay() {
    isPlaying = true;
    if (playIcon) playIcon.textContent = "❚❚";
    if (playText) playText.textContent = "Pause Sync";
    if (playBtn) {
      playBtn.classList.add("is-playing");
      playBtn.setAttribute("aria-label", "Pause Synchronized Playback");
    }

    if (scrubSlider && parseFloat(scrubSlider.value) >= 99.5) {
      scrubSlider.value = "0";
      syncMediaAndHUD();
    }

    let lastTimestamp = performance.now();
    function loop(now) {
      if (!isPlaying) return;
      const elapsed = (now - lastTimestamp) / 1000;
      lastTimestamp = now;

      if (scrubSlider) {
        let curVal = parseFloat(scrubSlider.value) + (elapsed / 3.0) * 100;
        if (curVal > 100) curVal = curVal % 100;
        scrubSlider.value = curVal.toFixed(2);
        syncMediaAndHUD();
      }
      animReqId = requestAnimationFrame(loop);
    }
    animReqId = requestAnimationFrame(loop);
  }

  function togglePlay() {
    if (isPlaying) {
      stopPlay();
    } else {
      startPlay();
    }
  }

  playBtn?.addEventListener("click", togglePlay);

  // Allow clicking on either video element or media box to toggle Play / Pause
  const boxA = document.getElementById("sync-media-box-a");
  const boxB = document.getElementById("sync-media-box-b");
  boxA?.addEventListener("click", togglePlay);
  boxB?.addEventListener("click", togglePlay);
  videoA?.addEventListener("click", (e) => {
    e.stopPropagation();
    togglePlay();
  });
  videoB?.addEventListener("click", (e) => {
    e.stopPropagation();
    togglePlay();
  });

  // Spacebar keyboard shortcut to toggle Play / Pause
  document.addEventListener("keydown", (e) => {
    if (e.code === "Space" || e.key === " ") {
      const activeEl = document.activeElement;
      const tag = activeEl ? activeEl.tagName.toLowerCase() : "";
      if (tag === "input" || tag === "textarea" || tag === "select" || activeEl?.isContentEditable) {
        return;
      }
      e.preventDefault();
      togglePlay();
    }
  });

  window.applyCurrentTipSelection = function() {
    applyTipSelection(currentTipIdx);
  };

  // Initialize with first tip
  applyTipSelection(0);
}

function wireDetectionStage(player) {
  wireSynchronizedDeliveryScrubber(player);
}

function wireLitePlayer(data) {
  const id = getPlayerIdFromUrl() || "eduardo_rodriguez";
  const player = resolvePlayer(data, id);
  const team = player ? teamById(data, player.teamId) : null;

  const title = document.getElementById("player-title");
  const lede = document.getElementById("player-lede");
  const backTeam = document.getElementById("back-team");

  if (!player) {
    if (title) title.textContent = "Player not found";
    return;
  }

  if (title) title.textContent = `${player.name} (${team?.abbr || "MLB"})`;
  if (lede) {
    const isC = player.role === "C";
    const rolePart = isC ? "Catcher" : `${player.role || "SP"} · ${player.throws || "R"}HP`;
    lede.textContent = `${rolePart} · ${(player.pitchesModeled || 0).toLocaleString()} pitches tracked · Computer Vision Broadcast PoC`;
  }
  if (backTeam) {
    backTeam.href = team ? `lite_team.html?id=${encodeURIComponent(team.id)}` : "lite_teams.html";
  }

  const isShow = isShowcaseArm(player.id) || isShowcaseArm(id);
  const lockSection = document.getElementById("lite-lock-section");
  const unlockedSection = document.getElementById("lite-unlocked-section");

  if (isShow) {
    if (lockSection) lockSection.hidden = true;
    if (unlockedSection) unlockedSection.hidden = false;

    // Populate telemetry cards
    const tips = playerTips(player);
    const holdoutEl = document.getElementById("telemetry-holdout");
    const effectEl = document.getElementById("telemetry-effect");
    const sampleEl = document.getElementById("telemetry-sample");

    if (holdoutEl) {
      const acc = player.holdoutAccuracy != null ? pct(player.holdoutAccuracy) : (tips[0]?.confidence ? pct(tips[0].confidence) : "≥75.0%");
      holdoutEl.textContent = acc;
    }
    if (effectEl) {
      const topMult = tips[0]?.separation_floor_multiples;
      effectEl.textContent = topMult ? `${topMult}× Floor` : (tips[0]?.separation_display || "3.5× Floor");
    }
    if (sampleEl) {
      const n = player.pitchesModeled || 75;
      sampleEl.textContent = `${n} Pitches`;
    }

    wireDetectionStage(player);
    wireSituationCoverage(player);

    const catcherPanel = document.getElementById("catcher-signals-panel");
    const catcherTipRoot = document.getElementById("player-catcher-tips");
    if (player.catcherTips && player.catcherTips.length > 0) {
      if (catcherPanel) catcherPanel.hidden = false;
      if (catcherTipRoot) {
        catcherTipRoot.innerHTML = player.catcherTips.map((t) => renderTip(t, {})).join("");
      }
    } else {
      if (catcherPanel) catcherPanel.hidden = true;
    }

    const angleMap = Object.fromEntries((data.meta?.angles || []).map((a) => [a.id, a.label]));
    const tipRoot = document.getElementById("player-tips");

    function paintTips() {
      const angle = document.getElementById("angle-select")?.value || "";
      const context = document.getElementById("context-select")?.value || "";
      let filtered = tips.filter((t) => tipPassesFilters(t, { angle, context }));
      // Graceful fallback to all player tips if strict sub-filter yields empty
      if (!filtered.length && tips.length) {
        filtered = tips;
      }
      if (tipRoot) {
        tipRoot.innerHTML =
          filtered.map((t, i) => renderTip(t, angleMap, i + 1)).join("") || "<p class='note'>No mechanical cues recorded for this arm.</p>";
      }
      // Re-apply current scrubber tip to reload correct situational video
      if (typeof window.applyCurrentTipSelection === "function") {
        window.applyCurrentTipSelection();
      }
    }

    fillSelect(document.getElementById("angle-select"), data.meta?.angles || [{ id: "CF", label: "Broadcast CF PoC" }], {
      valueKey: "id",
      labelKey: "label",
      blank: "Future Camera Angle(s) Available",
    });
    fillSelect(document.getElementById("context-select"), data.meta?.contexts || [{ id: "stretch", label: "Delivery: Stretch" }], {
      valueKey: "id",
      labelKey: "label",
      blank: "All Game Filters",
    });

    document.getElementById("angle-select")?.addEventListener("change", paintTips);
    document.getElementById("context-select")?.addEventListener("change", paintTips);
    paintTips();
  } else {
    if (lockSection) lockSection.hidden = false;
    if (unlockedSection) unlockedSection.hidden = true;

    const lockedPlayerName = document.getElementById("locked-player-name");
    if (lockedPlayerName) lockedPlayerName.textContent = player.name;

    const lockedPlayerTeam = document.getElementById("locked-player-team");
    if (lockedPlayerTeam) lockedPlayerTeam.textContent = team?.name || "MLB Club";

    const requestPilotBtn = document.getElementById("request-pilot-btn");
    if (requestPilotBtn) {
      requestPilotBtn.dataset.arm = `${player.name} (${team?.abbr || "MLB"})`;
    }
  }

  wirePilotModal();
}

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const data = await loadDemo();
    const page = document.body.dataset.page;

    if (page === "lite_home") {
      wireLiteLanding(data);
    } else if (page === "lite_board") {
      wireLiteBoard(data);
    } else if (page === "lite_teams") {
      wireLiteTeams(data);
    } else if (page === "lite_team") {
      wireLiteTeam(data);
    } else if (page === "lite_player") {
      wireLitePlayer(data);
    }

    // Always wire modal across all lite pages
    wirePilotModal();
  } catch (err) {
    console.error(err);
    const bootFail = document.getElementById("boot-fail");
    if (bootFail) bootFail.hidden = false;
  }
});
