#!/usr/bin/env python3
"""Package MP4 comparison clips and deck assets for sales-deck screenshot workflow."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path("/Users/colbymorris/Downloads/Preflight_Sales_Deck")
DECK = ROOT / "media" / "deck"
VIDEO_DIRS = [ROOT / "media" / "video", ROOT / "media" / "videos"]

VERIFIED_NON_MLB = {
    "gabriel_moreno": {"ff": "media/video/moreno_ff.mp4", "ch": "media/video/moreno_ch.mp4", "sl": "media/video/moreno_ch.mp4"},
    "moreno": {"ff": "media/video/moreno_ff.mp4", "ch": "media/video/moreno_ch.mp4", "sl": "media/video/moreno_ch.mp4"},
}

# Deck still PNGs (existing — frame timing may be off; use MP4s for screenshots)
ROUPP_STILLS = {
    "glove_elevation_lift": ("roupp_cu_curve_lift.png", "roupp_si_sinker_lift.png"),
    "hand_depth_pocket": ("roupp_ch_change_set.png", "roupp_si_sinker_set.png"),
    "settle_lift_tempo": ("roupp_cu_curve_set.png", "roupp_si_sinker_set.png"),
    "glove_pocket_flare": ("roupp_cu_curve_set.png", "roupp_si_sinker_set.png"),
    "glove_drift_dx": ("roupp_si_sinker_set.png", "roupp_cu_curve_set.png"),
}
MORENO_STILLS = {
    "target_shift": ("moreno_ch_changeup_setup.png", "moreno_ff_fastball_setup.png"),
    "target_height": ("moreno_ff_fastball_setup.png", "moreno_ch_changeup_setup.png"),
}


def slug(s: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")
    return s[:max_len] or "tip"


def pitch_code(player_id: str, pitch_type: str) -> str:
    p = (pitch_type or "").lower()
    norm = (player_id or "").lower()
    if "moreno" in norm:
        if re.search(r"\bff\b|four|fastball|\(ff\)|\bfast\b", p):
            return "ff"
        return "ch"
    if re.search(r"\bcu\b|curve", p):
        return "cu"
    if re.search(r"\bch\b|change", p):
        return "ch"
    if re.search(r"\bsl\b|slider|sweep", p):
        return "sl"
    if re.search(r"\bff\b|four|fastball|\(ff\)|\bfast\b", p):
        return "ff"
    if re.search(r"\bsi\b|sink", p):
        return "si"
    if re.search(r"\bfc\b|cutter", p):
        return "fc"
    if re.search(r"\bfs\b|split|fork", p):
        return "fs"
    return "ff"


def sit_suffix(context_filter: str) -> str:
    c = (context_filter or "").lower()
    if "2b" in c or "second" in c:
        return "_runner_2b"
    if "1b" in c or "first" in c:
        return "_runner_1b"
    if "runner" in c or "loaded" in c or "12" in c or "13" in c or "23" in c:
        return "_runners_on"
    if "none" in c or "empty" in c or "bases empty" in c:
        return "_bases_empty"
    if "rhh" in c or "rhb" in c:
        return "_vs_rhb"
    if "lhh" in c or "lhb" in c:
        return "_vs_lhb"
    if "windup" in c:
        return "_windup"
    if "stretch" in c:
        return "_stretch"
    return ""


def resolve_verified_non_mlb(norm_id: str, pitch_type: str) -> str:
    key = norm_id
    if key not in VERIFIED_NON_MLB:
        for k in VERIFIED_NON_MLB:
            if k in norm_id or norm_id in k:
                key = k
                break
    verified = VERIFIED_NON_MLB.get(key)
    if not verified:
        return ""
    code = pitch_code(key, pitch_type)
    return verified.get(code) or verified.get("ff") or verified.get("ch") or ""


def resolve_video_path(player_id: str, pitch_type: str, context: str) -> str:
    norm = (player_id or "").lower().replace("-", "_")
    verified = resolve_verified_non_mlb(norm, pitch_type)
    if verified:
        return verified

    code = pitch_code(player_id, pitch_type)
    suffix = sit_suffix(context)

    if "roupp" in norm or "landen_roupp" in norm:
        return f"media/video/roupp_{code}{suffix}.mp4"
    if "moreno" in norm or "gabriel_moreno" in norm:
        return f"media/video/moreno_{code}{suffix}.mp4"
    return ""


def parse_pitches(tip: dict) -> tuple[str, str]:
    if tip.get("pitch_a_label") and tip.get("pitch_b_label"):
        return tip["pitch_a_label"], tip["pitch_b_label"]
    label = tip.get("contrast_label") or tip.get("contrast") or ""
    parts = re.split(r" vs\.? | \/ | vs ", label, maxsplit=1, flags=re.I)
    if len(parts) >= 2:
        return parts[0].strip(), parts[1].strip()
    predicts = (tip.get("predicts") or "").upper()
    defaults = {
        "CU": ("Curveball (CU)", "Sinker (SI)"),
        "CH": ("Changeup (CH)", "Fastball (FF)"),
        "SI": ("Sinker (SI)", "Four-Seam (FF)"),
        "FF": ("Four-Seam Fastball (FF)", "Offspeed (CH/SL)"),
    }
    return defaults.get(predicts, (label or "Pitch A", "Pitch B"))


def moreno_explicit_videos(tip: dict) -> tuple[str, str, str, str] | None:
    tid = tip.get("id", "")
    title = (tip.get("title") or "").lower()
    if "target_shift" in tid or "lateral" in title:
        return (
            "Offspeed/Breaking (CH/SL)",
            "4-Seam Fastball (FF)",
            "media/video/moreno_ch.mp4",
            "media/video/moreno_ff.mp4",
        )
    if "target_height" in tid or "crouch" in title:
        return (
            "4-Seam Fastball (FF)",
            "Offspeed/Breaking (CH/SL)",
            "media/video/moreno_ff.mp4",
            "media/video/moreno_ch.mp4",
        )
    return None


def tip_context(tip: dict) -> str:
    ctx = tip.get("context") or []
    if isinstance(ctx, list):
        return " ".join(str(x) for x in ctx)
    return str(ctx or "")


def find_on_disk(rel_path: str) -> Path | None:
    rel = rel_path.replace("media/video/", "").replace("media/videos/", "")
    stem = Path(rel).stem
    for d in VIDEO_DIRS:
        if not d.is_dir():
            continue
        exact = d / f"{stem}.mp4"
        if exact.is_file():
            return exact
        # fallback: same pitch code without situation suffix
        base = re.sub(r"_(runner_2b|runner_1b|runners_on|bases_empty|vs_rhb|vs_lhb|windup|stretch)$", "", stem)
        if base != stem:
            plain = d / f"{base}.mp4"
            if plain.is_file():
                return plain
        # any file starting with base prefix
        matches = sorted(d.glob(f"{base}*.mp4"))
        if matches:
            return matches[0]
    return None


def pitch_slug(label: str, src: Path | None = None) -> str:
    if src:
        # e.g. roupp_cu_runners_on.mp4 -> cu
        m = re.match(r"^[a-z]+_([a-z]{2})", src.stem)
        if m:
            return m.group(1)
    m = re.search(r"\(([A-Z]{2})", label or "")
    if m:
        return m.group(1).lower()
    return slug(label, 12)


def still_for_tip(player_key: str, tip_id: str) -> tuple[str | None, str | None]:
    for key, pair in (ROUPP_STILLS if player_key == "roupp" else MORENO_STILLS).items():
        if key in tip_id:
            return pair
    return None, None


def load_players() -> dict:
    path = ROOT / "demo.json"
    if not path.is_file():
        path = ROOT / "data" / "demo.json"
    data = json.loads(path.read_text())
    return data.get("players", data)


def package_player(player_id: str, player: dict, dest: Path) -> list[dict]:
    tips = player.get("tips") or []
    if not tips:
        return []
    dest.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []

    for i, tip in enumerate(tips, start=1):
        tip_num = f"{i:02d}"
        tip_id = tip.get("id", f"tip_{i}")
        title = tip.get("title") or tip.get("cue") or tip_id
        label_slug = slug(tip.get("cue") or title.split("·")[0].strip(), 30)

        explicit = moreno_explicit_videos(tip) if "moreno" in player_id else None
        ctx = tip_context(tip)
        if explicit:
            pitch_a, pitch_b, video_a, video_b = explicit
        else:
            pitch_a, pitch_b = parse_pitches(tip)
            video_a = tip.get("videoA") or tip.get("video_a") or resolve_video_path(player_id, pitch_a, ctx)
            video_b = tip.get("videoB") or tip.get("video_b") or resolve_video_path(player_id, pitch_b, ctx)

        src_a = find_on_disk(video_a) if video_a else None
        src_b = find_on_disk(video_b) if video_b else None

        pa = pitch_slug(pitch_a, src_a)
        pb = pitch_slug(pitch_b, src_b)
        prefix = f"tip{tip_num}_{label_slug}"

        # 1) Tip label / description
        desc_path = dest / f"{prefix}_00_tip_description.txt"
        desc_path.write_text(
            "\n".join(
                [
                    f"Tip {i}: {title}",
                    f"ID: {tip_id}",
                    f"Contrast: {tip.get('contrast_label') or tip.get('contrast', '')}",
                    f"What to spot: {tip.get('what_to_spot') or tip.get('lookFor') or ''}",
                    f"Timestamp window: {tip.get('timestamp_window') or ''}",
                    f"Anchor hint (from app): tA≈{tip.get('anchor_a', 'see timestamp_window')}, tB≈{tip.get('anchor_b', 'see timestamp_window')}",
                    f"Pitch A label: {pitch_a}",
                    f"Pitch B label: {pitch_b}",
                    f"Resolved videoA: {video_a} -> {src_a}",
                    f"Resolved videoB: {video_b} -> {src_b}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        # 2) Still placeholder / note
        still_a_name, still_b_name = still_for_tip(player_id.split("_")[-1] if player_id.startswith("gabriel") else player_id, tip_id)
        note_path = dest / f"{prefix}_00_still_NOTE.txt"
        note_lines = [
            "STILL PLACEHOLDER NOTE",
            "=====================",
            "Existing deck stills may have wrong frame timing (too early/late).",
            "Use the MP4 files below and pause at the timestamp window above.",
            "",
        ]
        still_dir = dest / "deck_still_reference"
        still_dir.mkdir(exist_ok=True)
        for side, fname in (("A", still_a_name), ("B", still_b_name)):
            if fname and (DECK / fname).is_file():
                ref = still_dir / f"{prefix}_still_{side}_{fname}"
                shutil.copy2(DECK / fname, ref)
                note_lines.append(f"Reference still {side} (DO NOT trust frame timing): deck_still_reference/{ref.name}")
            else:
                note_lines.append(f"Reference still {side}: none on file")
        note_path.write_text("\n".join(note_lines) + "\n", encoding="utf-8")

        copied: list[str] = []
        for side, src, pitch_label, pslug in (
            ("01_first_vid", src_a, pitch_a, pa),
            ("02_second_vid", src_b, pitch_b, pb),
        ):
            out_name = f"{prefix}_{side}_{pslug}.mp4"
            out_path = dest / out_name
            if src and src.is_file():
                shutil.copy2(src, out_path)
                copied.append(out_name)
            else:
                (dest / f"{prefix}_{side}_MISSING_{pslug}.txt").write_text(
                    f"Could not locate source for {pitch_label}\nExpected: {video_a if side.startswith('01') else video_b}\n",
                    encoding="utf-8",
                )

        manifest.append(
            {
                "tip": i,
                "id": tip_id,
                "title": title,
                "pitch_a": pitch_a,
                "pitch_b": pitch_b,
                "video_a_resolved": str(src_a) if src_a else None,
                "video_b_resolved": str(src_b) if src_b else None,
                "copied": copied,
            }
        )

    return manifest


def copy_deck_outputs() -> dict:
    out_dir = OUT / "r_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    patterns = ("*.png", "*.jpg", "*.jpeg", "*.pdf", "*.svg", "*.html", "*.json")
    for pat in patterns:
        for src in DECK.rglob(pat):
            rel = src.relative_to(DECK)
            dst = out_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(str(dst))
    # also detection SVGs already in OUT/detection — symlink note only
    return {"dest": str(out_dir), "copied_count": len(copied), "files": copied}


def main() -> None:
    screenshot_root = OUT / "screenshot_source"
    roupp_dest = screenshot_root / "roupp"
    moreno_dest = screenshot_root / "moreno"
    screenshot_root.mkdir(parents=True, exist_ok=True)

    players = load_players()
    roupp = players.get("roupp") or {}
    moreno = players.get("gabriel_moreno") or players.get("moreno") or {}

    roupp_manifest = package_player("roupp", roupp, roupp_dest)
    moreno_manifest = package_player("gabriel_moreno", moreno, moreno_dest)

    readme_lines = [
        "PREFLIGHT SALES DECK — SCREENSHOT SOURCE VIDEOS",
        "================================================",
        "",
        "Per tip, files are ordered:",
        "  tipNN_<label>_00_tip_description.txt  — tip text, contrast, timestamp window",
        "  tipNN_<label>_00_still_NOTE.txt        — why stills are unreliable + reference PNG paths",
        "  tipNN_<label>_01_first_vid_<pitch>.mp4  — videoA (first panel in app compare)",
        "  tipNN_<label>_02_second_vid_<pitch>.mp4 — videoB (second panel)",
        "",
        "Pause each MP4 at the timestamp in the description file, then screenshot.",
        "",
        "=== ROUPP (pitcher) ===",
    ]
    for m in roupp_manifest:
        readme_lines.append(f"Tip {m['tip']}: {m['title']}")
        readme_lines.append(f"  A ({m['pitch_a']}): {m['copied'][0] if m['copied'] else 'MISSING'}")
        readme_lines.append(f"  B ({m['pitch_b']}): {m['copied'][1] if len(m['copied']) > 1 else 'MISSING'}")
        readme_lines.append("")

    readme_lines.append("=== MORENO (catcher) ===")
    for m in moreno_manifest:
        readme_lines.append(f"Tip {m['tip']}: {m['title']}")
        readme_lines.append(f"  A ({m['pitch_a']}): {m['copied'][0] if m['copied'] else 'MISSING'}")
        readme_lines.append(f"  B ({m['pitch_b']}): {m['copied'][1] if len(m['copied']) > 1 else 'MISSING'}")
        readme_lines.append("")

    # Shortcut folder for slide 4/5 primary pairs (clean CU+SI / CH+FF)
    deck_primary = screenshot_root / "deck_primary"
    deck_primary.mkdir(exist_ok=True)
    shortcuts = [
        ("slide04_roupp_cu_vs_si", roupp_dest, "tip04_glove_pocket_outward_flare_at__"),
        ("slide05_moreno_ch_vs_ff", moreno_dest, "tip01_mitt_lateral_setup_shift_6_inc_"),
    ]
    for label, src_dir, prefix in shortcuts:
        sub = deck_primary / label
        sub.mkdir(exist_ok=True)
        for f in sorted(src_dir.glob(f"{prefix}*")):
            if f.suffix in (".mp4", ".txt"):
                shutil.copy2(f, sub / f.name)

    readme_lines.extend(
        [
            "DECK SLIDE MAPPING (primary comparisons)",
            "  Slide 4 (Roupp CU vs SI): screenshot_source/deck_primary/slide04_roupp_cu_vs_si/ (tip04)",
            "  Slide 5 (Moreno CH vs FF): screenshot_source/deck_primary/slide05_moreno_ch_vs_ff/ (tip01)",
            "  Note: tip01 Roupp uses CU vs CH (app resolver); use tip04 for pure CU vs SI.",
            "",
            "R SCRIPTS: none found in pitch-tips/ or apexstats repo.",
            "Pre-generated deck assets copied to ../r_outputs/ (from pitch-tips/media/deck/).",
        ]
    )
    (screenshot_root / "README.txt").write_text("\n".join(readme_lines) + "\n", encoding="utf-8")

    deck_copy = copy_deck_outputs()

    summary = {
        "screenshot_source": str(screenshot_root),
        "roupp": roupp_manifest,
        "moreno": moreno_manifest,
        "r_outputs": deck_copy,
    }
    (OUT / "packaging_manifest.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
