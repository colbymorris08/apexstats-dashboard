"""
Is a run directory's tracked data on the CURRENT schema?

Three separate defects reached the board by looking complete while being
structurally stale, and this is the guard for that class in the tracking layer.
Phase A marked Kelly, Rodriguez and Pfaadt "done" by reusing 16-column track
dirs from earlier in the day: no landmark columns, so lift-anchored primitives
cannot be computed at all, and every window necessarily closed at hand break
instead of just after peak leg lift.

Detection is by the presence of the columns the current pipeline needs, NOT by a
version flag. A flag has to be remembered and bumped by hand; a column either
exists in the CSV or it does not. If a future schema change adds columns, add
them to REQUIRED_COLUMNS and stale dirs re-track themselves.
"""
from __future__ import annotations

import csv
from pathlib import Path

# Columns without which the current feature set cannot be produced:
#   knee + hip + shoulder  -> peak leg lift and the torso scale, so the window
#                             can close just after the top of the kick
#   wrist_dist             -> hand break as a recorded landmark
#   pitcher_score/n_poses  -> subject-selection provenance
REQUIRED_COLUMNS = (
    "lkne_y",
    "rkne_y",
    "lhip_y",
    "rhip_y",
    "lsho_y",
    "rsho_y",
    "lwri_y",
    "rwri_y",
    "wrist_dist",
    "pitcher_score",
    "n_poses",
)


def _header(path: Path) -> list[str]:
    with path.open(newline="") as fh:
        for row in csv.reader(fh):
            return row
    return []


def stale_schema_reason(work: Path) -> str | None:
    """
    None when the run's tracks are current; otherwise a short reason string.

    A run with no tracks at all is not stale — there is nothing to re-track
    around, so the normal path handles it.
    """
    tracks = work / "tracks"
    if not tracks.is_dir():
        return None
    files = sorted(tracks.glob("*_tracks.csv"))
    if not files:
        return None

    # Every file is checked, not just the newest. Checking only the newest lets
    # a partially re-tracked dir pass: the tracker skips plays that already have
    # a file, so a deeper game window adds rich tracks alongside surviving stale
    # ones and the dir reads as current while most pitches still lack landmarks.
    stale_n = 0
    example = ""
    for f in files:
        try:
            cols = set(_header(f))
        except Exception as exc:
            return f"unreadable_track:{exc}"
        missing = [c for c in REQUIRED_COLUMNS if c not in cols]
        if missing:
            stale_n += 1
            if not example:
                example = f"{len(cols)}col_missing_{len(missing)}({missing[0]}…)"
    if stale_n:
        return f"{stale_n}/{len(files)} tracks {example}"
    return None


def is_current(work: Path) -> bool:
    return stale_schema_reason(work) is None


def current_track_count(work: Path) -> int:
    """How many tracks in ``work`` are on the current schema."""
    tracks = work / "tracks"
    if not tracks.is_dir():
        return 0
    n = 0
    for f in tracks.glob("*_tracks.csv"):
        try:
            cols = set(_header(f))
        except Exception:
            continue
        if all(c in cols for c in REQUIRED_COLUMNS):
            n += 1
    return n


def report_outruns_tracks(work: Path, claimed: int) -> str | None:
    """
    None when ``report.json``'s pitch count is actually backed by current-schema
    tracks on disk; otherwise a reason string.

    Quarantining stale tracks re-creates the very state it fixes if the resume
    path is left alone: the dir becomes uniformly current because only the few
    rich files remain, while the old report still claims hundreds of pitches. The
    arm then resumes as "done" on a fraction of its volume. A report is only
    trustworthy if the tracks underneath it still exist under this schema.
    """
    have = current_track_count(work)
    if claimed and have < 0.8 * claimed:
        return f"report claims {claimed} pitches, only {have} current-schema tracks on disk"
    return None


def quarantine_stale_tracks(work: Path) -> tuple[int, int]:
    """
    Move every stale-schema track file out of ``tracks/`` so the re-track
    actually re-tracks them. Returns (n_quarantined, n_kept).

    Without this, forcing a re-track only picks up the clips the deeper game
    window newly adds: the tracker skips any play that already has a file, so
    the old 16-column tracks survive and the run dir ends up mixed. A mixed dir
    is worse than a uniformly stale one, because the arm then looks rich by
    column count while most of its pitches still cannot produce a
    lift-anchored primitive.

    Files are moved rather than deleted so the old boundary remains auditable.
    """
    tracks = work / "tracks"
    if not tracks.is_dir():
        return (0, 0)
    dest = work / "tracks_stale_schema"
    moved = kept = 0
    for f in sorted(tracks.glob("*_tracks.csv")):
        try:
            cols = set(_header(f))
        except Exception:
            cols = set()
        if any(c not in cols for c in REQUIRED_COLUMNS):
            dest.mkdir(exist_ok=True)
            f.rename(dest / f.name)
            moved += 1
        else:
            kept += 1
    moved += clear_orphan_summaries(work)
    moved += clear_stale_features(work)
    return (moved, kept)


def clear_stale_features(work: Path) -> int:
    """
    Move aside ``features.csv`` so a forced re-track actually revisits every play.

    This is the skip that mattered most, and it is invisible from the tracks
    directory. A play already present in features.csv is treated as processed, so
    a "forced" re-track only picked up the pitches the deeper game window newly
    added. The arithmetic was exact on all three ground-truth arms: Kelly came
    back 432 + 155 = 587 rows, Rodriguez 517 + 132 = 649, Pfaadt 467 + 154 = 621,
    where the first term is each arm's pre-existing row count. Webb tracked
    403/403 purely because his run dir had no prior features.csv.

    Stale rows also carry pre-fix values (the old hand-break window, and the
    ``0.0 if isnan`` fabrication of glove-at-belt-height), so keeping them would
    contaminate the arm even where the play was re-tracked.
    """
    dest = work / "tracks_stale_schema"
    moved = 0
    for name in ("features.csv", "features_actionable.csv"):
        f = work / name
        if f.is_file():
            dest.mkdir(exist_ok=True)
            f.rename(dest / name)
            moved += 1
    return moved


def clear_orphan_summaries(work: Path) -> int:
    """
    Move aside ``*_summary.json`` files that have no current-schema track.

    The tracker decides a play is already processed by the presence of its
    per-play summary, not its track csv. Quarantining only the csv therefore
    silently skips the play on the next pass instead of re-tracking it: Kelly
    came back with 267 tracks from 699 clips, and 699 - 267 was exactly the 432
    files that had been quarantined. The summary has to travel with the track,
    or "force a re-track" quietly becomes "drop those pitches".
    """
    tracks = work / "tracks"
    if not tracks.is_dir():
        return 0
    dest = work / "tracks_stale_schema"
    moved = 0
    for s in sorted(tracks.glob("*_summary.json")):
        if (tracks / s.name.replace("_summary.json", "_tracks.csv")).is_file():
            continue
        dest.mkdir(exist_ok=True)
        s.rename(dest / s.name)
        moved += 1
    return moved
