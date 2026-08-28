"""
Validity checks for the set-position and coming-set primitives.

Why these look the way they do
------------------------------
Three features shipped recently while measuring something other than their own
name: ``pitchcom_tap_count`` was glove-motion variance, the catcher features
were tracking the pitcher's body, and a rebuilt tap detector passed a
phase-shuffle test while actually responding to arm-motion smoothness. The
lesson is that passing a check is not the same as measuring the named thing.

So each check here plants a KNOWN quantity in a synthetic track and asserts the
primitive recovers that quantity and not a correlate of it. Where a primitive
could plausibly be reading an artifact instead — camera zoom, a tracking
dropout, an inverted pose, which way the pitcher faces — there is a check that
changes only the artifact and asserts the primitive does not move.

The reliability harness at the bottom is the second half of the standard: a
primitive also has to clear the landmark noise floor for the body part it uses.
It re-runs the real cached tracks with additive noise at the measured per-frame
jitter and reports between-pitch spread against the noise it induces.

Run directly: ``python -m preflight.test_primitives``
"""
from __future__ import annotations

import glob
import math
import os

import numpy as np
import pandas as pd

from preflight import primitives as P
from preflight.window import PRESET_LOOKBACK

FPS = 30
# Per-frame landmark jitter measured over the set interval, where the pitcher is
# still by construction, median over the trunk landmark groups.
# See landmark_noise_probe.py.
MEASURED_JITTER = 0.10
# Frame band the synthetic pelvis move occupies. Chosen to sit inside the
# detected pre-set segment for the default frame layout regardless of exactly
# where the set detector lands, so a planted amplitude is fully observable.
SWAY_START, SWAY_END = 40, 56

# --- retention rule, fixed before looking at any result ----------------------
# A primitive is kept only if both hold. Nothing downstream is tuned; this rule
# decides which features exist at all, and it is applied mechanically so the
# choice is not a judgement about which cues we would like to work.
#
#   1. Recoverable signal. between_sd^2 = signal^2 + noise^2, so the signal a
#      group contrast can actually see is sqrt(between^2 - induced^2). For a
#      length feature that has to clear the 0.05-torso practical-visibility
#      floor used everywhere else in the project.
#   2. Coverage. The feature must be defined on most usable pitches. A cue
#      present on a third of them is not a cue, it is a subsample, and it
#      spends an FDR slot for almost no power.
VISIBILITY_FLOOR = 0.05
MIN_COVERAGE = 0.60
# Features measured in degrees; the torso-length floor does not apply to them,
# so they are held to the ratio test alone.
ANGLE_PRIMITIVES = {
    "posture_lean_at_set",
    "shoulder_tilt_at_set",
    "glove_angle_at_set",
    "lean_change_set_to_lift",
}

LANDMARKS = (
    "nose", "lsho", "rsho", "lelb", "relb", "lwri", "rwri",
    "lpnk", "rpnk", "lidx", "ridx", "lhip", "rhip",
    "lkne", "rkne", "lank", "rank",
)


