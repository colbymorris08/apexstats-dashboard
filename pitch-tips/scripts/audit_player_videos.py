#!/usr/bin/env python3
"""Audit videoA/videoB resolution for every player in demo.json."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIDEO_DIR = ROOT / "media" / "video"
DEMO = ROOT / "demo.json"

MLB_PREFIXES = {"roupp", "webb", "erod", "pfaadt", "gausman", "gordon"}
NON_MLB = {"burns", "sasaki", "choi", "gulin", "rios", "hughes", "moreno"}
SHOWCASE = {
    "chase_burns", "burns", "roki_sasaki", "sasaki", "gabriel_moreno", "moreno",
    "won_tae_choi", "gu_lin_ruei_yang", "gu_lin", "gulin", "wilmer_rios", "rios",
    "hughes", "gabriel_hughes",
}

VERIFIED = {
    "chase_burns": {"ff": "media/video/burns_ff.mp4", "sl": "media/video/burns_sl.mp4", "ch": "media/video/burns_ch.mp4", "cu": "media/video/burns_ch.mp4"},
    "burns": {"ff": "media/video/burns_ff.mp4", "sl": "media/video/burns_sl.mp4", "ch": "media/video/burns_ch.mp4", "cu": "media/video/burns_ch.mp4"},
    "roki_sasaki": {"ff": "media/video/sasaki_ff.mp4", "fs": "media/video/sasaki_fs.mp4", "sl": "media/video/sasaki_fs.mp4"},
    "sasaki": {"ff": "media/video/sasaki_ff.mp4", "fs": "media/video/sasaki_fs.mp4", "sl": "media/video/sasaki_fs.mp4"},
    "won_tae_choi": {"si": "media/video/choi_si.mp4", "ch": "media/video/choi_ch.mp4", "ff": "media/video/choi_si.mp4", "sl": "media/video/choi_ch.mp4", "cu": "media/video/choi_ch.mp4"},
    "gu_lin_ruei_yang": {"ff": "media/video/gulin_ff.mp4", "cu": "media/video/gulin_cu.mp4", "sl": "media/video/gulin_cu.mp4", "ch": "media/video/gulin_cu.mp4"},
    "gulin": {"ff": "media/video/gulin_ff.mp4", "cu": "media/video/gulin_cu.mp4", "sl": "media/video/gulin_cu.mp4", "ch": "media/video/gulin_cu.mp4"},
    "wilmer_rios": {"si": "media/video/rios_si.mp4", "sl": "media/video/rios_sl.mp4", "ch": "media/video/rios_ch.mp4", "cu": "media/video/rios_sl.mp4", "ff": "media/video/rios_si.mp4"},
    "rios": {"si": "media/video/rios_si.mp4", "sl": "media/video/rios_sl.mp4", "ch": "media/video/rios_ch.mp4", "cu": "media/video/rios_sl.mp4", "ff": "media/video/rios_si.mp4"},
    "hughes": {"ff": "media/video/hughes_ff.mp4", "sl": "media/video/hughes_sl.mp4", "ch": "media/video/hughes_sl.mp4"},
    "gabriel_hughes": {"ff": "media/video/hughes_ff.mp4", "sl": "media/video/hughes_sl.mp4", "ch": "media/video/hughes_sl.mp4"},
    "gabriel_moreno": {"ff": "media/video/moreno_ff.mp4", "ch": "media/video/moreno_ch.mp4", "sl": "media/video/moreno_ch.mp4"},
    "moreno": {"ff": "media/video/moreno_ff.mp4", "ch": "media/video/moreno_ch.mp4", "sl": "media/video/moreno_ch.mp4"},
}


def md5_file(p: Path) -> str | None:
    if not p.is_file():
        return None
    h = hashlib.md5()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def parse_pitches(tip: dict) -> tuple[str, str]:
    if tip.get("pitch_a_label") and tip.get("pitch_b_label"):
        return tip["pitch_a_label"], tip["pitch_b_label"]
    label = tip.get("contrast_label") or tip.get("contrast") or ""
    parts = re.split(r" vs\.? | / | vs ", label, maxsplit=1)
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
    }
    return defaults.get(p, (label or "Pitch A", "Pitch B"))


def pitch_code(pitch: str, pid: str) -> str:
    p = pitch.lower()
    if "moreno" in pid:
        return "ff" if re.search(r"\bff\b|four|fastball|\(ff\)|\bfast\b|high", p) else "ch"
    if re.search(r"\bff\b|four|fastball|\(ff\)|\bfast\b", p):
        return "ff"
    if re.search(r"split|fork|\bfs\b", p):
        return "fs"
    if re.search(r"curve|\bcu\b", p):
        return "cu"
    if re.search(r"change|\bch\b", p):
        return "ch"
    if re.search(r"slider|\bsl\b|sweep", p):
        return "sl"
    if re.search(r"sink|\bsi\b", p):
        return "si"
    if re.search(r"cutter|\bfc\b", p):
        return "fc"
    return "ff"


def resolve(pid: str, pitch: str, tip: dict) -> str:
    if tip.get("videoA") and pitch == parse_pitches(tip)[0]:
        return tip["videoA"]
    if tip.get("videoB") and pitch == parse_pitches(tip)[1]:
        return tip["videoB"]
    v = VERIFIED.get(pid) or VERIFIED.get(pid.split("_")[-1] if "_" in pid else pid)
    if v:
        return v.get(pitch_code(pitch, pid), "")
    return ""


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
    print(f"Auditing {'showcase' if showcase_only else 'all'} players\n")

    for pid, player in sorted(players.items()):
        if not isinstance(player, dict):
            continue
        player_id = player.get("id") or pid
        if showcase_only and player_id not in SHOWCASE and pid not in SHOWCASE:
            continue
        tlist = tips(player)
        if not tlist:
            continue
        print(f"--- {player.get('name', pid)} ({player_id}) ---")
        for i, tip in enumerate(tlist):
            pa, pb = parse_pitches(tip)
            va, vb = resolve(player_id, pa, tip), resolve(player_id, pb, tip)
            print(f"  tip#{i+1}: A={va or 'NONE'}  B={vb or 'NONE'}")
            if va and vb and va == vb:
                msg = f"DUPLICATE: {player_id} tip#{i+1} videoA===videoB ({va})"
                issues.append(msg)
                print(f"    !! {msg}")
            for label, v in [("A", va), ("B", vb)]:
                if not v:
                    if "arsenal" not in (pa + pb).lower():
                        msg = f"MISSING: {player_id} tip#{i+1} video{label}"
                        issues.append(msg)
                        print(f"    !! {msg}")
                    continue
                rel = v.replace("media/video/", "")
                path = VIDEO_DIR / rel
                if not path.is_file():
                    msg = f"NOT_ON_DISK: {player_id} tip#{i+1} video{label} -> {v}"
                    issues.append(msg)
                    print(f"    !! {msg}")
                    continue
                h = md5_file(path)
                if h in mlb_hs:
                    msg = f"MLB_IMPERSONATOR: {player_id} tip#{i+1} video{label} ({v})"
                    issues.append(msg)
                    print(f"    !! {msg}")
                owners = [o for o in hash_owners.get(h or "", []) if o != rel]
                cross = [o for o in owners if o.split("_")[0] != rel.split("_")[0]]
                if cross:
                    msg = f"MD5_COLLISION: {v} == {cross[0]}"
                    if msg not in issues:
                        issues.append(msg)
                        print(f"    !! {msg}")

    print(f"\n=== SUMMARY: {len(issues)} issues ===")
    for iss in issues:
        print(f"  - {iss}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
