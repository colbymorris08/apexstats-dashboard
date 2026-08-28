"""
Is the pipeline actually alive, and does anything downstream say so out loud?

The janitor, supervisor and heartbeat have died silently three times. The lost
tracking time was not the worst of it: a dead heartbeat leaves the readiness
index and the progress page showing their last-known values, which read as
current. A consumer sees an arm at "complete, 463 rows" and cannot tell whether
that is true now or was true two hours ago — the same shape as the partial-sample
artifact, where a number that looked finished was not.

So staleness is published as a field rather than left to be inferred. A visible
stale marker is worth more than a daemon that is usually up.

The threshold is deliberately loose relative to the heartbeat's own cadence: the
keepalive touches every 60 s, so 300 s means five missed touches, which is a real
outage rather than one slow loop.
"""
from __future__ import annotations

import time
from pathlib import Path

HEARTBEAT_NAME = "league_progress_2026.json"
STALE_AFTER_SECS = 300


def heartbeat_age(runs: Path) -> float | None:
    """Seconds since the heartbeat was last touched, or None if absent."""
    hb = runs / HEARTBEAT_NAME
    if not hb.is_file():
        return None
    return time.time() - hb.stat().st_mtime


def liveness(runs: Path) -> dict:
    """
    A block for embedding in any published artifact.

    ``stale`` is the field consumers should branch on. When it is true the
    accompanying values are last-known rather than current and must not be
    presented as live.
    """
    age = heartbeat_age(runs)
    if age is None:
        return {
            "stale": True,
            "reason": f"no heartbeat file ({HEARTBEAT_NAME}) — pipeline has never run or state was cleared",
            "heartbeat_age_secs": None,
            "stale_after_secs": STALE_AFTER_SECS,
            "banner": "STALE — pipeline not running; values below are not current",
        }
    stale = age > STALE_AFTER_SECS
    return {
        "stale": stale,
        "reason": (
            f"heartbeat {age / 60:.1f} min old, over the {STALE_AFTER_SECS / 60:.0f} min threshold"
            if stale
            else f"heartbeat {age:.0f}s old"
        ),
        "heartbeat_age_secs": round(age, 1),
        "stale_after_secs": STALE_AFTER_SECS,
        "banner": (
            f"STALE — no pipeline heartbeat for {age / 60:.0f} min; "
            "values below are last-known, not current"
            if stale
            else None
        ),
    }
