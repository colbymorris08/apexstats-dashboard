"""
Prespecified single-hypothesis tests of externally documented scout tips.

This is a **separate family from the blind sweep and must never be pooled with it.**

The blind sweep tests every cue against every contrast with no prior, so it pays a
multiple-comparison penalty that is entirely deserved. These tests are different in
kind: for each one, a professional scout named the pitcher, the cue, the pitch
contrast and the direction, in writing, before we looked at any film. A
prespecified one-sided test of a named prediction on a named pitcher is a single
hypothesis and carries no multiplicity burden.

That is not a loophole and it is not a softer bar. It is the standard reason
prespecification earns power: the hypothesis space was fixed by someone else, in
advance, without access to our data. The registry lives in
``docs/prespecified_tips.json`` and is written before any result is computed, so
the prespecification is auditable and cannot be retrofitted.

Three protections against this becoming a route to a manufactured finding:

* **The direction is fixed in the registry.** A result in the opposite direction is
  a failure, not a finding with a flipped sign. This is enforced here, not trusted.
* **Retracted cues stay blocked**, even when a scout named them. Retraction is about
  what the instrument measures, and documentary support does not override it.
* **These results carry their own label** and never enter the blind-sweep counts,
  the FDR family, or the tier assignment used for the board's HIGH/MEDIUM rows.

Why this matters more than anything else in the project: of ten documented pitchers
we have footage on one. Every conclusion so far rests on a blind search that found
nothing, which is much weaker evidence about the method than a direct test of a tip
a human already judged real.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from preflight import game_dates, publication_eval, snapshot, spot_diff, temporal, tiering
from preflight.temporal_discover import load_family

REGISTRY = Path(__file__).resolve().parents[2] / "docs" / "prespecified_tips.json"

# Fastball labels in descending priority, used to resolve PRIMARY_FASTBALL. Fixed
# here rather than chosen per arm so the contrast cannot be picked to suit a result.
FASTBALL_PRIORITY = ["FF", "SI", "FC"]
BREAKING = {"SL", "CU", "ST", "SV", "KC"}


def resolve_contrast(df: pd.DataFrame, test: dict) -> tuple[str, str] | None:
    """Turn the registry's symbolic pitch labels into this arm's actual labels."""
    counts = df["pitch_type"].value_counts()
    a = test["pitch_a"]
    if a == "PRIMARY_FASTBALL":
        a = next((f for f in FASTBALL_PRIORITY if counts.get(f, 0) >= spot_diff.MIN_PER_GROUP), None)
    if a is None or counts.get(a, 0) < spot_diff.MIN_PER_GROUP:
        return None
    b = test["pitch_b"]
    if b == "PRIMARY_FASTBALL":
        b = next((f for f in FASTBALL_PRIORITY if f != a and counts.get(f, 0) >= spot_diff.MIN_PER_GROUP), None)
    elif b == "BREAKING":
        b = "REST_BREAKING"
    if b is None:
        return None
    return a, b


def _series(df: pd.DataFrame, col: str, a: str, b: str):
    """Values for each side of the contrast, honouring the symbolic 'rest' labels."""
    x = pd.to_numeric(df[col], errors="coerce")
    ga = x[df["pitch_type"] == a]
    if b == "REST":
        gb = x[df["pitch_type"] != a]
    elif b == "REST_BREAKING":
        gb = x[df["pitch_type"].isin(BREAKING)]
    else:
        gb = x[df["pitch_type"] == b]
    return ga.dropna().to_numpy(), gb.dropna().to_numpy()


def run_test(test: dict, args, cache) -> dict[str, Any]:
    """One registered hypothesis, one one-sided test, no correction."""
    out = {k: test[k] for k in ("id", "pitcher", "cue", "predicted_direction",
                                "scout_words", "prediction_in_words", "cf_status")}

    reason = tiering.retraction_reason(test["cue"])
    if reason:
        return {**out, "status": "blocked", "detail": f"retracted cue: {reason}"}

    run = test.get("run_dir")
    if not run or not (Path("..") / Path(run).relative_to("runs")).exists():
        candidate = Path(__file__).resolve().parents[2] / (run or "")
        if not run or not candidate.exists():
            return {**out, "status": "no_footage",
                    "detail": test.get("footage_status", "no film for this pitcher")}
        run = candidate
    else:
        run = Path(__file__).resolve().parents[2] / run

    try:
        snapshot.assert_quiescent(run, allow_unready=args.allow_unready)
    except (Exception, SystemExit) as exc:
        return {**out, "status": "not_ready", "detail": str(exc)}

    df = load_family(run, "position")
    if test["cue"] not in df.columns:
        return {**out, "status": "cue_absent", "detail": f"{test['cue']} not in features"}

    disc_g, val_g = temporal.temporal_split(df, args.n_disc, args.n_val, cache)
    keep = set(map(int, disc_g)) | set(map(int, val_g))
    sub = df[temporal.game_keys(df).isin(keep)].copy()

    # Fixed in advance, not chosen per arm: every prespecified test runs inside the
    # set-anchored stratum. Set-anchored and fixed-lookback windows are unlike
    # measurements — the geometry flag alone shifts at-set cues by mean |g| = 0.23 —
    # and every ``*_at_set`` value among the fixed-lookback pitches is anchored to a
    # set that was never detected. Pooling them would compare a real measurement
    # against a fabricated one, which is the mistake behind the Webb sign reversal.
    sub["_delivery"] = spot_diff._delivery_series(sub)
    sub = sub[sub["_delivery"] == "stretch"].copy()
    out["stratum"] = "set_anchored"
    if sub.empty:
        return {**out, "status": "no_set_anchored_pitches",
                "detail": "every pitch failed set detection"}

    resolved = resolve_contrast(sub, test)
    if resolved is None:
        return {**out, "status": "contrast_unavailable",
                "detail": f"fewer than {spot_diff.MIN_PER_GROUP} pitches on a side"}
    a, b = resolved
    out["contrast_resolved"] = f"{a} vs {b}"

    ga, gb = _series(sub, test["cue"], a, b)
    if min(len(ga), len(gb)) < spot_diff.MIN_PER_GROUP:
        return {**out, "status": "underpowered", "detail": f"n={len(ga)},{len(gb)}"}

    # One-sided, in the direction the scout wrote down. "a_higher" means the
    # registry predicts group a exceeds group b; anything else is a failed
    # prediction regardless of how large the difference is.
    alt = "greater" if test["predicted_direction"] == "a_higher" else "less"
    t = stats.ttest_ind(ga, gb, equal_var=False, alternative=alt)
    g = spot_diff.hedges_g(ga, gb)
    observed_dir = "a_higher" if float(np.mean(ga) - np.mean(gb)) > 0 else "a_lower"

    k = temporal.game_keys(sub)
    disc, hold = sub[k.isin(set(map(int, disc_g)))], sub[k.isin(set(map(int, val_g)))]
    ev = None
    if b not in {"REST", "REST_BREAKING"}:
        r = publication_eval.evaluate(disc, hold, test["cue"], a, b)
        if r and "too_few" not in r:
            ev = {
                "precision": round(float(r["precision"]), 3) if np.isfinite(r["precision"]) else None,
                "base_rate": round(float(r["base_rate"]), 3),
                "youden_j": round(float(r["youden_j"]), 3),
                "lr_pos": round(float(r["lr_pos"]), 2) if np.isfinite(r["lr_pos"]) else None,
                "prior": round(float(r["prior"]), 3),
                "post_fire": round(float(r["post_fire"]), 3) if np.isfinite(r["post_fire"]) else None,
                "n_fire": int(r["n_fire"]), "n_holdout": int(r["n_hold"]),
            }

    return {
        **out,
        "status": "tested",
        "n_a": int(len(ga)), "n_b": int(len(gb)),
        "n_games": len(keep),
        "mean_a": round(float(np.mean(ga)), 5), "mean_b": round(float(np.mean(gb)), 5),
        "delta": round(float(np.mean(ga) - np.mean(gb)), 5),
        "g": round(float(g), 3),
        "p_one_sided": float(f"{float(t.pvalue):.4g}"),
        "direction_observed": observed_dir,
        "direction_as_predicted": observed_dir == test["predicted_direction"],
        # The verdict. Direction is checked first and independently: a large,
        # significant difference in the wrong direction refutes the documented tip
        # rather than supporting it.
        "replicates": bool(observed_dir == test["predicted_direction"] and float(t.pvalue) < 0.05),
        "evaluation": ev,
        "sample": snapshot.fingerprint(run, "features.csv", sub),
        "family": "prespecified_documented",
    }


def report(results: list[dict]) -> str:
    lines = ["\n=== prespecified tests of documented scout tips ===",
             "separate family from the blind sweep: single hypotheses, no FDR",
             ""]
    tested = [r for r in results if r["status"] == "tested"]
    for r in results:
        if r["status"] != "tested":
            lines.append(f"  [{r['status']:20s}] {r['pitcher']:14s} {r['id']:24s} {r.get('detail','')}")
    lines.append("")
    for r in tested:
        verdict = "REPLICATES" if r["replicates"] else (
            "wrong direction" if not r["direction_as_predicted"] else "not significant")
        lines.append(f"  {r['pitcher']} — {r['id']}")
        lines.append(f"    scout: \"{r['scout_words']}\"")
        lines.append(f"    predicted: {r['prediction_in_words']}")
        lines.append(f"    {r['contrast_resolved']}  n={r['n_a']},{r['n_b']}  "
                     f"g={r['g']:+.3f}  one-sided p={r['p_one_sided']}  -> {verdict}")
        ev = r.get("evaluation")
        if ev and ev["precision"] is not None:
            lines.append(f"    when it fires it is right {ev['precision']:.1%}; "
                         f"random guessing on this pitcher gives {ev['base_rate']:.1%} "
                         f"(J={ev['youden_j']:+.3f}, LR+={ev['lr_pos']}, fires {ev['n_fire']})")
        lines.append("")
    n_rep = sum(1 for r in tested if r["replicates"])
    lines.append(f"tested {len(tested)} of {len(results)} registered hypotheses; "
                 f"{n_rep} replicate")
    lines.append(f"blocked on missing footage: "
                 f"{sum(1 for r in results if r['status'] == 'no_footage')}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--registry", default=str(REGISTRY))
    ap.add_argument("--n-disc", type=int, default=temporal.N_DISCOVERY_STARTS)
    ap.add_argument("--n-val", type=int, default=temporal.N_VALIDATION_STARTS)
    ap.add_argument("--only", help="run a single registered id")
    ap.add_argument("--allow-unready", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    reg = json.loads(Path(args.registry).read_text())
    cache = game_dates.load_cache()
    tests = [t for t in reg["tests"] if not args.only or t["id"] == args.only]
    results = [run_test(t, args, cache) for t in tests]
    print(report(results))

    if args.out:
        Path(args.out).write_text(json.dumps(
            {"family": "prespecified_documented", "registry": args.registry,
             "results": results}, indent=2, default=str))
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
