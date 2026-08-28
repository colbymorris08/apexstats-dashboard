"""
Retention gate for the trajectory features, applied before any of them is tested.

Three ways a trajectory feature can be worthless, each checked here:

1. **Coverage.** A path needs most of its frames tracked, so a feature can be
   mostly NaN on real footage even when it is perfectly well defined. This is
   what excluded the sway family at 31.8%.
2. **Noise floor.** Re-measure every pitch with additive landmark jitter at the
   measured per-frame level, and compare the perturbation it induces against the
   between-pitch spread the feature actually has. A feature whose induced noise
   exceeds its real spread is describing tracking error. Reported as noise ÷
   signal, the form that retired PitchCom at 1.9.
3. **Proxy.** A trajectory feature that correlates almost perfectly with an
   existing point cue is not new information, and testing it again spends FDR
   budget on a question already answered. Correlation is measured against all 20
   audited point cues.

The rule is fixed here, before any result is read, and applied mechanically:

    keep  =  coverage >= 0.60  and  noise/signal < 1.0  and  |r| vs any point cue < 0.90

That is the same coverage floor and the same noise logic the point primitives
faced. Nothing about it is tuned to the outcome — its whole purpose is to decide
which features are allowed to exist before anyone knows whether they would have
found anything.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from preflight.spot_diff import CUES, load_pitcher
from preflight.trajectory import TRAJECTORY_FEATURES, pitch_trajectory
from preflight.primitives import play_id_of, resolve_track_dir

# Per-frame landmark jitter, torso lengths, from landmark_noise_probe.py. The
# same figure the point primitives were audited against.
MEASURED_JITTER = 0.10

MIN_COVERAGE = 0.60
MAX_NOISE_RATIO = 1.0
MAX_PROXY_R = 0.90

LANDMARK_COLS = (
    "lsho", "rsho", "lhip", "rhip", "lwri", "rwri", "lelb", "relb",
    "lkne", "rkne", "lank", "rank",
)


def perturb(df: pd.DataFrame, rng: np.random.Generator, torso_px: float) -> pd.DataFrame:
    """Add independent per-frame jitter at the measured level to every landmark."""
    d = df.copy()
    for base in LANDMARK_COLS:
        for ax in ("x", "y"):
            c = f"{base}_{ax}"
            if c in d.columns:
                v = pd.to_numeric(d[c], errors="coerce").to_numpy(dtype=float)
                d[c] = v + rng.normal(0, MEASURED_JITTER * torso_px, len(v))
    return d


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", default="../runs/merrill_kelly_poc")
    ap.add_argument("--limit", type=int, default=250)
    args = ap.parse_args()

    run = Path(args.run)
    _, tracks = resolve_track_dir(run)
    tracks = tracks[: args.limit]
    rng = np.random.default_rng(0)

    clean, noisy = [], []
    for tp in tracks:
        try:
            df = pd.read_csv(tp)
        except Exception:
            continue
        pid = play_id_of(tp)
        a = pitch_trajectory(df, pid)
        if a is None:
            continue
        # Torso scale in normalised units, so the jitter is applied at the same
        # relative magnitude the landmark probe measured.
        sho_y = pd.to_numeric(df.get("lsho_y"), errors="coerce")
        hip_y = pd.to_numeric(df.get("lhip_y"), errors="coerce")
        torso = float(np.nanmedian((hip_y - sho_y).abs())) if sho_y is not None else 0.12
        if not np.isfinite(torso) or torso <= 0:
            torso = 0.12
        b = pitch_trajectory(perturb(df, rng, torso), pid)
        if b is None:
            continue
        clean.append(a)
        noisy.append(b)

    if not clean:
        print("no usable pitches")
        return
    A = pd.DataFrame(clean)
    B = pd.DataFrame(noisy)
    print(f"=== trajectory retention gate: {run.name} ===")
    print(f"pitches: {len(A)} clean / {len(B)} re-measured under jitter "
          f"{MEASURED_JITTER} torso per frame")
    print(f"rule: coverage >= {MIN_COVERAGE}, noise/signal < {MAX_NOISE_RATIO}, "
          f"|r| vs any point cue < {MAX_PROXY_R}\n")

    # Proxy check against the audited point cues.
    pts = load_pitcher(run)
    point_cols = [c for c in CUES if c in pts.columns]
    merged = A.merge(pts[["play_id"] + point_cols], on="play_id", how="left")

    hdr = (f"{'feature':26s} {'cover':>6s} {'signal':>9s} {'noise':>9s} "
           f"{'N/S':>6s} {'proxy r':>8s} {'closest cue':22s} {'KEEP'}")
    print(hdr)
    print("-" * len(hdr))
    verdict = {}
    for k in TRAJECTORY_FEATURES:
        a = A[k].to_numpy(dtype=float)
        cover = float(np.isfinite(a).mean())
        signal = float(np.nanstd(a[np.isfinite(a)])) if np.isfinite(a).any() else np.nan
        # Pair positionally: both passes ran the same pitches in the same order,
        # and only pitches where both produced a value can be differenced.
        pair = np.isfinite(a) & np.isfinite(B[k].to_numpy(dtype=float))
        d = a[pair] - B[k].to_numpy(dtype=float)[pair]
        noise = float(np.nanstd(d) / np.sqrt(2.0)) if pair.sum() >= 5 else np.nan
        ratio = noise / signal if signal and np.isfinite(signal) and signal > 0 else np.inf

        best_r, best_c = 0.0, "-"
        for c in point_cols:
            ok = merged[k].notna() & merged[c].notna()
            if ok.sum() < 25:
                continue
            x, y = merged.loc[ok, k].to_numpy(float), merged.loc[ok, c].to_numpy(float)
            if np.std(x) < 1e-9 or np.std(y) < 1e-9:
                continue
            r = abs(float(np.corrcoef(x, y)[0, 1]))
            if r > best_r:
                best_r, best_c = r, c

        keep = (cover >= MIN_COVERAGE) and (ratio < MAX_NOISE_RATIO) and (best_r < MAX_PROXY_R)
        verdict[k] = {"coverage": cover, "signal": signal, "noise": noise,
                      "ratio": ratio, "proxy_r": best_r, "proxy_cue": best_c,
                      "keep": bool(keep)}
        why = ""
        if not keep:
            fails = []
            if cover < MIN_COVERAGE:
                fails.append("coverage")
            if not (ratio < MAX_NOISE_RATIO):
                fails.append("noise")
            if best_r >= MAX_PROXY_R:
                fails.append("proxy")
            why = " <- " + ",".join(fails)
        print(f"{k:26s} {cover:6.2f} {signal:9.4f} {noise:9.4f} {ratio:6.2f} "
              f"{best_r:8.2f} {best_c:22s} {'yes' if keep else 'NO'}{why}")

    kept = [k for k, v in verdict.items() if v["keep"]]
    print(f"\nKEPT {len(kept)} of {len(TRAJECTORY_FEATURES)}: {kept}")
    print("These and only these are eligible for discovery.")


if __name__ == "__main__":
    main()
