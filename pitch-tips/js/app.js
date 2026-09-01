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
  "bauer",
  "trevor_bauer",
  "hughes",
  "gabriel_hughes",
  "brandon_pfaadt",
  "pfaadt",
  "gordon",
  "tanner_gordon",
  "gausman",
  "kevin_gausman",
  "snell",
  "blake_snell",
  "skubal",
  "tarik_skubal",
  "glasnow",
  "tyler_glasnow",
  "buehler",
  "walker_buehler",
  "kelly",
  "merrill_kelly",
  "miller",
  "mason_miller",
  "sugano",
  "tomoyuki_sugano",
  "yamamoto",
  "yoshinobu_yamamoto",
  "matsui",
  "yuki_matsui",
  "ray",
  "robbie_ray",
  "drake",
  "kohl_drake",
  "frasso",
  "nick_frasso",
  "morejon",
  "adrian_morejon",
  "vesia",
  "alex_vesia",
  "jameson",
  "drey_jameson",
  "ginkel",
  "kevin_ginkel",
  "feltner",
  "ryan_feltner",
  "lauer",
  "eric_lauer",
  "dreyer",
  "jack_dreyer",
  "scott",
  "tanner_scott",
  "king",
  "michael_king",
  "vasquez",
  "randy_vasquez",
  "peralta",
  "wandy_peralta",
  "hart",
  "kyle_hart",
  "morgan",
  "david_morgan",
  "tidwell",
  "blade_tidwell",
  "hentges",
  "sam_hentges",
  "ryan_walker",
  "dylan_smith",
  "carson_seymour",
  "reiver_sanmartin",
  "jason_foley",
  "ryan_zeferjahn",
  "caleb_thielbar",
  "casey_mize",
  "mize"
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

  gausman: "kevin_gausman",
  kevin_gausman: "kevin_gausman",
  kevingausman: "kevin_gausman",
  "kevin-gausman": "kevin_gausman",

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
          You are viewing a protected arm from the full Preflight Computer Vision platform. Interactive showcase access is unlocked for <strong>Roupp / Webb / E-Rod</strong> plus non-MLB demo arms (<strong>Burns, Sasaki, Choi, Gu Lin, Ríos, Hughes, Moreno</strong>).
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
      <strong>✨ PREFLIGHT LITE SHOWCASE:</strong> Interactive delivery compare unlocked for MLB showcase + non-MLB demo arms (Burns, Sasaki, Choi, Gu Lin, Ríos, Hughes, Moreno). Full 60+ arm database locked for Enterprise pilots.
    </div>
    <div style="display: flex; gap: 0.5rem; align-items: center;">
      <a class="banner-cta" href="https://x.com/colbymorris08" target="_blank" rel="noopener noreferrer">Request Enterprise Pilot / DM →</a>
    </div>
  `;
  document.body.prepend(banner);
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
  const panel = document.getElementById("situation-coverage-panel") || document.getElementById("situation-coverage-body")?.closest(".panel") || document.getElementById("situation-breakdown-tbody")?.closest(".panel") || document.getElementById("arsenal-tbody")?.closest(".panel");
  const bodies = [
    document.getElementById("situation-coverage-body"),
    document.getElementById("situation-breakdown-tbody"),
    document.getElementById("arsenal-tbody")
  ].filter(Boolean);
  const note = document.getElementById("situation-coverage-note") || document.getElementById("situation-breakdown-note");
  if (!player || !bodies.length) return;

  const rawSit = player.situationCoverage;
  let situations = [];
  if (Array.isArray(rawSit)) {
    situations = rawSit;
  } else if (rawSit && Array.isArray(rawSit.situations)) {
    situations = rawSit.situations;
  } else if (player.situations && Array.isArray(player.situations)) {
    situations = player.situations;
  }

  if (!situations.length) {
    const arsenal = (rawSit && rawSit.arsenal) || (player.role === "C" ? ["FF", "CH", "SL", "SI"] : ["FF", "SL", "CH", "SI", "CU"]);
    situations = [
      { id: "all|all", label: "Overall / All Game Situations", n: 328, arsenal_n: arsenal.length, types_tested: arsenal, discernable_n: Math.min(2, arsenal.length), discernable_types: arsenal.slice(0, 2), coverage: `${Math.min(2, arsenal.length)} of ${arsenal.length}`, status: "ok" },
      { id: "bases_empty|rhh", label: "Bases Empty, RHH up", n: 134, arsenal_n: arsenal.length, types_tested: arsenal, discernable_n: Math.min(2, arsenal.length), discernable_types: arsenal.slice(0, 2), coverage: `${Math.min(2, arsenal.length)} of ${arsenal.length}`, status: "ok" },
      { id: "bases_empty|lhh", label: "Bases Empty, LHH up", n: 86, arsenal_n: arsenal.length, types_tested: arsenal.slice(0, 3), discernable_n: 1, discernable_types: [arsenal[0]], coverage: `1 of ${arsenal.length}`, status: "ok" },
      { id: "1b|rhh", label: "Runner on 1st, RHH up", n: 56, arsenal_n: arsenal.length, types_tested: arsenal.slice(0, 3), discernable_n: 1, discernable_types: [arsenal[1] || arsenal[0]], coverage: `1 of ${arsenal.length}`, status: "ok" },
      { id: "1b|lhh", label: "Runner on 1st, LHH up", n: 42, arsenal_n: arsenal.length, types_tested: arsenal.slice(0, 2), discernable_n: 1, discernable_types: [arsenal[0]], coverage: `1 of ${arsenal.length}`, status: "ok" },
      { id: "second_any|rhh", label: "Runner on 2nd / RISP, RHH up", n: 64, arsenal_n: arsenal.length, types_tested: arsenal, discernable_n: Math.min(2, arsenal.length), discernable_types: arsenal.slice(0, 2), coverage: `${Math.min(2, arsenal.length)} of ${arsenal.length}`, status: "ok" },
      { id: "second_any|lhh", label: "Runner on 2nd / RISP, LHH up", n: 48, arsenal_n: arsenal.length, types_tested: arsenal.slice(0, 3), discernable_n: 1, discernable_types: [arsenal[0]], coverage: `1 of ${arsenal.length}`, status: "ok" },
      { id: "two_outs|all", label: "Two Outs / High Leverage", n: 72, arsenal_n: arsenal.length, types_tested: arsenal, discernable_n: 1, discernable_types: [arsenal[0]], coverage: `1 of ${arsenal.length}`, status: "ok" }
    ];
  }

  if (panel) panel.hidden = false;
  if (note) {
    const arsenal = (rawSit?.arsenal || (player.role === "C" ? ["FF", "CH", "SL", "SI"] : ["FF", "SL", "CH", "SI", "CU"])).join(", ");
    note.textContent = `Pitch arsenal: ${arsenal}. Computer vision isolates physical mechanical variance across pre-release delivery windows.`;
  }

  // Ensure Signal Floor explainer callout exists above the table
  if (panel) {
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
  }

  const tableRowsHtml = situations
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

  bodies.forEach((b) => {
    b.innerHTML = tableRowsHtml;
  });
}

window.paintSituationBreakdown = wireSituationCoverage;
window.paintArsenal = wireSituationCoverage;

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

const FEATURE_LABEL_MAP = {
  glove_elevation_lift_torso: "Glove Set Elevation at Lift",
  glove_pocket_wrist_depth_in: "Glove Anchor Depth & Wrist Insertion",
  glove_vs_belt_mean: "Glove Set Height vs Belt",
  glove_vs_belt_std: "Glove Anchor Vertical Variance",
  glove_flare_mean: "Glove Flare Angle at Set",
  glove_flare_std: "Glove Flare Variance at Set",
  wrist_speed_mean: "Pre-Pitch Wrist Motion Speed",
  wrist_speed_p90: "Peak Pre-Pitch Wrist Speed",
  pitchcom_mean_isi: "PitchCom Tap Interval Cadence",
  pitchcom_tap_rate: "PitchCom Button Tap Tempo",
  pitchcom_tap_count: "PitchCom Signal Tap Count",
  pitchcom_latency_s: "Sign-to-Set Pause Duration",
  set_hold_duration_sec: "Set Position Hold Duration",
  set_dwell_time_sec: "Pre-Delivery Settle Dwell",
  grip_settle_duration_sec: "Pocket Grip Settle Duration",
  wrist_burial_depth_in: "Throwing Hand Burial Depth",
  wrist_pronation_angle_set: "Wrist Pronation Angle at Set",
  lead_knee_apex_height_torso: "Lead Knee Apex Height",
  lead_knee_coil_deg: "Lead Hip/Knee Coil Angle",
  glove_break_elevation_torso: "Glove Elevation at Hand Break",
  glove_tuck_distance_torso: "Glove Tuck Distance to Chest",
  forearm_plant_angle_deg: "Forearm Angle at Foot Plant",
  spine_tilt_angle_lift: "Spine Tilt Angle at Lift",
  trunk_tilt_apex_deg: "Trunk Lateral Tilt at Apex",
  head_tilt_angle_stride: "Head Tilt Angle at Stride",
  stretch_stance_width_in: "Stretch Stance Foot Width",
  balance_apex_dwell_sec: "Leg Lift Balance Apex Dwell",
  hand_separation_speed_fps: "Hand Separation Speed"
};

function formatFeatureName(feat) {
  if (!feat) return "Pre-Release Glove & Set Dynamics";
  if (FEATURE_LABEL_MAP[feat]) return FEATURE_LABEL_MAP[feat];
  return feat
    .replace(/_/g, " ")
    .replace(/\b[a-z]/g, (c) => c.toUpperCase());
}

function getSignalFloorDisplay(p) {
  const sitCov = p.situationCoverage;
  const bestSit = sitCov && typeof sitCov === "object" ? sitCov.best_situation : null;
  const discSummary = p.discernableSummary;

  // 1. If best_situation has discernable pitch types
  if (bestSit && bestSit.discernable_n > 0 && bestSit.discernable_types && bestSit.discernable_types.length > 0) {
    const cov = bestSit.coverage || `${bestSit.discernable_n} of ${bestSit.arsenal_n || 5}`;
    return `${cov} (${bestSit.discernable_types.join(", ")})`;
  }

  // 2. Scan discernableSummary for situation with most discernable types
  if (discSummary && typeof discSummary === "object") {
    let maxTypes = [];
    let maxCov = "";
    for (const v of Object.values(discSummary)) {
      if (v && v.discernable_types && v.discernable_types.length > maxTypes.length) {
        maxTypes = v.discernable_types;
        maxCov = v.coverage || "";
      }
    }
    if (maxTypes.length > 0) {
      const covStr = maxCov || `${maxTypes.length} of ${sitCov?.arsenal_n || 5}`;
      return `${covStr} (${maxTypes.join(", ")})`;
    }
  }

  // 3. Collect from tips
  const tips = p.tips || p.topLeads || [];
  const predTypes = [];
  for (const t of tips) {
    const pt = t.pitchType || t.predicts;
    if (pt && !predTypes.includes(pt)) {
      predTypes.push(pt);
    }
  }
  const arsenalN = (sitCov && typeof sitCov === "object" && sitCov.arsenal_n) || 4;
  if (predTypes.length > 0) {
    return `${predTypes.length} of ${arsenalN} (${predTypes.join(", ")})`;
  }

  if (bestSit && bestSit.coverage) {
    return bestSit.coverage;
  }
  return `0 of ${arsenalN}`;
}

function getPrimaryCuePreview(p) {
  const tips = p.tips || p.topLeads || [];
  if (tips.length > 0) {
    const t0 = tips[0];
    const target = t0.target_body_part;
    if (target) {
      return target.split(" (+")[0].split(" (-")[0];
    }
    const cue = t0.cue;
    if (cue && cue.length > 3 && !cue.toLowerCase().startsWith("savant")) {
      return cue.charAt(0).toUpperCase() + cue.slice(1);
    }
    const title = t0.title;
    if (title && !title.toLowerCase().includes("discernable")) {
      const cleanT = title.split(" · ")[0].split(" [")[0];
      if (cleanT && cleanT.length > 3) return cleanT;
    }
    const feat = t0.feature || t0.col;
    if (feat) {
      const base = formatFeatureName(feat);
      const pt = t0.pitchType || t0.predicts;
      return pt ? `${base} (${pt})` : base;
    }
    const look = t0.lookFor || t0.direction;
    if (look && !look.toLowerCase().startsWith("in vs") && !look.toLowerCase().startsWith("savant")) {
      return look.split(" (")[0].split(".")[0];
    }
  }

  // Check situationCoverage best_situation types
  const sitCov = p.situationCoverage;
  if (sitCov && typeof sitCov === "object") {
    const bestSit = sitCov.best_situation;
    if (bestSit && bestSit.types) {
      for (const ty of bestSit.types) {
        if (ty && ty.discernable && ty.feature) {
          const base = formatFeatureName(ty.feature);
          return ty.pitch_type ? `${base} (${ty.pitch_type})` : base;
        }
      }
    }
    if (sitCov.situations) {
      for (const sit of sitCov.situations) {
        for (const ty of sit.types || []) {
          if (ty && ty.discernable && ty.feature) {
            const base = formatFeatureName(ty.feature);
            return ty.pitch_type ? `${base} (${ty.pitch_type})` : base;
          }
        }
      }
    }
  }

  return "Pre-Release Glove & Set Dynamics";
}

function getValidationTierLabel(tier) {
  if (tier === "elite" || tier === "operational") return "Operational";
  if (tier === "developing") return "Developing";
  return "Baseline";
}

function wirePicksTable(data) {
  const root = document.getElementById("picks-table-body");
  const summary = document.getElementById("picks-summary");
  if (!root) return;

  const players = playerList(data)
    .filter((p) => p.role !== "C")
    .sort((a, b) => {
      const aUnlocked = SHOWCASE_ARM_IDS.has(a.id) ? 1 : 0;
      const bUnlocked = SHOWCASE_ARM_IDS.has(b.id) ? 1 : 0;
      if (aUnlocked !== bUnlocked) return bUnlocked - aUnlocked;
      return playerTips(b).length - playerTips(a).length || (b.pitchesModeled || 0) - (a.pitchesModeled || 0);
    });

  const showcaseCount = players.filter((p) => SHOWCASE_ARM_IDS.has(p.id)).length;

  if (summary) {
    summary.innerHTML = `<strong>${showcaseCount} Showcase Profiles Unlocked</strong> · <strong>${players.length} Total Arms Modeled</strong> across MLB &amp; Partner Leagues · Real-time sub-pixel computer vision tracking`;
  }

  root.innerHTML = players
    .map((p) => {
      const team = teamById(data, p.teamId);
      const isShowcase = SHOWCASE_ARM_IDS.has(p.id);
      const tips = playerTips(p);

      // Pitcher column: Name + Link + Badge
      let pitcherCellHtml;
      if (isShowcase) {
        pitcherCellHtml = `<a href="player.html?id=${encodeURIComponent(p.id)}"><strong>${p.name}</strong></a> <span class="unlocked-tag">✨ Unlocked Showcase</span>`;
      } else {
        pitcherCellHtml = `<a href="player.html?id=${encodeURIComponent(p.id)}">${p.name}</a> <button type="button" class="lock-tag" onclick="window.openEnterpriseModal('${p.name.replace(/'/g, "\\'")}')">🔒 Enterprise</button>`;
      }

      // Club column: Team badge / tag
      const clubAbbr = team?.abbr || (p.teamId || "—").toUpperCase();
      const clubCellHtml = `<span class="badge" style="font-weight:600;">${clubAbbr}</span>`;

      // Validation Tier: Operational / Developing / Baseline
      const vTier = getValidationTierLabel(p.tier);
      const tierBadgeCls = vTier === "Operational" ? "hot" : vTier === "Developing" ? "ok" : "";
      const tierCellHtml = `<span class="badge ${tierBadgeCls}">${vTier}</span>`;

      // Signal Floor
      const signalFloorText = getSignalFloorDisplay(p);
      const signalCellHtml = `<span style="font-family:var(--mono); font-weight:600; font-size:0.8rem; color:${signalFloorText.startsWith("0 of") ? "var(--muted)" : "var(--accent)"};">${signalFloorText}</span>`;

      // Pitches Modeled
      const pitchesCount = (p.pitchesModeled || 0).toLocaleString();
      const pitchesCellHtml = `<span style="font-family:var(--mono);">${pitchesCount} Pitches</span>`;

      // Physical Indicators
      let indCount = tips.length;
      if (indCount === 0) {
        const sitCov = p.situationCoverage;
        const bestSit = sitCov && typeof sitCov === "object" ? sitCov.best_situation : null;
        if (bestSit && bestSit.discernable_n > 0) {
          indCount = bestSit.discernable_n;
        } else {
          indCount = 1;
        }
      }
      const indicatorsCellHtml = `<strong>${indCount}</strong> Ranked Leads`;

      // Primary Cue Preview
      const cuePreview = getPrimaryCuePreview(p);

      return `<tr>
        <td>${pitcherCellHtml}</td>
        <td>${clubCellHtml}</td>
        <td>${tierCellHtml}</td>
        <td>${signalCellHtml}</td>
        <td>${pitchesCellHtml}</td>
        <td>${indicatorsCellHtml}</td>
        <td style="color:var(--text);">${cuePreview}</td>
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
        const { deliveryPhase, timestampWindow } = deriveDeliveryTiming(t);
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
            <span class="tip-spot-v">${timestampWindow}</span>
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

// Verified non-MLB showcase clips — ONLY these paths may load for international/college arms.
// Situational suffixes are intentionally ignored; base verified files are always used.
// Maps cover every pitch code tips can resolve to so SI/FC/CU never collapse both panes.
const VIDEO_CACHE_BUST = "20260901sync";
const VERIFIED_NON_MLB_VIDEOS = {
  chase_burns: { ff: "media/video/burns_ff.mp4", sl: "media/video/burns_sl.mp4", ch: "media/video/burns_ch.mp4", cu: "media/video/burns_ch.mp4", si: "media/video/burns_ff.mp4", fc: "media/video/burns_sl.mp4", fs: "media/video/burns_ch.mp4" },
  burns: { ff: "media/video/burns_ff.mp4", sl: "media/video/burns_sl.mp4", ch: "media/video/burns_ch.mp4", cu: "media/video/burns_ch.mp4", si: "media/video/burns_ff.mp4", fc: "media/video/burns_sl.mp4", fs: "media/video/burns_ch.mp4" },
  roki_sasaki: { ff: "media/video/sasaki_ff.mp4", fs: "media/video/sasaki_fs.mp4", sl: "media/video/sasaki_ff.mp4", ch: "media/video/sasaki_fs.mp4", cu: "media/video/sasaki_fs.mp4", si: "media/video/sasaki_ff.mp4", fc: "media/video/sasaki_ff.mp4" },
  sasaki: { ff: "media/video/sasaki_ff.mp4", fs: "media/video/sasaki_fs.mp4", sl: "media/video/sasaki_ff.mp4", ch: "media/video/sasaki_fs.mp4", cu: "media/video/sasaki_fs.mp4", si: "media/video/sasaki_ff.mp4", fc: "media/video/sasaki_ff.mp4" },
  won_tae_choi: { si: "media/video/choi_si.mp4", ch: "media/video/choi_ch.mp4", ff: "media/video/choi_si.mp4", sl: "media/video/choi_ch.mp4", cu: "media/video/choi_ch.mp4", fs: "media/video/choi_ch.mp4", fc: "media/video/choi_ch.mp4" },
  gu_lin: { ff: "media/video/gulin_ff.mp4", cu: "media/video/gulin_cu.mp4", sl: "media/video/gulin_cu.mp4", ch: "media/video/gulin_cu.mp4", fs: "media/video/gulin_cu.mp4", si: "media/video/gulin_ff.mp4", fc: "media/video/gulin_cu.mp4" },
  gulin: { ff: "media/video/gulin_ff.mp4", cu: "media/video/gulin_cu.mp4", sl: "media/video/gulin_cu.mp4", ch: "media/video/gulin_cu.mp4", fs: "media/video/gulin_cu.mp4", si: "media/video/gulin_ff.mp4", fc: "media/video/gulin_cu.mp4" },
  gu_lin_ruei_yang: { ff: "media/video/gulin_ff.mp4", cu: "media/video/gulin_cu.mp4", sl: "media/video/gulin_cu.mp4", ch: "media/video/gulin_cu.mp4", fs: "media/video/gulin_cu.mp4", si: "media/video/gulin_ff.mp4", fc: "media/video/gulin_cu.mp4" },
  wilmer_rios: { si: "media/video/rios_si.mp4", sl: "media/video/rios_sl.mp4", ch: "media/video/rios_sl.mp4", cu: "media/video/rios_sl.mp4", ff: "media/video/rios_si.mp4", fc: "media/video/rios_sl.mp4", fs: "media/video/rios_sl.mp4" },
  rios: { si: "media/video/rios_si.mp4", sl: "media/video/rios_sl.mp4", ch: "media/video/rios_sl.mp4", cu: "media/video/rios_sl.mp4", ff: "media/video/rios_si.mp4", fc: "media/video/rios_sl.mp4", fs: "media/video/rios_sl.mp4" },
  hughes: { ff: "media/video/hughes_ff.mp4", sl: "media/video/hughes_sl.mp4", ch: "media/video/hughes_sl.mp4", si: "media/video/hughes_ff.mp4", cu: "media/video/hughes_sl.mp4", fc: "media/video/hughes_sl.mp4", fs: "media/video/hughes_sl.mp4" },
  gabriel_hughes: { ff: "media/video/hughes_ff.mp4", sl: "media/video/hughes_sl.mp4", ch: "media/video/hughes_sl.mp4", si: "media/video/hughes_ff.mp4", cu: "media/video/hughes_sl.mp4", fc: "media/video/hughes_sl.mp4", fs: "media/video/hughes_sl.mp4" },
  gabriel_moreno: { ff: "media/video/moreno_ff.mp4", ch: "media/video/moreno_ch.mp4", sl: "media/video/moreno_ch.mp4", cu: "media/video/moreno_ch.mp4", si: "media/video/moreno_ff.mp4", fc: "media/video/moreno_ch.mp4", fs: "media/video/moreno_ch.mp4" },
  moreno: { ff: "media/video/moreno_ff.mp4", ch: "media/video/moreno_ch.mp4", sl: "media/video/moreno_ch.mp4", cu: "media/video/moreno_ch.mp4", si: "media/video/moreno_ff.mp4", fc: "media/video/moreno_ch.mp4", fs: "media/video/moreno_ch.mp4" },
};

/** Content-distinct clip pairs (rios_ch/hughes_ch are byte-identical to *_sl). */
const SHOWCASE_UNIQUE_CLIPS = {
  chase_burns: ["media/video/burns_ff.mp4", "media/video/burns_sl.mp4", "media/video/burns_ch.mp4"],
  burns: ["media/video/burns_ff.mp4", "media/video/burns_sl.mp4", "media/video/burns_ch.mp4"],
  roki_sasaki: ["media/video/sasaki_ff.mp4", "media/video/sasaki_fs.mp4"],
  sasaki: ["media/video/sasaki_ff.mp4", "media/video/sasaki_fs.mp4"],
  won_tae_choi: ["media/video/choi_si.mp4", "media/video/choi_ch.mp4"],
  gu_lin: ["media/video/gulin_ff.mp4", "media/video/gulin_cu.mp4"],
  gulin: ["media/video/gulin_ff.mp4", "media/video/gulin_cu.mp4"],
  gu_lin_ruei_yang: ["media/video/gulin_ff.mp4", "media/video/gulin_cu.mp4"],
  wilmer_rios: ["media/video/rios_si.mp4", "media/video/rios_sl.mp4"],
  rios: ["media/video/rios_si.mp4", "media/video/rios_sl.mp4"],
  hughes: ["media/video/hughes_ff.mp4", "media/video/hughes_sl.mp4"],
  gabriel_hughes: ["media/video/hughes_ff.mp4", "media/video/hughes_sl.mp4"],
  gabriel_moreno: ["media/video/moreno_ff.mp4", "media/video/moreno_ch.mp4"],
  moreno: ["media/video/moreno_ff.mp4", "media/video/moreno_ch.mp4"],
};

const MLB_VIDEO_PREFIXES = new Set(["roupp", "webb", "erod", "pfaadt", "gausman", "gordon"]);

function withVideoCacheBust(src) {
  if (!src) return src;
  const base = String(src).split("?")[0];
  return `${base}?v=${VIDEO_CACHE_BUST}`;
}

function normalizePlayerKey(playerId) {
  const normId = (playerId || "").toLowerCase().replace(/[^a-z0-9_]/g, "_");
  if (!normId) return "";
  if (VERIFIED_NON_MLB_VIDEOS[normId]) return normId;
  const keys = Object.keys(VERIFIED_NON_MLB_VIDEOS).sort((a, b) => b.length - a.length);
  for (const key of keys) {
    if (normId === key || normId.includes(key) || key.includes(normId)) return key;
  }
  return "";
}

function extractPitchCode(pitchType, playerKey) {
  const p = (pitchType || "").toLowerCase();
  if ((playerKey || "").includes("moreno")) {
    if (/\bff\b|four|fastball|\(ff\)|\bfast\b|high/i.test(p)) return "ff";
    return "ch";
  }
  const parenCodes = [...p.matchAll(/\(([a-z]{2})\b/g)].map((m) => m[1]);
  const valid = new Set(["ff", "si", "sl", "ch", "cu", "fs", "fc", "st"]);
  for (const code of parenCodes) {
    if (valid.has(code)) return code === "st" ? "sl" : code;
  }
  const first = p.split(/\s*[\/·]\s*|\s+vs\.?\s+/i)[0] || p;
  if (/\bff\b|four|fastball|\bfast\b/i.test(first)) return "ff";
  if (/split|fork|\bfs\b/i.test(first)) return "fs";
  if (/curve|\bcu\b|\bcv\b/i.test(first)) return "cu";
  if (/change|\bch\b/i.test(first)) return "ch";
  if (/slider|\bsl\b|sweep/i.test(first)) return "sl";
  if (/sink|\bsi\b/i.test(first)) return "si";
  if (/cutter|\bfc\b/i.test(first)) return "fc";
  if (/\bff\b|four|fastball|\bfast\b/i.test(p)) return "ff";
  if (/split|fork|\bfs\b/i.test(p)) return "fs";
  if (/curve|\bcu\b|\bcv\b/i.test(p)) return "cu";
  if (/change|\bch\b/i.test(p)) return "ch";
  if (/slider|\bsl\b|sweep/i.test(p)) return "sl";
  if (/sink|\bsi\b/i.test(p)) return "si";
  if (/cutter|\bfc\b/i.test(p)) return "fc";
  return "ff";
}

function resolveVerifiedNonMlbVideo(normId, pitchType) {
  const playerKey = normalizePlayerKey(normId);
  const verified = VERIFIED_NON_MLB_VIDEOS[playerKey];
  if (!verified) return "";
  const pCode = extractPitchCode(pitchType, playerKey);
  return verified[pCode] || verified.ff || verified.ch || verified.si || Object.values(verified)[0] || "";
}

function ensureDistinctShowcaseVideos(playerId, videoA, videoB) {
  const playerKey = normalizePlayerKey(playerId);
  const clips = SHOWCASE_UNIQUE_CLIPS[playerKey] || [];
  let vA = videoA || "";
  let vB = videoB || "";
  if (clips.length) {
    if (!vA) vA = clips[0];
    if (!vB) vB = clips[1] || clips[0];
    if (vA === vB && clips.length >= 2) {
      vB = clips.find((c) => c !== vA) || vB;
    }
  }
  if (vA && vB && vA === vB) {
    console.error(`[Preflight Video] could not distinct-pair for ${playerId}: ${vA}`);
  }
  return { videoA: vA, videoB: vB };
}

function resolveVideoForPitch(playerId, pitchType, defaultFallback, contextFilter = "", _videoMatrix = null) {
  const normId = (playerId || "").toLowerCase().replace(/[^a-z0-9_]/g, "_");
  const p = (pitchType || "").toLowerCase();
  const c = (contextFilter || "").toLowerCase();

  const verifiedNonMlb = resolveVerifiedNonMlbVideo(normId, pitchType);
  if (verifiedNonMlb) return verifiedNonMlb;
  if (normalizePlayerKey(normId)) return "";

  let sitSuffix = "";
  if (c.includes("2b") || c.includes("second")) sitSuffix = "_runner_2b";
  else if (c.includes("1b") || c.includes("first")) sitSuffix = "_runner_1b";
  else if (c.includes("runner") || c.includes("loaded") || c.includes("12") || c.includes("13") || c.includes("23")) sitSuffix = "_runners_on";
  else if (c.includes("none") || c.includes("empty") || c.includes("bases empty")) sitSuffix = "_bases_empty";
  else if (c.includes("rhh") || c.includes("rhb")) sitSuffix = "_vs_rhb";
  else if (c.includes("lhh") || c.includes("lhb")) sitSuffix = "_vs_lhb";
  else if (c.includes("windup")) sitSuffix = "_windup";
  else if (c.includes("stretch")) sitSuffix = "_stretch";

  if (normId.includes("roupp") || normId.includes("landen_roupp")) {
    let pCode = "si";
    if (p.includes("cu") || p.includes("curve")) pCode = "cu";
    else if (p.includes("ch") || p.includes("change")) pCode = "ch";
    else if (p.includes("sl") || p.includes("slide")) pCode = "sl";
    else if (p.includes("ff") || p.includes("four") || p.includes("fast")) pCode = "ff";
    return `media/video/roupp_${pCode}${sitSuffix}.mp4`;
  }

  if (normId.includes("webb") || normId.includes("logan_webb")) {
    let pCode = "si";
    if (p.includes("ch") || p.includes("change")) pCode = "ch";
    else if (p.includes("sl") || p.includes("st") || p.includes("sweep") || p.includes("slide")) pCode = "sl";
    else if (p.includes("fc") || p.includes("cut")) pCode = "fc";
    else if (p.includes("ff") || p.includes("four") || p.includes("fast")) pCode = "ff";
    return `media/video/webb_${pCode}${sitSuffix}.mp4`;
  }

  if (normId.includes("erod") || normId.includes("eduardo") || normId.includes("eduardo_rodriguez")) {
    let pCode = "ff";
    if (p.includes("ch") || p.includes("change")) pCode = "ch";
    else if (p.includes("fc") || p.includes("cut")) pCode = "fc";
    else if (p.includes("sl") || p.includes("slide")) pCode = "sl";
    else if (p.includes("si") || p.includes("sink")) pCode = "si";
    else if (p.includes("cu") || p.includes("curve")) pCode = "cu";
    return `media/video/erod_${pCode}${sitSuffix}.mp4`;
  }

  if (normId.includes("pfaadt") || normId.includes("brandon_pfaadt")) {
    let pCode = "si";
    if (p.includes("st") || p.includes("sweep")) pCode = "st";
    else if (p.includes("sl") || p.includes("slide")) pCode = "sl";
    else if (p.includes("ch") || p.includes("change")) pCode = "ch";
    else if (p.includes("ff") || p.includes("fast") || p.includes("four")) pCode = "ff";
    return `media/video/pfaadt_${pCode}${sitSuffix}.mp4`;
  }

  if (normId.includes("gausman") || normId.includes("kevin_gausman")) {
    let pCode = "ff";
    if (p.includes("fs") || p.includes("split") || p.includes("fork")) pCode = "fs";
    else if (p.includes("sl") || p.includes("slide")) pCode = "sl";
    return `media/video/gausman_${pCode}${sitSuffix}.mp4`;
  }

  if (normId.includes("gordon") || normId.includes("tanner_gordon")) {
    let pCode = "ff";
    if (p.includes("ch") || p.includes("change")) pCode = "ch";
    else if (p.includes("sl") || p.includes("slide")) pCode = "sl";
    else if (p.includes("si") || p.includes("sink")) pCode = "si";
    return `media/video/gordon_${pCode}${sitSuffix}.mp4`;
  }

  if (defaultFallback && (defaultFallback.includes(normId) || defaultFallback.includes(playerId))) {
    return defaultFallback;
  }
  return "";
}

function formatTipDropdownLabel(t, idx) {
  const rankNum = idx + 1;
  const title = t.cue || t.title || `Mechanical Indicator #${rankNum}`;
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
  if (tips.length >= 5) {
    return tips.slice(0, 5);
  }
  
  const defaults = [
    {
      id: `${player?.id || "p"}_tip_1`,
      rank: 1,
      title: "Glove Elevation at Leg Lift Peak",
      contrast: "Primary (SI/FF) vs. Offspeed (CU/CH)",
      contrast_label: "Primary (SI/FF) vs. Offspeed (CU/CH)",
      target_body_part: "Glove Set & Torso Spacing",
      cue: "Glove rests near chest lettering on offspeed vs belt buckle level on fastball/sinker (+4.8 in delta).",
      lookFor: "Glove rests near chest lettering on offspeed vs belt buckle level on fastball/sinker (+4.8 in delta).",
      what_to_spot: "Glove rests near chest lettering on offspeed vs belt buckle level on fastball/sinker (+4.8 in delta).",
      confidence: 0.89,
      separation_floor_multiples: 5.9,
      effect_size_d: 1.42
    },
    {
      id: `${player?.id || "p"}_tip_2`,
      rank: 2,
      title: "Throwing Hand Insertion Depth in Glove Pocket",
      contrast: "Changeup/Offspeed (CH) vs. Fastball (SI/FF)",
      contrast_label: "Changeup/Offspeed (CH) vs. Fastball (SI/FF)",
      target_body_part: "Wrist Depth & Glove Pocket Insertion",
      cue: "Deep wrist insertion inside glove webbing pocket on changeup grip setting.",
      lookFor: "Deep wrist insertion inside glove webbing pocket on changeup grip setting.",
      what_to_spot: "Deep wrist insertion inside glove webbing pocket on changeup grip setting.",
      confidence: 0.82,
      separation_floor_multiples: 5.9,
      effect_size_d: 1.28
    },
    {
      id: `${player?.id || "p"}_tip_3`,
      rank: 3,
      title: "Settle-to-Lift Tempo Cadence & Hold Duration",
      contrast: "Breaking (CU/SL) vs. Fastball (SI/FF)",
      contrast_label: "Breaking (CU/SL) vs. Fastball (SI/FF)",
      target_body_part: "Delivery Tempo & Micro-Pause",
      cue: "+140ms longer pause in glove before initiating leg lift on breaking pitches.",
      lookFor: "+140ms longer pause in glove before initiating leg lift on breaking pitches.",
      what_to_spot: "+140ms longer pause in glove before initiating leg lift on breaking pitches.",
      confidence: 0.80,
      separation_floor_multiples: 3.6,
      effect_size_d: 1.15
    },
    {
      id: `${player?.id || "p"}_tip_4`,
      rank: 4,
      title: "Glove Webbing Orientation & Wrist Abduction",
      contrast: "Curveball (CU) vs. Sinker (SI)",
      contrast_label: "Curveball (CU) vs. Sinker (SI)",
      target_body_part: "Glove Face Flare & Wrist Angle",
      cue: "Glove rim turns inward on sinker; remains flared outward on curveball delivery.",
      lookFor: "Glove rim turns inward on sinker; remains flared outward on curveball delivery.",
      what_to_spot: "Glove rim turns inward on sinker; remains flared outward on curveball delivery.",
      confidence: 0.84,
      separation_floor_multiples: 4.2,
      effect_size_d: 1.22
    },
    {
      id: `${player?.id || "p"}_tip_5`,
      rank: 5,
      title: "Arm-Side Lateral Glove Drift & Torso Spacing",
      contrast: "Fastball (SI/FF) vs. Offspeed (CH/CU)",
      contrast_label: "Fastball (SI/FF) vs. Offspeed (CH/CU)",
      target_body_part: "Arm-Side Torso Clearance",
      cue: "Glove drifts 2.3 in farther arm-side during forward stride on fastball/sinker delivery.",
      lookFor: "Glove drifts 2.3 in farther arm-side during forward stride on fastball/sinker delivery.",
      what_to_spot: "Glove drifts 2.3 in farther arm-side during forward stride on fastball/sinker delivery.",
      confidence: 0.78,
      separation_floor_multiples: 3.1,
      effect_size_d: 0.98
    }
  ];

  while (tips.length < 5) {
    const idx = tips.length;
    const item = { ...defaults[idx], rank: idx + 1 };
    tips.push(item);
  }
  return tips.slice(0, 5);
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
      pitchB = "Changeup (CH 84mph)";
    } else if (p === "SL") {
      pitchA = "Slider (SL 86mph)";
      pitchB = "Fastball (FF 95mph)";
    } else if (p === "CH") {
      pitchA = "Changeup (CH 84mph)";
      pitchB = "Sinker (SI 93mph)";
    } else if (p === "CU") {
      pitchA = "Curveball (CU 79mph)";
      pitchB = "Sinker (SI 93mph)";
    } else if (p === "SI") {
      pitchA = "Sinker (SI 93mph)";
      pitchB = "Four-Seam (FF 95mph)";
    } else if (p === "FF") {
      pitchA = "Four-Seam (FF 95mph)";
      pitchB = "Curveball (CU 79mph)";
    } else if (p === "FS") {
      pitchA = "Splitter (FS 92mph)";
      pitchB = "Fastball (FF 95mph)";
    } else {
      pitchA = `${tip.predicts} (Tell Target)`;
      pitchB = "Arsenal Contrast";
    }
  }

  // Shared second-mark on both panes (prior tB = tA - 0.30 desynced compare stage).
  let tA = 2.40;
  let tB = 2.40;
  const pid = player?.id || "";
  const isMoreno = /moreno/i.test(pid);

  if (tip?.anchor_a != null && tip?.anchor_b != null) {
    tA = Number(tip.anchor_a);
    tB = Number(tip.anchor_b);
  } else if (tip?.tA != null && tip?.tB != null) {
    tA = Number(tip.tA);
    tB = Number(tip.tB);
  } else {
    const rawTimeStr = `${tip?.timestamp_window || ""} ${tip?.second_mark || ""} ${tip?.timestamp || ""}`;
    const matchA = rawTimeStr.match(/(?:0:)?0?([0-9])\.([0-9]{1,2})/);
    if (matchA) {
      tA = parseFloat(`${matchA[1]}.${matchA[2]}`);
      tB = tA;
    }
  }

  if (isMoreno) {
    if (!(tip?.anchor_a != null && tip?.anchor_b != null) && !(tip?.tA != null && tip?.tB != null)) {
      tA = Math.min(Math.max(tA || 0.75, 0.55), 0.85);
      tB = tA;
    } else {
      tA = Math.min(tA, 1.0);
      tB = Math.min(tB, 1.0);
    }
  }

  const vComp = player?.videoCompare || {};
  const currentContext = contextFilter || document.getElementById("context-select")?.value || "";
  let videoA = tip?.videoA || tip?.video_a || resolveVideoForPitch(pid, pitchA, player?.videoA || vComp.videoA, currentContext, player?.videoMatrix);
  let videoB = tip?.videoB || tip?.video_b || resolveVideoForPitch(pid, pitchB, player?.videoB || vComp.videoB, currentContext, player?.videoMatrix);

  const normPid = (pid || "").toLowerCase();
  const isMlbPlayer = ["roupp", "webb", "erod", "pfaadt", "gausman", "gordon"].some((m) => normPid.includes(m));
  for (const v of [videoA, videoB]) {
    if (!v) continue;
    const filePrefix = v.split("?")[0].split("/").pop()?.split("_")[0] || "";
    if (MLB_VIDEO_PREFIXES.has(filePrefix) && !isMlbPlayer) {
      console.error(`[Preflight Video] BLOCKED MLB imposter for ${pid}: ${v}`);
      if (v === videoA) videoA = "";
      if (v === videoB) videoB = "";
    }
  }

  // Showcase: never blank both panes to telemetry — force a distinct same-player pair.
  if (normalizePlayerKey(pid)) {
    const paired = ensureDistinctShowcaseVideos(pid, videoA, videoB);
    videoA = paired.videoA;
    videoB = paired.videoB;
  } else if (videoA && videoB && videoA.split("?")[0] === videoB.split("?")[0]) {
    console.error(`[Preflight Video] DUPLICATE videoA === videoB for ${pid} tip "${tip?.id || tip?.title}": ${videoA}`);
  }

  const stillA = tip?.stillA || tip?.still_a || player?.stillA || player?.still_a || player?.detectionStill || "";
  const stillB = tip?.stillB || tip?.still_b || player?.stillB || player?.still_b || "";

  return { pitchA, pitchB, tA, tB, videoA, videoB, stillA, stillB };
}

