# Handoff to the analysis agent: what the frame-rate finding does and does not fix

Read `docs/limits_preset_coverage.md` for the evidence. The short version, because
it changes the corrected-window re-run plan:

## 1. Longer tracks ARE obtainable — 180 was the cap, not the clip length

Direct decoding of 33 mp4s across 9 arms and 9 parks: none shorter than 358
frames, median ~440, ~7.3 s at 59.6 fps. Zero clips contain 180 frames. The
tracker was capping at 180 and discarding a median 61% of each clip.

`MAX_TRACK_FRAMES = 240` now applies in `track_pitcher.py`, for **new tracking
only**. The existing corpus was deliberately not re-fetched.

## 2. But raising the cap does NOT recover pre-set lead-in

This is the part that changes your plan. The truncation was at the **end** of the
clip. The pitch happens early — `delivery_frame` median 83, p90 164 — so the
recovered footage is ball flight, the catch and replay.

The pre-set problem is at the **start**: `window_start_frame` median is 25 frames
and ~31% of clips open at frame 0. A 1.5 s lookback needs 90 frames at 60 fps.
Savant cuts cannot be extended backwards (`docs/clip_lead_in.md`).

**So the corrected-window re-run will not answer the sway / coming-set question.**
The window can be made correct in its units; it cannot be made to cover its
designed pre-set span from this footage. Recommend reporting pre-set cues as
underpowered by coverage rather than as tested negatives.

## 3. The ~10% no-window clips are not truncation

Tested directly: over their final 20 tracked frames those tracks show median wrist
travel of 0.049 torso lengths/frame with 0% idle, indistinguishable from clips
that did window (0.058). They are in full motion at frame 179, not waiting to
deliver beyond it. Treat as window-detection failures.

## 4. Mixed track lengths ahead

New tracks will be 240 rows, existing ones 180. `schema_check` keys on columns,
not row count, so old tracks are correctly not flagged stale — but do not assume a
uniform row count when deriving features. Per-clip derivation is unaffected.

## 5. Your restored constants look right to me

Your finding that rescaling stillness thresholds drives them into the noise floor
is consistent with what I see: real motion per frame halves when the frame rate
doubles, but pose-estimator jitter does not, since jitter is a property of one
image pair. Worth stating explicitly in the limits text — it is the reason a
units fix is not a simple arithmetic conversion.
