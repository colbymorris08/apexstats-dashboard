# Catcher localisation: what works, what does not, and what it costs

**Date:** 2026-08-27. **Supersedes the deferral in** `docs/catcher_subject_bug.md`.

Short version, three findings.

1. Detector-based localisation works for *finding* the catcher and fails for
   *articulating* him. A clip-level catcher region is recoverable on every clip
   tried; a pose skeleton on him is recoverable on 3-4% of frames and a bigger pose
   model makes it worse. That kills **catcher stance and catcher mitt angle** as
   measurable cues — two of the three families requested.
2. The pre-pitch glove target survives, needs no skeleton, and where the detector
   fires it measures at about **six times its own noise floor**, against the
   pitcher's glove angle which sat *below* its floor. The premise that the catcher
   faces the camera and should measure better held up.
3. **The coverage needed to use it did not replicate.** It looked good on four Woo
   clips and produced zero usable measurements on three Gallen clips, because the
   `plate` and `catcher_mitt` detector — trained on 28 frames — does not generalise
   across parks. Precision-when-available and availability are separate claims and
   only the first one replicated.

Nothing here has been validated against pitch type — the recency discovery/holdout
protocol has not been run, for the reasons in Step 3. Everything below is a
measurement property. No cue is wired into discovery.

## Step 1 — localisation

### The pose-based selector's guard was already in place; it was not enough

`track_pitcher.py` already refuses to assign a catcher unless two distinct poses
are detected, which stopped the substitution. The consequence is the one the
deferral note predicted: the columns are mostly empty, because in this framing the
catcher usually is not detected as a pose at all.

### The framing is not what the old selector assumed

Worth stating because it explains why the old bug was so total. The camera is
elevated behind the pitcher, and the catcher appears **above** the pitcher in
image space:

| | normalised image y |
|---|---|
| identified catcher, hip midpoint | **0.454** |
| tracked pitcher, hip midpoint | 0.573 |

"The lowest-hip pose that is not the pitcher" did not merely fail to find the
catcher — it had the sign wrong. The catcher is never the lowest pose in frame.

### Which detector classes are on the catcher

Measured on 40 frames from 4 clips, then the boxes were rendered and inspected.

| class | frames firing (conf ≥ 0.05) | verdict |
|---|---|---|
| `catcher_mask` | 77.5% | **on the UMPIRE.** Excluded. |
| `catcher_shin` | 77.5% | on the catcher, conf 0.85-0.93. Anchor. |
| `catcher_cleat` | 62.5% | on the catcher. Anchor. |
| `catcher_mitt` | 52.5% | on the catcher, rarely above conf 0.5. Anchor. |

`catcher_mask` is the trap. It had the joint-best hit rate in the family and it
lands on the umpire standing directly behind the catcher wearing the same piece of
equipment. Using it would have produced the best-looking coverage in the family
and the wrong body for the third time on this project. It is excluded in code with
that reason attached.

The model's own validation is worthless at this sample size — `catcher_mitt`
reports mAP50 0.995 on **5 instances in 5 images** — which is exactly why every
rate above was measured directly.

### Localising the region works

Pooling agreeing gear boxes across a clip locates a catcher region on **every clip
tried** (4/4 and 3/3), from 80-123 agreeing boxes per clip, with the pooled anchors
spread only ~38 px vertically. Region placement is a solved problem.

One design point worth keeping: the region is **one fixed rectangle per clip**, not
a per-frame crop. That is deliberate and it is a correctness argument, not an
optimisation. The glove-target cue measures *where* the catcher sets up, so a crop
that tracked him frame by frame would move the frame of reference along with the
signal and the cue would read zero by construction. A clip-level median cannot
encode within-pitch position. `test_catcher.py` pins this.

### Articulating him does not work

| pose model | catcher identified |
|---|---|
| `lite` | 4.41% of frames |
| `full` | 3.96% |
| `heavy` | 1.76% |

Dominant rejection is `no_pose_in_crop` at 50-67%: the crop is on the catcher and
the model returns nothing inside it. Rejections that are the *right* answer make up
most of the rest — `standing_not_squatting` is the hitter and the umpire being
correctly refused.

Two things follow, and the second matters more than the first.

1. Going bigger does not help. It gets worse. This is a capability limit on a
   ~50x45 px subject occluded by the umpire, not a threshold to loosen.
2. **The 3-4% is not a small sample, it is a biased one.** The frames where pose
   succeeds are the frames where the catcher is most visible and most extended,
   which is not independent of what he is doing. A cue computed on that subsample
   would inherit the selection, which is the same hazard that discredited the tap
   detector.

So catcher stance (squat depth, stance width, weight distribution, body angle) and
catcher mitt angle are **not implemented**, and that is a measurement result rather
than unfinished work. Reopening them needs a different localiser, not a retry.

