"""
Situation definitions, and the census of what is actually testable inside them.

The hypothesis is that a tip may be situation-specific: an arm that never tips
with the bases empty may tip with a runner on second, when he changes his look,
uses a slide step, works faster, or gets sloppy holding the runner. Pooling every
situation together — which is what the analysis has done so far — would wash that
out. So the contrast to run is *within* a situation: all sliders with a runner on
second against all other pitch types with a runner on second.

Why these four situations and no more
-------------------------------------
Every situation added raises the FDR bar for all the others, so this is a
prioritised list with a mechanistic reason for each, not an enumeration:

``runner_on_2nd``  The one that matters most, and not only mechanically. Second
    base is the vantage from which a tip can actually be seen and relayed, so a
    tip that exists there is the most commercially valuable kind. It is also the
    base state that most changes a pitcher's behaviour.
``runners_on``     Any runner. Broader and better-populated than the above, and it
    separates "pitching from the set" from "pitching with nobody on" without
    requiring the runner to be on second specifically.
``bases_empty``    The control for the two above. Without it a difference found
    with a runner on second cannot be attributed to the runner.
``two_strikes``    The count state where pitch selection narrows hardest, so if
    predictability rises anywhere in the count it is here.

Deliberately excluded: the full count grid, outs, inning, score state, handedness
crossed with base state. Each is plausible; none is well enough motivated to be
worth the correction burden it would impose on the four above.

Situation is not delivery
-------------------------
Base state and delivery are correlated but not the same thing, and conflating them
would attribute a delivery difference to a situation. Plenty of arms work
exclusively from the stretch with the bases empty. So every situational contrast is
run inside a delivery stratum, and ``purity`` reports the confound per arm
empirically rather than assuming it.
"""
from __future__ import annotations

from typing import Callable

import pandas as pd

# Ordered by priority. The order is load-bearing: it is the order they are run and
# reported in, and it reflects mechanistic rationale, not cell size.
SITUATIONS: dict[str, dict] = {
    "runner_on_2nd": {
        "label": "runner on second",
        "mask": lambda d: d["on_2b"].fillna(False).astype(bool),
        "why": "the vantage a tip is relayed from, and the base state that most "
               "changes a pitcher's look, tempo and hold",
    },
    "runners_on": {
        "label": "any runner on",
        "mask": lambda d: (d["on_1b"].fillna(False).astype(bool)
                           | d["on_2b"].fillna(False).astype(bool)
                           | d["on_3b"].fillna(False).astype(bool)),
        "why": "pitching from the set with something to hold, pooled for power",
    },
    "bases_empty": {
        "label": "bases empty",
        "mask": lambda d: ~(d["on_1b"].fillna(False).astype(bool)
                            | d["on_2b"].fillna(False).astype(bool)
                            | d["on_3b"].fillna(False).astype(bool)),
        "why": "the control: without it, a difference with a runner on cannot be "
               "attributed to the runner",
    },
    "two_strikes": {
        "label": "two strikes",
        "mask": lambda d: pd.to_numeric(d["strikes"], errors="coerce") >= 2,
        "why": "the count state where pitch selection narrows hardest",
    },
}


def mask_for(df: pd.DataFrame, key: str) -> pd.Series:
    fn: Callable = SITUATIONS[key]["mask"]
    need = {"on_1b", "on_2b", "on_3b", "strikes"}
    missing = need - set(df.columns)
    if missing & _cols_used(key):
        raise ValueError(f"{key} needs columns missing from this run: {missing}")
    return fn(df).fillna(False).astype(bool)


def _cols_used(key: str) -> set[str]:
    return {
        "runner_on_2nd": {"on_2b"},
        "runners_on": {"on_1b", "on_2b", "on_3b"},
        "bases_empty": {"on_1b", "on_2b", "on_3b"},
        "two_strikes": {"strikes"},
    }[key]


def purity(df: pd.DataFrame, key: str, delivery: pd.Series) -> dict:
    """How strongly this situation determines the delivery, measured not assumed.

    If a situation is 100% stretch then its windup cells are *absent*, not null,
    and reporting them as "no difference found" would be false. This number is what
    lets the report say which of the two it is.
    """
    m = mask_for(df, key)
    if m.sum() == 0:
        return {"n": 0, "share_stretch": None, "delivery_pure": None}
    d = delivery[m].astype(str)
    share = float((d == "stretch").mean()) if len(d) else None
    return {
        "n": int(m.sum()),
        "share_stretch": round(share, 3) if share is not None else None,
        # "Pure" means the situation offers no contrast in the other stratum, so
        # only one stratum is testable and the other must be reported as absent.
        "delivery_pure": (share is not None and (share >= 0.98 or share <= 0.02)),
    }
