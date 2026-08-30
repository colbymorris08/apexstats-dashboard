const STORE_KEY = "apex_preflight_labels_v1";

const state = {
  manifest: null,
  frameIndex: 0,
  classId: null,
  annotations: {}, // frameId -> { boxes: [{classId, x,y,w,h}] }  normalized 0-1
  drag: null,
};

const $ = (id) => document.getElementById(id);

function loadStore() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) state.annotations = JSON.parse(raw).annotations || {};
  } catch {
    state.annotations = {};
  }
}

function saveStore() {
  const payload = {
    version: 1,
    updatedAt: new Date().toISOString(),
    annotations: state.annotations,
  };
  localStorage.setItem(STORE_KEY, JSON.stringify(payload));
  updateStats();
}

function frame() {
  return state.manifest?.frames?.[state.frameIndex] || null;
}

function boxesFor(id) {
  if (!state.annotations[id]) state.annotations[id] = { boxes: [] };
  return state.annotations[id].boxes;
}

// Keep frame metadata with the annotation so earlier batches survive manifest swaps.
function stampMeta(f) {
  const rec = state.annotations[f.id];
  if (!rec) return;
  rec.meta = {
    src: f.src,
    pitcher: f.pitcher,
    team: f.team || null,
    league: f.league || null,
    pitchType: f.pitchType,
    angle: f.angle,
    stadium: f.stadium || null,
    lighting: f.lighting || null,
    delivery: f.delivery || null,
  };
}

function classMeta(id) {
  return state.manifest.classes.find((c) => c.id === id);
}

function renderClasses() {
  const root = $("label-classes");
  root.innerHTML = "";
  state.manifest.classes.forEach((c, i) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "label-class" + (c.id === state.classId ? " active" : "");
    btn.innerHTML = `<span class="label-swatch" style="background:${c.color}"></span><span>${i + 1}. ${c.label}</span>`;
    btn.addEventListener("click", () => {
      state.classId = c.id;
      renderClasses();
    });
    root.appendChild(btn);
  });
}

function updateStats() {
  const ids = Object.keys(state.annotations);
  const labeled = ids.filter((id) => (state.annotations[id].boxes || []).length).length;
  const boxes = ids.reduce((n, id) => n + (state.annotations[id].boxes || []).length, 0);

  const perPitcher = {};
  for (const f of state.manifest.frames) {
    perPitcher[f.pitcher] = perPitcher[f.pitcher] || { done: 0, total: 0 };
    perPitcher[f.pitcher].total += 1;
    if ((state.annotations[f.id]?.boxes || []).length) perPitcher[f.pitcher].done += 1;
  }
  const spread = Object.entries(perPitcher)
    .map(([name, v]) => `${name.split(" ").pop()} ${v.done}/${v.total}`)
    .join(" · ");

  $("label-stats").innerHTML =
    `${labeled} frames labeled · ${boxes} boxes · frame ${state.frameIndex + 1}/${state.manifest.frames.length}` +
    `<br><span style="color:var(--faint)">${spread}</span>`;
}

function renderBoxList() {
  const f = frame();
  const list = $("label-box-list");
  list.innerHTML = "";
  if (!f) return;
  boxesFor(f.id).forEach((b, i) => {
    const m = classMeta(b.classId);
    const li = document.createElement("li");
    li.textContent = `${m?.label || b.classId} ${(b.w * 100).toFixed(0)}×${(b.h * 100).toFixed(0)}%`;
    li.style.borderColor = m?.color || "#888";
    li.title = "Click to delete";
    li.style.cursor = "pointer";
    li.addEventListener("click", () => {
      boxesFor(f.id).splice(i, 1);
      saveStore();
      draw();
      renderBoxList();
    });
    list.appendChild(li);
  });
}

function syncCanvasSize() {
  const img = $("label-img");
  const canvas = $("label-canvas");
  const r = img.getBoundingClientRect();
  canvas.width = Math.round(r.width * devicePixelRatio);
  canvas.height = Math.round(r.height * devicePixelRatio);
  canvas.style.width = `${r.width}px`;
  canvas.style.height = `${r.height}px`;
  draw();
}