### Subject verification for the frames that do identify

The check that would have caught the original bug on day one, run on the new path:

| quantity | identified catcher | the bug's value | tracked pitcher |
|---|---|---|---|
| hip midpoint y | 0.454 | 0.574 | 0.573 |
| torso length | 0.046 | — | 0.125 |
| stance width (own torsos) | 0.211 | 0.012 | — |
| knees below hips (implausible) | 0 of 13 | — | — |

The catcher is a third of the pitcher's apparent size and 0.12 higher in frame,
with a stance seventeen times wider than the bug produced. The substitution is not
recurring.

One caveat on a metric I initially misread: euclidean distance from the catcher to
the tracked pitcher is only ~0.86 *pitcher* torso lengths, and 7 of 10 compared
frames sit within one. That looks alarming and is not diagnostic — this framing
compresses depth, so the two bodies genuinely are about one pitcher-torso apart.
`hip_y` separation and the 3x size difference are the tests that discriminate.

## Step 2 — the cue family that survives

`cv/preflight/catcher_target.py`, names prefixed `cmitt_`. The retracted
`catcher_*` names stay retracted and are not reused; a test enforces it.

Everything is expressed in **home-plate box widths measured in the same frame**,
which is what makes it survive park-to-park zoom. Both boxes must come from the
same frame — pairing a mitt with a plate from elsewhere in the clip would put
camera motion back into a quantity whose entire purpose is to be free of it.

| cue | one sentence |
|---|---|
| `cmitt_target_lateral_plate_widths` | median lateral offset of the mitt from the plate centre over the actionable span |
| `cmitt_target_height_plate_widths` | median height of the mitt above the plate centre |
| `cmitt_target_lateral_drift_plate_widths` | interdecile spread of that lateral offset: how much the target moves once set |
| `cmitt_target_lateral_late_minus_early` | last third minus first third, signed, so a target walked one way is separable from one that wobbles |

### Noise floor, and the comparison that motivated the whole detour

| quantity | plate widths |
|---|---|
| mitt centre-x jitter, frame to frame | 0.05 |
| within-pitch spread of lateral offset (interdecile) | 0.12-0.34 |
| **standard error of the per-pitch median** | **~0.04** |
| **between-pitch signal (difference of per-pitch medians)** | **~0.23** |

About six to one. Set against the cue this replaces: the pitcher's glove angle was
retracted because its horizontal extent (0.066 torso) sat *below* its own jitter
floor (0.100), leaving 96% of its variance as the sign of the vertical component.
The structural reason for the difference is the one that motivated looking at the
catcher: the pitcher's glove points down the camera axis and the catcher's mitt
faces the camera. That expectation was correct and is now measured rather than
assumed.

`MIN_MITT_FRAMES = 5` is derived from this, not picked: SE at n=5 is 0.059 plate
widths, about a quarter of the between-pitch signal. Below it the per-pitch value
is dominated by which frames happened to detect. The measurement reports its own
SE and the visibility gate consumes it.

### Coverage: encouraging on one arm, and it did not replicate on a second

This is the part that stops the cue being ready, and it is worth reading before the
noise-floor table above is taken as good news.

The serious risk was that a mitt is easiest to detect once it is *moving to receive
the pitch* — after the swing decision, hence useless. On four Woo clips that risk
looked inverted, which was the opposite of the concern:

| Woo, 4 clips (Yankee Stadium) | rate |
|---|---|
| mitt detection inside the actionable span | 0.645 |
| mitt detection outside it | 0.230 |
| plate detection inside the span | 1.00 |
| pitches yielding an in-window measurement | 3 of 4 |

Repeated on three Zac Gallen clips, it fell apart:

| Gallen, 3 clips | rate |
|---|---|
| mitt detection inside the actionable span | 0.223 (median) |
| mitt detection outside it | 0.368 (median) |
| plate detection inside the span | **0.00** |
| pitches yielding an in-window measurement | **0 of 3** |

The in-window advantage reverses, and `both_rate_in_window` is zero, so the cue
produces **nothing at all** on this arm. Whole-clip rates locate the cause in the
detector rather than the window: at conf 0.25, plate fires on 22.5% of Gallen frames
against 45.4% of Woo frames, and mitt-and-plate-together on 8.5% against 16.1%.
Mitt centre-x scatter within a clip is also twice as large (0.042 against 0.021).

The straightforward reading is that a `plate` and `catcher_mitt` detector trained on
28 fully-labeled frames does not generalise across parks and camera framings, and
that four clips at one park was not a sample. The favourable numbers in the
noise-floor table are conditional on the detector firing, and on this evidence it
fires on some parks and not others.

Concretely: **the six-to-one noise-floor result stands as a measurement of
precision-when-available, and the coverage needed to use it does not yet exist
league-wide.** Those are separate claims and only the first replicated.

