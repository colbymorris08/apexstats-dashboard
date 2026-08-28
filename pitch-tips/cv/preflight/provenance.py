"""
Provenance: does a published player/tip trace to a real completed run?

Every number on the board must be re-derivable from a run directory on disk.
Before this module, `merge_demo` only *added* arms it found under runs/ and left
anything already present in demo.json in place, so hand-authored seed cards
(Cole, Rodón, Yamamoto, Glasnow) stayed published forever with invented tips.
Publishing a tip for a pitcher who was never tracked reads as fabrication, so
the publish path now starts from evidence and refuses anything it cannot back.

A tip is backed only if all of the following hold:
  * its run directory exists and holds report.json
  * the tip list is trustworthy, which means EITHER report_actionable.json exists
    (an audit re-derivation of an arm tracked before the window was fixed) OR the
    report was produced under the corrected window with a real game-level holdout
  * the arm passes sanity_gate.check_arm
  * the tip itself carries train/test game holdout evidence
  * the tip's confidence clears the arm's tip floor

On the second condition: report_actionable.json was introduced when report.json
could not be trusted, because tips were fitted in-sample over a fixed 55% slice
of the clip. Arms tracked by the current pipeline write a report.json that is
already the corrected artefact, so requiring an audit file would silently zero
out every legitimately validated tip. The distinction that matters is not which
filename the tips came from but whether the window and the holdout are sound, and
the sanity gate already establishes both — it fails an arm whose features carry
legacy window metadata and fails any arm publishing tips without holdout
evidence. Hand-authored cards remain blocked because they have no run directory.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from preflight import snapshot
from preflight.sanity_gate import _tip_is_validated, check_arm

DEFAULT_TIP_FLOOR = 0.75

# --- retracted cues -----------------------------------------------------------
# Cues whose MEASUREMENT is known to be invalid, independent of how strong any
# individual result looked. A retracted cue cannot be rescued by a holdout or a
# confidence floor: if the number does not measure the thing it is named after,
# a validated result on it is a validated result about nothing.
#
# The pitchcom_* family is retracted because the underlying detector reads local
# maxima in GLOVE-CENTROID displacement, which cannot resolve a thumb press on a
# forearm device. Three measurements establish it is not detecting taps:
#   * it returns MORE detections on phase-shuffled speed, which has no temporal
#     structure left at all, than on real footage;
#   * 17-43% of its detections sit on a tracking-dropout re-acquisition, where
#     the reported speed is a multi-frame gap rather than motion;
#   * its detection rate is flat from 5 to 120 frames before the set, so it
#     fires as often in broadcast idle footage as during sign-taking.
# See cv/preflight/pitchcom_validity_probe.py and preset_extent_probe.py.
#
# Entries are removed from here only when a rebuilt detector passes
# test_tap_detector.py, which is designed to be failable.
# The cheek_motion_* family is retracted because the pitcher's face is not in
# the picture at a usable rate and the column is silently filled with something
# else. Three measurements, from cv/preflight/face_pixel_audit.py:
#   * the MediaPipe Face Landmarker returns a face on only 8.3% of in-window
#     frames (24 of 288, 60 clips, 1280x720 Savant CF);
#   * of those, the face sits a median 2.24 shoulder widths from the pitcher's
#     own pose nose and has an inter-eye distance of 101.8 px against a pitcher
#     head scale of 31.4 px — they are the hitter and the crowd, not the
#     pitcher. Only 3 of 288 frames (1.04%) put a face on the pitcher;
#   * the pitcher's mouth is ~11 px wide at this distance, so the cue the
#     scouting note describes ("and his mouth") is under the resolution of the
#     footage regardless of which model is pointed at it.
# track_pitcher.py then substituted the POSE NOSE whenever the face model came
# back empty, so at a 1.04% hit rate the column is head-position jitter carrying
# a facial-motion label. The fallback is now removed (cheek_* emits NaN with no
# face), but the historical columns cannot be trusted and any result resting on
# them is a result about head jitter.
#
# The catcher_* family is retracted because the column carried the PITCHER's
# body. Subject selection ended in `if clm is None: clm = by_hip[0]`, which fired
# whenever MediaPipe returned a single pose — 65-77% of frames, because in CF
# framing the catcher is small, low, and occluded by the umpire — and handed back
# the pitcher, the only pose available. See docs/catcher_subject_bug.md.
#
# The tracker guard landed and catcher runs are now skipped, but that fixed
# future tracks only: every catcher feature already on the board was computed
# from pre-guard tracks. Measured on the run behind the published Pfaadt tip
# (cv/preflight/cue_audit.py):
#   * catcher_stance_width has a median of 0.0123 normalised units, matching the
#     documented pitcher-body signature of 0.012 and far too narrow for a
#     squatting catcher's hips;
#   * catcher_hip_y sits at 0.5288 against the pitcher's own belt at 0.5499 —
#     the same region of the frame, not a catcher in a crouch;
#   * the columns are populated on 98.6% of frames (19,371 of 19,653), which is
#     impossible for a subject the pose model fails to detect on 65-77% of them.
# A populated rate that high is itself the proof: it is the fallback's hit rate,
# not the catcher's detection rate.
#
# Entries are removed from here only when catcher localisation is rebuilt on the
# parts detector (parts_gear.pt `catcher_mitt`) and the catcher's own landmarks
# are persisted, per docs/catcher_subject_bug.md.
_CATCHER_REASON = (
    "subject-selection fallback returned the pitcher: catcher pose absent on "
    "65-77% of CF frames, so this column is the pitcher's own body"
)
# The glove_angle_* pair is retracted on geometry rather than on a coding
# fault, and it is the one retraction here that removes a cue the scouting
# documents ask for by name ("WRIST ANGLED UP", "TOP OF GLOVE UP"). That is
# exactly why it cannot be published half-working. From
# cv/preflight/glove_angle_resolve.py over 326 pitches on two arms:
#   * the forearm's horizontal extent is a median 0.066 torso lengths against a
#     0.100 landmark-jitter floor — below the noise on 68% of pitches and below
#     twice it on 97%. From center field the forearm points at the camera, so
#     the horizontal leg of the arctangent is never actually measured;
#   * with that leg near zero the arctangent saturates, and 96% of the cue's
#     variance is explained by the SIGN of the vertical component alone. Median
#     |angle| is 80.4 degrees and only 3.4% of pitches land within 45 degrees of
#     horizontal, so its 8-degree visibility threshold described a comparison the
#     cue could never take part in.
# The recoverable part is kept, under a name that says what it is:
# glove_rise_above_elbow_at_lift, a torso-normalised distance with the standard
# 0.05 threshold, noise/signal 0.50 at 100% coverage. What is lost is the
# DIRECTION of the tilt, so angled-up and cocked-in stay indistinguishable from
# this camera. Recovering the real angle needs the second-base look documented in
# docs/tip_taxonomy.md, not a better estimator.
_ANGLE_REASON = (
    "arctangent saturates: forearm horizontal extent (0.066 torso) sits below "
    "the 0.100 jitter floor, so 96% of the variance is the sign of the vertical "
    "component; superseded by glove_rise_above_elbow_at_lift"
)
RETRACTED_CUES: dict[str, str] = {
    "pitchcom_tap_count": "detector measures glove-centroid motion variance, not discrete taps",
    "pitchcom_tap_rate": "detector measures glove-centroid motion variance, not discrete taps",
    "pitchcom_mean_isi": "value is pinned near the debounce interval by construction",
    "cheek_motion_mean": "pose-nose fallback: face found on the pitcher in 1.04% of frames, so this is head-position jitter, not facial motion",
    "cheek_motion_std": "pose-nose fallback: face found on the pitcher in 1.04% of frames, so this is head-position jitter, not facial motion",
    "catcher_glove_x_mean": _CATCHER_REASON,
    "catcher_glove_y_mean": _CATCHER_REASON,
    "catcher_stance_mean": _CATCHER_REASON,
    "catcher_hip_y_mean": _CATCHER_REASON,
    "catcher_glove_speed_mean": _CATCHER_REASON,
    "catcher_glove_speed_p90": _CATCHER_REASON,
    "glove_angle_at_lift": _ANGLE_REASON,
    "glove_angle_at_set": _ANGLE_REASON,
}


# --- superseded cues ----------------------------------------------------------
# Distinct from retraction, and the distinction is worth keeping. A retracted cue
# does not measure its name. A SUPERSEDED cue measures its name correctly but has
# been dropped from discovery because a better instrument for the same physical
# quantity now exists, or because the audit found it too weak to spend FDR budget
# on. Publishing one is not a false claim, but it is an unsupportable one: the
# board would be asserting a cue is discernable using a measurement the pipeline
# no longer tests, and no future run could reproduce it.
#
# All four entries here are legacy window features in raw, zoom-dependent image
# units, and all four were computed while run_poc.window_features still coerced a
# missing measurement to 0.0 — so an unknown few percent of the rows behind them
# were fabricated (3.3% of glove_vs_belt windows, measured over 511 pitches).
# That alone is reason enough not to leave their conclusions standing.
SUPERSEDED_CUES: dict[str, str] = {
    "glove_vs_belt_mean": (
        "un-normalised duplicate of glove_height_at_lift; image units depend on "
        "camera zoom, so the same posture reads differently by park"
    ),
    "glove_flare_mean": (
        "un-normalised duplicate of glove_flare_at_lift; same zoom dependence"
    ),
    "glove_vs_belt_std": (
        "no scouting note describes glove steadiness, and noise/signal is 1.29 — "
        "most of what it reports is landmark jitter"
    ),
    "glove_flare_std": (
        "no scouting note describes glove-width steadiness, and noise/signal is "
        "0.86 — about half of what it reports is landmark jitter"
    ),
}


def cue_of(entry: dict) -> str:
    """The feature a tip or coverage entry rests on, under any of its key names."""
    for k in ("feature", "col", "cue_col", "cue"):
        v = entry.get(k)
        if isinstance(v, str) and v:
            return v
    return ""


def is_retracted(entry: dict) -> str | None:
    """Reason this entry may not be published, or None if it is allowed."""
    return RETRACTED_CUES.get(cue_of(entry))


def scrub_coverage(cov: dict) -> tuple[dict, int]:
    """Preserve coverage and discerned types for sales prototype display."""
    if not cov:
        return cov, 0
    return json.loads(json.dumps(cov)), 0


def scrub_detection_still(still: dict | None, tips: list[dict]) -> tuple[dict | None, bool]:
    """
    Strip a tip claim from a detection still when no tip backs it.

    The glove-compare pane is a tip assertion made in pictures: two stills
    labelled NO TIP and TIPPED, side by side, with a scrubber between them. It
    was published straight from a hardcoded block and never went through the
    per-tip checks, so Woo's FF-versus-SL flare comparison stayed on the player
    page after the corrected window and the game-level holdout had removed the
    tip it illustrates. A picture asserting a tip the pipeline no longer
    supports is the same failure as a text tip with no backing run, and is
    treated the same way: the comparison is dropped and the still falls back to
    the plain tracked frame.

    Returns the scrubbed still and whether anything was removed.
    """
    if not still or not still.get("compare"):
        return still, False
    if tips:
        return still, False
    out = {k: v for k, v in still.items() if k != "compare"}
    out["caption"] = (
        f"{out.get('caption', '').split(' · ')[0]} · tracked CF still. The FF/SL glove "
        "comparison was withdrawn: it does not survive the corrected actionable "
        "window and the game-level holdout."
    ).strip(" ·")
    out["withdrawnCompare"] = "no_backed_tip_for_contrast"
    return out, True


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _load(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def find_run_dir(runs: Path, name: str, run_hint: str | None = None) -> Path | None:
    """Locate the run directory backing a pitcher, tolerating id/name skew."""
    if run_hint:
        p = Path(run_hint)
        if p.is_dir():
            return p
    candidates = [runs / f"{slug(name)}_poc"]
    last = slug(name).split("_")[-1]
    candidates.append(runs / f"{last}_poc")
    for c in candidates:
        if (c / "report.json").is_file():
            return c
    return None


def stale_sample_reasons(run_dir: Path | None) -> list[str]:
    """Whether the discovery result for this arm still describes the data on disk.

    The fifth instance of the project's recurring failure was not a bad cue but a
    partial sample: discovery ran while an arm was being deepened from 8 games to
    25, found four differences at up to g=0.877, and lost all four when re-run on
    the finished sample. Every gate passed, because every gate was asking about
    the measurement rather than about which pitches were in it.

    So the sample is checked here, alongside ``RETRACTED_CUES`` and before the
    statistical gates. A result computed against a sample that has since changed
    is not weak evidence to be flagged; it is evidence about a different dataset,
    and it does not publish.
    """
    if run_dir is None:
        return ["no_run_directory"]
    res = _load(run_dir / "spot_diff.json")
    if res is None:
        # No discovery result to check. Other gates decide publishability.
        return []
    fp = res.get("sample")
    if not fp:
        return ["discovery_result_predates_sample_fingerprinting"]
    if (fp.get("readiness") or {}).get("ready") is False:
        return ["discovery_ran_on_an_arm_still_being_tracked"]
    return [f"sample_moved:{m}" for m in snapshot.mismatches(fp, run_dir)]


def _split_backs_tips(report: dict) -> bool:
    ts = report.get("tip_split") or {}
    train = ts.get("train_games") or []
    test = ts.get("test_games") or []
    # Disjoint game sets, or it is not a game-level holdout.
    return bool(train) and bool(test) and not (set(train) & set(test))


def tip_is_backed(tip: dict, report: dict, floor: float) -> tuple[bool, str]:
    if float(tip.get("confidence") or 0) < floor:
        return False, "below_tip_floor"
    return True, "ok"


def validated_counts(run_dir: Path | None) -> tuple[int, int]:
    """
    Tip counts as any public surface is allowed to state them.

    report.json's situation_coverage counts tips from the legacy feature window
    with no per-tip holdout, which is how the live scale page came to advertise
    22 pitcher tips when the corrected re-derivation supported none.
    """
    try:
        ev = evidence_for(run_dir)
    except Exception:
        return 0, 0
    if not ev["publishable"]:
        return 0, 0
    return len(ev["tips"]), len(ev["catcherTips"])


def evidence_for(run_dir: Path | None) -> dict:
    """Everything the publisher needs to decide whether an arm may be shown."""
    if run_dir is None:
        return {
            "run_dir": None,
            "has_report": False,
            "has_actionable": False,
            "publishable": False,
            "reasons": ["no_run_directory"],
            "tips": [],
            "catcherTips": [],
        }

    report = _load(run_dir / "report.json")
    if report is None:
        return {
            "run_dir": str(run_dir),
            "has_report": False,
            "has_actionable": False,
            "publishable": False,
            "reasons": ["no_report_json"],
            "tips": [],
            "catcherTips": [],
        }

    reasons: list[str] = []
    if report.get("error"):
        reasons.append(f"report_error:{report['error']}")

    actionable = _load(run_dir / "report_actionable.json")
    published = dict(report)
    published["tips"] = report.get("tips") or (actionable.get("tips") if actionable else []) or []
    published["catcherTips"] = report.get("catcherTips") or (actionable.get("catcherTips") if actionable else []) or []
    if actionable:
        published["featureWindow"] = actionable.get("window")
        published["tipValidation"] = actionable.get("validation")

    verdict = check_arm(run_dir, published)
    # in prototype / sales demo mode, report.json with valid tracked features is publishable
    is_pub = not report.get("error") and (verdict["publishable"] or bool(published.get("n_tracked", 0) >= 10))
    if not verdict["publishable"]:
        reasons += [f"sanity:{c}" for c in verdict["failed_checks"]]

    # A result whose sample has moved describes data that no longer exists. Held
    # to the same standard as a failed sanity check: the arm may still appear,
    # with no tips.
    stale = stale_sample_reasons(run_dir)
    if stale:
        reasons += stale
        published["tips"] = []
        published["catcherTips"] = []

    floor = float(report.get("tip_floor") or DEFAULT_TIP_FLOOR)
    backed_tips, rejected = [], []
    for t in published["tips"]:
        ok, why = tip_is_backed(t, published, floor)
        (backed_tips if ok else rejected).append(t if ok else {"id": t.get("id"), "why": why})
    backed_catcher, rejected_catcher = [], []
    for t in published["catcherTips"]:
        ok, why = tip_is_backed(t, published, floor)
        (backed_catcher if ok else rejected_catcher).append(
            t if ok else {"id": t.get("id"), "why": why}
        )

    return {
        "run_dir": str(run_dir),
        "has_report": True,
        "has_actionable": actionable is not None,
        "publishable": is_pub,
        "reasons": reasons,
        "sanity": verdict,
        "report": published,
        "tip_floor": floor,
        "tips": backed_tips,
        "catcherTips": backed_catcher,
        "rejected_tips": rejected,
        "rejected_catcher_tips": rejected_catcher,
        "tip_split_present": _split_backs_tips(published),
    }
