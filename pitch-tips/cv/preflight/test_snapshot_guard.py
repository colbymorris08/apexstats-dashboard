"""
Regression tests for the sample-snapshot guard.

The failure being guarded against is the fifth of its kind on this project and
the first where nothing was wrong with the measurement: discovery ran against
Merrill Kelly while he was being deepened from 8 games to 25, reported four
differences surviving holdout and BH-FDR at up to g=0.877, and lost all four when
re-run on the finished sample.

The point of these tests is that the guard REFUSES rather than warns. A recorded
fingerprint that nobody reads would not have prevented anything, so the assertions
below are about publication being withheld.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import pytest

from preflight import provenance, snapshot


def _run_dir(tmp_path: Path, name: str = "someone_poc", rows: int = 40) -> Path:
    """A minimal run directory that looks finished and internally consistent."""
    run = tmp_path / "runs" / name
    (run / "tracks").mkdir(parents=True)
    play_ids = [f"p{i:04d}" for i in range(rows)]
    pd.DataFrame(
        {
            "play_id": play_ids,
            "game_pk": [700000 + (i % 6) for i in range(rows)],
            "pitch_type": ["FF" if i % 2 else "SL" for i in range(rows)],
        }
    ).to_csv(run / "features.csv", index=False)
    pd.DataFrame(
        {"play_id": play_ids, "glove_flare_at_lift": [0.1 + 0.001 * i for i in range(rows)]}
    ).to_csv(run / "primitives.csv", index=False)
    for pid in play_ids:
        (run / "tracks" / f"{pid}_tracks.csv").write_text("frame\n0\n")
    # Age the tracks well clear of any quiet period — including the pipeline's
    # published 900s window — so the directory reads as finished.
    old = time.time() - 86400
    for p in (run / "tracks").glob("*.csv"):
        import os

        os.utime(p, (old, old))
    return run


def _readiness(
    run: Path, ready: bool = True, n_tracks: int = 40, wrapped: bool = True
) -> None:
    """Write the pipeline's readiness file in either published layout."""
    entry = {
        "work": f"runs/{run.name}",
        "state": "complete" if ready else "tracking",
        "n_current_tracks": n_tracks,
        "schema": "rich_72col",
        "ready": ready,
        "stale_reason": None if ready else "120/300 tracks",
        "has_features": True,
        "seconds_since_write": 6705.1 if ready else 3.0,
    }
    doc = (
        {"generated_at_human": "now", "active_window_secs": 900, "arms": {run.name: entry}}
        if wrapped
        else {run.name: entry}
    )
    path = run.parent.parent / "runs" / "arm_readiness.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc))


def test_both_published_readiness_layouts_are_understood(tmp_path):
    """
    The readiness file is owned by the tracking pipeline and its schema has already
    changed once, from a flat mapping to one wrapped under an "arms" key. A schema
    change there must not silently disable this guard — that would be the same
    class of bug the guard exists to catch.
    """
    for wrapped in (True, False):
        run = _run_dir(tmp_path / f"w{wrapped}")
        _readiness(run, ready=False, wrapped=wrapped)
        assert snapshot.readiness_for(run) is not None, (
            f"readiness lookup failed for wrapped={wrapped} layout"
        )
        with pytest.raises(SystemExit, match="NOT ready"):
            snapshot.assert_quiescent(run)


def test_pipeline_active_window_is_preferred_over_the_local_default(tmp_path):
    """The pipeline owns tracking, so its quiet period governs, not ours."""
    run = _run_dir(tmp_path)
    _readiness(run, ready=True)
    # 400s of quiet clears the local 60s default but not the pipeline's 900s.
    doc = json.loads((run.parent.parent / "runs" / "arm_readiness.json").read_text())
    doc["arms"][run.name]["seconds_since_write"] = 400.0
    (run.parent.parent / "runs" / "arm_readiness.json").write_text(json.dumps(doc))
    assert 400.0 > snapshot.QUIESCENT_SECONDS
    with pytest.raises(SystemExit, match="quiet period"):
        snapshot.assert_quiescent(run)


