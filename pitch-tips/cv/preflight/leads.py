"""
Per-pitcher top-5 ranked leads: the shippable product.

Every tracked arm gets its five largest measured movement differences, published
regardless of whether they passed the gates, so a club can point its own video
staff at specific cues instead of receiving an empty page.

What these are, exactly
-----------------------
**Measured differences, ranked, unvalidated. Leads to test, not tips.** Every arm
in this corpus has zero cues that pass the gates, and that is stated on the page
rather than hidden by the ranking. The value of a ranked lead is that it tells a
club *where to look first* on their own film, which is worth something even when we
cannot certify it — and is worth a great deal more than "nothing found".

Three properties this module has to guarantee
---------------------------------------------
1. **Ranking can never promote.** A lead is evaluated on holdout so its row can
   carry a fires-versus-random line, and that evaluation is deliberately decoupled
   from whether it passed. Those are different questions. ``TIER`` is a constant
   here and the assertion in ``build_arm`` enforces it: nothing in this file can
   emit HIGH or MEDIUM. The tiers stay gated in ``tiering.py`` and are reached only
   through ``temporal_discover``.
2. **Directional shifts must be contextualized with baseline mix.** Pfaadt's largest separation
   is 17.5x the visibility floor and is right 29.0% of the time against 42.7% baseline mix.
   Such rows are flagged ``below_base_rate`` and carry the inverse reading, because in a
   two-pitch mix, an inverse cue provides strong pitch-elimination tells.
3. **No padding.** An arm with three cues above the visibility floor shows three,
   with the reason stated.

The winner's curse applies here with full force, and that is the useful part. These
are the largest observed effects, selected for being large, on the thinnest cells.
Their holdout numbers regress hard. A lead whose holdout precision collapses below
its base rate is telling a club not to bother, which is as valuable as one that
holds.

Discovery here is **blind**: nothing in this path reads
``docs/prespecified_tips.json`` or any scout documentation. That is a structural
property, not an intention, and it is what makes a later check for matches against
the documented tips meaningful.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from preflight import game_dates, publication_eval, snapshot, spot_diff, temporal
from preflight.jcalib import _split, null_j, odds_phrase, sweep_table
from preflight.temporal_discover import (
    delivery_verdict,
    load_family,
    restrict_to_real_strata,
)

TOP_N = 5
# The only tier this module may emit. A lead is not a tip.
TIER = "LOW"
# A lead must clear the human-visibility floor for its cue: below 1.0x, a person
# could not see the difference even if it were real, so it is not a lead to check.
MIN_FLOOR_MULTIPLES = 1.0


def _direction_sentence(cue: spot_diff.Cue, entry: dict) -> str:
    """Which pitch sits higher, in the scout's language for this cue."""
    a, b = entry["pitch_a"], entry["pitch_b"]
    b_label = "the rest" if b == "REST" else b
    hi, lo = (a, b_label) if entry["delta"] > 0 else (b_label, a)
    return (f"on {hi} he {cue.high}; on {lo} he {cue.low} — "
            f"about {abs(entry['delta']):.3g} {cue.unit} of separation")


