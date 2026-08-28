"""
Binding a result to the sample it was computed from.

The failure this exists to prevent
----------------------------------
Merrill Kelly was being deepened from 8 games to 25. Partway through, discovery
ran against the run directory and found four differences surviving holdout and
BH-FDR, one at a holdout Hedges g of 0.877 — the strongest candidate the project
had produced. Re-run after the deepening finished, on the same code and the same
directory, the same four contrasts measured -0.001, -0.194, +0.093 and -0.125,
and nothing survived out of 828 comparisons.

Nothing was wrong with the cues, the statistics, or the code. The run directory
simply held a third of the CU/SL pitches at the moment it was read, and there was
no signal anywhere in the output that the sample was incomplete. Two agents
working the same directory diverged twice for exactly this reason.

This is a different species of error from the other four the project has caught.
The degenerate holdout, the catcher features that measured the pitcher, PitchCom
counting glove variance and cheek motion measuring head jitter were all faults in
an *instrument*, and all four were found by asking "what does this cue actually
measure". That question cannot catch this one, because every instrument was
sound. Only the sample was partial. So the guard has to be about identity of
data rather than validity of measurement.

Why a recorded fingerprint is not enough
---------------------------------------
Recording the sample in the JSON was the obvious fix and it is insufficient: it
only helps if somebody reads it, and the whole failure mode is a plausible result
that nobody had reason to question. What has actually worked on this project is
structural refusal — disjoint games or no tip, NaN when the subject is not
identified, ``RETRACTED_CUES`` consulted before the statistical gates rather than
after. So this module does three things:

  ``fingerprint``        identifies the exact sample a result was computed on
  ``assert_quiescent``   refuses to compute against a directory being written
  ``mismatches``         lets the publisher refuse a result whose sample moved

The last is the one that matters. A stale result does not get a warning printed
next to it; it fails to publish.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

# Inputs whose contents define the sample. If any of these differs from what a
# result recorded, that result describes a sample that no longer exists.
#
# trajectory.csv is included even though it is absent for most runs: a missing
# input records as absent and is not a mismatch, whereas an input that is read but
# not fingerprinted is exactly the hole this guard exists to close.
SAMPLE_INPUTS = ("features.csv", "primitives.csv", "trajectory.csv")

# Fallback quiet period, used only when the pipeline's own readiness file is
# unavailable. The pipeline publishes its own `active_window_secs` (currently 900)
# and that value is preferred wherever present, because the pipeline owns tracking
# and knows how long a gap between writes actually means "finished".
QUIESCENT_SECONDS = 60.0

READINESS = Path("runs/arm_readiness.json")

# States the tracking pipeline reports for an arm. Anything other than a finished
# arm is unsafe to analyse; "tracking" is the exact state that produced the Kelly
# artefact.
UNSAFE_STATES = {"tracking", "empty", "partial"}


def _digest(path: Path) -> dict[str, Any]:
    """Content identity of one input file, plus mtime for human diagnosis."""
    if not path.is_file():
        return {"present": False}
    raw = path.read_bytes()
    return {
        "present": True,
        "bytes": len(raw),
        # Row count excluding the header; the number an analyst would quote.
        "rows": max(0, raw.count(b"\n") - 1),
        "sha256": hashlib.sha256(raw).hexdigest()[:16],
        "mtime": round(path.stat().st_mtime, 3),
        "mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(path.stat().st_mtime)),
    }


def _readiness_doc(run_dir: Path, readiness_path: Path | None = None) -> dict[str, Any] | None:
    """Load the pipeline's readiness file, tolerating either layout.

    The pipeline has published this file both as a flat mapping of run name to
    state and, later, wrapped under an ``arms`` key alongside its own
    ``active_window_secs``. Both are accepted: this file is owned by the
    tracking pipeline and a schema change there must not silently disable the
    guard here — which is the same class of bug the guard exists to prevent.
    """
    for path in (
        readiness_path,
        run_dir.parent.parent / READINESS,
        run_dir.parent / "arm_readiness.json",
    ):
        if path and path.is_file():
            try:
                return json.loads(path.read_text())
            except Exception:
                return None
    return None


def readiness_for(run_dir: Path, readiness_path: Path | None = None) -> dict[str, Any] | None:
    """The pipeline's own view of whether this arm is finished tracking.

    Maintained by the tracking pipeline and recomputed from disk on every
    snapshot, so it is a live statement rather than a cached one. Consulted
    rather than duplicated: the pipeline owns tracking and knows when an arm is
    mid-flight.
    """
    doc = _readiness_doc(run_dir, readiness_path)
    if not doc:
        return None
    arms = doc.get("arms") if isinstance(doc.get("arms"), dict) else doc
    entry = arms.get(run_dir.name)
    if entry is None:
        return None
    entry = dict(entry)
    if isinstance(doc.get("active_window_secs"), (int, float)):
        entry.setdefault("_active_window_secs", doc["active_window_secs"])
    return entry


def fingerprint(
    run_dir: Path,
    features_name: str = "features.csv",
    df: Any | None = None,
) -> dict[str, Any]:
    """Identify the sample a result is about to be computed from.

    Records the two input tables by content, the track count on disk, and — when
    the assembled frame is supplied — the window and game counts the result
    actually rests on, which is what a reader wants to compare against a claim.
    """
    inputs = {}
    for name in SAMPLE_INPUTS:
        key = features_name if name == "features.csv" else name
        inputs[name] = _digest(run_dir / key)

    tracks = run_dir / "tracks"
    n_tracks = len(list(tracks.glob("*.csv"))) if tracks.is_dir() else 0

    fp: dict[str, Any] = {
        "run_dir": run_dir.name,
        "features_name": features_name,
        "inputs": inputs,
        "n_tracks_on_disk": n_tracks,
        "computed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if df is not None and len(getattr(df, "columns", [])):
        fp["n_windows"] = int(len(df))
        if "game_pk" in df.columns:
            fp["n_games"] = int(df["game_pk"].nunique())
    r = readiness_for(run_dir)
    if r is not None:
        fp["readiness"] = {
            "ready": r.get("ready"),
            "state": r.get("state"),
            "schema": r.get("schema"),
            "n_current_tracks": r.get("n_current_tracks"),
            "n_feature_rows": r.get("n_feature_rows"),
            "seconds_since_write": r.get("seconds_since_write"),
            "stale_reason": r.get("stale_reason"),
        }
    return fp


def mismatches(recorded: dict[str, Any] | None, run_dir: Path) -> list[str]:
    """How a recorded sample differs from what is on disk now.

    Empty list means the result still describes the data. Anything else means the
    result is about a sample that has changed underneath it, and the caller must
    treat it as unpublishable rather than merely annotated.
    """
    if not recorded:
        return ["no_sample_fingerprint_recorded"]

    out: list[str] = []
    now = fingerprint(run_dir, recorded.get("features_name", "features.csv"))
    for name, was in (recorded.get("inputs") or {}).items():
        is_ = now["inputs"].get(name, {"present": False})
        if was.get("present") and not is_.get("present"):
            out.append(f"{name}: was present, now missing")
        elif was.get("present") and was.get("sha256") != is_.get("sha256"):
            out.append(
                f"{name}: {was.get('rows')} rows -> {is_.get('rows')} rows "
                f"(content changed; recorded {was.get('mtime_iso')})"
            )
    if (
        recorded.get("n_tracks_on_disk") is not None
        and recorded["n_tracks_on_disk"] != now["n_tracks_on_disk"]
    ):
        out.append(
            f"tracks on disk: {recorded['n_tracks_on_disk']} -> {now['n_tracks_on_disk']}"
        )
    return out


def assert_quiescent(run_dir: Path, allow_unready: bool = False) -> dict[str, Any]:
    """Refuse to compute against a run directory that is still being written.

    This is the precise circumstance that produced the Kelly artefact, so it is
    an exception rather than a warning. ``--allow-unready`` exists for
    deliberately inspecting an in-flight arm, and results produced that way carry
    the readiness state in their fingerprint and will not publish.
    """
    state: dict[str, Any] = {"run_dir": run_dir.name, "ready": None, "state": None, "quiet_for": None}
    r = readiness_for(run_dir)
    if r is not None:
        state["ready"] = bool(r.get("ready"))
        state["state"] = r.get("state")
        if not r.get("ready") and not allow_unready:
            detail = r.get("stale_reason") or r.get("state") or "no reason given"
            raise SystemExit(
                f"{run_dir.name}: arm_readiness.json marks this arm NOT ready "
                f"(state={r.get('state')}, {detail}). Discovery on a partially "
                "tracked arm is how the Kelly four-survivor artefact was produced. "
                "Wait for tracking to finish, or pass --allow-unready to inspect it "
                "knowing the result cannot publish."
            )
        if str(r.get("state")) in UNSAFE_STATES and not allow_unready:
            raise SystemExit(
                f"{run_dir.name}: pipeline reports state={r.get('state')} — its tables "
                "are still growing. Re-run once tracking has finished."
            )

    # The pipeline publishes the quiet period it considers sufficient, and that
    # threshold governs because the pipeline owns tracking. How long the directory
    # has actually been quiet is taken as the SMALLER of what the pipeline reported
    # and what is observable on disk right now: the readiness file is a snapshot
    # that may be minutes old, so a "complete" arm in it can already be receiving
    # writes again. Trusting the stale half of that pair would reintroduce exactly
    # the failure this guard exists to prevent.
    window = float((r or {}).get("_active_window_secs") or QUIESCENT_SECONDS)
    candidates = []
    reported = (r or {}).get("seconds_since_write")
    if reported is not None:
        candidates.append(float(reported))
    tracks = run_dir / "tracks"
    if tracks.is_dir():
        newest = max((p.stat().st_mtime for p in tracks.glob("*.csv")), default=None)
        if newest is not None:
            candidates.append(time.time() - newest)
    quiet = min(candidates) if candidates else None
    if quiet is not None:
        state["quiet_for"] = round(float(quiet), 1)
        if float(quiet) < window and not allow_unready:
            raise SystemExit(
                f"{run_dir.name}: last written {float(quiet):.0f}s ago, inside the "
                f"{window:.0f}s quiet period — the directory looks like it is still "
                "being tracked, so any sample read now may be partial. Re-run once "
                "tracking has finished."
            )
    return state


def describe(fp: dict[str, Any] | None) -> str:
    """One line naming the sample, for a report header."""
    if not fp:
        return "sample: unrecorded"
    prim = (fp.get("inputs") or {}).get("primitives.csv") or {}
    feat = (fp.get("inputs") or {}).get("features.csv") or {}
    bits = [
        f"windows={fp.get('n_windows')}",
        f"games={fp.get('n_games')}",
        f"features={feat.get('rows')} rows",
        f"primitives={prim.get('rows')} rows @ {prim.get('mtime_iso')}",
        f"tracks={fp.get('n_tracks_on_disk')}",
    ]
    return "sample: " + " | ".join(str(b) for b in bits)
