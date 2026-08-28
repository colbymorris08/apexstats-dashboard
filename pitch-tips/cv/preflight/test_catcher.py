"""
Checks for catcher localisation and the pre-pitch glove target cue.

The catcher is the subject this project has got wrong most badly: its features
described the pitcher's body on 71-91% of frames while the columns looked 98.6%
populated. So the checks here are weighted toward the two things that failure
needed and did not have — a refusal path that is actually reachable, and names
that cannot be confused with the retracted ones.

Run directly: ``python -m preflight.test_catcher``
"""
from __future__ import annotations

import numpy as np


# --- localisation -------------------------------------------------------------

def test_umpire_mask_class_is_excluded_from_anchors() -> None:
    """
    ``catcher_mask`` must never anchor a catcher crop.

    It was the highest-rate catcher class at 77.5% of frames, and rendering the
    boxes showed it lands on the UMPIRE's head — he stands directly behind the
    catcher wearing the same equipment. Using it would have produced the best
    coverage numbers in the family and the wrong body for the third time.
    """
    from preflight import catcher_locate as CL

    assert "catcher_mask" in CL.EXCLUDED_CLASSES
    assert "catcher_mask" not in CL.ANCHOR_CLASSES


def test_crop_multipliers_match_the_measured_body_ratio() -> None:
    """
    Crop size must stay near the measured gear-box-to-body ratio.

    The first version used 5.0 and 4.0 chosen by eye, which is 2.3x and 2.9x the
    measured ratios (2.21 and 1.36), and the consequence was the hitter and the
    umpire inside the crop winning the pose competition. Margin is needed and is
    fine; a multiple of the ratio is not.
    """
    from preflight import catcher_locate as CL

    assert 2.21 <= CL.CROP_H_MULT <= 2.21 * 2.0, CL.CROP_H_MULT
    assert 1.36 <= CL.CROP_W_MULT <= 1.36 * 2.5, CL.CROP_W_MULT


def test_locate_refuses_rather_than_returning_a_best_guess() -> None:
    """
    Every failure path must return None, never a nearby pose.

    This is the specific defect the catcher columns had: an unconditional
    ``if clm is None: clm = by_hip[0]`` at the end of subject selection.
    """
    import inspect

    from preflight import catcher_locate as CL

    for fn in (CL.locate_catcher, CL.catcher_in_region, CL.catcher_crop, CL.clip_catcher_region):
        src = inspect.getsource(fn)
        # No bare "take the first/best candidate" recovery after the checks.
        assert "by_hip[0]" not in src
        assert "return None" in src or "_nan" in src, fn.__name__


def test_clip_region_is_one_rectangle_for_the_whole_clip() -> None:
    """
    The clip region must carry no per-frame positional information.

    This is what stops the crop from becoming a proxy for the cue: the third cue
    family measures WHERE the catcher sets up, so a crop that followed him frame
    by frame would move the frame of reference with the signal and the cue would
    read zero by construction. ``ClipRegion`` is a single immutable rectangle, so
    it cannot.
    """
    from dataclasses import fields

    from preflight.catcher_locate import ClipRegion

    assert ClipRegion.__dataclass_params__.frozen
    names = {f.name for f in fields(ClipRegion)}
    assert {"x1", "y1", "x2", "y2"} <= names
    # No per-frame field may exist on it.
    assert "frame" not in names


# --- glove target cue ---------------------------------------------------------

def _frames(lateral_by_frame: dict[int, float], pw: float = 0.06, plate_cx: float = 0.5):
    """Synthetic per-frame detector output at a given lateral offset."""
    out = []
    for f, dx in lateral_by_frame.items():
        out.append({
            "frame": f,
            "mitt": {"cx": plate_cx + dx * pw, "cy": 0.45, "bw": 0.02, "conf": 0.4},
            "plate": {"cx": plate_cx, "cy": 0.50, "bw": pw, "conf": 0.8},
        })
    return out


def test_target_recovers_a_known_offset() -> None:
    from preflight.catcher_target import mitt_target

    t = mitt_target(_frames({i: 0.4 for i in range(20, 40)}), 10, 60)
    assert t.reason == "measured"
    assert abs(t.lateral - 0.4) < 1e-6
    # Height: mitt at cy 0.45, plate at 0.50, pw 0.06 -> 0.05/0.06.
    # Tolerance is the 5-decimal rounding the dataclass applies on the way out.
    assert abs(t.height - 0.05 / 0.06) < 1e-5


def test_target_is_nan_when_too_few_frames_and_says_why() -> None:
    """
    Below the noise-floor-derived minimum the value must not exist at all.

    MIN_MITT_FRAMES is 5 because the standard error of the per-pitch median at
    n=5 is 0.059 plate widths, about a quarter of the ~0.23 between-pitch signal.
    At n=4 the value would be dominated by which frames happened to detect.
    """
    from preflight.catcher_target import MIN_MITT_FRAMES, mitt_target

    t = mitt_target(_frames({i: 0.4 for i in range(20, 24)}), 10, 60)
    assert t.lateral is None
    assert t.reason == "too_few_mitt_frames"
    assert MIN_MITT_FRAMES == 5


