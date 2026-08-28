/**
 * Apex Preflight Lite — Public Showcase & Enterprise Scouting Preview Logic
 */

const SHOWCASE_IDS = ["eduardo_rodriguez", "webb", "roupp", "woo"];

async function loadDemo() {
  try {
    const res = await fetch("data/demo.json");
    if (res.ok) return await res.json();
  } catch (e) {
    // try fallback
  }
  const fallback = await fetch("demo.json");
  if (!fallback.ok) throw new Error("Failed to load demo data");
  return fallback.json();
}

function pct(n) {
  return `${Math.round(Number(n) * 100)}%`;
}

function qs(name) {
  return new URLSearchParams(location.search).get(name);
}

function isShowcaseArm(id) {
  return SHOWCASE_IDS.includes(id);
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

function setGloveCompareBalance(pctVal) {
  const left = document.getElementById("glove-pane-left");
  const right = document.getElementById("glove-pane-right");
  const clamped = Math.max(0, Math.min(100, Number(pctVal) || 0));
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
}

function wirePilotModal() {
  const modal = document.getElementById("pilot-modal");
  const backdrop = document.getElementById("pilot-modal-backdrop");
  const closeBtn = document.getElementById("pilot-modal-close");
  const form = document.getElementById("pilot-modal-form");
  const success = document.getElementById("pilot-modal-success");

  if (!backdrop) return;

  function openModal(defaultArmName = "") {
    backdrop.classList.add("open");
    if (defaultArmName && form) {
      const notesField = form.querySelector("#pilot-notes");
      if (notesField && !notesField.value) {
        notesField.value = `Requesting enterprise scouting models and 4K multi-angle tracking for ${defaultArmName} and organization pitching staff.`;
      }
    }
  }

  function closeModal() {
    backdrop.classList.remove("open");
  }

  document.querySelectorAll(".trigger-pilot-modal").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const arm = btn.dataset.arm || "";
      openModal(arm);
    });
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
    const role = form.querySelector("#pilot-role")?.value || "";
    const notes = form.querySelector("#pilot-notes")?.value || "";

    const subject = encodeURIComponent(`Apex Preflight Enterprise Pilot Request — ${org} (${name})`);
    const body = encodeURIComponent(
      `Name: ${name}\nOrganization/Club: ${org}\nEmail: ${email}\nRole: ${role}\n\nProject Scope / Target Arms:\n${notes}\n\nSent from Preflight Lite Interface`
    );

    window.open(`mailto:colby.morris08@gmail.com?subject=${subject}&body=${body}`, "_blank");

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
  const conf = topTip?.confidence ? pct(topTip.confidence) : "88%";

  return `
    <div class="tile" style="border-top: 3px solid var(--good); background: var(--bg-panel); display: flex; flex-direction: column; justify-content: space-between;">
      <div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
          <span class="lite-badge-showcase"><span style="color:var(--good); font-weight:900;">●</span> SHOWCASE ARM</span>
          <span class="badge ok">${team?.abbr || "MLB"} · ${player.throws || "R"}HP</span>
        </div>
        <h3 style="margin: 0.2rem 0 0.4rem; font-size:1.2rem;">${player.name}</h3>
        <p style="font-size: 0.84rem; color: var(--muted); margin-bottom: 0.75rem; line-height: 1.5;">${lookFor}</p>
        <div class="meta" style="margin-bottom:1rem;">
          <span class="badge hot">${conf} Signal</span>
          <span class="badge ok">${tips.length} Verified Indicators</span>
          <span class="badge">CF Multi-Start</span>
        </div>
      </div>
      <a class="btn" style="width:100%; text-align:center; justify-content:center;" href="lite_player.html?id=${encodeURIComponent(player.id)}">
        Open Interactive Delivery Tool →
      </a>
    </div>
  `;
}

