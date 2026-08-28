"""
Woo runner-on-second re-analysis: re-derive window features from cached tracks.

Tracking is the expensive stage and is unchanged by window placement, so this
walks the cached ``tracks/*_tracks.csv`` and rebuilds the feature vector under
whatever ``window.py`` is currently on disk. Pitch metadata (Statcast labels,
including the base state) is joined back from the previous features table.

Output is written beside the run as ``features_rederived.csv`` so the file the
live pipeline reads is left untouched.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from preflight.retrack_thorpe import META_COLS  # noqa: E402
from preflight.run_poc import _feature_vector  # noqa: E402
from preflight.window import actionable_window  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--meta", default="features.csv")
    ap.add_argument("--out", default="features_rederived.csv")
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    meta = pd.read_csv(run_dir / args.meta, dtype={"play_id": str})
    meta_by_id = {r["play_id"]: r for _, r in meta.iterrows()}

    rows: list[dict] = []
    diag: list[dict] = []
    dropped_no_window = 0
    dropped_no_meta = 0
    tracks = sorted((run_dir / "tracks").glob("*_tracks.csv"))
    for t in tracks:
        play_id = t.name.replace("_tracks.csv", "")
        # Window diagnostics are kept for every track, including the ones whose
        # boundary could not be established. Those pitches carry no features but
        # they still tell us how the pitcher was working, and dropping them from
        # the mechanics question would bias it toward clips the tracker liked.
        raw = pd.read_csv(t)
        win = actionable_window(raw)
        m0 = meta_by_id.get(play_id)
        diag.append(
            {
                "play_id": play_id,
                "window_valid": win.valid,
                "window_method": win.method,
                "delivery_type": win.delivery_type,
                "set_frame": win.set_frame,
                "n_frames": win.n_frames,
                "on_2b": (bool(m0["on_2b"]) if m0 is not None else None),
                "delivery_base_state": (m0["delivery"] if m0 is not None else None),
                "pitch_type": (m0["pitch_type"] if m0 is not None else None),
            }
        )
        feats = _feature_vector(t)
        if not feats:
            dropped_no_window += 1
            continue
        m = meta_by_id.get(play_id)
        if m is None:
            dropped_no_meta += 1
            continue
        for c in META_COLS:
            if c in m.index:
                feats[c] = m[c]
        feats["play_id"] = play_id
        rows.append(feats)

    out = pd.DataFrame(rows)
    out.to_csv(run_dir / args.out, index=False)
    dg = pd.DataFrame(diag)
    dg.to_csv(run_dir / "window_diagnostics.csv", index=False)
    print("\n-- delivery type by base state, ALL tracked pitches --")
    print(pd.crosstab(dg["on_2b"], dg["delivery_type"]))
    print("\n-- window validity by base state --")
    print(pd.crosstab(dg["on_2b"], dg["window_valid"]))
    print("\n-- track-read delivery vs base-state guess --")
    print(pd.crosstab(dg["delivery_base_state"], dg["delivery_type"]))
    agree = (dg["delivery_base_state"] == dg["delivery_type"]).mean()
    print(f"agreement between the two labels: {agree:.1%}")
    print(
        f"{run_dir.name}: {len(tracks)} tracks -> {len(out)} featured "
        f"({dropped_no_window} unbounded window, {dropped_no_meta} no metadata)"
    )
    if "delivery_type" in out.columns:
        print("track-derived delivery type:", dict(out["delivery_type"].value_counts()))
    if "delivery" in out.columns:
        print("base-state delivery label:", dict(out["delivery"].value_counts()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
