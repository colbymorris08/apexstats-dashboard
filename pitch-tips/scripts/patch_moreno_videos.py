#!/usr/bin/env python3
"""Patch Gabriel Moreno tips with video paths, labels, and pre-pitch glove-target anchors."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "media" / "deck"
VIDEO = ROOT / "media" / "video"
DOWNLOADS = Path("/Users/colbymorris/Downloads/Preflight_Sales_Deck")
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/opt/ffmpeg/bin/ffmpeg"

# Pre-pitch glove target — before pitcher windup.
# CH/FF clips are not phase-aligned; CH starts moving earlier.
MORENO_ANCHOR_A = 0.08  # tip1 CH pane / tip2 FF pane primary
MORENO_ANCHOR_B = 0.25


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
            tip["anchor_a"] = MORENO_ANCHOR_A
            tip["anchor_b"] = MORENO_ANCHOR_B
            n += 1
        elif "target_height" in tid or "crouch" in tip.get("title", "").lower():
            tip["pitch_a_label"] = "4-Seam Fastball (FF)"
            tip["pitch_b_label"] = "Offspeed/Breaking (CH/SL)"
            tip["videoA"] = "media/video/moreno_ff.mp4"
            tip["videoB"] = "media/video/moreno_ch.mp4"
            tip["anchor_a"] = MORENO_ANCHOR_B
            tip["anchor_b"] = MORENO_ANCHOR_A
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


def extract_still(video: Path, t: float, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [FFMPEG, "-y", "-ss", str(t), "-i", str(video), "-vframes", "1", "-q:v", "2", str(out)],
        capture_output=True,
        check=True,
    )


def regenerate_deck_stills() -> None:
    """Extract pre-pitch glove-target frames and rebuild deck comparison PNG."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available — skipping deck still regeneration")
        return

    ch_still = DECK / "moreno_ch_changeup_setup.png"
    ff_still = DECK / "moreno_ff_fastball_setup.png"
    comparison = DECK / "moreno_catcher_setup_deck_comparison.png"

    extract_still(VIDEO / "moreno_ch.mp4", MORENO_ANCHOR_A, ch_still)
    extract_still(VIDEO / "moreno_ff.mp4", MORENO_ANCHOR_B, ff_still)

    ch = Image.open(ch_still).convert("RGB")
    ff = Image.open(ff_still).convert("RGB")
    target_h = 720
    def scale(img: Image.Image) -> Image.Image:
        ratio = target_h / img.height
        return img.resize((int(img.width * ratio), target_h), Image.Resampling.LANCZOS)

    ch, ff = scale(ch), scale(ff)
    gap = 8
    header = 56
    canvas = Image.new("RGB", (ch.width + ff.width + gap, target_h + header), (7, 11, 20))
    canvas.paste(ch, (0, header))
    canvas.paste(ff, (ch.width + gap, header))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 28)
        small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
        small = font
    draw.text((24, 12), "Gabriel Moreno · Pre-Pitch Glove Target", fill=(232, 237, 245), font=font)
    draw.text((24, 38), f"CH/SL @ {MORENO_ANCHOR_A:.2f}s · FF @ {MORENO_ANCHOR_B:.2f}s (pre-windup)", fill=(148, 163, 184), font=small)
    draw.text((ch.width // 2 - 80, header - 4), "CH / Offspeed", fill=(248, 113, 113), font=small)
    draw.text((ch.width + gap + ff.width // 2 - 60, header - 4), "FF / Fastball", fill=(96, 165, 250), font=small)
    canvas.save(comparison, optimize=True)

    if DOWNLOADS.parent.exists():
        DOWNLOADS.mkdir(parents=True, exist_ok=True)
        for name in (
            "moreno_ch_changeup_setup.png",
            "moreno_ff_fastball_setup.png",
            "moreno_catcher_setup_deck_comparison.png",
        ):
            shutil.copy2(DECK / name, DOWNLOADS / name)
    print(f"Regenerated Moreno deck stills @ CH={MORENO_ANCHOR_A}s FF={MORENO_ANCHOR_B}s")


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
        print(f"Patched {total} Moreno tips in {path.name} (anchors={MORENO_ANCHOR_A}/{MORENO_ANCHOR_B}s)")

    regenerate_deck_stills()


if __name__ == "__main__":
    main()
