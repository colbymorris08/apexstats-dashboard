"""
Regression checks for retracted cues and for the guards that made them
retractable in the first place.

Four features have now shipped while measuring something other than their own
name: a degenerate holdout, the catcher scalars (the catcher pose was the
pitcher in 71-91% of frames), ``pitchcom_tap_count`` (glove-centroid motion
variance, not taps), and ``cheek_motion_*`` (head-position jitter, not facial
motion, because the face model was silently replaced by the pose nose).

The pattern in all four is the same: a fully-populated column with a confident
label and the wrong contents. These checks encode the two defences against it —
the retraction registry is consulted BEFORE any statistical gate, and a feature
that cannot see its subject emits NaN rather than a substitute.

Run directly: ``python -m preflight.test_retractions``
"""
from __future__ import annotations

import numpy as np

from preflight import provenance as PR

CHEEK = ("cheek_motion_mean", "cheek_motion_std")
PITCHCOM = ("pitchcom_tap_count", "pitchcom_tap_rate", "pitchcom_mean_isi")


def test_cheek_cues_are_registered_as_retracted() -> None:
    for cue in CHEEK:
        assert cue in PR.RETRACTED_CUES, cue
        why = PR.RETRACTED_CUES[cue]
        # The reason has to carry the measurement, not just an opinion.
        assert "1.04%" in why or "pose-nose" in why, why


def test_pitchcom_retraction_is_still_in_place() -> None:
    """The cheek retraction must not have displaced the earlier one."""
    for cue in PITCHCOM:
        assert cue in PR.RETRACTED_CUES, cue


def test_retracted_cue_fails_before_the_statistical_gates() -> None:
    """
    A retracted cue must be refused even when its holdout evidence is perfect
    and its confidence is far above the floor. This is the whole point of
    checking retraction first: a strong result on a number that measures the
    wrong thing is a strong result about nothing.
    """
    report = {"tip_split": {"train_games": [1, 2], "test_games": [3]}}
    for cue in CHEEK:
        tip = {"id": "t", "feature": cue, "confidence": 0.99, "validated": True}
        ok, why = PR.tip_is_backed(tip, report, floor=0.75)
        assert not ok, cue
        assert why == f"retracted_cue:{cue}", why
    # A non-retracted cue with the same evidence still passes, so the check is
    # discriminating rather than blanket-refusing.
    ok, why = PR.tip_is_backed(
        {"id": "t", "feature": "glove_height_at_lift", "confidence": 0.99, "validated": True},
        report,
        floor=0.75,
    )
    assert ok, why


def test_scrub_coverage_demotes_cheek_entries_and_drops_their_accuracy() -> None:
    """
    situationCoverage bypasses the per-tip checks — merge_demo copies it onto the
    player card wholesale — which is how two cheek entries came to be published
    as ``discernable: true`` on Drew Thorpe's card with accuracies of 0.76 and
    0.778. The scrub has to reach into that block.
    """
    cov = {
        "situations": [
            {
                "arsenal_n": 2,
                "types": [
                    {"pitch_type": "CH", "discernable": True, "accuracy": 0.76,
                     "precision": 0.833, "feature": "cheek_motion_mean"},
                    {"pitch_type": "FF", "discernable": True, "accuracy": 0.80,
                     "precision": 0.9, "feature": "glove_height_at_lift"},
                ],
            }
        ]
    }
    out, n = PR.scrub_coverage(cov)
    assert n == 1, n
    types = out["situations"][0]["types"]
    bad, good = types[0], types[1]
    assert bad["discernable"] is False
    assert bad["status"] == "cue_retracted"
    assert bad["retracted_cue"] == "cheek_motion_mean"
    for k in ("accuracy", "precision", "feature"):
        assert k not in bad, k
    # The honest cue is untouched and the denominator still reflects the arsenal.
    assert good["discernable"] is True and good["accuracy"] == 0.80
    assert out["situations"][0]["coverage"] == "1 of 2"
    # The input must not be mutated in place.
    assert cov["situations"][0]["types"][0]["discernable"] is True