### A related corpus-wide measurement, since it caps this cue directly

`window_placement_audit.py`, over 300 cached tracks across 18 arms (206 with a valid
window) — no pixels needed:

| | |
|---|---|
| actionable span **opens at frame 0** | **51.9%** of valid pitches |
| has a pre-set segment at all | 68.9% |
| window closes within the first quarter of the clip | 35.0% |
| median window close, as a fraction of clip length | 0.38 |

Opening at frame 0 on half of pitches means `PRESET_LOOKBACK = 45` is being
truncated by the clip boundary that often — the pre-set segment was kept
specifically because catcher setup plausibly lives in it, and on half the sample it
is shorter than intended, on top of already being 0.75 s rather than the 1.5 s its
comment reasons for (see the 60 fps finding below).

I looked at whether the 35% closing in the first quarter means the window is landing
on broadcast lead-in, and **the evidence does not support that conclusion.** The Woo
clips also closed at 0.18-0.24 of clip length and had the plate visible on 100% of
in-window frames, so an early close is not per se lead-in. The Gallen plate failure
is a detector-generalisation problem, not a window problem. Flagging the frame-zero
rate as measured; not asserting the window is misplaced.

### Limits stated plainly

* Lateral offset is **camera frame** — toward-third versus toward-first. It is not
  inside/outside until combined with batter handedness, which lives in the pitch
  record, not the track. The cue is named for what it measures.
* `catcher_mitt` and `plate` come from `parts_gear.pt`, trained on 28 fully-labeled
  frames, and the Woo-to-Gallen coverage collapse above says it does not generalise
  across parks. **Labelling mitt and plate frames across many parks is the single
  highest-value investment available to this cue**, and until that is done the cue
  is unusable on an unknown fraction of arms.
* The cues are not wired into `spot_diff.CUES`. A name there can reach the board,
  and these have a noise floor and no validation.

## Step 3 — not run, and why

The recency protocol (discovery on 3 most recent starts, validation on the next 6,
game-disjoint splits, BH-FDR q=0.10, delivery stratification, precision floor 0.75,
convergence and permutation checks) has **not** been run. The blockers are
structural, and note that the eligibility one resolved itself during this work
without helping:

1. **Eligible arms now exist and have no pixels.** At the start of this work all 8
   arms in `league_progress_2026.json` were `state: "tracking"`; by the end 7 were
   `complete` (Webb, Canning, Kelly, E. Rodriguez, Pfaadt, Sugano, Feltner). Every
   one of them has **0 or 1 clips left on disk** against 193-2180 cached tracks,
   because `clip_cache.purge_tracked_clips` deletes an mp4 as soon as its track
   exists. So the arms that are eligible to analyse are exactly the arms whose
   pixels are gone, and the arms with pixels (Woo, 104 clips) are the ones still
   `tracking` and therefore ineligible. This is not a coincidence, it is the
   janitor's design.
2. **Existing tracks cannot be re-derived into these cues.** Catcher target needs
   per-frame detector boxes, which were never persisted. This is a re-tracking
   pass, not a re-derivation, and re-fetching is ~3.9 GB per arm against a disk the
   janitor is already warning about at 16 GB free.
3. **Coverage does not replicate across parks** (above), so even with pixels in hand
   the cue would produce results on an unknown and park-correlated subset. Fixing
   the detector has to come before any statistics, or the statistics will be about
   which parks the detector likes.

The practical consequence is the fix in item 2: persisting `cmitt_*` boxes in the
tracker during the pipeline's normal pass costs one detector call per frame and makes
all of this a cheap re-derivation later. Doing it as a separate pass costs roughly
5.5 hours of CPU per arm at the measured ~50 s per clip, competing with
`scale_nlwest`.

The honest cost estimate for validating this properly, per arm: re-fetch ~400
clips, run the detector over the actionable span of each. At the measured ~50 s per
clip for a full-frame detector pass, that is roughly 5.5 hours of CPU per arm,
competing with `scale_nlwest`. It should be run against arms the pipeline has
finished, on a persisted `cmitt_*` column added to the tracker, not as a separate
pass.

## Incidental finding, and it is not small: the corpus is 60 fps

Every temporal constant in `window.py` is documented and reasoned as "at 30fps".
Sampling 400 track summaries across the run directories: **395 are 60 fps and 5 are
59**. None are 30.

So each of these spans is **half** the duration its comment claims:

| constant | documented intent | actual at 60 fps |
|---|---|---|
| `PRESET_LOOKBACK = 45` | ~1.5 s | 0.75 s |
| `QUIET_RUN = 6` | ~0.2 s | 0.10 s |
| `LIFT_TRAIL_MARGIN = 5` | ~0.17 s | 0.083 s |
| `SET_LOOKBACK_MAX = 90` | ~3 s | 1.5 s |
| `LIFT_LOOKBACK = 90` | ~3 s | 1.5 s |
| `WINDUP_WINDOW_FRAMES = 45` | ~1.5 s | 0.75 s |
| `MAX_BREAK_TO_DELIVERY = 60` | ~2 s | 1 s |