function draw() {
  const img = $("label-img");
  const canvas = $("label-canvas");
  const ctx = canvas.getContext("2d");
  const f = frame();
  if (!f || !img.naturalWidth) return;
  ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
  const w = canvas.width / devicePixelRatio;
  const h = canvas.height / devicePixelRatio;
  ctx.clearRect(0, 0, w, h);

  const boxes = boxesFor(f.id);
  for (const b of boxes) {
    const m = classMeta(b.classId);
    ctx.strokeStyle = m?.color || "#ff8c00";
    ctx.lineWidth = 2;
    ctx.strokeRect(b.x * w, b.y * h, b.w * w, b.h * h);
    ctx.fillStyle = m?.color || "#ff8c00";
    ctx.globalAlpha = 0.15;
    ctx.fillRect(b.x * w, b.y * h, b.w * w, b.h * h);
    ctx.globalAlpha = 1;
    ctx.font = "11px IBM Plex Mono, monospace";
    ctx.fillStyle = m?.color || "#ff8c00";
    ctx.fillText(m?.label || b.classId, b.x * w + 4, b.y * h + 14);
  }

  if (state.drag) {
    const { x0, y0, x1, y1 } = state.drag;
    const m = classMeta(state.classId);
    ctx.strokeStyle = m?.color || "#fff";
    ctx.setLineDash([4, 3]);
    ctx.strokeRect(
      Math.min(x0, x1) * w,
      Math.min(y0, y1) * h,
      Math.abs(x1 - x0) * w,
      Math.abs(y1 - y0) * h
    );
    ctx.setLineDash([]);
  }
}

function loadFrameMeta() {
  const f = frame();
  if (!f) return;
  const labeled = (state.annotations[f.id]?.boxes || []).length;
  const hard =
    f.gloveConf !== undefined && f.gloveConf > 0
      ? ` · <span style="color:var(--warn)">model conf ${f.gloveConf}</span>`
      : "";
  const hand =
    f.handConf !== undefined && f.handConf > 0
      ? ` · <span style="color:var(--warn)">bare_hand ${f.handConf}</span>`
      : "";
  const leagueBadge = f.league ? ` <span class="badge" style="background:rgba(61,139,253,0.22); color:var(--accent); font-weight:700;">${f.league}</span>` : "";
  const pos =
    f.windowPos !== undefined
      ? `<br><span style="color:var(--faint)">window: come-set → hand break (${Math.round(f.windowPos * 100)}%)${f.delivery ? ` · ${f.delivery}` : ""}${f.liftFrame != null ? ` · lift f${f.liftFrame}` : ""}</span>`
      : "";
  const locationMeta = (f.stadium || f.lighting)
    ? `<br><span style="color:var(--faint); font-size:0.8rem;">📍 ${f.stadium || ""}${f.lighting ? ` · ${f.lighting}` : ""}</span>`
    : "";

  $("label-frame-meta").innerHTML =
    `<strong>${f.pitcher}</strong>${leagueBadge}${f.team ? ` · ${f.team}` : ""}${f.pitchType && f.pitchType !== "?" ? ` · ${f.pitchType}` : ""}${hard}${hand}${pos}${locationMeta}` +
    `<br><span style="color:${labeled ? "var(--good)" : "var(--faint)"}">${labeled ? `${labeled} boxes saved` : "unlabeled"}</span>`;
}

function loadFrame() {
  const f = frame();
  if (!f) return;
  const img = $("label-img");
  loadFrameMeta();
  img.onload = () => {
    syncCanvasSize();
    renderBoxList();
    updateStats();
  };
  img.src = f.src;
}

function pointerNorm(e) {
  const wrap = $("label-canvas-wrap");
  const r = wrap.getBoundingClientRect();
  return {
    x: Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)),
    y: Math.min(1, Math.max(0, (e.clientY - r.top) / r.height)),
  };
}

