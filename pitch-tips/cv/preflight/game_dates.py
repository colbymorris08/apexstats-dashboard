"""
Real calendar dates for game_pks, so games can be ordered chronologically.

Why this exists
---------------
Recency is the whole point of the current protocol: a pitcher who is told he is
tipping will correct it, so a cue from April may genuinely be gone by August.
Selecting the most recent starts and validating on the latest ones requires
knowing when each game was played, and no feature table on disk carries a date —
only ``game_pk``.

``game_pk`` is assigned in schedule order, so sorting by it is very nearly the
same as sorting by date. "Very nearly" is not good enough for something the
protocol now rests on, so the dates are fetched once, cached, and the proxy is
checked against them rather than assumed. ``verify_pk_ordering`` reports exactly
how often the two orderings disagree.

The cache is a plain JSON map committed alongside the runs, so every downstream
split is reproducible without network access.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

CACHE = Path(__file__).resolve().parents[2] / "runs" / "game_dates.json"
API = "https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live"


def load_cache(path: Path | None = None) -> dict[str, str]:
    p = path or CACHE
    if p.is_file():
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}
    return {}


def save_cache(d: dict[str, str], path: Path | None = None) -> None:
    p = path or CACHE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dict(sorted(d.items())), indent=2))


def fetch_dates(pks, path: Path | None = None, sleep: float = 0.05) -> dict[str, str]:
    """Official date for each game_pk, fetched once and cached.

    Uses the same endpoint and the same ``gameData.datetime.officialDate`` field
    that ``run_poc`` already uses to pick a pitcher's most recent starts, so the
    ordering here agrees with the ordering the pipeline selects on.
    """
    import requests

    cache = load_cache(path)
    todo = [str(int(p)) for p in pks if str(int(p)) not in cache]
    if not todo:
        return cache
    sess = requests.Session()
    for i, pk in enumerate(todo, 1):
        try:
            js = sess.get(API.format(pk=pk), timeout=20).json()
            date = ((js.get("gameData") or {}).get("datetime") or {}).get("officialDate")
            if date:
                cache[pk] = date
        except Exception:
            pass
        if i % 25 == 0:
            save_cache(cache, path)
            print(f"  fetched {i}/{len(todo)}", flush=True)
        time.sleep(sleep)
    save_cache(cache, path)
    return cache


def date_of(pk, cache: dict[str, str] | None = None) -> str | None:
    c = cache if cache is not None else load_cache()
    return c.get(str(int(pk)))


def order_games(pks, cache: dict[str, str] | None = None) -> list:
    """Game_pks sorted oldest to newest.

    Games with no known date sort last, keyed by game_pk, so an unresolved date
    degrades to the proxy ordering for that game alone rather than silently
    reordering the whole arm.
    """
    c = cache if cache is not None else load_cache()
    uniq = sorted({int(p) for p in pks})
    return sorted(uniq, key=lambda p: (c.get(str(p)) or "9999-99-99", p))


def verify_pk_ordering(pks, cache: dict[str, str] | None = None) -> dict:
    """How often ordering by game_pk disagrees with ordering by date.

    Reported rather than assumed, because the whole temporal protocol rests on
    the ordering being right.
    """
    c = cache if cache is not None else load_cache()
    known = [(int(p), c[str(int(p))]) for p in {int(x) for x in pks} if str(int(p)) in c]
    known.sort(key=lambda t: t[0])
    inversions = sum(
        1
        for i in range(len(known))
        for j in range(i + 1, len(known))
        if known[i][1] > known[j][1]
    )
    pairs = len(known) * (len(known) - 1) // 2
    return {
        "n_with_dates": len(known),
        "n_missing": len({int(x) for x in pks}) - len(known),
        "pairs": pairs,
        "inversions": inversions,
        "agreement": (1.0 - inversions / pairs) if pairs else float("nan"),
    }


def main() -> None:
    import argparse
    import glob

    import pandas as pd

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default="runs/*_poc")
    args = ap.parse_args()
    pks = set()
    for f in glob.glob(f"{args.runs}/features.csv"):
        try:
            pks |= set(pd.read_csv(f, usecols=["game_pk"]).game_pk.dropna().astype(int))
        except Exception:
            continue
    print(f"resolving dates for {len(pks)} game_pks")
    cache = fetch_dates(pks)
    v = verify_pk_ordering(pks, cache)
    print(f"cached dates: {len(cache)}")
    print(f"game_pk vs date ordering: {v['inversions']} inversions of {v['pairs']} pairs "
          f"-> {v['agreement']:.4%} agreement ({v['n_missing']} games without a date)")


if __name__ == "__main__":
    main()