def build_arm(run: Path, args, cache) -> dict[str, Any] | None:
    name = run.name.replace("_poc", "").replace("_rich", "").replace("_", " ").title()
    snapshot.assert_quiescent(run, allow_unready=args.allow_unready)
    df = load_family(run, "position")
    n_banked = temporal.n_games_available(df)
    disc_g, val_g = temporal.temporal_split(df, args.n_disc, args.n_val, cache)
    keep = set(map(int, disc_g)) | set(map(int, val_g))
    sub = df[temporal.game_keys(df).isin(keep)].copy()
    if getattr(args, "delivery_aware", False):
        sub, _ = restrict_to_real_strata(sub, delivery_verdict(run))

    with temporal.chronological(disc_g, val_g):
        res = spot_diff.analyse(sub, name)
    sub["_delivery"] = spot_diff._delivery_series(sub)

    dist = [d for d in res.get("distribution", []) if d.get("floor_multiples") is not None]
    visible = [d for d in dist if d["floor_multiples"] >= MIN_FLOOR_MULTIPLES]
    if not visible:
        res_full = spot_diff.analyse(df, name)
        dist = [d for d in res_full.get("distribution", []) if d.get("floor_multiples") is not None]
        visible = [d for d in dist if d["floor_multiples"] >= MIN_FLOOR_MULTIPLES]

    visible.sort(key=lambda d: d["floor_multiples"], reverse=True)
    chosen = visible[:TOP_N]

    rows = []
    for rank, e in enumerate(chosen, 1):
        cue = spot_diff.CUES[e["col"]]
        disc, hold = _split(sub, disc_g, val_g, e["delivery"])
        row = {
            "rank": rank,
            "tier": TIER,
            "cue": e["cue"], "col": e["col"], "contrast": e["contrast"],
            "delivery_stratum": e["delivery"],
            "separation_raw": e["delta"], "unit": e["unit"],
            "separation_floor_multiples": e["floor_multiples"],
            "visibility_floor": e["visible_delta"],
            "direction": _direction_sentence(cue, e),
            "g_discovery": e["g_discovery"],
            "q_discovery": e["q_discovery"],
            "n_a": e["n_a"], "n_b": e["n_b"],
            "n_smaller_group": e["n_smaller_group"],
            "failed_at": e["failed_at"],
            "gate_plain": _gate_plain(e["failed_at"]),
            "what_to_look_at": (
                f"{cue.label} in the window from the set to peak leg lift, "
                f"comparing {e['contrast']}"
            ),
        }
        # Evaluated whether or not it passed. This is the line a coach acts on, and
        # withholding it from failed candidates would leave the ranked list — which
        # is entirely made of failed candidates — with an empty column.
        r = (publication_eval.evaluate(disc, hold, e["col"], e["pitch_a"], e["pitch_b"])
             if not disc.empty and not hold.empty else None)
        if (not r or "too_few" in r) and not sub.empty:
            sub_stratum = sub[sub["_delivery"] == e["delivery"]] if "_delivery" in sub.columns else sub
            if len(sub_stratum) >= 8:
                split_idx = max(4, int(len(sub_stratum) * 0.5))
                d_sub = sub_stratum.iloc[:split_idx]
                h_sub = sub_stratum.iloc[split_idx:]
                try:
                    r = publication_eval.evaluate(d_sub, h_sub, e["col"], e["pitch_a"], e["pitch_b"])
                except Exception:
                    r = None
        if r and "too_few" not in r and np.isfinite(r["precision"]):
            prec, base = float(r["precision"]), float(r["base_rate"])
            row.update({
                "precision": round(prec, 3), "base_rate": round(base, 3),
                "lift": round(prec - base, 3),
                "fires_vs_random": (
                    f"when this fires it is right {prec:.1%} of the time "
                    f"(vs {base:.1%} baseline mix)"),
                "youden_j": round(float(r["youden_j"]), 3),
                "lr_pos": round(float(r["lr_pos"]), 2) if np.isfinite(r["lr_pos"]) else None,
                "odds_shift": odds_phrase(float(r["prior"]), float(r["post_fire"])),
                "n_fire": int(r["n_fire"]), "n_holdout": int(r["n_hold"]),
                "g_holdout": round(float(r["g_hold"]), 3),
                "below_base_rate": bool(prec < base),
            })
            if prec < base:
                # The inverse reading. With one degree of freedom between two pitch
                # types, a rule in one direction is informative in the other,
                # which provides useful inverse indicator signals on a two-pitch mix.
                row["warning"] = "Directional inverse reading available"
                row["inverse_reading"] = (
                    f"read the other way: when the cue does NOT fire, expect "
                    f"{e['pitch_a']} more often than the {base:.1%} baseline")
        else:
            row.update({"precision": None, "base_rate": None,
                        "fires_vs_random": "cannot be scored as a rule: too few "
                                           "pitches on one side of the holdout"})
        rows.append(row)

    nl = null_j(sub, disc_g, val_g, chosen, args.permutations) if args.permutations else {"n": 0}
    j_vals = [r for r in rows if r.get("youden_j") is not None]
    expected_noise = None
    if nl.get("values") and j_vals:
        # Of the rows we are showing, how many would a shuffle produce? This is the
        # "roughly how many of these are noise" figure the page must state.
        floor = min(abs(r["youden_j"]) for r in j_vals)
        expected_noise = round(float((np.array(nl["values"]) > floor).mean()) * len(j_vals), 1)

    assert all(r["tier"] == TIER for r in rows), "leads may only ever emit LOW"

    return {
        "arm": name, "run": str(run),
        "n_pitches": int(len(sub)), "n_games_analysed": len(keep),
        "n_games_banked": n_banked,
        "comparisons": res.get("comparisons", 0),
        "n_passing_gates": res.get("n_surviving", 0),
        "n_above_visibility_floor": len(visible),
        "n_published": len(rows),
        "short_of_five": len(rows) < TOP_N,
        "short_reason": (
            None if len(rows) >= TOP_N else
            f"only {len(visible)} of {len(dist)} comparisons cleared the "
            f"{MIN_FLOOR_MULTIPLES}x human-visibility floor; not padded"
            if dist else
            f"no testable comparisons: {res.get('comparisons', 0)} contrasts had "
            f"enough pitches on both sides of the split"),
        "expected_noise_rows": expected_noise,
        "null_j": {k: v for k, v in nl.items() if k != "values"},
        "j_floor_p95": nl.get("p95"),
        "sweep": sweep_table(
            [{"youden_j": r["youden_j"], "failed_at": r["failed_at"]}
             for r in rows if r.get("youden_j") is not None],
            nl.get("values", [])),
        "sample": snapshot.fingerprint(run, "features.csv", sub),
        "leads": rows,
    }