function wireCanvas() {
  const wrap = $("label-canvas-wrap");
  wrap.addEventListener("pointerdown", (e) => {
    if (!state.classId) return;
    wrap.setPointerCapture(e.pointerId);
    const p = pointerNorm(e);
    state.drag = { x0: p.x, y0: p.y, x1: p.x, y1: p.y };
    draw();
  });
  wrap.addEventListener("pointermove", (e) => {
    if (!state.drag) return;
    const p = pointerNorm(e);
    state.drag.x1 = p.x;
    state.drag.y1 = p.y;
    draw();
  });
  const end = (e) => {
    if (!state.drag) return;
    const p = pointerNorm(e);
    state.drag.x1 = p.x;
    state.drag.y1 = p.y;
    const { x0, y0, x1, y1 } = state.drag;
    const x = Math.min(x0, x1);
    const y = Math.min(y0, y1);
    const w = Math.abs(x1 - x0);
    const h = Math.abs(y1 - y0);
    state.drag = null;
    if (w > 0.008 && h > 0.008) {
      const f = frame();
      boxesFor(f.id).push({ classId: state.classId, x, y, w, h });
      stampMeta(f);
      saveStore();
      renderBoxList();
      loadFrameMeta();
    }
    draw();
  };
  wrap.addEventListener("pointerup", end);
  wrap.addEventListener("pointercancel", () => {
    state.drag = null;
    draw();
  });
}

function buildExport() {
  const classIndex = Object.fromEntries(state.manifest.classes.map((c, i) => [c.id, i]));
  const images = [];

  const encode = (id, meta, boxes) => ({
    id,
    file_name: meta.src,
    pitcher: meta.pitcher,
    team: meta.team || null,
    pitchType: meta.pitchType,
    angle: meta.angle,
    width: null,
    height: null,
    boxes: boxes.map((b) => ({
      class: b.classId,
      class_id: classIndex[b.classId],
      // YOLO normalized cx,cy,w,h
      yolo: [b.x + b.w / 2, b.y + b.h / 2, b.w, b.h].map((v) => +v.toFixed(6)),
      xywh: [b.x, b.y, b.w, b.h].map((v) => +v.toFixed(6)),
    })),
  });

  const inManifest = new Set();
  for (const f of state.manifest.frames) {
    inManifest.add(f.id);
    const boxes = boxesFor(f.id);
    if (!boxes.length) continue;
    images.push(encode(f.id, f, boxes));
  }

  // Batches labeled against an older manifest still export.
  for (const [id, rec] of Object.entries(state.annotations)) {
    if (inManifest.has(id) || !(rec.boxes || []).length || !rec.meta) continue;
    images.push(encode(id, rec.meta, rec.boxes));
  }
  return {
    format: "apex_preflight_yolo_v1",
    createdAt: new Date().toISOString(),
    angle: state.manifest.angle,
    classes: state.manifest.classes.map((c, i) => ({ id: i, name: c.id, label: c.label })),
    images,
    note: "Drop this JSON in chat or save under data/labels/ for fine-tune.",
  };
}