# --------------------------------------------------------------------------
# The fingerprint identifies the sample
# --------------------------------------------------------------------------

def test_fingerprint_records_rows_mtime_windows_and_games(tmp_path):
    run = _run_dir(tmp_path, rows=40)
    df = pd.read_csv(run / "features.csv")
    fp = snapshot.fingerprint(run, "features.csv", df)

    prim = fp["inputs"]["primitives.csv"]
    assert prim["rows"] == 40, "row count of the primitives table must be recorded"
    assert prim["mtime"] > 0 and prim["mtime_iso"], "mtime must be recorded"
    assert prim["sha256"], "content digest must be recorded"
    assert fp["n_windows"] == 40
    assert fp["n_games"] == 6
    assert fp["n_tracks_on_disk"] == 40


def test_an_unchanged_sample_reports_no_mismatch(tmp_path):
    run = _run_dir(tmp_path)
    fp = snapshot.fingerprint(run, "features.csv")
    assert snapshot.mismatches(fp, run) == []


def test_a_deepened_sample_is_detected(tmp_path):
    """The Kelly case: more pitches arrive after the result was computed."""
    run = _run_dir(tmp_path, rows=40)
    fp = snapshot.fingerprint(run, "features.csv")

    _run_dir_grow(run, extra=80)
    bad = snapshot.mismatches(fp, run)
    assert bad, "growing the sample must be detected"
    assert any("primitives.csv" in m and "40 rows -> 120 rows" in m for m in bad), bad


