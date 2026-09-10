#!/usr/bin/env python3
"""Remove retracted / non-observable cues from demo.json (PitchCom, cheek, legacy catcher, glove_angle).

PitchCom on Savant CF is not observable: clips start after set and glove-centroid
"taps" are not PitchCom presses. These tips must never ship on lite or full site.
Also drops contradictory one-vs-rest duplicates (same situation+feature+direction).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cv"))

from preflight.tiering import retraction_reason  # noqa: E402

DEMO_PATHS = [ROOT / "demo.json", ROOT / "data" / "demo.json"]

PITCHCOM_TEXT = re.compile(r"pitch\s*-?\s*com", re.I)
RETRACTED_TEXT_MARKERS = (
    "pitchcom",
    "pitch com",
    "pitch-com",
    "cheek tension",
    "jaw clench",
    "facial muscle",
)


def tip_feature(tip: dict) -> str:
    return str(tip.get("feature") or tip.get("cue") or "").strip()


def is_bad_tip(tip: dict) -> bool:
    feat = tip_feature(tip)
    if feat and retraction_reason(feat):
        return True
    if feat.startswith(("pitchcom_", "cheek_motion_", "catcher_", "glove_angle_")):
        return True
    blob = " ".join(
        str(tip.get(k) or "")
        for k in (
            "lookFor",
            "what_to_spot",
            "direction",
            "behavior",
            "title",
            "cue",
            "spot_the_difference",
        )
    ).lower()
    if PITCHCOM_TEXT.search(blob):
        return True
    if any(m in blob for m in ("pitchcom",)):
        return True
    return False


def situation_key(tip: dict) -> str:
    if tip.get("situationId"):
        return str(tip["situationId"])
    ctx = tip.get("context")
    if isinstance(ctx, list):
        return "|".join(str(c) for c in ctx)
    if isinstance(ctx, str):
        return ctx
    return str(tip.get("situationLabel") or tip.get("situation") or "all")


def dedupe_vs_rest(tips: list[dict]) -> list[dict]:
    """Keep at most one tip per (situation, feature, high_means_type)."""
    best: dict[tuple, dict] = {}
    passthrough: list[dict] = []
    for t in tips:
        feat = tip_feature(t)
        if not feat:
            passthrough.append(t)
            continue
        direction = t.get("high_means_type")
        if direction is None:
            # Infer from copy direction keywords when missing
            look = str(t.get("lookFor") or "").lower()
            if any(w in look for w in ("slow", "wide pause", "lower", "deeper", "only 1")):
                direction = False
            elif any(w in look for w in ("rapid", "brisk", "higher", "3+", "multiple")):
                direction = True
            else:
                direction = "unk"
        key = (situation_key(t), feat, bool(direction) if direction != "unk" else "unk")
        conf = float(t.get("confidence") or t.get("precision") or 0)
        prev = best.get(key)
        if prev is None or conf > float(prev.get("confidence") or prev.get("precision") or 0):
            best[key] = t
    # Preserve original relative order among winners
    winners = {id(v) for v in best.values()}
    out = [t for t in tips if id(t) in winners or tip_feature(t) == ""]
    # Drop empty-feature passthrough duplicates that also conflict? keep them after winners
    seen = set()
    ordered = []
    for t in tips:
        if id(t) in winners:
            tid = tip_feature(t) + "|" + situation_key(t)
            if tid in seen:
                continue
            seen.add(tid)
            ordered.append(t)
    for t in passthrough:
        ordered.append(t)
    return ordered


def scrub_obj(obj, stats: dict):
    """Recursively drop tip-like dicts that are retracted; scrub nested coverage."""
    if isinstance(obj, dict):
        # Tip-shaped
        if ("lookFor" in obj or "what_to_spot" in obj) and (
            "feature" in obj or "predicts" in obj or "confidence" in obj
        ):
            if is_bad_tip(obj):
                stats["tips_removed"] += 1
                return None
        # Coverage type rows with feature
        if obj.get("feature") and retraction_reason(str(obj["feature"])):
            stats["coverage_rows_removed"] += 1
            return None
        out = {}
        for k, v in obj.items():
            if k in ("tips", "topLeads", "catcherTips", "leads") and isinstance(v, list):
                cleaned = []
                for item in v:
                    scrubbed = scrub_obj(item, stats)
                    if scrubbed is not None:
                        cleaned.append(scrubbed)
                if k in ("tips", "topLeads"):
                    before = len(cleaned)
                    cleaned = dedupe_vs_rest(cleaned)
                    stats["deduped"] += before - len(cleaned)
                out[k] = cleaned
            else:
                scrubbed = scrub_obj(v, stats)
                if scrubbed is not None:
                    out[k] = scrubbed
        return out
    if isinstance(obj, list):
        out = []
        for item in obj:
            scrubbed = scrub_obj(item, stats)
            if scrubbed is not None:
                out.append(scrubbed)
        return out
    return obj


def recompute_team_counts(demo: dict) -> None:
    players = demo.get("players") or {}
    for team in demo.get("teams") or []:
        tid = team.get("id")
        ids = [pid for pid, p in players.items() if p.get("teamId") == tid]
        tips_n = 0
        with_tips = 0
        for pid in ids:
            tips = (players[pid].get("tips") or []) + (players[pid].get("catcherTips") or [])
            n = len(tips)
            tips_n += n
            if n:
                with_tips += 1
        team["players"] = sorted(ids)
        team["tipCount"] = tips_n
        team["playersWithTips"] = with_tips


def scrub_file(path: Path) -> dict:
    demo = json.loads(path.read_text())
    stats = {"tips_removed": 0, "coverage_rows_removed": 0, "deduped": 0}
    scrubbed = scrub_obj(demo, stats)
    assert isinstance(scrubbed, dict)
    # Hard pass: strip any remaining pitchcom string in tip text fields
    for p in (scrubbed.get("players") or {}).values():
        for key in ("tips", "topLeads", "catcherTips"):
            keep = []
            for t in p.get(key) or []:
                if is_bad_tip(t):
                    stats["tips_removed"] += 1
                    continue
                keep.append(t)
            if key in p:
                p[key] = dedupe_vs_rest(keep)
    recompute_team_counts(scrubbed)
    meta = scrubbed.setdefault("meta", {})
    notes = meta.setdefault("publishNotes", [])
    note = (
        "PitchCom / cheek / legacy catcher / glove_angle cues are withheld on broadcast "
        "Savant CF (clips start after set; detectors do not observe real PitchCom taps). "
        "Club 4K multi-angle continuous video is required before PitchCom cadence tips can return."
    )
    if note not in notes:
        notes.append(note)
    path.write_text(json.dumps(scrubbed, indent=2, ensure_ascii=False) + "\n")
    return stats


def verify(path: Path) -> int:
    d = json.loads(path.read_text())
    bad = 0
    for pid, p in (d.get("players") or {}).items():
        for t in (p.get("tips") or []) + (p.get("catcherTips") or []) + (p.get("topLeads") or []):
            if is_bad_tip(t):
                print("STILL BAD", pid, tip_feature(t), (t.get("lookFor") or "")[:80])
                bad += 1
        blob = json.dumps(p.get("tips") or []).lower()
        if "pitchcom" in blob or "pitch com" in blob:
            print("STILL TEXT", pid)
            bad += 1
    return bad


def main() -> int:
    for path in DEMO_PATHS:
        if not path.exists():
            print("missing", path)
            continue
        stats = scrub_file(path)
        bad = verify(path)
        print(f"{path}: removed={stats} remaining_bad={bad}")
        if bad:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
