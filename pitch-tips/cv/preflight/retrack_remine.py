"""Re-track existing MP4s (adds catcher + refreshed pitcher landmarks) then remine."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from preflight.run_poc import run_poc  # noqa: E402
from preflight.track_pitcher import MAX_TRACK_FRAMES, track_clip  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--pitcher", required=True)
    p.add_argument("--season", type=int, default=2026)
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()
    clips = sorted((args.work / "clips").glob("*.mp4"))
    if args.limit:
        clips = clips[: args.limit]
    tracks = args.work / "tracks"
    print(f"Re-tracking {len(clips)} clips in {args.work}")
    for i, clip in enumerate(clips, 1):
        try:
            track_clip(clip, tracks, camera_id="CF", max_frames=MAX_TRACK_FRAMES)
            print(f"  [{i}/{len(clips)}] {clip.stem[:8]}…")
        except Exception as e:
            print(f"  skip {clip.stem}: {e}")
    run_poc(args.pitcher, args.season, sample=9999, work=args.work, remine_only=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
