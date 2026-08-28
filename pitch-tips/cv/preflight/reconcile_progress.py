#!/usr/bin/env python3
"""
Rewrite data/progress.json tip counts from validated evidence.

The live scale page reads this file directly. It was last written by the (now
paused) scaler using legacy report.json coverage counts, so it advertised 22
pitcher tips / 17 catcher tips for three arms whose corrected-window
re-derivation supports 0 / 1. This restates the counts without restarting or
resuming the pipeline: queue, phases, done/failed membership and timings are
left exactly as the scaler wrote them.

Original is preserved as data/progress.pre_provenance_audit.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from preflight.provenance import find_run_dir, validated_counts  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
PROGRESS = ROOT / "data" / "progress.json"
BACKUP = ROOT / "data" / "progress.pre_provenance_audit.json"


def main() -> None:
    prog = json.loads(PROGRESS.read_text())
    if not BACKUP.is_file():
        BACKUP.write_text(json.dumps(prog, indent=2) + "\n")

    for row in (prog.get("done") or {}).values():
        run_dir = find_run_dir(RUNS, row.get("name") or "", row.get("work"))
        v_tips, v_catcher = validated_counts(run_dir)
        # Idempotent: keep the first-seen legacy figures so re-running cannot
        # erase what the board used to claim.
        legacy_p = row.setdefault("legacy_tips_ge_75", row.get("tips_ge_75"))
        legacy_c = row.setdefault("legacy_catcher_tips", row.get("catcher_tips"))
        row["tips_ge_75"] = v_tips
        row["catcher_tips"] = v_catcher
        print(f"{row.get('name')}: {legacy_p}/{legacy_c} → {v_tips}/{v_catcher}")

    for row in (prog.get("catchers_done") or {}).values():
        run_dir = find_run_dir(RUNS, row.get("name") or "", row.get("work"))
        row.setdefault("legacy_tips_ge_75", row.get("tips_ge_75"))
        row["tips_ge_75"] = validated_counts(run_dir)[0]

    by_team = prog.get("by_team") or {}
    for t in by_team.values():
        t["pitcher_tips"] = 0
        t["catcher_tips"] = 0
    for row in (prog.get("done") or {}).values():
        t = by_team.setdefault(
            row.get("team") or "OTH", {"queued": 0, "done": 0, "pitcher_tips": 0, "catcher_tips": 0}
        )
        t["pitcher_tips"] += int(row.get("tips_ge_75") or 0)
        t["catcher_tips"] += int(row.get("catcher_tips") or 0)
    for row in (prog.get("catchers_done") or {}).values():
        t = by_team.setdefault(
            row.get("team") or "OTH", {"queued": 0, "done": 0, "pitcher_tips": 0, "catcher_tips": 0}
        )
        t["catcher_tips"] += int(row.get("tips_ge_75") or 0)

    prog["totals"] = {
        "pitcher_tips": sum(int(x.get("tips_ge_75") or 0) for x in (prog.get("done") or {}).values()),
        "catcher_tips": sum(
            int(x.get("tips_ge_75") or 0) for x in (prog.get("catchers_done") or {}).values()
        )
        + sum(int(x.get("catcher_tips") or 0) for x in (prog.get("done") or {}).values()),
    }
    # The file was left mid-run by a scaler that is now on hold, so the page
    # was animating a "currently tracking Gabriel Moreno" state that is not
    # happening. Say what is true instead.
    if prog.get("status") == "running":
        prog["status"] = "paused"
    prog["current"] = None
    prog["live"] = None
    prog["heartbeat"] = False
    prog["tip_count_basis"] = (
        "validated: corrected set→hand-break window, passing sanity gate, per-tip game holdout"
    )
    PROGRESS.write_text(json.dumps(prog, indent=2) + "\n")
    print(f"totals → {prog['totals']}")


if __name__ == "__main__":
    main()