def synth_track(
    n: int = 150,
    set_frame: int = 70,
    lift_frame: int = 110,
    torso: float = 0.12,
    *,
    sway: tuple[float, float] = (0.0, 0.0),
    sway_shape: str = "monotone",
    stance: float = 0.30,
    trunk_lean_deg: float = 0.0,
    forearm_elev_deg: float = 30.0,
    noise: float = 0.0,
    seed: int = 0,
    invert_trunk: bool = False,
    zoom: float = 1.0,
) -> pd.DataFrame:
    """
    A synthetic pitcher whose posture is known exactly.

    Geometry is built in torso units and then scaled, so a planted quantity such
    as ``stance`` is directly comparable to the primitive that recovers it. The
    frame layout satisfies ``actionable_window``: a pre-set approach, a quiet
    set long enough to be detected, a knee lift, then a fast delivery burst.

    ``sway`` is the net pelvis displacement (dx, dy) in torso lengths over the
    pre-set segment, applied with ``sway_shape``:
      ``monotone``    one smooth settle into the set   -> directness near 1
      ``out_and_back`` a rock away and back to the set -> directness near 0
    """
    rng = np.random.default_rng(seed)
    T = torso * zoom
    rows = []
    for f in range(n):
        # --- pelvis path over the coming-set approach ----------------------
        # The move is placed in a fixed frame band that sits comfortably inside
        # the pre-set segment wherever the set detector happens to land, so the
        # planted amplitude is fully observable and the assertions can compare
        # against the planted number directly.
        if f <= SWAY_START:
            u = 0.0
        elif f >= SWAY_END:
            u = 1.0
        else:
            u = (f - SWAY_START) / (SWAY_END - SWAY_START)
        if sway_shape == "monotone":
            # Held away from the plate, then one smooth settle into the set.
            k = 1.0 - u
        else:
            # Starts and ends at the set anchor, bulging away in between.
            k = math.sin(math.pi * u)
        ox, oy = sway[0] * k, sway[1] * k

        hipx = 0.50 + ox * T
        hipy = 0.60 - oy * T

        # --- trunk ----------------------------------------------------------
        th = math.radians(trunk_lean_deg)
        sx = hipx + math.sin(th) * T
        sy = hipy - math.cos(th) * T
        if invert_trunk:
            sy = hipy + math.cos(th) * T

        # --- knee lift ------------------------------------------------------
        if f < set_frame:
            rise = 0.0
        elif f <= lift_frame:
            rise = 0.55 * (f - set_frame) / max(1, lift_frame - set_frame)
        else:
            rise = 0.55 * max(0.0, 1 - (f - lift_frame) / 12)

        # --- delivery burst so the window can be anchored -------------------
        burst = max(0, f - (lift_frame + P.LIFT_HALF_WIN + 2))
        push = min(0.30, 0.06 * burst)

        # --- forearms and glove --------------------------------------------
        # The hands move while he is coming set and go still at the set. Without
        # this the whole synthetic clip reads as quiet and the set detector
        # anchors on frame 0, which puts the pre-set segment somewhere the
        # planted sway does not exist. Amplitude is chosen to sit above
        # window.QUIET_SPEED and below window.DELIVERY_SPEED, so it reads as
        # approach motion and not as the delivery.
        fidget = 0.20 * T * math.sin(f * 1.5) if f < set_frame else 0.0
        fe = math.radians(forearm_elev_deg)
        gx = hipx + 0.05 * T + fidget
        gy = hipy - 0.55 * T
        elbx = gx - math.cos(fe) * 0.45 * T
        elby = gy + math.sin(fe) * 0.45 * T

        row = {"frame": f, "t_sec": f / FPS, "camera_id": "CF"}
        pts = {
            "nose": (sx, sy - 0.35 * T),
            "lsho": (sx - 0.30 * T, sy),
            "rsho": (sx + 0.30 * T, sy),
            "lelb": (elbx, elby),
            "relb": (elbx + 0.04 * T, elby),
            "lwri": (gx - 0.02 * T + push, gy),
            "rwri": (gx + 0.02 * T - push, gy),
            "lpnk": (gx - 0.05 * T, gy + 0.03 * T),
            "rpnk": (gx + 0.05 * T, gy + 0.03 * T),
            "lidx": (gx - 0.04 * T, gy - 0.02 * T),
            "ridx": (gx + 0.04 * T, gy - 0.02 * T),
            "lhip": (hipx - 0.18 * T, hipy),
            "rhip": (hipx + 0.18 * T, hipy),
            "lkne": (hipx - 0.16 * T, hipy + (0.90 - rise) * T),
            "rkne": (hipx + 0.16 * T, hipy + 0.90 * T),
            "lank": (hipx - stance / 2 * T, hipy + 1.75 * T),
            "rank": (hipx + stance / 2 * T, hipy + 1.75 * T),
        }
        for name, (x, y) in pts.items():
            jx = rng.normal(0, noise * T) if noise else 0.0
            jy = rng.normal(0, noise * T) if noise else 0.0
            row[f"{name}_x"] = x + jx
            row[f"{name}_y"] = y + jy
            row[f"{name}_v"] = 0.95
        rows.append(row)
    return pd.DataFrame(rows)


def _prim(**kw) -> dict:
    df = synth_track(**kw)
    got = P.pitch_primitives(df, "synth")
    assert got is not None, "synthetic track produced no usable window"
    return got


# --- does it recover the planted quantity? ------------------------------------

