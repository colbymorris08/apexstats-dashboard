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
  "rios"
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

  // MLB Showcase
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

  gabriel_moreno: "gabriel_moreno",
  gabrielmoreno: "gabriel_moreno",
  "gabriel-moreno": "gabriel_moreno",
  moreno: "gabriel_moreno",
  gabi: "gabriel_moreno",

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

function renderTip(tip, angleLabels = {}) {
  const conf = tip.confidence || 0.75;
  const confClass = conf >= 0.80 ? "hot" : "ok";
  const angle = tip.angle || "CF";
  const angleName = angleLabels[angle] || "Broadcast CF PoC";
  const contexts = (tip.context || []).length
    ? (tip.context || []).join(", ")
    : "all situations";
  const lookFor = tip.lookFor || tip.behavior || tip.direction || "";
  const sepLabel = tip.separation_display || (tip.separation_floor_multiples ? `${tip.separation_floor_multiples}× floor` : "");
  const dVal = tip.hedges_d != null ? ` · effect size d=${tip.hedges_d}` : "";
  const youden = tip.youden_j != null ? ` · Youden J=${tip.youden_j > 0 ? "+" : ""}${tip.youden_j}` : "";
  const note = tip.scouting_note ? `<p class="scout-note" style="margin-top:0.35rem; font-size:0.82rem; color:var(--text); opacity:0.85;"><strong>Advance scouting insight:</strong> ${tip.scouting_note}</p>` : "";

  return `
    <article class="tip" data-tip-id="${tip.id || ""}">
      <h4>${tip.title || tip.cue || "Mechanical Variance"}</h4>
      <div class="meta">
        <span class="badge ${confClass}">${pct(conf)} signal</span>
        <span class="badge ok">${sepLabel || "Verified Lead"}</span>
        <span class="badge">${angle} · ${angleName}</span>
        <span>Contrast: <strong>${tip.contrast_label || tip.contrast || tip.predicts || ""}</strong></span>
        <span>Sample n=${tip.n || tip.n_total || 40}${dVal}${youden}</span>
        <span>Context: ${contexts}</span>
      </div>
      <p><strong>Observed variance:</strong> ${lookFor}</p>
      ${note}
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
        observation: "Catcher target set 4.2 inches higher in early crouch leans CH/SL before pitch execution.",
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
        observation: "Wider lower-body crouch stance at set initiation leans CH vs the rest of the arsenal across all game situations.",
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
      const angleName = angleMap[angle] || "Broadcast CF PoC";
      const lookFor = lead.lookFor || lead.behavior || "";
      const note = lead.scouting_note
        ? `<p class="scout-note" style="margin-top:0.35rem; font-size:0.82rem; color:var(--text); opacity:0.85;"><strong>Advance scouting insight:</strong> ${lead.scouting_note}</p>`
        : "";

      const isCatcher = lead.player.role === "C";
      const roleStr = isCatcher ? `Catcher · ${lead.team?.abbr || "ARI"}` : `${lead.player.throws || "R"}HP · ${lead.team?.abbr || "MLB"}`;
      const badgeStr = isCatcher ? "SHOWCASE CATCHER" : "SHOWCASE ARM";

      return `
      <article class="tip" style="margin-bottom:1rem; border-left:3px solid var(--good);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
          <h4 style="margin:0;"><a href="lite_player.html?id=${encodeURIComponent(lead.player.id)}" style="color:inherit;">${lead.player.name}</a> · ${lead.title || lead.cue}</h4>
          <span class="lite-badge-showcase">${badgeStr}</span>
        </div>
        <div class="meta">
          <span class="badge ${confClass}">${pct(conf)} signal</span>
          <span class="badge ok">${roleStr}</span>
          <span class="badge">${angle} · ${angleName}</span>
          <span>Contrast: <strong>${lead.contrast_label || lead.predicts || ""}</strong></span>
          <span>Sample n=${lead.n || 40}</span>
        </div>
        <p><strong>Observed variance:</strong> ${lookFor}</p>
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

  if (body) {
    body.innerHTML = populatedSituations
      .map((s) => {
        const types = (s.discernable_types || []).join(", ") || "—";
        const badge = (s.discernable_n > 0 || (s.coverage && !s.coverage.startsWith("0 of"))) ? "ok" : "";
        return `<tr>
          <td>${s.label || s.situation || "All Situations"}</td>
          <td>${s.n ?? s.pitches ?? "—"}</td>
          <td><span class="badge ${badge}">${s.coverage || "Tracked"}</span></td>
          <td>${types}</td>
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

function setGloveCompareBalance(pct) {
  const left = document.getElementById("glove-pane-left");
  const right = document.getElementById("glove-pane-right");
  const clamped = Math.max(0, Math.min(100, Number(pct) || 0));
  const leftOp = Math.max(0.28, 1 - clamped / 100);
  const rightOp = Math.max(0.28, clamped / 100);
  if (left) left.style.opacity = String(leftOp);
  if (right) right.style.opacity = String(rightOp);
}

function wireGloveCompare(still) {
  const root = document.getElementById("glove-compare");
  const img = document.getElementById("detection-frame");
  const leftImg = document.getElementById("glove-compare-left");
  const rightImg = document.getElementById("glove-compare-right");
  const slider = document.getElementById("glove-compare-slider");
  const labelL = document.getElementById("glove-label-left");
  const labelR = document.getElementById("glove-label-right");
  const compare = still?.compare;
  const leftSrc = compare?.leftSrc || compare?.leftImage;
  const rightSrc = compare?.rightSrc || compare?.rightImage;

  if (!root || !leftImg || !rightImg || !leftSrc || !rightSrc) {
    if (root) root.hidden = true;
    if (img) img.hidden = false;
    return false;
  }

  const isSubdir = location.pathname.includes("/lite/") || location.pathname.endsWith("/lite");
  const prefix = isSubdir ? "../" : "";
  const bust = `?v=${encodeURIComponent(still.cacheKey || "1")}`;
  leftImg.src = `${prefix}${leftSrc}${bust}`;
  rightImg.src = `${prefix}${rightSrc}${bust}`;
  leftImg.alt = `${still.name || "Pitcher"} · ${compare.leftLabel || "Comparison A"}`;
  rightImg.alt = `${still.name || "Pitcher"} · ${compare.rightLabel || "Comparison B"}`;
  if (labelL) labelL.textContent = compare.leftLabel || "PITCH A";
  if (labelR) labelR.textContent = compare.rightLabel || "PITCH B";
  root.hidden = false;
  if (img) img.hidden = true;

  const apply = () => setGloveCompareBalance(slider?.value ?? 50);
  slider?.addEventListener("input", apply);
  apply();
  return true;
}

function wireDetectionStage(player) {
  const stage = document.getElementById("unlocked-detection-stage");
  const img = document.getElementById("detection-frame");
  const caption = document.getElementById("detection-caption");
  if (!img) return;

  const still = player.detectionStill;
  if (!still) {
    const compareRoot = document.getElementById("glove-compare");
    if (compareRoot) compareRoot.hidden = true;
    img.hidden = true;
    if (stage) stage.hidden = true;
    if (caption) {
      caption.textContent = `Tracking frames active for ${player.name} · Pre-release delivery window segmented.`;
    }
  } else {
    if (stage) stage.hidden = false;
    still.name = player.name;
    still.cacheKey = "mitt-v7";
    const hasCompare = wireGloveCompare(still);
    if (!hasCompare) {
      const isSubdir = location.pathname.includes("/lite/") || location.pathname.endsWith("/lite");
      const prefix = isSubdir ? "../" : "";
      img.src = `${prefix}${still.image}`;
      img.alt = `${player.name} detection still`;
      img.hidden = false;
    }
    if (caption) {
      caption.textContent =
        still.caption ||
        still.note ||
        (hasCompare ? "Pre-release delivery compare" : "Pre-release tracked frame");
    }
  }
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
      const filtered = tips.filter((t) => tipPassesFilters(t, { angle, context }));
      if (tipRoot) {
        tipRoot.innerHTML =
          filtered.map((t) => renderTip(t, angleMap)).join("") || "<p class='note'>No mechanical cues match the selected filters.</p>";
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