function downloadJson() {
  const set = new URLSearchParams(location.search).get("set") || "multileague";
  const data = buildExport();
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `apex_labels_${set}_${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
}

function openPdfPacket() {
  const data = buildExport();
  const win = window.open("", "_blank");
  if (!win) {
    alert("Allow pop-ups to open the PDF packet, then Print → Save as PDF.");
    return;
  }
  const rows = data.images
    .map(
      (im) => `
      <section style="page-break-inside:avoid;margin:0 0 18px;border-bottom:1px solid #ddd;padding-bottom:12px">
        <h3 style="margin:0 0 6px;font:600 14px Manrope,sans-serif">${im.pitcher} · ${im.pitchType} · ${im.id}</h3>
        <img src="${im.file_name}" style="max-width:100%;height:auto;border:1px solid #ccc" />
        <ul style="font:12px IBM Plex Mono,monospace;color:#333">
          ${im.boxes.map((b) => `<li>${b.class} · yolo ${b.yolo.join(", ")}</li>`).join("")}
        </ul>
      </section>`
    )
    .join("");
  win.document.write(`<!DOCTYPE html><html><head><title>Preflight label packet</title>
    <style>body{font-family:Manrope,sans-serif;padding:24px;color:#111} h1{font-size:18px}</style></head>
    <body>
      <h1>Preflight · part labels (CF)</h1>
      <p>${data.images.length} frames · ${data.images.reduce((n, i) => n + i.boxes.length, 0)} boxes · ${data.createdAt}</p>
      <p>Print this page → Save as PDF, then send the PDF + the JSON export in chat for YOLO fine-tune.</p>
      ${rows || "<p>No boxes yet.</p>"}
      <script>setTimeout(()=>print(),400)<\\/script>
    </body></html>`);
  win.document.close();
}

function go(delta) {
  const n = state.manifest.frames.length;
  state.frameIndex = (state.frameIndex + delta + n) % n;
  loadFrame();
}

function goNextUnlabeled() {
  const frames = state.manifest.frames;
  for (let step = 1; step <= frames.length; step += 1) {
    const idx = (state.frameIndex + step) % frames.length;
    if (!(state.annotations[frames[idx].id]?.boxes || []).length) {
      state.frameIndex = idx;
      loadFrame();
      return;
    }
  }
  alert("Every frame in this manifest has boxes. Export the JSON and I'll pull a fresh pool.");
}

const MANIFESTS = {
  multileague: "data/label_manifest_multileague.json",
  ncaa: "data/label_manifest_ncaa.json",
  npb: "data/label_manifest_npb.json",
  kbo: "data/label_manifest_kbo.json",
  cpbl: "data/label_manifest_cpbl.json",
  lmb: "data/label_manifest_lmb.json",
  parts: "data/label_manifest.json",
  gloves: "data/label_manifest_gloves.json",
  hands: "data/label_manifest_hands.json",
};

function highlightActiveDatasetButton(activeSet) {
  document.querySelectorAll("[data-set-btn]").forEach((btn) => {
    const btnSet = btn.getAttribute("data-set-btn");
    if (btnSet === activeSet) {
      btn.className = "btn";
      btn.style.boxShadow = "0 0 0 2px var(--accent)";
    } else {
      btn.className = "btn ghost";
      btn.style.boxShadow = "none";
    }
  });
}

async function main() {
  loadStore();
  const set = new URLSearchParams(location.search).get("set") || "multileague";
  highlightActiveDatasetButton(set);

  try {
    const res = await fetch(MANIFESTS[set] || MANIFESTS.multileague);
    if (!res.ok) throw new Error("Manifest load failed");
    state.manifest = await res.json();
  } catch (err) {
    console.warn("Falling back to multileague manifest:", err);
    const res = await fetch(MANIFESTS.multileague);
    state.manifest = await res.json();
  }

  state.classId = state.manifest.classes[0]?.id || null;
  renderClasses();
  wireCanvas();
  loadFrame();

  $("btn-prev").onclick = () => go(-1);
  $("btn-next").onclick = () => go(1);
  $("btn-next-unlabeled").onclick = goNextUnlabeled;
  $("btn-undo").onclick = () => {
    const f = frame();
    const boxes = boxesFor(f.id);
    boxes.pop();
    saveStore();
    draw();
    renderBoxList();
  };
  $("btn-clear").onclick = () => {
    const f = frame();
    state.annotations[f.id] = { boxes: [] };
    saveStore();
    draw();
    renderBoxList();
  };
  $("btn-export-json").onclick = downloadJson;
  $("btn-export-pdf").onclick = openPdfPacket;

  window.addEventListener("resize", syncCanvasSize);
  window.addEventListener("keydown", (e) => {
    if (e.target.matches("input,textarea")) return;
    if (e.key === "n" || e.key === "ArrowRight") go(1);
    if (e.key === "p" || e.key === "ArrowLeft") go(-1);
    if (e.key === "z") $("btn-undo").click();
    if (e.key === "u") goNextUnlabeled();
    if (e.key === "s") downloadJson();
    const num = parseInt(e.key, 10);
    if (num >= 1 && num <= state.manifest.classes.length) {
      state.classId = state.manifest.classes[num - 1].id;
      renderClasses();
    }
  });
}

main();