def test_stance_width_recovers_planted_value() -> None:
    """stance_width_at_set must return the ankle separation that was planted."""
    for planted in (0.20, 0.45, 0.80):
        got = _prim(stance=planted)["stance_width_at_set"]
        assert abs(got - planted) < 0.02, (planted, got)


def test_lean_recovers_planted_angle() -> None:
    """posture_lean_at_set must return the trunk angle that was planted."""
    for planted in (-12.0, 0.0, 8.0):
        got = _prim(trunk_lean_deg=planted)["posture_lean_at_set"]
        assert abs(got - planted) < 1.0, (planted, got)


def test_glove_angle_recovers_planted_elevation() -> None:
    for planted in (10.0, 30.0, 55.0):
        got = _prim(forearm_elev_deg=planted)["glove_angle_at_set"]
        assert abs(got - planted) < 3.0, (planted, got)


def test_sway_amplitude_recovers_planted_displacement() -> None:
    """A planted lateral pelvis move must come back as that amplitude."""
    for planted in (0.10, 0.30, 0.60):
        got = _prim(sway=(planted, 0.0))
        assert abs(got["sway_amplitude"] - planted) < 0.06, (planted, got["sway_amplitude"])
        assert abs(abs(got["sway_dx"]) - planted) < 0.06, (planted, got["sway_dx"])


def test_sway_separates_a_settle_from_a_rock() -> None:
    """
    The trajectory feature has to earn its keep: a single settle into the set
    and a rock out-and-back have the SAME amplitude, and only the path shape
    tells them apart. If directness cannot separate them, no single-frame
    measurement could and the feature is not worth its FDR slot.
    """
    settle = _prim(sway=(0.35, 0.0), sway_shape="monotone")
    rock = _prim(sway=(0.35, 0.0), sway_shape="out_and_back")
    assert settle["sway_directness"] > 0.8, settle["sway_directness"]
    assert rock["sway_directness"] < 0.3, rock["sway_directness"]
    # ...and it is genuinely the shape, not the size: amplitudes agree.
    assert abs(settle["sway_amplitude"] - rock["sway_amplitude"]) < 0.12


# --- is it responding to an artifact instead? ---------------------------------

def test_zoom_does_not_move_normalised_primitives() -> None:
    """
    Camera zoom changes every raw coordinate and must change nothing here.
    This is what torso normalisation is for, and the check that it works.
    """
    a = _prim(zoom=1.0, stance=0.4, trunk_lean_deg=6.0, sway=(0.3, 0.0))
    b = _prim(zoom=1.8, stance=0.4, trunk_lean_deg=6.0, sway=(0.3, 0.0))
    for k in (
        "stance_width_at_set", "knee_flex_at_set", "posture_lean_at_set",
        "torso_foreshorten_at_set", "glove_angle_at_set",
        "forearm_exposure_at_set", "sway_amplitude", "sway_directness",
    ):
        assert abs(a[k] - b[k]) < 0.05 * max(1.0, abs(a[k])) + 0.05, (k, a[k], b[k])


def test_folded_angles_are_handedness_invariant() -> None:
    """
    Mirroring the pitcher left-to-right is the difference between a lefty and a
    righty and must not change a folded angle. Before the fold this flipped the
    raw arctangent by 180 degrees, which put a bimodal artifact into the group
    mean of any mixed-handedness sample.
    """
    df = synth_track(forearm_elev_deg=35.0)
    mir = df.copy()
    for c in [c for c in df.columns if c.endswith("_x")]:
        mir[c] = 1.0 - df[c]
    a = P.pitch_primitives(df, "a")
    b = P.pitch_primitives(mir, "b")
    assert a is not None and b is not None
    for k in ("glove_angle_at_set", "shoulder_tilt_at_set"):
        if np.isfinite(a[k]) or np.isfinite(b[k]):
            assert abs(a[k] - b[k]) < 2.0, (k, a[k], b[k])


def test_inverted_pose_is_nan_not_a_posture() -> None:
    """
    An upside-down trunk is a tracking failure. It must not enter the sample as
    a large lean, which is what the raw arctangent did (5th percentile -159
    degrees on real tracks).
    """
    got = _prim(invert_trunk=True)
    assert not np.isfinite(got["posture_lean_at_set"]), got["posture_lean_at_set"]
    assert not np.isfinite(got["lean_change_set_to_lift"])


