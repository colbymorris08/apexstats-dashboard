"""
Per-arm readiness, published so consumers can tell complete from in-flight.

"Ready" used to mean "has rich tracks", and that is what produced a false
finding. Kelly had rich tracks throughout his deepening from 8 to 25 games, so he
read as ready the whole time; a spot_diff run against him mid-deepening saw a
primitives table covering roughly a third of the CU/SL pitches the finished arm
would have, produced 462 comparisons instead of 828, and reported four survivors
that measure at g = -0.001 to +0.093 on the complete data. Nothing was wrong with
either computation. They were computed against different snapshots of the same
directory.

So readiness here answers two separate questions:

  * is the data structurally usable  (schema)
  * is anyone still writing to it    (state)

and it publishes the sample identity — feature row count, mtime, size — so a
consumer can record what it computed against and later prove the sample has not
moved underneath it.

An arm is only ``ready`` when it is current-schema AND quiet.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from preflight.liveness import liveness
from preflight.schema_check import current_track_count, stale_schema_reason

# An arm that has had a track or feature file written recently is assumed to be
# mid-run. Tracking writes a file every few seconds, and the gap between an
# arm's last track and its features being rebuilt is well inside this, so the
# window has to comfortably exceed that gap or an arm flickers to "complete"
# during its own feature build. Fifteen minutes is far longer than any observed
# gap and still far shorter than an arm's runtime.
ACTIVE_WINDOW_SECS = 900


def _newest_mtime(work: Path) -> float:
    newest = 0.0
    tracks = work / "tracks"
    if tracks.is_dir():
        try:
            for f in tracks.iterdir():
                if f.name.endswith((".csv", ".json")):
                    m = f.stat().st_mtime
                    if m > newest:
                        newest = m
        except OSError:
            pass
    for name in ("features.csv", "report.json"):
        f = work / name
        if f.is_file():
            newest = max(newest, f.stat().st_mtime)
    return newest


def _feature_rows(f: Path) -> int:
    """Row count excluding the header, without parsing the file."""
    try:
        with f.open("rb") as fh:
            return max(0, sum(1 for _ in fh) - 1)
    except OSError:
        return 0


def arm_status(work: Path) -> dict:
    n_tracks = current_track_count(work)
    stale = stale_schema_reason(work)
    feats = work / "features.csv"
    newest = _newest_mtime(work)
    idle = time.time() - newest if newest else None
    active = idle is not None and idle < ACTIVE_WINDOW_SECS

    if active:
        state = "tracking"
    elif stale is not None:
        state = "stale_schema"
    elif n_tracks == 0:
        state = "empty"
    elif not feats.is_file():
        state = "tracked_no_features"
    else:
        state = "complete"

    return {
        "work": str(work),
        "state": state,
        "ready": state == "complete",
        "schema": "rich_72col" if stale is None and n_tracks else "stale",
        "stale_reason": stale,
        "n_current_tracks": n_tracks,
        # Sample identity: a consumer should record these alongside its result
        # and refuse to publish if they no longer match at publish time.
        "n_feature_rows": _feature_rows(feats) if feats.is_file() else 0,
        "features_mtime": feats.stat().st_mtime if feats.is_file() else None,
        "features_size": feats.stat().st_size if feats.is_file() else None,
        "seconds_since_write": round(idle, 1) if idle is not None else None,
    }


def write_index(runs: Path) -> dict:
    index = {}
    for d in sorted(runs.glob("*_poc")):
        if not (d / "tracks").is_dir() and not (d / "features.csv").is_file():
            continue
        index[d.name] = arm_status(d)
    # Published, not inferred. If the pipeline is dead this index keeps being
    # rewritten with correct-but-frozen values, and a consumer cannot distinguish
    # "complete" from "complete as of two hours ago". Branch on liveness.stale.
    live = liveness(runs)
    payload = {
        "generated_at": time.time(),
        "generated_at_human": time.strftime("%Y-%m-%d %H:%M:%S"),
        "liveness": live,
        "stale": live["stale"],
        "active_window_secs": ACTIVE_WINDOW_SECS,
        "note": (
            "ready=true means current schema AND no writes for "
            f"{ACTIVE_WINDOW_SECS}s. Do not analyse an arm in state 'tracking': "
            "its primitives table is still growing. Record n_feature_rows and "
            "features_mtime with any result computed from this arm. "
            "If stale=true the pipeline is not running and every value here is "
            "last-known rather than current; do not present it as live."
        ),
        "arms": index,
    }
    tmp = runs / "arm_readiness.json.tmp"
    tmp.write_text(json.dumps(payload, indent=2))
    tmp.replace(runs / "arm_readiness.json")
    return payload
