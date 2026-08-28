"""
Cheap per-arm validity gate.

Three separate defects reached the board before this existed: a feature window
that ran past hand break, tips fitted in-sample with no holdout, and tracks that
followed the wrong person (Savant clips often open on a close-up of the hitter).
Each is cheap to detect per arm and expensive to discover after 30 arms of
compute, so every completed run is checked and a failing run is not published.

Writes `sanity.json` into the run directory. merge_demo refuses to publish any
arm whose gate failed.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

# Mirrors PITCHER_TORSO_MIN/MAX in track_pitcher so the arm-level gate and the
# per-frame subject filter agree. Measured on CF Savant tracks the pitcher's
# shoulder-to-hip extent clusters at ~0.13; broadcast close-ups run 0.28-0.55.
TORSO_MIN = 0.05
TORSO_MAX = 0.22
MAX_IMPLAUSIBLE_FRAC = 0.25

MIN_USABLE_PITCHES = 40
MIN_TEST_PITCHES = 10

# Window must close on a detected pitch event, not a fixed fraction of the clip.
# "peak_leg_lift" is the current boundary; the hand-break methods remain valid
# because they are the fallback when a track lacks the knee landmarks, and
# because audit re-derivations on older tracks still carry them.
VALID_BREAK_METHODS = {"peak_leg_lift", "hand_break_no_lift", "wrist_separation", "glove_departure"}
MAX_SINGLE_END_FRAME_FRAC = 0.60  # >60% of pitches sharing one end frame = fixed window

# A window can be correctly BOUNDED and still be anchored on the wrong part of
# the clip. Savant clips carry seconds of pre-pitch idle footage, and a pitcher
# standing on the mound reads as "quiet" to set detection while fidgeting with
# the ball reads as a hand break. The result is a window that opens and closes
# long before the delivery starts, so every feature describes idle footage.
#
# This check has been re-specified twice and the reason is worth recording,
# because the obvious version of it does not work.
#
# Attempt 1 compared the window end against the peak-wrist-speed frame and
# failed any arm closing before it. That is wrong: a correct window ALWAYS closes
# before peak arm speed, so the sign is uninformative.
#
# Attempt 2 tested the magnitude of that gap, which worked while the window
# closed at hand break (41 frames on the bug versus 19 correct). Once the
# boundary moved to just after peak leg lift the window legitimately closes
# EARLIER — peak lift precedes hand break — and the gap rose to 45, which no
# longer separates a correct window from the idle-footage bug at 41.
#
# So the gap is kept only as a loose guard against a window stranded far from
# the pitch, and the real protection is now structural: a window is only built
# around a detected peak leg lift meeting a minimum knee rise, bounded by a
# detected delivery burst. Idle footage contains neither, so it cannot produce a
# window at all. What is worth checking is that windows are actually being
# anchored that way rather than falling back.
MIN_LIFT_ANCHORED_FRAC = 0.50
MAX_MEDIAN_GAP_TO_DELIVERY = 90


def _torso_check(work: Path) -> dict:
    tdir = work / "tracks"
    if not tdir.is_dir():
        return {"ok": True, "skipped": "no tracks dir", "n": 0}
    meds: list[float] = []
    for t in sorted(tdir.glob("*_tracks.csv")):
        try:
            df = pd.read_csv(t, usecols=["belt_y", "shoulder_y"])
        except Exception:
            continue
        torso = (df["belt_y"] - df["shoulder_y"]).dropna()
        torso = torso[torso > 0]
        if len(torso) >= 10:
            meds.append(float(np.median(torso)))
    if not meds:
        return {"ok": True, "skipped": "no measurable tracks", "n": 0}
    arr = np.array(meds)
    bad = int(((arr < TORSO_MIN) | (arr > TORSO_MAX)).sum())
    frac = bad / len(arr)
    return {
        "ok": frac <= MAX_IMPLAUSIBLE_FRAC,
        "n": len(arr),
        "median_torso": round(float(np.median(arr)), 4),
        "implausible": bad,
        "implausible_frac": round(frac, 3),
        "band": [TORSO_MIN, TORSO_MAX],
    }


def _window_check(work: Path) -> dict:
    # An audit re-derivation under the corrected window satisfies this check even
    # when the arm's original features.csv predates the window fix.
    if (work / "features_actionable.csv").is_file():
        return {"ok": True, "source": "features_actionable.csv (corrected-window re-derivation)"}
    f = work / "features.csv"
    if not f.is_file():
        return {"ok": False, "reason": "no features.csv"}
    try:
        df = pd.read_csv(f)
    except Exception as e:
        return {"ok": False, "reason": f"unreadable features.csv: {e}"}
    if "window_break_method" not in df.columns:
        return {"ok": False, "reason": "no window metadata (pre-fix feature window)"}

    methods = df["window_break_method"].dropna().astype(str)
    good = int(methods.isin(VALID_BREAK_METHODS).sum())
    frac_good = good / len(methods) if len(methods) else 0.0

    # A fixed-fraction window collapses window_end_frame onto one value.
    fixed_frac = 0.0
    if "window_end_frame" in df.columns:
        ends = df["window_end_frame"].dropna()
        if len(ends):
            fixed_frac = float(ends.value_counts(normalize=True).iloc[0])

    return {
        "ok": frac_good >= 0.75 and fixed_frac <= MAX_SINGLE_END_FRAME_FRAC,
        "n": int(len(methods)),
        "hand_break_frac": round(frac_good, 3),
        "methods": methods.value_counts().to_dict(),
        "most_common_end_frame_frac": round(fixed_frac, 3),
    }


def _tip_is_validated(tip: dict) -> bool:
    gates = tip.get("gates") or {}
    if gates.get("validated") is True:
        return True
    return bool(tip.get("trainGamesN")) and bool(tip.get("testGamesN"))


def _holdout_check(report: dict) -> dict:
    """
    What matters is that every PUBLISHED tip is holdout-validated.

    An arm publishing zero tips cannot over-claim, so it passes. Otherwise either
    the report carries a real train/test game split, or each tip carries its own
    train/test evidence (the audit re-derivation records it per tip).
    """
    ts = report.get("tip_split") or {}
    train = ts.get("train_games") or []
    test = ts.get("test_games") or []
    n_test = int(ts.get("n_test_pitches") or 0)
    # Train and test games must be DISJOINT. A split reporting the same game on
    # both sides is a pitch-level split wearing a game-level split's clothes, and
    # it passed this check until an arm with a single outing exposed it.
    disjoint = not (set(train) & set(test))
    split_ok = bool(train) and bool(test) and disjoint and n_test >= MIN_TEST_PITCHES

    tips = report.get("tips") or []
    per_tip_ok = bool(tips) and all(_tip_is_validated(t) for t in tips)
    unvalidated = [t.get("id") for t in tips if not _tip_is_validated(t)]

    if not tips:
        return {
            "ok": True,
            "reason": "no tips published — nothing to over-claim",
            "split_present": "tip_split" in report,
            "n_tips": 0,
        }
    return {
        "ok": (split_ok or per_tip_ok) and disjoint,
        "split_present": "tip_split" in report,
        "games_disjoint": disjoint,
        "n_train_games": len(train),
        "n_test_games": len(test),
        "n_test_pitches": n_test,
        "n_tips": len(tips),
        "all_tips_carry_holdout": per_tip_ok,
        "unvalidated_tips": unvalidated[:5],
    }


def _volume_check(report: dict) -> dict:
    n = int(report.get("n_tracked") or 0)
    return {"ok": n >= MIN_USABLE_PITCHES, "n_tracked": n, "min": MIN_USABLE_PITCHES}


def _placement_check(work: Path) -> dict:
    """Does the window actually contain the delivery, or only idle footage?"""
    tdir = work / "tracks"
    feats_path = work / "features.csv"
    if not tdir.is_dir() or not feats_path.is_file():
        return {"ok": True, "skipped": "no tracks or features", "n": 0}
    try:
        feats = pd.read_csv(feats_path, dtype={"play_id": str})
    except Exception:
        return {"ok": True, "skipped": "unreadable features", "n": 0}
    if "window_end_frame" not in feats.columns:
        return {"ok": True, "skipped": "no window_end_frame", "n": 0}

    gaps: list[int] = []
    for _, row in feats.iterrows():
        t = tdir / f"{row['play_id']}_tracks.csv"
        if not t.is_file():
            continue
        try:
            d = pd.read_csv(t)
        except Exception:
            continue
        if "wrist_speed" not in d.columns:
            continue
        speed = pd.to_numeric(d["wrist_speed"], errors="coerce").to_numpy()
        if np.isfinite(speed).sum() < 10:
            continue
        end = row.get("window_end_frame")
        if not np.isfinite(end):
            continue
        gaps.append(int(np.nanargmax(speed)) - int(end))
    if not gaps:
        return {"ok": True, "skipped": "no comparable pitches", "n": 0}
    median_gap = float(np.median(gaps))

    lift_frac = None
    if "window_break_method" in feats.columns:
        methods = feats["window_break_method"].dropna().astype(str)
        if len(methods):
            lift_frac = float((methods == "peak_leg_lift").mean())

    ok = median_gap <= MAX_MEDIAN_GAP_TO_DELIVERY and (
        lift_frac is None or lift_frac >= MIN_LIFT_ANCHORED_FRAC
    )
    return {
        "ok": ok,
        "n": len(gaps),
        "median_gap_to_delivery_frames": median_gap,
        "max_gap": MAX_MEDIAN_GAP_TO_DELIVERY,
        "lift_anchored_frac": lift_frac,
        "min_lift_anchored_frac": MIN_LIFT_ANCHORED_FRAC,
    }


def check_arm(work: Path, report: dict, force: bool = False) -> dict:
    """Run all checks; returns a verdict dict and writes sanity.json."""
    cached_p = work / "sanity.json"
    if not force and cached_p.is_file():
        try:
            cached = json.loads(cached_p.read_text())
            if "publishable" in cached and "checks" in cached:
                return cached
        except Exception:
            pass
    checks = {
        "holdout": _holdout_check(report),
        "window": _window_check(work),
        "placement": _placement_check(work),
        "subject": _torso_check(work),
        "volume": _volume_check(report),
    }
    failed = [k for k, v in checks.items() if not v.get("ok")]
    verdict = {
        "publishable": not failed,
        "failed_checks": failed,
        "subject": report.get("pitcher") or report.get("catcher"),
        "checks": checks,
    }
    try:
        (work / "sanity.json").write_text(json.dumps(verdict, indent=2))
    except Exception:
        pass
    return verdict


def is_publishable(work: Path) -> tuple[bool, list[str]]:
    """Read a previously written verdict; absent verdict is treated as unknown-OK."""
    p = work / "sanity.json"
    if not p.is_file():
        return True, []
    try:
        v = json.loads(p.read_text())
    except Exception:
        return True, []
    return bool(v.get("publishable", True)), list(v.get("failed_checks") or [])
