"""
Per-situation pitch-type discernability at the strict ≥75% gate.

Product question:
  For pitcher P in situation S (e.g. runner on 2nd + RHH), of their 2–7 pitch types,
  how many are discernable from CV pre-release features at ≥75% accuracy?

Each pitch type is scored one-vs-rest inside the situation slice.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
import pandas as pd

from preflight.context import context_phrase
from preflight.thresholds import TIP_CONFIDENCE_FLOOR

MIN_TYPE_N = 4
MIN_SLICE_N = 10
# Softer mins when fitting on ~4 train games (still require full mins on test)
MIN_TYPE_N_TRAIN = 3
MIN_SLICE_N_TRAIN = 6
# Holdout gate: a published tip must beat simply calling the majority class,
# fire on its own, and catch at least one real instance of the pitch it claims.
HOLDOUT_BASELINE_MARGIN = 0.08
MIN_HOLDOUT_FIRES = 3
MIN_HOLDOUT_TYPE_N = 3
PITCHER_FEATURE_PREFIXES = ("glove", "wrist", "cheek", "pitchcom")
CATCHER_FEATURE_PREFIXES = ("catcher",)
FEATURE_PREFIXES = PITCHER_FEATURE_PREFIXES  # default for pitcher tips


def _feature_cols(df: pd.DataFrame, prefixes: tuple[str, ...] = FEATURE_PREFIXES) -> list[str]:
    return [c for c in df.columns if c.startswith(prefixes)]


def _best_one_vs_rest(
    df: pd.DataFrame,
    pitch_type: str,
    fcols: list[str],
    *,
    min_type_n: int = MIN_TYPE_N,
) -> dict[str, Any] | None:
    y = (df["pitch_type"] == pitch_type).to_numpy()
    n_pos = int(y.sum())
    n_neg = int((~y).sum())
    if n_pos < min_type_n or n_neg < min_type_n:
        return None
    best: dict[str, Any] | None = None
    for col in fcols:
        x = pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=float)
        # Drop NaNs before evaluating discrimination on available tracked pitches
        valid = ~np.isnan(x)
        if valid.sum() < 4 or y[valid].sum() < min_type_n or (~y[valid]).sum() < min_type_n:
            continue
        xv = x[valid]
        yv = y[valid]
        m_pos = float(np.mean(xv[yv]))
        m_neg = float(np.mean(xv[~yv]))
        if abs(m_pos - m_neg) < 1e-6:
            continue
        thr = (m_pos + m_neg) / 2.0
        high_is_pos = m_pos > m_neg
        pred = (xv >= thr) if high_is_pos else (xv < thr)
        acc = float((pred == yv).mean())
        fires = pred
        prec = float(yv[fires].mean()) if fires.any() else 0.0
        if best is None or acc > best["accuracy"]:
            best = {
                "feature": col,
                "threshold": thr,
                "accuracy": round(acc, 3),
                "precision": round(prec, 3),
                "high_means_type": bool(high_is_pos),
                "n_type": int(yv.sum()),
                "n_other": int((~yv).sum()),
                "baseline": round(float(yv.sum()) / max(len(yv), 1), 3),
            }
    return best


def _score_frozen_rule(
    df: pd.DataFrame,
    pitch_type: str,
    feature: str,
    threshold: float,
    high_means_type: bool,
    *,
    min_slice_n: int = MIN_SLICE_N,
    min_type_n: int = 2,
) -> dict[str, Any] | None:
    """Apply a train-fit tip rule to held-out pitches (per-pitch correct/incorrect)."""
    if feature not in df.columns or len(df) < 1:
        return None
    y = (df["pitch_type"] == pitch_type).to_numpy()
    x = pd.to_numeric(df[feature], errors="coerce").to_numpy(dtype=float)
    if np.isnan(x).all():
        return None
    pred = (x >= threshold) if high_means_type else (x < threshold)
    pred = np.where(np.isnan(x), False, pred)
    n = int(len(df))
    n_pos = int(y.sum())
    if n < min_slice_n or n_pos < min_type_n:
        return {
            "accuracy": None,
            "precision": None,
            "n": n,
            "n_type": n_pos,
            "status": "insufficient_n",
        }
    acc = float((pred == y).mean())
    fires = pred
    prec = float(y[fires].mean()) if fires.any() else 0.0
    # One-vs-rest cells are imbalanced, so raw accuracy alone can be met by a
    # rule that simply never fires. Report what it takes to tell those apart.
    majority = max(float(y.mean()), 1.0 - float(y.mean()))
    return {
        "accuracy": round(acc, 3),
        "precision": round(prec, 3),
        "n": n,
        "n_type": n_pos,
        "n_correct": int((pred == y).sum()),
        "n_fires": int(fires.sum()),
        "n_true_positive": int((y & pred).sum()),
        "majority_baseline": round(majority, 3),
        "status": "ok",
    }


def split_games_train_test(
    feat_df: pd.DataFrame,
    *,
    train_games: int = 4,
    test_games: int = 4,
) -> tuple[pd.DataFrame, pd.DataFrame, list, list]:
    """
    Temporal split: older games → quasi-train (fit thresholds), newer → test (validate).
    Aims for ~train_games / ~test_games when enough outings exist.
    """
    # A split that cannot be made at the game boundary must not be made at all.
    # Pitches inside one game share camera, park, lighting and whatever the
    # pitcher's stuff was that day, so validating across a pitch-level split
    # validates those artefacts instead of the tip. Returning empty frames leaves
    # the arm explicitly unvalidated rather than silently in-sample.
    empty = feat_df.iloc[0:0]
    if "game_pk" not in feat_df.columns or feat_df.empty:
        return empty, empty, [], []

    # Prefer chronological if game_date present
    if "game_date" in feat_df.columns:
        order = (
            feat_df[["game_pk", "game_date"]]
            .drop_duplicates("game_pk")
            .sort_values("game_date")["game_pk"]
            .astype(int)
            .tolist()
        )
    else:
        order = sorted(int(g) for g in feat_df["game_pk"].unique().tolist())

    n = len(order)
    if n < 2:
        # One outing: no holdout is possible. Previously this returned the same
        # game id as both train and test, which read as a populated split and
        # passed the holdout gate while being a pitch-level split.
        return empty, empty, [], []

    n_test = min(test_games, max(1, n // 2))
    n_train = min(train_games, n - n_test)
    if n_train < 1:
        n_train = n - n_test
    train_ids = order[:n_train]
    test_ids = order[n_train : n_train + n_test]
    # If leftover games, fold into train (more fit data)
    leftover = order[n_train + n_test :]
    train_ids = train_ids + leftover

    train_df = feat_df[feat_df["game_pk"].astype(int).isin(train_ids)].copy()
    test_df = feat_df[feat_df["game_pk"].astype(int).isin(test_ids)].copy()
    return train_df, test_df, train_ids, test_ids


def evaluate_situations_validated(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    *,
    floor: float = TIP_CONFIDENCE_FLOOR,
    feature_prefixes: tuple[str, ...] = PITCHER_FEATURE_PREFIXES,
    tip_kind: str = "pitcher",
    id_prefix: str = "disc",
    discover_floor: float | None = None,
) -> dict[str, Any]:
    """
    Fit tip thresholds on train games; score frozen rules on held-out test games.
    Publish only tips whose *test* accuracy clears `floor` (default 75%).
    `discover_floor` (default = floor) gates which rules are candidates from train fit.
    """
    if discover_floor is None:
        discover_floor = floor

    # Discover candidates on train (softer n — ~4 games)
    train_cov = evaluate_situations(
        train_df,
        floor=discover_floor,
        feature_prefixes=feature_prefixes,
        tip_kind=tip_kind,
        id_prefix=id_prefix,
        min_slice_n=MIN_SLICE_N_TRAIN,
        min_type_n=MIN_TYPE_N_TRAIN,
    )

    # Re-fit to capture threshold (evaluate_situations tips don't store thr — refit)
    fcols = _feature_cols(train_df, feature_prefixes)
    usable = []
    for c in fcols:
        s = pd.to_numeric(train_df[c], errors="coerce")
        if s.notna().sum() >= MIN_SLICE_N_TRAIN and float(s.std(ddof=0) or 0) > 1e-6:
            usable.append(c)
    fcols = usable

    validated: list[dict[str, Any]] = []
    candidates_failed: list[dict[str, Any]] = []

    for tip in train_cov["tips_ge_floor"]:
        runner = tip["context"][0] if tip.get("context") else None
        batter = tip["context"][1] if tip.get("context") and len(tip["context"]) > 1 else None
        pitch_type = tip.get("pitchType") or tip.get("predicts")
        delivery = delivery_of_situation(runner)
        train_slice = delivery_pure(
            train_df[(train_df["runner_bucket"] == runner) & (train_df["batter_tag"] == batter)],
            delivery,
        )
        test_slice = delivery_pure(
            test_df[(test_df["runner_bucket"] == runner) & (test_df["batter_tag"] == batter)],
            delivery,
        )
        # Prefer threshold stored on tip; else re-fit
        if tip.get("feature") and tip.get("threshold") is not None and tip.get("high_means_type") is not None:
            feat = tip["feature"]
            thr = float(tip["threshold"])
            high = bool(tip["high_means_type"])
            train_acc = float(tip["confidence"])
        else:
            fit = _best_one_vs_rest(
                train_slice, str(pitch_type), fcols, min_type_n=MIN_TYPE_N_TRAIN
            )
            if fit is None:
                continue
            feat = fit["feature"]
            thr = float(fit["threshold"])
            high = bool(fit["high_means_type"])
            train_acc = float(fit["accuracy"])
        scored = _score_frozen_rule(
            test_slice,
            str(pitch_type),
            feat,
            thr,
            high,
            # Score even thin holdout cells; publish gate is still ≥75% test accuracy
            min_slice_n=2,
            min_type_n=1,
        )
        row = {
            **tip,
            "feature": feat,
            "threshold": round(thr, 6),
            "high_means_type": high,
            "trainConfidence": train_acc,
            "trainN": tip.get("n"),
            "trainNType": tip.get("nType"),
            "validation": "game_holdout_tip",
            "trainGamesN": int(train_df["game_pk"].nunique()) if "game_pk" in train_df else None,
            "testGamesN": int(test_df["game_pk"].nunique()) if "game_pk" in test_df else None,
        }
        if scored is None or scored.get("status") != "ok" or scored.get("accuracy") is None:
            row["testConfidence"] = None
            row["testN"] = scored.get("n") if scored else 0
            row["status"] = "insufficient_test_n"
            row["confidence"] = tip["confidence"]  # keep train for inspection
            row["gates"] = {
                "tip_floor": floor,
                "clears_train_75": True,
                "clears_test_75": False,
                "validated": False,
            }
            candidates_failed.append(row)
            continue

        test_acc = float(scored["accuracy"])
        row["testConfidence"] = test_acc
        row["testPrecision"] = scored["precision"]
        row["testN"] = scored["n"]
        row["testNType"] = scored["n_type"]
        row["testNCorrect"] = scored.get("n_correct")
        row["testNFires"] = scored.get("n_fires")
        row["testNTruePositive"] = scored.get("n_true_positive")
        row["testMajorityBaseline"] = scored.get("majority_baseline")
        row["confidence"] = test_acc  # published confidence = held-out
        row["n"] = scored["n"]
        row["nType"] = scored["n_type"]

        # A tip has to beat calling the majority class, actually fire, and be
        # right when it fires. Accuracy alone lets a never-fires rule through.
        majority = float(scored.get("majority_baseline") or 0.0)
        clears_floor = test_acc >= floor
        beats_baseline = test_acc >= majority + HOLDOUT_BASELINE_MARGIN
        fires_enough = int(scored.get("n_fires") or 0) >= MIN_HOLDOUT_FIRES
        has_positives = int(scored["n_type"]) >= MIN_HOLDOUT_TYPE_N
        catches_any = int(scored.get("n_true_positive") or 0) >= 1
        clears = clears_floor and beats_baseline and fires_enough and has_positives and catches_any

        row["status"] = "active" if clears else "failed_holdout"
        row["gates"] = {
            "tip_floor": floor,
            "clears_train_75": True,
            "clears_test_75": clears_floor,
            "beats_majority_baseline": beats_baseline,
            "baseline_margin_required": HOLDOUT_BASELINE_MARGIN,
            "fires_enough": fires_enough,
            "has_positives": has_positives,
            "catches_any": catches_any,
            "validated": clears,
        }
        if clears:
            validated.append(row)
        else:
            candidates_failed.append(row)

    validated.sort(key=lambda t: (t["confidence"], t.get("testNType") or 0), reverse=True)

    return {
        "tip_floor": floor,
        "validation": "train_fit_test_games",
        "arsenal": train_cov["arsenal"],
        "arsenal_n": train_cov["arsenal_n"],
        "situations": train_cov["situations"],  # train discovery coverage
        "tips_ge_floor": validated,
        "n_tips_ge_floor": len(validated),
        "candidates_train": train_cov["n_tips_ge_floor"],
        "failed_holdout": candidates_failed,
        "n_failed_holdout": len(candidates_failed),
        "best_situation": train_cov.get("best_situation"),
    }

def _look_for(pitch_type: str, feat: str, high: bool, ctx_tags: list[str]) -> str:
    prefix = context_phrase(ctx_tags)
    pname = {
        "FF": "4-Seam Fastball",
        "SI": "2-Seam Sinker",
        "FC": "Cutter",
        "SL": "Slider",
        "ST": "Sweeper",
        "CU": "Curveball",
        "KC": "Knuckle Curve",
        "CV": "Curveball",
        "CH": "Changeup",
        "FS": "Splitter",
        "SPL": "Splitter",
        "KN": "Knuckleball",
        "SV": "Slurve",
        "OFF": "Offspeed",
    }.get(pitch_type, f"{pitch_type} pitch")

    body_map = {
        "glove_vs_belt_mean": (
            f"On {pname} ({pitch_type}), glove is anchored high across jersey chest letters during set pause vs low at belt buckle on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), glove sits 2 to 3 inches lower below belt seam before leg lift begins vs locked at mid-chest on rest of arsenal."
        ),
        "glove_vs_belt_std": (
            f"On {pname} ({pitch_type}), glove visibly micro-bobbles vertically at set position while securing grip vs motionless hands on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), hands lock into instant motionless set hold vs micro-adjustments on rest of arsenal."
        ),
        "glove_flare_mean": (
            f"On {pname} ({pitch_type}), glove pocket flares wide outward exposing inner laces vs tightly closed mitt parallel to torso on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), glove is clamped flat and tight against sternum vs flared rim on rest of arsenal."
        ),
        "glove_flare_std": (
            f"On {pname} ({pitch_type}), glove pocket flexes and expands during grip dig vs rigid angle on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), glove pocket angle is locked rigid from first touch vs flexing during grip dig on rest of arsenal."
        ),
        "wrist_speed_mean": (
            f"On {pname} ({pitch_type}), active wrist micro-movement is visible at glove collar vs motionless hands on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), hands and wrist remain completely quiet and still at set vs wrist micro-movement on rest of arsenal."
        ),
        "wrist_speed_p90": (
            f"On {pname} ({pitch_type}), a sharp late glove twitch occurs right as knee lift starts vs smooth continuous delivery on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), motion into leg lift is completely smooth without late hitch vs sharp late twitch on rest of arsenal."
        ),
        "cheek_motion_mean": (
            f"On {pname} ({pitch_type}), visible jaw clench / cheek tension occurs before coming set vs neutral relaxed face on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), face locks into immediate motionless stillness vs visible jaw/cheek motion on rest of arsenal."
        ),
        "cheek_motion_std": (
            f"On {pname} ({pitch_type}), variable facial muscle shifting occurs during sign receive vs steady facial set on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), facial set remains calm and steady vs variable tension on rest of arsenal."
        ),
        "pitchcom_tap_count": (
            f"On {pname} ({pitch_type}), pitcher executes 3+ deliberate PitchCom taps vs 1-2 quick taps on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), pitcher uses only 1 quick PitchCom tap before coming set vs multiple taps on rest of arsenal."
        ),
        "pitchcom_tap_rate": (
            f"On {pname} ({pitch_type}), PitchCom tap cadence is rapid and brisk vs slow deliberate cadence on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), PitchCom taps are slow and spaced out vs rapid cadence on rest of arsenal."
        ),
        "pitchcom_mean_isi": (
            f"On {pname} ({pitch_type}), wide pauses (>1.0s) occur between PitchCom presses vs tightly clustered taps on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), PitchCom taps occur in rapid back-to-back cluster vs wide pauses on rest of arsenal."
        ),
        "catcher_glove_x_mean": (
            f"On {pname} ({pitch_type}), catcher sets target 5+ inches wider to glove-side edge vs centered target on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), catcher shifts target toward arm-side border vs centered target on rest of arsenal."
        ),
        "catcher_glove_y_mean": (
            f"On {pname} ({pitch_type}), catcher sets mitt target high at chest level vs low below knees on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), catcher anchors target low below the knees vs chest-high target on rest of arsenal."
        ),
        "catcher_stance_mean": (
            f"On {pname} ({pitch_type}), catcher establishes a noticeably wider base stance vs narrow compact stance on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), catcher sets up with compact, narrow foot spread vs wide blocking base on rest of arsenal."
        ),
        "catcher_hip_y_mean": (
            f"On {pname} ({pitch_type}), catcher sets in a taller upright crouch vs deep one-knee crouch on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), catcher drops deep into a one-knee stance on dirt vs standard higher crouch on rest of arsenal."
        ),
        "catcher_glove_speed_mean": (
            f"On {pname} ({pitch_type}), catcher exhibits active pre-set glove movement vs static target on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), catcher holds quiet motionless target at set vs active movement on rest of arsenal."
        ),
        "catcher_glove_speed_p90": (
            f"On {pname} ({pitch_type}), catcher executes a sharp late glove repositioning before lift vs rock-still target on rest of arsenal."
            if high else
            f"On {pname} ({pitch_type}), catcher locks into early static target hold vs late adjustments on rest of arsenal."
        ),
    }

    body = body_map.get(feat, f"On {pname} ({pitch_type}), distinct visual variance observed on {feat.replace('_', ' ')} vs rest of arsenal.")
    text = (prefix + " " + body).strip() if prefix else body
    return text[0].upper() + text[1:] if text else text


def situation_key(runner_bucket: str, batter_tag: str) -> str:
    return f"{runner_bucket}|{batter_tag}"


def situation_label(runner_bucket: str, batter_tag: str) -> str:
    runners = {
        "none": "bases empty",
        "1b": "first only",
        "second_any": "any w/ runner on 2nd",
        "3b": "third only",
        "other": "other runner state",
    }.get(runner_bucket, runner_bucket)
    batter = {"lhh": "LHH", "rhh": "RHH"}.get(batter_tag, batter_tag or "?")
    return f"{runners}, {batter} up"


def delivery_of_situation(runner: str) -> str:
    """The delivery a situation is defined to be about: runners mean the set."""
    return "windup" if runner == "none" else "stretch"


def delivery_pure(df: "pd.DataFrame", delivery: str) -> "pd.DataFrame":
    """
    Restrict a situation slice to pitches actually thrown from its delivery.

    A situation like "runner on first, RHH up" is implicitly a stretch
    situation, and "bases empty" an implicitly windup one — but only
    implicitly. The base state is not the delivery: plenty of arms work
    exclusively from the stretch with the bases empty, and a few use a windup
    with a runner on third. Measured on Woo, the base-state assumption
    disagreed with what the pose track actually showed on 28% of classifiable
    pitches.

    That matters because stretch and windup differ mechanically on nearly every
    glove cue, so a slice containing both is a slice in which a pitch-type
    contrast is partly a delivery contrast. Where the track carries a read
    delivery (``delivery_type`` from window.actionable_window) it is used to
    make the slice pure. Where it does not, the slice is returned unchanged and
    the older base-state label — which is delivery-pure by construction, being
    a function of the base state — still holds.
    """
    if "delivery_type" not in df.columns:
        return df
    read = df["delivery_type"].astype(str).str.lower()
    # Pitches the window could not classify keep the situation's assumption
    # rather than being discarded: dropping them would bias the slice toward
    # clips the tracker happened to like.
    return df[(read == delivery) | (~read.isin(["stretch", "windup"]))]


# Primary situations the product cares about
SITUATION_GRID: list[tuple[str, str]] = [
    ("none", "lhh"),
    ("none", "rhh"),
    ("1b", "lhh"),
    ("1b", "rhh"),
    ("second_any", "lhh"),
    ("second_any", "rhh"),
    ("3b", "lhh"),
    ("3b", "rhh"),
]


def evaluate_situations(
    feat_df: pd.DataFrame,
    *,
    floor: float = TIP_CONFIDENCE_FLOOR,
    feature_prefixes: tuple[str, ...] = PITCHER_FEATURE_PREFIXES,
    tip_kind: str = "pitcher",
    id_prefix: str = "disc",
    min_slice_n: int = MIN_SLICE_N,
    min_type_n: int = MIN_TYPE_N,
) -> dict[str, Any]:
    """
    Returns arsenal coverage by situation + tip cards only for types clearing `floor`.
    tip_kind: 'pitcher' (presentation / PitchCom) or 'catcher' (setup target).
    """
    fcols = _feature_cols(feat_df, feature_prefixes)
    # Need at least one usable feature column with data
    usable = []
    min_feat_n = min(min_slice_n, 4)
    for c in fcols:
        s = pd.to_numeric(feat_df[c], errors="coerce")
        if s.notna().sum() >= min_feat_n and float(s.std(ddof=0) or 0) > 1e-6:
            usable.append(c)
    fcols = usable
    arsenal = [t for t, _ in Counter(feat_df["pitch_type"]).most_common()]
    situations: list[dict[str, Any]] = []
    tips: list[dict[str, Any]] = []

    for runner, batter in SITUATION_GRID:
        delivery = delivery_of_situation(runner)
        sliced = delivery_pure(
            feat_df[(feat_df["runner_bucket"] == runner) & (feat_df["batter_tag"] == batter)],
            delivery,
        )
        ctx = [runner, batter, delivery]

        types_present = [t for t in arsenal if int((sliced["pitch_type"] == t).sum()) >= min_type_n]
        discerned: list[dict[str, Any]] = []
        missed: list[dict[str, Any]] = []

        if len(sliced) < min_slice_n or len(types_present) < 2 or not fcols:
            situations.append(
                {
                    "id": situation_key(runner, batter),
                    "label": situation_label(runner, batter),
                    "runner_bucket": runner,
                    "batter_tag": batter,
                    "n": int(len(sliced)),
                    "arsenal_n": len(arsenal),
                    "types_tested": types_present,
                    "discernable_n": 0,
                    "discernable_types": [],
                    "coverage": f"0 of {len(arsenal)}",
                    "status": "insufficient_n",
                    "types": [],
                }
            )
            continue

        type_rows = []
        for t in arsenal:
            n_t = int((sliced["pitch_type"] == t).sum())
            row: dict[str, Any] = {
                "pitch_type": t,
                "n": n_t,
                "discernable": False,
                "accuracy": None,
                "feature": None,
            }
            if n_t < min_type_n:
                row["status"] = "insufficient_n"
                type_rows.append(row)
                continue
            best = _best_one_vs_rest(sliced, t, fcols, min_type_n=min_type_n)
            if best is None:
                row["status"] = "no_separation"
                type_rows.append(row)
                missed.append(row)
                continue
            row.update(
                {
                    "accuracy": best["accuracy"],
                    "precision": best["precision"],
                    "feature": best["feature"],
                    "threshold": best.get("threshold"),
                    "high_means_type": best.get("high_means_type"),
                    "baseline": best["baseline"],
                    "status": "ok",
                }
            )
            if best["accuracy"] >= floor:
                row["discernable"] = True
                discerned.append(row)
                tips.append(
                    {
                        "id": f"{id_prefix}-{runner}-{batter}-{t}-{best['feature']}",
                        "title": (
                            f"{t} via catcher setup [{situation_label(runner, batter)}]"
                            if tip_kind == "catcher"
                            else f"{t} discernable [{situation_label(runner, batter)}]"
                        ),
                        "angle": "CF",
                        "context": ctx,
                        "tipKind": tip_kind,
                        "stratum": {
                            "kind": f"situation_{tip_kind}",
                            "value": f"{runner}+{batter}+{t}",
                        },
                        "lookFor": _look_for(t, best["feature"], best["high_means_type"], ctx),
                        "predicts": t,
                        "confidence": best["accuracy"],
                        "precision": best["precision"],
                        "feature": best["feature"],
                        "threshold": best.get("threshold"),
                        "high_means_type": best.get("high_means_type"),
                        "n": int(len(sliced)),
                        "nType": best["n_type"],
                        "baseline": best["baseline"],
                        "lift": round(best["accuracy"] / max(best["baseline"], 1e-6), 2),
                        "status": "active" if best["accuracy"] >= floor else "watch",
                        "validation": "situation_one_vs_rest",
                        "modelScope": "per_pitcher" if tip_kind == "pitcher" else "catcher_setup",
                        "gates": {"tip_floor": floor, "clears_75": True},
                        "pitchType": t,
                        "situationId": situation_key(runner, batter),
                        "situationLabel": situation_label(runner, batter),
                    }
                )
            else:
                missed.append(row)
            type_rows.append(row)

        situations.append(
            {
                "id": situation_key(runner, batter),
                "label": situation_label(runner, batter),
                "runner_bucket": runner,
                "batter_tag": batter,
                "n": int(len(sliced)),
                "arsenal_n": len(arsenal),
                "types_tested": types_present,
                "discernable_n": len(discerned),
                "discernable_types": [d["pitch_type"] for d in discerned],
                "coverage": f"{len(discerned)} of {len(arsenal)}",
                "status": "ok",
                "types": type_rows,
            }
        )

    # Additional macro situations for discovery / sales tool prototype
    macro_grid: list[tuple[str, str, str, list[str]]] = [
        ("all", "all", "all situations", ["all situations"]),
        ("none", "all", "bases empty", ["bases empty", "windup"]),
        ("runners_on", "all", "runners on base", ["runners on", "stretch"]),
        ("all", "lhh", "vs lefties", ["vs lefties"]),
        ("all", "rhh", "vs righties", ["vs righties"]),
    ]

    for m_run, m_bat, m_label, m_ctx in macro_grid:
        if m_run == "all" and m_bat == "all":
            sliced = feat_df.copy()
        elif m_run == "none":
            sliced = feat_df[feat_df["runner_bucket"] == "none"]
        elif m_run == "runners_on":
            sliced = feat_df[feat_df["runner_bucket"] != "none"]
        elif m_bat == "lhh":
            sliced = feat_df[feat_df["batter_tag"] == "lhh"]
        elif m_bat == "rhh":
            sliced = feat_df[feat_df["batter_tag"] == "rhh"]
        else:
            sliced = feat_df.copy()

        if len(sliced) < min(min_slice_n, 6) or not fcols:
            continue

        for t in arsenal:
            n_t = int((sliced["pitch_type"] == t).sum())
            if n_t < 1 or n_t >= len(sliced):
                continue
            best = _best_one_vs_rest(sliced, t, fcols, min_type_n=1)
            if best and best["accuracy"] >= floor:
                tip_id = f"{id_prefix}-{m_run}-{m_bat}-{t}-{best['feature']}"
                # avoid duplicate if same pitch_type + feature already in tips
                if any(tip["predicts"] == t and tip["feature"] == best["feature"] for tip in tips):
                    continue
                tips.append(
                    {
                        "id": tip_id,
                        "title": (
                            f"{t} via Catcher Setup [{m_label}]"
                            if tip_kind == "catcher"
                            else f"{t} discernable [{m_label}]"
                        ),
                        "angle": "CF",
                        "context": m_ctx,
                        "tipKind": tip_kind,
                        "stratum": {
                            "kind": f"situation_{tip_kind}",
                            "value": f"{m_run}+{m_bat}+{t}",
                        },
                        "lookFor": _look_for(t, best["feature"], best["high_means_type"], m_ctx),
                        "predicts": t,
                        "confidence": best["accuracy"],
                        "precision": best["precision"],
                        "feature": best["feature"],
                        "threshold": best.get("threshold"),
                        "high_means_type": best.get("high_means_type"),
                        "n": int(len(sliced)),
                        "nType": best["n_type"],
                        "baseline": best["baseline"],
                        "lift": round(best["accuracy"] / max(best["baseline"], 1e-6), 2),
                        "status": "active",
                        "validation": "empirical_detection_75",
                        "modelScope": "per_pitcher" if tip_kind == "pitcher" else "catcher_setup",
                        "gates": {"tip_floor": floor, "clears_75": True},
                        "pitchType": t,
                        "situationId": f"{m_run}|{m_bat}",
                        "situationLabel": m_label,
                    }
                )

    # Mark tips that hold for both batter sides (same runner + pitch + feature)
    groups: dict[str, list[dict]] = {}
    for tip in tips:
        pref = f"{id_prefix}-"
        rest = tip["id"][len(pref) :] if tip["id"].startswith(pref) else tip["id"]
        parts = rest.split("-", 3)
        if len(parts) >= 4:
            runner, _batter, t, feat = parts
            groups.setdefault(f"{runner}|{t}|{feat}", []).append(tip)
    for group in groups.values():
        sides = sorted({t["context"][1] for t in group if len(t["context"]) > 1})
        if len(sides) >= 2:
            for tip in group:
                tip["alsoHoldsFor"] = [s for s in sides if s != tip["context"][1]]
                tip["sameTipBothHands"] = True

    tips.sort(key=lambda t: (t["confidence"], t["nType"]), reverse=True)

    return {
        "tip_floor": floor,
        "arsenal": arsenal,
        "arsenal_n": len(arsenal),
        "situations": situations,
        "tips_ge_floor": tips,
        "n_tips_ge_floor": len(tips),
        "best_situation": max(
            (s for s in situations if s["status"] == "ok"),
            key=lambda s: (s["discernable_n"], s["n"]),
            default=None,
        ),
    }
