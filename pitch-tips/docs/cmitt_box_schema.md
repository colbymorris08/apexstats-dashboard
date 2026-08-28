# `cmitt_*` box schema — implementable spec

**Status:** ready to implement now. **Version:** `cmitt_boxes_v1`.
**Reference implementation:** `cv/preflight/catcher_boxes.py` — that module *is* the
schema. Import it; do not reimplement the column names.

## Integration, in three lines

```python
from preflight.catcher_boxes import blank_row, box_row, detect_gear, provenance_block

# frames inside the pass:
row.update(box_row(detect_gear(frame), frame_w, frame_h))

# frames outside it (never examined — all blank, including cmitt_n):
row.update(blank_row(examined=False))

# once per clip, into *_summary.json:
summary["parts_boxes"] = provenance_block(stride=1)
```

`box_row` and `blank_row` both return all 21 keys, so `csv.DictWriter` fieldnames
stay stable whether or not anything was detected and whether or not the frame was
examined.

**Read the cost section below before deciding where to call it** — a stride-1 pass
over every frame adds ~56 s per clip, and there is a ~20 s option that gives better
precision.

## Cost — read this before choosing where to call it

Use `detect_gear`, not `detect_parts`. All four persisted classes live in
`parts_gear.pt`; `detect_parts` also runs `parts_glovehand.pt`, which contributes
nothing here. Measured back to back on real frames, warmed, model load excluded:

| | s/frame | 240-frame clip |
|---|---|---|
| `detect_gear` (gear only) | **0.235** | 56 s |
| `detect_parts` (both models) | 0.533 | 128 s |

So gear-only saves 56%. **But correcting my own earlier estimate: I previously said
~0.06 s/frame and that was wrong** — it came from a probe run on an idle machine,
and the numbers above were taken with the pipeline and fetcher running, which is the
condition that matters. Expect 0.12–0.24 s/frame depending on contention.

At 0.235 s/frame, a naive stride-1 pass over every frame adds ~56 s to a clip that
currently costs ~7 s. That is an 8x increase in tracking time and it is not worth
paying, because most of those frames are outside the span where the cue lives.

### Recommended: a second bounded pass over the actionable span only

The cue only ever reads in-window frames, and in-window is where the mitt is most
detectable anyway (0.645 in window vs 0.230 outside). So:

1. Track as now, and write the track.
2. Compute the window from the track you just wrote — `actionable_window(df)` plus
   `preset_segment(df, win)`, which needs no pixels.
3. Re-open the clip and run `detect_gear` only on frames `[lo - 15, hi + 15)`.

Cost: a median span is ~58 frames, so ~88 frames with margin ≈ **20 s per clip**,
against 56 s for the whole clip. The 15-frame margin exists so a future change to
the window boundaries does not immediately invalidate every box written — cheap
insurance at ~7 s.

Re-decoding a ~5.6 MB mp4 is around a second and does not need the clip retained
afterwards, so this composes with the janitor.

For frames outside the pass, leave the columns blank. That is honest: they were
never examined, and `cmitt_n` being blank rather than `0` distinguishes exactly
that case. (Within the pass, `cmitt_n` is `0` when nothing credible was found.)

### If you prefer one pass, use a stride

Quantified rather than guessed. Mitt centre-x jitter is 0.05 plate widths
frame-to-frame, so the standard error of a per-pitch median goes:

| stride | SE (plate widths) | vs the cue's 0.06 visibility floor | added cost/clip |
|---|---|---|---|
| 1 | 0.040 | clears | 56 s |
| 2 | 0.057 | clears | 28 s |
| 3 | 0.069 | **fails** | 19 s |

**Stride 3 is not acceptable** — the cue stops clearing its own visibility floor, so
the boxes would be written and then be unusable. Stride 2 whole-clip (28 s) costs
more than the bounded pass (20 s) and yields worse precision, so the bounded pass is
the better trade on both axes.

Record whichever you choose in `provenance_block(stride=...)`.

## Columns — 21 total

Four classes × five fields, plus one count.

| class | prefix | columns |
|---|---|---|
| `catcher_mitt` | `cmitt` | `cmitt_cx cmitt_cy cmitt_bw cmitt_bh cmitt_conf` |
| `plate` | `cplate` | `cplate_cx cplate_cy cplate_bw cplate_bh cplate_conf` |
| `catcher_shin` | `cshin` | `cshin_cx cshin_cy cshin_bw cshin_bh cshin_conf` |
| `catcher_cleat` | `ccleat` | `ccleat_cx ccleat_cy ccleat_bw ccleat_bh ccleat_conf` |
| — | — | `cmitt_n` |

Against a 72-column track that is +29%. If that is too much, the two anchor classes
(`cshin`, `ccleat`) are the droppable ten — see "what each class is for" below for
what dropping them costs. `cmitt` and `cplate` are not negotiable; `cplate` in
particular is what makes the cue survive park-to-park zoom, and a mitt coordinate
without it is raw image position carrying camera pan.

### Coordinate convention

* `cx`, `cy` — box **centre**, normalised to the **full frame**, `x` rightward and
  `y` **downward** (image convention, matching every existing coordinate in the
  tracks). Always full-frame, even if a detection ever comes from a crop.
