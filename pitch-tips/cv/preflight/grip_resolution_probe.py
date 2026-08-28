"""
Is grip resolvable in the hand region from center field, even with perfect localisation?

Why this probe exists
---------------------
Ten arms of center-field pose geometry produced zero publishable tips, and the
taxonomy says why: 10 of the 24 documented tip types are cues *inside the glove*,
which pose landmarks cannot express. The proposed answer is a hand/glove
detector, and it would cost a few thousand hand-labelled boxes.

Before spending that, one question decides whether the whole programme is
possible: at the pixel scale the hand actually occupies in a Savant CF clip, is
there enough information to separate two known-different grips at all? If the
answer is no, a better model cannot help, because the limit is in the pixels
rather than in the estimator. That is the same reasoning that retired the PitchCom
cue and the glove-angle cue, and it has to be applied here with equal willingness
to close the door.

Method
------
The probe measures the regime a real detector would operate in, not the full frame:

  * **Localisation is assumed perfect.** The crop is centred on the pose
    landmarks' own estimate of where the hands are, so the probe asks only whether
    the pixels carry the information — a detector cannot do better than a correctly
    placed crop, so this is an upper bound on what one could recover.
  * **Drew Thorpe, changeup versus fastball.** He is the only arm with an
    externally documented tip: "hand lower in glove / less buried" on the
    changeup. So a positive result is checkable against ground truth rather than
    merely suggestive.
  * **Inside the settled actionable window only** (closing at peak leg lift + 5
    frames), and restricted to windows anchored on a real detected lift. A grip
    difference visible only during delivery is not actionable and does not count.
  * **Signal is between pitch types; noise is within a single pitch.** The noise
    reference is frame-to-frame variation of the same descriptor on the same pitch,
    which is exactly the "inter-frame pixel noise" the landmark-noise-floor method
    uses. Between-type separation is measured on per-pitch summaries.

The result is reported as **noise ÷ signal**, the same form that retired PitchCom
at 1.9x and the glove-angle cue, so it sits in a comparable frame. A ratio above 1
means the measurement is dominated by noise.

Descriptors
-----------
Several, deliberately, so the answer does not rest on one arbitrary choice of
statistic. Each is a plain appearance measure of the hand region, and the one most
aligned with the documented tip is the skin-pixel fraction: "less buried" should
mean more bare hand visible.

Nothing here is tuned. Descriptors and thresholds are fixed before the result is
read, and all of them are reported whatever they say.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from preflight.window import actionable_window  # noqa: E402

# Crop side length as a multiple of shoulder width. The labelled glove boxes run
# ~56 px against a ~128 px shoulder width, so 0.75 comfortably contains the glove
# and both hands without swallowing the torso.
CROP_SCALE = 0.75

# Skin detection in YCrCb, the standard range. Fixed before looking at results.
SKIN_LO = np.array([0, 133, 77], dtype=np.uint8)
SKIN_HI = np.array([255, 173, 127], dtype=np.uint8)

MIN_FRAMES = 6          # a pitch needs this many usable window frames
MIN_CROP_PX = 12        # below this the crop is too small to describe at all


def descriptors(crop: np.ndarray) -> dict[str, float]:
    """Plain appearance measures of one hand-region crop."""
    if crop.size == 0 or min(crop.shape[:2]) < MIN_CROP_PX:
        return {}
    g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    ycrcb = cv2.cvtColor(crop, cv2.COLOR_BGR2YCrCb)
    skin = cv2.inRange(ycrcb, SKIN_LO, SKIN_HI)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    return {
        # Most aligned with the documented tip: more bare hand visible.
        "skin_frac": float(skin.mean() / 255.0),
        "mean_intensity": float(g.mean()),
        "intensity_sd": float(g.std()),
        "edge_energy": float(np.hypot(gx, gy).mean()),
        "dark_frac": float((g < 60).mean()),
        "bright_frac": float((g > 180).mean()),
    }


DESC_KEYS = [
    "skin_frac",
    "mean_intensity",
    "intensity_sd",
    "edge_energy",
    "dark_frac",
    "bright_frac",
]


def torso_centre(row: pd.Series, W: int, H: int) -> tuple[float, float, float] | None:
    """Midpoint of shoulders and hips — a control region with no grip in it.

    The single most dangerous confound in this probe is that the hand crop
    *follows the wrists*, and glove position is already known to differ by pitch
    type — that is what the existing cue set measures. So a brightness difference
    between changeups and fastballs in a wrist-centred crop may be describing
    what is BEHIND the hand (sky, crowd, dirt, jersey) rather than the hand.

    This control crop is the same size and on the same pitcher under the same
    lighting, but contains no grip. If changeups and fastballs separate just as
    well here, the hand crop is not measuring grip.
    """
    try:
        ls = (float(row["lsho_x"]) * W, float(row["lsho_y"]) * H)
        rs = (float(row["rsho_x"]) * W, float(row["rsho_y"]) * H)
        lh = (float(row["lhip_x"]) * W, float(row["lhip_y"]) * H)
        rh = (float(row["rhip_x"]) * W, float(row["rhip_y"]) * H)
    except (KeyError, TypeError, ValueError):
        return None
    if not all(np.isfinite(v) for v in (*ls, *rs, *lh, *rh)):
        return None
    sho = float(np.hypot(ls[0] - rs[0], ls[1] - rs[1]))
    if not np.isfinite(sho) or sho <= 0:
        return None
    cx = (ls[0] + rs[0] + lh[0] + rh[0]) / 4.0
    cy = (ls[1] + rs[1] + lh[1] + rh[1]) / 4.0
    return cx, cy, sho


def hand_centre(row: pd.Series, W: int, H: int) -> tuple[float, float, float] | None:
    """Midpoint of the two wrists, and the shoulder width that scales the crop.

    The two hands are together in the glove through the pre-lift window, which is
    the moment every documented 'in glove' cue refers to, so their midpoint is
    where the glove is.
    """
    try:
        lw = (float(row["lwri_x"]) * W, float(row["lwri_y"]) * H)
        rw = (float(row["rwri_x"]) * W, float(row["rwri_y"]) * H)
        ls = (float(row["lsho_x"]) * W, float(row["lsho_y"]) * H)
        rs = (float(row["rsho_x"]) * W, float(row["rsho_y"]) * H)
    except (KeyError, TypeError, ValueError):
        return None
    if not all(np.isfinite(v) for v in (*lw, *rw, *ls, *rs)):
        return None
    sho = float(np.hypot(ls[0] - rs[0], ls[1] - rs[1]))
    if not np.isfinite(sho) or sho <= 0:
        return None
    return (lw[0] + rw[0]) / 2.0, (lw[1] + rw[1]) / 2.0, sho


def _crop(frame: np.ndarray, cx: float, cy: float, half: float, W: int, H: int):
    x0, x1 = int(round(cx - half)), int(round(cx + half))
    y0, y1 = int(round(cy - half)), int(round(cy + half))
    if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
        return None
    return frame[y0:y1, x0:x1]


def pitch_series(clip: Path, trk: pd.DataFrame, win) -> tuple[pd.DataFrame, float]:
    """Descriptors for every frame of one pitch's actionable window.

    Emits the hand-region descriptors and, prefixed ``ctl_``, the same
    descriptors on the torso control region, so any apparent grip signal can be
    checked against a region that cannot contain one.
    """
    cap = cv2.VideoCapture(str(clip))
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    rows, sides = [], []
    for fi in range(win.start, win.end):
        if fi >= len(trk):
            break
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ok, frame = cap.read()
        if not ok:
            continue
        row = trk.iloc[fi]
        c = hand_centre(row, W, H)
        if c is None:
            continue
        cx, cy, sho = c
        half = max(MIN_CROP_PX, CROP_SCALE * sho / 2.0)
        sub = _crop(frame, cx, cy, half, W, H)
        if sub is None:
            continue
        d = descriptors(sub)
        if not d:
            continue
        # Where the crop sits, so a position confound is visible rather than
        # inferred: the crop follows the wrists and glove position is known to
        # vary by pitch type.
        d["frame"] = fi
        d["cx_norm"] = cx / W
        d["cy_norm"] = cy / H
        tc = torso_centre(row, W, H)
        if tc is not None:
            tsub = _crop(frame, tc[0], tc[1], half, W, H)
            if tsub is not None:
                for k, v in (descriptors(tsub) or {}).items():
                    d[f"ctl_{k}"] = v
        rows.append(d)
        sides.append(2 * half)
    cap.release()
    return pd.DataFrame(rows), (float(np.median(sides)) if sides else float("nan"))


def interframe_noise(s: pd.Series) -> float:
    """Frame-to-frame measurement noise, isolated from slow real movement.

    Consecutive differences remove any trend across the window, and dividing by
    root two converts the SD of a difference of two noisy values back to the noise
    on a single one. This is the same construction as the landmark noise floor.
    """
    d = s.astype(float).diff().dropna()
    if len(d) < 3:
        return float("nan")
    return float(d.std(ddof=1) / np.sqrt(2.0))


def hedges_g(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float("nan")
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    if sp == 0:
        return float("nan")
    g = (a.mean() - b.mean()) / sp
    return float(g * (1 - 3 / (4 * (na + nb) - 9)))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", default="../runs/drew_thorpe_rich_poc")
    ap.add_argument("--picks", default="/tmp/thorpe_picks.json")
    ap.add_argument(
        "--clip-cache",
        default="/tmp/grip_probe_clips",
        help="scratch directory for clips, OUTSIDE the pipeline's run tree: the "
        "pipeline purges its own clips/ directories to manage disk, and did delete "
        "90 clips out from under this probe mid-run",
    )
    ap.add_argument("--keep-clips", action="store_true", help="do not delete after measuring")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    run = Path(args.run)
    picks = json.load(open(args.picks))
    cache = Path(args.clip_cache)
    cache.mkdir(parents=True, exist_ok=True)
    from preflight.fetch_savant import download_play_clip

    per_pitch, noises, crop_sides = [], [], []
    n_fetch = n_missing = 0
    for t, pid, game, s, e in picks:
        tpath = run / "tracks" / f"{pid}_tracks.csv"
        if not tpath.exists():
            continue
        # Prefer a clip the pipeline still has; otherwise fetch to scratch. Each
        # clip is measured and released immediately so nothing depends on it
        # surviving, and peak disk stays at one clip.
        clip = run / "clips" / f"{pid}.mp4"
        temp = None
        if not clip.exists():
            clip = cache / f"{pid}.mp4"
            if not clip.exists():
                try:
                    download_play_clip(pid, cache)
                    n_fetch += 1
                except Exception:
                    n_missing += 1
                    continue
            if not clip.exists():
                n_missing += 1
                continue
            temp = clip if not args.keep_clips else None
        trk = pd.read_csv(tpath)
        win = actionable_window(trk)
        if not win.valid or win.method != "peak_leg_lift":
            if temp is not None:
                temp.unlink(missing_ok=True)
            continue
        ser, side = pitch_series(clip, trk, win)
        if temp is not None:
            temp.unlink(missing_ok=True)
        if len(ser) < MIN_FRAMES:
            continue
        crop_sides.append(side)
        rec = {"play_id": pid, "pitch_type": t, "game_pk": game, "n_frames": len(ser),
               "crop_px": side}
        for k in DESC_KEYS:
            rec[k] = float(ser[k].median())
            noises.append({"desc": k, "noise": interframe_noise(ser[k]),
                           "pitch_type": t})
        for k in ("cx_norm", "cy_norm"):
            if k in ser:
                rec[k] = float(ser[k].median())
        for k in DESC_KEYS:
            ck = f"ctl_{k}"
            if ck in ser and ser[ck].notna().any():
                rec[ck] = float(ser[ck].median())
                noises.append({"desc": ck, "noise": interframe_noise(ser[ck].dropna()),
                               "pitch_type": t})
        per_pitch.append(rec)

    df = pd.DataFrame(per_pitch)
    nz = pd.DataFrame(noises)
    if df.empty:
        print("no usable pitches")
        return

    print("=== grip resolution probe: Drew Thorpe, CH vs FF ===")
    print(f"clips fetched to scratch: {n_fetch}   unavailable: {n_missing}")
    print(f"pitches measured: {len(df)}  ({df.pitch_type.value_counts().to_dict()})")
    print(f"games: {df.game_pk.nunique()}   window frames per pitch: "
          f"median {df.n_frames.median():.0f}")
    print(f"hand-region crop: median {np.median(crop_sides):.1f} px square "
          f"(p5 {np.percentile(crop_sides,5):.1f}, p95 {np.percentile(crop_sides,95):.1f})")
    print()
    print("Localisation is assumed perfect: the crop is centred on the pose model's")
    print("own wrist midpoint, so this is an upper bound on a detector's information.")
    print()

    hdr = (f"{'descriptor':16s} {'CH mean':>10s} {'FF mean':>10s} {'signal':>10s} "
           f"{'interfrm':>10s} {'NOISE/SIG':>10s} {'g':>7s} {'resolvable?':>12s}")
    print(hdr)
    print("-" * len(hdr))
    verdicts = {}
    for k in DESC_KEYS:
        ch = df[df.pitch_type == "CH"][k].to_numpy(float)
        ff = df[df.pitch_type == "FF"][k].to_numpy(float)
        signal = abs(float(ch.mean() - ff.mean()))
        noise = float(nz[nz.desc == k]["noise"].median())
        ratio = noise / signal if signal > 0 else float("inf")
        g = hedges_g(ch, ff)
        ok = ratio < 1.0
        verdicts[k] = {"signal": signal, "noise": noise, "ratio": ratio, "g": g,
                       "resolvable": bool(ok)}
        print(f"{k:16s} {ch.mean():10.4f} {ff.mean():10.4f} {signal:10.4f} "
              f"{noise:10.4f} {ratio:10.2f} {g:+7.3f} {'yes' if ok else 'NO':>12s}")

    print()
    print("signal   = |mean(CH) - mean(FF)| of per-pitch medians")
    print("interfrm = median within-pitch frame-to-frame noise on a single measurement")
    print("NOISE/SIG> 1 means the difference is smaller than the noise on measuring it")
    print("           (PitchCom was retired at 1.9; glove angle at a comparable figure)")

    best = min(verdicts.items(), key=lambda kv: kv[1]["ratio"])
    print()
    print(f"BEST CASE: {best[0]} at noise/signal = {best[1]['ratio']:.2f}, "
          f"g = {best[1]['g']:+.3f}")
    n_res = sum(v["resolvable"] for v in verdicts.values())
    print(f"descriptors clearing noise: {n_res} of {len(DESC_KEYS)}")

    # ---------------------------------------------------------------
    # The control: the same measurement on a region with no grip in it.
    # ---------------------------------------------------------------
    have_ctl = [k for k in DESC_KEYS if f"ctl_{k}" in df.columns]
    if have_ctl:
        print()
        print("=== CONTROL: torso region, same crop size, no grip present ===")
        print("If changeups and fastballs separate here too, the hand crop is not")
        print("measuring grip — it is measuring where the crop landed.")
        print()
        print(f"{'descriptor':16s} {'hand g':>9s} {'CONTROL g':>10s} {'ctl/hand':>9s}")
        print("-" * 48)
        for k in have_ctl:
            ch = df[df.pitch_type == "CH"][k].to_numpy(float)
            ff = df[df.pitch_type == "FF"][k].to_numpy(float)
            cch = df[df.pitch_type == "CH"][f"ctl_{k}"].to_numpy(float)
            cff = df[df.pitch_type == "FF"][f"ctl_{k}"].to_numpy(float)
            gh, gc = hedges_g(ch, ff), hedges_g(cch, cff)
            frac = abs(gc) / abs(gh) if gh and np.isfinite(gh) and gh != 0 else float("nan")
            verdicts[k]["control_g"] = gc
            verdicts[k]["control_over_hand"] = frac
            print(f"{k:16s} {gh:+9.3f} {gc:+10.3f} {frac:9.2f}")

    # Where the crop actually sat, by pitch type.
    if "cy_norm" in df.columns:
        print()
        print("=== crop position by pitch type (the confound, measured) ===")
        for k in ("cx_norm", "cy_norm"):
            ch = df[df.pitch_type == "CH"][k].to_numpy(float)
            ff = df[df.pitch_type == "FF"][k].to_numpy(float)
            print(f"{k:10s} CH={ch.mean():.4f} FF={ff.mean():.4f} "
                  f"delta={ch.mean()-ff.mean():+.4f} g={hedges_g(ch,ff):+.3f}")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(
            {"n_pitches": len(df), "crop_px_median": float(np.median(crop_sides)),
             "verdicts": verdicts}, indent=2))
        df.to_csv(str(args.out).replace(".json", "_perpitch.csv"), index=False)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