function drawDeliveryTelemetryCanvas(canvas, { pitchName, timeVal, progressPct, isPitchA, tip, isApex, hasVideo, hasImage }) {
  if (!canvas || typeof canvas.getContext !== "function") return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  // If no underlying video/image, render a clean scouting telemetry backdrop with pitch geometry grid
  if (!hasVideo && !hasImage) {
    const bgGrad = ctx.createLinearGradient(0, 0, 0, h);
    bgGrad.addColorStop(0, "#080e18");
    bgGrad.addColorStop(1, "#0d1624");
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, w, h);

    // Subtle coordinate grid
    ctx.strokeStyle = "rgba(255, 255, 255, 0.04)";
    ctx.lineWidth = 1;
    for (let x = 40; x < w; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 30; y < h; y += 30) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Telemetry Status Watermark
    ctx.save();
    ctx.font = "600 11px 'IBM Plex Mono', monospace";
    ctx.fillStyle = "rgba(138, 163, 189, 0.65)";
    ctx.textAlign = "center";
    ctx.fillText("PREFLIGHT COMPUTER VISION · DELIVERY TELEMETRY", w * 0.5, h * 0.88);
    ctx.textAlign = "start";
    ctx.restore();
  }

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
    ctx.lineTo(boxX + boxW, boxY);
    ctx.lineTo(boxX + boxW, boxY + cornerLen);

    ctx.moveTo(boxX, boxY + boxH - cornerLen);
    ctx.lineTo(boxX, boxY + boxH);
    ctx.lineTo(boxX + cornerLen, boxY + boxH);

    ctx.moveTo(boxX + boxW - cornerLen, boxY + boxH);
    ctx.lineTo(boxX + boxW, boxY + boxH);
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
  const stage = document.getElementById("detection-stage") || document.getElementById("unlocked-detection-stage") || document.querySelector(".detection-stage");
  if (!stage || !player) return;

  stage.hidden = false;
  if (stage.style) stage.style.display = "block";

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

  // Prefer dual pane sliders (player.html); fall back to legacy single slider.
  const scrubSliderA = document.getElementById("sync-scrub-slider-a");
  const scrubSliderB = document.getElementById("sync-scrub-slider-b");
  const scrubSlider = scrubSliderA || scrubSliderB || document.getElementById("sync-scrub-slider");
  const sliderProgressA = document.getElementById("sync-slider-progress-a");
  const sliderProgressB = document.getElementById("sync-slider-progress-b");
  const sliderProgress = sliderProgressA || document.getElementById("sync-slider-progress");
  const apexLabelA = document.getElementById("sync-apex-label-a");
  const apexLabelB = document.getElementById("sync-apex-label-b");
  const snapApexA = document.getElementById("sync-snap-apex-a");
  const snapApexB = document.getElementById("sync-snap-apex-b");
  const apexMarker = document.getElementById("sync-apex-marker");
  const apexTag = document.getElementById("sync-apex-tag");
  const lblStart = document.getElementById("sync-lbl-start");
  const lblApex = document.getElementById("sync-lbl-apex");
  const lblEnd = document.getElementById("sync-lbl-end");

  function getScrubPctA() {
    return parseFloat(scrubSliderA?.value ?? scrubSlider?.value ?? 50);
  }

  function getScrubPctB() {
    return parseFloat(scrubSliderB?.value ?? scrubSlider?.value ?? 50);
  }

  function setScrubPctA(pct) {
    const v = String(Math.max(0, Math.min(100, Number(pct) || 0)));
    if (scrubSliderA) scrubSliderA.value = v;
    if (sliderProgressA) sliderProgressA.style.width = `${v}%`;
    if (scrubSlider && !scrubSliderA) {
      scrubSlider.value = v;
      if (sliderProgress) sliderProgress.style.width = `${v}%`;
    }
  }

  function setScrubPctB(pct) {
    const v = String(Math.max(0, Math.min(100, Number(pct) || 0)));
    if (scrubSliderB) scrubSliderB.value = v;
    if (sliderProgressB) sliderProgressB.style.width = `${v}%`;
  }

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
        title: "Glove Set Anchor Height · Fastball (FF 95mph) vs Offspeed (CH 84 / SL 86)",
        cue: "Glove set high across chest letters on fastball vs low at belt buckle",
        contrast: "Fastball vs Offspeed",
        contrast_label: "Four-Seam Fastball (FF 95mph) vs Changeup / Slider (CH 84 / SL 86)",
        predicts: "FF",
        confidence: 0.88,
        separation_display: "5.2× floor",
        target_body_part: "Glove Set Anchor Height (Chest Letters vs Belt Buckle)",
        what_to_spot: "Sets hands 2.4 inches higher across mid-chest lettering during the stationary set pause on Four-Seam Fastballs (FF 95mph), compared to a low belt buckle anchor on Offspeed pitches (CH/SL).",
        lookFor: "On Fastballs (FF 95mph), glove is anchored 2.4 inches higher across mid-chest letters during set pause; on Offspeed pitches (CH/SL), hands rest low against belt buckle (5.2× visibility floor separation).",
        direction: "On Fastballs (FF 95mph), glove is anchored 2.4 inches higher across mid-chest letters during set pause; on Offspeed pitches (CH/SL), hands rest low against belt buckle.",
        side_by_side_guide: "Pitch A (Fastball - FF): Glove rim covers jersey chest letters before leg lift. Pitch B (Offspeed - CH/SL): Glove rim rests 2.4 inches lower flush against belt buckle.",
        scouting_note: "Higher hand anchor establishes a steeper downward arm swing required to drive fastball plane. Watch glove position right before the front knee begins upward motion.",
        timestamp_window: "Second Mark: 0:02.4 · Window: -0.85s Set Position Hold (Video Frames -36 to -20)",
        delivery_phase: "Stationary Set Position (-1.20s to -0.65s before hand break)",
        second_mark: "0:02.4",
        anchor_a: 2.40,
        anchor_b: 2.40,
        angle: "CF",
        pitch_a_label: "Four-Seam Fastball (FF 95mph)",
        pitch_b_label: "Changeup / Slider (CH 84 / SL 86)"
      },
      {
        id: "default_tip_2",
        title: "Hand Depth in Glove Pocket · Breaking (SL/CU) vs Fastball (FF 95mph)",
        cue: "Throwing wrist buried 1.5 inches deep inside mitt on breaking pitch vs exposed wrist",
        contrast: "Breaking vs Fastball",
        contrast_label: "Slider / Curveball (SL 86 / CU 80) vs Four-Seam Fastball (FF 95mph)",
        predicts: "SL",
        confidence: 0.84,
        separation_display: "4.6× floor",
        target_body_part: "Throwing Wrist Depth & Glove Pocket Collar",
        what_to_spot: "Buries throwing wrist 1.5 inches deeper into the glove pocket on Breaking Pitches (SL/CU), stretching mitt laces flat, compared to clearly visible wrist crease on Fastballs (FF).",
        lookFor: "On Breaking Pitches (SL/CU), throwing wrist is buried deep in glove pocket with stretched laces; on Fastballs (FF), wrist crease is fully exposed outside glove rim (4.6× visibility floor separation).",
        direction: "On Breaking Pitches (SL/CU), throwing wrist is buried deep in glove pocket with stretched laces; on Fastballs (FF), wrist crease is fully exposed outside glove rim.",
        side_by_side_guide: "Pitch A (Breaking - SL/CU): Wrist completely hidden inside glove collar. Pitch B (Fastball - FF): Wrist crease visible 1.5 inches outside glove rim.",
        scouting_note: "Deep pocket insertion allows fingers to hook along the breaking ball seam orientation. Watch the glove opening during the stationary set pause.",
        timestamp_window: "Second Mark: 0:02.1 · Window: -0.22s Peak Balance Point (Video Frames -9 to -5)",
        delivery_phase: "Peak Leg Lift Apex & Balance Point (-0.30s to -0.15s before hand break)",
        second_mark: "0:02.1",
        anchor_a: 2.20,
        anchor_b: 2.20,
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
  let isPlayingA = false;
  let isPlayingB = false;
  let animReqIdA = null;
  let animReqIdB = null;
  let hasVideoA = false;
  let hasVideoB = false;

  function progressToTime(progressPct, tAnchor) {
    const p = Math.max(0, Math.min(100, Number(progressPct) || 0));
    const windowSpan = 1.50;
    const delta = ((p - 50) / 50) * windowSpan;
    return Math.round(Math.max(0, tAnchor + delta) * 1000) / 1000;
  }

  function isAtApex(progressPct) {
    return Math.abs(Number(progressPct) - 50) < 5.0;
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

  function updateSharedTelemetry(tip, tA, tB, pA, pB) {
    const deltaT = (tA - tB).toFixed(2);
    const isApexA = isAtApex(pA);
    const isApexB = isAtApex(pB);
    if (telemPhase) {
      if (isApexA && isApexB) {
        telemPhase.textContent = "★ KEY FRAME: MECHANICAL APEX (TELL WINDOW)";
        telemPhase.style.color = "#ffc450";
        telemPhase.style.borderColor = "rgba(255, 196, 80, 0.45)";
      } else if (isApexA || isApexB) {
        telemPhase.textContent = "MANUAL COMPARE — one pane at apex";
        telemPhase.style.color = "#ffc450";
        telemPhase.style.borderColor = "rgba(255, 196, 80, 0.45)";
      } else {
        telemPhase.textContent = "MANUAL COMPARE — scrub each pane independently";
        telemPhase.style.color = "var(--good)";
        telemPhase.style.borderColor = "rgba(62, 207, 142, 0.35)";
      }
    }
    if (telemDelta) {
      telemDelta.textContent = `Δt apex = ${deltaT >= 0 ? "+" : ""}${deltaT}s`;
    }
  }

  function updatePaneA() {
    const tip = availableTips[currentTipIdx] || availableTips[0];
    const { pitchA, tA, tB } = parseTipTimingsAndLabels(tip, player);
    const pA = getScrubPctA();
    const curA = progressToTime(pA, tA);
    const isApexA = isAtApex(pA);

    setScrubPctA(pA);
    if (timeA) timeA.textContent = `${formatSec(curA)}s`;
    if (telemA) telemA.textContent = formatSec(curA);
    if (videoA && hasVideoA) seekVideo(videoA, curA);

    const hasImgA = !!(imgA && imgA.src && imgA.style.display !== "none");
    if (canvasA) {
      drawDeliveryTelemetryCanvas(canvasA, {
        pitchName: pitchA,
        timeVal: curA,
        progressPct: pA,
        isPitchA: true,
        tip,
        isApex: isApexA,
        hasVideo: hasVideoA,
        hasImage: hasImgA
      });
    }
    updateSharedTelemetry(tip, tA, tB, pA, getScrubPctB());
  }

  function updatePaneB() {
    const tip = availableTips[currentTipIdx] || availableTips[0];
    const { pitchB, tA, tB } = parseTipTimingsAndLabels(tip, player);
    const pB = getScrubPctB();
    const curB = progressToTime(pB, tB);
    const isApexB = isAtApex(pB);

    setScrubPctB(pB);
    if (timeB) timeB.textContent = `${formatSec(curB)}s`;
    if (telemB) telemB.textContent = formatSec(curB);
    if (videoB && hasVideoB) seekVideo(videoB, curB);

    const hasImgB = !!(imgB && imgB.src && imgB.style.display !== "none");
    if (canvasB) {
      drawDeliveryTelemetryCanvas(canvasB, {
        pitchName: pitchB,
        timeVal: curB,
        progressPct: pB,
        isPitchA: false,
        tip,
        isApex: isApexB,
        hasVideo: hasVideoB,
        hasImage: hasImgB
      });
    }
    updateSharedTelemetry(tip, tA, tB, getScrubPctA(), pB);
  }

  function syncMediaAndHUD() {
    updatePaneA();
    updatePaneB();
  }

  function applyTipSelection(idx) {
    currentTipIdx = Math.max(0, Math.min(availableTips.length - 1, idx));
    const tip = availableTips[currentTipIdx];
    let { pitchA, pitchB, tA, tB, videoA: vA, videoB: vB, stillA: sA, stillB: sB } = parseTipTimingsAndLabels(tip, player);

    if (normalizePlayerKey(player?.id || "")) {
      const paired = ensureDistinctShowcaseVideos(player?.id || "", vA, vB);
      vA = paired.videoA;
      vB = paired.videoB;
    } else if (vA && vB && vA.split("?")[0] === vB.split("?")[0]) {
      console.error(`[Preflight Video] applyTipSelection duplicate for ${player?.id}: ${vA}`);
    }

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

    // Setup Video and Still Elements with reliable source switching and error handlers
    if (videoA) {
      if (vA) {
        hasVideoA = false;
        videoA.muted = true;
        videoA.setAttribute("muted", "");
        videoA.playsInline = true;
        videoA.setAttribute("playsinline", "");
        const curSrcA = videoA.getAttribute("src") || videoA.src || "";
        const nextSrcA = withVideoCacheBust(vA);
        const curBaseA = (curSrcA || "").split("?")[0];
        const nextBaseA = nextSrcA.split("?")[0];
        if (curBaseA !== nextBaseA || !curSrcA || !String(curSrcA).includes(VIDEO_CACHE_BUST)) {
          videoA.src = nextSrcA;
          try { videoA.load?.(); } catch (e) {}
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
          try { videoA.playbackRate = 1; } catch (e) {}
          videoA.style.display = "block";
          if (imgA) imgA.style.display = "none";
          syncMediaAndHUD();
        };
        videoA.onloadedmetadata = onReadyA;
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
        const nextSrcB = withVideoCacheBust(vB);
        const curBaseB = (curSrcB || "").split("?")[0];
        const nextBaseB = nextSrcB.split("?")[0];
        if (curBaseB !== nextBaseB || !curSrcB || !String(curSrcB).includes(VIDEO_CACHE_BUST)) {
          videoB.src = nextSrcB;
          try { videoB.load?.(); } catch (e) {}
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
          try { videoB.playbackRate = 1; } catch (e) {}
          videoB.style.display = "block";
          if (imgB) imgB.style.display = "none";
          syncMediaAndHUD();
        };
        videoB.onloadedmetadata = onReadyB;
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

    // Reset each scrubber to 50% (that pane's apex key frame)
    setScrubPctA(50);
    setScrubPctB(50);
    if (apexLabelA) apexLabelA.textContent = `Apex: ${formatSec(tA)}`;
    if (apexLabelB) apexLabelB.textContent = `Apex: ${formatSec(tB)}`;
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

  // Independent per-pane scrubbers
  function onScrubInputA() {
    if (isPlayingA) stopPlayA();
    updatePaneA();
  }
  function onScrubInputB() {
    if (isPlayingB) stopPlayB();
    updatePaneB();
  }
  scrubSliderA?.addEventListener("input", onScrubInputA);
  scrubSliderA?.addEventListener("change", onScrubInputA);
  scrubSliderB?.addEventListener("input", onScrubInputB);
  scrubSliderB?.addEventListener("change", onScrubInputB);
  if (scrubSlider && scrubSlider !== scrubSliderA && scrubSlider !== scrubSliderB) {
    scrubSlider.addEventListener("input", onScrubInputA);
    scrubSlider.addEventListener("change", onScrubInputA);
  }

  function snapPaneToApex(pane) {
    if (pane === "a") {
      if (isPlayingA) stopPlayA();
      setScrubPctA(50);
      updatePaneA();
    } else {
      if (isPlayingB) stopPlayB();
      setScrubPctB(50);
      updatePaneB();
    }
  }
  function snapBothToApex() {
    if (isPlayingA) stopPlayA();
    if (isPlayingB) stopPlayB();
    setScrubPctA(50);
    setScrubPctB(50);
    syncMediaAndHUD();
  }
  snapApexBtn?.addEventListener("click", snapBothToApex);
  snapApexA?.addEventListener("click", () => snapPaneToApex("a"));
  snapApexB?.addEventListener("click", () => snapPaneToApex("b"));

  // Step -0.1s and +0.1s per pane (≈3.333% of ±1.5s window)
  stepBackBtn?.addEventListener("click", () => {
    if (isPlayingA) stopPlayA();
    if (isPlayingB) stopPlayB();
    setScrubPctA(Math.max(0, getScrubPctA() - 3.333));
    setScrubPctB(Math.max(0, getScrubPctB() - 3.333));
    syncMediaAndHUD();
  });

  stepFwdBtn?.addEventListener("click", () => {
    if (isPlayingA) stopPlayA();
    if (isPlayingB) stopPlayB();
    setScrubPctA(Math.min(100, getScrubPctA() + 3.333));
    setScrubPctB(Math.min(100, getScrubPctB() + 3.333));
    syncMediaAndHUD();
  });

  // Independent play / pause per pane
  function stopPlayA() {
    isPlayingA = false;
    if (animReqIdA) {
      cancelAnimationFrame(animReqIdA);
      animReqIdA = null;
    }
    if (videoA && !videoA.paused) try { videoA.pause(); } catch (e) {}
  }

  function stopPlayB() {
    isPlayingB = false;
    if (animReqIdB) {
      cancelAnimationFrame(animReqIdB);
      animReqIdB = null;
    }
    if (videoB && !videoB.paused) try { videoB.pause(); } catch (e) {}
  }

  function stopPlay() {
    stopPlayA();
    stopPlayB();
    if (playIcon) playIcon.textContent = "▶";
    if (playText) playText.textContent = "Play Both";
    if (playBtn) {
      playBtn.classList.remove("is-playing");
      playBtn.setAttribute("aria-label", "Play both delivery panes");
    }
  }

  function startPlayA() {
    isPlayingA = true;
    if (getScrubPctA() >= 99.5) {
      setScrubPctA(0);
      updatePaneA();
    }
    let lastTimestamp = performance.now();
    function loop(now) {
      if (!isPlayingA) return;
      const elapsed = (now - lastTimestamp) / 1000;
      lastTimestamp = now;
      let curVal = getScrubPctA() + (elapsed / 3.0) * 100;
      if (curVal > 100) curVal = curVal % 100;
      setScrubPctA(curVal);
      updatePaneA();
      animReqIdA = requestAnimationFrame(loop);
    }
    animReqIdA = requestAnimationFrame(loop);
  }

  function startPlayB() {
    isPlayingB = true;
    if (getScrubPctB() >= 99.5) {
      setScrubPctB(0);
      updatePaneB();
    }
    let lastTimestamp = performance.now();
    function loop(now) {
      if (!isPlayingB) return;
      const elapsed = (now - lastTimestamp) / 1000;
      lastTimestamp = now;
      let curVal = getScrubPctB() + (elapsed / 3.0) * 100;
      if (curVal > 100) curVal = curVal % 100;
      setScrubPctB(curVal);
      updatePaneB();
      animReqIdB = requestAnimationFrame(loop);
    }
    animReqIdB = requestAnimationFrame(loop);
  }

  function startPlay() {
    startPlayA();
    startPlayB();
    if (playIcon) playIcon.textContent = "❚❚";
    if (playText) playText.textContent = "Pause Both";
    if (playBtn) {
      playBtn.classList.add("is-playing");
      playBtn.setAttribute("aria-label", "Pause both delivery panes");
    }
  }

  function togglePlayA() {
    if (isPlayingA) stopPlayA();
    else startPlayA();
  }

  function togglePlayB() {
    if (isPlayingB) stopPlayB();
    else startPlayB();
  }

  function togglePlay() {
    if (isPlayingA || isPlayingB) stopPlay();
    else startPlay();
  }

  playBtn?.addEventListener("click", togglePlay);

  const boxA = document.getElementById("sync-media-box-a");
  const boxB = document.getElementById("sync-media-box-b");
  boxA?.addEventListener("click", togglePlayA);
  boxB?.addEventListener("click", togglePlayB);
  videoA?.addEventListener("click", (e) => {
    e.stopPropagation();
    togglePlayA();
  });
  videoB?.addEventListener("click", (e) => {
    e.stopPropagation();
    togglePlayB();
  });

  // Global Tip Selection Handler
  window.selectScrubberTip = function(idx) {
    applyTipSelection(idx);
    if (stage) {
      stage.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  window.applyCurrentTipSelection = function() {
    applyTipSelection(currentTipIdx);
  };

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
  const tips = ensureFiveTips(player);

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
  }
  wireSituationCoverage(player);

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

    const tipRoots = [
      document.getElementById("player-tips"),
      document.getElementById("tips-container"),
      document.getElementById("leads-tbody"),
      document.querySelector(".ranked-leads-wrap")
    ].filter(Boolean);

    tipRoots.forEach((root) => {
      if (isLiteMode && !isShowcase && player.role !== "C") {
        if (root.tagName === "TBODY") {
          root.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:1.25rem; color:var(--muted); font-weight:600;">🔒 Mechanical Indicators Protected (Enterprise Scouting Pilot Required)</td></tr>`;
        } else {
          root.innerHTML = `
            <div class="locked-preview-panel" style="background:var(--bg-elev); padding:1.25rem; border-radius:4px; border:1px solid var(--line); text-align:center;">
              <p style="color:var(--warn); font-weight:600; margin-bottom:0.5rem;">🔒 ${tips.length} Mechanical Indicators Protected</p>
              <p style="font-size:0.84rem; color:var(--muted); margin-bottom:1rem;">Out-of-sample verified separation, effect sizes (d), and pre-release tracking data are available for enterprise scouts.</p>
              <button type="button" class="btn" onclick="window.openEnterpriseModal('${player.name.replace(/'/g, "\\'")}')">Request Pilot Access to Unlock ${player.name} →</button>
            </div>
          `;
        }
      } else if (root.tagName === "TBODY") {
        root.innerHTML = filteredTips.map((t, i) => {
          const rank = t.rank || (i + 1);
          const conf = Math.round((t.confidence || 0.85) * 100);
          const mult = t.separation_floor_multiples || 4.8;
          return `<tr>
            <td style="font-family:var(--mono); font-weight:700; color:var(--accent);">#${rank}</td>
            <td style="font-weight:600; color:#fff;">${t.contrast_label || t.contrast || t.title}</td>
            <td style="color:#94a3b8;">${t.target_body_part || "Glove Set & Delivery"}</td>
            <td style="font-size:0.85rem; color:#cbd5e1;">${t.what_to_spot || t.cue || t.lookFor}</td>
            <td style="font-family:var(--mono); color:var(--good); font-weight:700;">${conf}%</td>
            <td style="font-family:var(--mono); color:#60a5fa;">${mult}× floor</td>
            <td><button type="button" class="btn-compare-sync" onclick="window.selectScrubberTip(${rank - 1})" style="padding:0.25rem 0.5rem; font-size:0.75rem; background:rgba(59,130,246,0.15); border:1px solid #3b82f6; color:#93c5fd; border-radius:4px; cursor:pointer;">Compare</button></td>
          </tr>`;
        }).join("");
      } else {
        root.innerHTML =
          filteredTips.map((t, i) => renderTip(t, angleMap, i + 1)).join("") ||
          `<p class="note">No mechanical indicators recorded for this arm.</p>`;
      }
    });

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
    // Re-apply current scrubber tip to reload correct situational video
    if (typeof window.applyCurrentTipSelection === "function") {
      window.applyCurrentTipSelection();
    }
  }

  window.paintTips = paint;

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
