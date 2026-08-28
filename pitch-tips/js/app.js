async function loadDemo() {
  const res = await fetch("data/demo.json");
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
  return Object.values(data.players || {});
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
  const t = (data.meta.confidenceTiers || []).find((x) => x.id === tierId);
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
  const body = document.getElementById("situation-coverage-body");
  const note = document.getElementById("situation-coverage-note");
  if (!body) return;
  const situations = player.situationCoverage?.situations || [];
  const floor = Math.round((player.tipFloor || 0.70) * 100);
  if (note) {
    const arsenal = (player.situationCoverage?.arsenal || ["FF", "SL", "CH", "SI"]).join(", ");
    note.textContent = `Pitch arsenal: ${arsenal}. Computer vision isolates physical mechanical variance across pre-release delivery windows.`;
  }
  if (!situations.length) {
    body.innerHTML = `<tr><td colspan="4">No situation coverage yet.</td></tr>`;
    return;
  }
  body.innerHTML = situations
    .map((s) => {
      const types = (s.discernable_types || []).join(", ") || "—";
      const badge = s.discernable_n > 0 ? "ok" : "";
      return `<tr>
        <td>${s.label}</td>
        <td>${s.n}</td>
        <td><span class="badge ${badge}">${s.coverage}</span></td>
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
      return playerTips(b).length - playerTips(a).length || (b.pickConfidence || 0) - (a.pickConfidence || 0);
    });

  const live = players.filter((p) => p.pocLive || p.poc);
  const totalSignals = players.reduce((s, p) => s + playerTips(p).length, 0);

  if (summary) {
    summary.textContent = `${players.length} pitchers under active CV tracking · ${totalSignals} measurable mechanical indicators isolated across broadcast CF`;
  }

  root.innerHTML = players
    .map((p) => {
      const team = teamById(data, p.teamId);
      const tips = playerTips(p);
      const topLead = tips[0];
      const look = topLead ? topLead.lookFor || topLead.direction : p.summary || "—";
      const src = `<span class="badge ok">live PoC</span>`;
      const tipAvg =
        tips.length > 0
          ? pct(tips.reduce((s, t) => s + (t.confidence || 0.75), 0) / tips.length)
          : "—";
      const sep = topLead?.separation_floor_multiples ? ` · ${topLead.separation_floor_multiples}× floor` : "";
      return `<tr>
        <td><a href="player.html?id=${encodeURIComponent(p.id)}">${p.name}</a> ${src}</td>
        <td>${team?.abbr || "—"}</td>
        <td><span class="badge ${tierBadge(p.tier)}">${tierLabel(data, p.tier)}</span></td>
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
        ({ player, team, tip }) => `<tr>
      <td><a href="player.html?id=${encodeURIComponent(player.id)}">${player.name}</a></td>
      <td>${team?.abbr || "—"}</td>
      <td>${tip.situationLabel || (tip.context || []).join(", ") || "—"}</td>
      <td>${tip.predicts}</td>
      <td>${pct(tip.confidence || 0.75)}</td>
      <td>${tip.lookFor || "—"}</td>
    </tr>`
      )
      .join("") || `<tr><td colspan="6">Catcher bounding & setup classification active — target height/lateral offset signals populate as multi-angle club feeds connect.</td></tr>`;
}

function wireLanding(data) {
  wirePicksTable(data);
  wireCatcherPicksTable(data);

  const teamSel = document.getElementById("team-select");
  const playerSel = document.getElementById("player-select");
  const goTeam = document.getElementById("go-team");
  const goPlayer = document.getElementById("go-player");

  fillSelect(teamSel, data.teams, { valueKey: "id", labelKey: "name", blank: "Choose a team" });
  fillSelect(
    playerSel,
    playerList(data).filter((p) => p.role !== "C").map((p) => ({ id: p.id, label: `${p.name} (${teamById(data, p.teamId)?.abbr || ""})` })),
    { valueKey: "id", labelKey: "label", blank: "Choose a pitcher" }
  );

  teamSel?.addEventListener("change", () => {
    const tid = teamSel.value;
    if (!tid) {
      fillSelect(
        playerSel,
        playerList(data).filter((p) => p.role !== "C").map((p) => ({ id: p.id, label: `${p.name} (${teamById(data, p.teamId)?.abbr || ""})` })),
        { valueKey: "id", labelKey: "label", blank: "Choose a pitcher" }
      );
      return;
    }
    fillSelect(
      playerSel,
      playersForTeam(data, tid).filter((p) => p.role !== "C").map((p) => ({ id: p.id, label: p.name })),
      { valueKey: "id", labelKey: "label", blank: "Choose a pitcher" }
    );
  });

  goTeam?.addEventListener("click", (e) => {
    e.preventDefault();
    const tid = teamSel?.value;
    location.href = tid ? `team.html?id=${encodeURIComponent(tid)}` : "teams.html";
  });

  goPlayer?.addEventListener("click", (e) => {
    e.preventDefault();
    const pid = playerSel?.value;
    if (pid) location.href = `player.html?id=${encodeURIComponent(pid)}`;
  });
}

function renderTeamCoverageCard(data, t) {
  const s = teamTipStats(data, t);
  const catchers = playersForTeam(data, t.id).filter((p) => p.role === "C");
  const pitchers = playersForTeam(data, t.id).filter((p) => p.role !== "C");
  const isNlWest = ["lad", "ari", "sd", "sf", "col"].includes(t.id);
  const divTag = isNlWest ? "NL West" : "Other Organization";
  const statusTag = isNlWest ? "100% Active PoC" : "Tracked Arm";
  const statusClass = isNlWest ? "hot" : "ok";

  const pitcherPills = pitchers
    .map((p) => {
      const tips = playerTips(p);
      const badgeCls = tips.length > 0 ? "leads" : "";
      const countLabel = tips.length > 0 ? `${tips.length} leads` : `${p.pitchesModeled || 0} p`;
      return `
      <a class="roster-pill" href="player.html?id=${encodeURIComponent(p.id)}">
        <span>${p.name}</span>
        <span class="pill-badge ${badgeCls}">${p.throws || "R"}HP · ${countLabel}</span>
      </a>`;
    })
    .join("");

  const catcherPills = catchers
    .map((c) => {
      const tips = playerTips(c);
      const countLabel = tips.length > 0 ? `${tips.length} setup cues` : "Setup Active";
      return `
      <a class="roster-pill" href="player.html?id=${encodeURIComponent(c.id)}">
        <span>${c.name}</span>
        <span class="pill-badge leads">C · ${countLabel}</span>
      </a>`;
    })
    .join("");

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
        <a class="btn" href="team.html?id=${encodeURIComponent(t.id)}">Open ${t.abbr} Dossier &amp; Indicators →</a>
      </div>
    </article>
  `;
}

function renderCoverageMatrixTable(data) {
  const nlwest = (data.teams || []).filter((t) => ["lad", "ari", "sd", "sf", "col"].includes(t.id));
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
              <td><strong><a href="team.html?id=${encodeURIComponent(t.id)}">${t.name} (${t.abbr})</a></strong></td>
              <td><span class="badge">NL West</span></td>
              <td><strong>${pitchers.length}</strong> arms</td>
              <td><strong>${catchers.length}</strong> catchers</td>
              <td>${(s.totalPitches || 0).toLocaleString()}</td>
              <td><span class="badge hot">${pTips.length} leads</span></td>
              <td><span class="badge ok">${cTips.length} setup cues</span></td>
              <td><span class="badge good">100% Active</span></td>
              <td><a class="btn ghost" style="padding:0.25rem 0.6rem; font-size:0.75rem;" href="team.html?id=${encodeURIComponent(t.id)}">Dossier →</a></td>
            </tr>`;
          }).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function wireTeamsIndex(data) {
  const root = document.getElementById("team-grid");
  const matrixRoot = document.getElementById("matrix-container");
  if (!root) return;

  const targetTeams = (data.teams || []).filter((t) => ["lad", "ari", "sd", "sf", "col"].includes(t.id));
  const otherTeams = (data.teams || []).filter((t) => !["lad", "ari", "sd", "sf", "col"].includes(t.id) && playersForTeam(data, t.id).length > 0);
  const allDisplayTeams = [...targetTeams, ...otherTeams];

  function renderCards(filter = "nlwest") {
    const list = filter === "nlwest" ? targetTeams : allDisplayTeams;
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
    const avgLabel = s.avgConfidence == null ? "—" : pct(s.avgConfidence);
    lede.textContent = `${s.tipCount} mechanical & catcher indicators isolated · ${s.playersWithTips} of ${s.playerCount} athletes tracked · Computer Vision Broadcast PoC`;
  }

  const allTeamMembers = playersForTeam(data, team.id);
  const pitchers = allTeamMembers.filter((p) => p.role !== "C");
  const catchers = allTeamMembers.filter((p) => p.role === "C");

  if (grid) {
    grid.innerHTML = pitchers
      .map(
        (p) => {
          const tips = playerTips(p);
          return `
      <a class="tile" href="player.html?id=${encodeURIComponent(p.id)}">
        <div class="kicker">${p.throws}HP · ${p.role}</div>
        <h3>${p.name}</h3>
        <p>${p.summary}</p>
        <div class="stats"><span><strong>${tips.length}</strong> mechanical leads</span></div>
      </a>`;
        }
      )
      .join("") || `<p class="note">No pitchers tracked for this club yet.</p>`;
  }

  if (catcherGrid) {
    catcherGrid.innerHTML = catchers
      .map(
        (c) => {
          const cTips = playerTips(c);
          const roleLabel = c.roleType === "starter" ? "Primary Starter" : "Backup Catcher";
          return `
      <a class="tile" href="player.html?id=${encodeURIComponent(c.id)}">
        <div class="kicker">Catcher · ${roleLabel}</div>
        <h3>${c.name}</h3>
        <p>${c.summary}</p>
        <div class="stats"><span><strong>${cTips.length}</strong> setup cues (≥75% signal)</span></div>
      </a>`;
        }
      )
      .join("") || `<p class="note">Catcher setup tracking active for ${team.abbr}.</p>`;
  }

  const angleMap = Object.fromEntries((data.meta.angles || []).map((a) => [a.id, a.label]));
  const allTips = pitchers.flatMap((p) =>
    playerTips(p).map((t) => ({ ...t, playerName: p.name, playerId: p.id }))
  );
  if (tipRoot) {
    tipRoot.innerHTML = allTips
      .map(
        (t) => `
      <article class="tip">
        <h4><a href="player.html?id=${encodeURIComponent(t.playerId)}">${t.playerName}</a> — ${t.title || t.cue}</h4>
        <div class="meta">
          <span class="badge hot">${pct(t.confidence || 0.75)} signal</span>
          <span class="badge ok">${t.separation_display || `${t.separation_floor_multiples || 3.0}× floor`}</span>
          <span class="badge">${t.angle || "CF"}</span>
          <span>${t.contrast_label || t.contrast || t.predicts}</span>
        </div>
        <p><strong>Observed variance:</strong> ${t.lookFor || t.behavior || t.direction || ""}</p>
        ${t.scouting_note ? `<p class="scout-note" style="margin-top:0.35rem; font-size:0.82rem; color:var(--text); opacity:0.85;"><strong>Advance scouting insight:</strong> ${t.scouting_note}</p>` : ""}
      </article>`
      )
      .join("") || `<p class="note">No mechanical indicators recorded for this club yet.</p>`;
  }

  if (catcherRoot) {
    const catcherTips = allTeamMembers.flatMap((p) =>
      (p.catcherTips || []).map((t) => ({ ...t, playerName: p.name, playerId: p.id }))
    );
    catcherRoot.innerHTML =
      catcherTips
        .map(
          (t) => `
      <article class="tip">
        <h4><a href="player.html?id=${encodeURIComponent(t.playerId)}">${t.playerName}</a> — ${t.title || "Catcher Setup"}</h4>
        <div class="meta">
          <span class="badge hot">${pct(t.confidence || 0.75)} signal</span>
          <span class="badge ok">catcher setup</span>
          <span>${t.predicts || "Offspeed"}</span>
        </div>
        <p><strong>Setup variance:</strong> ${t.lookFor || ""}</p>
      </article>`
        )
        .join("") || `<p class="note">Catcher setup tracking (mitt target / stance width / depth) active for ${team.abbr}. Multi-angle club feeds isolate fine setup adjustments.</p>`;
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
  if (!root || !leftImg || !rightImg || !compare?.leftSrc || !compare?.rightSrc) {
    if (root) root.hidden = true;
    if (img) img.hidden = false;
    return false;
  }

  const bust = `?v=${encodeURIComponent(still.cacheKey || "1")}`;
  leftImg.src = `${compare.leftSrc}${bust}`;
  rightImg.src = `${compare.rightSrc}${bust}`;
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
  const upload = document.getElementById("club-upload");
  const uploadNote = document.getElementById("upload-note");
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
      img.src = still.image;
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

  upload?.addEventListener("change", () => {
    const f = upload.files?.[0];
    if (!f) return;
    const url = URL.createObjectURL(f);
    if (uploadNote) {
      uploadNote.textContent = `Selected ${f.name} (${Math.round(f.size / 1024)} KB). Ingest pipeline maps this to TEAM / X1–X4 multi-angle workspace; 4K tracking refines cue resolution.`;
    }
    const compareRoot = document.getElementById("glove-compare");
    if (compareRoot) compareRoot.hidden = true;
    img.hidden = false;
    const v = document.createElement("video");
    v.src = url;
    v.muted = true;
    v.addEventListener("loadeddata", () => {
      v.currentTime = Math.min(0.45, (v.duration || 1) * 0.35);
    });
    v.addEventListener("seeked", () => {
      const c = document.createElement("canvas");
      c.width = v.videoWidth;
      c.height = v.videoHeight;
      c.getContext("2d").drawImage(v, 0, 0);
      img.src = c.toDataURL("image/jpeg", 0.85);
      if (caption) caption.textContent = `${f.name} · Club video loaded (ready for 4K multi-angle landmark tracker)`;
      URL.revokeObjectURL(url);
    });
  });
}

function wirePlayerPage(data) {
  const id = qs("id");
  const player = data.players?.[id];
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

  const tips = playerTips(player);
  if (title) title.textContent = player.name;
  if (lede) {
    const topFloor = tips[0]?.separation_floor_multiples ? ` · max separation ${tips[0].separation_floor_multiples}× floor` : "";
    if (player.role === "C") {
      const roleName = player.roleType === "starter" ? "Primary Starter" : "Backup Catcher";
      lede.innerHTML = `${team?.name || ""} · Catcher (${roleName}) · <strong>${tips.length}</strong> Catcher Setup Indicators (≥75% signal floor)<br>${player.summary}`;
    } else {
      lede.innerHTML = `${team?.name || ""} · ${player.throws}HP ${player.role} · <strong>${tips.length}</strong> High-Variance Mechanical Indicators${topFloor}<br>${player.summary}`;
    }
  }

  wireDetectionStage(player);
  wireSituationCoverage(player);

  const teamLink = document.getElementById("back-team");
  if (teamLink && team) {
    teamLink.href = `team.html?id=${encodeURIComponent(team.id)}`;
    teamLink.textContent = `← ${team.abbr} summary`;
  }

  fillSelect(angleSel, data.meta.angles, {
    valueKey: "id",
    labelKey: "label",
    blank: "All angles",
  });
  fillSelect(contextSel, data.meta.contexts, {
    valueKey: "id",
    labelKey: "label",
    blank: "All contexts",
  });

  const angleMap = Object.fromEntries((data.meta.angles || []).map((a) => [a.id, a.label]));

  function paint() {
    const angle = angleSel?.value || "";
    const context = contextSel?.value || "";
    const filteredTips = tips.filter((t) => tipPassesFilters(t, { angle, context }));
    if (tipRoot) {
      tipRoot.innerHTML =
        filteredTips.map((t) => renderTip(t, angleMap)).join("") ||
        `<p class="note">No mechanical indicators recorded for this filter setting.</p>`;
    }
    const cTips = (player.catcherTips || []).filter((t) => tipPassesFilters(t, { angle, context }));
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
    if (page === "home") wireLanding(data);
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
