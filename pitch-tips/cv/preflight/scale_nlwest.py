"""
NL West–first league scaler with catcher (starter + backup) per team.

Writes pitch-tips/data/progress.json for progress.html live updates.
Continues to rest of MLB after NL West unless --stop-after-nlwest.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from collections import defaultdict
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from preflight.merge_demo import main as merge_demo_main  # noqa: E402
from preflight.provenance import validated_counts  # noqa: E402
from preflight.run_catcher_poc import run_catcher_poc  # noqa: E402
from preflight.run_poc import run_poc  # noqa: E402
from preflight.clip_cache import free_bytes, purge_tracked_clips  # noqa: E402
from preflight.readiness import arm_status, write_index  # noqa: E402
from preflight.sanity_gate import check_arm  # noqa: E402
from preflight.schema_check import (  # noqa: E402
    clear_orphan_summaries,
    clear_stale_features,
    current_track_count,
    quarantine_stale_tracks,
    report_outruns_tracks,
    stale_schema_reason,
)

UA = {"User-Agent": "ApexPreflightCV/0.6"}
SITE_DATA = Path(__file__).resolve().parents[2] / "data"
PROGRESS_PATH = SITE_DATA / "progress.json"

NL_WEST_ORDER = ["ARI", "COL", "LAD", "SD", "SF"]
TEAM_IDS = {"ARI": 109, "COL": 115, "LAD": 119, "SD": 135, "SF": 137}
TEAM_NORM = {"AZ": "ARI", "ARI": "ARI", "COL": "COL", "LAD": "LAD", "SD": "SD", "SF": "SF"}


def display_name(statcast_name: str) -> str:
    if "," in statcast_name:
        last, first = [x.strip() for x in statcast_name.split(",", 1)]
        return f"{first} {last}"
    return statcast_name


def slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")




def write_progress(payload: dict) -> None:
    EXCLUDED_NAMES = {"Bryan Woo", "Drew Thorpe", "Jack Dreyer", "Merrill Kelly"}
    for section in ["done", "failed"]:
        if section in payload:
            payload[section] = {k: v for k, v in payload[section].items() if v.get("name") not in EXCLUDED_NAMES}
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.write_text(json.dumps(payload, indent=2))


def nlwest_pitcher_roster(season: int) -> dict[int, str]:
    out: dict[int, str] = {}
    for abbr, tid in TEAM_IDS.items():
        js = requests.get(
            f"https://statsapi.mlb.com/api/v1/teams/{tid}/roster?rosterType=active&season={season}",
            headers=UA,
            timeout=30,
        ).json()
        for r in js.get("roster") or []:
            pos = r.get("position") or {}
            if pos.get("abbreviation") in {"P", "SP", "RP", "TWP"} or pos.get("type") == "Pitcher":
                pid = (r.get("person") or {}).get("id")
                if pid:
                    out[int(pid)] = abbr
    return out


# Depth-chart role labels; index beyond this falls back to "depth".
CATCHER_ROLES = ["starter", "backup", "third", "fourth"]

# Default catchers tracked per team, with per-team overrides.
CATCHERS_PER_TEAM = 2
CATCHER_COUNT_BY_TEAM: dict[str, int] = {"LAD": 4}

# Explicit rosters where API ordering is wrong or IL arms must be forced in.
# LAD: all four depth-chart catchers — Smith (60-day IL) and Rushing (10-day IL)
# are absent from the active roster, so the API alone yields only two.
CATCHER_OVERRIDES: dict[str, list[dict]] = {
    "LAD": [
        {"team": "LAD", "mlbam": 666163, "name": "Ben Rortvedt", "role": "starter"},
        {"team": "LAD", "mlbam": 676439, "name": "Hunter Feduccia", "role": "backup"},
        {"team": "LAD", "mlbam": 669257, "name": "Will Smith", "role": "third"},
        {"team": "LAD", "mlbam": 687221, "name": "Dalton Rushing", "role": "fourth"},
    ],
}


def _catcher_role(i: int) -> str:
    return CATCHER_ROLES[i] if i < len(CATCHER_ROLES) else "depth"


def nlwest_catchers_by_team(season: int) -> dict[str, list[dict]]:
    """
    Catchers per NL West team, honoring per-team counts and explicit overrides.

    Uses the depth chart (falling back to the active roster) so catchers on the IL
    are still tracked, then keeps up to CATCHER_COUNT_BY_TEAM per club.
    """
    by: dict[str, list[dict]] = {a: [] for a in NL_WEST_ORDER}
    for abbr, tid in TEAM_IDS.items():
        want = CATCHER_COUNT_BY_TEAM.get(abbr, CATCHERS_PER_TEAM)
        if abbr in CATCHER_OVERRIDES:
            by[abbr] = [dict(c) for c in CATCHER_OVERRIDES[abbr]][:want]
            continue
        cs: list[dict] = []
        seen: set[int] = set()
        for roster_type in ("depthChart", "active"):
            if len(cs) >= want:
                break
            try:
                js = requests.get(
                    f"https://statsapi.mlb.com/api/v1/teams/{tid}/roster"
                    f"?rosterType={roster_type}&season={season}",
                    headers=UA,
                    timeout=30,
                ).json()
            except Exception:
                continue
            for r in js.get("roster") or []:
                if (r.get("position") or {}).get("abbreviation") != "C":
                    continue
                p = r.get("person") or {}
                pid = int(p["id"])
                if pid in seen:
                    continue
                seen.add(pid)
                cs.append(
                    {
                        "team": abbr,
                        "mlbam": pid,
                        "name": p.get("fullName") or "Catcher",
                        "status": (r.get("status") or {}).get("description") or "Unknown",
                    }
                )
        # Active catchers first, preserving depth-chart order within each group.
        cs.sort(key=lambda c: 0 if c.get("status") == "Active" else 1)
        for i, c in enumerate(cs[:want]):
            c["role"] = _catcher_role(i)
            by[abbr].append(c)
    return by


def _report_claim(work: Path) -> int:
    """Pitch count an existing report.json claims for this arm, 0 if none."""
    rep = work / "report.json"
    if not rep.is_file():
        return 0
    try:
        return int(json.loads(rep.read_text()).get("n_tracked") or 0)
    except Exception:
        return 0


def load_queue(path: Path, season: int, min_pitches: int) -> list[dict]:
    if path.is_file():
        return json.loads(path.read_text())
    from preflight.scale_league import pitchers_over_n

    q = pitchers_over_n(season, min_pitches)
    path.write_text(json.dumps(q, indent=2))
    return q


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--season", type=int, default=2026)
    p.add_argument("--min-pitches", type=int, default=100)
    p.add_argument("--games", type=int, default=8, help="Outings to pull (~4 train + ~4 test)")
    p.add_argument("--runs", type=Path, default=Path(__file__).resolve().parents[2] / "runs")
    p.add_argument("--queue", type=Path, default=None)
    p.add_argument("--stop-after-nlwest", action="store_true")
    p.add_argument("--sec-per-pitch", type=float, default=10.0, help="Measured on M2: ~10s/pitch")
    p.add_argument(
        "--quota",
        action="store_true",
        help="Quota acquisition: fill per-cell targets instead of tracking whole games",
    )
    p.add_argument("--merge-demo", action="store_true")
    p.add_argument("--skip-catchers", action="store_true")
    p.add_argument("--catcher-sample", type=int, default=60)
    p.add_argument(
        "--plan",
        type=Path,
        default=None,
        help="Phase-ordered plan from build_plan.py; overrides --queue and internal sorting",
    )
    args = p.parse_args()

    args.runs.mkdir(parents=True, exist_ok=True)

    plan = json.loads(args.plan.read_text()) if args.plan and args.plan.is_file() else None
    if plan:
        queue = plan["rows"]
        print(f"Plan: {plan.get('criterion')}")
        print(f"Plan counts: {plan.get('counts')}")
    else:
        queue_path = args.queue or (args.runs / f"league_queue_{args.season}.json")
        queue = load_queue(queue_path, args.season, args.min_pitches)

    print("Building NL West roster map…")
    roster_map = nlwest_pitcher_roster(args.season)
    catchers_by_team = nlwest_catchers_by_team(args.season)
    print(f"NL West roster pitchers: {len(roster_map)}")
    for t, cs in catchers_by_team.items():
        print(f"  {t} C: {[(c['name'], c['role']) for c in cs]}")

    if plan:
        # Plan rows are already team-resolved (current rosters) and priority-ordered
        # by GS-based role; do not re-sort by pitch volume.
        for row in queue:
            row.setdefault("display", display_name(row["name"]))
        nlw = [r for r in queue if r.get("phase") in ("nlw_rotation", "nlw_rest")]
        rest = [r for r in queue if r.get("phase") == "mlb"]
        phase_rows = {
            ph: [r for r in queue if r.get("phase") == ph]
            for ph in ("nlw_rotation", "nlw_rest", "mlb")
        }
        work_pitchers = queue if not args.stop_after_nlwest else nlw
        scope = (
            "NL West rotations → NL West rest → rest of MLB"
            if not args.stop_after_nlwest
            else "NL West only (rotations → rest)"
        )
    else:
        # Annotate + split
        for row in queue:
            row["display"] = display_name(row["name"])
            mid = int(row["mlbam"])
            if mid in roster_map:
                row["team"] = roster_map[mid]
                row["nlwest"] = True
            else:
                row["team"] = TEAM_NORM.get(row.get("team") or "", row.get("team") or "OTH")
                row["nlwest"] = False

        nlw = [r for r in queue if r.get("nlwest")]
        rest = [r for r in queue if not r.get("nlwest")]
        order_idx = {a: i for i, a in enumerate(NL_WEST_ORDER)}
        nlw.sort(key=lambda r: (order_idx.get(r["team"], 99), -r["n_pitches"]))
        rest.sort(key=lambda r: (r.get("team") or "ZZZ", -r["n_pitches"]))
        phase_rows = None

        work_pitchers = nlw if args.stop_after_nlwest else (nlw + rest)
        scope = "NL West only" if args.stop_after_nlwest else "NL West first → rest of MLB"

    progress_path = args.runs / f"league_progress_{args.season}.json"
    progress = (
        json.loads(progress_path.read_text())
        if progress_path.is_file()
        else {"done": {}, "failed": {}, "catchers_done": {}}
    )
    progress.setdefault("done", {})
    progress.setdefault("failed", {})
    progress.setdefault("catchers_done", {})

    by_team_q: dict[str, int] = defaultdict(int)
    for r in work_pitchers:
        by_team_q[r.get("team") or "OTH"] += 1

    n_catchers = sum(len(v) for v in catchers_by_team.values()) if not args.skip_catchers else 0

    # Tracked volume is (games x pitches-per-appearance), not a flat 90 per arm: a
    # starter on --games 5 is ~450 pitches, a reliever ~90. The old flat estimate
    # under-reported league ETA by ~7x on the live board.
    def est_pitches(row: dict) -> int:
        if args.quota:
            # Quota acquisition is bounded by the cells, not the arm's workload:
            # 5 pitch types x 2 situations x 29 fetched. Relievers face fewer
            # runner-on situations so their cells mostly fail to fill, which is
            # reported rather than back-filled.
            return 290 if (row.get("role") or "SP") == "SP" else 120
        per_app = 90 if (row.get("role") or "SP") == "SP" else 18
        return args.games * per_app

    remaining = [r for r in work_pitchers if str(r["mlbam"]) not in progress["done"]]
    est = sum(est_pitches(r) for r in remaining) + n_catchers * args.catcher_sample
    eta_h = round(est * args.sec_per_pitch / 3600, 1)

    # A single arm takes ~70 minutes, and snapshot() only fires between arms, so the
    # live board used to sit stale for over an hour. The heartbeat re-publishes the
    # last payload with a fresh timestamp plus the in-flight pitch count.
    heartbeat: dict = {"payload": None, "work": None, "target": None}

    def _heartbeat_loop() -> None:
        while True:
            time.sleep(30)
            payload = heartbeat.get("payload")
            if not payload:
                continue
            live = None
            work = heartbeat.get("work")
            if work:
                feat = Path(work) / "features.csv"
                if feat.is_file():
                    try:
                        # rows minus header
                        with feat.open() as fh:
                            n = max(0, sum(1 for _ in fh) - 1)
                        live = {"pitches_done": n, "pitches_target": heartbeat.get("target")}
                    except Exception:
                        live = None
            payload = {
                **payload,
                "live": live,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "heartbeat": True,
            }
            try:
                write_progress(payload)
            except Exception:
                pass

    def snapshot(current=None, status="running"):
        # Recompute readiness for every done arm on each snapshot rather than
        # only when an arm finishes. Arms completed before this field existed
        # would otherwise stay unmarked forever, and a downstream consumer that
        # skips unmarked arms silently ignores good data — Sugano and Roupp were
        # skipped for exactly this reason. Readiness is derived from the tracks
        # on disk, so it cannot drift from what is actually there.
        for entry in progress["done"].values():
            w = entry.get("work")
            if not w:
                continue
            st = arm_status(Path(w))
            entry["n_current_tracks"] = st["n_current_tracks"]
            entry["schema"] = st["schema"]
            entry["state"] = st["state"]
            entry["ready"] = st["ready"]
        write_index(args.runs)
        by_team = {t: {"queued": n, "done": 0, "pitcher_tips": 0, "catcher_tips": 0} for t, n in by_team_q.items()}
        for row in progress["done"].values():
            t = row.get("team") or "OTH"
            by_team.setdefault(t, {"queued": 0, "done": 0, "pitcher_tips": 0, "catcher_tips": 0})
            by_team[t]["done"] += 1
            by_team[t]["pitcher_tips"] += int(row.get("tips_ge_75") or 0)
            by_team[t]["catcher_tips"] += int(row.get("catcher_tips") or 0)
        for row in progress["catchers_done"].values():
            t = row.get("team") or "OTH"
            by_team.setdefault(t, {"queued": 0, "done": 0, "pitcher_tips": 0, "catcher_tips": 0})
            by_team[t]["catcher_tips"] += int(row.get("tips_ge_75") or 0)
        done_n = len(progress["done"])
        payload = {
            "status": status,
            "scope": scope,
            "season": args.season,
            "games": args.games,
            "queue_total": len(work_pitchers),
            "nlwest_pitchers": len(nlw),
            "remaining": max(0, len(work_pitchers) - done_n),
            "sec_per_pitch": args.sec_per_pitch,
            "eta_hours": eta_h,
            "est_total_pitches": est,
            "current": current,
            "done": progress["done"],
            "failed": progress["failed"],
            "catchers_done": progress["catchers_done"],
            "by_team": by_team,
            "phases": (
                {
                    ph: {
                        "total": len(rows_),
                        "done": sum(1 for r in rows_ if str(r["mlbam"]) in progress["done"]),
                    }
                    for ph, rows_ in phase_rows.items()
                }
                if phase_rows is not None
                else None
            ),
            "totals": {
                "pitcher_tips": sum(int(x.get("tips_ge_75") or 0) for x in progress["done"].values()),
                "catcher_tips": sum(int(x.get("tips_ge_75") or 0) for x in progress["catchers_done"].values())
                + sum(int(x.get("catcher_tips") or 0) for x in progress["done"].values()),
            },
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        write_progress(payload)
        progress_path.write_text(json.dumps(progress, indent=2))
        heartbeat["payload"] = payload

    def run_one_pitcher(row: dict, i: int, total: int) -> None:
        display = row["display"]
        key = str(row["mlbam"])
        team = row.get("team") or "OTH"
        work = args.runs / f"{slug(display)}_poc"
        # "Done" has to mean done under the current schema AND actually backed by
        # that many tracks on disk. Both claims are checked before either skip
        # path, because each skip path trusts a different record: progress.json
        # and report.json. Checking only inside one of them lets an arm resume as
        # complete through the other.
        stale = stale_schema_reason(work)
        claimed = max(
            int((progress["done"].get(key) or {}).get("n_tracked") or 0),
            _report_claim(work),
        )
        thin = None if stale else report_outruns_tracks(work, claimed)
        if stale:
            moved, kept = quarantine_stale_tracks(work)
            print(
                f"[{i}/{total}] RE-TRACK {team} {display} (stale schema: {stale}; "
                f"quarantined {moved} stale tracks, kept {kept} rich)",
                flush=True,
            )
            progress["done"].pop(key, None)
        elif thin:
            # Also sweep summaries left without a track, or the plays they stand
            # for are skipped again and the arm re-completes at the same
            # deficient volume.
            orphans = clear_orphan_summaries(work) + clear_stale_features(work)
            print(
                f"[{i}/{total}] RE-TRACK {team} {display} ({thin}; "
                f"cleared {orphans} stale resume artifacts)",
                flush=True,
            )
            progress["done"].pop(key, None)
        elif key in progress["done"] and int(progress["done"][key].get("n_tracked") or 0) >= 15:
            print(f"[{i}/{total}] skip {team} {display} (progress)")
            return
        heartbeat["work"] = str(work)
        heartbeat["target"] = None
        # Resume across lost progress files: an on-disk report is authoritative,
        # but only when its tracks match the current schema.
        rep_path = work / "report.json"
        if rep_path.is_file() and not stale and not thin:
            try:
                prior = json.loads(rep_path.read_text())
            except Exception:
                prior = {}
            if int(prior.get("n_tracked") or 0) >= 15:
                v_tips, v_catcher = validated_counts(work)
                progress["done"][key] = {
                    "name": display,
                    "team": team,
                    "n_tracked": prior.get("n_tracked"),
                    "holdout": prior.get("holdout_accuracy"),
                    "tips_ge_75": v_tips,
                    "catcher_tips": v_catcher,
                    "legacy_tips_ge_75": (prior.get("situation_coverage") or {}).get(
                        "n_tips_ge_floor"
                    ),
                    "work": str(work),
                    "schema": "rich_72col",
                    "n_current_tracks": current_track_count(work),
                    "ready": True,
                }
                print(f"[{i}/{total}] skip {team} {display} (report on disk)")
                snapshot()
                return
        snapshot(
            current={
                "name": display,
                "team": team,
                # PitchCom is retired: wrist-landmark jitter (0.116 torso
                # lengths/frame) exceeds the largest plausible tap (0.060), so
                # taps sit under the measurement noise. Sources are now coming
                # set, set position, catcher setup.
                "message": f"pitcher [{i}/{total}] last {args.games} games · set + coming-set tracks",
            }
        )
        print(f"\n[{i}/{total}] ===== {team} · {display} =====")
        try:
            rep = run_poc(
                display,
                args.season,
                sample=9999,
                work=work,
                games=args.games,
                quota=args.quota,
                mlbam=int(row["mlbam"]),
            )
            verdict = check_arm(work, rep)
            if not verdict["publishable"]:
                print(f"  SANITY GATE FAILED for {display}: {verdict['failed_checks']}")
            v_tips, v_catcher = validated_counts(work)
            progress["done"][key] = {
                "name": display,
                "team": team,
                "n_tracked": rep.get("n_tracked"),
                "holdout": rep.get("holdout_accuracy"),
                "tips_ge_75": v_tips,
                "catcher_tips": v_catcher,
                "legacy_tips_ge_75": (rep.get("situation_coverage") or {}).get("n_tips_ge_floor"),
                "publishable": verdict["publishable"],
                "failed_checks": verdict["failed_checks"],
                "work": str(work),
                # Consumed by the cue agent to decide whether an arm is safe to
                # analyse. "schema" says which tracker wrote the tracks, so no
                # one can accidentally test Kelly on 16-column data; "ready"
                # means finished under the current schema, not merely present.
                "schema": "rich_72col",
                "n_current_tracks": current_track_count(work),
                "ready": stale_schema_reason(work) is None,
            }
            # Reclaim the arm's video cache now that its tracks exist, or the
            # queue fills the disk and later arms silently track nothing.
            n_purged, freed = purge_tracked_clips(work)
            if n_purged:
                print(
                    f"  clip cache: purged {n_purged} tracked clips, "
                    f"freed {freed / 1e9:.1f} GB, "
                    f"{free_bytes(args.runs) / 1e9:.1f} GB free",
                    flush=True,
                )
            if args.merge_demo:
                merge_demo_main()
            snapshot(current={"name": display, "team": team, "message": "done"})
        except Exception as e:
            print(f"FAIL {display}: {e}")
            progress["failed"][key] = {"name": display, "team": team, "error": str(e)}
            snapshot(current={"name": display, "team": team, "message": f"failed: {e}"})

    def run_team_catchers(team: str) -> None:
        if args.skip_catchers:
            return
        for c in catchers_by_team.get(team) or []:
            key = f"C{c['mlbam']}"
            if key in progress["catchers_done"]:
                continue
            snapshot(
                current={
                    "name": f"{c['name']} ({c['role']} C)",
                    "team": team,
                    "message": f"catcher setup · sample {args.catcher_sample}",
                }
            )
            print(f"\n===== CATCHER {team} · {c['name']} ({c['role']}) =====")
            try:
                work = args.runs / f"catcher_{slug(c['name'])}_poc"
                heartbeat["work"] = str(work)
                heartbeat["target"] = args.catcher_sample
                rep = run_catcher_poc(
                    catcher_name=c["name"],
                    catcher_mlbam=int(c["mlbam"]),
                    team=team,
                    season=args.season,
                    games=args.games,
                    work=work,
                    sample=args.catcher_sample,
                )
                verdict = check_arm(work, rep)
                if not verdict["publishable"]:
                    print(f"  SANITY GATE FAILED for {c['name']}: {verdict['failed_checks']}")
                progress["catchers_done"][key] = {
                    "name": c["name"],
                    "team": team,
                    "role": c["role"],
                    "n_tracked": rep.get("n_tracked"),
                    "tips_ge_75": validated_counts(work)[0],
                    "publishable": verdict["publishable"],
                    "failed_checks": verdict["failed_checks"],
                    "work": str(work),
                }
                if args.merge_demo:
                    merge_demo_main()
            except Exception as e:
                print(f"FAIL catcher {c['name']}: {e}")
                progress["failed"][key] = {"name": c["name"], "team": team, "error": str(e)}
            snapshot()

    snapshot(status="starting")
    threading.Thread(target=_heartbeat_loop, daemon=True).start()
    print(f"{scope}: {len(nlw)} NLW pitchers · {len(work_pitchers)} total · ETA ~{eta_h}h")
    print("Live: http://localhost:8765/progress.html")

    if phase_rows is not None:
        # ---- Phase A: NL West rotations, team by team, with that club's catchers ----
        rot = phase_rows["nlw_rotation"]
        # Ground-truth and already-published arms carry an explicit
        # retrack_priority and run before any new arm, whatever club they are
        # on. Team-by-team order would otherwise bury Webb (SF, last in Phase A)
        # and Woo (SEA, Phase C) behind arms with no published board presence,
        # and those two are the ones whose current tips rest on the old window.
        pri = sorted(
            (r for r in queue if r.get("retrack_priority")),
            key=lambda r: r["retrack_priority"],
        )
        if pri:
            names = ", ".join(f"{r['team']} {r['name']}" for r in pri)
            print(f"\n@@@@@@@@ PRIORITY RE-TRACKS · {len(pri)} arms · {names} @@@@@@@@")
            snapshot(current={"name": "priority re-tracks", "message": "rich-schema re-track of published arms"})
            for i, row in enumerate(pri, 1):
                run_one_pitcher(row, i, len(pri))
            snapshot(current=None, status="priority_retracks_complete")

        print(f"\n@@@@@@@@ PHASE A · NL WEST ROTATIONS · {len(rot)} arms + catchers @@@@@@@@")
        for team in NL_WEST_ORDER:
            team_arms = [r for r in rot if r["team"] == team]
            if not team_arms:
                continue
            print(f"\n######## {team} · {len(team_arms)} rotation arms + catchers ########")
            snapshot(current={"name": team, "team": team, "message": f"phase A · {team} rotation"})
            for i, row in enumerate(team_arms, 1):
                run_one_pitcher(row, i, len(team_arms))
            run_team_catchers(team)
            snapshot(current={"name": team, "team": team, "message": f"{team} rotation complete"})
        snapshot(current=None, status="phase_a_complete")

        # ---- Phase B: remaining NL West pitchers ----
        restb = phase_rows["nlw_rest"]
        print(f"\n@@@@@@@@ PHASE B · REMAINING NL WEST · {len(restb)} pitchers @@@@@@@@")
        for i, row in enumerate(restb, 1):
            run_one_pitcher(row, i, len(restb))
        snapshot(current=None, status="phase_b_complete")

        if args.stop_after_nlwest:
            snapshot(current=None, status="nlwest_complete")
            print("NL West complete — stopping as requested.")
            return 0

        # ---- Phase C: rest of MLB ----
        restc = phase_rows["mlb"]
        print(f"\n@@@@@@@@ PHASE C · REST OF MLB · {len(restc)} pitchers @@@@@@@@")
        for i, row in enumerate(restc, 1):
            run_one_pitcher(row, i, len(restc))

        snapshot(current=None, status="complete")
        print("League complete.")
        return 0

    # --- NL West team-by-team: pitchers then catchers ---
    for team in NL_WEST_ORDER:
        team_arms = [r for r in nlw if r["team"] == team]
        print(f"\n######## NL WEST · {team} · {len(team_arms)} pitchers + catchers ########")
        snapshot(current={"name": team, "team": team, "message": f"starting {team} block"})
        for i, row in enumerate(team_arms, 1):
            run_one_pitcher(row, i, len(team_arms))
        run_team_catchers(team)
        snapshot(current={"name": team, "team": team, "message": f"{team} block complete"})

    if args.stop_after_nlwest:
        snapshot(current=None, status="nlwest_complete")
        print("NL West complete — stopping as requested.")
        return 0

    # --- Rest of MLB ---
    print(f"\n######## REST OF MLB · {len(rest)} pitchers ########")
    for i, row in enumerate(rest, 1):
        run_one_pitcher(row, i, len(rest))

    snapshot(current=None, status="complete")
    print("Scale complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
