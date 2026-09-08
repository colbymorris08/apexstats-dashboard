#!/usr/bin/env python3
"""Wire top-5 tips + mlbam + team membership for COL Rockies staff into demo.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO_PATHS = [ROOT / "demo.json", ROOT / "data" / "demo.json"]

# demo player id -> (run dir, mlbam, video prefix)
ARMS = [
    ("blas_casta_o", "blas_castaño_poc", 680604, "castano", "Blas Castaño"),
    ("brennan_bernardino", "brennan_bernardino_poc", 657514, "bernardino", "Brennan Bernardino"),
    ("jaden_hill", "jaden_hill_poc", 677955, "hill", "Jaden Hill"),
    ("herget", "jimmy_herget_poc", 623474, "herget", "Jimmy Herget"),
    ("jordan_romano", "jordan_romano_poc", 605447, "romano", "Jordan Romano"),
    ("juan_mejia", "juan_mejia_poc", 675848, "mejia", "Juan Mejia"),
    ("mark_manfredi", "mark_manfredi_poc", 815081, "manfredi", "Mark Manfredi"),
    ("mason_adams", "mason_adams_poc", 690279, "adams", "Mason Adams"),
    ("nick_frasso", "nick_frasso_poc", 693308, "frasso", "Nick Frasso"),
    ("feltner", "ryan_feltner_poc", 663372, "feltner", "Ryan Feltner"),
    ("sugano", "tomoyuki_sugano_poc", 608372, "sugano", "Tomoyuki Sugano"),
    ("zach_agnos", "zach_agnos_poc", 688642, "agnos", "Zach Agnos"),
]

CATCHERS = ["drew_romo", "jacob_stallings"]
COL_PLAYER_IDS = [a[0] for a in ARMS]


def top_tips(report: dict, n: int = 5) -> list[dict]:
    tips = list(report.get("tips") or [])
    tips.sort(key=lambda t: (-(t.get("confidence") or 0), -(t.get("lift") or 0), -(t.get("n") or 0)))
    out = []
    seen = set()
    for t in tips:
        tid = t.get("id") or json.dumps(t, sort_keys=True)[:80]
        if tid in seen:
            continue
        seen.add(tid)
        # Ensure tip has anchor defaults for pre-set→delivery window
        t = dict(t)
        if t.get("anchor_a") is None and t.get("tA") is None:
            t["anchor_a"] = 2.40
        if t.get("anchor_b") is None and t.get("tB") is None:
            t["anchor_b"] = 2.20
        t["status"] = t.get("status") or "active"
        out.append(t)
        if len(out) >= n:
            break
    return out


def main() -> int:
    for path in DEMO_PATHS:
        demo = json.loads(path.read_text())
        players = demo["players"]
        for pid, run, mlbam, prefix, name in ARMS:
            report_path = ROOT / "runs" / run / "report.json"
            if not report_path.exists():
                print(f"missing report {run}")
                continue
            report = json.loads(report_path.read_text())
            tips = top_tips(report, 5)
            if pid not in players:
                # create stub from report
                players[pid] = {
                    "id": pid,
                    "name": name,
                    "teamId": "col",
                    "throws": "R",
                    "role": "SP",
                    "picked": True,
                    "tier": "operational",
                    "tips": tips,
                }
            p = players[pid]
            p["mlbam"] = mlbam
            p["teamId"] = "col"
            p["videoPrefix"] = prefix
            p["tips"] = tips
            p["pitchesModeled"] = report.get("n_tracked") or p.get("pitchesModeled")
            p["holdoutAccuracy"] = report.get("holdout_accuracy") or p.get("holdoutAccuracy")
            p["summary"] = (
                f"Savant CF PoC: {report.get('n_tracked', '?')} pitches / "
                f"{report.get('n_games', '?')} games. "
                f"{len(tips)} pitcher leads (≥75% detected movement separation floor)."
            )
            print(f"  {pid}: {len(tips)} tips prefix={prefix}")

        # Update COL team roster to full staff (timed set) + keep gordon/hughes noted
        for team in demo["teams"]:
            if team["id"] != "col":
                continue
            # Full timed staff + prior tip1 arms remain on team page
            roster = list(dict.fromkeys(COL_PLAYER_IDS + ["gordon", "hughes"]))
            team["players"] = roster
            team["catchers"] = CATCHERS
            team["playersWithTips"] = sum(1 for pid in roster if players.get(pid, {}).get("tips"))
            tip_count = sum(len(players.get(pid, {}).get("tips") or []) for pid in roster)
            tip_count += sum(len(demo["catchers"].get(cid, {}).get("tips") or []) for cid in CATCHERS)
            team["tipCount"] = tip_count
            print(f"  team COL players={len(roster)} tipCount={tip_count}")

        # frasso was on LAD — leave LAD list but he's also COL for this benchmark; remove from LAD if present
        for team in demo["teams"]:
            if team["id"] == "lad" and "nick_frasso" in team.get("players", []):
                team["players"] = [x for x in team["players"] if x != "nick_frasso"]
                print("  removed nick_frasso from LAD (now COL live roster)")

        path.write_text(json.dumps(demo, indent=2) + "\n")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
