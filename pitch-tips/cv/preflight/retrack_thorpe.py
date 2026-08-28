"""
Thorpe acceptance test — stage 1: re-track with the rich-landmark tracker.

Re-tracks already-downloaded clips through the unified 72-column tracker, then
derives two artefacts from that single pose pass:

  * ``lift_tracks/<play_id>.csv``  — landmark subset in the schema primitives.py
    expects, so no second inference pass is needed
  * ``features.csv``              — window features recomputed under the corrected
    (set -> hand-break) window, with Statcast pitch metadata joined back on

Pitch metadata (pitch_type, game_pk, count, runners) comes from the previous
features table. That metadata is Statcast labelling and is independent of
tracking quality, so it is safe to reuse; every tracked quantity is recomputed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from preflight.run_poc import _feature_vector  # noqa: E402
from preflight.track_pitcher import KEEP_LANDMARKS, track_clip  # noqa: E402

LIFT_COLS = ["frame", "t_sec", "camera_id"] + [
    f"{name}_{suffix}" for name in KEEP_LANDMARKS for suffix in ("x", "y", "v")
]

META_COLS = [
    "play_id",
    "pitch_type",
    "balls",
    "strikes",
    "game_pk",
    "pitcher_name",
    "on_1b",
    "on_2b",
    "on_3b",
    "runner_exact",
    "runner_bucket",
    "bat_side",
    "batter_tag",
    "delivery",
    "context_tags",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--meta", default="features_meta_source.csv")
    ap.add_argument("--max-frames", type=int, default=180)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    clips_dir = run_dir / "clips"
    tracks_dir = run_dir / "tracks"
    lift_dir = run_dir / "lift_tracks"
    tracks_dir.mkdir(parents=True, exist_ok=True)
    lift_dir.mkdir(parents=True, exist_ok=True)

    meta = pd.read_csv(run_dir / args.meta, dtype={"play_id": str})
    meta_by_id = {r["play_id"]: r for _, r in meta.iterrows()}

    clips = sorted(clips_dir.glob("*.mp4"))
    if args.limit:
        clips = clips[: args.limit]
    print(f"{run_dir.name}: re-tracking {len(clips)} clips", flush=True)

    rows: list[dict] = []
    skipped = 0
    for i, clip in enumerate(clips, 1):
        play_id = clip.stem
        try:
            track = track_clip(clip, tracks_dir, camera_id="CF", max_frames=args.max_frames)
            tdf = pd.read_csv(track)

            # lift_tracks: landmark subset, one pose pass shared with features
            have = [c for c in LIFT_COLS if c in tdf.columns]
            tdf[have].to_csv(lift_dir / f"{play_id}.csv", index=False)

            feats = _feature_vector(track)
            if not feats:
                skipped += 1
                continue
            m = meta_by_id.get(play_id)
            if m is None:
                skipped += 1
                continue
            for c in META_COLS:
                if c in m.index:
                    feats[c] = m[c]
            feats["play_id"] = play_id
            rows.append(feats)
        except Exception as exc:
            print(f"  [{i}] FAIL {play_id[:8]}: {exc}", flush=True)
            skipped += 1
            continue
        if i % 25 == 0 or i == len(clips):
            print(f"  [{i}/{len(clips)}] tracked={len(rows)} skipped={skipped}", flush=True)
            pd.DataFrame(rows).to_csv(run_dir / "features.csv", index=False)

    pd.DataFrame(rows).to_csv(run_dir / "features.csv", index=False)
    print(f"DONE: {len(rows)} pitches featured, {skipped} skipped", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
