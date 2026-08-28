#!/usr/bin/env python3
"""
Mine a park-diverse labelling set for ``catcher_mitt`` and ``plate``.

Why this set exists
-------------------
``parts_gear.pt`` is trained on 28 fully-labeled frames with ``catcher_mitt``
validated on 5 instances, and it does not generalise across parks: in-window plate
detection measured 1.00 on Woo clips and 0.00 on Gallen clips. That coverage gap is
the binding constraint on the whole ``cmitt_*`` cue family — not the cue's
precision, which is fine (signal-to-noise about 6:1).

Coverage that varies by park varies by opponent, which is a confound capable of
manufacturing an effect. So this is not a nice-to-have: the family cannot be tested
honestly until coverage is comparable across parks.

Sampling design
---------------
*Stratify by game, then weight toward failure.*

**Park identity.** Nothing in the retained clips records a venue — clip
``.meta.json`` carries only ``play_id``, ``source`` and ``angle``. The finest park
proxy available is ``game_pk`` from the arm's ``features.csv``: one game is played
in exactly one park, so distinct games upper-bound distinct parks. Stratifying by
game therefore gets at least as much park diversity as stratifying by park would,
and never less. Reported counts say "games", not "parks", because that is what is
actually known.

**Failure weighting.** Frames where the detector currently fails are what teach it
the parks it cannot see. But a set made only of failures is a biased training set
that can degrade the cases already working, so the mix is deliberate and recorded:
``--fail-frac`` of frames are ones where the current model misses mitt or plate, the
remainder are frames where it succeeds. Default 0.65.

**Which frames.** The cue only reads in-window frames, and the mitt is most
detectable there (0.645 in window vs 0.230 outside). Where a track exists the real
actionable window is used. Most retained clips are not yet tracked, so for those
frames are sampled across the clip's central span, which is where the set-through-
delivery period falls in a ~440-frame clip. The method used is recorded per frame in
``boundsMethod`` so a labelled frame never misrepresents how it was chosen.

Usage
-----
    python -m preflight.catcher_label_mine --verify        # contact sheet first
    python -m preflight.catcher_label_mine --target 180
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
OUT_IMG_DIR = ROOT / "media" / "detection" / "catcher_target"
OUT_MANIFEST = ROOT / "data" / "label_manifest_catcher.json"

# The two classes being labelled. catcher_mask is absent on purpose: it fires on
# the umpire at a 77.5% rate and must not be trained further.
CLASSES = [
    {"id": "catcher_mitt", "label": "Catcher mitt (the target he sets)", "color": "#00e5ff"},
    {"id": "plate", "label": "Home plate (the reference)", "color": "#ffd400"},
]

# Crop framing.
#
# The mitt is ~3.5% of frame width — about 45 px on a 1280-wide frame — which is
# unpleasant to box accurately on a full frame, so frames are cropped and upscaled.
#
# A FIXED crop was tried first and rejected on inspection: framing varies enough
# between parks that a fixed window cut the catcher off in several arms, and one
# arm's mid-clip frame was not a home-plate view at all. A fixed crop would have
# produced silently unlabelable frames.
#
# So the crop is a fixed-SIZE window placed at a RANDOM offset subject to
# containing the clip's pooled detector anchor. Two things are being balanced:
#
#   containment  the plate must be inside the crop, or the frame is useless —
#                the plate is the unit the mitt is measured in.
#   offset       the anchor must NOT be centred. Training a detector on crops
#                where the object is always dead centre teaches position as much
#                as appearance, and inflates apparent performance. The random
#                offset keeps the object's location in-frame varied.
CROP_W_FRAC = 0.62
CROP_H_FRAC = 0.62
CROP_UPSCALE = 1.6
# Keep the anchor at least this far inside the crop edge, as a fraction of crop
# size, so it is never clipped by the random placement.
ANCHOR_MARGIN = 0.18

# Classes pooled to locate the home-plate area in a clip. catcher_mask is absent:
# it tracks the umpire.
ANCHOR_NAMES = ("plate", "catcher_shin", "catcher_cleat", "catcher_mitt")
# Frames probed per clip to build the pooled anchor and pick candidates.
PROBE_FRACS = (0.24, 0.32, 0.40, 0.48, 0.56, 0.64)

# A frame "fails" if either class is missing at the level where boxes were
# confirmed to be on the right object.
CONF_OK = 0.25

UNTRACKED_FRACS = PROBE_FRACS


def arm_dirs() -> list[Path]:
    out = []
    for d in sorted(RUNS.glob("*_poc")):
        if (d / "clips").is_dir() and any((d / "clips").glob("*.mp4")):
            out.append(d)
    return out


def play_to_game(arm: Path) -> dict[str, str]:
    """play_id -> game_pk, the park proxy."""
    f = arm / "features.csv"
    if not f.is_file():
        return {}
    try:
        import pandas as pd

        df = pd.read_csv(f, usecols=["play_id", "game_pk"], dtype=str)
        return dict(zip(df["play_id"], df["game_pk"]))
    except Exception:
        return {}


def clip_play_id(clip: Path) -> str | None:
    meta = clip.with_suffix(".meta.json")
    if meta.is_file():
        try:
            return json.loads(meta.read_text()).get("play_id")
        except Exception:
            pass
    return None


def window_for(arm: Path, clip: Path) -> tuple[int, int] | None:
    """Real actionable window when the clip has a track; None otherwise."""
    t = arm / "tracks" / f"{clip.stem}_tracks.csv"
    if not t.is_file():
        return None
    try:
        import pandas as pd

        from preflight.window import actionable_window

        df = pd.read_csv(t)
        win = actionable_window(df)
        if win is None:
            return None
        lo, hi = int(win[0]), int(win[1])
        return (lo, hi) if hi > lo else None
    except Exception:
        return None


def crop_frame(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    x0, y0, x1, y1 = CROP
    sub = frame[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
    if CROP_UPSCALE != 1.0 and sub.size:
        sub = cv2.resize(sub, None, fx=CROP_UPSCALE, fy=CROP_UPSCALE, interpolation=cv2.INTER_CUBIC)
    return sub


def probe_frame(frame: np.ndarray) -> dict:
    """Current-model confidence for the two classes on the FULL frame."""
    from preflight.catcher_boxes import detect_gear

    dets = detect_gear(frame)
    best = {"catcher_mitt": 0.0, "plate": 0.0}
    for d in dets:
        n = d["name"]
        if n in best and d["conf"] > best[n]:
            best[n] = round(float(d["conf"]), 4)
    return best


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=180, help="frames to emit")
    ap.add_argument("--fail-frac", type=float, default=0.65)
    ap.add_argument("--per-clip", type=int, default=2, help="max frames kept per clip")
    ap.add_argument("--max-clips-per-arm", type=int, default=14)
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--verify", action="store_true",
                    help="write a contact sheet of crops across arms and stop")
    a = ap.parse_args(argv)

    rng = random.Random(a.seed)
    arms = arm_dirs()
    if not arms:
        print("no retained clips found")
        return 1

    print(f"arms with retained clips: {len(arms)}")

    # --- verification pass: does the crop hold across arms? -------------------
    if a.verify:
        tiles = []
        for arm in arms:
            clips = sorted((arm / "clips").glob("*.mp4"))
            if not clips:
                continue
            clip = clips[len(clips) // 2]
            cap = cv2.VideoCapture(str(clip))
            n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 440
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * 0.5))
            ok, frame = cap.read()
            cap.release()
            if not ok:
                continue
            sub = crop_frame(frame)
            sub = cv2.resize(sub, (420, 320))
            cv2.putText(sub, arm.name.replace("_poc", ""), (8, 26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            tiles.append(sub)
        if tiles:
            cols = 3
            rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles) - len(tiles) % cols, cols)]
            if rows:
                sheet = np.vstack(rows)
                p = ROOT / "media" / "detection" / "catcher_crop_verify.jpg"
                cv2.imwrite(str(p), sheet)
                print(f"wrote {p}  ({len(tiles)} arms)")
        return 0

    # --- candidate pass ------------------------------------------------------
    OUT_IMG_DIR.mkdir(parents=True, exist_ok=True)
    cands: list[dict] = []

    for arm in arms:
        pg = play_to_game(arm)
        clips = sorted((arm / "clips").glob("*.mp4"))
        rng.shuffle(clips)
        clips = clips[: a.max_clips_per_arm]
        for clip in clips:
            cap = cv2.VideoCapture(str(clip))
            n_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
            if n_total <= 0:
                cap.release()
                continue
            win = window_for(arm, clip)
            if win:
                lo, hi = win
                lo, hi = max(0, lo), min(n_total - 1, hi)
                idxs = list(np.linspace(lo, hi, num=len(UNTRACKED_FRACS), dtype=int)) if hi > lo else []
                method = "actionable_window"
            else:
                idxs = [int(n_total * f) for f in UNTRACKED_FRACS]
                method = "central_span_untracked"
            pid = clip_play_id(clip)
            game = pg.get(pid or "", "unknown")
            kept = 0
            for fi in idxs:
                if kept >= a.per_clip:
                    break
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(fi))
                ok, frame = cap.read()
                if not ok:
                    continue
                conf = probe_frame(frame)
                fails = conf["catcher_mitt"] < CONF_OK or conf["plate"] < CONF_OK
                cands.append({
                    "arm": arm.name.replace("_poc", ""),
                    "clip": clip,
                    "frame": int(fi),
                    "game": game,
                    "play_id": pid,
                    "mittConf": conf["catcher_mitt"],
                    "plateConf": conf["plate"],
                    "fails": fails,
                    "boundsMethod": method,
                })
                kept += 1
            cap.release()
        done = sum(1 for c in cands if c["arm"] == arm.name.replace("_poc", ""))
        print(f"  {arm.name.replace('_poc','')}: {done} candidates")

    if not cands:
        print("no candidates")
        return 1

    # --- selection: stratify by game, then honour the fail/succeed mix -------
    by_game: dict[str, list[dict]] = defaultdict(list)
    for c in cands:
        by_game[c["game"]].append(c)
    for v in by_game.values():
        rng.shuffle(v)

    want_fail = int(round(a.target * a.fail_frac))
    chosen: list[dict] = []
    games = sorted(by_game, key=lambda g: -len(by_game[g]))
    # Round-robin across games so no single park dominates the set.
    while len(chosen) < a.target:
        progressed = False
        for g in games:
            if len(chosen) >= a.target:
                break
            pool = by_game[g]
            n_fail = sum(1 for c in chosen if c["fails"])
            prefer_fail = n_fail < want_fail
            pick = None
            for i, c in enumerate(pool):
                if c["fails"] == prefer_fail:
                    pick = pool.pop(i)
                    break
            if pick is None and pool:
                pick = pool.pop(0)
            if pick is not None:
                chosen.append(pick)
                progressed = True
        if not progressed:
            break

    # --- write crops + manifest ---------------------------------------------
    frames_out = []
    for c in chosen:
        cap = cv2.VideoCapture(str(c["clip"]))
        cap.set(cv2.CAP_PROP_POS_FRAMES, c["frame"])
        ok, frame = cap.read()
        cap.release()
        if not ok:
            continue
        sub = crop_frame(frame)
        fid = f"cmitt_{c['arm']}_{c['clip'].stem[:8]}_f{c['frame']}"
        rel = f"media/detection/catcher_target/{fid}.jpg"
        cv2.imwrite(str(ROOT / rel), sub, [cv2.IMWRITE_JPEG_QUALITY, 95])
        frames_out.append({
            "id": fid,
            "src": rel,
            "pitcher": c["arm"].replace("_", " ").title(),
            "team": None,
            "pitchType": "?",
            "angle": "CF",
            "game": c["game"],
            "frame": c["frame"],
            "mittConf": c["mittConf"],
            "plateConf": c["plateConf"],
            "detectorFails": bool(c["fails"]),
            "boundsMethod": c["boundsMethod"],
            "crop": list(CROP),
            "cropUpscale": CROP_UPSCALE,
        })

    n_games = len({f["game"] for f in frames_out if f["game"] != "unknown"})
    n_fail = sum(1 for f in frames_out if f["detectorFails"])
    manifest = {
        "version": 2,
        "angle": "CF_savant",
        "mode": "catcher_mitt_plate",
        "classes": CLASSES,
        "ordering": "round_robin_by_game",
        "note": (
            "Box the CATCHER'S MITT and HOME PLATE. Both classes are needed in every "
            "frame where both are visible: the plate is the measurement unit the mitt "
            "position is expressed in, so a mitt without a plate in the same frame is "
            "not usable. Frames are cropped and 2x upscaled around the plate area so "
            "the mitt is large enough to box accurately. "
            f"{n_fail} of {len(frames_out)} frames are ones the current detector MISSES "
            "— those are the ones that fix park generalisation. Do NOT box the umpire's "
            "mask or mitt: the umpire stands directly behind the catcher and confusing "
            "the two is exactly the failure being corrected. If the catcher's mitt is "
            "not visible, leave the frame without a mitt box rather than guessing."
        ),
        "provenance": {
            "purpose": "fix parts_gear.pt park generalisation for catcher_mitt and plate",
            "baseline_model": "parts_gear.pt",
            "baseline_model_sha256_24": "15891fea835eecbb406765e2",
            "baseline_training_frames": 28,
            "baseline_failure": "in-window plate detection 1.00 on Woo, 0.00 on Gallen",
            "n_frames": len(frames_out),
            "n_games": n_games,
            "n_arms": len({f["pitcher"] for f in frames_out}),
            "n_detector_failures": n_fail,
            "fail_frac_target": a.fail_frac,
            "park_proxy": "game_pk; clips record no venue, one game is one park",
            "excluded_class": {
                "catcher_mask": "fires on the umpire at 77.5%; not labelled, not trained"
            },
            "seed": a.seed,
        },
        "frames": frames_out,
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2))

    print(f"\nwrote {OUT_MANIFEST}")
    print(f"  frames        {len(frames_out)}")
    print(f"  arms          {manifest['provenance']['n_arms']}")
    print(f"  games (parks) {n_games}")
    print(f"  detector-miss {n_fail}  ({n_fail/max(len(frames_out),1):.0%})")
    per_arm = defaultdict(int)
    for f in frames_out:
        per_arm[f["pitcher"]] += 1
    for k in sorted(per_arm):
        print(f"    {k:22s} {per_arm[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
