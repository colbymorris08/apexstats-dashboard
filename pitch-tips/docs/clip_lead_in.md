# Clip lead-in: there is no knob to turn

**Decision: do not re-fetch clips for more pre-set lead-in. It is not available
from the source.** Recorded because the sway / coming-set work was planned around
the premise that a re-fetch with more lead-in would roughly triple coverage of
the pre-set segment. That premise does not hold, and acting on it would cost a
night of fetching and return byte-identical files.

## What the source actually gives us

Clips come from the Savant sporty-videos embed, one pre-rendered mp4 per
`playId` (`fetch_savant.resolve_mp4_url`). The request carries a play id and
nothing else: there is no start offset, no duration, no trim parameter. We
receive the asset as MLB rendered it.

Measured across all 381 clips of `drew_thorpe_rich_poc`:

```
frames/clip: min=180  p10=180  median=180  p90=180  max=180
```

Exactly 180 frames — 6.0 s at 30 fps — with zero variance. A fixed-length
render, not a window we are choosing badly.

## So why is pre-set coverage thin?

The shortfall is not the clip being cut short at the front. It is where the set
falls inside a clip whose length is fixed:

```
window_start_frame (frames of lead-in before the set), n=286
  >=  8 frames: 161 (56.3%)
  >= 15 frames: 149 (52.1%)
  >= 30 frames: 117 (40.9%)
  >= 45 frames:  91 (31.8%)   <- PRESET_LOOKBACK
```

The delivery sits at a median of frame 70, so the back of the clip is roomy. For
the thin cases the pitcher was already at or near the set when the render opened.
Those frames do not exist in any asset we can request, so no re-fetch recovers
them, and neither does re-processing the cached mp4s.

## Cost, had it been possible

Cached clips run ~5.6 MB each (Kelly: 2.5 GB / 447 clips). Re-fetching the five
priority arms would be roughly 14 GB and hours of pure download, on top of
tracking — against zero expected gain.

## What this means for the sway family

The cue survives on the ~56% of pitches with at least 8 frames of lead-in and the
~32% that clear `PRESET_LOOKBACK`; it cannot be rescued to full coverage by
fetching. Whether it clears the group minimums on that subset is a question for
`spot_diff` under the current gates, not something to fix upstream. Coverage
should be reported as the constraint it is rather than treated as a bug.

Chasing a different feed with a custom trim would be a new video integration.
That was declined tonight as a destabilizing change under a depth deadline; the
depth run and the ground-truth re-tracks are the priority.