def test_dropout_is_nan_not_motion() -> None:
    """
    A pelvis that stops being tracked mid-approach and reappears must read as
    missing, never as a sway. This is the failure mode that made the original
    glove path-length feature report impossible values.
    """
    df = synth_track(sway=(0.0, 0.0))
    pre_start = 70 - PRESET_LOOKBACK
    gap = slice(pre_start + 2, 70 - 4)
    for c in ("lhip_x", "lhip_y", "rhip_x", "rhip_y"):
        df.loc[gap, c] = np.nan
    got = P.pitch_primitives(df, "gap")
    assert got is not None
    assert not np.isfinite(got["sway_amplitude"]), got["sway_amplitude"]


def test_short_projected_segment_is_nan_not_an_angle() -> None:
    """
    A segment pointing at the camera projects to nothing, and the arctangent of
    two noise terms is a uniform angle, not a posture. Collapsing the shoulder
    line must produce NaN rather than a confident number.
    """
    df = synth_track()
    mid = (df["lsho_x"] + df["rsho_x"]) / 2
    df["lsho_x"] = mid
    df["rsho_x"] = mid
    got = P.pitch_primitives(df, "flat")
    assert got is not None
    assert not np.isfinite(got["shoulder_tilt_at_set"]), got["shoulder_tilt_at_set"]


def test_no_preset_footage_yields_nan_sway_not_zero() -> None:
    """
    A clip that does not carry the approach has unknown sway, not absent sway.
    Zero would enter a group mean as a real measurement.
    """
    df = synth_track(n=100, set_frame=12, lift_frame=45)
    got = P.pitch_primitives(df, "short")
    if got is not None:
        for k in P.PRESET_PRIMITIVES:
            assert not np.isfinite(got[k]) or got[k] != 0.0


def test_subject_change_across_approach_is_rejected() -> None:
    """
    If the tracked body changes size part-way through the approach, the tracker
    swapped subject or the broadcast changed zoom. Either way the pelvis path is
    not a sway. This is the guard the catcher features did not have.
    """
    df = synth_track(sway=(0.0, 0.0))
    pre_start = 70 - PRESET_LOOKBACK
    grow = slice(pre_start, pre_start + 18)
    for c in [c for c in df.columns if c.endswith(("_x", "_y"))]:
        df.loc[grow, c] = 0.5 + (df.loc[grow, c] - 0.5) * 2.2
    got = P.pitch_primitives(df, "swap")
    assert got is not None
    assert not np.isfinite(got["sway_amplitude"]), got["sway_amplitude"]


def test_all_new_primitives_are_present_and_finite_on_clean_input() -> None:
    """Guards must not have removed the features on a clean, well-posed pitch."""
    got = _prim(stance=0.4, trunk_lean_deg=5.0, sway=(0.25, 0.05), forearm_elev_deg=35.0)
    missing = [k for k in P.PRIMITIVES if k not in got]
    assert not missing, missing
    nan = [k for k in P.PRIMITIVES[15:] if not np.isfinite(got[k])]
    # shoulder_tilt is legitimately allowed to drop out: the synthetic shoulder
    # line is short. Everything else must survive clean input.
    assert set(nan) <= {"shoulder_tilt_at_set"}, nan


# --- reliability against the measured landmark noise floor --------------------

def test_status_table_covers_every_primitive() -> None:
    """
    EVERY primitive must carry an explicit retention status, not just the ones
    added most recently. A feature that appears with no status is exactly how an
    unvalidated cue gets published.

    This assertion used to read ``set(P.PRIMITIVES[15:])``, covering only the
    primitives after a positional cutoff. That was wrong twice over: it exempted
    the original fifteen from the bar their successors had to clear — and those
    fifteen are where all four of the known measurement failures were found — and
    it silently changed meaning the moment a primitive was inserted before the
    cutoff. Position in a list is not a validation record.
    """
    assert set(P.PRIMITIVE_STATUS) == set(P.PRIMITIVES), set(P.PRIMITIVE_STATUS) ^ set(
        P.PRIMITIVES
    )
    assert set(P.PRIMITIVE_STATUS.values()) <= {
        "validated",
        "under_covered",
        "excluded_permanently",
        "resolution_limited",
        "underpowered",
        "retracted",
    }


