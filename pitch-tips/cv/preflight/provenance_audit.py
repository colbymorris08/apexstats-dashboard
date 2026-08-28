#!/usr/bin/env python3
"""
Audit every user-visible number against the runs on disk.

Read-only. Checks the two files the site fetches — data/demo.json (board,
team tiles, player dossiers) and data/progress.json (live scale page) — and
reports, per player and per tip, whether it traces to a completed run with a
corrected-window report_actionable.json, a passing sanity gate and per-tip
holdout evidence.

Writes runs/provenance_audit.json and prints a table. Exit code 1 if anything
user-visible is unbacked, so it can be used as a pre-publish check.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from preflight.provenance import evidence_for, find_run_dir  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
DEMO = ROOT / "data" / "demo.json"
PROGRESS = ROOT / "data" / "progress.json"


def audit_demo() -> dict:
    demo = json.loads(DEMO.read_text())
    players = demo.get("players") or {}
    rows = []
    for pid, p in players.items():
        run_dir = find_run_dir(RUNS, p.get("name") or pid)
        ev = evidence_for(run_dir)
        backed_ids = {t.get("id") for t in ev["tips"]}
        backed_catcher_ids = {t.get("id") for t in ev["catcherTips"]}
        def classify(tip: dict, backed: set[str]) -> str:
            if tip.get("id") in backed:
                return "backed"
            if ev["run_dir"] is None:
                return "unbacked_never_tracked"
            if not ev["has_actionable"]:
                return "unbacked_legacy_window"
            if not ev["publishable"]:
                return "unbacked_sanity_gate_failed"
            # The arm is real and re-derived, but this tip is not in the current
            # corrected-window tip set — a stale publish from an earlier pass.
            return "unbacked_stale_superseded"

        tips = []
        for t in p.get("tips") or []:
            tips.append(
                {
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "confidence": t.get("confidence"),
                    "backed": t.get("id") in backed_ids,
                    "verdict": classify(t, backed_ids),
                    "kind": "pitcher",
                }
            )
        for t in p.get("catcherTips") or []:
            tips.append(
                {
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "confidence": t.get("confidence"),
                    "backed": t.get("id") in backed_catcher_ids,
                    "verdict": classify(t, backed_catcher_ids),
                    "kind": "catcher",
                }
            )
        if ev["run_dir"] is None:
            origin = "unbacked: no run directory (hand-authored seed card)"
        elif not ev["has_actionable"]:
            origin = "unbacked: run exists but no corrected-window re-derivation"
        elif not ev["publishable"]:
            origin = f"unbacked: sanity gate failed {ev['sanity']['failed_checks']}"
        else:
            origin = "run: " + Path(ev["run_dir"]).name
        rows.append(
            {
                "id": pid,
                "name": p.get("name"),
                "teamId": p.get("teamId"),
                "flags": {
                    "poc": bool(p.get("poc")),
                    "illustrative": bool(p.get("illustrative")),
                    "tipsSource": p.get("tipsSource"),
                },
                "published_tips": len(p.get("tips") or []),
                "published_catcher_tips": len(p.get("catcherTips") or []),
                "backed_tips": sum(1 for t in tips if t["backed"] and t["kind"] == "pitcher"),
                "backed_catcher_tips": sum(
                    1 for t in tips if t["backed"] and t["kind"] == "catcher"
                ),
                "player_backed": ev["publishable"],
                "origin": origin,
                "evidence": {
                    "run_dir": ev["run_dir"],
                    "has_report": ev["has_report"],
                    "has_actionable": ev["has_actionable"],
                    "tip_split_backs_tips": ev.get("tip_split_present"),
                    "reasons": ev["reasons"],
                },
                "tips": tips,
            }
        )
    return {"players": rows, "teams": demo.get("teams") or []}


def audit_progress() -> dict:
    if not PROGRESS.is_file():
        return {"present": False}
    prog = json.loads(PROGRESS.read_text())
    rows = []
    for key, row in (prog.get("done") or {}).items():
        ev = evidence_for(find_run_dir(RUNS, row.get("name") or "", row.get("work")))
        rows.append(
            {
                "key": key,
                "name": row.get("name"),
                "team": row.get("team"),
                "published_tips_ge_75": row.get("tips_ge_75"),
                "published_catcher_tips": row.get("catcher_tips"),
                "backed_tips": len(ev["tips"]),
                "backed_catcher_tips": len(ev["catcherTips"]),
                "run_dir": ev["run_dir"],
                "reasons": ev["reasons"],
            }
        )
    return {
        "present": True,
        "status": prog.get("status"),
        "published_totals": prog.get("totals"),
        "backed_totals": {
            "pitcher_tips": sum(r["backed_tips"] for r in rows),
            "catcher_tips": sum(r["backed_catcher_tips"] for r in rows),
        },
        "arms": rows,
    }


def main(argv: list[str] | None = None) -> int:
    global DEMO, PROGRESS
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--demo", type=Path, default=DEMO)
    ap.add_argument("--progress", type=Path, default=PROGRESS)
    ap.add_argument("--out", type=Path, default=RUNS / "provenance_audit.json")
    args = ap.parse_args(argv)
    DEMO, PROGRESS = args.demo, args.progress

    demo = audit_demo()
    progress = audit_progress()

    print("=== data/demo.json ===")
    print(f"{'player':22} {'team':5} {'pub':>4} {'backed':>7}  origin")
    unbacked = 0
    for r in demo["players"]:
        pub = r["published_tips"] + r["published_catcher_tips"]
        backed = r["backed_tips"] + r["backed_catcher_tips"]
        unbacked += pub - backed
        mark = " " if pub == backed and r["player_backed"] else "!"
        print(f"{mark}{r['name'][:21]:21} {str(r['teamId'])[:5]:5} {pub:>4} {backed:>7}  {r['origin']}")
    print(
        f"\npublished tips: {sum(r['published_tips'] + r['published_catcher_tips'] for r in demo['players'])}"
        f" · backed: {sum(r['backed_tips'] + r['backed_catcher_tips'] for r in demo['players'])}"
        f" · unbacked: {unbacked}"
    )
    verdicts: dict[str, int] = {}
    for r in demo["players"]:
        for t in r["tips"]:
            verdicts[t["verdict"]] = verdicts.get(t["verdict"], 0) + 1
    for k, v in sorted(verdicts.items(), key=lambda kv: -kv[1]):
        print(f"  {v:>3} {k}")

    if progress.get("present"):
        print("\n=== data/progress.json (live scale page) ===")
        print(f"published totals: {progress['published_totals']}")
        print(f"backed totals:    {progress['backed_totals']}")
        for r in progress["arms"]:
            print(
                f"  {r['name'][:24]:24} pub {r['published_tips_ge_75']}/{r['published_catcher_tips']}"
                f"  backed {r['backed_tips']}/{r['backed_catcher_tips']}"
            )

    out = {"demo_source": str(DEMO), "demo": demo, "progress": progress}
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote {args.out}")

    pub_tot = progress.get("published_totals") or {}
    bak_tot = progress.get("backed_totals") or {}
    return 1 if unbacked or pub_tot != bak_tot else 0


if __name__ == "__main__":
    raise SystemExit(main())
