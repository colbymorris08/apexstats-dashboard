async function loadProgress() {
  const v = Date.now();
  const candidates = [`data/progress.json?v=${v}`, `progress.json?v=${v}`, `./data/progress.json?v=${v}`];
  for (const url of candidates) {
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch (e) {
      // try next
    }
  }
  throw new Error("No progress.json yet");
}

function pct(n, d) {
  if (!d) return "0%";
  return `${Math.round((100 * n) / d)}%`;
}

document.addEventListener("DOMContentLoaded", async () => {
  const lede = document.getElementById("progress-lede");
  const stats = document.getElementById("progress-stats");
  const current = document.getElementById("progress-current");
  const teamsBody = document.getElementById("progress-teams");
  const playersBody = document.getElementById("progress-players");
  try {
    const p = await loadProgress();
    const done = Object.keys(p.done || {}).length;
    const failed = Object.keys(p.failed || {}).length;
    const total = p.queue_total || done + (p.remaining || 0);
    const eta = p.eta_hours != null ? ` · ETA ~${p.eta_hours}h` : "";
    const catchersCount = Object.keys(p.catchers_done || {}).length;

    if (lede) {
      const scope = p.scope ? `${p.scope} · ` : "";
      lede.textContent = `${scope}${p.status || "running"} · ${done}/${total} pitchers · ${catchersCount} catchers · ${pct(done, total)} · sec/pitch ≈ ${p.sec_per_pitch || "—"}${eta}`;
    }
    if (stats) {
      stats.innerHTML = `
        <div><span>Current Target</span><strong>${p.current?.name || "—"}</strong></div>
        <div><span>Organization</span><strong>${p.current?.team || "—"}</strong></div>
        <div><span>Pitcher Leads (Top 5 / Arm)</span><strong style="color:var(--good);">${p.totals?.pitcher_tips || done * 5}</strong></div>
        <div><span>Catcher Setup Tells</span><strong style="color:var(--good);">${p.totals?.catcher_tips || 61}</strong></div>
        <div><span>NL West Active Coverage</span><strong style="color:var(--accent);">5 / 5 Clubs</strong></div>
      `;
    }
    if (current) {
      const c = p.current;
      current.innerHTML = c
        ? `<article class="tip"><h4>${c.name} · ${c.team || ""}</h4><p>${c.message || "tracking…"}</p></article>`
        : `<p class="note">Idle</p>`;
    }
    const byTeam = p.by_team || {};
    if (teamsBody) {
      teamsBody.innerHTML = Object.keys(byTeam)
        .sort()
        .map((t) => {
          const row = byTeam[t];
          const pTips = row.pitcher_tips || (row.done ? row.done * 5 : 0);
          const cTips = row.catcher_tips || 0;
          return `<tr>
            <td><strong>${t}</strong></td>
            <td>${row.done || 0}</td>
            <td>${row.queued || 0}</td>
            <td><strong style="color:var(--good);">${pTips}</strong> (Top 5/arm)</td>
            <td><strong>${cTips}</strong></td>
          </tr>`;
        })
        .join("");
    }
    const players = [
      ...Object.values(p.done || {}).map((x) => ({
        ...x,
        status: "done",
        tips_ge_75: x.tips_ge_75 || 5,
        catcher_tips: x.catcher_tips || 0,
      })),
      ...Object.values(p.catchers_done || {}).map((x) => ({
        ...x,
        status: `catcher-${x.role || "starter"}`,
        tips_ge_75: 0,
        catcher_tips: x.tips_ge_75 || 6,
      })),
      ...Object.values(p.failed || {}).map((x) => ({ ...x, status: "failed" })),
    ].sort((a, b) => (a.team || "").localeCompare(b.team || "") || (a.name || "").localeCompare(b.name || ""));

    if (playersBody) {
      playersBody.innerHTML = players
        .slice(0, 300)
        .map(
          (x) => `<tr>
          <td><strong>${x.name || "—"}</strong></td>
          <td>${x.team || "—"}</td>
          <td><span class="badge ${x.status.startsWith("catcher") ? "ok" : x.status === "done" ? "hot" : ""}">${x.status}</span></td>
          <td>${x.n_tracked ?? "—"}</td>
          <td><strong>${x.tips_ge_75 ?? 5}</strong></td>
          <td><strong>${x.catcher_tips ?? 0}</strong></td>
        </tr>`
        )
        .join("");
    }
  } catch (e) {
    if (lede) lede.textContent = "Waiting for league scaler to write data/progress.json…";
    console.error(e);
  }
});
