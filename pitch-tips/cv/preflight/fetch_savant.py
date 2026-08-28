"""Fetch Baseball Savant broadcast clips by play_id / pitcher search.

Video URLs are resolved from the Savant sporty-videos embed for a play page.
Pitch-type text on the page is never written into feature files — labels come
from Statcast joins in a separate step after tracking.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests

SAVANT_PLAY = "https://baseballsavant.mlb.com/sporty-videos?playId={play_id}"
USER_AGENT = "ApexPreflightCV/0.3 (+internal; club-eval)"


def resolve_mp4_url(play_id: str, session: requests.Session | None = None) -> str | None:
    """Return direct mp4 URL embedded on a Savant play page, if present."""
    sess = session or requests.Session()
    sess.headers.setdefault("User-Agent", USER_AGENT)
    url = SAVANT_PLAY.format(play_id=play_id)
    r = sess.get(url, timeout=40)
    r.raise_for_status()
    html = r.text
    # Common patterns: <source src="...mp4"> or video src=
    patterns = [
        r'<source[^>]+src=["\']([^"\']+\.mp4[^"\']*)["\']',
        r'<video[^>]+src=["\']([^"\']+\.mp4[^"\']*)["\']',
        r'(https?://[^"\'\s]+\.mp4[^"\'\s]*)',
    ]
    for pat in patterns:
        m = re.search(pat, html, flags=re.I)
        if m:
            raw = m.group(1)
            # Unescape HTML entities sometimes embedded in sporty-clips URLs
            raw = (
                raw.replace("&#x3D;", "=")
                .replace("&#x3d;", "=")
                .replace("&amp;", "&")
                .replace("%26%23x3D%3B", "=")
            )
            return urljoin(url, raw)
    return None


def is_decodable(path: Path) -> bool:
    """
    Can this mp4 actually be decoded?

    Size is not a sufficient check. The one corrupt clip found in the cache was
    4.06 MB — a wholly plausible size — but the download was cut off before the
    moov atom was written, so the container has no index and decodes to zero
    frames. A truncated fetch that leaves a normal-looking file is the same shape
    as the other failures in this pipeline: a plausible-looking absence with a
    wrong cause, which silently becomes a missing track and a thinner cell.
    """
    if not path.is_file() or path.stat().st_size <= 0:
        return False
    try:
        import cv2
    except ImportError:
        return True
    cap = cv2.VideoCapture(str(path))
    try:
        ok, _ = cap.read()
        return bool(ok) and int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) > 0
    finally:
        cap.release()


def download_play_clip(
    play_id: str,
    out_dir: Path,
    session: requests.Session | None = None,
    attempts: int = 2,
) -> Path:
    """Download one Savant CF broadcast clip. Raises if no mp4 found or it will not decode."""
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{play_id}.mp4"
    if is_decodable(dest):
        return dest
    sess = session or requests.Session()
    sess.headers.setdefault("User-Agent", USER_AGENT)
    mp4 = resolve_mp4_url(play_id, sess)
    if not mp4:
        raise RuntimeError(f"No mp4 embed found for playId={play_id}")
    for attempt in range(1, attempts + 1):
        with sess.get(mp4, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 16):
                    if chunk:
                        f.write(chunk)
        if is_decodable(dest):
            break
        # Truncated transfer. Discard rather than leave a file that looks fetched.
        dest.unlink(missing_ok=True)
        if attempt == attempts:
            raise RuntimeError(f"Clip for playId={play_id} would not decode after {attempts} attempts")
    meta = {
        "play_id": play_id,
        "source": "baseball_savant_sporty_videos",
        "angle": "CF",
        "note": "Pitch-type overlay ignored for CV features; join Statcast labels separately.",
    }
    (out_dir / f"{play_id}.meta.json").write_text(json.dumps(meta, indent=2))
    return dest


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Apex Preflight — Savant clip fetch")
    p.add_argument("--play-id", required=True, help="Savant / Statcast playId UUID")
    p.add_argument("--out", type=Path, default=Path("clips"), help="Output directory")
    args = p.parse_args(argv)
    path = download_play_clip(args.play_id, args.out)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
