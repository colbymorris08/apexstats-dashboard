"""
Pre-FDR diagnostics: sign stability across the game boundary, and across
delivery strata.

Discovery reports pass/fail. That is the right output for publishing and the
wrong one for understanding, because it collapses "nothing was close" and "seven
things were close and five of them were noise" into the same zero. Two
diagnostics separate those, and both are about REPLICATION rather than p-values:

  game boundary  A cue's effect is measured on the discovery games and again on
                 the held-out games. A real difference keeps its sign; noise
                 flips. On Thorpe, five of seven nominal hits flipped, which was
                 the single most informative number produced overnight.
  delivery strata Stretch and windup are different deliveries. A cue describing
                 something real about how a pitcher grips or presents the ball
                 should behave the same way in both; one that only appears in one
                 stratum is either delivery-specific or an artefact. Logan Webb
                 is the first arm with both strata powered, so this comparison
                 has never been runnable before.

Nothing here is publishable. Uncorrected p-values selected post hoc out of
several hundred comparisons are precisely the artefact the FDR gate exists to
stop, and the sign checks are descriptive. This module exists to characterise a
zero, not to find a way around it.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from scipy import stats

from preflight.spot_diff import (
    CUES,
    MIN_PER_GROUP,
    _contrasts,
    _groups,
    hedges_g,
    load_pitcher,
    split_by_game,
)


def stratum_rows(df, stratum: str) -> list[dict]:
    """Every cue x contrast in one stratum, with discovery and holdout effects."""
    col = "delivery_type" if "delivery_type" in df.columns else "delivery"
    sub = df[df[col] == stratum]
    if sub.empty:
        return []
    disc, hold = split_by_game(sub)
    types = sorted({t for t in sub["pitch_type"].dropna().unique() if t})
    rows = []
    for a, b, _ in _contrasts(sub, types) or []:
        for cue in CUES:
            if cue not in sub.columns:
                continue
            try:
                da, db = _groups(disc, cue, a, b)
                ha, hb = _groups(hold, cue, a, b)
            except Exception:
                continue
            if min(len(da), len(db)) < MIN_PER_GROUP:
                continue
            gd = hedges_g(da, db)
            pd_ = float(stats.ttest_ind(da, db, equal_var=False).pvalue)
            thin = min(len(ha), len(hb)) < MIN_PER_GROUP
            gh = None if thin else hedges_g(ha, hb)
            rows.append(
                {
                    "cue": cue,
                    "contrast": f"{a} vs {b}",
                    "n_disc": (len(da), len(db)),
                    "g_disc": gd,
                    "p_disc": pd_,
                    "g_hold": gh,
                    "same_sign": None if gh is None else bool(np.sign(gd) == np.sign(gh)),
                }
            )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--strata", nargs="+", default=["stretch", "windup"])
    args = ap.parse_args()

    df = load_pitcher(Path(args.run_dir))
    name = Path(args.run_dir).name
    per_stratum: dict[str, list[dict]] = {}

    for st in args.strata:
        rows = stratum_rows(df, st)
        per_stratum[st] = rows
        if not rows:
            print(f"\n--- {name} / {st}: no testable contrast ---")
            continue
        nominal = [r for r in rows if r["p_disc"] < 0.05]
        checkable = [r for r in nominal if r["same_sign"] is not None]
        held = [r for r in checkable if r["same_sign"]]
        print(f"\n--- {name} / {st} ---")
        print(f"cue x contrast tested        : {len(rows)}")
        print(f"nominally p<0.05 (uncorrected): {len(nominal)}  (chance alone: {0.05*len(rows):.1f})")
        if checkable:
            print(
                f"of those, sign holds on the held-out games: {len(held)} of "
                f"{len(checkable)}  ({len(held)/len(checkable):.0%})"
            )
        for r in sorted(nominal, key=lambda r: r["p_disc"])[:8]:
            gh = "thin" if r["g_hold"] is None else f"{r['g_hold']:+.3f}"
            ss = "—" if r["same_sign"] is None else ("yes" if r["same_sign"] else "NO")
            print(
                f"   p={r['p_disc']:.4f}  g_disc={r['g_disc']:+.3f}  g_hold={gh:>7s}  "
                f"sign={ss:<3s}  {r['cue']} ({r['contrast']})"
            )

    # --- cross-stratum consistency -----------------------------------------
    a, b = args.strata[0], args.strata[-1]
    ra, rb = per_stratum.get(a) or [], per_stratum.get(b) or []
    if ra and rb:
        ka = {(r["cue"], r["contrast"]): r for r in ra}
        kb = {(r["cue"], r["contrast"]): r for r in rb}
        shared = sorted(set(ka) & set(kb))
        print(f"\n=== cross-stratum read: {a} vs {b} ===")
        print(f"cue x contrast testable in BOTH strata: {len(shared)}")
        if not shared:
            print("  nothing overlaps; the two strata do not share a testable contrast")
            return
        agree = [k for k in shared if np.sign(ka[k]["g_disc"]) == np.sign(kb[k]["g_disc"])]
        print(
            f"same sign in both deliveries: {len(agree)} of {len(shared)} "
            f"({len(agree)/len(shared):.0%}); coin-flip expectation is 50%"
        )
        print(f"\n{'cue':34s} {'contrast':12s} {'g_'+a:>9s} {'g_'+b:>9s} {'agree':>6s}")
        for k in sorted(shared, key=lambda k: -abs(ka[k]["g_disc"])):
            cue, contrast = k
            ga, gb = ka[k]["g_disc"], kb[k]["g_disc"]
            print(
                f"{cue:34s} {contrast:12s} {ga:+9.3f} {gb:+9.3f} "
                f"{('yes' if np.sign(ga)==np.sign(gb) else 'NO'):>6s}"
            )


if __name__ == "__main__":
    main()
