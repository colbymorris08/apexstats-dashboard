#!/usr/bin/env python3
"""
``cmitt_*`` box schema — the producer/consumer contract for persisted catcher
detector boxes.

This module IS the schema. The tracker calls ``box_row`` and writes the result
into its per-frame dict; consumers call ``read_boxes``. Neither side hand-rolls
column names, so the two cannot drift apart. Import it rather than reimplementing
it.

    from preflight.catcher_boxes import BOX_COLUMNS, box_row, provenance_block

    row.update(box_row(gear_dets, frame_w, frame_h))     # in the tracker
    ...
    summary["parts_boxes"] = provenance_block()           # in the summary json

Why persist boxes at all
------------------------
Catcher work needs pixels, and pixels are the expensive, perishable part: a
separate detector pass over an arm costs roughly 5.5 CPU-hours, and clips are
retained only as a bounded sample. Boxes written during the tracking pass that is
already decoding every frame turn all future catcher cue work into a
re-derivation from the tracks — the same reason ``KEEP_LANDMARKS`` persists raw
pitcher landmarks instead of only derived scalars.

Only the gear model is needed
-----------------------------
All four persisted classes live in ``parts_gear.pt``. Do NOT call
``parts_detect.detect_parts`` for this, which also loads and runs
``parts_glovehand.pt`` and doubles the cost for nothing. Use ``detect_gear``
below. Measured: both models together run ~0.124 s/frame on CPU, so the gear
model alone is ~0.06 s/frame, or ~15 s over a 240-frame clip.

If that cost is not affordable at stride 1, stride 2 is a defensible fallback and
the consequence is quantified: mitt centre-x jitter is 0.05 plate widths frame to
frame, and halving the frame count raises the standard error of a per-pitch median
from ~0.040 to ~0.057 plate widths, which still sits under the cue's 0.06
visibility threshold. Stride 3 does not — it lands at 0.069 and the cue stops
clearing its own floor. So: stride 1 preferred, stride 2 acceptable, stride 3 not.
If a stride is used, record it in the provenance block.

``catcher_mask`` is excluded, deliberately
------------------------------------------
It is not persisted and must not be added later without new evidence. It fires on
**77.5% of frames** — the joint-highest rate in the catcher family — and the boxes
were rendered and land on the **UMPIRE's** head, who stands directly behind the
catcher wearing the same equipment. It is the single most dangerous class in this
model precisely because it looks like the best one by coverage. Carrying it into a
new table would launder that error into a fresh column with a clean name.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

# Persisted classes, in column order. All four are gear-model classes.
#
#   catcher_mitt  the cue subject: where the catcher sets his mitt.
#   plate         the reference. Every cmitt_* cue is expressed in plate widths
#                 measured in the SAME frame, which is what makes it survive the
#                 zoom differences between parks. Without it the mitt coordinate
#                 is raw image position and carries camera pan.
#   catcher_shin  localisation anchors. Kept because they are what identifies the
#   catcher_cleat catcher's region for any future pose attempt, and re-deriving
#                 them later would mean another pixel pass — the exact cost this
#                 schema exists to avoid. Cheap: 5 columns each.
PERSIST_CLASSES: tuple[str, ...] = ("catcher_mitt", "plate", "catcher_shin", "catcher_cleat")

# Column prefix per class. Short, and unambiguously separate from the retracted
# ``catcher_*`` scalar family, which stays retracted.
PREFIX: dict[str, str] = {
    "catcher_mitt": "cmitt",
    "plate": "cplate",
    "catcher_shin": "cshin",
    "catcher_cleat": "ccleat",
}

EXCLUDED_CLASSES: dict[str, str] = {
    "catcher_mask": (
        "fires on the umpire, not the catcher: 77.5% frame rate, boxes inspected "
        "and land on the umpire's head directly behind the catcher"
    ),
}

# Per-class fields. Five each.
#
# cx, cy   box centre, normalised to the FULL FRAME, x rightward, y DOWNWARD.
#          Image convention, matching every existing coordinate in the tracks.
# bw, bh   box width and height, as fractions of frame width and height
#          respectively. Both are needed: bw of the plate is the unit every
#          lateral cue is measured in, and bh of shin/cleat sizes the catcher
#          crop.
# conf     detector confidence as returned, NOT thresholded. See below.
FIELDS: tuple[str, ...] = ("cx", "cy", "bw", "bh", "conf")

# Count of CREDIBLE mitt candidates in the frame. One extra column, on the mitt
# only, and it earns its place: two credible mitt boxes means at least one is on
# something else, and a consumer that cannot tell "one confident mitt" from "the
# most confident of several candidates" is one step from the wrong-object failure
# this project keeps finding.
COUNT_COLUMN = "cmitt_n"

# The count is taken at this confidence, NOT at WRITE_CONF.
#
# Measured on real frames: at the 0.05 write floor the mitt class returns 5-8
# boxes per frame, because that floor deliberately admits the whole noise lobe
# (median confidence in the family is ~0.09). A count of the noise lobe conveys
# nothing about ambiguity — it is roughly constant — so counting there would give
# the column a plausible-looking value with no information in it, which is the
# exact defect this schema is built to avoid.
#
# 0.25 is the level at which mitt boxes were rendered and confirmed to be on the
# mitt, so "how many boxes at or above 0.25" is a real question with a real
# answer: normally one.
AMBIGUITY_CONF = 0.25

# Confidence floor applied AT WRITE TIME. This is the detector's own floor, not a
# cue threshold, and it is deliberately permissive.
#
# Thresholding harder here would be unrecoverable without another pixel pass, and
# it would repeat the mistake the cheek columns made: a value discarded at write
# time cannot be reconsidered, and confidence is itself information. Consumers
# gate at their own floor — catcher_target.MITT_CONF is 0.25, which is the
# loosest level at which mitt boxes were rendered and confirmed on the mitt.
WRITE_CONF = 0.05

SCHEMA_VERSION = "cmitt_boxes_v1"


def box_columns() -> list[str]:
    """All columns this schema adds, in order. 21 total."""
    cols: list[str] = []
    for cls in PERSIST_CLASSES:
        p = PREFIX[cls]
        cols.extend(f"{p}_{f}" for f in FIELDS)
    cols.append(COUNT_COLUMN)
    return cols


BOX_COLUMNS: list[str] = box_columns()


def blank_row(examined: bool = True) -> dict[str, Any]:
    """
    Every column absent.

    ``examined`` distinguishes the two reasons a frame can have no boxes, and the
    distinction is the whole reason ``cmitt_n`` exists:

      examined=True   the frame was run through the detector and nothing credible
                      was found. ``cmitt_n`` is 0 — a real observation.
      examined=False  the frame was never run through the detector, because it
                      fell outside the bounded pass. ``cmitt_n`` is blank, i.e.
                      NaN. We do not know what is in this frame.

    Collapsing those two into a single "0" would assert an absence that was never
    measured, which is the failure this project keeps retracting.

    Absence of a BOX is the empty string, matching how the tracker already writes
    a missing landmark, and it reads back as NaN through pandas. There is no
    sentinel number, no zero, and no carry-forward from the previous frame: a
    plausible substitute for a missing detection is the failure mode behind four
    of this project's six retractions. A class is blank in ALL FIVE of its
    columns or in none of them — never partially, because a half-populated box is
    a box a consumer can silently misread.
    """
    row: dict[str, Any] = {c: "" for c in BOX_COLUMNS}
    row[COUNT_COLUMN] = 0 if examined else ""
    return row


def box_row(dets: list[dict], frame_w: int, frame_h: int) -> dict[str, Any]:
    """
    Per-frame box columns from gear-model detections.

    ``dets`` is what ``detect_gear`` returns: dicts with ``name`` and ``xyxy`` in
    PIXELS, plus ``conf``. Pass every detection; filtering happens here so the
    write floor lives in one place.

    One box per class — the highest confidence one. Extra candidates are not
    persisted, only counted for the mitt.
    """
    row = blank_row(examined=True)
    if frame_w <= 0 or frame_h <= 0:
        return row

    kept = [d for d in dets if d.get("conf", 0.0) >= WRITE_CONF and d.get("name") in PERSIST_CLASSES]
    row[COUNT_COLUMN] = sum(
        1 for d in kept if d["name"] == "catcher_mitt" and d["conf"] >= AMBIGUITY_CONF
    )

    for cls in PERSIST_CLASSES:
        cands = [d for d in kept if d["name"] == cls]
        if not cands:
            continue
        best = max(cands, key=lambda d: d["conf"])
        x1, y1, x2, y2 = best["xyxy"]
        p = PREFIX[cls]
        row[f"{p}_cx"] = round((x1 + x2) / 2 / frame_w, 5)
        row[f"{p}_cy"] = round((y1 + y2) / 2 / frame_h, 5)
        row[f"{p}_bw"] = round((x2 - x1) / frame_w, 5)
        row[f"{p}_bh"] = round((y2 - y1) / frame_h, 5)
        row[f"{p}_conf"] = round(float(best["conf"]), 4)
    return row


# --- detection ----------------------------------------------------------------

_GEAR_OFFSET = 2  # gear class index -> canonical 10-class index


@lru_cache(maxsize=None)
def _gear_model(weights: str):
    from ultralytics import YOLO

    return YOLO(weights)


def gear_weights() -> Path:
    from preflight.parts_detect import GEAR_W

    return GEAR_W


def detect_gear(image, conf: float = WRITE_CONF, imgsz: int = 640, device: str = "cpu") -> list[dict]:
    """
    Run ONLY the gear specialist. Same output shape as ``detect_parts``.

    Separate from ``detect_parts`` on purpose: that function also runs
    ``parts_glovehand.pt``, which contributes none of the persisted classes and
    doubles the per-frame cost.
    """
    from preflight.parts_detect import CLASSES

    w = gear_weights()
    if not w.is_file():
        return []
    res = _gear_model(str(w)).predict(image, imgsz=imgsz, conf=conf, device=device, verbose=False)[0]
    out = []
    for b in res.boxes:
        cid = int(b.cls) + _GEAR_OFFSET
        out.append({
            "cls": cid,
            "name": CLASSES[cid],
            "conf": float(b.conf),
            "xyxy": [float(v) for v in b.xyxy[0]],
            "model": "gear",
        })
    out.sort(key=lambda d: d["conf"], reverse=True)
    return out


# --- provenance ---------------------------------------------------------------

def provenance_block(stride: int = 1) -> dict[str, Any]:
    """
    Goes in the clip's ``*_summary.json`` under ``"parts_boxes"``, NOT in the
    per-frame rows — it is constant for a clip and 21 columns is already the
    budget.

    The model fingerprint is the point. ``parts_gear.pt`` is trained on 28
    fully-labeled frames and is about to be retrained on a park-diverse labelling
    set, so tracks written before and after that will carry boxes of materially
    different quality under identical column names. Without the hash there is no
    way to tell them apart afterwards, and mixing them silently is how a coverage
    artifact becomes an effect size.
    """
    import hashlib

    w = gear_weights()
    digest = None
    size = None
    if w.is_file():
        size = w.stat().st_size
        h = hashlib.sha256()
        with open(w, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        digest = h.hexdigest()[:24]
    return {
        "schema": SCHEMA_VERSION,
        "model": w.name,
        "model_sha256_24": digest,
        "model_bytes": size,
        # Expected value at the time this schema was written. A mismatch is not an
        # error — it means the detector was retrained, which is the plan — but it
        # must be visible.
        "model_sha256_24_at_schema_v1": "15891fea835eecbb406765e2",
        "write_conf": WRITE_CONF,
        "ambiguity_conf": AMBIGUITY_CONF,
        "stride": stride,
        "persist_classes": list(PERSIST_CLASSES),
        "excluded_classes": EXCLUDED_CLASSES,
        "columns": BOX_COLUMNS,
        "coords": "box centre and size, normalised to full frame; x right, y down",
        "absent": "empty string -> NaN; never substituted or carried forward",
    }


# --- consumer side ------------------------------------------------------------

def read_boxes(df, cls: str):
    """
    Numeric (cx, cy, bw, bh, conf) arrays for one class from a tracks DataFrame.

    Returns all-NaN arrays when the columns are absent, so a consumer reading a
    pre-schema track gets NaN rather than a KeyError — the track genuinely has no
    information about this, which is what NaN means.
    """
    import numpy as np
    import pandas as pd

    p = PREFIX[cls]
    out = []
    for f in FIELDS:
        col = f"{p}_{f}"
        if col not in getattr(df, "columns", []):
            out.append(np.full(len(df), np.nan))
        else:
            out.append(pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=float))
    return tuple(out)


def has_box_schema(df) -> bool:
    return all(c in getattr(df, "columns", []) for c in BOX_COLUMNS)


__all__ = [
    "AMBIGUITY_CONF",
    "BOX_COLUMNS",
    "COUNT_COLUMN",
    "blank_row",
    "EXCLUDED_CLASSES",
    "FIELDS",
    "PERSIST_CLASSES",
    "PREFIX",
    "SCHEMA_VERSION",
    "WRITE_CONF",
    "box_row",
    "detect_gear",
    "has_box_schema",
    "provenance_block",
    "read_boxes",
]