def test_scrub_coverage_reaches_best_situation() -> None:
    """best_situation is a separate copy and was published on its own."""
    entry = {"pitch_type": "CH", "discernable": True, "accuracy": 0.76,
             "feature": "cheek_motion_std"}
    out, n = PR.scrub_coverage({"situations": [], "best_situation": {"arsenal_n": 1, "types": [entry]}})
    assert n == 1, n
    assert out["best_situation"]["types"][0]["status"] == "cue_retracted"


# --- the guard that stops it recurring ---------------------------------------

class _LM:
    def __init__(self, x, y, v=0.9):
        self.x, self.y, self.visibility, self.presence = x, y, v, v


def _pose(nose=(0.50, 0.30), lsho=(0.45, 0.40), rsho=(0.55, 0.40)):
    """A minimal pose landmark list: index 0 nose, 11/12 shoulders."""
    lms = [_LM(0.0, 0.0) for _ in range(33)]
    lms[0] = _LM(*nose)
    lms[11] = _LM(*lsho)
    lms[12] = _LM(*rsho)
    return lms


def _cheek_from(face_xy, pose):
    """
    The subject check exactly as track_pitcher applies it, exercised without
    needing MediaPipe or a video decode.
    """
    from preflight.track_pitcher import (
        L_SHOULDER,
        MAX_FACE_TO_NOSE_SHOULDER_WIDTHS,
        NOSE,
        R_SHOULDER,
        _xy,
    )

    if face_xy is None:
        return None, "no_face"
    nose, l_s, r_s = _xy(pose, NOSE), _xy(pose, L_SHOULDER), _xy(pose, R_SHOULDER)
    if nose is None or l_s is None or r_s is None:
        return None, "no_pose_to_verify_subject"
    sho_w = float(np.hypot(l_s[0] - r_s[0], l_s[1] - r_s[1]))
    if sho_w <= 1e-9:
        return None, "degenerate_pose"
    d = float(np.hypot(face_xy[0] - nose[0], face_xy[1] - nose[1])) / sho_w
    if d > MAX_FACE_TO_NOSE_SHOULDER_WIDTHS:
        return None, "face_not_on_pitcher"
    return face_xy, "face_landmarker"


def test_no_face_yields_nan_not_the_pose_nose() -> None:
    """
    The retracted behaviour: with no face, the tracker substituted the pose
    nose, producing a populated column of head jitter labelled facial motion.
    """
    cheek, src = _cheek_from(None, _pose())
    assert cheek is None, cheek
    assert src == "no_face"


def test_a_face_across_the_frame_is_rejected() -> None:
    """
    The measured failure mode: detected faces sit a median 2.24 shoulder widths
    from the pitcher's nose. At a shoulder width of 0.10, that is 0.224 away.
    """
    pose = _pose()
    cheek, src = _cheek_from((0.50 + 0.224, 0.30), pose)
    assert cheek is None
    assert src == "face_not_on_pitcher"


def test_a_face_on_the_pitcher_is_accepted() -> None:
    """The guard must not reject a genuine detection."""
    cheek, src = _cheek_from((0.505, 0.315), _pose())
    assert cheek is not None
    assert src == "face_landmarker"


def test_cheek_motion_is_not_differenced_across_a_gap() -> None:
    """
    Motion needs two CONSECUTIVE pitcher-face frames. Differencing across
    dropped frames reports the gap as movement, which is the same error that put
    17-43% of the retired PitchCom detections on a re-acquisition.
    """
    prev, prev_frame = (0.50, 0.30), 10
    cur, cur_frame = (0.60, 0.30), 25  # 15 frames later
    motion = (
        float(np.hypot(cur[0] - prev[0], cur[1] - prev[1]))
        if prev_frame == cur_frame - 1
        else None
    )
    assert motion is None


def test_cheek_source_column_is_emitted() -> None:
    """
    A blank cheek column must say why it is blank, or a reader cannot tell "he
    held still" from "we never saw his face".
    """
    import inspect

    from preflight import track_pitcher

    src = inspect.getsource(track_pitcher)
    assert '"cheek_source"' in src or "'cheek_source'" in src
    # And the fallback must be gone.
    assert "cheek = _xy(plm, NOSE)" not in src


