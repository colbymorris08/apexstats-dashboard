"""
End-to-end PoC: MLB live playIds + Savant CF clips + MediaPipe tracks → tip cards.

Proof-of-concept on broadcast CF. Club delivery swaps clips for X1–X4 angles with
the same tracker schema and thresholds.

Tips are mined pooled and stratified by:
  runners (first only / any w/ 2nd / third only / empty),
  batter side (LHH / RHH),
  delivery (set/stretch vs windup).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from preflight.context import (  # noqa: E402
    TIP_STRATA,
    apply_runner_movements,
    batter_side_tag,
    context_phrase,
    context_tags,
    delivery_from_runners,
    runner_state,
    runner_test_bucket,
)
from preflight.discern import (  # noqa: E402
    CATCHER_FEATURE_PREFIXES,
    PITCHER_FEATURE_PREFIXES,
    evaluate_situations,
    evaluate_situations_validated,
    split_games_train_test,
)
from preflight.fetch_savant import download_play_clip  # noqa: E402
from preflight.quota_select import select as quota_select  # noqa: E402
from preflight.thresholds import (  # noqa: E402
    COUNT_GATES,
    TIP_CONFIDENCE_FLOOR,
    binary_ev_breakeven,
    confidence_tier,
    passes_gate,
    required_accuracy,
)
from preflight.track_pitcher import MAX_TRACK_FRAMES, track_clip  # noqa: E402
from preflight.window import actionable_window, preset_segment  # noqa: E402

UA = {"User-Agent": "PreflightCV/0.3"}
MIN_STRATUM_N = 6


def _mlbam(name: str, mlbam: int | None = None) -> int:
    if mlbam is not None:
        return int(mlbam)
    from pybaseball import playerid_lookup

    parts = name.strip().split()
    last, first = parts[-1], " ".join(parts[:-1])
    # Strip accents for lookup fallback
    import unicodedata

    def strip(s: str) -> str:
        return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

    ids = playerid_lookup(last, first).dropna(subset=["key_mlbam"])
    if ids.empty:
        ids = playerid_lookup(strip(last), strip(first)).dropna(subset=["key_mlbam"])
    if ids.empty:
        raise RuntimeError(f"No MLBAM id for {name}")
    return int(ids.iloc[0]["key_mlbam"])


def _recent_game_pks(mlbam: int, season: int, n_games: int = 6) -> list[int]:
    from pybaseball import statcast_pitcher

    df = statcast_pitcher(f"{season}-03-01", f"{season}-11-30", mlbam)
    if df is None or df.empty:
        raise RuntimeError("No Statcast rows")
    games = (
        df.dropna(subset=["game_pk"])
        .sort_values("game_date", ascending=False)["game_pk"]
        .astype(int)
        .drop_duplicates()
        .tolist()
    )
    return games[:n_games]


def _pitches_from_game(game_pk: int, pitcher_id: int) -> list[dict]:
    """Extract pitches with runner / batter-side / delivery context via base-state machine."""
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    js = requests.get(url, headers=UA, timeout=40).json()
    out: list[dict] = []
    bases: dict = {"1B": None, "2B": None, "3B": None}
    # Carried per pitch so downstream work can split chronologically: fit on the
    # earlier starts and validate on the most recent ones. A pitcher who is told
    # he is tipping will correct it, so a cue from April can be genuinely gone by
    # August, and game_pk alone does not order reliably.
    game_date = ((js.get("gameData") or {}).get("datetime") or {}).get("officialDate")

    for pl in js.get("liveData", {}).get("plays", {}).get("allPlays", []) or []:
        matchup = pl.get("matchup") or {}
        pit = (matchup.get("pitcher") or {}).get("id")
        bat_code = (matchup.get("batSide") or {}).get("code")
        on1, on2, on3 = bool(bases["1B"]), bool(bases["2B"]), bool(bases["3B"])
        delivery = delivery_from_runners(on1, on2, on3)
        tags = context_tags(on1=on1, on2=on2, on3=on3, bat_side=bat_code, delivery=delivery)

        for ev in pl.get("playEvents") or []:
            if not ev.get("isPitch"):
                continue
            pid = ev.get("playId")
            if not pid:
                continue
            if pit is not None and int(pit) != int(pitcher_id):
                continue
            pitch_data = ev.get("pitchData") or {}
            details = ev.get("details") or {}
            ptype = (details.get("type") or {}).get("code")
            count = ev.get("count") or {}
            out.append(
                {
                    "play_id": str(pid),
                    "game_pk": int(game_pk),
                    "game_date": game_date,
                    "pitch_type": str(ptype or ""),
                    "balls": int(count.get("balls") or 0),
                    "strikes": int(count.get("strikes") or 0),
                    "start_speed": pitch_data.get("startSpeed"),
                    "on_1b": on1,
                    "on_2b": on2,
                    "on_3b": on3,
                    "runner_exact": runner_state(on1, on2, on3),
                    "runner_bucket": runner_test_bucket(on1, on2, on3),
                    "bat_side": (bat_code or "").upper()[:1] or "",
                    "batter_tag": batter_side_tag(bat_code) or "",
                    "delivery": delivery,
                    "context_tags": tags,
                }
            )

        bases = apply_runner_movements(bases, pl.get("runners") or [])

    return [r for r in out if r["pitch_type"]]


def pitchcom_features(seg: pd.DataFrame) -> dict[str, float]:
    """
    PitchCom programming proxy, measured over the PRE-SET segment.

    Taking the sign, shaking it off and working the wrist device all happen on
    the rubber before the pitcher comes set, so these are computed on
    ``window.preset_segment`` rather than on the set-to-lift window where the
    glove and lift cues live. Keeping the two segments separate stops each from
    diluting the other: glove position during sign-taking says nothing about how
    he sets up, and tap cadence during the leg kick says nothing about
    programming.

    KNOWN LIMITATION — read before trusting these three numbers. ``wrist_speed``
    is written by track_pitcher as the frame-to-frame displacement of the GLOVE
    centroid, so this looks for local maxima in gross glove translation, not
    finger movement on a forearm device. Three measurements say it is not
    isolating discrete taps:
      * on phase-shuffled speed, which has no temporal structure left at all,
        it returns MORE "taps" than on real footage (3.88 vs 2.97 on Kelly);
      * 17-43% of detected peaks sit on a tracking-dropout re-acquisition,
        where the reported speed is a multi-frame gap, not motion;
      * the detection rate is flat from 5 to 120 frames before the set, i.e. it
        fires just as often in broadcast idle footage as on the rubber.
    Treat these as a glove-motion distribution summary, not a tap count. See
    pitchcom_validity_probe.py and preset_extent_probe.py.
    """
    speed = pd.to_numeric(seg.get("wrist_speed"), errors="coerce").fillna(0.0).to_numpy(dtype=float)
    thr = max(float(np.nanpercentile(speed, 75)) if len(speed) else 0.0, 0.015)
    raw_peaks = [
        i
        for i in range(1, len(speed) - 1)
        if speed[i] >= thr and speed[i] >= speed[i - 1] and speed[i] >= speed[i + 1]
    ]
    taps: list[int] = []
    for i in raw_peaks:
        if not taps or (i - taps[-1]) >= 3:  # debounce ~0.1s at 30fps
            taps.append(i)
    tap_count = float(len(taps))
    if "t_sec" in seg and len(seg) > 1:
        duration = max(float(seg["t_sec"].iloc[-1] - seg["t_sec"].iloc[0]), 1e-3)
    else:
        duration = max(len(seg) / 30.0, 1e-3)
    isi = np.diff(taps) if len(taps) >= 2 else np.array([])
    return {
        "pitchcom_tap_count": tap_count,
        "pitchcom_tap_rate": float(tap_count / duration),
        "pitchcom_mean_isi": float(np.mean(isi)) if len(isi) else 0.0,
    }


def window_features(pre: pd.DataFrame) -> dict[str, float]:
    """
    Summary stats over an already-clamped frame window.

    Missing measurements emit NaN, never 0.0. This function used to end with

        return {k: (0.0 if np.isnan(v) else v) for k, v in out.items()}

    and hand back a zero for any feature whose window held no usable data, plus a
    zero for every catcher feature when the column was absent from the track
    entirely. Zero is not a neutral placeholder here: it is a specific physical
    claim. ``glove_vs_belt_mean`` of 0.0 asserts the glove sat exactly at belt
    height, and ``catcher_glove_y_mean`` of 0.0 puts the catcher at the top edge
    of the frame. Those rows then flowed into discovery indistinguishable from
    real ones, which is the same failure mode as the retracted cues: a value that
    looks populated, passes a gate, and means nothing.

    Measured share of pitches that took the fabricated-zero path, over 511
    windows (cv/preflight/cue_audit.py): 3.3% of glove_vs_belt, 1.2% of
    wrist_speed, and 100% of the catcher features on the 251 tracks written
    before the catcher columns existed. Downstream is already NaN-safe — the
    discovery slices count with ``notna()`` and require a non-degenerate standard
    deviation — so a NaN drops the pitch from that one feature instead of
    inventing a reading for it.
    """

    def series(col: str) -> pd.Series:
        if col not in pre.columns:
            return pd.Series(dtype=float)
        return pd.to_numeric(pre[col], errors="coerce")

    def mean(col: str) -> float:
        return float(series(col).mean()) if len(series(col)) else float("nan")

    def sd(col: str) -> float:
        # No `or 0`: that idiom turned a legitimate zero-variance window and a
        # NaN into the same answer.
        s = series(col)
        return float(s.std(ddof=0)) if s.notna().sum() >= 2 else float("nan")

    def p90(col: str) -> float:
        s = series(col)
        return float(s.quantile(0.9)) if s.notna().any() else float("nan")

    return {
        "glove_vs_belt_mean": mean("glove_vs_belt_y"),
        "glove_vs_belt_std": sd("glove_vs_belt_y"),
        "glove_flare_mean": mean("glove_flare"),
        "glove_flare_std": sd("glove_flare"),
        "wrist_speed_mean": mean("wrist_speed"),
        "wrist_speed_p90": p90("wrist_speed"),
        "cheek_motion_mean": mean("cheek_motion"),
        "cheek_motion_std": sd("cheek_motion"),
        "catcher_glove_x_mean": mean("catcher_glove_x"),
        "catcher_glove_y_mean": mean("catcher_glove_y"),
        "catcher_stance_mean": mean("catcher_stance_width"),
        "catcher_hip_y_mean": mean("catcher_hip_y"),
        "catcher_glove_speed_mean": mean("catcher_glove_speed"),
        "catcher_glove_speed_p90": p90("catcher_glove_speed"),
    }


def _feature_vector(track_csv: Path) -> dict[str, Any]:
    df = pd.read_csv(track_csv)
    if len(df) < 5:
        return {}
    # Features may only see frames a hitter or baserunner could act on. That
    # region is measured in two disjoint segments rather than one wide window:
    #
    #   [pre-set]                    [set -> just past peak leg lift]
    #   PitchCom programming         coming set, set position, catcher setup,
    #   (pitchcom_* features)        glove/lift geometry (all other features)
    #
    # Both end before arm action, so both stay actionable. A pitch whose
    # boundary cannot be established is dropped, not guessed at.
    win = actionable_window(df)
    if not win.valid:
        return {}
    out: dict[str, Any] = dict(window_features(df.iloc[win.start : win.end]))

    seg = preset_segment(df, win)
    if seg is None:
        # No usable pre-set footage. Emit NaN rather than 0.0 so these pitches
        # are excluded from PitchCom comparisons instead of piling up at a
        # fake zero that would look like a real "no taps" reading.
        out.update({k: float("nan") for k in ("pitchcom_tap_count", "pitchcom_tap_rate", "pitchcom_mean_isi")})
        out["preset_n_frames"] = 0.0
    else:
        out.update(pitchcom_features(df.iloc[seg[0] : seg[1]]))
        out["preset_start_frame"] = float(seg[0])
        out["preset_n_frames"] = float(seg[1] - seg[0])

    out["window_end_frame"] = float(win.end)
    out["window_start_frame"] = float(win.start)
    out["window_n_frames"] = float(win.n_frames)
    out["window_break_method"] = win.method
    out["delivery_frame"] = float(win.delivery_frame) if win.delivery_frame is not None else float("nan")
    out["delivery_type"] = win.delivery_type
    return out


def _tip_text(feat: str, high: bool, pitch_a: str, pitch_b: str, ctx_tags: list[str]) -> str:
    prefix = context_phrase(ctx_tags)
    templates = {
        "glove_vs_belt_mean": (
            f"watch glove height vs the belt before separation — {'higher' if high else 'lower'} "
            f"glove more often precedes {pitch_a}; the other look more often precedes {pitch_b}."
        ),
        "glove_vs_belt_std": (
            f"watch how stable glove height stays at set — {'more bobble' if high else 'steadier height'} "
            f"leans {pitch_a}; the opposite leans {pitch_b}."
        ),
        "glove_flare_mean": (
            f"watch how far the glove sits off the torso midline — {'wider flare' if high else 'tighter glove'} "
            f"leans {pitch_a}; the opposite presentation leans {pitch_b}."
        ),
        "glove_flare_std": (
            f"watch whether glove width wanders before hand break — {'more flare variance' if high else 'locked flare'} "
            f"leans {pitch_a}; the opposite leans {pitch_b}."
        ),
        "wrist_speed_mean": (
            f"watch glove/hand stillness in the set window — {'more micro-motion' if high else 'quieter glove'} "
            f"leans {pitch_a}; the other pattern leans {pitch_b}."
        ),
        "wrist_speed_p90": (
            f"watch for a late glove twitch before separation — {'a sharper peak' if high else 'a flatter peak'} "
            f"leans {pitch_a}; the opposite leans {pitch_b}."
        ),
        "cheek_motion_mean": (
            f"from a face-visible angle, {'more cheek/jaw motion' if high else 'earlier facial stillness'} "
            f"leans {pitch_a}; the opposite leans {pitch_b}."
        ),
        "cheek_motion_std": (
            f"from a face-visible angle, {'more variable facial motion' if high else 'steadier facial set'} "
            f"leans {pitch_a}; the opposite leans {pitch_b}."
        ),
        "pitchcom_tap_count": (
            f"count PitchCom glove taps before separation — {'more taps' if high else 'fewer taps'} "
            f"leans {pitch_a}; the other pattern leans {pitch_b}."
        ),
        "pitchcom_tap_rate": (
            f"watch PitchCom tap cadence — {'faster tapping' if high else 'slower tapping'} "
            f"leans {pitch_a}; the opposite leans {pitch_b}."
        ),
        "pitchcom_mean_isi": (
            f"watch spacing between PitchCom taps — {'wider gaps' if high else 'tighter spacing'} "
            f"leans {pitch_a}; the opposite leans {pitch_b}."
        ),
    }
    body = templates.get(
        feat,
        f"feature {feat} separates {pitch_a} vs {pitch_b} in pre-release CV tracks.",
    )
    text = (prefix + body).strip()
    return text[0].upper() + text[1:] if text else text


def _delivery_col(feat_df: pd.DataFrame) -> str:
    """
    Column carrying the per-pitch delivery, preferring the one read off the pose
    track over the one inferred from the base state.

    ``delivery_type`` is what window.actionable_window saw on this pitch: a
    sustained quiet glove before the lift is a set, its absence is a windup.
    ``delivery`` is the older inference that runners mean the stretch, which is
    wrong for the many arms that work from the stretch with the bases empty.
    """
    if "delivery_type" in feat_df.columns:
        return "delivery_type"
    return "delivery"


def _slice_df(feat_df: pd.DataFrame, kind: str, value: str | None) -> pd.DataFrame:
    if kind == "all" or value is None:
        return feat_df
    if kind == "runner":
        return feat_df[feat_df["runner_bucket"] == value]
    if kind == "batter":
        return feat_df[feat_df["batter_tag"] == value]
    if kind == "delivery":
        return feat_df[feat_df[_delivery_col(feat_df)] == value]
    return feat_df.iloc[0:0]


def _mine_slice(
    sub_all: pd.DataFrame,
    *,
    holdout_acc: float,
    stratum_kind: str,
    stratum_value: str | None,
    ctx_tags: list[str],
    tip_id_prefix: str,
) -> list[dict]:
    tips: list[dict] = []
    # Stretch and windup are different deliveries, not different looks, and
    # pitchers throw different mixes from each. A pitch-type contrast spanning
    # both is partly a delivery contrast, so it can report the mechanical
    # signature of the stretch as a tip. Every caller must slice to one
    # delivery first; this refuses the mistake rather than reporting it.
    if len(sub_all):
        kinds = set(sub_all[_delivery_col(sub_all)].dropna().astype(str).str.lower().unique())
        if len(kinds & {"stretch", "windup"}) > 1:
            raise ValueError(
                f"cross-delivery slice passed to _mine_slice ({sorted(kinds)}); "
                "pitch-type contrasts must be mined inside one delivery"
            )
    if len(sub_all) < MIN_STRATUM_N or sub_all["pitch_type"].nunique() < 2:
        return tips
    top2 = [t for t, _ in Counter(sub_all["pitch_type"]).most_common(2)]
    a, b = top2[0], top2[1]
    sub = sub_all[sub_all["pitch_type"].isin([a, b])]
    if len(sub) < MIN_STRATUM_N:
        return tips
    base_rate = float(sub_all["pitch_type"].value_counts(normalize=True).iloc[0])
    feature_cols = [c for c in sub.columns if c.startswith(("glove", "wrist", "cheek", "pitchcom"))]
    for col in feature_cols:
        ma = sub.loc[sub["pitch_type"] == a, col].mean()
        mb = sub.loc[sub["pitch_type"] == b, col].mean()
        if np.isnan(ma) or np.isnan(mb) or abs(ma - mb) < 1e-4:
            continue
        high_is_a = ma > mb
        thr = (ma + mb) / 2.0
        pred = np.where(sub[col] >= thr, a if high_is_a else b, b if high_is_a else a)
        acc = float((pred == sub["pitch_type"].to_numpy()).mean())
        early_ok = passes_gate(acc, base_rate, 0, 0)
        late_ok = passes_gate(acc, base_rate, 1, 2)
        if not early_ok and not late_ok:
            continue
        title_ctx = "" if stratum_kind == "all" else f" [{stratum_value}]"
        tips.append(
            {
                "id": f"{tip_id_prefix}-{col}-{a}-{b}",
                "title": f"{col.replace('_', ' ')} → {a} vs {b}{title_ctx}",
                "angle": "CF",
                "context": ctx_tags,
                "stratum": {"kind": stratum_kind, "value": stratum_value or "all"},
                "lookFor": _tip_text(col, high_is_a, a, b, ctx_tags),
                "predicts": f"{a} vs {b}",
                "confidence": round(acc, 3),
                "n": int(len(sub)),
                "baseline": round(base_rate, 3),
                "lift": round(acc / max(base_rate, 1e-6), 2),
                "status": "poc",
                "validation": "game_holdout_poc",
                "modelScope": "per_pitcher",
                "gates": {
                    "early": early_ok,
                    "two_strike": late_ok,
                    "early_need": round(required_accuracy(base_rate, 0, 0), 3),
                    "two_strike_need": round(required_accuracy(base_rate, 1, 2), 3),
                },
                "holdout_model_acc": round(holdout_acc, 3),
            }
        )
    return tips


def mine_tips(feat_df: pd.DataFrame, holdout_acc: float) -> list[dict]:
    """
    Mine situational tips (runners / LHH-RHH), always inside one delivery.

    Delivery is the outer loop rather than one stratum among many. The former
    pooled "all" stratum and the batter-only strata both spanned stretch and
    windup, so a pitcher whose mix shifts with runners on — most of them —
    could produce a tip that was really the stretch. Every slice below is
    delivery-pure, and ``_mine_slice`` rejects one that is not.
    """
    tips: list[dict] = []
    dcol = _delivery_col(feat_df)
    for delivery in ("stretch", "windup"):
        dframe = feat_df[feat_df[dcol].astype(str).str.lower() == delivery]
        if dframe.empty:
            continue
        for kind, value in TIP_STRATA:
            if kind == "delivery":
                continue  # the delivery loop already is this stratum
            sliced = _slice_df(dframe, kind, value)
            if kind == "all":
                # Applies across situations WITHIN this delivery, so the
                # delivery is part of the context rather than dropped.
                ctx: list[str] = [delivery]
                prefix = f"auto-{delivery}"
            else:
                ctx = list(dict.fromkeys([value, delivery])) if value else [delivery]
                prefix = f"auto-{delivery}-{kind}-{value}"
            tips.extend(
                _mine_slice(
                    sliced,
                    holdout_acc=holdout_acc,
                    stratum_kind=kind if kind != "all" else "delivery",
                    stratum_value=value if kind != "all" else delivery,
                    ctx_tags=ctx,
                    tip_id_prefix=prefix,
                )
            )

    # Cross strata when sample allows: runner x batter, inside one delivery.
    seen_cross: set[str] = set()
    for delivery in ("stretch", "windup"):
        dframe = feat_df[feat_df[dcol].astype(str).str.lower() == delivery]
        if dframe.empty:
            continue
        for rb in ("none", "1b", "second_any", "3b"):
            for bt in ("lhh", "rhh"):
                key = f"{delivery}-{rb}-{bt}"
                if key in seen_cross:
                    continue
                seen_cross.add(key)
                sliced = dframe[(dframe["runner_bucket"] == rb) & (dframe["batter_tag"] == bt)]
                tips.extend(
                    _mine_slice(
                        sliced,
                        holdout_acc=holdout_acc,
                        stratum_kind="runner_batter",
                        stratum_value=f"{rb}+{bt}+{delivery}",
                        ctx_tags=list(dict.fromkeys([rb, bt, delivery])),
                        tip_id_prefix=f"auto-{delivery}-runner_batter-{rb}-{bt}",
                    )
                )

    tips.sort(key=lambda t: (t["confidence"], t["n"]), reverse=True)
    # Keep best tips overall but ensure situational diversity
    out: list[dict] = []
    by_stratum: Counter = Counter()
    for t in tips:
        sk = f"{t['stratum']['kind']}:{t['stratum']['value']}"
        broad = t["stratum"]["kind"] == "delivery"  # the whole delivery, no other filter
        if by_stratum[sk] >= (6 if broad else 3):
            continue
        by_stratum[sk] += 1
        out.append(t)
        if len(out) >= 24:
            break
    return out


def _context_coverage(feat_df: pd.DataFrame) -> dict:
    return {
        "runner_bucket": feat_df["runner_bucket"].value_counts().to_dict() if "runner_bucket" in feat_df else {},
        "batter_tag": feat_df["batter_tag"].value_counts().to_dict() if "batter_tag" in feat_df else {},
        "delivery": feat_df["delivery"].value_counts().to_dict() if "delivery" in feat_df else {},
        "runner_exact": feat_df["runner_exact"].value_counts().to_dict() if "runner_exact" in feat_df else {},
    }


def enrich_features_from_catalog(feat_df: pd.DataFrame, catalog: list[dict]) -> pd.DataFrame:
    """Join live-feed context onto already-tracked feature rows by play_id."""
    by_id = {r["play_id"]: r for r in catalog}
    rows = []
    for _, row in feat_df.iterrows():
        d = row.to_dict()
        meta = by_id.get(str(d.get("play_id")), {})
        if meta:
            for k in (
                "on_1b",
                "on_2b",
                "on_3b",
                "runner_exact",
                "runner_bucket",
                "bat_side",
                "batter_tag",
                "delivery",
                "context_tags",
            ):
                d[k] = meta.get(k, d.get(k))
        else:
            on1 = bool(d.get("on_1b", False))
            on2 = bool(d.get("on_2b", False))
            on3 = bool(d.get("on_3b", False))
            d.setdefault("runner_exact", runner_state(on1, on2, on3))
            d.setdefault("runner_bucket", runner_test_bucket(on1, on2, on3))
            d.setdefault("delivery", delivery_from_runners(on1, on2, on3))
            d.setdefault("batter_tag", batter_side_tag(d.get("bat_side")) or "")
            d.setdefault(
                "context_tags",
                context_tags(
                    on1=on1,
                    on2=on2,
                    on3=on3,
                    bat_side=d.get("bat_side"),
                    delivery=d.get("delivery"),
                ),
            )
        rows.append(d)
    return pd.DataFrame(rows)


def _windowed_play_ids(feat_path: Path, tracks_dir: Path) -> set[str]:
    """
    Play ids already tracked AND carrying a usable actionable window.

    A track with no window contributes nothing to a cell, so it must not count
    towards the cell's quota. Falls back to the empty set when no features exist
    yet, which makes a fresh arm fetch its full quota.
    """
    if not feat_path.is_file():
        return set()
    try:
        df = pd.read_csv(feat_path)
    except Exception:
        return set()
    if "play_id" not in df.columns or "delivery_type" not in df.columns:
        return set()
    ok = df[df["delivery_type"].notna()]
    return {str(p) for p in ok["play_id"].tolist() if (tracks_dir / f"{p}_tracks.csv").is_file()}


def run_poc(
    pitcher: str,
    season: int,
    sample: int,
    work: Path,
    *,
    remine_only: bool = False,
    games: int | None = None,
    quota: bool = False,
    mlbam: int | None = None,
) -> dict:
    """
    If games is set, take all pitches from the last `games` outings (5-game scale mode).
    Otherwise sample up to `sample` pitches mixed across games/context.
    """
    work.mkdir(parents=True, exist_ok=True)
    clips_dir = work / "clips"
    tracks_dir = work / "tracks"
    clips_dir.mkdir(exist_ok=True)
    tracks_dir.mkdir(exist_ok=True)

    print(f"Resolving {pitcher}…")
    mlbam_id = _mlbam(pitcher, mlbam)
    # Quota mode needs a catalog wide enough to cover the recency window before
    # trimming to it. Building the catalog is metadata only — one game-feed
    # request each, no video — so spanning a few extra starts is nearly free and
    # is what lets cells be filled without downloading whole games.
    n_games = 12 if quota else (int(games) if games else 8)
    game_list = _recent_game_pks(mlbam_id, season, n_games=n_games)
    print(f"MLBAM {mlbam_id}; recent games {game_list}")

    catalog: list[dict] = []
    for gpk in game_list:
        catalog.extend(_pitches_from_game(gpk, mlbam_id))
    print(f"Catalog pitches with playId: {len(catalog)}")
    if not catalog:
        raise RuntimeError("No pitches with playId found")

    feat_path = work / "features.csv"
    if remine_only and feat_path.is_file():
        feat_df = enrich_features_from_catalog(pd.read_csv(feat_path), catalog)
        # Recompute PitchCom features from existing tracks when possible
        rebuilt = []
        for _, row in feat_df.iterrows():
            d = row.to_dict()
            play_id = str(d.get("play_id") or "")
            track_csv = tracks_dir / f"{play_id}_tracks.csv"
            if track_csv.is_file():
                feats = _feature_vector(track_csv)
                if feats:
                    d.update(feats)
            rebuilt.append(d)
        feat_df = pd.DataFrame(rebuilt)
        print(f"Remine-only: enriched {len(feat_df)} rows (PitchCom features refreshed)")
    else:
        if quota:
            # Quota mode: fetch a per-cell target instead of whole games. Pitches
            # already tracked count towards a cell's quota, so a partially
            # covered arm is topped up rather than re-fetched.
            # Credit a cell only for pitches that produced a VALID WINDOW, not
            # merely a track file. A third of tracks yield no window, so counting
            # tracks would have declared Hughes' cells full at 32 apiece while
            # cell_coverage found one testable cell on the same arm — the fetcher
            # would skip exactly the arms that most need topping up.
            already = _windowed_play_ids(feat_path, tracks_dir)
            selected, qreport = quota_select(catalog, already_tracked=already)
            (work / "quota_selection.json").write_text(json.dumps(qreport, indent=2))
            print(
                f"Quota mode: {qreport['n_within_recency']}/{qreport['n_catalog']} pitches "
                f"within {qreport['recency_days']}d; "
                f"{qreport['n_cells_usable']}/{qreport['n_cells']} cells usable; "
                f"fetching {len(selected)} (already tracked counted towards quota)"
            )
            for name, c in qreport["cells"].items():
                mark = "usable" if c["usable"] else f"UNUSABLE ({c['shortfall_reason']})"
                print(
                    f"  {name:<32} avail={c['n_available']:<4} take={c['n_selected']:<3} "
                    f"have={c['n_already_tracked']:<3} fetch={c['n_to_fetch']:<3} "
                    f"games={c['n_distinct_games']:<3} {mark}"
                )
        elif games:
            # Full last-N-games mode
            selected = list(catalog)
            print(f"Games mode: tracking all {len(selected)} pitches from last {games} games")
        else:
            # Prefer mix of types, games, AND context strata
            by_game: dict[int, list] = {}
            for row in catalog:
                by_game.setdefault(int(row["game_pk"]), []).append(row)
            selected = []
            seen_types: Counter = Counter()
            seen_ctx: Counter = Counter()
            game_keys = list(by_game.keys())
            gi = 0

            def ctx_key(r: dict) -> str:
                return f"{r.get('runner_bucket')}|{r.get('batter_tag')}|{r.get('delivery')}"

            while len(selected) < sample and any(by_game.values()):
                g = game_keys[gi % len(game_keys)]
                gi += 1
                bucket = by_game.get(g) or []
                if not bucket:
                    continue
                bucket.sort(
                    key=lambda r: (
                        seen_types[r["pitch_type"]],
                        seen_ctx[ctx_key(r)],
                        r["play_id"],
                    )
                )
                pick = bucket.pop(0)
                selected.append(pick)
                seen_types[pick["pitch_type"]] += 1
                seen_ctx[ctx_key(pick)] += 1
                if not bucket:
                    by_game.pop(g, None)
                    game_keys = list(by_game.keys()) or game_keys

        # Resume: skip play_ids already in features.csv
        done_ids: set[str] = set()
        prior_rows: list[dict] = []
        if feat_path.is_file():
            prior = pd.read_csv(feat_path)
            if "play_id" in prior.columns:
                done_ids = set(prior["play_id"].astype(str))
                prior_rows = prior.to_dict(orient="records")
                print(f"Resuming: {len(done_ids)} pitches already featured")

        rows = list(prior_rows)
        target = len(selected)
        for r in selected:
            play_id = r["play_id"]
            if play_id in done_ids:
                continue
            try:
                clip = download_play_clip(play_id, clips_dir)
                track = track_clip(clip, tracks_dir, camera_id="CF", max_frames=MAX_TRACK_FRAMES)
                feats = _feature_vector(track)
                if not feats:
                    continue
                feats.update(
                    {
                        "play_id": play_id,
                        "pitch_type": r["pitch_type"],
                        "balls": r["balls"],
                        "strikes": r["strikes"],
                        "game_pk": r["game_pk"],
                        "game_date": r.get("game_date"),
                        "pitcher_name": pitcher,
                        "on_1b": r["on_1b"],
                        "on_2b": r["on_2b"],
                        "on_3b": r["on_3b"],
                        "runner_exact": r["runner_exact"],
                        "runner_bucket": r["runner_bucket"],
                        "bat_side": r["bat_side"],
                        "batter_tag": r["batter_tag"],
                        "delivery": r["delivery"],
                        "context_tags": r["context_tags"],
                    }
                )
                rows.append(feats)
                done_ids.add(play_id)
                print(
                    f"  [{len(rows)}/{target}] {play_id[:8]}… → {r['pitch_type']} "
                    f"[{r['runner_bucket']}/{r['batter_tag']}/{r['delivery']}] "
                    f"taps={feats.get('pitchcom_tap_count', 0):.0f}"
                )
                # checkpoint
                if len(rows) % 10 == 0:
                    pd.DataFrame(rows).assign(
                        context_tags=lambda d: d["context_tags"].apply(
                            lambda x: "|".join(x) if isinstance(x, list) else (x or "")
                        )
                    ).to_csv(feat_path, index=False)
                time.sleep(0.2)
            except Exception as e:
                print(f"  skip {play_id}: {e}")

        if len(rows) < 8:
            raise RuntimeError(f"Only {len(rows)} tracked pitches; need more successful downloads")
        feat_df = pd.DataFrame(rows)

    # Serialize context_tags for CSV
    feat_out = feat_df.copy()
    if "context_tags" in feat_out.columns:
        feat_out["context_tags"] = feat_out["context_tags"].apply(
            lambda x: "|".join(x) if isinstance(x, list) else (x or "")
        )
    feat_out.to_csv(work / "features.csv", index=False)

    # Restore list form for mining
    if feat_df["context_tags"].dtype == object:
        feat_df = feat_df.copy()
        feat_df["context_tags"] = feat_df["context_tags"].apply(
            lambda x: x if isinstance(x, list) else ([t for t in str(x).split("|") if t] if pd.notna(x) else [])
        )

    games_u = sorted(feat_df["game_pk"].unique().tolist())
    if len(games_u) >= 2:
        test = feat_df[feat_df["game_pk"] == games_u[0]]
        train = feat_df[feat_df["game_pk"] != games_u[0]]
    else:
        mid = len(feat_df) // 2
        train, test = feat_df.iloc[:mid], feat_df.iloc[mid:]

    base_rate = float(feat_df["pitch_type"].value_counts(normalize=True).iloc[0])
    fcols = [c for c in feat_df.columns if c.startswith(("glove", "wrist", "cheek", "pitchcom"))]
    holdout_acc = 0.0
    if len(train) and len(test) and fcols:
        means = train.groupby("pitch_type")[fcols].mean()
        preds = []
        for _, row in test.iterrows():
            vec = row[fcols].to_numpy(dtype=float)
            best_t, best_d = None, 1e18
            for t, mrow in means.iterrows():
                d = float(np.nansum((vec - mrow.to_numpy(dtype=float)) ** 2))
                if d < best_d:
                    best_d, best_t = d, t
            preds.append(best_t)
        holdout_acc = float(np.mean([p == y for p, y in zip(preds, test["pitch_type"])]))

    tips = mine_tips(feat_df, holdout_acc)
    pitcher_cov = evaluate_situations(
        feat_df,
        floor=TIP_CONFIDENCE_FLOOR,
        feature_prefixes=PITCHER_FEATURE_PREFIXES,
        tip_kind="pitcher",
        id_prefix="disc",
    )
    catcher_cov = evaluate_situations(
        feat_df,
        floor=TIP_CONFIDENCE_FLOOR,
        feature_prefixes=CATCHER_FEATURE_PREFIXES,
        tip_kind="catcher",
        id_prefix="catch",
    )
    published_tips = pitcher_cov["tips_ge_floor"]
    catcher_tips_75 = catcher_cov["tips_ge_floor"]
    train_ids, test_ids = [], []
    train_df, test_df = feat_df, feat_df
    ctx_cov = _context_coverage(feat_df)
    report = {
        "pitcher": pitcher,
        "season": season,
        "n_tracked": int(len(feat_df)),
        "n_games": int(feat_df["game_pk"].nunique()),
        "tip_split": {
            "protocol": "train_fit_4_test_holdout_4",
            "train_games": train_ids,
            "test_games": test_ids,
            "n_train_pitches": int(len(train_df)),
            "n_test_pitches": int(len(test_df)),
            "note": "Thresholds from train games; published tip confidence = per-pitch accuracy on held-out test games.",
        },
        "pitch_mix": feat_df["pitch_type"].value_counts(normalize=True).round(3).to_dict(),
        "base_rate": round(base_rate, 3),
        "holdout_accuracy": round(holdout_acc, 3),
        "tier": confidence_tier(holdout_acc),
        "tip_floor": TIP_CONFIDENCE_FLOOR,
        "floor_package": "C_strict_club",
        "ev_breakeven_example": round(binary_ev_breakeven(0.400, 0.000, 0.200), 3),
        "count_gates": {
            k: {"abs_floor": g.abs_floor, "margin": g.base_rate_margin, "note": g.note}
            for k, g in COUNT_GATES.items()
        },
        "required_early": round(required_accuracy(base_rate, 0, 0), 3),
        "required_two_strike": round(required_accuracy(base_rate, 1, 2), 3),
        "context_coverage": ctx_cov,
        "situation_coverage": {
            "arsenal": pitcher_cov["arsenal"],
            "arsenal_n": pitcher_cov["arsenal_n"],
            "tip_floor": pitcher_cov["tip_floor"],
            "validation": pitcher_cov.get("validation"),
            "n_tips_ge_floor": pitcher_cov["n_tips_ge_floor"],
            "candidates_train": pitcher_cov.get("candidates_train"),
            "n_failed_holdout": pitcher_cov.get("n_failed_holdout"),
            "best_situation": pitcher_cov["best_situation"],
            "situations": pitcher_cov["situations"],
        },
        "catcher_coverage": {
            "arsenal": catcher_cov["arsenal"],
            "arsenal_n": catcher_cov["arsenal_n"],
            "tip_floor": catcher_cov["tip_floor"],
            "validation": catcher_cov.get("validation"),
            "n_tips_ge_floor": catcher_cov["n_tips_ge_floor"],
            "candidates_train": catcher_cov.get("candidates_train"),
            "n_failed_holdout": catcher_cov.get("n_failed_holdout"),
            "best_situation": catcher_cov["best_situation"],
            "situations": catcher_cov["situations"],
        },
        "discernable_summary": {
            s["id"]: {
                "label": s["label"],
                "coverage": s["coverage"],
                "discernable_types": s["discernable_types"],
                "n": s["n"],
            }
            for s in pitcher_cov["situations"]
        },
        "poc": True,
        "camera": "CF_savant_proof_of_concept",
        "tips": published_tips,
        "catcherTips": catcher_tips_75,
        "exploratory_tips": tips[:12],
        "failed_holdout_tips": pitcher_cov.get("failed_holdout") or [],
        "pitchcom_enabled": True,
    }
    (work / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in report if k not in {"tips", "catcherTips", "exploratory_tips", "situation_coverage", "catcher_coverage", "failed_holdout_tips"}}, indent=2))
    print(
        f"Tip split: {len(train_ids)} train games / {len(test_ids)} test games "
        f"({len(train_df)} / {len(test_df)} pitches)"
    )
    print(
        f"Pitcher tips validated ≥{TIP_CONFIDENCE_FLOOR:.0%} on test: {len(published_tips)} "
        f"(train candidates {pitcher_cov.get('candidates_train')}, "
        f"failed holdout {pitcher_cov.get('n_failed_holdout')})"
    )
    print(
        f"Catcher tips validated ≥{TIP_CONFIDENCE_FLOOR:.0%} on test: {len(catcher_tips_75)} "
        f"(train candidates {catcher_cov.get('candidates_train')})"
    )
    for s in pitcher_cov["situations"]:
        print(f"  P {s['label']}: {s['coverage']} {s['discernable_types']}")
    for s in catcher_cov["situations"]:
        if s["discernable_n"]:
            print(f"  C {s['label']}: {s['coverage']} {s['discernable_types']}")
    for t in published_tips[:6]:
        tc = t.get("trainConfidence")
        print(
            f"  - test {t['confidence']:.0%}"
            + (f" (train {tc:.0%})" if tc is not None else "")
            + f" {t['title']}"
        )
    for t in catcher_tips_75[:4]:
        print(f"  - catcher test {t['confidence']:.0%} {t['title']}")
    return report


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pitcher", default="Logan Webb")
    p.add_argument("--season", type=int, default=2026)
    p.add_argument("--sample", type=int, default=12)
    p.add_argument(
        "--games",
        type=int,
        default=None,
        help="If set, track ALL pitches from the last N games (overrides --sample mix)",
    )
    p.add_argument("--work", type=Path, default=Path(__file__).resolve().parents[1] / "runs" / "poc")
    p.add_argument(
        "--quota",
        action="store_true",
        help="Fill a per-cell quota (situation x pitch type) instead of tracking whole games",
    )
    p.add_argument(
        "--remine-only",
        action="store_true",
        help="Skip download/track; join context onto existing features.csv and remine tips",
    )
    args = p.parse_args()
    run_poc(
        args.pitcher,
        args.season,
        args.sample,
        args.work,
        remine_only=args.remine_only,
        games=args.games,
        quota=args.quota,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