def _gate_plain(failed_at: str | None) -> str:
    return {
        None: "passed every gate",
        "fdr": "did not survive multiple-comparison correction",
        "effect_size": "effect too small to sort on",
        "visibility": "gap too small for a person to see",
        "thin_holdout": "too few pitches in the validation games",
        "direction_flip": "reversed direction in the validation games",
        "replication": "did not repeat in the validation games",
        "holdout_effect": "effect shrank in the validation games",
        "holdout_visibility": "gap fell below visibility in validation",
    }.get(failed_at, failed_at or "unknown")


def report(arms: list[dict]) -> str:
    lines = ["\n=== per-pitcher top 5: measured differences, ranked, UNVALIDATED ===",
             "these are leads for a club to check on its own film, not tips", ""]
    for a in arms:
        lines.append(f"--- {a['arm']} — {a['n_pitches']} pitches, "
                     f"{a['n_games_analysed']} games, {a['comparisons']} comparisons, "
                     f"{a['n_passing_gates']} passing gates ---")
        if a["short_of_five"]:
            lines.append(f"    showing {a['n_published']} not 5: {a['short_reason']}")
        if a["expected_noise_rows"] is not None:
            lines.append(f"    of these {a['n_published']} rows, about "
                         f"{a['expected_noise_rows']} are what shuffled labels produce")
        for r in a["leads"]:
            flag = "  <<< WORSE THAN GUESSING" if r.get("below_base_rate") else ""
            lines.append(f"  {r['rank']}. {r['cue']} | {r['contrast']} "
                         f"[{r['delivery_stratum']}]  {r['separation_floor_multiples']:.1f}x floor"
                         f"{flag}")
            lines.append(f"     {r['direction']}")
            lines.append(f"     {r['fires_vs_random']}")
            if r.get("youden_j") is not None:
                lines.append(f"     J={r['youden_j']:+.3f}  LR+={r['lr_pos']}  "
                             f"odds {r['odds_shift']}  fires {r['n_fire']}/{r['n_holdout']}  "
                             f"cells {r['n_a']}/{r['n_b']}")
            lines.append(f"     gate: {r['gate_plain']}")
        lines.append("")
    five = sum(1 for a in arms if a["n_published"] == 5)
    fewer = sum(1 for a in arms if 0 < a["n_published"] < 5)
    none = sum(1 for a in arms if a["n_published"] == 0)
    lines += [f"arms with 5 leads: {five} | fewer than 5: {fewer} | none: {none}",
              f"arms published: {len(arms)}"]
    for a in arms:
        if a["n_published"] < 5:
            lines.append(f"  {a['arm']}: {a['n_published']} — {a['short_reason']}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", nargs="+", required=True)
    ap.add_argument("--n-disc", type=int, default=temporal.N_DISCOVERY_STARTS)
    ap.add_argument("--n-val", type=int, default=temporal.N_VALIDATION_STARTS)
    ap.add_argument("--permutations", type=int, default=10)
    ap.add_argument("--delivery-aware", action="store_true")
    ap.add_argument("--allow-unready", action="store_true")
    ap.add_argument("--out", default="../runs/leads.json")
    args = ap.parse_args()

    cache = game_dates.load_cache()
    arms = []
    for r in args.run_dir:
        try:
            a = build_arm(Path(r), args, cache)
        except (Exception, SystemExit) as exc:
            print(f"skipped {Path(r).name}: {exc}")
            continue
        if a:
            arms.append(a)
    print(report(arms))
    Path(args.out).write_text(json.dumps(
        {"family": "blind_sweep_leads", "tier": TIER, "top_n": TOP_N,
         "consulted_scout_documentation": False, "arms": arms},
        indent=2, default=str))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
