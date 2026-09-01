#!/usr/bin/env python3
"""Audit videoA/videoB resolution for showcase (and optionally all) players in demo.json.

Mirrors the live JS rules in app.js / lite_app.js:
  - parenthetical pitch codes preferred
  - distinct same-player pair when codes collapse
  - MD5 must not match any MLB-prefixed file
  - videoA and videoB must be distinct paths AND distinct content
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIDEO_DIR = ROOT / "media" / "video"
DEMO = ROOT / "demo.json"

MLB_PREFIXES = {"roupp", "webb", "erod", "pfaadt", "gausman", "gordon"}
SHOWCASE = {
    "chase_burns", "burns", "roki_sasaki", "sasaki", "gabriel_moreno", "moreno",
    "won_tae_choi", "gu_lin_ruei_yang", "gu_lin", "gulin", "wilmer_rios", "rios",
    "hughes", "gabriel_hughes",
}

VERIFIED = {
    "chase_burns": {"ff": "media/video/burns_ff.mp4", "sl": "media/video/burns_sl.mp4", "ch": "media/video/burns_ch.mp4", "cu": "media/video/burns_ch.mp4", "si": "media/video/burns_ff.mp4", "fc": "media/video/burns_sl.mp4", "fs": "media/video/burns_ch.mp4"},
    "burns": {"ff": "media/video/burns_ff.mp4", "sl": "media/video/burns_sl.mp4", "ch": "media/video/burns_ch.mp4", "cu": "media/video/burns_ch.mp4", "si": "media/video/burns_ff.mp4", "fc": "media/video/burns_sl.mp4", "fs": "media/video/burns_ch.mp4"},
    "roki_sasaki": {"ff": "media/video/sasaki_ff.mp4", "fs": "media/video/sasaki_fs.mp4", "sl": "media/video/sasaki_ff.mp4", "ch": "media/video/sasaki_fs.mp4", "cu": "media/video/sasaki_fs.mp4", "si": "media/video/sasaki_ff.mp4", "fc": "media/video/sasaki_ff.mp4"},
    "sasaki": {"ff": "media/video/sasaki_ff.mp4", "fs": "media/video/sasaki_fs.mp4", "sl": "media/video/sasaki_ff.mp4", "ch": "media/video/sasaki_fs.mp4", "cu": "media/video/sasaki_fs.mp4", "si": "media/video/sasaki_ff.mp4", "fc": "media/video/sasaki_ff.mp4"},
    "won_tae_choi": {"si": "media/video/choi_si.mp4", "ch": "media/video/choi_ch.mp4", "ff": "media/video/choi_si.mp4", "sl": "media/video/choi_ch.mp4", "cu": "media/video/choi_ch.mp4", "fs": "media/video/choi_ch.mp4", "fc": "media/video/choi_ch.mp4"},
    "gu_lin_ruei_yang": {"ff": "media/video/gulin_ff.mp4", "cu": "media/video/gulin_cu.mp4", "sl": "media/video/gulin_cu.mp4", "ch": "media/video/gulin_cu.mp4", "fs": "media/video/gulin_cu.mp4", "si": "media/video/gulin_ff.mp4", "fc": "media/video/gulin_cu.mp4"},
    "gulin": {"ff": "media/video/gulin_ff.mp4", "cu": "media/video/gulin_cu.mp4", "sl": "media/video/gulin_cu.mp4", "ch": "media/video/gulin_cu.mp4", "fs": "media/video/gulin_cu.mp4", "si": "media/video/gulin_ff.mp4", "fc": "media/video/gulin_cu.mp4"},
    "gu_lin": {"ff": "media/video/gulin_ff.mp4", "cu": "media/video/gulin_cu.mp4", "sl": "media/video/gulin_cu.mp4", "ch": "media/video/gulin_cu.mp4", "fs": "media/video/gulin_cu.mp4", "si": "media/video/gulin_ff.mp4", "fc": "media/video/gulin_cu.mp4"},
    "wilmer_rios": {"si": "media/video/rios_si.mp4", "sl": "media/video/rios_sl.mp4", "ch": "media/video/rios_sl.mp4", "cu": "media/video/rios_sl.mp4", "ff": "media/video/rios_si.mp4", "fc": "media/video/rios_sl.mp4", "fs": "media/video/rios_sl.mp4"},
    "rios": {"si": "media/video/rios_si.mp4", "sl": "media/video/rios_sl.mp4", "ch": "media/video/rios_sl.mp4", "cu": "media/video/rios_sl.mp4", "ff": "media/video/rios_si.mp4", "fc": "media/video/rios_sl.mp4", "fs": "media/video/rios_sl.mp4"},
    "hughes": {"ff": "media/video/hughes_ff.mp4", "sl": "media/video/hughes_sl.mp4", "ch": "media/video/hughes_sl.mp4", "si": "media/video/hughes_ff.mp4", "cu": "media/video/hughes_sl.mp4", "fc": "media/video/hughes_sl.mp4", "fs": "media/video/hughes_sl.mp4"},
    "gabriel_hughes": {"ff": "media/video/hughes_ff.mp4", "sl": "media/video/hughes_sl.mp4", "ch": "media/video/hughes_sl.mp4", "si": "media/video/hughes_ff.mp4", "cu": "media/video/hughes_sl.mp4", "fc": "media/video/hughes_sl.mp4", "fs": "media/video/hughes_sl.mp4"},
    "gabriel_moreno": {"ff": "media/video/moreno_ff.mp4", "ch": "media/video/moreno_ch.mp4", "sl": "media/video/moreno_ch.mp4", "cu": "media/video/moreno_ch.mp4", "si": "media/video/moreno_ff.mp4", "fc": "media/video/moreno_ch.mp4", "fs": "media/video/moreno_ch.mp4"},
    "moreno": {"ff": "media/video/moreno_ff.mp4", "ch": "media/video/moreno_ch.mp4", "sl": "media/video/moreno_ch.mp4", "cu": "media/video/moreno_ch.mp4", "si": "media/video/moreno_ff.mp4", "fc": "media/video/moreno_ch.mp4", "fs": "media/video/moreno_ch.mp4"},
}

UNIQUE = {
    "chase_burns": ["media/video/burns_ff.mp4", "media/video/burns_sl.mp4", "media/video/burns_ch.mp4"],
    "burns": ["media/video/burns_ff.mp4", "media/video/burns_sl.mp4", "media/video/burns_ch.mp4"],
    "roki_sasaki": ["media/video/sasaki_ff.mp4", "media/video/sasaki_fs.mp4"],
    "sasaki": ["media/video/sasaki_ff.mp4", "media/video/sasaki_fs.mp4"],
    "won_tae_choi": ["media/video/choi_si.mp4", "media/video/choi_ch.mp4"],
    "gu_lin_ruei_yang": ["media/video/gulin_ff.mp4", "media/video/gulin_cu.mp4"],
    "gulin": ["media/video/gulin_ff.mp4", "media/video/gulin_cu.mp4"],
    "gu_lin": ["media/video/gulin_ff.mp4", "media/video/gulin_cu.mp4"],
    "wilmer_rios": ["media/video/rios_si.mp4", "media/video/rios_sl.mp4"],
    "rios": ["media/video/rios_si.mp4", "media/video/rios_sl.mp4"],
    "hughes": ["media/video/hughes_ff.mp4", "media/video/hughes_sl.mp4"],
    "gabriel_hughes": ["media/video/hughes_ff.mp4", "media/video/hughes_sl.mp4"],
    "gabriel_moreno": ["media/video/moreno_ff.mp4", "media/video/moreno_ch.mp4"],
    "moreno": ["media/video/moreno_ff.mp4", "media/video/moreno_ch.mp4"],
}


def md5_file(p: Path) -> str | None:
    if not p.is_file():
        return None
    h = hashlib.md5()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def mp4_duration(path: Path) -> float | None:
    try:
        data = path.read_bytes()
        i = data.find(b"mvhd")
        if i < 0:
            return None
        version = data[i + 4]
        if version == 1:
            timescale = struct.unpack(">I", data[i + 24 : i + 28])[0]
            duration = struct.unpack(">Q", data[i + 28 : i + 36])[0]
        else:
            timescale = struct.unpack(">I", data[i + 16 : i + 20])[0]
            duration = struct.unpack(">I", data[i + 20 : i + 24])[0]
        return duration / timescale if timescale else None
    except Exception:
        return None


def parse_pitches(tip: dict) -> tuple[str, str]:
    if tip.get("pitch_a_label") and tip.get("pitch_b_label"):
        return tip["pitch_a_label"], tip["pitch_b_label"]
    label = tip.get("contrast_label") or tip.get("contrast") or ""
    parts = re.split(r" vs\.? | / | vs ", label, maxsplit=1, flags=re.I)
    if len(parts) >= 2:
        return parts[0].strip(), parts[1].strip()
    p = (tip.get("predicts") or "").upper()
    defaults = {
        "FF": ("Four-Seam (FF)", "Curveball (CU)"),
        "SL": ("Slider (SL)", "Fastball (FF)"),
        "CH": ("Changeup (CH)", "Sinker (SI)"),
        "FS": ("Splitter (FS)", "Fastball (FF)"),
        "SI": ("Sinker (SI)", "Four-Seam (FF)"),
        "CU": ("Curveball (CU)", "Sinker (SI)"),
        "FC": ("Cutter (FC)", "Changeup (CH)"),
    }
    return defaults.get(p, (label or "Pitch A", "Pitch B"))


def pitch_code(pitch: str, pid: str) -> str:
    p = pitch.lower()
    if "moreno" in pid:
        return "ff" if re.search(r"\bff\b|four|fastball|\(ff\)|\bfast\b|high", p) else "ch"
    paren = [m.group(1) for m in re.finditer(r"\(([a-z]{2})\b", p)]
    valid = {"ff", "si", "sl", "ch", "cu", "fs", "fc", "st"}
    for c in paren:
        if c in valid:
            return "sl" if c == "st" else c
    first = re.split(r"\s*[\/·]\s*|\s+vs\.?\s+", p, maxsplit=1)[0]
    for pat, code in [
        (r"\bff\b|four|fastball|\bfast\b", "ff"),
        (r"split|fork|\bfs\b", "fs"),
        (r"curve|\bcu\b|\bcv\b", "cu"),
        (r"change|\bch\b", "ch"),
        (r"slider|\bsl\b|sweep", "sl"),
        (r"sink|\bsi\b", "si"),
        (r"cutter|\bfc\b", "fc"),
    ]:
        if re.search(pat, first):
            return code
    for pat, code in [
        (r"\bff\b|four|fastball|\bfast\b", "ff"),
        (r"split|fork|\bfs\b", "fs"),
        (r"curve|\bcu\b|\bcv\b", "cu"),
        (r"change|\bch\b", "ch"),
        (r"slider|\bsl\b|sweep", "sl"),
        (r"sink|\bsi\b", "si"),
        (r"cutter|\bfc\b", "fc"),
    ]:
        if re.search(pat, p):
            return code
    return "ff"


def resolve_key(pid: str) -> str | None:
    if pid in VERIFIED:
        return pid
    for key in sorted(VERIFIED, key=len, reverse=True):
        if key in pid or pid in key:
            return key
    return None


def ensure_distinct(pid: str, va: str, vb: str) -> tuple[str, str]:
    key = resolve_key(pid) or ""
    clips = UNIQUE.get(key) or []
    a = va or (clips[0] if clips else "")
    b = vb or (clips[1] if len(clips) > 1 else (clips[0] if clips else ""))
    if a and b and a == b and len(clips) >= 2:
        b = next(c for c in clips if c != a)
    return a, b


def resolve(pid: str, pitch: str, tip: dict, side: str) -> str:
    if side == "A" and tip.get("videoA"):
        return tip["videoA"].split("?")[0]
    if side == "B" and tip.get("videoB"):
        return tip["videoB"].split("?")[0]
    key = resolve_key(pid)
    if not key:
        return ""
    v = VERIFIED[key]
    code = pitch_code(pitch, key)
    return (v.get(code) or v.get("ff") or v.get("ch") or next(iter(v.values()))).split("?")[0]


def tips(player: dict) -> list:
    t = player.get("tips") or player.get("coachingTips") or []
    if isinstance(t, dict):
        t = list(t.values())
    return sorted(t, key=lambda x: x.get("rank", 99))[:5]


def main() -> int:
    showcase_only = "--showcase-only" in sys.argv
    data = json.loads(DEMO.read_text())
    players = data.get("players", data)

    mlb_hs: set[str] = set()
    for f in VIDEO_DIR.glob("*.mp4"):
        if f.name.split("_")[0] in MLB_PREFIXES:
            h = md5_file(f)
            if h:
                mlb_hs.add(h)

    hash_owners: dict[str, list[str]] = defaultdict(list)
    for f in VIDEO_DIR.glob("*.mp4"):
        h = md5_file(f)
        if h:
            hash_owners[h].append(f.name)

    issues: list[str] = []
    rows: list[dict] = []
    print(f"Auditing {'showcase' if showcase_only else 'all'} players\n")

    seen_ids: set[str] = set()
    for pid_key, player in sorted(players.items()):
        if not isinstance(player, dict):
            continue
        player_id = player.get("id") or pid_key
        if showcase_only and player_id not in SHOWCASE and pid_key not in SHOWCASE:
            continue
        if player_id in seen_ids:
            continue
        seen_ids.add(player_id)
        tlist = tips(player)
        if not tlist:
            continue
        print(f"--- {player.get('name', pid_key)} ({player_id}) ---")
        for i, tip in enumerate(tlist):
            pa, pb = parse_pitches(tip)
            va = resolve(player_id, pa, tip, "A")
            vb = resolve(player_id, pb, tip, "B")
            if player_id in SHOWCASE or resolve_key(player_id):
                va, vb = ensure_distinct(player_id, va, vb)
            tA = tip.get("anchor_a", tip.get("tA"))
            tB = tip.get("anchor_b", tip.get("tB"))
            print(f"  tip#{i+1}: A={va or 'NONE'}  B={vb or 'NONE'}  tA={tA} tB={tB}")

            if not va or not vb:
                msg = f"MISSING: {player_id} tip#{i+1}"
                issues.append(msg)
                print(f"    !! {msg}")
                continue
            if va == vb:
                msg = f"DUPLICATE_PATH: {player_id} tip#{i+1} {va}"
                issues.append(msg)
                print(f"    !! {msg}")

            ha = hb = None
            for label, v in [("A", va), ("B", vb)]:
                path = ROOT / v
                if not path.is_file():
                    msg = f"NOT_ON_DISK: {player_id} tip#{i+1} video{label} -> {v}"
                    issues.append(msg)
                    print(f"    !! {msg}")
                    continue
                h = md5_file(path)
                if label == "A":
                    ha = h
                else:
                    hb = h
                if h in mlb_hs:
                    msg = f"MLB_IMPERSONATOR: {player_id} tip#{i+1} video{label} ({v})"
                    issues.append(msg)
                    print(f"    !! {msg}")
                owners = [o for o in hash_owners.get(h or "", []) if o != Path(v).name]
                cross = [o for o in owners if o.split("_")[0] != Path(v).name.split("_")[0]]
                if cross:
                    msg = f"MD5_COLLISION: {v} == {cross[0]}"
                    if msg not in issues:
                        issues.append(msg)
                        print(f"    !! {msg}")

            if ha and hb and ha == hb:
                msg = f"DUPLICATE_MD5: {player_id} tip#{i+1} ({va} == {vb})"
                issues.append(msg)
                print(f"    !! {msg}")

            if i == 0:
                rows.append({
                    "player": player.get("name", player_id),
                    "videoA": va,
                    "videoB": vb,
                    "md5A": ha,
                    "md5B": hb,
                    "samePath": va == vb,
                    "sameHash": ha == hb,
                    "mlbA": ha in mlb_hs if ha else None,
                    "mlbB": hb in mlb_hs if hb else None,
                    "durA": mp4_duration(ROOT / va) if va else None,
                    "durB": mp4_duration(ROOT / vb) if vb else None,
                    "tA": tA,
                    "tB": tB,
                })

    print("\n=== VERIFICATION TABLE (tip #1) ===")
    print(f"{'player':22} {'videoA':22} {'videoB':22} {'A==B':5} {'mlbA':5} {'mlbB':5} {'durA':6} {'durB':6} {'tA':5} {'tB':5}")
    for r in rows:
        print(
            f"{r['player'][:22]:22} {Path(r['videoA']).name:22} {Path(r['videoB']).name:22} "
            f"{str(r['samePath']):5} {str(r['mlbA']):5} {str(r['mlbB']):5} "
            f"{(f'{r['durA']:.2f}' if r['durA'] else '-'):6} {(f'{r['durB']:.2f}' if r['durB'] else '-'):6} "
            f"{str(r['tA']):5} {str(r['tB']):5}"
        )
        print(f"  md5A={r['md5A']}  md5B={r['md5B']}")

    print(f"\n=== SUMMARY: {len(issues)} issues ===")
    for iss in issues:
        print(f"  - {iss}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