function wireLiteLanding(data) {
  const showcaseGrid = document.getElementById("lite-showcase-grid");
  const picksTable = document.getElementById("lite-picks-table-body");
  const picksSummary = document.getElementById("lite-picks-summary");

  if (showcaseGrid) {
    const showcasePlayers = SHOWCASE_IDS.map((id) => data.players?.[id]).filter(Boolean);
    showcaseGrid.innerHTML = showcasePlayers
      .map((p) => renderShowcaseCard(p, teamById(data, p.teamId)))
      .join("");
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
      picksSummary.textContent = `${players.length} MLB pitchers modeled · 3 interactive showcase arms unlocked · Full staff accessible via Enterprise Pilot`;
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
          ? (topLead?.lookFor || p.summary || "Pre-release glove & tempo separation")
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
    playerList(data).filter((p) => p.role !== "C").map((p) => ({
      id: p.id,
      label: `${p.name} (${teamById(data, p.teamId)?.abbr || ""})${isShowcaseArm(p.id) ? " ★ SHOWCASE" : ""}`,
    })),
    { valueKey: "id", labelKey: "label", blank: "Choose a pitcher" }
  );

  teamSel?.addEventListener("change", () => {
    const tid = teamSel.value;
    if (!tid) {
      fillSelect(
        playerSel,
        playerList(data).filter((p) => p.role !== "C").map((p) => ({
          id: p.id,
          label: `${p.name} (${teamById(data, p.teamId)?.abbr || ""})${isShowcaseArm(p.id) ? " ★ SHOWCASE" : ""}`,
        })),
        { valueKey: "id", labelKey: "label", blank: "Choose a pitcher" }
      );
      return;
    }
    fillSelect(
      playerSel,
      playersForTeam(data, tid).filter((p) => p.role !== "C").map((p) => ({
        id: p.id,
        label: `${p.name}${isShowcaseArm(p.id) ? " ★ SHOWCASE" : ""}`,
      })),
      { valueKey: "id", labelKey: "label", blank: "Choose a pitcher" }
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

  wirePilotModal();
}

function wireLiteBoard(data) {
  const root = document.getElementById("lite-board-leads");
  if (!root) return;

  const showcasePlayers = SHOWCASE_IDS.map((id) => data.players?.[id]).filter(Boolean);
  const leads = [];

  for (const p of showcasePlayers) {
    const team = teamById(data, p.teamId);
    for (const t of playerTips(p)) {
      leads.push({ player: p, team, tip: t });
    }
  }

  leads.sort((a, b) => (b.tip.confidence || 0) - (a.tip.confidence || 0));

  root.innerHTML = leads
    .map(({ player, team, tip }) => {
      const conf = tip.confidence || 0.75;
      const confClass = conf >= 0.80 ? "hot" : "ok";
      const sep = tip.separation_display || (tip.separation_floor_multiples ? `${tip.separation_floor_multiples}× floor` : "3.5× floor");
      const dVal = tip.hedges_d != null ? ` · Hedges d=${tip.hedges_d}` : "";
      const note = tip.scouting_note
        ? `<p class="scout-note" style="margin-top:0.4rem; font-size:0.84rem; color:var(--text); opacity:0.9;"><strong>Advance scouting insight:</strong> ${tip.scouting_note}</p>`
        : "";

      return `
        <article class="tip" style="background:var(--bg-panel); border-left:3px solid var(--good); padding:1rem 1.25rem; margin-bottom:1rem; border-radius:4px;">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:0.5rem; margin-bottom:0.35rem;">
            <h4 style="margin:0; font-size:1.05rem;">
              <a href="lite_player.html?id=${encodeURIComponent(player.id)}" style="color:var(--text);">${player.name}</a>
              <span style="font-weight:400; color:var(--muted);">(${team?.abbr || "MLB"})</span> — ${tip.title || tip.cue}
            </h4>
            <span class="lite-badge-showcase">SHOWCASE</span>
          </div>
          <div class="meta" style="margin:0.5rem 0;">
            <span class="badge ${confClass}">${pct(conf)} Signal</span>
            <span class="badge ok">${sep}</span>
            <span class="badge">${tip.angle || "CF"}</span>
            <span>Contrast: <strong>${tip.contrast_label || tip.contrast || tip.predicts}</strong></span>
            <span>Sample n=${tip.n || tip.n_total || 40}${dVal}</span>
          </div>
          <p style="margin:0.35rem 0; font-size:0.86rem;"><strong>Observed variance:</strong> ${tip.lookFor || tip.behavior || tip.direction || ""}</p>
          ${note}
        </article>
      `;
    })
    .join("");

  wirePilotModal();
}

function wireLiteTeams(data) {
  const gridRoot = document.getElementById("lite-team-grid");
  const filterBtns = document.querySelectorAll(".filter-btn");

  function renderCards(filter) {
    if (!gridRoot) return;
    let teams = data.teams || [];
    if (filter === "nlwest") {
      teams = teams.filter((t) => ["lad", "ari", "sd", "sf", "col"].includes(t.id));
    }

    gridRoot.innerHTML = teams
      .map((t) => {
        const players = playersForTeam(data, t.id);
        const pitchers = players.filter((p) => p.role !== "C");
        const catchers = players.filter((p) => p.role === "C");
        const isNlWest = ["lad", "ari", "sd", "sf", "col"].includes(t.id);

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
            return `
            <a class="roster-pill trigger-pilot-modal" href="#" data-arm="${c.name}">
              <span>${c.name}</span>
              <span class="pill-badge">🔒 Setup Active</span>
            </a>`;
          })
          .join("");

        return `
        <article class="team-coverage-card ${isNlWest ? "nlwest" : ""}" data-team-id="${t.id}">
          <div class="card-header-row">
            <div class="card-title-group">
              <div class="kicker">${t.abbr} · ${isNlWest ? "NL West" : "MLB Organization"}</div>
              <h3><a href="lite_team.html?id=${encodeURIComponent(t.id)}" style="color:inherit; text-decoration:none;">${t.name}</a></h3>
            </div>
            <div class="card-badges">
              <span class="badge ${isNlWest ? "hot" : "ok"}">${isNlWest ? "Full Staff Modeled" : "Tracked"}</span>
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
          <p style="font-size:0.84rem; color:var(--muted);">${p.summary || "Pre-release delivery tracking."}</p>
          <div class="stats" style="margin-top:0.75rem;">
            <span><strong>${tips.length}</strong> mechanical leads</span>
          </div>
        </a>`;
      })
      .join("");
  }

  if (catcherGrid) {
    catcherGrid.innerHTML = catchers
      .map((c) => {
        const cTips = playerTips(c);
        return `
        <div class="tile" style="border-top:3px solid rgba(232,162,58,0.4);">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
            <span class="kicker" style="margin:0;">Catcher · ${c.roleType || "Starter"}</span>
            <span class="lite-badge-locked">🔒 ENTERPRISE</span>
          </div>
          <h3 style="margin:0.2rem 0 0.4rem;">${c.name}</h3>
          <p style="font-size:0.84rem; color:var(--muted);">${c.summary || "Pre-pitch target drift & setup depth."}</p>
          <div class="stats" style="margin-top:0.75rem;">
            <span><strong>${cTips.length}</strong> setup cues modeled</span>
          </div>
        </div>`;
      })
      .join("");
  }

  wirePilotModal();
}

function wireLitePlayer(data) {
  const id = qs("id");
  const player = data.players?.[id];
  const title = document.getElementById("player-title");
  const lede = document.getElementById("player-lede");
  const backTeam = document.getElementById("back-team");
  const isShow = isShowcaseArm(id);

  if (!player) {
    if (title) title.textContent = "Player not found";
    return;
  }

  const team = teamById(data, player.teamId);
  if (backTeam) {
    backTeam.href = team ? `lite_team.html?id=${encodeURIComponent(team.id)}` : "lite_teams.html";
    backTeam.textContent = `← ${team?.name || "Coverage Board"}`;
  }

  if (title) {
    title.innerHTML = `${player.name} ${isShow ? '<span class="lite-badge-showcase" style="font-size:0.85rem; vertical-align:middle; margin-left:0.5rem;">★ SHOWCASE ARM · UNLOCKED</span>' : '<span class="lite-badge-locked" style="font-size:0.85rem; vertical-align:middle; margin-left:0.5rem;">🔒 ENTERPRISE SCOUTING ACCESS</span>'}`;
  }

  if (lede) {
    lede.textContent = `${player.role} · ${player.throws}HP · ${team?.name || "MLB"} · ${player.summary || "Computer vision mechanical tracking"}`;
  }

  const lockSection = document.getElementById("lite-lock-section");
  const unlockedSection = document.getElementById("lite-unlocked-section");

  if (isShow) {
    if (lockSection) lockSection.hidden = true;
    if (unlockedSection) unlockedSection.hidden = false;

    wireDetectionStage(player);
    wireSituationCoverage(player);

    const angleMap = Object.fromEntries((data.meta?.angles || []).map((a) => [a.id, a.label]));
    const tipRoot = document.getElementById("player-tips");
    const tips = playerTips(player);

    if (tipRoot) {
      tipRoot.innerHTML = tips.map((t) => renderTip(t, angleMap)).join("") || "<p class='note'>No mechanical cues.</p>";
    }

    fillSelect(document.getElementById("angle-select"), data.meta?.angles || [], { blank: "All views" });
    fillSelect(document.getElementById("context-select"), data.meta?.contexts || [], { blank: "All game situations" });
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
  } catch (err) {
    console.error(err);
    const bootFail = document.getElementById("boot-fail");
    if (bootFail) bootFail.hidden = false;
  }
});
