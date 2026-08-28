async function loadProgress() {
  const res = await fetch("data/progress.json", { cache: "no-store" });
  if (!res.ok) throw new Error("No progress.json yet");
  return res.json();
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
    if (lede) {
      const scope = p.scope ? `${p.scope} · ` : "";
      const catchers = Object.keys(p.catchers_done || {}).length;
      lede.textContent = `${scope}${p.status || "running"} · ${done}/${total} pitchers · ${catchers} catchers · ${pct(done, total)} · sec/pitch ≈ ${p.sec_per_pitch || "—"}${eta}`;
    }
    if (stats) {
      stats.innerHTML = `
        <div><span>Current</span><strong>${p.current?.name || "—"}</strong></div>
        <div><span>Team</span><strong>${p.current?.team || "—"}</strong></div>
        <div><span>Pitch tips ≥75%</span><strong>${p.totals?.pitcher_tips || 0}</strong></div>
        <div><span>Catcher tips ≥75%</span><strong>${p.totals?.catcher_tips || 0}</strong></div>
        <div><span>Failed</span><strong>${failed}</strong></div>
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
          return `<tr>
            <td>${t}</td>
            <td>${row.done || 0}</td>
            <td>${row.queued || 0}</td>
            <td>${row.pitcher_tips || 0}</td>
            <td>${row.catcher_tips || 0}</td>
          </tr>`;
        })
        .join("");
    }
    const players = [
      ...Object.values(p.done || {}).map((x) => ({ ...x, status: "done", tips_ge_75: x.tips_ge_75, catcher_tips: x.catcher_tips })),
      ...Object.values(p.catchers_done || {}).map((x) => ({
        ...x,
        status: `catcher-${x.role || "C"}`,
        tips_ge_75: 0,
        catcher_tips: x.tips_ge_75,
      })),
      ...Object.values(p.failed || {}).map((x) => ({ ...x, status: "failed" })),
    ].sort((a, b) => (a.team || "").localeCompare(b.team || "") || (a.name || "").localeCompare(b.name || ""));
    if (playersBody) {
      playersBody.innerHTML = players
        .slice(0, 300)
        .map(
          (x) => `<tr>
          <td>${x.name || "—"}</td>
          <td>${x.team || "—"}</td>
          <td>${x.status}</td>
          <td>${x.n_tracked ?? "—"}</td>
          <td>${x.tips_ge_75 ?? 0}</td>
          <td>${x.catcher_tips ?? 0}</td>
        </tr>`
        )
        .join("");
    }
  } catch (e) {
    if (lede) lede.textContent = "Waiting for league scaler to write data/progress.json…";
    console.error(e);
  }
});
