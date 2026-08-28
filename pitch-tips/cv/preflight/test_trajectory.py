"""
Do the trajectory features measure the movement they claim?

Same bar the point primitives faced: plant a known movement in a synthetic track
and check the feature recovers it; confirm a zoom change cannot become a speed;
confirm a tracking dropout returns NaN rather than a fast, tortuous path; and
confirm the shape features separate a settle from a rock at equal amplitude,
which is the one thing amplitude alone cannot do.

The dropout tests matter more here than they did for the point features. A point
cue needs one good frame near its anchor. A path integrates every frame it
covers, so a landmark that vanishes and reappears elsewhere manufactures a large,
fast, wandering movement out of nothing.

The synthetic pitcher is the one already used for the point primitives, so the
window, set and lift are detected exactly as they are there; the scripted glove
path and knee profile are injected on top of it.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from preflight import trajectory as T
from preflight.test_primitives import synth_track

SET_F, LIFT_F = 70, 110
TORSO = 0.12


def with_path(
    df: pd.DataFrame,
    path=None,
    knee=None,
    dropout: tuple[int, int] | None = None,
    zoom: float = 1.0,
    pin_glove: bool = False,
    hip_path=None,
) -> pd.DataFrame:
    """Inject a scripted glove path and/or knee profile into a synthetic track.

    Only frames up to peak lift are touched, so the delivery burst that lets the
    window module find its boundaries is left intact.

    ``pin_glove`` replaces the glove position outright instead of adding to it.
    The base fixture deliberately fidgets the hands before the set so the set
    detector has motion to anchor on, and the detected set can land earlier than
    the nominal one — so "add a zero offset" does not produce a still glove over
    the measured segment, and a test that needs one has to pin it.
    """
    d = df.copy()
    Tz = TORSO * zoom
    for f in range(len(d)):
        if f > LIFT_F:
            continue
        if pin_glove:
            for c, v in (("lwri_x", 0.50 - 0.02 * Tz), ("rwri_x", 0.50 + 0.02 * Tz)):
                d.at[f, c] = v
            for c in ("lwri_y", "rwri_y"):
                d.at[f, c] = 0.60 - 0.55 * Tz
        if path is not None:
            dx, dy = path(f)
            for c, off in (("lwri_x", dx), ("rwri_x", dx)):
                d.at[f, c] = d.at[f, c] + off * Tz
            for c in ("lwri_y", "rwri_y"):
                d.at[f, c] = d.at[f, c] + dy * Tz
        if hip_path is not None:
            off = hip_path(f) * Tz
            for c in ("lhip_x", "rhip_x"):
                d.at[f, c] = d.at[f, c] + off
        if knee is not None:
            hipy = d.at[f, "lhip_y"]
            d.at[f, "lkne_y"] = hipy + (0.90 - knee(f)) * Tz
    if dropout:
        for f in range(*dropout):
            if f < len(d):
                for c in ("lwri_x", "lwri_y", "rwri_x", "rwri_y"):
                    d.at[f, c] = np.nan
    return d


def feat(path=None, knee=None, dropout=None, zoom=1.0, pin_glove=False,
         hip_path=None, **kw) -> dict:
    base = synth_track(torso=TORSO, set_frame=SET_F, lift_frame=LIFT_F, zoom=zoom, **kw)
    out = T.pitch_trajectory(
        with_path(base, path=path, knee=knee, dropout=dropout, zoom=zoom,
                  pin_glove=pin_glove, hip_path=hip_path),
        "synthetic",
    )
    assert out is not None, "synthetic track should yield a usable window"
    return out


def _ramp(amp: float, over: float = 25.0):
    """A single smooth settle of `amp` torso lengths, downward."""
    def p(f):
        if f < SET_F:
            return 0.0, 0.0
        return 0.0, amp * min(1.0, (f - SET_F) / over)
    return p


# ---------------------------------------------------------------------------
# Tempo
# ---------------------------------------------------------------------------

def test_set_to_lift_recovers_planted_tempo():
    """A lift further from the set must read as a longer tempo, by that amount."""
    slow = T.pitch_trajectory(
        synth_track(torso=TORSO, set_frame=SET_F, lift_frame=LIFT_F), "s"
    )["set_to_lift_frames"]
    quick = T.pitch_trajectory(
        synth_track(torso=TORSO, set_frame=SET_F, lift_frame=SET_F + 20), "q"
    )["set_to_lift_frames"]
    assert quick < slow, f"quicker delivery should read shorter: {quick} vs {slow}"
    assert slow - quick == pytest.approx(20, abs=6), (
        f"the recovered tempo difference should match the planted 20 frames: "
        f"{slow - quick}"
    )


def test_hold_at_top_separates_a_held_lift_from_a_tap():
    """A knee that reaches its peak early and stays there scores high."""
    def held(f):
        if f < SET_F:
            return 0.0
        return 0.55 * min(1.0, (f - SET_F) / 12.0)

    def tap(f):
        if f < SET_F:
            return 0.0
        return 0.55 * min(1.0, ((f - SET_F) / (LIFT_F - SET_F)) ** 3)

    h = feat(knee=held)["hold_at_top_frac"]
    t = feat(knee=tap)["hold_at_top_frac"]
    assert h > t, f"held lift {h} should exceed tap {t}"


# ---------------------------------------------------------------------------
# Shape: the thing amplitude cannot do
# ---------------------------------------------------------------------------

def test_shape_separates_a_settle_from_a_rock_at_equal_amplitude():
    """
    The central claim of the shape features.

    Both paths end at the same place having reached the same peak excursion. A
    settle moves once and stops; a rock oscillates on the way. Amplitude cannot
    tell them apart, so tortuosity and reversal count must.
    """
    A = 0.5

    def rock(f):
        if f < SET_F:
            return 0.0, 0.0
        u = min(1.0, (f - SET_F) / 25.0)
        return 0.0, A * u + A * 0.8 * math.sin((f - SET_F) * 2 * math.pi / 12.0)

    s, r = feat(path=_ramp(A)), feat(path=rock)
    assert r["glove_vertical_reversals"] > s["glove_vertical_reversals"], (
        f"rock {r['glove_vertical_reversals']} should exceed settle "
        f"{s['glove_vertical_reversals']}"
    )
    assert r["glove_tortuosity"] > s["glove_tortuosity"], (
        f"rock {r['glove_tortuosity']} should wander more than settle "
        f"{s['glove_tortuosity']}"
    )
    assert s["glove_tortuosity"] == pytest.approx(1.0, abs=0.4), (
        f"a single direct move should sit near tortuosity 1, got {s['glove_tortuosity']}"
    )


def test_speed_cv_separates_smooth_from_stop_start():
    """Equal total travel, delivered smoothly versus in discrete steps."""
    A = 0.6

    def pulsed(f):
        if f < SET_F:
            return 0.0, 0.0
        step = ((f - SET_F) // 10) * (A / 4.0)
        return 0.0, min(A, step)

    sm = feat(path=_ramp(A, over=40.0))["glove_speed_cv"]
    pu = feat(path=pulsed)["glove_speed_cv"]
    assert pu > sm, f"stop-start {pu} should be more variable than smooth {sm}"


# ---------------------------------------------------------------------------
# Invariance and refusal
# ---------------------------------------------------------------------------

def test_zoom_does_not_become_a_speed():
    """Torso normalisation: a camera zoom must not read as faster movement."""
    a = feat(path=_ramp(0.5), zoom=1.0)
    b = feat(path=_ramp(0.5), zoom=1.4)
    for k in ("glove_speed_mean", "glove_tortuosity", "glove_speed_cv"):
        assert a[k] == pytest.approx(b[k], rel=0.30), (
            f"{k} moved with zoom: {a[k]} vs {b[k]}"
        )


def test_dropout_is_nan_not_a_fast_wandering_path():
    """
    The failure mode trajectory features are most exposed to.

    The glove vanishes across most of the window. Bridging that gap would
    manufacture a large, fast, tortuous movement, so every path feature must
    decline to answer.
    """
    out = feat(path=_ramp(0.5), dropout=(SET_F + 4, LIFT_F))
    for k in ("glove_speed_mean", "glove_speed_cv", "glove_tortuosity",
              "glove_vertical_reversals", "glove_peak_speed_timing"):
        assert not np.isfinite(out[k]), f"{k} answered {out[k]} across a dropout"


def test_a_still_glove_yields_no_tortuosity_rather_than_a_huge_one():
    """
    Dividing by a near-zero net displacement is the trap in a shape ratio.

    A glove that barely moves has a net displacement inside the jitter floor, so
    path-over-net would return an arbitrarily large number describing noise.
    """
    out = feat(pin_glove=True)
    assert not np.isfinite(out["glove_tortuosity"]), (
        f"a still glove reported tortuosity {out['glove_tortuosity']}"
    )


def test_hip_coupling_is_nan_when_the_hips_do_not_move():
    """
    Correlation against a constant is undefined, and must read as such.

    A still pelvis has no horizontal variation to correlate against, so the
    coupling feature has to return NaN rather than an arbitrary value — the
    synthetic pitcher stands still by default, which makes this the common case
    in the fixture rather than an edge case.
    """
    out = feat(path=_ramp(0.5))
    assert not np.isfinite(out["hip_glove_x_coupling"])


def test_every_feature_is_present_and_finite_on_clean_moving_input():
    def path(f):
        if f < SET_F:
            return 0.0, 0.0
        u = min(1.0, (f - SET_F) / 30.0)
        return 0.15 * u, 0.5 * u + 0.1 * math.sin((f - SET_F) / 6.0)

    # Hip motion is planted inside the measured set-to-lift segment, since the
    # coupling feature needs the pelvis to move there for a correlation to exist.
    # The fixture's own `sway` happens before the set and so cannot serve.
    out = feat(path=path, hip_path=lambda f: 0.30 * min(1.0, max(0.0, (f - SET_F) / 30.0)))
    missing = [k for k in T.TRAJECTORY_FEATURES if k not in out]
    assert not missing, f"features absent from output: {missing}"
    nan = [k for k in T.TRAJECTORY_FEATURES if not np.isfinite(out[k])]
    assert not nan, f"features NaN on clean moving input: {nan}"


def test_every_feature_has_a_stated_meaning():
    """A feature nobody can describe in a sentence cannot be audited."""
    assert set(T.FEATURE_MEANING) == set(T.TRAJECTORY_FEATURES)
    for k, v in T.FEATURE_MEANING.items():
        assert len(v) > 40, f"{k} lacks a real description"


# ---------------------------------------------------------------------------
# The dispersion artifact: a regression guard, not a feature test
# ---------------------------------------------------------------------------

def test_dispersion_of_a_small_group_is_biased_low():
    """
    Why the consistency family's replication rate was not evidence.

    An absolute deviation is measured from a median estimated on the same group,
    so a group of few pitches sits closer to its own median than a group of many
    does — for purely arithmetic reasons, with no difference in the underlying
    spread. Both samples here are drawn from the SAME distribution, so any gap is
    bias.

    This is what produced a 72% sign-hold rate on real data that shuffled labels
    reproduced at 48-81%: the bias points the same way in every game, so it
    replicates across a game boundary exactly as a real cue would.

    Anything reading the dispersion family must therefore compare against
    ``permute_labels``, never against a coin.
    """
    from preflight.trajectory_discover import to_dispersion

    rng = np.random.default_rng(0)
    rows = []
    for game in range(12):
        # Identical spread for both types; only the group SIZE differs.
        for kind, n in (("RARE", 5), ("COMMON", 40)):
            for v in rng.normal(0.0, 1.0, n):
                rows.append({"game_pk": game, "pitch_type": kind,
                             "set_to_lift_frames": v})
    df = pd.DataFrame(rows)
    d = to_dispersion(df, ["set_to_lift_frames"])
    rare = d[d.pitch_type == "RARE"]["set_to_lift_frames"].mean()
    common = d[d.pitch_type == "COMMON"]["set_to_lift_frames"].mean()
    assert rare < common, (
        f"expected the small group to look spuriously tighter: {rare} vs {common}"
    )