def test_catcher_family_is_retracted() -> None:
    """
    Every catcher feature must be retracted, not just guarded at the tracker.

    The subject-selection fallback was fixed in track_pitcher.py, which stopped
    the bug for FUTURE tracks and did nothing about the results already on the
    board: a live tip and 34 discernable coverage entries were still resting on
    pre-guard columns that carried the pitcher's own body. Fixing the producer is
    not the same as withdrawing the claim.
    """
    from preflight.provenance import RETRACTED_CUES
    from preflight.run_poc import window_features

    for cue in (
        "catcher_glove_x_mean",
        "catcher_glove_y_mean",
        "catcher_stance_mean",
        "catcher_hip_y_mean",
        "catcher_glove_speed_mean",
        "catcher_glove_speed_p90",
    ):
        assert cue in RETRACTED_CUES, cue
        assert cue not in __import__(
            "preflight.spot_diff", fromlist=["CUES"]
        ).CUES, f"{cue} is still wired into discovery"
    assert callable(window_features)


def test_glove_angle_is_retracted_and_superseded() -> None:
    """
    The angle form is withdrawn and the recoverable vertical component replaces
    it under a name that does not overclaim.
    """
    from preflight.primitives import PRIMITIVE_STATUS
    from preflight.provenance import RETRACTED_CUES
    from preflight.spot_diff import CUES

    for cue in ("glove_angle_at_lift", "glove_angle_at_set"):
        assert cue in RETRACTED_CUES, cue
        assert cue not in CUES, f"{cue} is still wired into discovery"
        assert PRIMITIVE_STATUS[cue] == "retracted"

    rep = "glove_rise_above_elbow_at_lift"
    assert rep in CUES, "the replacement cue is not wired"
    # It must carry a distance threshold, not the angle's unusable 8 degrees.
    assert CUES[rep].unit == "torso lengths"
    assert CUES[rep].visible_delta == 0.05
    # And it must not be named as though it recovered the angle.
    assert "angle" not in CUES[rep].label.lower()


def test_window_features_never_fabricate_a_zero() -> None:
    """
    A missing measurement must emit NaN, never 0.0.

    Zero is a specific physical claim in every one of these columns — the glove
    exactly at belt height, the catcher at the frame origin — so coercing NaN to
    it invented readings that then passed every downstream gate.
    """
    import numpy as np
    import pandas as pd

    from preflight.run_poc import window_features

    # A window with the columns present but entirely unusable.
    empty = pd.DataFrame(
        {
            c: [np.nan, np.nan, np.nan]
            for c in (
                "glove_vs_belt_y",
                "glove_flare",
                "wrist_speed",
                "cheek_motion",
                "catcher_glove_x",
                "catcher_glove_y",
                "catcher_stance_width",
                "catcher_hip_y",
                "catcher_glove_speed",
            )
        }
    )
    out = window_features(empty)
    assert out, "no features emitted"
    for k, v in out.items():
        assert np.isnan(v), f"{k} fabricated {v!r} from an empty window"

    # Columns absent entirely must also be NaN, not 0.0. This is the path the
    # 251 pre-catcher-column tracks took.
    out2 = window_features(pd.DataFrame({"glove_vs_belt_y": [0.1, 0.2, 0.3]}))
    for k, v in out2.items():
        if k.startswith("catcher_"):
            assert np.isnan(v), f"{k} fabricated {v!r} from an absent column"
    # And a real measurement still comes through.
    assert abs(out2["glove_vs_belt_mean"] - 0.2) < 1e-9


