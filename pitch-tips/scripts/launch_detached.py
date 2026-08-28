#!/usr/bin/env python3
"""
Launch the overnight supervisor in its own session.

The run died at 23:43 with no error in the log because it was killed, not
crashed: it was a child of the tool shell that started it, and when that shell
was torn down the whole process group went with it. The supervisor did not
recover the scaler because the supervisor was in that same group and died at the
same instant. ``nohup`` only ignores SIGHUP; it does not move the process out of
the group that receives the teardown.

``start_new_session=True`` calls setsid(2) in the child, so the supervisor
becomes a session leader with no controlling terminal and survives the shell
that launched it. macOS ships no setsid(1) binary, which is why this is a Python
launcher rather than a line in the shell script.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    # Any long job launched from a tool shell needs this treatment, not just the
    # supervisor: the quota fetcher was lost the same way, silently, after
    # downloading 101 clips. Usage:
    #   launch_detached.py [--log NAME] [CMD ...]
    argv = sys.argv[1:]
    log_name = "overnight_nohup.log"
    if argv and argv[0] == "--log":
        log_name = argv[1]
        argv = argv[2:]
    cmd = argv or ["bash", str(ROOT / "scripts" / "overnight.sh")]

    log = (ROOT / "runs" / log_name).open("ab", buffering=0)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "cv")
    env["MPLCONFIGDIR"] = "/tmp/mpl"
    # Unbuffered, so a stalled run can be diagnosed from the log instead of
    # guessing from file counts.
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=log,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        env=env,
    )
    (ROOT / "runs" / f"{Path(log_name).stem}.pid").write_text(str(proc.pid))
    print(f"pid={proc.pid} (own session, survives shell teardown): {' '.join(cmd)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
