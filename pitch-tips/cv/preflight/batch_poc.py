#!/usr/bin/env python3
"""Batch PoC runner: scale sample across named pitchers, write per-arm reports."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from preflight.run_poc import run_poc  # noqa: E402

DEFAULT = [
    "Logan Webb",
    "Bryan Woo",
    "Logan Gilbert",
    "George Kirby",
    "Luis Castillo",
]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--season", type=int, default=2026)
    p.add_argument("--sample", type=int, default=80)
    p.add_argument("--pitchers", nargs="*", default=DEFAULT)
    p.add_argument("--runs", type=Path, default=Path(__file__).resolve().parents[1] / "runs")
    p.add_argument("--skip-existing", action="store_true")
    args = p.parse_args()
    summary = []
    for name in args.pitchers:
        slug = name.lower().replace(" ", "_")
        work = args.runs / f"{slug}_poc"
        report_path = work / "report.json"
        if args.skip_existing and report_path.is_file():
            rep = json.loads(report_path.read_text())
            if int(rep.get("n_tracked") or 0) >= max(20, args.sample // 3):
                print(f"skip {name}: existing n={rep.get('n_tracked')}")
                summary.append(rep)
                continue
        print(f"\n===== {name} sample={args.sample} =====")
        try:
            rep = run_poc(name, args.season, args.sample, work)
            summary.append(rep)
        except Exception as e:
            print(f"FAIL {name}: {e}")
            summary.append({"pitcher": name, "error": str(e)})
    out = args.runs / "batch_summary.json"
    out.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
