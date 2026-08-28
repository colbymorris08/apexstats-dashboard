#!/usr/bin/env python3
"""
Pipeline Scheduler for Apex Pitch-Tips.

Controls scheduled pause and resume:
- 18:00 PDT (6:00 PM): Graceful pause of supervisor and scalers
- 20:15 PDT (8:15 PM): Resume supervisor under launchd

Maintains real-time status in runs/scheduler_status.json and logs to runs/scheduler.log.
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
RUNS.mkdir(parents=True, exist_ok=True)

LOG_FILE = RUNS / "scheduler.log"
STATUS_FILE = RUNS / "scheduler_status.json"
PAUSE_SCRIPT = ROOT / "scripts" / "pause_pipeline.sh"
RESUME_SCRIPT = ROOT / "scripts" / "resume_pipeline.sh"

# Exact target times for today: 2026-08-27 (America/Los_Angeles)
TARGET_PAUSE_HOUR = 18
TARGET_PAUSE_MIN = 0
TARGET_RESUME_HOUR = 20
TARGET_RESUME_MIN = 15


def log(msg: str) -> None:
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{now_str}] {msg}"
    print(formatted, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(formatted + "\n")


def get_target_datetimes() -> tuple[datetime.datetime, datetime.datetime]:
    now = datetime.datetime.now()
    pause_dt = now.replace(hour=TARGET_PAUSE_HOUR, minute=TARGET_PAUSE_MIN, second=0, microsecond=0)
    resume_dt = now.replace(hour=TARGET_RESUME_HOUR, minute=TARGET_RESUME_MIN, second=0, microsecond=0)
    return pause_dt, resume_dt


def update_status(data: dict) -> None:
    try:
        STATUS_FILE.write_text(json.dumps(data, indent=2))
    except Exception as e:
        log(f"Failed to write status file: {e}")


def execute_script(script_path: Path, action_name: str) -> bool:
    log(f"Executing {action_name} script: {script_path}")
    try:
        res = subprocess.run(
            ["/bin/bash", str(script_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        log(f"{action_name} stdout:\n{res.stdout.strip()}")
        if res.stderr.strip():
            log(f"{action_name} stderr:\n{res.stderr.strip()}")
        log(f"{action_name} exit code: {res.returncode}")
        return res.returncode == 0
    except Exception as exc:
        log(f"ERROR executing {action_name}: {exc}")
        return False


def main() -> None:
    log("=== Apex Pipeline Scheduler Started ===")
    pause_dt, resume_dt = get_target_datetimes()
    
    paused_done = False
    resumed_done = False

    # Check if we started after any of the target times
    now = datetime.datetime.now()
    if now >= pause_dt and now < resume_dt:
        log(f"Current time ({now.strftime('%H:%M:%S')}) is past 18:00 and before 20:15. Checking if pause needed...")
    elif now >= resume_dt:
        log(f"Current time ({now.strftime('%H:%M:%S')}) is past 20:15.")

    last_status_write = 0.0

    while True:
        now = datetime.datetime.now()
        now_ts = time.time()
        
        pause_secs_left = max(0.0, (pause_dt - now).total_seconds())
        resume_secs_left = max(0.0, (resume_dt - now).total_seconds())

        # 1. Trigger Pause at 18:00
        if not paused_done and now >= pause_dt:
            log(f">>> TARGET REACHED: 18:00 PDT ({now.strftime('%H:%M:%S')}). Executing Pause...")
            success = execute_script(PAUSE_SCRIPT, "PAUSE")
            paused_done = True
            log(f"Pause complete (success={success}). Next trigger: Resume at {resume_dt.strftime('%H:%M:%S')} PDT.")

        # 2. Trigger Resume at 20:15
        if paused_done and not resumed_done and now >= resume_dt:
            log(f">>> TARGET REACHED: 20:15 PDT ({now.strftime('%H:%M:%S')}). Executing Resume...")
            success = execute_script(RESUME_SCRIPT, "RESUME")
            resumed_done = True
            log(f"Resume complete (success={success}). Processing seamlessly restarted.")

        # Periodic status update
        if now_ts - last_status_write >= 30 or (paused_done and not resumed_done and now_ts - last_status_write >= 10):
            current_state = "RUNNING_PRE_PAUSE"
            if paused_done and not resumed_done:
                current_state = "PAUSED"
            elif resumed_done:
                current_state = "RESUMED_ACTIVE"

            status_payload = {
                "scheduler_pid": os.getpid(),
                "current_time": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "state": current_state,
                "pause_scheduled_for": pause_dt.strftime("%Y-%m-%d %H:%M:%S PDT"),
                "pause_completed": paused_done,
                "seconds_until_pause": round(pause_secs_left, 1),
                "resume_scheduled_for": resume_dt.strftime("%Y-%m-%d %H:%M:%S PDT"),
                "resume_completed": resumed_done,
                "seconds_until_resume": round(resume_secs_left, 1),
            }
            update_status(status_payload)
            last_status_write = now_ts

            if not paused_done:
                log(f"Heartbeat: {round(pause_secs_left / 60, 1)}m until pause (at 18:00 PDT)")
            elif paused_done and not resumed_done:
                log(f"Heartbeat: In pause period. {round(resume_secs_left / 60, 1)}m until resume (at 20:15 PDT)")
            else:
                log("Heartbeat: Pipeline resumed and running. Monitoring active.")

        time.sleep(10)


if __name__ == "__main__":
    main()