* `bw` — box width as a fraction of frame **width**.
* `bh` — box height as a fraction of frame **height**.
* All in `[0, 1]`. Coordinates rounded to 5 dp, confidence to 4.

Both `bw` and `bh` are needed and neither is redundant: `cplate_bw` is the unit
every lateral cue is expressed in, and `cshin_bh`/`ccleat_bh` size the catcher crop.

### One box per class per frame

The highest-confidence one. Extra candidates are not persisted — except that
`cmitt_n` counts them.

`cmitt_n` earns its column: two credible mitt boxes in a frame means at least one is
on something else, and a consumer that cannot distinguish "one confident mitt" from
"the most confident of several candidates" is one step from the wrong-object failure
this project keeps finding.

**It counts at `AMBIGUITY_CONF = 0.25`, not at the write floor.** Measured on real
frames, the mitt class returns **5–8 boxes per frame** at the 0.05 write floor,
because that floor admits the whole noise lobe by design. Counting there gives a
roughly constant number with no information in it — a plausible-looking column that
says nothing, which is the exact defect this schema exists to avoid. At 0.25 the
count is normally 1–2, which is a real answer to a real question.

Three states, all distinguishable:

| `cmitt_n` | meaning |
|---|---|
| `0` | frame was examined, no credible mitt found |
| `1`, `2`, … | number of credible mitt candidates |
| blank (NaN) | **frame was never examined** — outside the bounded pass |

Use `blank_row(examined=False)` for the third. Collapsing it into `0` would assert
an absence that was never measured.

### Absence

**Empty string**, which reads back as NaN through pandas. Consistent with how the
tracker already writes a missing landmark.

* No sentinel number, no zero, no `-1`.
* **No carry-forward from the previous frame**, and no substitution from a nearby
  frame or from the other classes. A plausible stand-in for a missing detection is
  the mechanism behind four of this project's six retractions.
* A class is blank in **all five** of its columns or in none of them. Never
  partially — a half-populated box is a box a consumer can silently misread.

### Confidence

Persist the detector's confidence **as returned, unthresholded** above a permissive
write floor of `WRITE_CONF = 0.05` (the detector's own floor).

Do not gate harder at write time. It is unrecoverable without another pixel pass,
and it repeats the cheek-column mistake: a value discarded at write time cannot be
reconsidered, and confidence is itself information. Consumers apply their own floor
— `catcher_target.MITT_CONF` is 0.25, which is the loosest level at which mitt boxes
were rendered and confirmed to be on the mitt.

## `catcher_mask` is excluded — do not add it

Not persisted, and it must not be added later without new evidence.

It fires on **77.5% of frames**, the joint-highest rate in the catcher family, and
the rendered boxes land on the **umpire's head** — he stands directly behind the
catcher wearing the same equipment and the class cannot tell them apart. It is the
most dangerous class in this model precisely because it looks like the best one by
coverage. Carrying it forward would launder that error into a fresh column with a
clean name.

The exclusion and its reason travel in `provenance_block()["excluded_classes"]`, so
the record survives in the data rather than only in this document.

## What each class is for

| class | why persisted | cost of dropping |
|---|---|---|
| `catcher_mitt` | the cue subject: where the mitt is set | the whole family |
| `plate` | the reference; all cues are in plate widths from the same frame | cue becomes camera-frame position, unusable across parks |
| `catcher_shin` | localisation anchor for any future catcher pose attempt | another full pixel pass to recover |
| `catcher_cleat` | second anchor; anchor agreement is the subject evidence | anchors can no longer corroborate each other |

## Provenance — in `*_summary.json`, not per row

`provenance_block()` returns schema version, model filename, `model_sha256_24`,
byte size, write floor, stride, persisted and excluded classes, column list, and
the coordinate/absence conventions.

The hash matters more than usual here. `parts_gear.pt` is trained on 28
fully-labeled frames and is about to be retrained on a park-diverse labelling set,
so tracks written before and after will carry boxes of **materially different
quality under identical column names**. A mismatch against
`model_sha256_24_at_schema_v1 = "15891fea835eecbb406765e2"` is not an error — it
means the retrain happened, which is the plan — but it has to be visible. Mixing
the two silently is how a coverage artifact becomes an effect size.

## Reading it back

```python
from preflight.catcher_boxes import has_box_schema, read_boxes

cx, cy, bw, bh, conf = read_boxes(df, "catcher_mitt")
```

Returns all-NaN arrays for pre-schema tracks rather than raising: such a track
genuinely has no information here, which is what NaN means.

## Known limitation this schema does not fix

The detector does not generalise across parks. In-window plate detection was 1.00
on four Woo clips and **0.00** on three Gallen clips; whole-clip plate rate 45.4%
vs 22.5%. Persisting boxes preserves whatever the current model can see — it does
not make it see more.

So expect `cmitt_*` to be well-populated on some arms and near-empty on others, and
**report per-arm coverage alongside any result derived from these columns.** Coverage
that varies by park varies by opponent, which is a confound capable of manufacturing
an effect. The fix is the retrain, not the schema.
