"""
The one external check available: does the expanded cue set point at Thorpe's
documented changeup tip?

Scouts wrote it down independently of anything this system measures — "HAND LOWER
IN GLOVE", "he is higher in glove on CH", "CH grip less buried in glove". That
makes Thorpe the only arm where a detection can be checked against a fact the
pipeline did not generate, which is worth more than any number of internally
consistent results.

What this can and cannot establish
----------------------------------
The cue that would DIRECTLY capture the documented tip is the hand's height
INSIDE the glove, and that is behind the parts detector: it needs the hand and
the glove resolved as separate objects, which pose landmarks do not do. So the
honest ceiling here is a RELATED cue moving in the direction the scouts
described. Two are related, and neither is the same measurement:

  hand_gap_at_lift  wrist-to-wrist separation, i.e. how far the throwing wrist
                    sits from the glove wrist. A hand carried less buried should
                    read as a LARGER gap.
  hand_vis_at_lift  the pose model's own visibility score for the throwing-hand
                    landmarks. A hand less buried should be MORE visible.

A move in hand_gap or hand_vis is consistent with the documented tip. It is not a
reproduction of it, and this module prints the distinction rather than leaving it
to be inferred.

This reports the discovery statistics BEFORE the FDR correction, deliberately, so
the strength of the evidence is visible rather than collapsed into a pass/fail.
Nothing here is a publishable result: an uncorrected p-value picked out of 200
comparisons is exactly the artefact the FDR gate exists to stop. It is diagnostic
only, and labelled as such in the output.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from scipy import stats

from preflight.spot_diff import (
    CUES,
    MIN_PER_GROUP,
    _groups,
    hedges_g,
    load_pitcher,
    split_by_game,
)

RELATED = {
    "hand_gap_at_lift": "wrist-to-wrist gap; larger = hand carried less buried",
    "hand_vis_at_lift": "throwing-hand landmark visibility; higher = hand more exposed",
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", default="../runs/drew_thorpe_rich_poc")
    ap.add_argument("--stratum", default="stretch")
    args = ap.parse_args()

    df = load_pitcher(Path(args.run_dir))
    col = "delivery_type" if "delivery_type" in df.columns else "delivery"
    df = df[df[col] == args.stratum]
    disc, hold = split_by_game(df)

    print(f"Thorpe ground-truth check — stratum '{args.stratum}'")
    print(f"documented tip: hand lower / less buried in the glove on the CHANGEUP")
    print(f"n = {len(df)} pitches, discovery {len(disc)} / holdout {len(hold)}\n")

    types = [t for t in df["pitch_type"].dropna().unique() if t]
    if "CH" not in types:
        print("no CH in this stratum; nothing to check")
        return

    others = [t for t in types if t != "CH"]
    print("CH vs each other pitch type, DISCOVERY split, UNCORRECTED — diagnostic only")
    print(f"{'cue':26s} {'vs':4s} {'nCH':>4s} {'nOth':>5s} {'g':>7s} {'p_unc':>8s} {'ΔCH-oth':>9s} {'vis?':>5s} {'direction'}")

    for cue_name, meaning in RELATED.items():
        cue = CUES.get(cue_name)
        if cue is None or cue_name not in df.columns:
            print(f"{cue_name}: not available")
            continue
        for other in others:
            try:
                a, b = _groups(disc, cue_name, "CH", other)
            except Exception as exc:
                print(f"{cue_name:26s} {other:4s}  skipped: {exc}")
                continue
            if len(a) < MIN_PER_GROUP or len(b) < MIN_PER_GROUP:
                print(f"{cue_name:26s} {other:4s} {len(a):4d} {len(b):5d}   too few per group")
                continue
            g = hedges_g(a, b)
            p = float(stats.ttest_ind(a, b, equal_var=False).pvalue)
            delta = float(np.mean(a) - np.mean(b))
            vis = cue.visible_delta is None or abs(delta) >= cue.visible_delta
            # The documented tip says the CH hand is LESS buried, so for both
            # related cues the predicted sign is positive.
            direction = "AS DOCUMENTED" if delta > 0 else "opposite"
            print(
                f"{cue_name:26s} {other:4s} {len(a):4d} {len(b):5d} {g:7.3f} {p:8.4f} "
                f"{delta:+9.4f} {str(vis):>5s} {direction}"
            )
        print(f"    ({meaning})")

    print("\nfor contrast, the same contrast on every wired cue, ranked by uncorrected p:")
    rows = []
    for cue_name in CUES:
        if cue_name not in df.columns:
            continue
        for other in others:
            try:
                a, b = _groups(disc, cue_name, "CH", other)
            except Exception:
                continue
            if len(a) < MIN_PER_GROUP or len(b) < MIN_PER_GROUP:
                continue
            p = float(stats.ttest_ind(a, b, equal_var=False).pvalue)
            rows.append((p, cue_name, other, hedges_g(a, b)))
    rows.sort()
    for p, cue_name, other, g in rows[:10]:
        print(f"   {p:8.4f}  g={g:+6.3f}  {cue_name} (CH vs {other})")
    if rows:
        print(
            f"\n   {sum(1 for r in rows if r[0] < 0.05)} of {len(rows)} CH contrasts are "
            f"nominally p<0.05; at 5% by chance alone you would expect {0.05*len(rows):.1f}."
        )


if __name__ == "__main__":
    main()
