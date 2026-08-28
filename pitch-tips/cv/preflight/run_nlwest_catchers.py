"""
Run Catcher PoC for all NL West teams in parallel.
Scores empirical movement discrimination rate (≥75% signal) for sales tool / operational prototype.
"""
from __future__ import annotations

import concurrent.futures
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from preflight.run_catcher_poc import run_catcher_poc

NL_WEST_CATCHERS = [
    # LAD
    {"name": "Will Smith", "mlbam": 669257, "team": "LAD", "role": "starter"},
    {"name": "Austin Barnes", "mlbam": 605131, "team": "LAD", "role": "backup"},
    # ARI
    {"name": "Gabriel Moreno", "mlbam": 672515, "team": "ARI", "role": "starter"},
    {"name": "James McCann", "mlbam": 543510, "team": "ARI", "role": "backup"},
    # SD
    {"name": "Elias Díaz", "mlbam": 553869, "team": "SD", "role": "starter"},
    {"name": "Luis Campusano", "mlbam": 669134, "team": "SD", "role": "backup"},
    # SF
    {"name": "Patrick Bailey", "mlbam": 672275, "team": "SF", "role": "starter"},
    {"name": "Curt Casali", "mlbam": 592200, "team": "SF", "role": "backup"},
    # COL
    {"name": "Drew Romo", "mlbam": 691011, "team": "COL", "role": "starter"},
    {"name": "Jacob Stallings", "mlbam": 607732, "team": "COL", "role": "backup"},
]


def slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")


def process_catcher(c: dict) -> dict:
    name = c["name"]
    mlbam = c["mlbam"]
    team = c["team"]
    role = c["role"]
    runs_dir = Path(__file__).resolve().parents[2] / "runs"
    work = runs_dir / f"catcher_{slug(name)}_poc"
    print(f"--> [START] {name} ({team} · {role}) [MLBAM {mlbam}]")
    t0 = time.time()
    try:
        rep = run_catcher_poc(
            catcher_name=name,
            catcher_mlbam=mlbam,
            team=team,
            season=2026,
            games=6,
            work=work,
            sample=12,
        )
        rep["role_type"] = role
        (work / "report.json").write_text(json.dumps(rep, indent=2))
        tips = rep.get("tips", [])
        elapsed = time.time() - t0
        print(f"✓ [DONE {elapsed:.1f}s] {name} ({team}): {rep.get('n_tracked', 0)} pitches, {len(tips)} setup tips ≥75%")
        return {
            "catcher": name,
            "catcher_mlbam": mlbam,
            "team": team,
            "role": role,
            "n_tracked": rep.get("n_tracked", 0),
            "n_games": rep.get("n_games", 0),
            "tips_ge_75": len(tips),
            "tips": tips,
            "pitch_mix": rep.get("pitch_mix", {}),
            "catcher_coverage": rep.get("catcher_coverage", {}),
            "status": "success",
        }
    except Exception as e:
        print(f"✗ [FAIL] {name} ({team}): {e}")
        import traceback
        traceback.print_exc()
        return {
            "catcher": name,
            "catcher_mlbam": mlbam,
            "team": team,
            "role": role,
            "status": "error",
            "error": str(e),
        }


def main() -> None:
    runs_dir = Path(__file__).resolve().parents[2] / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting parallel Catcher PoC for {len(NL_WEST_CATCHERS)} NL West catchers...")
    summary = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(process_catcher, c): c for c in NL_WEST_CATCHERS}
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            summary.append(res)

    out_file = runs_dir / "nlwest_catchers_summary.json"
    out_file.write_text(json.dumps(summary, indent=2))
    print(f"\nWrote summary of {len(summary)} catchers to {out_file}")


if __name__ == "__main__":
    main()
