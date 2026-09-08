#!/usr/bin/env python3
"""When CHC full-staff orch finishes, stamp measured wall-clock into sales deck + rebuild PPTX."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "runs" / "chc_cubs_exemplars"
SUMMARY = META / "full_staff_summary.json"
START = META / "wallclock_start.json"
DECK = ROOT / "scripts" / "build_sales_deck.py"


def wait_for_summary(timeout_h: float = 36.0) -> dict:
    deadline = time.time() + timeout_h * 3600
    while time.time() < deadline:
        if SUMMARY.exists():
            s = json.loads(SUMMARY.read_text())
            # Ignore poisoned/incomplete summaries
            if int(s.get("n_video_exemplars") or 0) >= 50 and "h" in str(s.get("elapsed_hm") or ""):
                return s
        time.sleep(60)
    raise TimeoutError("full_staff_summary.json not written")


def patch_deck(summary: dict) -> None:
    text = DECK.read_text()
    elapsed = summary.get("elapsed_hm") or "?"
    cells = summary.get("n_video_exemplars", "?")
    # Replace RUNNING placeholder bullet
    new_bullet = (
        f'            "**Wall-clock:** **{elapsed}** end-to-end '
        f'(tips → n≈10 video matrix → merge → deploy) · **{cells}** exemplars published",'
    )
    text2, n = re.subn(
        r'            "\*\*Wall-clock:\*\*.*",',
        new_bullet,
        text,
        count=1,
    )
    if n == 0:
        print("WARN: could not patch wall-clock bullet")
    else:
        DECK.write_text(text2)
    # Also patch stat card if present
    text2 = DECK.read_text()
    text2 = re.sub(
        r'(<div class="stat-card"><div class="stat-num">)14\+2(</div><div class="stat-label">Full Staff</div></div>)',
        rf'\g<1>{elapsed}\g<2>',
        text2,
        count=1,
    )
    # Better: add wall-clock as first stat
    text2 = text2.replace(
        '<div class="stat-card"><div class="stat-num">14+2</div><div class="stat-label">Full Staff</div></div>',
        f'<div class="stat-card"><div class="stat-num">{elapsed}</div><div class="stat-label">Wall-Clock</div></div>\n'
        f'  <div class="stat-card"><div class="stat-num">14+2</div><div class="stat-label">Full Staff</div></div>',
        1,
    )
    DECK.write_text(text2)
    print("Patched build_sales_deck.py")


def rebuild() -> None:
    subprocess.check_call([sys.executable, str(DECK)], cwd=str(ROOT))


def main() -> int:
    print("Waiting for CHC full_staff_summary.json…")
    summary = wait_for_summary()
    print("Got summary", summary.get("elapsed_hm"), summary.get("n_video_exemplars"))
    patch_deck(summary)
    rebuild()
    print("Deck rebuilt in Downloads/Preflight_Sales_Deck/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