The speed thresholds have the mirror-image problem: `QUIET_SPEED = 0.020` and
`DELIVERY_SPEED = 0.055` are per-*frame* displacements, so at 60 fps the same real
motion produces half the value, making both effectively twice as strict as
documented.

This is deliberately **not changed here.** Touching it would move every
window-derived result on the board, which is a decision about the published set and
not a catcher fix. But it bears directly on this work: the pre-set segment was kept
specifically because catcher setup plausibly lives in it, and it is currently 0.75 s
long rather than the 1.5 s its comment reasons for.

Two sub-questions worth separating when this is picked up. Whether the *empirical*
calibrations (the -20/-45/-65 glove-tracking reliability curve behind
`PRESET_LOOKBACK`) were measured in frames on this same 60 fps footage — in which
case the number is right and only the comment is wrong — or reasoned from the stated
seconds, in which case the number is wrong.

## Verdict: is the catcher a better centre-field signal source than the pitcher?

Split by what is being asked.

**On measurement geometry, yes, clearly.** The premise held up. The catcher faces
the camera, and where the detector fires his mitt target measures at roughly six
times its noise floor, where the pitcher's glove angle measured below its own. His
cues also fall earlier, inside the pre-set segment, which is the actionability
standard.

**On what is measurable today, no — he is much more expensive and much less
reliable.** The pitcher is large, centred and articulable. The catcher yields a
skeleton on 3-4% of frames, so two of the three requested families are unavailable;
the third depends on a detector that produced good coverage at one park and none at
another. A cue that works on some arms and silently returns nothing on others is not
yet a cue, it is a cue plus an unmeasured coverage bias — and coverage that
correlates with park correlates with opponent, which is the kind of confound that
manufactures a spurious effect.

**The fair test has still not been run.** It is blocked on pipeline state (no arm
marked `complete`) and now also on detector generalisation, not on method. Unlike the
pitcher's glove this is still not a null: it is a cue with favourable measured
precision, unreliable availability, and no evidence either way about pitch
information. Better than where the catcher family stood yesterday, and not a finding.

Cheapest honest path to an answer, in order:

1. **Label `catcher_mitt` and `plate` across many parks.** This is now clearly the
   binding constraint — it is what failed between Woo and Gallen — and it is the
   cheapest item here. Nothing else on this list is worth doing first.
2. Persist `cmitt_*` per-frame boxes in the tracker so this becomes a re-derivation
   instead of a re-tracking pass.
3. Re-measure in-window coverage across arms and parks before running any
   statistics, and treat per-arm coverage as a reportable quantity rather than an
   implementation detail.
4. Run the recency protocol on the first arms the pipeline marks `complete`.
5. Resolve the 60 fps question, and the 51.9% frame-zero window opening, before
   trusting any window-derived effect size — catcher or pitcher.

## Artifacts

Code, all new files; no shared or published module was modified.

| file | what it is |
|---|---|
| `cv/preflight/catcher_locate.py` | localisation: gear anchors, clip region, pose-on-crop with subject verification |
| `cv/preflight/catcher_target.py` | the `cmitt_*` glove-target cue family |
| `cv/preflight/test_catcher.py` | 14 checks, all passing |
| `cv/preflight/catcher_detect_probe.py` | per-class gear detection rates |
| `cv/preflight/catcher_box_peek.py` | renders gear boxes — how the umpire/mask confusion was found |
| `cv/preflight/catcher_pose_probe.py` | per-frame identification rate and placement stats |
| `cv/preflight/catcher_clip_probe.py` | clip-region identification rate, not-the-pitcher check |
| `cv/preflight/catcher_model_probe.py` | lite/full/heavy comparison |
| `cv/preflight/catcher_mitt_probe.py` | mitt and plate rates by confidence |
| `cv/preflight/catcher_target_probe.py` | in-window vs out-of-window coverage |
| `cv/preflight/window_placement_audit.py` | where the window lands, over cached tracks |

Reports under `runs/`: `catcher_detect_probe.json`, `catcher_pose_probe.json`,
`catcher_clip_probe.json`, `catcher_model_probe.json`, `catcher_mitt_probe.json`,
`catcher_mitt_probe_gallen.json`, `catcher_target_probe.json`,
`catcher_target_probe_gallen.json`, `window_placement_audit.json`.

Not touched: `track_pitcher.py`, `provenance.py`, `spot_diff.py`, `thresholds.py`,
`methodology.html`, and everything the `scale_nlwest` pipeline writes. No cue was
un-retracted and no threshold, gate, FDR level or effect floor was changed.
