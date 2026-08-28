# Catcher tracking measured the pitcher, not the catcher

**Found:** 2026-08-26. **Status:** tracking guard landed; catcher tracking deferred to
detector-based localization. Catcher runs are skipped in the league pipeline
(`cv/run_league.sh` passes `--skip-catchers`).

## What was wrong

Every catcher feature persisted by `cv/preflight/track_pitcher.py` —

- `catcher_glove_x`, `catcher_glove_y`
- `catcher_stance_width`
- `catcher_hip_y`
- `catcher_glove_speed`

— was describing the **pitcher's body** in the large majority of frames, and so was
every catcher setup tip derived from them via `CATCHER_FEATURE_PREFIXES` in
`cv/preflight/run_catcher_poc.py`.

Measured on tracks written by the current tracker:

| Run | frames where the "catcher" pose IS the pitcher | frames with only 1 pose detected |
|---|---|---|
| `catcher_james_mccann_poc` | **90.9%** (n=5,312) | 77% |
| `catcher_gabriel_moreno_poc` | **71.3%** (n=2,204) | 65% |

The clearest single piece of evidence: `catcher_hip_y` had a median of **0.574**
against the pitcher's hip midpoint median of **0.573** — not a similar
distribution, the same body. `catcher_stance_width` had a median of 0.012
normalized units, far too narrow for a squatting catcher's hips.

## Cause

Subject selection ended in an unconditional fallback:

```python
by_hip = sorted(pose_res.pose_landmarks, key=pose_hip_y, reverse=True)
for cand in by_hip:
    if cand is not plm or len(pose_res.pose_landmarks) == 1:
        clm = cand
        break
if clm is None:
    clm = by_hip[0]          # <-- fires whenever no other pose exists
```

MediaPipe returns a **single** pose on 65-77% of these frames despite
`num_poses=3`: in CF framing the catcher is small, low, and occluded by the
umpire directly behind him. So the fallback fired constantly and returned the
pitcher, who was the only pose available.

This is the same failure as the earlier "largest torso in frame" bug that tracked
hitters instead of pitchers, but at 71-91% rather than ~11%.

## Guard

`clm` is now only assigned when at least two distinct poses are detected AND the
pitcher has been identified, so the catcher pose is necessarily a different body.
There is deliberately **no fallback**: when the catcher is not detected the
catcher columns stay empty rather than carrying another player's coordinates.

The principle is the one applied to the game-level holdout requirement: make the
invalid state unrepresentable rather than relying on a reader remembering the
caveat. A populated-looking column that is structurally meaningless is worse than
a missing one, because it passes gates.

Note this guard makes the catcher columns *mostly empty* on current footage. That
is the honest state of the measurement, not a regression.

## How catcher tracking should be done

Do not rebuild the pose-based selector; it cannot work, because the catcher
usually is not detected as a pose at all in the CF view. The approach is
detector-based localization:

1. Detect the catcher region with the trained parts detector — `parts_gear.pt`
   already carries a `catcher_mitt` class. Production entry point is
   `cv/preflight/parts_detect.py`.
2. Crop to that region and run pose on the crop, where the catcher is large
   enough to land landmarks reliably.
3. Persist the catcher's landmarks per frame the way `KEEP_LANDMARKS` does for
   the pitcher, so catcher setup and PitchCom features can be re-derived later
   without another tracking pass.

Catcher setup and catcher PitchCom remain a primary tip source — they are among
the few cues visible early enough to relay to a hitter — so this is deferred, not
abandoned.

## Related

Two other defects found the same day share this shape: a value that looks
populated and passes a gate while being structurally meaningless.

- **Degenerate holdout.** `split_games_train_test` fell back to a pitch-level
  split for single-outing arms and reported the same `game_pk` as both train and
  test. Now returns empty frames, and the sanity gate and provenance guard both
  require disjoint game sets.
- **PitchCom tap detection.** `pitchcom_tap_count` reports more taps on
  phase-shuffled noise than on real footage and fires at a flat rate seconds
  before the set: it is glove-motion variance, not an event detector.

Worth screening other features for the same pattern — a summary statistic
masquerading as an event detector.
