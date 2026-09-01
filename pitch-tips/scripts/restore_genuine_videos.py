#!/usr/bin/env python3
"""Restore genuine non-MLB clips from git and purge MLB imposters."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIDEO_DIR = ROOT / "media" / "video"
WORKSPACE = ROOT.parent
SOURCE_COMMIT = "a922d2b"
MLB_PREFIXES = {"roupp", "webb", "erod", "pfaadt", "gausman", "gordon"}
NON_MLB_PREFIXES = {"burns", "sasaki", "choi", "gulin", "rios", "hughes", "moreno"}
SIT_SUFFIXES = [
    "_bases_empty", "_runner_1b", "_runner_2b", "_runners_on",
    "_vs_rhb", "_vs_lhb", "_windup", "_stretch",
]


def md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git_show(commit: str, rel: str) -> bytes | None:
    r = subprocess.run(
        ["git", "-C", str(WORKSPACE), "show", f"{commit}:{rel}"],
        capture_output=True,
    )
    if r.returncode != 0 or len(r.stdout) < 500:
        return None
    return r.stdout


def git_list(commit: str) -> list[str]:
    r = subprocess.run(
        ["git", "-C", str(WORKSPACE), "ls-tree", "-r", commit, "--name-only"],
        capture_output=True, text=True,
    )
    prefix = "pitch-tips/media/video/"
    return [ln[len(prefix):] for ln in r.stdout.splitlines()
            if ln.startswith(prefix) and ln.endswith(".mp4")]


def mlb_hash_set() -> set[str]:
    hs: set[str] = set()
    for f in VIDEO_DIR.glob("*.mp4"):
        if f.name.split("_")[0] in MLB_PREFIXES:
            hs.add(md5_file(f))
    return hs


def pitch_code(fname: str) -> str | None:
    m = re.match(r"^[a-z]+_([a-z]+)(?:_|\.mp4)", fname)
    return m.group(1) if m else None


def cf_code(fname: str, prefix: str) -> str | None:
    if not fname.endswith("_cf.mp4") and "target" not in fname:
        return None
    if "fastball" in fname or fname.startswith(f"{prefix}_ff"):
        return "ff"
    if "slider" in fname:
        return "sl"
    if "splitter" in fname or "fork" in fname:
        return "fs"
    if "sinker" in fname:
        return "si"
    if "changeup" in fname:
        return "ch"
    if "curveball" in fname:
        return "cu"
    if "target" in fname:
        return "ff" if "_ff_" in fname or fname.startswith(f"{prefix}_ff") else "ch"
    return None


def main() -> int:
    if not VIDEO_DIR.is_dir():
        print(f"ERROR: {VIDEO_DIR} missing", file=sys.stderr)
        return 1

    mlb_hs = mlb_hash_set()
    print(f"Indexed {len(mlb_hs)} unique MLB hashes")

    # Restore canonical files from original showcase commit
    restored = 0
    for fname in git_list(SOURCE_COMMIT):
        prefix = fname.split("_")[0]
        if prefix not in NON_MLB_PREFIXES:
            continue
        if any(s in fname for s in SIT_SUFFIXES):
            continue
        data = git_show(SOURCE_COMMIT, f"pitch-tips/media/video/{fname}")
        if not data:
            continue
        if md5_bytes(data) in mlb_hs:
            print(f"  SKIP git imposter: {fname}")
            continue
        (VIDEO_DIR / fname).write_bytes(data)
        restored += 1
        print(f"  restored {fname} ({len(data)//1024}KB)")

    deleted = 0
    copied = 0
    for prefix in sorted(NON_MLB_PREFIXES):
        canonical: dict[str, Path] = {}
        for f in sorted(VIDEO_DIR.glob(f"{prefix}_*.mp4")):
            if any(s in f.name for s in SIT_SUFFIXES) or f.name.endswith("_cf.mp4"):
                if f.name.endswith("_cf.mp4") or "target" in f.name:
                    code = cf_code(f.name, prefix)
                    if code and md5_file(f) not in mlb_hs:
                        canonical.setdefault(code, f)
                continue
            code = pitch_code(f.name)
            if code and f.stat().st_size > 500 and md5_file(f) not in mlb_hs:
                canonical[code] = f

        if not canonical:
            print(f"  WARNING: no verified files for {prefix}")
            continue

        print(f"  {prefix}: verified codes {sorted(canonical)}")

        for f in list(VIDEO_DIR.glob(f"{prefix}_*.mp4")):
            if md5_file(f) in mlb_hs:
                f.unlink()
                deleted += 1

        for code, src in canonical.items():
            base = VIDEO_DIR / f"{prefix}_{code}.mp4"
            if not base.exists() or md5_file(base) != md5_file(src):
                base.write_bytes(src.read_bytes())
                copied += 1
            for suf in SIT_SUFFIXES:
                dst = VIDEO_DIR / f"{prefix}_{code}{suf}.mp4"
                if not dst.exists() or md5_file(dst) != md5_file(base):
                    dst.write_bytes(base.read_bytes())
                    copied += 1

    manifest = {}
    for prefix in NON_MLB_PREFIXES:
        manifest[prefix] = {}
        for f in sorted(VIDEO_DIR.glob(f"{prefix}_*.mp4")):
            if any(s in f.name for s in SIT_SUFFIXES) or "_cf" in f.name or "target" in f.name:
                continue
            if md5_file(f) in mlb_hs:
                continue
            code = pitch_code(f.name)
            if code:
                manifest[prefix][code] = f"media/video/{f.name}"

    out = ROOT / "media" / "deck" / "verified_non_mlb_videos.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"\nRestored {restored} from git, deleted {deleted} imposters, wrote {copied} copies")
    print(f"Manifest: {out.relative_to(WORKSPACE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
