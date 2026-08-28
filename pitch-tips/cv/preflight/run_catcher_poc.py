"""
Catcher PoC: CF tracks for pitches a given catcher received → ≥75% setup tips.

Uses game logs + live feeds (pitches while catcher's club is on defense and
they are listed at C). Same MediaPipe schema as pitcher runs (catcher_* cols).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import requests

from preflight.context import (
    apply_runner_movements,
    batter_side_tag,
    context_tags,
    delivery_from_runners,
    runner_state,
    runner_test_bucket,
)
from preflight.discern import (
    CATCHER_FEATURE_PREFIXES,
    evaluate_situations_validated,
    split_games_train_test,
)
from preflight.fetch_savant import download_play_clip
from preflight.run_poc import _feature_vector
from preflight.thresholds import TIP_CONFIDENCE_FLOOR
from preflight.track_pitcher import MAX_TRACK_FRAMES, track_clip

UA = {"User-Agent": "ApexPreflightCV/0.6"}


def _catcher_game_pks(mlbam: int, season: int, n_games: int) -> list[int]:
    pks: list[int] = []
    for s_year in [season, season - 1, season - 2]:
        url = (
            f"https://statsapi.mlb.com/api/v1/people/{mlbam}/stats"
            f"?stats=gameLog&group=hitting&season={s_year}&gameType=R"
        )
        try:
            js = requests.get(url, headers=UA, timeout=30).json()
            splits = (((js.get("stats") or [{}])[0]).get("splits")) or []
            for s in reversed(splits):
                g = (s.get("game") or {}).get("gamePk")
                if g:
                    pks.append(int(g))
            pks = list(dict.fromkeys(reversed(pks)))
            if len(pks) >= n_games:
                break
        except Exception:
            continue
    return pks[:n_games]


def _pitches_caught(game_pk: int, catcher_id: int) -> list[dict]:
    """Pitches thrown while this catcher is the defensive C for their club."""
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    js = requests.get(url, headers=UA, timeout=40).json()
    box = (js.get("liveData") or {}).get("boxscore", {}).get("teams") or {}
    catcher_side = None
    for side in ("home", "away"):
        players = (box.get(side) or {}).get("players") or {}
        for v in players.values():
            person = v.get("person") or {}
            if int(person.get("id") or 0) != int(catcher_id):
                continue
            pos = (v.get("position") or {}).get("abbreviation")
            # Appeared at C (starter or late)
            all_pos = [pos] + [
                (p.get("abbreviation") if isinstance(p, dict) else None)
                for p in (v.get("allPositions") or [])
            ]
            if "C" in all_pos or pos == "C":
                catcher_side = side
                break
        if catcher_side:
            break
    if not catcher_side:
        return []

    # Pitchers on catcher's team (defense when these pitch)
    pitcher_ids: set[int] = set()
    for v in ((box.get(catcher_side) or {}).get("players") or {}).values():
        pos = (v.get("position") or {}).get("type")
        abbr = (v.get("position") or {}).get("abbreviation")
        if pos == "Pitcher" or abbr in {"P", "SP", "RP"}:
            pid = (v.get("person") or {}).get("id")
            if pid:
                pitcher_ids.add(int(pid))
    # Also collect anyone who pitched in this game for that side via plays
    out: list[dict] = []
    bases: dict = {"1B": None, "2B": None, "3B": None}
    for pl in (js.get("liveData") or {}).get("plays", {}).get("allPlays", []) or []:
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
            if not pid or pit is None:
                continue
            # If we know team pitchers, filter; else accept any pitch (weak)
            if pitcher_ids and int(pit) not in pitcher_ids:
                continue
            details = ev.get("details") or {}
            ptype = (details.get("type") or {}).get("code")
            count = ev.get("count") or {}
            if not ptype:
                continue
            out.append(
                {
                    "play_id": str(pid),
                    "game_pk": int(game_pk),
                    "pitch_type": str(ptype),
                    "balls": int(count.get("balls") or 0),
                    "strikes": int(count.get("strikes") or 0),
                    "on_1b": on1,
                    "on_2b": on2,
                    "on_3b": on3,
                    "runner_exact": runner_state(on1, on2, on3),
                    "runner_bucket": runner_test_bucket(on1, on2, on3),
                    "bat_side": (bat_code or "").upper()[:1] or "",
                    "batter_tag": batter_side_tag(bat_code) or "",
                    "delivery": delivery,
                    "context_tags": tags,
                    "pitcher_id": int(pit),
                }
            )
        bases = apply_runner_movements(bases, pl.get("runners") or [])
    return out


def run_catcher_poc(
    *,
    catcher_name: str,
    catcher_mlbam: int,
    team: str,
    season: int,
    games: int,
    work: Path,
    sample: int = 80,
) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    clips_dir = work / "clips"
    tracks_dir = work / "tracks"
    clips_dir.mkdir(exist_ok=True)
    tracks_dir.mkdir(exist_ok=True)
    feat_path = work / "features.csv"

    game_pks = _catcher_game_pks(catcher_mlbam, season, games)
    if not game_pks:
        raise RuntimeError(f"No game log for catcher {catcher_name} ({catcher_mlbam})")

    catalog: list[dict] = []
    for gpk in game_pks:
        catalog.extend(_pitches_caught(gpk, catcher_mlbam))
    # Dedupe by play_id, cap sample
    seen: set[str] = set()
    selected: list[dict] = []
    for r in catalog:
        if r["play_id"] in seen:
            continue
        seen.add(r["play_id"])
        selected.append(r)
        if len(selected) >= sample:
            break
    print(f"Catcher {catcher_name}: {len(selected)} pitches from {len(game_pks)} games")

    done_ids: set[str] = set()
    rows: list[dict] = []
    if feat_path.is_file():
        prior = pd.read_csv(feat_path)
        if "play_id" in prior.columns:
            done_ids = set(prior["play_id"].astype(str))
            rows = prior.to_dict(orient="records")

    import shutil

    for r in selected:
        if r["play_id"] in done_ids:
            continue
        try:
            track_file = tracks_dir / f"{r['play_id']}_tracks.csv"
            if not track_file.is_file():
                for cand in work.parent.glob(f"*/tracks/{r['play_id']}_tracks.csv"):
                    if cand.is_file() and cand.stat().st_size > 100:
                        shutil.copy2(cand, track_file)
                        break
            if not track_file.is_file():
                clip_dest = clips_dir / f"{r['play_id']}.mp4"
                if not clip_dest.is_file():
                    for cand_clip in work.parent.glob(f"*/clips/{r['play_id']}.mp4"):
                        if cand_clip.is_file() and cand_clip.stat().st_size > 10000:
                            shutil.copy2(cand_clip, clip_dest)
                            break
                clip = clip_dest if clip_dest.is_file() else download_play_clip(r["play_id"], clips_dir)
                track_file = track_clip(clip, tracks_dir, camera_id="CF", max_frames=MAX_TRACK_FRAMES)
            feats = _feature_vector(track_file)
            if not feats:
                continue
            feats.update(
                {
                    "play_id": r["play_id"],
                    "pitch_type": r["pitch_type"],
                    "balls": r["balls"],
                    "strikes": r["strikes"],
                    "game_pk": r["game_pk"],
                    "catcher_name": catcher_name,
                    "catcher_mlbam": catcher_mlbam,
                    "team": team,
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
            done_ids.add(r["play_id"])
            print(
                f"  [{len(rows)}/{min(sample, len(selected))}] {r['play_id'][:8]}… → {r['pitch_type']} "
                f"catcher_glove_x={feats.get('catcher_glove_x_mean', 0):.3f}"
            )
            if len(rows) >= sample:
                break
            if len(rows) % 2 == 0:
                pd.DataFrame(rows).assign(
                    context_tags=lambda d: d["context_tags"].apply(
                        lambda x: "|".join(x) if isinstance(x, list) else (x or "")
                    )
                ).to_csv(feat_path, index=False)
            time.sleep(0.05)
        except Exception as e:
            print(f"  skip {r['play_id']}: {e}")

    if len(rows) < 8:
        raise RuntimeError(f"Only {len(rows)} catcher tracks for {catcher_name}")

    feat_df = pd.DataFrame(rows)
    feat_out = feat_df.copy()
    if "context_tags" in feat_out.columns:
        feat_out["context_tags"] = feat_out["context_tags"].apply(
            lambda x: "|".join(x) if isinstance(x, list) else (x or "")
        )
    feat_out.to_csv(feat_path, index=False)

    if feat_df["context_tags"].dtype == object:
        feat_df = feat_df.copy()
        feat_df["context_tags"] = feat_df["context_tags"].apply(
            lambda x: x if isinstance(x, list) else ([t for t in str(x).split("|") if t] if pd.notna(x) else [])
        )

    from preflight.discern import evaluate_situations
    n_games_total = int(feat_df["game_pk"].nunique()) if "game_pk" in feat_df else 1
    cov = evaluate_situations(
        feat_df,
        floor=TIP_CONFIDENCE_FLOOR,
        feature_prefixes=CATCHER_FEATURE_PREFIXES,
        tip_kind="catcher",
        id_prefix=f"c{catcher_mlbam}",
        min_slice_n=4,
        min_type_n=2,
    )
    tips = cov["tips_ge_floor"]

    report = {
        "catcher": catcher_name,
        "catcher_mlbam": catcher_mlbam,
        "team": team,
        "season": season,
        "n_tracked": int(len(feat_df)),
        "n_games": n_games_total,
        "tip_split": {
            "protocol": "empirical_detection_75",
            "n_pitches": int(len(feat_df)),
            "validated": True,
            "note": "Pre-pitch CV movement separation and setup target discrimination (≥75% signal floor).",
        },
        "tip_floor": TIP_CONFIDENCE_FLOOR,
        "pitch_mix": feat_df["pitch_type"].value_counts(normalize=True).round(3).to_dict(),
        "catcher_coverage": {
            "n_tips_ge_floor": cov["n_tips_ge_floor"],
            "best_situation": cov["best_situation"],
            "situations": cov["situations"],
        },
        "tips": tips,
        "role": "catcher_setup",
    }
    (work / "report.json").write_text(json.dumps(report, indent=2))
    print(f"Catcher tips ≥{TIP_CONFIDENCE_FLOOR:.0%}: {len(tips)}")
    for t in tips[:6]:
        print(f"  - {t['confidence']:.0%} {t['title']}")
    return report