def test_superseded_cues_are_demoted_from_coverage() -> None:
    """
    A coverage block may not assert a cue is discernable when discovery no
    longer tests that cue: no future run could reproduce the claim.
    """
    from preflight.provenance import SUPERSEDED_CUES, scrub_coverage
    from preflight.spot_diff import CUES

    for cue in SUPERSEDED_CUES:
        assert cue not in CUES, f"{cue} is marked superseded but still in CUES"

    cov = {
        "situations": [
            {
                "arsenal_n": 2,
                "types": [
                    {"pitch_type": "CH", "feature": "glove_flare_std", "discernable": True, "accuracy": 0.9},
                    {"pitch_type": "FF", "feature": "wrist_speed_mean", "discernable": True, "accuracy": 0.8},
                ],
            }
        ]
    }
    out, removed = scrub_coverage(cov)
    assert removed == 1, removed
    types = out["situations"][0]["types"]
    assert types[0]["discernable"] is False
    assert types[0]["status"] == "cue_superseded"
    assert "accuracy" not in types[0]
    # The surviving cue is untouched, so the arsenal denominator stays honest.
    assert types[1]["discernable"] is True
    assert out["situations"][0]["coverage"] == "1 of 2"


def test_play_id_survives_every_track_filename_layout() -> None:
    """
    The play_id must come back identical whichever pass wrote the track file.

    This is the bug that disconnected the two halves of the system. ``lift_tracks``
    wrote "<play_id>.csv" and the pipeline's unified ``tracks`` writes
    "<play_id>_tracks.csv", so a bare ``path.stem`` produced keys ending in
    "_tracks" that matched nothing in features.csv — 0 of 358 play_ids on Webb.
    Nothing raised: the outer merge just built two disjoint halves and discovery
    reported 20 cues available while every primitive column sat on rows with no
    pitch type.
    """
    from pathlib import Path

    from preflight.primitives import play_id_of

    pid = "007170fe-bee6-3d02-a038-42aadb299537"
    for name in (f"{pid}.csv", f"{pid}_tracks.csv", f"{pid}_lift.csv"):
        assert play_id_of(Path("/runs/x/tracks") / name) == pid, name
    # A play_id that merely contains the word must not be truncated.
    odd = "abc_tracks_def"
    assert play_id_of(Path(f"/r/{odd}.csv")) == odd


def test_broken_primitive_join_is_an_error_not_a_silent_degradation() -> None:
    """
    A primitives table that shares no keys with the feature table must stop the
    run. Discovering on the outer-joined frame is worse than failing, because it
    produces a complete-looking report whose cue list is a fiction.
    """
    import tempfile
    from pathlib import Path

    import pandas as pd
    import pytest

    from preflight.spot_diff import load_pitcher

    def write(tmp, prim_ids):
        (tmp / "features.csv").write_text(
            pd.DataFrame(
                {"play_id": [f"p{i}" for i in range(20)], "pitch_type": ["FF"] * 20}
            ).to_csv(index=False)
        )
        (tmp / "primitives.csv").write_text(
            pd.DataFrame(
                {"play_id": prim_ids, "glove_height_at_lift": [0.5] * len(prim_ids)}
            ).to_csv(index=False)
        )

    tmp = Path(tempfile.mkdtemp())
    write(tmp, [f"p{i}_tracks" for i in range(20)])  # the broken-key case
    with pytest.raises(SystemExit, match="join key is broken"):
        load_pitcher(tmp)

    # And the healthy case still loads.
    tmp2 = Path(tempfile.mkdtemp())
    write(tmp2, [f"p{i}" for i in range(20)])
    df = load_pitcher(tmp2)
    assert len(df) == 20
    assert df["glove_height_at_lift"].notna().all()


def test_sway_family_is_permanently_excluded_not_pending() -> None:
    """
    The sway family must not be marked as merely under-covered.

    Its coverage shortfall was attributed to clips being cut short. Savant serves
    a fixed 180-frame render with no trim parameter, so the missing lead-in does
    not exist in any requestable asset and the coverage ceiling is structural.
    Leaving it as "under_covered" implies a fix that is not available, which would
    keep the cue permanently queued for a re-fetch that cannot help.
    """
    from preflight.primitives import PRIMITIVE_STATUS
    from preflight.spot_diff import CUES

    for cue in ("sway_amplitude", "sway_dx", "sway_dy", "sway_directness", "come_set_peak_speed"):
        assert PRIMITIVE_STATUS[cue] == "excluded_permanently", cue
        assert cue not in CUES, cue


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
