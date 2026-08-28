# Limit: the pre-set period is not covered by the source film

Status: **structural, not fixable by re-tracking or re-fetching.**

A distinct entry alongside resolution, sightline, precision and sample. Unlike
the frame-rate units error, no code change recovers this.

## The claim

The pre-set period — the seconds in which the pitcher comes set, sways, settles
and the catcher sets up — **has never been properly measurable in this corpus.**
A large share of the scouted cues live there, including coming-set movement and
sway, and it is the part of the delivery a runner on second or a coach in the
dugout would read earliest. It is the most actionable window we have, and the
film mostly does not contain it.

## Evidence

Frame rate, verified two independent ways:

- Track timestamps across all ten arms: 600 of 600 tracks at 60 fps, uniform.
- Direct decoding of 33 source mp4s across 9 arms and 9 parks: 59.51–59.80 fps.

Source clip length, by decoding frames rather than trusting container metadata:

| Measure | Value |
|---|---|
| Decoded frames, min / median / max | 358 / ~440 / 1336 |
| Duration at 59.6 fps, median | ~7.3 s |
| Clips containing exactly 180 frames | 0 of 33 |

So the clips are long enough in total. The problem is where they *start*:

| Measure | Value | n |
|---|---|---|
| `window_start_frame`, median | 25 frames (0.42 s) | 5,406 |
| Clips whose window opens at frame 0 | ~31% | 5,406 |
| Frames needed for a 1.5 s pre-set lookback at 60 fps | 90 | — |

A correct lookback needs 90 frames of lead-in. The typical clip provides 25, and
in roughly a third there is none at all: the clip already opens with the pitcher
settled or moving. `PRESET_LOOKBACK = 45` frames was reasoned at 30 fps, where it
meant 1.5 s; at the true 59.6 fps it is 0.75 s, and even that does not fit.

Savant serves a fixed cut per `playId` and it cannot be extended backwards; see
`docs/clip_lead_in.md`.

## What this is NOT

Do not conflate this with the `max_frames` cap, which was a separate and real
bug. Tracking stopped at 180 frames — 3.0 s at 60 fps, not the 6.0 s assumed —
discarding a median 61% of each clip. That cap is now `MAX_TRACK_FRAMES = 240`
in `track_pitcher.py`, applied to new tracking only.

**Raising the cap does not help this limit.** The truncation was at the *end* of
the clip and the pitch happens early: `delivery_frame` has median 83 and p90 164.
Footage beyond frame 180 is ball flight, the catch, batter reaction and replay —
nothing a pre-pitch tip can use. The corpus was deliberately not re-fetched for
this reason.

Nor is it the cause of the ~10% of clips yielding no window. Those were tested
directly: over their final 20 tracked frames the pitcher shows median wrist travel
of 0.049 torso lengths per frame with **0% idle**, indistinguishable from clips
that did window (0.058). They are in full motion at the cap, so they were not
waiting to deliver beyond it. Those are window-detection failures.

## Consequence for interpretation

This is a plausible structural contributor to the universal null. Cues that were
measured in the pre-set period were measured on 0–25 frames of lead-in, often
zero, which is far too little to characterise a settle or a rock out-and-back.
A null on those cues is therefore **not evidence that the cue does not exist** —
it is substantially uninformative, and should be reported as underpowered by
coverage rather than as a tested negative.

A corrected-window re-run can fix the window's units. It cannot make the window
cover its designed pre-set span from this footage. Answering the sway and
coming-set questions needs a different film source with earlier cut-in, not more
processing of these clips.
