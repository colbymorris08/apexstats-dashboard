#!/usr/bin/env python3
"""
Two questions that decide whether a pre-pitch glove-target cue is buildable.

The measurement geometry already looks favourable, and unusually so. Measured on
436 sampled frames from 8 clips (catcher_mitt_probe.py):

  home plate box width                       0.0637 of frame width
  mitt centre-x jitter, frame to frame        0.0035 = 0.05 plate widths
  mitt centre-x range across clips            0.061  = 0.96 plate widths

That is a signal about twenty times its own noise floor, which is the opposite of
the pitcher's glove angle (horizontal extent 0.066 torso against a 0.100 jitter
floor, i.e. below its floor). The catcher facing the camera is exactly the
structural reason expected.

But favourable precision is worth nothing if either of the following is true, and
neither has been established:

  1. The mitt boxes are not on the mitt. ``catcher_mask`` looked like the best
     class in the family by hit rate and turned out to be on the UMPIRE, so no
     class in this model gets believed on its rate alone. Boxes are rendered.

  2. The detections sit outside the actionable window. The window closes at peak
     leg lift + 5 frames, and a mitt is far easier to detect once it is moving to
     receive the pitch — which is after the window, after the swing decision, and
     useless. If coverage is concentrated post-window then the 16% figure is not
     16% of usable frames, and the cue is unactionable no matter how precise.
     This is the same selection effect that made a flat pre-set tap profile
     evidence against the tap detector.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from preflight.parts_detect import detect_parts
from preflight.window import actionable_window, preset_segment

MITT_CONF = 0.25
PLATE_CONF = 0.25


def _render(frame, mitt, plate, out_path: Path) -> None:
    h, w = frame.shape[:2]
    vis = frame.copy()
    for d, col, tag in ((mitt, (0, 255, 255), "mitt"), (plate, (0, 128, 255), "plate")):
        if d is None:
            continue
        x1 = int((d["cx"] - d["bw"] / 2) * w)
        x2 = int((d["cx"] + d["bw"] / 2) * w)
        y1 = int(d["cy"] * h - d["bw"] * w / 2)
        y2 = int(d["cy"] * h + d["bw"] * w / 2)
        cv2.rectangle(vis, (x1, y1), (x2, y2), col, 2)
        cv2.putText(vis, f"{tag} {d['conf']:.2f}", (x1, max(12, y1 - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 2, cv2.LINE_AA)
    cv2.imwrite(str(out_path), vis)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clips-dir", type=Path, required=True)
    ap.add_argument("--tracks-dir", type=Path, required=True,
                    help="pitcher tracks for these clips, used to locate the window")
    ap.add_argument("--n-clips", type=int, default=4)
    ap.add_argument("--out", type=Path, default=Path("runs/catcher_target_probe.json"))
    ap.add_argument("--peek-dir", type=Path, default=None)
    a = ap.parse_args(argv)

    if a.peek_dir:
        a.peek_dir.mkdir(parents=True, exist_ok=True)
    per_clip: list[dict] = []
    n_peek = 0

    for clip in sorted(a.clips_dir.glob("*.mp4"))[: a.n_clips]:
        tr = a.tracks_dir / f"{clip.stem}_tracks.csv"
        if not tr.is_file():
            continue
        df = pd.read_csv(tr, low_memory=False)
        win = actionable_window(df)
        pre = preset_segment(df, win)
        if not win.valid:
            per_clip.append({"clip": clip.stem, "window": win.method, "valid": False})
            continue
        # The settled actionable span: pre-set open through window close.
        lo = pre[0] if pre else win.start
        hi = win.end

        cap = cv2.VideoCapture(str(clip))
        i = 0
        rows: list[dict] = []
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            h, w = frame.shape[:2]
            dets = detect_parts(frame, conf=0.05)
            mitt = max((d for d in dets if d["name"] == "catcher_mitt" and d["conf"] >= MITT_CONF),
                       key=lambda d: d["conf"], default=None)
            plate = max((d for d in dets if d["name"] == "plate" and d["conf"] >= PLATE_CONF),
                        key=lambda d: d["conf"], default=None)

            def norm(d):
                if d is None:
                    return None
                x1, y1, x2, y2 = d["xyxy"]
                return {"conf": round(d["conf"], 4), "cx": (x1 + x2) / 2 / w,
                        "cy": (y1 + y2) / 2 / h, "bw": (x2 - x1) / w}

            m, p = norm(mitt), norm(plate)
            rows.append({"frame": i, "in_window": bool(lo <= i < hi), "mitt": m, "plate": p})
            if (a.peek_dir and n_peek < 4 and m is not None and p is not None and lo <= i < hi):
                _render(frame, m, p, a.peek_dir / f"{clip.stem}_{i}_target.png")
                n_peek += 1
            i += 1
        cap.release()

        inw = [r for r in rows if r["in_window"]]
        outw = [r for r in rows if not r["in_window"]]

        def rate(rs, key):
            if not rs:
                return None
            return round(sum(1 for r in rs if r[key] is not None) / len(rs), 4)

        both_in = [r for r in inw if r["mitt"] and r["plate"]]
        # Mitt offset from the plate centre, in plate widths: the actual cue.
        offs = [(r["mitt"]["cx"] - r["plate"]["cx"]) / r["plate"]["bw"] for r in both_in]
        per_clip.append({
            "clip": clip.stem,
            "valid": True,
            "window": {"method": win.method, "delivery_type": win.delivery_type,
                       "lo": lo, "hi": hi, "n_frames": hi - lo, "clip_frames": len(rows)},
            "mitt_rate_in_window": rate(inw, "mitt"),
            "mitt_rate_out_of_window": rate(outw, "mitt"),
            "plate_rate_in_window": rate(inw, "plate"),
            "both_rate_in_window": round(len(both_in) / len(inw), 4) if inw else None,
            "n_both_in_window": len(both_in),
            "mitt_offset_plate_widths": {
                "median": round(st.median(offs), 4) if offs else None,
                "interdecile": round(float(np.percentile(offs, 90) - np.percentile(offs, 10)), 4)
                if len(offs) >= 5 else None,
            },
        })
        print(json.dumps(per_clip[-1]), flush=True)

    valid = [c for c in per_clip if c.get("valid")]
    inr = [c["mitt_rate_in_window"] for c in valid if c["mitt_rate_in_window"] is not None]
    outr = [c["mitt_rate_out_of_window"] for c in valid if c["mitt_rate_out_of_window"] is not None]
    bothr = [c["both_rate_in_window"] for c in valid if c["both_rate_in_window"] is not None]
    report = {
        "n_clips": len(per_clip),
        "n_valid_windows": len(valid),
        "mitt_rate_in_window_median": round(st.median(inr), 4) if inr else None,
        "mitt_rate_out_of_window_median": round(st.median(outr), 4) if outr else None,
        "both_rate_in_window_median": round(st.median(bothr), 4) if bothr else None,
        "n_pitches_with_any_in_window_measurement":
            sum(1 for c in valid if (c["n_both_in_window"] or 0) > 0),
        "per_clip": per_clip,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "per_clip"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
