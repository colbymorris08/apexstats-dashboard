#!/usr/bin/env python3
"""Patch Gabriel Moreno tips with video paths, labels, and glove-setup anchors."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch_tips(tips: list) -> int:
    n = 0
    for tip in tips:
        if not isinstance(tip, dict):
            continue
        tid = tip.get("id", "")
        if "moreno" not in tid and "moreno" not in tip.get("title", "").lower():
            continue
        if "target_shift" in tid or "lateral" in tip.get("title", "").lower():
            tip["pitch_a_label"] = "Offspeed/Breaking (CH/SL)"
            tip["pitch_b_label"] = "4-Seam Fastball (FF)"
            tip["videoA"] = "media/video/moreno_ch.mp4"
            tip["videoB"] = "media/video/moreno_ff.mp4"
            tip["anchor_a"] = 0.75
            tip["anchor_b"] = 0.75
            n += 1
        elif "target_height" in tid or "crouch" in tip.get("title", "").lower():
            tip["pitch_a_label"] = "4-Seam Fastball (FF)"
            tip["pitch_b_label"] = "Offspeed/Breaking (CH/SL)"
            tip["videoA"] = "media/video/moreno_ff.mp4"
            tip["videoB"] = "media/video/moreno_ch.mp4"
            tip["anchor_a"] = 0.80
            tip["anchor_b"] = 0.70
            n += 1
    return n


def patch_player(player: dict) -> int:
    if not isinstance(player, dict):
        return 0
    pid = (player.get("id") or "").lower()
    if pid not in ("gabriel_moreno", "moreno") and "moreno" not in (player.get("name") or "").lower():
        return 0
    player["videoA"] = "media/video/moreno_ch.mp4"
    player["videoB"] = "media/video/moreno_ff.mp4"
    count = 0
    for key in ("tips", "coachingTips"):
        t = player.get(key)
        if isinstance(t, list):
            count += patch_tips(t)
        elif isinstance(t, dict):
            count += patch_tips(list(t.values()))
    return count


def main() -> None:
    for path in (ROOT / "data" / "demo.json", ROOT / "demo.json"):
        if not path.is_file():
            continue
        data = json.loads(path.read_text())
        players = data.get("players", data)
        total = 0
        for pid, player in players.items():
            if isinstance(player, dict):
                total += patch_player(player)
        path.write_text(json.dumps(data, indent=2) + "\n")
        print(f"Patched {total} Moreno tips in {path.name}")


if __name__ == "__main__":
    main()
