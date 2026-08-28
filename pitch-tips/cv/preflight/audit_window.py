"""
Re-derive tips for completed runs under the corrected actionable window.

Rebuilds per-pitch features from the cached per-frame tracks in
``runs/<run>/tracks/`` — no video re-tracking — and runs the same validated tip
protocol used by ``run_poc``. Writes ``report_actionable.json`` and
``features_actionable.csv`` next to the originals so the before/after stays
auditable; the original ``report.json`` is never modified.

The legacy fixed 55%-of-clip window is scored alongside it so the tip-count delta
is measured with identical code on identical pitches.

  python cv/preflight/audit_window.py --runs brandon_pfaadt_poc drew_thorpe_poc
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from preflight.discern import (  # noqa: E402
    CATCHER_FEATURE_PREFIXES,
    PITCHER_FEATURE_PREFIXES,
    evaluate_situations,
    evaluate_situations_validated,
    split_games_train_test,
)
from preflight.run_poc import window_features  # noqa: E402
from preflight.thresholds import TIP_CONFIDENCE_FLOOR  # noqa: E402
from preflight.window import actionable_window  # noqa: E402

CONTEXT_COLS = (
    "play_id",
    "pitch_type",
    "game_pk",
    "balls",
    "strikes",
    "on_1b",
    "on_2b",
    "on_3b",
    "runner_exact",
    "runner_bucket",
    "bat_side",
    "batter_tag",
    "delivery",
    "context_tags",
    "pitcher_name",
)


def _legacy_slice(df: pd.DataFrame) -> pd.DataFrame:
    """The window this code used before the fix: a fixed 55% of clip frames."""
    return df.iloc[: max(5, int(len(df) * 0.55))]


def rebuild(run_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    feat_path = run_dir / "features.csv"
    tracks_dir = run_dir / "tracks"
    if not feat_path.is_file():
        raise RuntimeError(f"{run_dir.name}: no features.csv")

    base = pd.read_csv(feat_path)
    keep = [c for c in CONTEXT_COLS if c in base.columns]

    new_rows: list[dict] = []
    old_rows: list[dict] = []
    stats = {"pitches": 0, "no_track": 0, "dropped_unbounded": 0, "methods": {}}

    for _, row in base.iterrows():
        ctx = {c: row[c] for c in keep}
        play_id = str(row.get("play_id") or "")
        track_csv = tracks_dir / f"{play_id}_tracks.csv"
        if not track_csv.is_file():
            stats["no_track"] += 1
            continue
        df = pd.read_csv(track_csv)
        if len(df) < 5:
            stats["no_track"] += 1
            continue
        stats["pitches"] += 1

        old_rows.append({**ctx, **window_features(_legacy_slice(df))})

        win = actionable_window(df)
        stats["methods"][win.method] = stats["methods"].get(win.method, 0) + 1
        if not win.valid:
            stats["dropped_unbounded"] += 1
            continue
        new_rows.append(
            {
                **ctx,
                **window_features(df.iloc[win.start : win.end]),
                "window_end_frame": float(win.end),
                "window_n_frames": float(win.n_frames),
                "window_break_method": win.method,
            }
        )

    return pd.DataFrame(old_rows), pd.DataFrame(new_rows), stats


def score(feat_df: pd.DataFrame) -> dict:
    """Same train-fit / test-holdout tip protocol run_poc publishes from."""
    if feat_df.empty:
        return {"pitcher_tips": [], "catcher_tips": [], "n_pitches": 0}
    train_df, test_df, train_ids, test_ids = split_games_train_test(
        feat_df, train_games=4, test_games=4
    )
    pitcher = evaluate_situations_validated(
        train_df,
        test_df,
        floor=TIP_CONFIDENCE_FLOOR,
        feature_prefixes=PITCHER_FEATURE_PREFIXES,
        tip_kind="pitcher",
        id_prefix="disc",
    )
    catcher = evaluate_situations_validated(
        train_df,
        test_df,
        floor=TIP_CONFIDENCE_FLOOR,
        feature_prefixes=CATCHER_FEATURE_PREFIXES,
        tip_kind="catcher",
        id_prefix="catch",
    )
    return {
        "pitcher_tips": pitcher["tips_ge_floor"],
        "catcher_tips": catcher["tips_ge_floor"],
        "candidates_train": pitcher.get("candidates_train"),
        "n_failed_holdout": pitcher.get("n_failed_holdout"),
        "situations": pitcher["situations"],
        "arsenal": pitcher["arsenal"],
        "n_pitches": int(len(feat_df)),
        "train_games": train_ids,
        "test_games": test_ids,
        "n_train_pitches": int(len(train_df)),
        "n_test_pitches": int(len(test_df)),
    }


def score_insample(feat_df: pd.DataFrame) -> list[dict]:
    """
    In-sample fit, no holdout — the protocol that produced the tips currently on
    the board for the early runs. Reproduced here only so the window's effect can
    be measured against those tips on equal terms.
    """
    if feat_df.empty:
        return []
    cov = evaluate_situations(
        feat_df,
        floor=TIP_CONFIDENCE_FLOOR,
        feature_prefixes=PITCHER_FEATURE_PREFIXES,
        tip_kind="pitcher",
        id_prefix="disc",
    )
    return cov["tips_ge_floor"]


def audit_run(run_dir: Path) -> dict:
    old_df, new_df, stats = rebuild(run_dir)
    old = score(old_df)
    new = score(new_df)
    old_ins = score_insample(old_df)
    new_ins = score_insample(new_df)

    published = []
    report_path = run_dir / "report.json"
    if report_path.is_file():
        published = json.loads(report_path.read_text()).get("tips") or []
    board_ids = {t["id"] for t in published}
    new_ins_ids = {t["id"] for t in new_ins}

    summary = {
        "run": run_dir.name,
        "window": {
            "legacy": "fixed 55% of clip frames (could include arm action / delivery)",
            "corrected": "coming set -> set -> PitchCom / catcher setup, ends at hand break",
            "boundary_detection": stats["methods"],
            "pitches_with_tracks": stats["pitches"],
            "pitches_missing_tracks": stats["no_track"],
            "pitches_dropped_unbounded": stats["dropped_unbounded"],
        },
        "published_tips_on_board": len(published),
        # Same in-sample protocol the board used, legacy vs corrected window.
        # This isolates the window's effect from the separate holdout gap below.
        "insample_legacy_window": len(old_ins),
        "insample_corrected_window": len(new_ins),
        "board_tips_surviving_corrected_window": sorted(board_ids & new_ins_ids),
        "board_tips_lost_to_corrected_window": sorted(board_ids - new_ins_ids),
        "legacy_rebuild": {
            "n_pitches": old["n_pitches"],
            "n_pitcher_tips": len(old["pitcher_tips"]),
            "n_catcher_tips": len(old["catcher_tips"]),
        },
        "corrected": {
            "n_pitches": new["n_pitches"],
            "n_pitcher_tips": len(new["pitcher_tips"]),
            "n_catcher_tips": len(new["catcher_tips"]),
            "candidates_train": new.get("candidates_train"),
            "n_failed_holdout": new.get("n_failed_holdout"),
        },
        "surviving_tip_ids": [t["id"] for t in new["pitcher_tips"]],
        "lost_tip_ids": sorted(
            {t["id"] for t in old["pitcher_tips"]} - {t["id"] for t in new["pitcher_tips"]}
        ),
        "tips": new["pitcher_tips"],
        "catcherTips": new["catcher_tips"],
        "tip_floor": TIP_CONFIDENCE_FLOOR,
        "validation": "train_fit_test_holdout_actionable_window",
        "note": (
            "Derived from cached per-frame tracks. Original report.json left intact "
            "for before/after audit."
        ),
    }

    if not new_df.empty:
        new_df.to_csv(run_dir / "features_actionable.csv", index=False)
    (run_dir / "report_actionable.json").write_text(json.dumps(summary, indent=2))
    return summary


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--runs", nargs="+", required=True)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2] / "runs")
    args = p.parse_args()

    rows = []
    for name in args.runs:
        run_dir = args.root / name
        try:
            s = audit_run(run_dir)
        except Exception as e:  # keep auditing the rest
            print(f"{name}: SKIP ({e})")
            continue
        rows.append(s)
        print(
            f"{name:24s} board={s['published_tips_on_board']:3d} | "
            f"in-sample legacy={s['insample_legacy_window']:3d} "
            f"corrected={s['insample_corrected_window']:3d} "
            f"(board survivors {len(s['board_tips_surviving_corrected_window'])}) | "
            f"holdout legacy={s['legacy_rebuild']['n_pitcher_tips']:2d} "
            f"corrected={s['corrected']['n_pitcher_tips']:2d} | "
            f"pitches {s['legacy_rebuild']['n_pitches']}->{s['corrected']['n_pitches']}"
        )

    def tot(f) -> int:
        return sum(f(r) for r in rows)

    print(
        f"\nTOTALS  board={tot(lambda r: r['published_tips_on_board'])}"
        f"  in-sample corrected={tot(lambda r: r['insample_corrected_window'])}"
        f"  board survivors={tot(lambda r: len(r['board_tips_surviving_corrected_window']))}"
        f"  holdout-validated corrected={tot(lambda r: r['corrected']['n_pitcher_tips'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