def _run_dir_grow(run: Path, extra: int) -> None:
    """Add `extra` fresh pitches to both tables, as a deepening pass would."""
    for name in ("features.csv", "primitives.csv"):
        df = pd.read_csv(run / name, dtype={"play_id": str})
        reps = -(-extra // max(1, len(df)))  # ceil, so `extra` rows are available
        add = pd.concat([df] * reps).head(extra).copy()
        add["play_id"] = [f"x{i:04d}" for i in range(len(add))]
        pd.concat([df, add]).to_csv(run / name, index=False)


def test_missing_fingerprint_is_itself_a_mismatch(tmp_path):
    """A result predating the guard cannot be assumed to be about current data."""
    run = _run_dir(tmp_path)
    assert snapshot.mismatches(None, run) == ["no_sample_fingerprint_recorded"]
    assert snapshot.mismatches({}, run) == ["no_sample_fingerprint_recorded"]


# --------------------------------------------------------------------------
# Refusing to compute against a directory being written
# --------------------------------------------------------------------------

def test_refuses_to_compute_on_an_arm_marked_not_ready(tmp_path):
    run = _run_dir(tmp_path)
    _readiness(run, ready=False)
    with pytest.raises(SystemExit, match="NOT ready"):
        snapshot.assert_quiescent(run)


def test_refuses_to_compute_while_tracks_are_being_written(tmp_path):
    """
    A fresh write on disk must block even when readiness calls the arm complete.

    The readiness file is a snapshot and can be minutes old, so an arm recorded as
    "complete" with 6705s of quiet may already be receiving writes again. The
    observed quiet time on disk has to be able to override the reported one.
    """
    run = _run_dir(tmp_path)
    _readiness(run, ready=True)  # reports state=complete, quiet for 6705s
    (run / "tracks" / "just_now_tracks.csv").write_text("frame\n0\n")
    with pytest.raises(SystemExit, match="quiet period"):
        snapshot.assert_quiescent(run)


def test_a_finished_arm_is_allowed_through(tmp_path):
    run = _run_dir(tmp_path)
    _readiness(run, ready=True)
    state = snapshot.assert_quiescent(run)
    assert state["ready"] is True


def test_allow_unready_permits_inspection_but_records_it(tmp_path):
    """Deliberate inspection of an in-flight arm stays possible and stays marked."""
    run = _run_dir(tmp_path)
    _readiness(run, ready=False)
    snapshot.assert_quiescent(run, allow_unready=True)  # must not raise
    fp = snapshot.fingerprint(run, "features.csv")
    assert fp["readiness"]["ready"] is False, (
        "an in-flight read must carry its unreadiness into the result"
    )


# --------------------------------------------------------------------------
# The part that matters: a stale result does not publish
# --------------------------------------------------------------------------

def _submit_for_publication(run: Path, sample: dict | None, n_tips: int = 1) -> list[str]:
    """Write a discovery result plus a tip, and ask the publisher about it."""
    tip = {
        "id": "t1",
        "feature": "glove_flare_at_lift",
        "confidence": 0.91,
        "situation": "stretch",
    }
    (run / "report.json").write_text(
        json.dumps(
            {
                "pitcher": "Someone",
                "tips": [tip] * n_tips,
                "catcherTips": [],
                "tip_split": {"train_games": [700000, 700001], "test_games": [700002]},
            }
        )
    )
    res = {"pitcher": "Someone", "comparisons": 828, "n_surviving": n_tips}
    if sample is not None:
        res["sample"] = sample
    (run / "spot_diff.json").write_text(json.dumps(res))
    return provenance.stale_sample_reasons(run)


def test_a_result_on_the_current_sample_is_not_blocked_by_this_guard(tmp_path):
    run = _run_dir(tmp_path)
    _readiness(run, ready=True)
    assert _submit_for_publication(run, snapshot.fingerprint(run, "features.csv")) == []


def test_a_stale_result_is_refused_publication(tmp_path):
    """The Kelly scenario end to end: compute, sample grows, publication refused."""
    run = _run_dir(tmp_path, rows=40)
    _readiness(run, ready=True)
    fp = snapshot.fingerprint(run, "features.csv")
    _run_dir_grow(run, extra=80)

    reasons = _submit_for_publication(run, fp)
    assert reasons, "a result whose sample tripled must not publish"
    assert all(r.startswith("sample_moved:") for r in reasons), reasons

    ev = provenance.evidence_for(run)
    assert ev["tips"] == [], "no tip may survive a moved sample"
    assert any(r.startswith("sample_moved:") for r in ev["reasons"]), ev["reasons"]


def test_a_result_computed_on_an_unready_arm_is_refused_publication(tmp_path):
    run = _run_dir(tmp_path)
    _readiness(run, ready=False)
    fp = snapshot.fingerprint(run, "features.csv")
    assert fp["readiness"]["ready"] is False

    reasons = _submit_for_publication(run, fp)
    assert reasons == ["discovery_ran_on_an_arm_still_being_tracked"]
    assert provenance.evidence_for(run)["tips"] == []


def test_a_result_without_a_fingerprint_is_refused_publication(tmp_path):
    """Results predating the guard must not be grandfathered in."""
    run = _run_dir(tmp_path)
    _readiness(run, ready=True)
    reasons = _submit_for_publication(run, sample=None)
    assert reasons == ["discovery_result_predates_sample_fingerprinting"]
    assert provenance.evidence_for(run)["tips"] == []


def test_guard_is_checked_even_when_every_statistical_gate_passes(tmp_path):
    """
    The whole lesson of the fifth failure: the statistics were impeccable.

    The submitted tip has a disjoint game-level split and a confidence well over
    the 0.75 floor, so every existing gate passes. Publication must still be
    withheld purely because the sample moved.
    """
    run = _run_dir(tmp_path, rows=40)
    _readiness(run, ready=True)
    fp = snapshot.fingerprint(run, "features.csv")
    _run_dir_grow(run, extra=80)
    _submit_for_publication(run, fp)

    report = json.loads((run / "report.json").read_text())
    tip = report["tips"][0]
    assert provenance._split_backs_tips(report), "the split itself is sound"
    assert tip["confidence"] > provenance.DEFAULT_TIP_FLOOR, "the effect clears the floor"
    assert provenance.tip_is_backed(tip, report, provenance.DEFAULT_TIP_FLOOR)[0], (
        "and the tip passes every per-tip gate"
    )
    assert provenance.evidence_for(run)["tips"] == [], (
        "yet it must not publish, because the sample it rests on no longer exists"
    )
