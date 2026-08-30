"""
Git synchronization utility for Preflight.

Commits and pushes updated data/findings to:
1. origin main (Colby Morris apexstats / dashboard repository)
2. preflight main (standalone preflight repository)

Also copies updated pitch-tips/data/demo.json to pitch-tips/demo.json for any legacy root references.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # pitch-tips/
WORKSPACE_ROOT = ROOT.parent  # apexstats/


def sync_findings(player_name: str, context: str = "pitcher") -> bool:
    """
    Commit and push updated data/findings to origin and preflight remotes.
    """
    try:
        # 1. Ensure pitch-tips/demo.json mirrors pitch-tips/data/demo.json
        src_demo = ROOT / "data" / "demo.json"
        dst_demo = ROOT / "demo.json"
        if src_demo.is_file():
            try:
                dst_demo.write_text(src_demo.read_text())
            except Exception:
                pass

        # 2. Stage data and site updates
        files_to_add = [
            "pitch-tips/data/demo.json",
            "pitch-tips/data/progress.json",
            "pitch-tips/demo.json",
            "pitch-tips/runs/arm_readiness.json",
            "pitch-tips/runs/league_progress_2026.json",
            "pitch-tips/runs/scheduler_status.json",
        ]
        
        # Check if there are changes to stage
        st = subprocess.run(
            ["git", "status", "--porcelain"] + files_to_add,
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if not st.stdout.strip():
            # No changes to sync
            return True

        subprocess.run(
            ["git", "add"] + files_to_add,
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )

        commit_msg = (
            f"feat(preflight): update findings for {player_name} [{context}]\n\n"
            f"- Auto-synced findings to live dashboard and GitHub Pages\n"
            f"- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        commit_res = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if commit_res.returncode != 0 and "nothing to commit" not in commit_res.stdout:
            print(f"  git commit note: {commit_res.stdout.strip() or commit_res.stderr.strip()}")

        # 3. Push to origin main
        push_origin = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if push_origin.returncode == 0:
            print(f"  [git sync] Pushed updated findings for {player_name} to origin main")
        else:
            print(f"  [git sync] Push to origin main note: {push_origin.stderr.strip()}")

        # 4. Push standalone pitch-tips subtree to preflight main
        # We perform a subtree split or push
        split_res = subprocess.run(
            ["git", "subtree", "split", "--prefix=pitch-tips", "HEAD"],
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if split_res.returncode == 0 and split_res.stdout.strip():
            tree_hash = split_res.stdout.strip().splitlines()[-1]
            push_preflight = subprocess.run(
                ["git", "push", "preflight", f"{tree_hash}:main", "--force"],
                cwd=str(WORKSPACE_ROOT),
                capture_output=True,
                text=True,
                timeout=60,
            )
            if push_preflight.returncode == 0:
                print(f"  [git sync] Pushed standalone findings for {player_name} to preflight main")
            else:
                print(f"  [git sync] Push to preflight note: {push_preflight.stderr.strip()}")
        return True

    except Exception as e:
        print(f"  [git sync] Warning: automated git sync failed: {e}")
        return False
