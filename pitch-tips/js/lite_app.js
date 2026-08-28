/**
 * Apex Preflight Lite — Public Showcase & Enterprise Scouting Preview Logic
 */

const SHOWCASE_IDS = ["eduardo_rodriguez", "webb", "roupp"];

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

function setGloveCompareBalance(value) {
  const pair = document.getElementById("glove-compare-pair");
  const leftPane = document.getElementById("glove-pane-left");
  const rightPane = document.getElementById("glove-pane-right");
  if (!pair || !leftPane || !rightPane) return;

  const v = Math.min(100, Math.max(0, Number(value)));
  const rightPct = v;
  const leftPct = 100 - v;

  leftPane.style.flex = `0 0 ${leftPct}%`;
  rightPane.style.flex = `0 0 ${rightPct}%`;

  leftPane.style.opacity = `${0.35 + (0.65 * (100 - v)) / 100}`;
  rightPane.style.opacity = `${0.35 + (0.65 * v) / 100}`;
}

function wireGloveCompare(still) {
  const root = document.getElementById("glove-compare");
  const img = document.getElementById("detection-frame");
  const left = document.getElementById("glove-compare-left");
  const right = document.getElementById("glove-compare-right");
  const labelL = document.getElementById("glove-label-left");
  const labelR = document.getElementById("glove-label-right");
  const slider = document.getElementById("glove-compare-slider");
  if (!root || !left || !right) return false;

  const compare = still?.compare;
  if (!compare || !compare.leftImage || !compare.rightImage) {
    root.hidden = true;
    if (img) img.hidden = false;
    return false;
  }

  left.src = compare.leftImage;
  right.src = compare.rightImage;
  left.alt = `${still.name || "Pitcher"} ${compare.leftLabel || "Pitch A"}`;
  right.alt = `${still.name || "Pitcher"} ${compare.rightLabel || "Pitch B"}`;

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
          <div>✓ Automated opponent weekend rotation audits via Synergy or stadium video</div>
          <div>✓ Active catcher setup &amp; pitcher pre-release mechanical variance reports</div>
          <div>✓ Conference lockout protection (guaranteed single-school exclusivity)</div>
        </div>

        <form id="pilot-modal-form">
          <div class="form-group">
            <label for="pilot-name">Full Name *</label>
            <input type="text" id="pilot-name" required placeholder="e.g. Coach Dan Miller" />
          </div>

          <div class="form-group">
            <label for="pilot-org">Organization / School *</label>
            <input type="text" id="pilot-org" required placeholder="e.g. Texas A&amp;M University / MLB Club" />
          </div>

          <div class="form-group">
            <label for="pilot-email">Work / Official Email *</label>
            <input type="email" id="pilot-email" required placeholder="e.g. dmiller@athletics.tamu.edu" />
          </div>

          <div class="form-group">
            <label for="pilot-level">Level / Division *</label>
            <select id="pilot-level">
              <option value="NCAA Division I (Power Conference)">NCAA Division I (Power Conference - SEC, ACC, Big 12, Big Ten)</option>
              <option value="NCAA Division I (Mid-Major)">NCAA Division I (Mid-Major)</option>
              <option value="NCAA Division II / III / NAIA / JUCO">NCAA Division II / III / NAIA / JUCO</option>
              <option value="MLB / MiLB Professional Organization">MLB / MiLB Professional Organization</option>
              <option value="Independent / Player Development Facility">Independent / Player Development Facility</option>
            </select>
          </div>

          <div class="form-group">
            <label for="pilot-tier">Tier of Interest *</label>
            <select id="pilot-tier">
              <option value="College Tier 1: Standard Team License">College Tier 1: Standard Team License</option>
              <option value="College Tier 2: Conference Exclusivity Premium" selected>College Tier 2: Conference Exclusivity Premium ("Monopolize Your Conference")</option>
              <option value="College Tier 3: National Monopoly Sole Contract">College Tier 3: National Monopoly Sole Contract</option>
              <option value="Pro / MLB Enterprise (Custom Quote)">Pro / MLB Enterprise (Custom Quote)</option>
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
  const conf = topTip?.confidence ? pct(topTip.confidence) : "88%";
  const isCatcher = player.role === "C";
  const roleLabel = isCatcher ? `${team?.abbr || "ARI"} · Catcher` : `${team?.abbr || "MLB"} · ${player.throws || "R"}HP`;
  const badgeLabel = isCatcher ? "SHOWCASE CATCHER" : "SHOWCASE ARM";
  const btnLabel = isCatcher ? "Open Interactive Catcher Setup Tool →" : "Open Interactive Delivery Tool →";

  return `
    <div class="tile" style="border-top: 3px solid var(--good); background: var(--bg-panel); display: flex; flex-direction: column; justify-content: space-between;">
      <div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
          <span class="lite-badge-showcase"><span style="color:var(--good); font-weight:900;">●</span> ${badgeLabel}</span>
          <span class="badge ok">${roleLabel}</span>
        </div>
        <h3 style="margin: 0.2rem 0 0.4rem; font-size:1.2rem;">${player.name}</h3>
        <p style="font-size: 0.84rem; color: var(--muted); margin-bottom: 0.75rem; line-height: 1.5;">${lookFor}</p>
        <div class="meta" style="margin-bottom:1rem;">
          <span class="badge hot">${conf} Signal</span>
          <span class="badge ok">${tips.length} Verified Indicators</span>
          <span class="badge">${isCatcher ? "Target & Crouch Tracking" : "CF Multi-Start"}</span>
        </div>
      </div>
      <div style="display:flex; gap:0.5rem; flex-direction:column;">
        <a class="btn" style="width:100%; text-align:center; justify-content:center;" href="lite_player.html?id=${encodeURIComponent(player.id)}">
          ${btnLabel}
        </a>
        <button type="button" class="btn ghost trigger-pilot-modal" data-arm="${player.name} (${team?.abbr || "MLB"})" style="width:100%; text-align:center; justify-content:center; font-size:0.8rem; padding:0.4rem;">
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
        observation: "Before Merrill Kelly or Eduardo Rodriguez comes set, Moreno establishes his primary glove target noticeably wider glove-side (outside border to LHH) on Changeups compared to 4-Seam Fastballs.",
        takeaway: "When Moreno sets target >6 inches glove-side before the pitcher settles into the stretch, off-speed probability is 94%+. LHH hitters can eliminate the high inside fastball."
      },
      {
        id: "stance_width",
        name: "Stance Crouch Width & Base Timing",
        signal: "100%",
        contrast: "Changeup (CH) vs. Arsenal",
        situation: "All Game Situations",
        sample: "n=48 pitches",
        metric1: "+14.2%",
        metric1Lbl: "Wider Crouch Base",
        metric2: "0.94 m",
        metric2Lbl: "Lower-Body Spread",
        metric3: "100%",
        metric3Lbl: "Signal Accuracy",
        metric4: "All Counts",
        metric4Lbl: "Situation Coverage",
        targetA: { x: -30, y: 40, label: "CH Crouch (Wide / Deep)", color: "#3ecf8e" },
        targetB: { x: 0, y: 0, label: "Arsenal Baseline", color: "#e8a23a" },
        stanceA: { width: 155, height: 70, depth: "Wide Blocking Base" },
        stanceB: { width: 115, height: 88, depth: "Neutral Posture" },
        observation: "Wider lower-body crouch stance at set initiation leans CH vs the rest of the arsenal across all game situations.",
        takeaway: "Moreno widens his base early to prepare for low-in-the-dirt off-speed blocks. Hitters and 2B runners recognize the base spread before hand break."
      },
      {
        id: "target_height",
        name: "Glove Target Elevation (High vs. Low Zone)",
        signal: "80.0%",
        contrast: "Slider (SL) vs. Off-Speed",
        situation: "All Game Situations",
        sample: "n=40 pitches",
        metric1: "+5.4 in",
        metric1Lbl: "Vertical Target Offset",
        metric2: "80.0%",
        metric2Lbl: "Signal Floor",
        metric3: "0.78 m",
        metric3Lbl: "Target Y (Chest High)",
        metric4: "SL vs CH",
        metric4Lbl: "Contrast Pair",
        targetA: { x: -15, y: -25, label: "SL Target (Chest Level)", color: "#e8a23a" },
        targetB: { x: -25, y: 35, label: "CH Target (Knee Level)", color: "#3ecf8e" },
        stanceA: { width: 125, height: 82, depth: "Upright Setup" },
        stanceB: { width: 145, height: 72, depth: "Low Drop Setup" },
        observation: "Catcher target set higher at chest height leans SL before pitch execution.",
        takeaway: "Provides clear advance tell when sitting on breaking balls in two-strike counts."
      }
    ]
  },
  will_smith: {
    id: "will_smith",
    name: "Will Smith",
    team: "LAD",
    teamName: "Los Angeles Dodgers",
    role: "Primary Starter",
    totalIndicators: 7,
    tells: [
      {
        id: "target_shift",
        name: "Pre-Pitch Target Shift (Arm-Side Offset)",
        signal: "100%",
        contrast: "Sinker (SI) vs. Four-Seam (FF)",
        situation: "All Game Situations",
        sample: "n=60 pitches",
        metric1: "+6.5 in",
        metric1Lbl: "Arm-Side Target Shift",
        metric2: "100%",
        metric2Lbl: "Signal Floor",
        metric3: "+0.32 m",
        metric3Lbl: "Target X (Arm-Side)",
        metric4: "SI vs FF",
        metric4Lbl: "Primary Contrast",
        targetA: { x: 32, y: 20, label: "SI Target (Arm-Side / In)", color: "#3ecf8e" },
        targetB: { x: -10, y: -20, label: "FF Target (Glove-Side / High)", color: "#3d8bfd" },
        stanceA: { width: 130, height: 74, depth: "Lower Drop Base" },
        stanceB: { width: 115, height: 85, depth: "Standard Stance" },
        observation: "Catcher target set noticeably arm-side before set leans SI across all situations.",
        takeaway: "Dodgers battery sets early inside target on sinkers to right-handed batters before the pitcher begins leg kick."
      },
      {
        id: "target_height",
        name: "Glove Target Elevation (Curveball Tell)",
        signal: "81.2%",
        contrast: "Curveball (CU) vs. Fastball",
        situation: "All Game Situations",
        sample: "n=45 pitches",
        metric1: "+7.1 in",
        metric1Lbl: "High Target Elevation",
        metric2: "81.2%",
        metric2Lbl: "Signal Floor",
        metric3: "0.85 m",
        metric3Lbl: "Target Y Elevation",
        metric4: "CU vs SI/FF",
        metric4Lbl: "Pitch Contrast",
        targetA: { x: 5, y: -35, label: "CU Target (High Zone Setup)", color: "#a855f7" },
        targetB: { x: 20, y: 25, label: "SI Target (Low Zone Setup)", color: "#3ecf8e" },
        stanceA: { width: 120, height: 86, depth: "Tall Target Crouch" },
        stanceB: { width: 135, height: 72, depth: "Low Target Crouch" },
        observation: "Target set higher at top of zone leans CU before delivery.",
        takeaway: "High pre-set target gives pitcher a top-of-zone focus point to execute 12-6 downward break."
      }
    ]
  },
  patrick_bailey: {
    id: "patrick_bailey",
    name: "Patrick Bailey",
    team: "SF",
    teamName: "San Francisco Giants",
    role: "Primary Starter",
    totalIndicators: 6,
    tells: [
      {
        id: "target_height",
        name: "Glove Target Elevation (Four-Seam Tell)",
        signal: "100%",
        contrast: "Four-Seam Fastball (FF) vs. Arsenal",
        situation: "All Game Situations",
        sample: "n=55 pitches",
        metric1: "+8.2 in",
        metric1Lbl: "High Zone Glove Setup",
        metric2: "100%",
        metric2Lbl: "Predictive Floor",
        metric3: "0.92 m",
        metric3Lbl: "Target Y (Letters)",
        metric4: "FF vs Offspeed",
        metric4Lbl: "Contrast Pair",
        targetA: { x: 0, y: -40, label: "FF Target (Top of Zone)", color: "#3ecf8e" },
        targetB: { x: -28, y: 30, label: "CH/SI Target (Bottom)", color: "#3d8bfd" },
        stanceA: { width: 120, height: 90, depth: "Taller Target Frame" },
        stanceB: { width: 140, height: 74, depth: "Low Target Frame" },
        observation: "Target set high in zone leans FF at 100% signal floor across all situations.",
        takeaway: "Logan Webb / Giants staff uses Bailey's elevated glove target to calibrate top-of-zone 4-seamers."
      },
      {
        id: "stance_height",
        name: "Stance Setup Height (Cutter Tell)",
        signal: "87.5%",
        contrast: "Cutter (FC) vs. Breaking Balls",
        situation: "All Game Situations",
        sample: "n=42 pitches",
        metric1: "+6.4 in",
        metric1Lbl: "Taller Crouch Stance",
        metric2: "87.5%",
        metric2Lbl: "Signal Accuracy",
        metric3: "0.58 m",
        metric3Lbl: "Stance Y Height",
        metric4: "FC vs CU/SL",
        metric4Lbl: "Pitch Contrast",
        targetA: { x: -20, y: -10, label: "FC Setup (Taller Stance)", color: "#e8a23a" },
        targetB: { x: -30, y: 35, label: "Breaking Setup (Deep)", color: "#a855f7" },
        stanceA: { width: 125, height: 92, depth: "Upright Stance" },
        stanceB: { width: 145, height: 70, depth: "Deep Crouch" },
        observation: "Catcher set taller before leg lift leans FC vs all pitches.",
        takeaway: "Distinct posture elevation isolated across 42 scored game pitches."
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
      .filter((p) => p.role !== "C")
      .map((p) => ({
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
        playerList(data)
          .filter((p) => p.role !== "C")
          .map((p) => ({
            id: p.id,
            label: `${p.name} (${teamById(data, p.teamId)?.abbr || ""})${isShowcaseArm(p.id) ? " ★ SHOWCASE" : ""}`,
          })),
        { valueKey: "id", labelKey: "label", blank: "Choose a pitcher" }
      );
      return;
    }
    fillSelect(
      playerSel,
      playersForTeam(data, tid)
        .filter((p) => p.role !== "C")
        .map((p) => ({
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

  wireCatcherShowcase();
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
      leads.push({ ...t, player: p, team });
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

      return `
      <article class="tip" style="margin-bottom:1rem; border-left:3px solid var(--good);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
          <h4 style="margin:0;"><a href="lite_player.html?id=${encodeURIComponent(lead.player.id)}" style="color:inherit;">${lead.player.name}</a> · ${lead.title || lead.cue}</h4>
          <span class="lite-badge-showcase">SHOWCASE ARM</span>
        </div>
        <div class="meta">
          <span class="badge ${confClass}">${pct(conf)} signal</span>
          <span class="badge ok">${lead.player.throws || "R"}HP · ${lead.team?.abbr || "MLB"}</span>
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

function wireLiteTeams(data) {
  const grid = document.getElementById("lite-team-grid");
  const filterBtns = document.querySelectorAll(".filter-btn");
  if (!grid) return;

  const nlWestIds = new Set(["ari", "col", "lad", "sd", "sf"]);

  function renderCards(filter = "nlwest") {
    let teams = data.teams || [];
    if (filter === "nlwest") {
      teams = teams.filter((t) => nlWestIds.has(t.id));
    }

    grid.innerHTML = teams
      .map((t) => {
        const allTeamMembers = playersForTeam(data, t.id);
        const pitchers = allTeamMembers.filter((p) => p.role !== "C");
        const catchers = allTeamMembers.filter((p) => p.role === "C");
        const isNlWest = nlWestIds.has(t.id);

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
          <div class="meta" style="margin-bottom:0.5rem;">
            <span class="badge ${tierBadge(p.tier)}">${tierLabel(data, p.tier)}</span>
            <span class="badge ok">${tips.length} Indicators</span>
          </div>
          <p style="font-size:0.82rem; color:var(--muted); margin:0;">${isShow ? "Interactive delivery comparison unlocked →" : "Click to view dossier & request enterprise unlock →"}</p>
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
  const el = document.getElementById("situation-coverage");
  if (!el) return;
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

function wireLitePlayer(data) {
  const id = qs("id") || "eduardo_rodriguez";
  const player = data.players?.[id] || playerList(data).find((p) => p.id === id);
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
    lede.textContent = `${player.role || "SP"} · ${player.throws || "R"}HP · ${(player.pitchesModeled || 0).toLocaleString()} pitches tracked · Computer Vision Broadcast PoC`;
  }
  if (backTeam) {
    backTeam.href = team ? `lite_team.html?id=${encodeURIComponent(team.id)}` : "lite_teams.html";
  }

  const isShow = isShowcaseArm(player.id);
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
      tipRoot.innerHTML =
        tips.map((t) => renderTip(t, angleMap)).join("") || "<p class='note'>No mechanical cues.</p>";
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

    // Always wire modal across all lite pages
    wirePilotModal();
  } catch (err) {
    console.error(err);
    const bootFail = document.getElementById("boot-fail");
    if (bootFail) bootFail.hidden = false;
  }
});