def test_only_validated_primitives_reach_discovery() -> None:
    """
    Discovery may only see primitives whose status is ``validated``.

    Adding a feature to spot_diff.CUES spends FDR budget for the whole family, so
    a noisy, thinly-covered, or retracted cue does not merely fail on its own — it
    raises the bar every other cue has to clear. This is the gate that keeps that
    from happening by accident.
    """
    from preflight import spot_diff as S

    for cue in S.CUES:
        status = P.PRIMITIVE_STATUS.get(cue)
        if status is None:
            continue  # legacy window feature, audited separately
        assert status == "validated", f"{cue} is wired into discovery at status {status}"


def test_delivery_type_is_emitted_for_stratification() -> None:
    """
    spot_diff refuses a frame carrying more than one delivery, so the label has
    to travel with the features rather than be inferred later.
    """
    got = _prim()
    assert got["delivery_type"] in {"stretch", "windup", "unknown"}


def noise_reliability(run: str, limit: int = 200) -> list[dict]:
    """
    Between-pitch spread against the spread that landmark noise alone induces.

    Real cached tracks are recomputed with additive Gaussian landmark noise at
    the measured per-frame jitter. The ratio is the honest read on whether a
    primitive carries information beyond the tracker's own error; a ratio near 1
    means the feature is noise.
    """
    files = sorted(glob.glob(os.path.join(run, "lift_tracks", "*.csv")))[:limit]
    base, pert = [], []
    rng = np.random.default_rng(7)
    for path in files:
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        r0 = P.pitch_primitives(df, "b")
        if r0 is None:
            continue
        nz = df.copy()
        # Noise in torso units needs the pitch's own torso length in image units.
        t = float(r0["torso_scale"])
        for lm in LANDMARKS:
            for ax in ("x", "y"):
                c = f"{lm}_{ax}"
                if c in nz.columns:
                    nz[c] = pd.to_numeric(nz[c], errors="coerce") + rng.normal(
                        0, MEASURED_JITTER * t, len(nz)
                    )
        r1 = P.pitch_primitives(nz, "p")
        if r1 is None:
            continue
        base.append(r0)
        pert.append(r1)

    b, q = pd.DataFrame(base), pd.DataFrame(pert)
    out = []
    for c in P.PRIMITIVES[15:]:
        d = (b[c] - q[c]).dropna()
        between = float(b[c].std())
        induced = float(d.std() / np.sqrt(2)) if len(d) > 2 else float("nan")
        ratio = between / induced if induced and np.isfinite(induced) and induced > 1e-12 else float("nan")
        signal = (
            float(np.sqrt(max(0.0, between**2 - induced**2))) if np.isfinite(induced) else float("nan")
        )
        coverage = float(b[c].notna().mean()) if len(b) else float("nan")
        keeps_signal = (
            np.isfinite(ratio) and ratio > 1.0
            if c in ANGLE_PRIMITIVES
            else np.isfinite(signal) and signal > VISIBILITY_FLOOR
        )
        out.append(
            {
                "primitive": c,
                "n": len(d),
                "coverage": coverage,
                "between_sd": between,
                "induced_sd": induced,
                "ratio": ratio,
                "signal_sd": signal,
                "keep": bool(keeps_signal and coverage >= MIN_COVERAGE),
            }
        )
    return out


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")

    run = os.environ.get("PRIM_RUN", "../runs/drew_thorpe_rich_poc")
    if os.path.isdir(os.path.join(run, "lift_tracks")):
        print(
            f"\nreliability on {run} "
            f"(noise at measured jitter {MEASURED_JITTER} torso/frame):"
        )
        hdr = ("primitive", "n", "cover", "between", "induced", "ratio", "signal", "keep")
        print(f"  {hdr[0]:32s} {hdr[1]:>4s} {hdr[2]:>6s} {hdr[3]:>8s} {hdr[4]:>8s} {hdr[5]:>6s} {hdr[6]:>8s}  {hdr[7]}")
        for r in noise_reliability(run):
            print(
                f"  {r['primitive']:32s} {r['n']:4d} {r['coverage']:6.2f} "
                f"{r['between_sd']:8.4f} {r['induced_sd']:8.4f} {r['ratio']:6.2f} "
                f"{r['signal_sd']:8.4f}  {'keep' if r['keep'] else 'DROP'}"
            )
