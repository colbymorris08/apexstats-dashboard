"""
Calibration checks for the spot-the-difference stage.

A detector that reports nothing is indistinguishable from a detector that is
broken, and this one currently reports very little on real arms. These checks
establish that the silence is a property of the data and not of the code: the
stage must find a difference that was deliberately planted, must stay quiet on
data with nothing in it, and must locate the boundary between the two so the
detection floor can be stated honestly to a club.

Run directly: ``python -m preflight.test_spot_diff``
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from preflight import spot_diff as S

# Pitch-to-pitch spread of a torso-normalised glove cue, from the real
# primitives tables. Planted effects are expressed against it so the reported
# floor is in the units a scout thinks in.
CUE_SD = 0.12
GAMES, PER_GAME = 6, 60


def synthetic(effect: float, seed: int, delivery: str = "stretch") -> pd.DataFrame:
    """
    Two pitch types over several games, every cue pure noise except one.

    ``effect`` is the planted glove-height gap on the slider, in torso lengths.
    Every other cue is independent noise, so the run also exercises the
    multiple-comparison machinery on the ~25 decoys that come with it. Every
    pitch carries a delivery label because the stage refuses to test pitches it
    cannot place in a delivery stratum.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for game in range(GAMES):
        for i in range(PER_GAME):
            pitch = "FF" if i % 2 else "SL"
            row = {"play_id": f"{game}-{i}", "game_pk": game, "pitch_type": pitch,
                   "delivery_type": delivery}
            for cue in S.CUES:
                row[cue] = rng.normal(0.0, 1.0)
            row["glove_height_at_lift"] = rng.normal(0.9 + (effect if pitch == "SL" else 0.0), CUE_SD)
            rows.append(row)
    return pd.DataFrame(rows)


def confounded(seed: int) -> pd.DataFrame:
    """
    The phantom-tip scenario the stratification rule exists to kill.

    No pitch type differs from another WITHIN a delivery. What differs is the
    delivery itself — the glove sits lower from the stretch, as it does for
    every pitcher alive — combined with a mix skew: sliders come mostly from the
    stretch, fastballs mostly from the windup. Pooled, that reads as a large,
    replicating, plainly visible fastball-versus-slider glove-height tip. It is
    not one. It is the stretch.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for game in range(GAMES):
        for i in range(PER_GAME):
            pitch = "FF" if i % 2 else "SL"
            stretch = rng.random() < (0.8 if pitch == "SL" else 0.2)
            row = {
                "play_id": f"{game}-{i}", "game_pk": game, "pitch_type": pitch,
                "delivery_type": "stretch" if stretch else "windup",
            }
            for cue in S.CUES:
                row[cue] = rng.normal(0.0, 1.0)
            row["glove_height_at_lift"] = rng.normal(0.9 - (0.20 if stretch else 0.0), CUE_SD)
            rows.append(row)
    return pd.DataFrame(rows)


def test_finds_planted_tip() -> None:
    res = S.analyse(synthetic(-0.12, 0), "planted")
    assert res["n_surviving"] == 1, res["n_surviving"]
    found = res["differences"][0]
    assert found["feature"] == "glove_height_at_lift"
    assert "slider" in found["scouting_note"] and "lower" in found["scouting_note"]


def test_quiet_on_noise() -> None:
    """Across many null runs, survivors must stay at or under the FDR budget."""
    survivors = [S.analyse(synthetic(0.0, seed), "null")["n_surviving"] for seed in range(20)]
    assert sum(survivors) <= 1, survivors


def test_delivery_confound_does_not_become_a_tip() -> None:
    """
    A pure windup-vs-stretch difference with a skewed pitch mix must not be
    reported as a pitch tip, because within each delivery the pitch types are
    identical.

    Both readings of the same data are run so the comparison is direct: pooling
    the deliveries (by relabelling them into one stratum, which is the only way
    to get a pooled contrast past the guard) manufactures the phantom on nearly
    every seed, while stratifying holds it to the stated FDR budget.
    """
    pooled = 0
    stratified = 0
    for seed in range(8):
        df = confounded(seed)
        flat = df.assign(delivery_type="stretch")
        pooled += S.analyse(flat, "pooled")["n_surviving"] > 0
        stratified += S.analyse(df, "stratified")["n_surviving"] > 0
    assert pooled >= 6, pooled  # the confound is real and pooling reports it
    assert stratified <= 1, stratified  # within-delivery, it is gone


def test_pooled_comparison_is_structurally_refused() -> None:
    """The guard fires on any frame carrying more than one delivery."""
    df = confounded(0)
    try:
        S._groups(df, "glove_height_at_lift", "FF", "SL")
    except ValueError as exc:
        assert "cross-delivery" in str(exc)
    else:
        raise AssertionError("pooled cross-delivery comparison was allowed")


def test_unlabelled_delivery_is_reported_not_pooled() -> None:
    df = synthetic(-0.12, 0)
    df.loc[df.index[:40], "delivery_type"] = ""
    res = S.analyse(df, "partly unlabelled")
    assert res["unlabelled_delivery_pitches"] == 40
    assert res["delivery_mix"].get("unlabelled") == 40


def test_single_delivery_stratum_is_marked_underpowered() -> None:
    """A stratum too thin to test must not read as a clean stratum."""
    df = synthetic(-0.12, 0)
    df.loc[df.index[:6], "delivery_type"] = "windup"
    res = S.analyse(df, "thin windup")
    windup = next(s for s in res["strata"] if s["delivery"] == "windup")
    assert windup["status"] == "underpowered"
    assert windup["n_pitches"] == 6


def test_benjamini_hochberg_matches_reference() -> None:
    p = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216]
    adj, _ = S.benjamini_hochberg(p, 0.05)
    expected = [0.01, 0.04, 0.084, 0.084, 0.084, 0.1, 0.1057, 0.216, 0.216, 0.216]
    assert np.allclose(adj, expected, atol=1e-3), adj


def test_split_never_shares_a_game() -> None:
    df = synthetic(0.0, 1)
    disc, hold = S.split_by_game(df)
    assert not set(disc["game_pk"]) & set(hold["game_pk"])
    assert len(hold) > 0


def detection_floor() -> list[tuple[float, int]]:
    """Share of runs in which a planted effect of each size is recovered."""
    out = []
    for effect in (0.03, 0.05, 0.06, 0.08, 0.12):
        hits = sum(S.analyse(synthetic(-effect, s), "x")["n_surviving"] > 0 for s in range(12))
        out.append((effect, hits))
    return out


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("\ndetection floor (12 runs each, effect in torso lengths):")
    for effect, hits in detection_floor():
        print(f"  {effect:.2f} (g={effect / CUE_SD:.1f}): recovered {hits}/12")
