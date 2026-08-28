"""
Re-derive window features from already-tracked clips.

Tracking is the expensive stage and its output does not change when window
placement changes, so a corrected window only requires re-running
``_feature_vector`` over the cached ``tracks/*_tracks.csv``. Pitch metadata is
joined back from the previous features table (Statcast labelling, independent of
tracking).
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--meta", default="features_meta_source.csv")
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    meta = pd.read_csv(run_dir / args.meta, dtype={"play_id": str})
    meta_by_id = {r["play_id"]: r for _, r in meta.iterrows()}

    tracks = sorted((run_dir / "tracks").glob("*_tracks.csv"))
    rows: list[dict] = []
    dropped = 0
    for t in tracks:
        play_id = t.name.replace("_tracks.csv", "")
        feats = _feature_vector(t)
        if not feats:
            dropped += 1
            continue
        m = meta_by_id.get(play_id)
        if m is None:
            dropped += 1
            continue
        for c in META_COLS:
            if c in m.index:
                feats[c] = m[c]
        feats["play_id"] = play_id
        rows.append(feats)

    out = pd.DataFrame(rows)
    out.to_csv(run_dir / "features.csv", index=False)
    print(f"{run_dir.name}: {len(tracks)} tracks -> {len(out)} featured, {dropped} dropped")
    if "delivery_type" in out.columns:
        print("delivery type mix:")
        for k, v in out["delivery_type"].value_counts().items():
            print(f"  {k:12s} {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
