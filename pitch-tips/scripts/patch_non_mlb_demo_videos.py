#!/usr/bin/env python3
"""Patch non-MLB showcase tips with verified video paths and pitch labels (tips 1–5)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NON_MLB_KEYS = {
    "burns", "chase_burns", "sasaki", "roki_sasaki", "choi", "won_tae_choi",
    "gulin", "gu_lin", "gu_lin_ruei_yang", "rios", "wilmer_rios", "hughes", "gabriel_hughes",
}

VERIFIED: dict[str, dict[str, str]] = {
    "burns": {
        "ff": "media/video/burns_ff.mp4",
        "sl": "media/video/burns_sl.mp4",
        "ch": "media/video/burns_sl.mp4",
        "cu": "media/video/burns_sl.mp4",
        "si": "media/video/burns_ff.mp4",
    },
    "sasaki": {
        "ff": "media/video/sasaki_ff.mp4",
        "fs": "media/video/sasaki_fs.mp4",
        "sl": "media/video/sasaki_fs.mp4",
    },
    "choi": {
        "ch": "media/video/choi_ch.mp4",
        "si": "media/video/choi_si.mp4",
        "ff": "media/video/choi_si.mp4",
        "sl": "media/video/choi_ch.mp4",
        "cu": "media/video/choi_ch.mp4",
    },
    "gulin": {
        "ff": "media/video/gulin_ff.mp4",
        "cu": "media/video/gulin_cu.mp4",
        "sl": "media/video/gulin_cu.mp4",
        "ch": "media/video/gulin_cu.mp4",
    },
    "rios": {
        "si": "media/video/rios_si.mp4",
        "sl": "media/video/rios_sl.mp4",
        "fc": "media/video/rios_sl.mp4",
        "ch": "media/video/rios_sl.mp4",
        "ff": "media/video/rios_si.mp4",
    },
    "hughes": {
        "ff": "media/video/hughes_ff.mp4",
        "sl": "media/video/hughes_sl.mp4",
        "ch": "media/video/hughes_sl.mp4",
        "si": "media/video/hughes_ff.mp4",
    },
}

PREFIX = {
    "chase_burns": "burns", "burns": "burns",
    "roki_sasaki": "sasaki", "sasaki": "sasaki",
    "won_tae_choi": "choi", "choi": "choi",
    "gu_lin_ruei_yang": "gulin", "gu_lin": "gulin", "gulin": "gulin",
    "wilmer_rios": "rios", "rios": "rios",
    "gabriel_hughes": "hughes", "hughes": "hughes",
}

BASELINE = {
    "ff": ["ch", "sl", "si", "cu"],
    "si": ["ff", "ch", "sl"],
    "sl": ["ff", "ch"],
    "ch": ["ff", "si"],
    "cu": ["ff", "si", "sl"],
    "fs": ["ff", "ch"],
    "fc": ["ch", "ff"],
    "st": ["ff", "si"],
}


def pitch_code(pitch: str) -> str:
    p = (pitch or "").lower()
    paren = [m.group(1) for m in re.finditer(r"\(([a-z]{2})\b", p)]
    valid = {"ff", "si", "sl", "ch", "cu", "fs", "fc", "st"}
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
        (r"slider|\bsl\b", "sl"),
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
    predicts = (tip.get("predicts") or "FF").upper()
    defaults = {
        "FF": ("Four-Seam Fastball (FF)", "Changeup (CH)"),
        "SI": ("2-Seam Sinker (SI)", "Four-Seam Fastball (FF)"),
        "SL": ("Slider (SL)", "Four-Seam Fastball (FF)"),
        "CH": ("Changeup (CH)", "Four-Seam Fastball (FF)"),
        "CU": ("Curveball (CU)", "Four-Seam Fastball (FF)"),
        "FS": ("Splitter (FS)", "Four-Seam Fastball (FF)"),
        "FC": ("Cutter (FC)", "Changeup (CH)"),
    }
    return defaults.get(predicts, (label or "Pitch A", "Pitch B"))


def resolve_video(prefix: str, pitch: str, exclude: str = "") -> str:
    manifest = VERIFIED.get(prefix, {})
    code = pitch_code(pitch)
    path = manifest.get(code)
    if path and path != exclude:
        return path
    for alt in BASELINE.get(code, ["ff", "ch", "sl", "si", "cu"]):
        if alt == code:
            continue
        candidate = manifest.get(alt)
        if candidate and candidate != exclude:
            return candidate
    return manifest.get("ff") or manifest.get("sl") or next(iter(manifest.values()), "")


def anchor_from_tip(tip: dict) -> tuple[float, float]:
    raw = f"{tip.get('timestamp_window', '')} {tip.get('second_mark', '')}"
    m = re.search(r"(?:0:)?0?([0-9])\.([0-9]{1,2})", raw)
    if m:
        t = float(f"{m.group(1)}.{m.group(2)}")
        return t, t
    return 2.40, 2.40


def player_prefix(player_id: str) -> str | None:
    pid = (player_id or "").lower()
    if pid in PREFIX:
        return PREFIX[pid]
    for key, val in PREFIX.items():
        if key in pid or pid in key:
            return val
    return None


def patch_player(player_id: str, player: dict) -> int:
    prefix = player_prefix(player.get("id") or player_id)
    if not prefix:
        return 0
    tips = player.get("tips") or []
    if isinstance(tips, dict):
        tips = list(tips.values())
    tips = sorted(tips, key=lambda t: t.get("rank", 99))[:5]
    n = 0
    for tip in tips:
        if not isinstance(tip, dict):
            continue
        pa, pb = parse_pitches(tip)
        va = resolve_video(prefix, pa)
        vb = resolve_video(prefix, pb, exclude=va)
        if va == vb:
            vb = resolve_video(prefix, pb)
        tip["pitch_a_label"] = pa
        tip["pitch_b_label"] = pb
        tip["videoA"] = va
        tip["videoB"] = vb
        ta, tb = anchor_from_tip(tip)
        tip["anchor_a"] = ta
        tip["anchor_b"] = tb
        n += 1
    if tips:
        t0 = tips[0]
        player["videoA"] = t0.get("videoA", "")
        player["videoB"] = t0.get("videoB", "")
    return n


def main() -> None:
    for path in (ROOT / "data" / "demo.json", ROOT / "demo.json"):
        if not path.is_file():
            continue
        data = json.loads(path.read_text())
        players = data.get("players", data)
        total = 0
        for pid, player in players.items():
            if not isinstance(player, dict):
                continue
            if pid not in NON_MLB_KEYS and player_prefix(player.get("id") or pid) is None:
                continue
            total += patch_player(pid, player)
        path.write_text(json.dumps(data, indent=2) + "\n")
        print(f"Patched {total} non-MLB tips in {path.name}")


if __name__ == "__main__":
    main()
