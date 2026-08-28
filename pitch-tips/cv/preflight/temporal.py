"""
Recency-ordered game selection and chronological (temporal) validation.

Why chronological rather than random
------------------------------------
A pitcher who is told he is tipping corrects it. So a cue that was real in April
may genuinely be gone by August, and a random split across a season does two bad
things at once: it dilutes a real recent tip with games where it no longer exists,
and it lets a stale tip validate against its own era.

The split here mirrors deployment: fit on the earlier starts, predict the next
ones. Learn from past outings, then face a future one. This is *stricter* than a
random game split, not merely different — a cue that only survives when past and
future games are shuffled together is not something a club could use anyway,
because in use the future games are the ones you have to call.

Ordering is by real calendar date, never by ``game_pk``. That is not a stylistic
choice: measured across the 93 games on disk, ordering by ``game_pk`` agrees with
ordering by date on only **53.8%** of pairs, which is indistinguishable from
random. The intuition that a game key increases with the schedule does not hold in
this data, and building the temporal protocol on it would have silently produced a
scrambled split that still looked chronological. See ``game_dates.py``.

Every existing guarantee is preserved. The two sides are disjoint game sets by
construction, both must be non-empty, and an arm that cannot supply both is
reported as underpowered rather than split into something degenerate.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import pandas as pd

from preflight import game_dates, spot_diff

# Protocol: discover on the 3 most recent starts, validate on the next 6 going
# back. Fixed here rather than passed around, so it cannot drift per arm.
#
# Discovery sits on the freshest film because that is where a live tip would be:
# a pitcher who is told he is tipping corrects it, so a cue found in April may not
# exist now. Validation then gets 2-3x as many pitches as discovery, which is what
# a precision estimate actually needs — precision is a proportion measured only on
# the pitches where a rule fires, so it is the noisiest number on the board and the
# one that most needs sample.
#
# Note this is not the usual "train on the past, test on the future" direction. It
# tests something different and, for this purpose, more useful: whether a cue
# visible in the most recent film is a persistent property of the pitcher rather
# than a feature of three outings. A cue that fails here was a three-start
# coincidence.
N_DISCOVERY_STARTS = 3
N_VALIDATION_STARTS = 6
N_RECENT_STARTS = N_DISCOVERY_STARTS + N_VALIDATION_STARTS


def game_keys(df: pd.DataFrame) -> pd.Series:
    """Game keys as integers, with unassignable rows marked -1.

    A pitch with no ``game_pk`` cannot be placed on either side of a game-level
    boundary, so it is excluded from both rather than coerced into one. Coercing
    would put pitches of unknown provenance into a validation set, which is the
    kind of quiet contamination the disjoint-split rule exists to prevent.
    """
    if "game_pk" not in df.columns:
        return pd.Series(-1, index=df.index, dtype=int)
    return pd.to_numeric(df["game_pk"], errors="coerce").fillna(-1).astype(int)


def game_order(df: pd.DataFrame, cache=None) -> list[int]:
    """Every game this arm has, ordered oldest-first by calendar date.

    Ordering comes from the ``game_date`` column the pipeline now writes into each
    pitch row, taken from the game feed's ``officialDate``. ``game_pk`` is
    explicitly *not* used for ordering: it does not sort by date, and a split built
    on it would put the wrong outings on the wrong side of the boundary while
    looking perfectly well-formed.

    A date is required to be unique per game. If one game carries two dates the
    row-level column is inconsistent and we fall back to the API date cache rather
    than picking one, because silently choosing would corrupt the ordering.
    """
    if "game_pk" not in df.columns:
        raise ValueError("cannot order games without game_pk")
    keys = game_keys(df)
    pks = [int(g) for g in keys.unique() if g >= 0]

    if "game_date" in df.columns:
        dates = (
            pd.DataFrame({"pk": keys, "date": df["game_date"].astype("string")})
            .loc[keys >= 0]
            .dropna()
            .groupby("pk")["date"]
            .agg(lambda s: sorted(set(s)))
        )
        by_pk = {int(k): v[0] for k, v in dates.items() if len(v) == 1}
        if len(by_pk) == len(pks):
            return sorted(pks, key=lambda p: (by_pk[p], p))

    return game_dates.order_games(pks, cache)


def recent_games(df: pd.DataFrame, n: int = N_RECENT_STARTS, cache=None) -> list[int]:
    """The ``n`` most recent games this arm actually has, oldest-first.

    Returned in chronological order so the caller can take the tail as the
    validation set without re-sorting.
    """
    return game_order(df, cache)[-n:]


def n_games_available(df: pd.DataFrame) -> int:
    """Total dated starts banked for this arm, ignoring the protocol cap.

    Used to decide whether a convergence curve is computable: the cap limits what
    is *analysed*, not what exists, and a deep arm can support a stability check
    that a capped one cannot.
    """
    keys = game_keys(df)
    return int((keys[keys >= 0]).nunique())


def temporal_split(
    df: pd.DataFrame,
    n_disc: int = N_DISCOVERY_STARTS,
    n_val: int = N_VALIDATION_STARTS,
    cache=None,
) -> tuple[list[int], list[int]]:
    """Game keys for (discovery, validation) under the recency protocol.

    Discovery is the ``n_disc`` most recent starts; validation is the ``n_val``
    starts immediately before them. Both lists are non-empty and disjoint or a
    ``ValueError`` is raised. Refusing is deliberate: a temporal split must not be
    allowed to degenerate the way an earlier single-game split did, where an empty
    or overlapping side produced a result that still looked valid.
    """
    games = recent_games(df, n_disc + n_val, cache)  # oldest-first
    if len(games) < 2:
        raise ValueError(f"only {len(games)} game(s) available; cannot split")
    # Never let discovery consume every game: validation must keep at least one.
    k = min(n_disc, len(games) - 1)
    disc, val = games[-k:], games[:-k]
    if not disc or not val:
        raise ValueError("degenerate temporal split")
    if set(disc) & set(val):
        raise ValueError("temporal split produced overlapping game sets")
    return disc, val


@contextmanager
def chronological(disc_games, val_games):
    """Make ``spot_diff.analyse`` split on a fixed pair of game sets.

    ``analyse`` splits inside each delivery stratum, so patching the split
    function rather than pre-slicing the frame keeps one consistent
    earlier/recent boundary across both strata — a stratum-local split could
    otherwise put the same game on opposite sides for stretch and windup.

    Everything else about ``analyse`` is untouched: the same FDR, the same effect
    and visibility floors, the same replication test. Only which games are on
    which side changes.
    """
    disc_set, val_set = set(int(g) for g in disc_games), set(int(g) for g in val_games)
    original = spot_diff.split_by_game

    def fixed(df: pd.DataFrame, fraction: float = None):  # noqa: ARG001
        keys = game_keys(df)
        return df[keys.isin(disc_set)], df[keys.isin(val_set)]

    spot_diff.split_by_game = fixed
    try:
        yield
    finally:
        spot_diff.split_by_game = original


def describe(df: pd.DataFrame, disc, val, cache=None) -> dict[str, Any]:
    """Human-readable account of what the split actually selected."""
    c = cache if cache is not None else game_dates.load_cache()
    def dates(gs):
        return [game_dates.date_of(g, c) or "unknown" for g in gs]
    return {
        "n_games_available": int((game_keys(df) >= 0).pipe(lambda m: game_keys(df)[m].nunique())),
        "n_pitches_without_a_game_key": int((game_keys(df) < 0).sum()),
        "discovery_games": [int(g) for g in disc],
        "validation_games": [int(g) for g in val],
        "discovery_dates": dates(disc),
        "validation_dates": dates(val),
        "n_discovery_pitches": int(game_keys(df).isin(set(map(int, disc))).sum()),
        "n_validation_pitches": int(game_keys(df).isin(set(map(int, val))).sum()),
    }