def test_out_of_window_frames_cannot_contribute() -> None:
    """
    A mitt seen after the window closes is not actionable and must be ignored.
    On Gallen's clips out-of-window detection (0.368) exceeds in-window (0.223),
    so letting late frames in would be the difference between a cue and no cue —
    which is exactly why they must not be allowed to substitute.
    """
    from preflight.catcher_target import mitt_target

    fr = _frames({i: 0.4 for i in range(20, 30)}) + _frames({i: -1.0 for i in range(60, 90)})
    t = mitt_target(fr, 10, 40)
    assert t.n_frames == 10
    assert abs(t.lateral - 0.4) < 1e-6


def test_implausible_boxes_are_dropped_and_counted() -> None:
    """
    A mitt box far off the plate is on something else — a shin guard, the
    umpire's gear, a passing fielder. It must be dropped, and the count must be
    reported, because a guard that fires often is evidence about the detector
    rather than a save.
    """
    from preflight.catcher_target import mitt_target

    fr = _frames({i: 0.3 for i in range(20, 30)}) + _frames({i: 5.0 for i in range(30, 35)})
    t = mitt_target(fr, 10, 40)
    assert t.n_dropped_implausible == 5
    assert t.n_frames == 10


def test_missing_plate_yields_no_value_rather_than_a_frame_coordinate() -> None:
    """
    Without a plate in the same frame there is no scale and no origin, and the
    raw mitt coordinate would carry camera pan and park-to-park zoom. That is the
    class of substitution this project keeps retracting, so it must refuse.
    """
    from preflight.catcher_target import mitt_target

    fr = _frames({i: 0.4 for i in range(20, 40)})
    for f in fr:
        f["plate"] = None
    t = mitt_target(fr, 10, 60)
    assert t.lateral is None
    assert t.reason == "too_few_mitt_frames"


def test_standard_error_is_reported_and_gates_the_claim() -> None:
    """
    The measurement carries its own error and the visibility gate uses it. A
    per-pitch value whose SE exceeds the threshold must not clear it.
    """
    from preflight.catcher_target import LATERAL_VISIBILITY_PLATE_WIDTHS, clears_visibility, mitt_target

    tight = mitt_target(_frames({i: 0.4 for i in range(20, 45)}), 10, 60)
    assert tight.lateral_se is not None and tight.lateral_se <= LATERAL_VISIBILITY_PLATE_WIDTHS
    assert clears_visibility(tight)

    rng = np.random.default_rng(0)
    noisy = mitt_target(_frames({i: float(rng.normal(0.4, 0.8)) for i in range(20, 26)}), 10, 60)
    assert noisy.reason == "measured"
    assert not clears_visibility(noisy)


def test_drift_separates_a_walked_target_from_a_jittery_one() -> None:
    """
    ``lateral_late_minus_early`` is signed and threshold-free, so a target the
    catcher moves in one direction is distinguishable from one that wobbles
    around a fixed spot. Both show drift; only one shows displacement.
    """
    from preflight.catcher_target import mitt_target

    walked = mitt_target(_frames({i: -0.5 + 0.05 * (i - 20) for i in range(20, 40)}), 10, 60)
    rng = np.random.default_rng(1)
    wobble = mitt_target(_frames({i: float(rng.normal(0.0, 0.25)) for i in range(20, 40)}), 10, 60)
    assert walked.lateral_late_minus_early > 0.5
    assert abs(wobble.lateral_late_minus_early) < 0.5
    assert wobble.lateral_drift > 0.2


# --- names and provenance -----------------------------------------------------

def test_new_cues_do_not_reuse_retracted_catcher_names() -> None:
    """
    The retracted ``catcher_*`` names stay retracted. A correctly-measured cue
    gets a new name; un-retracting one would erase the record of the claim that
    was withdrawn.
    """
    from preflight.catcher_target import CMITT_CUES
    from preflight.provenance import RETRACTED_CUES

    for cue in CMITT_CUES:
        assert cue not in RETRACTED_CUES, cue
        assert not cue.startswith("catcher_"), cue


def test_retracted_catcher_family_is_still_retracted() -> None:
    """This work must not have disturbed the existing retractions."""
    from preflight.provenance import RETRACTED_CUES

    for cue in ("catcher_glove_x_mean", "catcher_glove_y_mean", "catcher_stance_mean",
                "catcher_hip_y_mean", "catcher_glove_speed_mean", "catcher_glove_speed_p90"):
        assert cue in RETRACTED_CUES, cue


def test_new_cues_are_not_wired_into_discovery_yet() -> None:
    """
    A name in ``spot_diff.CUES`` can reach the board. These cues have a known
    noise floor and no validation, and their coverage collapsed from 0.645 to 0.00
    between two arms at different parks. They must not be reachable until the
    recency discovery/holdout protocol has been run on them.
    """
    from preflight.catcher_target import CMITT_CUES, CMITT_STATUS
    from preflight.spot_diff import CUES

    for cue in CMITT_CUES:
        assert cue not in CUES, f"{cue} is reachable by discovery without validation"
        assert CMITT_STATUS[cue] == "measured_unvalidated", cue


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
