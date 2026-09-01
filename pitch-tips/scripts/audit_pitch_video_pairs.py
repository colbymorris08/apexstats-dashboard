#!/usr/bin/env python3
"""Audit tip compare panes: pitch codes must differ and MP4 paths/content must differ."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIDEO_DIR = ROOT / "media" / "video"
DEMO = ROOT / "demo.json"

MLB_PREFIXES = {"roupp", "webb", "erod", "pfaadt", "gausman", "gordon"}
SHOWCASE_MLB = {"landen_roupp", "roupp", "logan_webb", "webb", "eduardo_rodriguez", "erod",
                "brandon_pfaadt", "pfaadt", "kevin_gausman", "gausman", "tanner_gordon", "gordon",
                "gabriel_moreno", "moreno"}
SHOWCASE_ALL = SHOWCASE_MLB | {
    "chase_burns", "burns", "roki_sasaki", "sasaki", "won_tae_choi", "choi",
    "gu_lin_ruei_yang", "gu_lin", "gulin", "wilmer_rios", "rios", "hughes", "gabriel_hughes",
}

PITCH_LABEL_BY_CODE = {
    "ff": "Four-Seam Fastball (FF)",
    "si": "2-Seam Sinker (SI)",
    "sl": "Slider (SL)",
    "st": "Sweeper (ST)",
    "ch": "Changeup (CH)",
    "cu": "Curveball (CU)",
    "fs": "Splitter (FS)",
    "fc": "Cutter (FC)",
}

PREDICTS_CONTRAST = {
    "FF": ("Four-Seam Fastball (FF)", "Changeup (CH)"),
    "SI": ("2-Seam Sinker (SI)", "Four-Seam Fastball (FF)"),
    "SL": ("Slider (SL)", "Four-Seam Fastball (FF)"),
    "ST": ("Sweeper (ST)", "Four-Seam Fastball (FF)"),
    "CH": ("Changeup (CH)", "Four-Seam Fastball (FF)"),
    "CU": ("Curveball (CU)", "2-Seam Sinker (SI)"),
    "FS": ("Splitter (FS)", "Four-Seam Fastball (FF)"),
    "FC": ("Cutter (FC)", "Changeup (CH)"),
}

BASELINE = {
    "ff": ["ch", "sl", "si", "cu"],
    "si": ["ff", "ch", "sl"],
    "sl": ["ff", "ch"],
    "st": ["ff", "si"],
    "ch": ["ff", "si"],
    "cu": ["ff", "si", "sl"],
    "fs": ["ff", "ch"],
    "fc": ["ch", "ff"],
}


def md5_file(p: Path) -> str | None:
    if not p.is_file():
        return None
    h = hashlib.md5()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def pitch_code(pitch: str, pid: str = "") -> str:
    p = pitch.lower()
    if "moreno" in pid:
        return "ff" if re.search(r"\bff\b|four|fastball|\(ff\)|\bfast\b|high", p) else "ch"
    paren = [m.group(1) for m in re.finditer(r"\(([a-z]{2})\b", p)]
    valid = set(PITCH_LABEL_BY_CODE)
    for c in paren:
        if c in valid:
            return c
    first = re.split(r"\s*[\/·]\s*|\s+vs\.?\s+", p, maxsplit=1)[0]
    for pat, code in [
        (r"\bff\b|four|fastball|\bfast\b", "ff"),
        (r"split|fork|\bfs\b", "fs"),
        (r"\bst\b|sweeper", "st"),
        (r"curve|\bcu\b|\bcv\b", "cu"),
        (r"change|\bch\b", "ch"),
        (r"slider|\bsl\b", "sl"),
        (r"sweep", "st"),
        (r"sink|\bsi\b", "si"),
        (r"cutter|\bfc\b", "fc"),
    ]:
        if re.search(pat, first):
            return code
    for pat, code in [
        (r"\bff\b|four|fastball|\bfast\b", "ff"),
        (r"split|fork|\bfs\b", "fs"),
        (r"\bst\b|sweeper", "st"),
        (r"curve|\bcu\b|\bcv\b", "cu"),
        (r"change|\bch\b", "ch"),
        (r"slider|\bsl\b", "sl"),
        (r"sweep", "st"),
        (r"sink|\bsi\b", "si"),
        (r"cutter|\bfc\b", "fc"),
    ]:
        if re.search(pat, p):
            return code
    return "ff"


def parse_pitches(tip: dict) -> tuple[str, str]:
    if tip.get("pitch_a_label") and tip.get("pitch_b_label"):
        return tip["pitch_a_label"], tip["pitch_b_label"]
    label = tip.get("contrast_label") or tip.get("contrast") or ""
    parts = re.split(r" vs\.? | vs ", label, maxsplit=1, flags=re.I)
    if len(parts) >= 2:
        return parts[0].strip(), parts[1].strip()
    p = (tip.get("predicts") or "").upper()
    if p in PREDICTS_CONTRAST:
        return PREDICTS_CONTRAST[p]
    return label or "Pitch A", "Four-Seam Fastball (FF)"


def map_pfaadt(code: str) -> str:
    return {"fs": "st", "cu": "ch"}.get(code, code)


def resolve_mlb(pid: str, pitch: str) -> str:
    norm = pid.lower()
    code = pitch_code(pitch, norm)
    if "pfaadt" in norm:
        return f"media/video/pfaadt_{map_pfaadt(code)}.mp4"
    if "roupp" in norm:
        mapped = "sl" if code == "fc" else ("si" if code == "fs" else code)
        return f"media/video/roupp_{mapped}.mp4"
    if "webb" in norm:
        mapped = "sl" if code == "cu" else ("si" if code == "fs" else code)
        return f"media/video/webb_{mapped}.mp4"
    if "erod" in norm or "eduardo" in norm:
        return f"media/video/erod_{code}.mp4"
    if "gausman" in norm:
        mapped = code if code in {"ff", "fs", "sl"} else "ff"
        return f"media/video/gausman_{mapped}.mp4"
    if "gordon" in norm:
        mapped = code if code in {"ff", "ch", "sl"} else "ff"
        return f"media/video/gordon_{mapped}.mp4"
    return ""


def resolve(pid: str, pitch: str, tip: dict, side: str) -> str:
    if side == "A" and tip.get("videoA"):
        return tip["videoA"].split("?")[0]
    if side == "B" and tip.get("videoB"):
        return tip["videoB"].split("?")[0]
    norm = pid.lower()
    if any(k in norm for k in ("roupp", "webb", "erod", "pfaadt", "gausman", "gordon", "eduardo")):
        return resolve_mlb(pid, pitch)
    if "moreno" in norm:
        v = {"ff": "media/video/moreno_ff.mp4", "ch": "media/video/moreno_ch.mp4"}
        c = pitch_code(pitch, norm)
        return v.get(c, v["ff"])
    return ""


def tips(player: dict) -> list:
    t = player.get("tips") or player.get("coachingTips") or []
    if isinstance(t, dict):
        t = list(t.values())
    return sorted(t, key=lambda x: x.get("rank", 99))[:5]


def main() -> int:
    only = "--showcase-only" in sys.argv
    data = json.loads(DEMO.read_text())
    players = data.get("players", data)
    issues: list[str] = []

    for pid_key, player in sorted(players.items()):
        if not isinstance(player, dict):
            continue
        player_id = player.get("id") or pid_key
        if only and player_id not in SHOWCASE_ALL and pid_key not in SHOWCASE_ALL:
            continue
        tlist = tips(player)
        if not tlist:
            continue
        print(f"--- {player.get('name', player_id)} ---")
        for i, tip in enumerate(tlist):
            pa, pb = parse_pitches(tip)
            va = resolve(player_id, pa, tip, "A")
            vb = resolve(player_id, pb, tip, "B")
            ca, cb = pitch_code(pa, player_id), pitch_code(pb, player_id)
            if ca == cb:
                issues.append(f"SAME_PITCH_CODE: {player_id} tip#{i+1} {ca}")
                print(f"  tip#{i+1} !! same pitch code {ca}")
            print(f"  tip#{i+1}: {ca} vs {cb} -> {Path(va).name if va else 'NONE'} | {Path(vb).name if vb else 'NONE'}")
            if va and vb:
                if va == vb:
                    issues.append(f"DUPLICATE_PATH: {player_id} tip#{i+1} {va}")
                ha, hb = md5_file(ROOT / va), md5_file(ROOT / vb)
                if ha and hb and ha == hb:
                    issues.append(f"DUPLICATE_MD5: {player_id} tip#{i+1}")
                if va and not (ROOT / va).is_file():
                    issues.append(f"MISSING: {va}")

    print(f"\n=== {len(issues)} issues ===")
    for iss in issues:
        print(f"  - {iss}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
