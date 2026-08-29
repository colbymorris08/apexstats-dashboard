"""
Keep the clip cache from filling the disk.

The overnight run stopped tracking at 03:08 with "no space left on device": at
~5.6 MB per clip and ~700 clips per arm, each arm leaves roughly 3.9 GB of mp4
behind, and the league queue is 617 arms. Tracking silently became a no-op while
the scaler kept marching through the queue, which is the same failure shape as
the stale-schema reuse — work that looks like it is happening and is not.

A clip is disposable once its track exists: the track is the durable artifact and
the clip can be re-fetched from Savant by play id. Clips without a track are kept,
because those are exactly the plays a pending re-track still has to process.

RETENTION FLOOR
---------------
"Disposable once tracked" was too aggressive and created a deadlock for any
pixel-level work. The clip was deleted the instant its track appeared, so by the
time an arm turned ``complete`` — the only state downstream work will touch — it
had no pixels left. Seven arms finished during the catcher work and every one had
0-1 clips; the single arm that still had pixels was ineligible because it was
still ``tracking``. Every eligible arm was empty by design.

Detector training, mitt and plate labelling, and resolution probes all need
pixels, and re-fetching is 5.5 CPU-hours per arm. So a bounded sample survives
the purge: KEEP_PER_ARM clips per arm, spread across distinct games rather than
taken from whichever game happens to sort first, since a detector that only ever
sees one park is the exact failure already observed — parts_gear.pt works on Woo's
clips and finds no plate at all on Gallen's.

The floor is bounded and small, so the disk argument that motivated the purge
still holds: the cap is per arm, not per clip tracked.
"""
from __future__ import annotations

import csv
from pathlib import Path

# Purge all completed arm video clips now that tracks exist.
# Retaining full outings exhausts hard drives. Setting keep_per_arm=0 frees all raw video.
KEEP_PER_ARM = 0


def _game_of(work: Path) -> dict[str, str]:
    """play_id -> game_date, so the retained sample can span parks and dates."""
    feats = work / "features.csv"
    if not feats.is_file():
        return {}
    try:
        with feats.open(newline="") as fh:
            rows = list(csv.DictReader(fh))
    except OSError:
        return {}
    return {
        str(r.get("play_id")): str(r.get("game_date") or "")
        for r in rows
        if r.get("play_id")
    }


def _retain(work: Path, candidates: list[Path], keep: int) -> set[Path]:
    """
    Choose ``keep`` clips to survive, round-robin over games.

    Round-robin rather than newest-first: a park-diverse sample is what the
    detector needs, and newest-first would hand it two games from one stadium.
    """
    if keep <= 0 or len(candidates) <= keep:
        return set(candidates)
    by_game: dict[str, list[Path]] = {}
    dates = _game_of(work)
    for p in candidates:
        by_game.setdefault(dates.get(p.stem, ""), []).append(p)
    for v in by_game.values():
        v.sort(key=lambda p: p.stem)
    order = sorted(by_game, reverse=True)

    out: set[Path] = set()
    idx = 0
    while len(out) < keep:
        added = False
        for gd in order:
            if len(out) >= keep:
                break
            rows = by_game[gd]
            if idx < len(rows):
                out.add(rows[idx])
                added = True
        if not added:
            break
        idx += 1
    return out


def purge_tracked_clips(work: Path, keep_per_arm: int = KEEP_PER_ARM) -> tuple[int, float]:
    """
    Delete mp4s that already have a track, keeping a bounded park-diverse sample.

    Returns (n_deleted, bytes_freed).
    """
    clips = work / "clips"
    tracks = work / "tracks"
    if not clips.is_dir() or not tracks.is_dir():
        return (0, 0.0)
    tracked = [
        mp4 for mp4 in clips.glob("*.mp4")
        if (tracks / f"{mp4.stem}_tracks.csv").is_file()
    ]
    keep = _retain(work, tracked, keep_per_arm)
    freed = 0.0
    n = 0
    for mp4 in tracked:
        if mp4 in keep:
            continue
        try:
            freed += mp4.stat().st_size
            mp4.unlink()
            n += 1
        except OSError:
            continue
    return (n, freed)


def free_bytes(path: Path) -> float:
    import shutil

    return float(shutil.disk_usage(path).free)
