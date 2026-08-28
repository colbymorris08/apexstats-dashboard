"""
Add ``game_date`` to feature tables written before dates were carried through.

Validation is chronological now — fit on the earlier starts, check against the
most recent — so date is load-bearing rather than metadata. Arms tracked earlier
carry only ``game_pk``, which does not order reliably, and several of them (Kelly
at 25 games especially) are the arms most worth selecting recent starts from.

Only arms reported ``complete`` are touched. Rewriting the features of an arm
that is still being written is what produced the snapshot divergence in the
first place.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from preflight.readiness import write_index  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0"}
FEED = "https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live"


def game_date(pk: int, cache: dict[int, str | None]) -> str | None:
    if pk in cache:
        return cache[pk]
    try:
        js = requests.get(FEED.format(pk=pk), headers=UA, timeout=40).json()
        d = ((js.get("gameData") or {}).get("datetime") or {}).get("officialDate")
    except Exception:
        d = None
    cache[pk] = d
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=Path, default=Path(__file__).resolve().parents[2] / "runs")
    args = ap.parse_args()

    index = write_index(args.runs)["arms"]
    cache: dict[int, str | None] = {}
    for name, st in index.items():
        if st["state"] != "complete":
            print(f"skip {name} (state={st['state']})")
            continue
        f = Path(st["work"]) / "features.csv"
        if not f.is_file():
            continue
        df = pd.read_csv(f)
        if "game_pk" not in df.columns:
            print(f"skip {name} (no game_pk)")
            continue
        if "game_date" in df.columns and df["game_date"].notna().all():
            print(f"ok   {name} (dates already present)")
            continue
        pks = sorted(int(p) for p in df["game_pk"].dropna().unique())
        mapping = {pk: game_date(pk, cache) for pk in pks}
        df["game_date"] = df["game_pk"].map(mapping)
        missing = int(df["game_date"].isna().sum())
        df.to_csv(f, index=False)
        got = sum(1 for v in mapping.values() if v)
        print(
            f"done {name}: {got}/{len(pks)} games dated, "
            f"{len(df) - missing}/{len(df)} pitches carry a date"
        )
    write_index(args.runs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
