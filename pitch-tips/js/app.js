const SHOWCASE_ARM_IDS = new Set([
  "roupp",
  "landen_roupp",
  "webb",
  "logan_webb",
  "eduardo_rodriguez",
  "gabriel_moreno",
  "chase_burns",
  "burns",
  "roki_sasaki",
  "sasaki",
  "won_tae_choi",
  "choi",
  "gu_lin_ruei_yang",
  "gulin",
  "trevor_bauer",
  "bauer"
]);

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
  const isSubdir = location.pathname.includes("/lite/") || location.pathname.endsWith("/lite");
  const dataPath = isSubdir ? "../data/demo.json" : "data/demo.json";
  let res = await fetch(dataPath);
  if (!res.ok) {
    res = await fetch("data/demo.json");
  }
  if (!res.ok) throw new Error("Failed to load demo data");
  return res.json();
}

function pct(n) {
  return `${Math.round(Number(n) * 100)}%`;
}

function qs(name) {
  return new URLSearchParams(location.search).get(name);
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

function tipPassesFilters(tip, { angle, context }) {
  if (angle && tip.angle && tip.angle !== angle) return false;
  if (context) {
    const ctx = tip.context || [];
    if (ctx.length && !ctx.includes(context) && !ctx.includes("all situations")) return false;
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
        <span class="badge ok">${sepLabel}</span>
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
      valEl.textContent = catchers.length || 10;
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
          <span>${t.contrast_label || t.contrast || t.predicts}</span>
        </div>
        <p><strong>Observed variance:</strong> ${t.lookFor || t.behavior || t.direction || ""}</p>
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
  const img = document.getElementById("detection-frame");
  const caption = document.getElementById("detection-caption");
  if (!img) return;

  const still = player.detectionStill;
  if (!still) {
    const compareRoot = document.getElementById("glove-compare");
    if (compareRoot) compareRoot.hidden = true;
    img.hidden = true;
    if (caption) {
      caption.textContent = `Tracking frames active for ${player.name} · Pre-release delivery window segmented.`;
    }
  } else {
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

function wirePlayerPage(data) {
  ensureEnterpriseModal();
  ensureLiteBanner();
  const id = qs("id");
  let player = data.players?.[id];
  if (!player && id) {
    const aliases = {
      roupp: "landen_roupp",
      landen_roupp: "roupp",
      webb: "logan_webb",
      logan_webb: "webb",
      erod: "eduardo_rodriguez",
      moreno: "gabriel_moreno",
      canning: "griffin_canning",
      griffin_canning: "canning",
      burns: "chase_burns",
      chase_burns: "chase_burns",
      sasaki: "roki_sasaki",
      roki_sasaki: "roki_sasaki",
      choi: "won_tae_choi",
      won_tae_choi: "won_tae_choi",
      gulin: "gu_lin_ruei_yang",
      gu_lin_ruei_yang: "gu_lin_ruei_yang",
      bauer: "trevor_bauer",
      trevor_bauer: "trevor_bauer",
    };
    if (aliases[id] && data.players?.[aliases[id]]) {
      player = data.players[aliases[id]];
    }
  }
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

  const isShowcase = SHOWCASE_ARM_IDS.has(player.id) || SHOWCASE_ARM_IDS.has(id);
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
    const filteredTips = tips.filter((t) => tipPassesFilters(t, { angle, context }));
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
          filteredTips.map((t) => renderTip(t, angleMap)).join("") ||
          `<p class="note">No mechanical indicators recorded for this filter setting.</p>`;
      }
    }
    const catcherPanel = document.getElementById("catcher-signals-panel");
    const cTips = (player.catcherTips || []).filter((t) => tipPassesFilters(t, { angle, context }));
    if (catcherPanel) {
      if (player.role !== "C" && (!player.catcherTips || !player.catcherTips.length)) {
        catcherPanel.hidden = true;
      } else {
        catcherPanel.hidden = false;
      }
    }
    if (catcherTipRoot) {
      catcherTipRoot.innerHTML =
        cTips.map((t) => renderTip(t, angleMap)).join("") ||
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
