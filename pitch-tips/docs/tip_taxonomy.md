# The scout tip taxonomy, and what we can measure of it

Source documents: `apex_tipping_examples.pdf` (five pages, eleven pitchers) and
`thorpe_pitch_tip_milb.pdf` (four pages, one pitcher, two viewing angles). The
text of both is thin; most of the content is in the image annotations, which are
transcribed here alongside the prose.

The point of this document is a count. Every cue in the shipped system measures
where the glove sits in the frame. The documents describe a much wider
vocabulary, and the honest reading of "zero validated tips" is partly that we
have not been measuring most of the things that tip.

---

## 1. The complete taxonomy, in the scouts' words

Twenty-four distinct tip types. Quotes are verbatim; ALL-CAPS entries are
on-image annotations.

### Glove presentation

| # | Tip type | Source language |
|---|---|---|
| 1 | Glove height at lift | "his glove height/angle at lift"; "a lot lower relative to FB/CH glove height"; "generally lower on the SL" |
| 2 | Glove angle at lift | "glove height/angle at lift"; "The glove angled up"; "TOP OF GLOVE UP" |
| 3 | Glove tuck depth | "The SL would be more tucked"; "GLOVE LOWER + TUCKED" |
| 4 | Glove distance off the body | "came off the body more on the CH"; "staying closer to body on SL" |
| 5 | Glove flare | "Glove more flared on CH"; "MORE FLAIR" |
| 6 | Glove drift before lift, and its synchrony with the leg | "his glove drifting before lift on FB/CH and staying closer to body on SL (synced with leg lift)" |
| 7 | Glove squeezes | "2 SQUEEZES + MORE FLAIR" |

### Set position and posture

| # | Tip type | Source language |
|---|---|---|
| 8 | Set position, generally | "various notes centered around his set position" |
| 9 | Glove position at set | "also had him with glove issues at set in 2023" |
| 10 | Posture / uprightness | "hitters felt like he was more upright on the SL"; "STRAIGHTER POSTURE"; "Similar posture issues flagged" |
| 11 | Lean forward / weight distribution | *not in the documents; named by the user as a target* |
| 12 | Sway coming set | *not in the documents; named by the user as a target* |

### Hand, wrist and grip

| # | Tip type | Source language |
|---|---|---|
| 13 | Hand height inside the glove | "HAND LOWER IN GLOVE"; "he is higher in glove on CH" |
| 14 | Hand drop | "Hand drops more on CH" |
| 15 | Wrist angle | "WRIST UP"; "WRIST ANGLED UP" |
| 16 | Grip burial depth | "CH grip less buried in glove" |
| 17 | Grip identifiable at lift | "Can see circle grip at lift in windup and stretch" |
| 18 | Late grip change | "LATE CHANGE TO - CH GRIP"; "IF YOU SEE = CH" |
| 19 | Index-finger curl | "Runner can see hand index finger curled"; "Hitter can see curled index finger on inside of the ball on CH" |
| 20 | Hand visibility to a runner | "more hand visible on CH from 2nd" |

### Arm

| # | Tip type | Source language |
|---|---|---|
| 21 | Forearm exposure | "MORE FOREARM VISIBLE TO COACH" |
| 22 | Arm window size | "BIGGER ARM WINDOW" |

### Other

| # | Tip type | Source language |
|---|---|---|
| 23 | Facial movement | "and his mouth" |
| 24 | Catcher setup | *not in the documents; named by the user as a target* |

---

## 1a. The sightline limit — the largest single gap, and not a resolution problem

**Nine of the eleven pitcher notes specify a viewing angle.** The scouts are not
only naming a cue, they are naming *who can see it*:

- Bubic: "we had issues with him from 2nd, **open and closed side** (NYY base
  coaches relaying off of him)"
- Erceg: "**from 2nd base** has also been an on-and-off concern"
- Speier: "various notes centered around his set position and **exposure from
  2nd**"
- Burke: "more hand visible on CH **from 2nd**"
- Thorpe: "Had Thorpe **from the plate and 2nd base** … **From 2nd**, he is
  higher in glove on CH — here is Jazz relaying off of this."
- Thorpe MiLB deck: an entire page titled "**Runner Perspective**" — "CH grip
  less buried in glove", "**Runner** can see hand index finger curled"

**Six of the 24 tip types are recorded specifically as second-base reads**:
13 (hand height in glove), 16 (grip burial), 19 (index-finger curl), 20 (hand
visibility), 21 (forearm exposure), and the "exposure from 2nd" reading of set
position (8/9).

This is a **sightline** limit, not a resolution limit, and that distinction
matters because nothing about model quality or sensor improvement touches it. A
runner on second stands roughly 90° off our axis and sees the back and open side
of the glove. Center field sees the pitcher's back straight down his forward
axis, which is the worst available angle for exactly these cues: the glove's
open side faces away, and the segments whose angles carry the cue project along
the camera axis to nearly nothing. Our own measurements show that directly —
gating the glove-forearm angle on a resolvable projected segment leaves 36% of
pitches with a value, and shoulder tilt at the set 56% (§4).

Two consequences worth stating plainly:

1. **"We found nothing" and "there is nothing there" are different claims.** For
   the second-base cues the honest one is the first. A meaningful share of real,
   professionally scouted, in-game-relayed tips are simply outside our footage.
2. **Where we can measure a CF analogue of a second-base cue, it is an analogue
   and not the same observation.** Types 13, 16 and 21 may be partly recoverable
   from CF with the detector, but the documented tip in each case is the
   second-base view, and a CF version should not be reported as having
   reproduced it.

This is the strongest argument for the club X1–X4 angles the methodology page is
already schema-ready for. The operational definition of a tip used throughout
this project is that a runner or base coach can see and relay the pitch before
the swing decision — and a runner on second is literally that vantage. One
second-base angle would open six tip types that no amount of work on center
field can reach.

---

## 2. Four-way mapping

**Count: of 24 tip types, 8 were measured before this work (7 fully, 1 by proxy
only). Four more become measurable here, taking the total to 12. Of the
remaining 12, ten need the parts detector, two are beyond CF resolution at any
model quality, and one is blocked on catcher localisation.**

Type 10 (posture) appears in both (a) and (b): it was already measured at the
lift and is now also measured at the set and as a set-to-lift change. It is
counted once, in (a).

### (a) Already measured — 8 types

| Tip type | Existing feature |
|---|---|
| 1 Glove height at lift | `glove_height_at_lift`, `glove_rise_set_to_lift` |
| 2 Glove angle at lift | `glove_angle_at_lift` — see the defect note below |
| 4 Glove off the body | `glove_off_body_at_lift`, `glove_off_body_at_set` |
| 5 Glove flare | `glove_flare_at_lift` |
| 6 Glove drift and leg synchrony | `glove_drift_pre_lift`, `glove_drift_dx/dy`, `drift_lift_sync` |
| 9 Glove position at set | `glove_height_at_set`, `glove_off_body_at_set` |
| 10 Posture / uprightness | `posture_lean_at_lift`, `posture_upright_at_lift` |
| 16 Grip burial (proxy only) | `hand_gap_at_lift`, `hand_vis_at_lift` — explicitly proxies |

**Two defects in shipped features — now fixed.** `glove_angle_at_lift` took a
raw `atan2` of the forearm vector, unfolded for handedness and ungated on
segment length; `posture_lean_at_lift` returned a number near ±180 on an
inverted pose instead of NaN. Both were assessed before being touched, because
both sit downstream of the window verified at 94.3%. See §5 for the
before/after measurements and the placement re-verification.

### (b) Computable now from banked pose tracks — 4 new types, implemented

No re-tracking. All derived from the 54-column rich `lift_tracks` (18 landmarks
× x/y/visibility) already on disk. Note the brief said 72 columns; the actual
rich schema is 54, and `cheek_x`/`cheek_y` live in a separate 16-column legacy
`tracks` schema, not in the rich tracks.

| Tip type | New primitives |
|---|---|
| 8 Set position | `stance_width_at_set`, `knee_flex_at_set` |
| 10 Posture at the set, and its change into the lift (extends (a)) | `posture_lean_at_set`, `lean_change_set_to_lift` |
| 11 Lean forward | `torso_foreshorten_at_set`, `foreshorten_change_set_to_lift` |
| 12 Sway coming set | `sway_amplitude`, `sway_dx`, `sway_dy`, `sway_directness`, `come_set_peak_speed` |
| 21 Forearm exposure | `forearm_exposure_at_set`, `forearm_exposure_at_lift` |

Two further attempts failed validation and are marked
`resolution_limited` — see §4.

### (c) Needs the parts detector — 10 types

Everything here is about what is happening *inside or around the glove*, which
pose landmarks fundamentally cannot report: MediaPipe emits a wrist, an index
knuckle and a pinky knuckle, and none of those say how deep the hand is in the
glove or which way a finger is curled.

3 (tuck depth), 7 (squeezes), 13 (hand height in glove), 14 (hand drop),
15 (wrist angle), 16 (grip burial, beyond the current proxies),
17 (grip identifiable), 18 (late grip change), 20 (hand visibility),
22 (arm window).

Feasibility, measured on 91 Thorpe clips with valid windows at 1280×720:
the hand bounding box is **15–17 px** on a side (median; 5th percentile ≈ 5 px,
95th ≈ 32 px), against a shoulder width of 48 px. A 16-px object is a hard but
real detection target for `parts_glovehand.pt`, which is the case for investing
in the detector. Individual finger geometry is not: the index-knuckle to
pinky-knuckle span is **4.7–5.1 px** (median), so tip type 19 sits with the
resolution-limited group rather than this one.

### (d) Beyond current resolution — 2 types

**19 Index-finger curl.** The span that would have to resolve a curl is 4.7–5.1
px median. Pose visibility on those landmarks is already only 0.50–0.51, and
single-anchor landmark noise there is 0.080–0.082 torso lengths, the worst of
any landmark group. No detector recovers a finger pose from 5 px.

**23 Facial movement.** This is the one worth the detail, because the codebase
makes it look shipped and it is not. See §4.

**15 Wrist angle and 22 arm window** are counted in (c) rather than here because
the detector is a precondition for either, but neither is likely to survive CF
geometry even with it — both are angles on short segments pointing down the
camera axis, and `glove_angle_at_set` in §4 is the direct measurement of how
badly that goes. `WRIST UP` in particular is a side-on read.

### Blocked on catcher tracking — 1 type

**24 Catcher setup.** Not implemented, as instructed. The catcher pose was the
pitcher in 71–91% of frames (`docs/catcher_subject_bug.md`), so the existing
`catcher_glove_x/y`, `catcher_stance_width`, `catcher_hip_y` and
`catcher_glove_speed` columns are measuring the wrong body. This is deferred
pending detector-based localisation, not merely a tracking-quality problem.
Nothing in the new primitives touches the catcher.

---

## 3. Resolution limits, with numbers

For the methodology page's limits section. All measured on cached Thorpe tracks
and clips, 1280×720 Savant CF.

**Landmark noise floor** (`cv/preflight/landmark_noise_probe.py`, 254 pitches).
Measured over the set interval, where the pitcher is still by construction, so
observed displacement is measurement error. In torso lengths:

| Landmark group | Per-frame jitter | Single-anchor SD | Visibility |
|---|---|---|---|
| Hips | 0.098–0.106 | 0.054–0.057 | 0.999 |
| Shoulders | 0.101–0.102 | 0.048–0.054 | 0.998 |
| Nose | 0.096 | 0.044 | 0.990 |
| Knees | 0.138 | 0.068 | 0.69–0.74 |
| Ankles | 0.120–0.133 | 0.064–0.066 | 0.70–0.73 |
| Elbows | 0.127–0.146 | 0.056–0.068 | 0.60–0.63 |
| Wrists | 0.151–0.156 | 0.069–0.071 | 0.54 |
| Index knuckles | 0.167–0.184 | 0.080–0.082 | 0.50–0.51 |

Two consequences. First, the 0.05-torso practical-visibility floor sits *at* the
single-anchor noise level for the best landmarks and *below* it for the hands —
a single-pitch reading can never resolve a visible tip, and only the group mean
can, which is why sample size dominates everything. Second, per-frame jitter of
0.10–0.18 torso lengths means no feature may integrate a path frame by frame; a
45-frame segment accumulates several torso lengths of pure noise. This is the
same failure that made the original glove path-length feature report physically
impossible values, and it is why the new trajectory features use smoothed
excursion instead.

**Hand and finger extent** (`cv/preflight/hand_pixel_audit.py`, 91 clips):
hand bbox 15–17 px, index-to-pinky 4.7–5.1 px, shoulder width 48 px.

**Face extent and detectability** (`cv/preflight/face_pixel_audit.py`).
This is the rigorous version of "facial movements", held to the standard set by
the retired PitchCom cue:

- Pitcher head scale (nose to shoulder midpoint), model-free from cached pose:
  **31.4 px** median (5th percentile 18.8, 95th 77.7). Implied mouth width at
  0.35 of head scale: **≈ 11 px**.
- MediaPipe Face Landmarker, run on 288 in-window frames across 60 clips with
  the same model and options `track_pitcher.py` uses: a face was returned in
  **24 frames (8.3%)**.
- Of those 24, the face sits a median of **2.24 shoulder widths** from the
  pitcher's pose nose, and only **3 of 288 frames (1.04%)** put a face within
  one shoulder width of him. The detected faces have inter-eye distance 101.8 px
  — larger than the pitcher's entire head at 31.4 px. **They are the hitter,
  the on-deck batter and spectators, not the pitcher.**

So the pitcher's mouth is about 11 px wide, and the face model finds his face in
roughly 1% of frames. Facial movement is not measurable from Savant CF video.

**Both cheek cues are now retracted.** `cheek_motion_mean` and
`cheek_motion_std` are in `provenance.RETRACTED_CUES`, checked before the
statistical gates. Audit result: **0 published tips** ever rested on them, but
**20 `situationCoverage` assertions across 5 arms** did — and two were live on
Drew Thorpe's card as `discernable: true` with accuracies of 0.76 and 0.778.
`scrub_coverage` demotions went from 38 (PitchCom only) to 58. In the
regenerated `data/demo.json` all 18 cheek entries are demoted, 0 remain
`discernable: true` (was 2), and 0 retain an accuracy claim (was 18). The
pre-retraction file is preserved as `data/demo.pre_cheek_retraction.json`.

**This also means an existing feature was mislabelled.** `track_pitcher.py`
falls back to the pose nose whenever the face model returns nothing:

```python
if cheek is None:
    cheek = _xy(plm, NOSE)
```

At a 1% pitcher-face rate, `cheek_motion` is essentially always the pose nose.
`cheek_motion_mean` and `cheek_motion_std` were therefore described in
`spot_diff.CUES` as "cheek/jaw motion before separation" and "variability of
facial motion" while actually measuring **head-position jitter**.

**The fallback itself is now removed**, not just the label. `cheek_*` emits NaN
when no pitcher face is found, a detected face must sit within
`MAX_FACE_TO_NOSE_SHOULDER_WIDTHS = 1.0` of the pose nose to be accepted at all,
motion is only differenced across consecutive pitcher-face frames, and a new
`cheek_source` column records which case applied — so a blank cannot be misread
as stillness. Same principle as the catcher NaN guard: make the invalid state
unrepresentable rather than relying on someone remembering. Regression tests are
in `cv/preflight/test_retractions.py`.

### The pattern, stated plainly

This is the **fourth** feature today that passed its gates while measuring
something other than its name:

| Feature | Label | What it actually measured |
|---|---|---|
| Holdout accuracy | out-of-sample skill | a degenerate split |
| `catcher_*` scalars | catcher setup | the pitcher's body, in 71–91% of frames |
| `pitchcom_tap_count` | discrete PitchCom taps | glove-centroid motion variance |
| `cheek_motion_*` | facial motion | head-position jitter via a pose-nose fallback |

The common mechanism is a **fully populated column with a confident label and
the wrong contents** — and in three of the four cases a silent fallback or a
mis-selected subject is what filled it. Statistical gates cannot catch this
class of error, because the number is well-behaved; only asking "what does this
actually measure" catches it.

**The implication is that the remaining cues should all be audited on that
question, not just the ones that happened to surface tonight.** Every cue in
`spot_diff.CUES` deserves the treatment applied here: name the physical
quantity, verify the feature responds to it and not to a proxy, and confirm it
clears the noise floor for the body part involved. Two of the shipped glove cues
were checked in the course of this work (§5) and both were defective, which is
not an encouraging base rate.

---

## 4. The implemented primitives

One sentence each, with validation evidence. Retention status is recorded
mechanically in `primitives.PRIMITIVE_STATUS` against a rule fixed before any
result was inspected: recoverable signal above the 0.05-torso floor (or above
induced noise, for angles), and defined on at least 60% of usable pitches.

Reliability is measured by recomputing all 381 cached Thorpe tracks with
additive landmark noise at the measured 0.10 torso/frame jitter.
`signal = sqrt(between² − induced²)` is the spread a group contrast can actually
see.

### Validated — 8 primitives

| Primitive | What it computes | Signal | Coverage |
|---|---|---|---|
| `stance_width_at_set` | Ankle-to-ankle separation at the set, in torso lengths. | 0.184 | 0.86 |
| `knee_flex_at_set` | How deep he sits into the set, as knee height relative to the hips. | 0.259 | 0.96 |
| `posture_lean_at_set` | Degrees the trunk leans off image vertical at the set (lateral component). | 15.4° vs 3.7° noise | 0.90 |
| `torso_foreshorten_at_set` | Apparent trunk length at the set over the pitch's own median — a proxy for leaning out of the frontal plane. | 0.083 | 0.98 |
| `forearm_exposure_at_set` | Apparent elbow-to-wrist length at the set, which shortens as the forearm turns toward the camera. | 0.180 | 0.98 |
| `forearm_exposure_at_lift` | The same at peak lift. | 0.184 | 1.00 |
| `lean_change_set_to_lift` | Degrees the trunk lean changes between the set and peak lift. | 10.0° vs 8.4° noise | 0.85 |
| `foreshorten_change_set_to_lift` | Change in apparent trunk length between the set and peak lift. | 0.179 | 0.98 |

`torso_foreshorten_at_set` is the weakest of these — signal 0.083 against
induced noise 0.105 — and should be the first dropped if FDR burden bites.

### Under-covered — the sway family, 5 primitives

Implemented, validated for correctness, **not fit for discovery yet**. Signal is
real (0.116–0.245 torso, all above the floor) but only 32% of stretch pitches
carry a measurable approach.

| Primitive | What it computes |
|---|---|
| `sway_amplitude` | Furthest the smoothed pelvis path ever gets from where it ends up at the set, in torso lengths. |
| `sway_dx` | Net sideways pelvis displacement across the approach. |
| `sway_dy` | Net vertical pelvis displacement across the approach. |
| `sway_directness` | Net displacement over amplitude, 0 to 1: near 1 for one smooth settle into the set, near 0 for a rock out and back. |
| `come_set_peak_speed` | Fastest the smoothed pelvis path moves during the approach. |

Why coverage is 32%, from 381 tracks: 93 have no valid window at all, 46 are
windups with no set, **92 have fewer than 8 frames of footage before the set
because the Savant clip starts too late**, 40 show apparent trunk length varying
by more than 25% across the approach (the tracker changing subject, or the
broadcast changing zoom, in the lead-in), and 19 imply the pelvis travelling
more than a torso length, which means he walked or the tracker swapped bodies.
78 survive. **The fix is longer clips, not a different feature** — a re-fetch
with more pre-set lead-in would roughly triple the sample.

### Resolution-limited — 2 primitives

`shoulder_tilt_at_set` (coverage 0.56, induced noise 13.2° on a cue whose real
range is perhaps ±15°) and `glove_angle_at_set` (coverage 0.44, induced noise
27.5°). Both are angles on a segment that points down the CF camera axis, so it
projects to almost nothing and the arctangent is dominated by two noise terms.
`MIN_ANGLE_SEGMENT = 0.28` torso lengths — derived as 0.05/tan(10°) from the
measured anchor noise — converts the unresolvable cases to NaN, which is why
coverage is well under 1.0. Without the gate both were 100% populated and 100%
noise. Folding for handedness also costs the open-versus-closed side, which was
the scouting content of the shoulder cue in the first place.

### Design notes

- **Window untouched.** Set-anchored primitives use the existing set anchor;
  trajectory primitives use `window.preset_segment` with `PRESET_LOOKBACK = 45`;
  the closing boundary stays at peak lift + 5. No boundary constant changed.
- **Trajectories are excursions, not path lengths**, for the noise reason in §3.
- **`delivery_type` now travels with the primitives**, read off the window
  rather than inferred from base state, because `spot_diff._groups` refuses a
  mixed-delivery frame and the set-position cues only exist for a delivery that
  has a set.
- **Dropouts are NaN, never zero and never motion.** `MIN_TRAJ_COVERAGE = 0.5`
  and the subject-continuity guard exist because a landmark that vanishes and
  reappears elsewhere otherwise reads as a large sway.
- **Nothing is wired into `spot_diff.CUES`.** A test asserts this. Discovery
  with these features is a separate decision under the corrected pipeline.

---

## 5. The two shipped angle defects: assessment and outcome

Both were treated as testable changes rather than patches, because both feed the
window verified at 94.3%.

**Can they move the window? No, structurally and measurably.** `window.py`
imports nothing from `primitives.py` — the window is computed upstream and the
primitives only consume it — so neither feature can influence placement. That
was verified rather than asserted: `cv/preflight/angle_fix_probe.py` recomputes
both code paths pitch-by-pitch over 416 pitches on three arms and reports
identical placement. After applying the fixes, placement re-verified on 401
usable pitches:

| Placement statistic | Before | After |
|---|---|---|
| Peak lift inside the window | 100% | 100% |
| Window ends at or before delivery onset | 100% | 100% |
| Median window length | 19–20 frames | 20 frames |
| Median lift → window end | 5 frames | 5 frames |
| Boundary method | `peak_leg_lift` | `peak_leg_lift` |

**`posture_lean_at_lift` — fixed, unambiguous win.** Now NaN on an inverted
trunk. 42 of 416 pitches (10.1%) had the shoulders tracked below the hips and
were being published as leans, which is why the 5th percentile was −171.5°.

| | Before | After |
|---|---|---|
| Standard deviation | 55.0° | 16.1° |
| 5th percentile | −171.5° | −26.8° |
| Induced landmark noise | 31.0° | 4.3° |
| Signal-to-noise ratio | 1.77 | 3.78 |
| Values beyond ±90° | 10.1% | 0% |
| Coverage | 100% | 90% |

**`glove_angle_at_lift` — fixed, and it matters.** Folded for handedness and
gated on `MIN_ANGLE_SEGMENT`. This is the one worth the attention because glove
angle is named directly in the documents (`WRIST ANGLED UP`, `TOP OF GLOVE UP`),
so a defective version could have been masking a real cue.

| | Before | After |
|---|---|---|
| Standard deviation | 81.4° | 71.4° |
| Induced landmark noise | 42.7° | 7.2° |
| Signal-to-noise ratio | 1.91 | 9.95 |
| Values beyond ±90° | 44.2% | 0% |
| Sign split (handedness artifact) | 134 pos / 282 neg | folded |
| Coverage | 100% | 36% |

The old version was **noise 42.7° against a `spot_diff` visibility threshold of
8.0°** — noise over five times the effect size it was being asked to resolve,
which is the PitchCom situation. The fix improves precision nearly sixfold. The
64% coverage loss is not a cost: those pitches had a forearm pointing down the
camera axis, so their angle was never measurable and was previously being
reported confidently anyway.

**One caveat recorded rather than resolved.** The surviving distribution is
bimodal near ±80° (5th percentile −89.4°, median −78.5°, 95th +82.9°). That is
consistent with the *vertical* component dominating while the horizontal
component remains unresolved, i.e. the length gate admits segments whose
elevation is still ill-conditioned. The feature is materially better than it
was, but it should not be treated as a clean cue without a gate on the
horizontal component specifically. `glove_angle_at_set`, its set-anchored twin,
is already marked `resolution_limited` for the same reason.

**Resolved: the angle is retracted, its vertical component is kept.** The caveat
above turned out to understate the problem. `cv/preflight/glove_angle_resolve.py`
over 326 pitches settled it:

| Question | Measurement |
|---|---|
| Is the horizontal extent resolved? | median \|dx\| **0.066 torso** against a **0.100** jitter floor; below the noise on **67.8%** of pitches, below 2× on **96.6%** |
| Is the magnitude informative? | median \|angle\| **80.4°**, only **3.4%** of pitches within ±45° of horizontal |
| How much is just the sign? | **96%** of the variance is explained by the sign of the vertical component alone |

So the cue was one bit of information — is the glove above the elbow or not —
wearing a degrees label and an 8° visibility threshold it could never be
compared against. The arctangent was not measuring a tilt; it was saturating,
because from center field the forearm points at the camera and the horizontal leg
of the arctangent is never actually observed. No estimator fixes that. It is the
sightline limit of §1a, arriving in a cue the documents specifically ask for.

The recoverable part is real and is kept, renamed to say exactly what it is:

| | `glove_angle_at_lift` (retracted) | `glove_rise_above_elbow_at_lift` (kept) |
|---|---|---|
| Quantity | arctangent of the forearm | vertical component only, in torso lengths |
| Threshold | 8.0° (uncomparable) | 0.05 torso, the standard distance floor |
| Induced noise | 18.2° | 0.132 torso |
| Recovered signal | — | 0.263 torso |
| Noise / signal | — | **0.50** (PitchCom retired at 1.9) |
| Coverage | 36% | **100%** |

The estimator is the windowed median the other lift-anchored cues already use,
not a new one; at the single lift frame the same quantity is far noisier
(0.132 → the median over ±3 frames is what makes it usable).

**What is lost.** The direction of the tilt. `WRIST ANGLED UP` and a wrist cocked
inward are indistinguishable in the magnitude alone, so this cue can say the
glove is presented higher relative to the elbow and cannot say which way it is
turned. Recovering that needs the second-base look, not a better model.

---

## 5a. The systematic cue audit

Two shipped glove cues checked in passing were both defective, so every cue the
pipeline can publish went through the same three questions. Full inventory in
`cv/preflight/cue_audit.py`; the outcome:

**A method correction first, because it changes the headline.** Comparing a
per-pitch noise standard deviation directly against a visibility threshold is not
a valid test. The threshold applies to a *difference of group means*, whose
standard error falls as 1/√n. Applied literally, that comparison disqualifies 14
of the 15 original lift-anchored cues; applied correctly it disqualifies none of
them on noise alone. The two tests actually used are (a) noise/signal against the
1.9 bar that retired PitchCom, and (b) the group-mean standard error against the
cue's own threshold. Both are reported per cue in `PRIMITIVE_STATUS`.

**Noise did not turn out to be the problem. Subject selection and silent
fallbacks were.** Not one of the 44 measured features breaches the 1.9 noise/signal
bar. The two worst are `glove_vs_belt_std` at 1.29 and `sway_directness` at 1.13 —
majority jitter, but below the retraction precedent. Meanwhile the catcher family
has the *lowest* noise/signal in the whole set, 0.02–0.04, precisely because it
was tracking the pitcher: a large, well-lit, reliably-detected subject. **Low noise
on the wrong subject.** A noise test cannot catch a subject bug, which is why the
fallback grep is a separate and equally necessary pass.

**Retracted by this audit (6 cues, 106 published assertions withdrawn).**

The `catcher_*` family. `docs/catcher_subject_bug.md` fixed the tracker and
skipped future catcher runs, but never withdrew the results already on the board —
a live tip on Pfaadt plus 34 `discernable: true` coverage entries, all computed
from pre-guard tracks. Fixing the producer is not withdrawing the claim. Evidence
the published columns are the pitcher:

| Column | Published median | Expected for a squatting catcher |
|---|---|---|
| `catcher_stance_width` | 0.0123 torso | far wider; 0.012 is the documented pitcher-body signature |
| `catcher_hip_y` | 0.5288 | the pitcher's own belt sits at 0.5499 — same region of frame |
| populated rate | **98.6%** (19,371 / 19,653 frames) | impossible: pose fails on the catcher in 65–77% of CF frames |

That 98.6% is itself the proof. It is the fallback's hit rate, not a detection
rate.

**Fixed: `window_features` fabricated zeros.** The function ended with

```python
return {k: (0.0 if np.isnan(v) else v) for k, v in out.items()}
```

Zero is not a neutral placeholder in these columns — it asserts the glove sat
exactly at belt height, or the catcher stood at the frame origin. Measured over
511 windows, the fabricated-zero path was taken by 3.3% of `glove_vs_belt`, 1.2%
of `wrist_speed`, and 100% of the catcher features on the 251 tracks written
before those columns existed. All of them now emit NaN, and the `or 0` idiom that
made a legitimate zero-variance window indistinguishable from a NaN is gone.

**Underpowered, not defective (2 cues).** `glove_drift_pre_lift` and
`glove_drift_dy` carry real signal, but their group-mean error at n=50 (0.068 and
0.055 torso) does not clear the 0.05 threshold. They need roughly n=92 and n=60
per pitch type. Pulled from discovery until the sample supports them; the cue is
not wrong, the sample is small.

**Superseded, not retracted (4 cues).** A new distinction, and worth keeping:
`glove_vs_belt_mean` and `glove_flare_mean` are un-normalised duplicates of
`glove_height_at_lift` and `glove_flare_at_lift`, in zoom-dependent image units;
`glove_vs_belt_std` and `glove_flare_std` have no documentary basis (no scouting
note describes glove *steadiness*) and are the weakest measurements in the
system. They measured their names correctly, so retracting them would overclaim —
but a board asserting they are discernable while discovery no longer tests them
makes a claim no future run could reproduce. `scrub_coverage` now demotes them
with `status: cue_superseded`.

**A test-scope bug found in my own work.** `test_status_table_covers_every_new_primitive`
asserted coverage over `PRIMITIVES[15:]` — a positional cutoff that exempted the
original fifteen from the bar their successors had to clear, and those fifteen are
where every one of the known measurement failures was found. Position in a list is
not a validation record. Now every primitive must carry a status, and a second
test refuses to let anything but a `validated` cue reach discovery.

---

## 6. The honest summary

Of 24 tip types the scouts describe, we measured 8 before this work and can now
measure 12. The remaining 12 split into 10 that need `parts_glovehand.pt` /
`parts_gear.pt`, 2 that center-field broadcast video cannot resolve at any model
quality, and 1 blocked on catcher localisation.

**Count of trustworthy cues, before and after the audit.** "Trustworthy" means it
measures its name, its noise clears its own visibility threshold as a group-mean
error, and a scouting document describes it.

| | Cues |
|---|---|
| In `spot_diff.CUES` this morning | 26 |
| — retracted: `pitchcom_*` (3), `cheek_motion_*` (2) | −5 |
| — retracted: `catcher_*` family, published on the board | −6 (were never in CUES) |
| — retracted: `glove_angle_at_lift`, `glove_angle_at_set` | −2 |
| — underpowered: `glove_drift_pre_lift`, `glove_drift_dy` | −2 |
| — superseded: 4 legacy image-unit window features | −4 |
| + new, validated and documented: 6 set-position / posture / forearm cues | +6 |
| + new: `glove_rise_above_elbow_at_lift`, replacing the angle | +1 |
| **In `spot_diff.CUES` tonight** | **20** |

The headline number barely moved, 26 → 20, but the composition changed
completely: 8 of the 26 were retracted outright, and 18 of the 20 now carry a
torso-normalised unit with a real visibility threshold their measured noise
clears. Only 2 remain in zoom-dependent image units (`wrist_speed_mean/p90`, kept
because tip 7 documents glove squeezes and nothing normalised measures fidget).

On the board itself: **0 published tips, 0 catcher tips, and 8 `discernable: true`
coverage entries, down from 26** — 106 catcher assertions and 20 superseded ones
withdrawn.

The distribution is the finding. The four newly covered types are real and sit
early in the actionable window, which is where the operational value is. But
the largest single bucket is the detector bucket, and it is not close — ten of
twenty-four. Tuck depth, hand height in glove, grip burial, grip identification,
late grip change, squeezes and hand visibility are among the most frequently
cited cues in the documents, they are all about what is happening inside the
glove, and no amount of additional pose-landmark feature engineering will reach
any of them. Six of the twenty-four are recorded specifically as second-base
reads, which no center-field camera delivers regardless of resolution.

### The ceiling: how many of the 24 are reachable from center field?

Counting what CF could support **with the detector built** and the catcher
localisation fixed — the optimistic case, not the current state:

| Bucket | Count | Types |
|---|---|---|
| Measured today | 12 | 1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 16 (proxy), 21 |
| Reachable with the detector | 5 | 3, 13, 14, 16 (properly), 22 |
| Reachable once catcher tracking is fixed | 1 | 24 |
| **CF ceiling** | **18 of 24** | |
| Not reachable from CF at any model quality | 6 | 7, 15, 17, 18, 19, 20, 23 |

The six unreachable ones, each with its measured reason: 7 squeezes and 15 wrist
angle are *articulation* and *camera-axis angle* respectively, which is the
boundary the methodology page already draws; 17 grip identification, 18 late
grip change and 19 index-finger curl all need finger geometry at a 4.7–5.1 px
span; 20 hand visibility and 23 facial movement are a second-base read and an
11 px mouth. (That list is seven entries for six types because 20 is both
sightline- and detector-limited and is counted once.)

So the realistic CF ceiling is **18 of 24, or 75%** — and three of those 18
(types 13, 16, 21) are CF analogues of cues the scouts actually read from second
base, so they should be reported as analogues rather than as reproductions.

### Recommendation

**Invest in the detector, in longer clips, and in one second-base angle — not in
more pose features.** The pose-landmark seam has now been worked close to its
limit: the primitives added here are the set-position and coming-set cues, and
after them what remains in the taxonomy is mostly not visible to a skeleton. In
rough order of return per unit effort:

1. **Longer clips.** Cheapest by far, already in motion. Moves the sway family
   from 32% coverage to usable on its own.
2. **The parts detector.** Opens five tip types, all of them frequently cited,
   none of them reachable any other way. The 15–17 px hand is a hard but real
   target.
3. **One second-base angle.** Opens six tip types that center field cannot
   reach at any resolution, and it is the vantage the scouting notes are
   actually written from.

And, independent of new data: **audit the remaining cues in `spot_diff.CUES`
against what they measure.** Four features failed that question today, and the
two shipped glove cues examined in passing were both defective. *(Done — §5a.)*

---

## 7. What the expanded cue set actually found

The audited cues were wired into discovery — 20 of them, down from 26 — and run
against the arms that have rich tracks. This is the part a buyer should read
first, because it is the test of whether any of the above matters.

| | Drew Thorpe | Eduardo Rodríguez |
|---|---|---|
| Pitches | 289 (5 games) | 520 (6 games) |
| Stretch stratum | 219 — **testable** | 3 |
| Windup stratum | 67 — underpowered (only FF) | 0 |
| Unlabelled delivery | 3, held out | **517, held out** |
| Cues available | 20 | 20 |
| Comparisons performed | **200** | 0 |
| Surviving holdout + BH-FDR(q=0.10) | **0** | 0 |

Rodríguez is not a result. 517 of his 520 pitches carry no delivery label, so
every contrast was refused before it was tested — he needs re-tracking, and no
conclusion of any kind should be drawn from his row. Kelly and Woo were
deliberately not tested: their re-tracks had not landed, and testing them on
stale 16-column data would produce a number with nothing behind it.

**Thorpe: 200 comparisons, zero survivors.** All 200 were lost at the FDR gate.
With 200 comparisons, BH at q=0.10 requires the smallest p ≤ 0.0005, and the
smallest observed was 0.010.

The pre-correction picture, which is diagnostic only and not a result:

| Rank | Cue (CH vs …) | g discovery | p uncorrected | g **holdout** | Sign holds? |
|---|---|---|---|---|---|
| 1 | `glove_rise_above_elbow_at_lift` (FF) | +0.558 | 0.0100 | **+0.560** | yes |
| 2 | `wrist_speed_mean` (FF) | +0.475 | 0.0209 | −0.393 | **no** |
| 3 | `glove_flare_at_lift` (FF) | −0.468 | 0.0255 | +0.345 | **no** |
| 4 | `glove_off_body_at_lift` (FC) | +0.433 | 0.0292 | −0.283 | **no** |
| 5 | `knee_flex_at_set` (SL) | +0.485 | 0.0302 | +0.297 | yes |
| 6 | `glove_off_body_at_set` (FF) | +0.439 | 0.0324 | −0.044 | **no** |
| 7 | `glove_off_body_at_set` (FC) | +0.435 | 0.0344 | −0.426 | **no** |

**Five of seven flip sign on held-out games.** That is the shape of noise, and it
is the clearest single argument for why the game-level holdout is the primary
defence rather than the p-value. 7 of 60 CH contrasts were nominally p<0.05
against 3.0 expected by chance — a mild excess that the holdout dissolves.

One candidate is worth naming without publishing it:
`glove_rise_above_elbow_at_lift` on CH vs FF held an effect size of +0.558 in
discovery and +0.560 across the game boundary — the same effect, twice, on
different games — but holdout p = 0.114 on a thin holdout, and it does not
survive FDR. It is the single interesting thing the expanded vocabulary produced,
it is **not a tip**, and more games would settle it either way. It is also,
notably, the cue that replaced the retracted glove angle.

### The Thorpe check against external ground truth

Thorpe is the one arm with a documented tip the pipeline did not generate:
`HAND LOWER IN GLOVE`, "he is higher in glove on CH", "CH grip less buried".

**The expanded cue set does not point at it.** The two cues related to the
documented tip both fail, and the direction is wrong on the larger comparisons:

| Cue | CH vs FF | CH vs SL | CH vs FC |
|---|---|---|---|
| `hand_gap_at_lift` | −0.036 (**opposite**) | −0.066 (**opposite**) | +0.013, p=0.81 |
| `hand_vis_at_lift` | −0.040 (**opposite**) | +0.015, p=0.66 | +0.008, p=0.83 |

Nothing approaches significance, and `hand_gap_at_lift` — the closer of the two
proxies — moves *against* the documented direction on both larger contrasts.

This is the expected outcome, and saying so is not a rescue. The cue that would
directly capture the documented tip is the hand's height *inside the glove*, which
requires hand and glove resolved as separate objects: tip type 13, sitting in the
detector bucket. `hand_gap_at_lift` is wrist-to-wrist separation and
`hand_vis_at_lift` is a landmark-confidence proxy; a move in either would have
been *consistent with* the scouts' note, never a reproduction of it. Neither
moved. The honest reading is that this tip is behind the detector, exactly where
§2 placed it, and the expanded pose vocabulary did not reach it.

### The 20 cues were not reaching the pipeline's arms at all

Everything in §7 above was measured on the one arm that happened to have a stale
`lift_tracks/` directory. On every arm the current pipeline produced, **only 2 of
the 20 cues were available**, and nothing errored. Two independent bugs, both of
the same shape as the rest of this document — a plausible-looking result standing
on a silent fallback:

1. **The track directory moved.** `primitives.py` looked for `lift_tracks/`, a
   hard-coded path. The tracker now writes one unified `tracks/` table carrying
   the 16 window scalars *and* the 18 landmarks (72–73 columns), and no longer
   writes `lift_tracks/` at all. So `build_run` refused to run, no
   `primitives.csv` was produced, and `spot_diff.load_pitcher` fell back to
   window features alone. After the audit removed six of the eight legacy window
   cues, that left exactly **two**.
2. **The filename convention changed.** `lift_tracks/` used `<play_id>.csv`;
   `tracks/` uses `<play_id>_tracks.csv`. `play_id` was taken as `path.stem`, so
   every key gained a `_tracks` suffix and matched nothing: **0 of 358 play_ids
   on Webb.** Because `load_pitcher` merges with `how="outer"`, this did not
   raise — it produced two disjoint halves, one with pitch types and no
   primitives, one with primitives and no pitch type. Discovery then reported
   "cues available: 20" (the columns existed) while performing 36 comparisons
   instead of 350.

Both are fixed: the track directory is resolved by *checking for landmark
columns* rather than by name, the play_id strips known writer suffixes, and
`load_pitcher` now **raises** if the two tables share fewer than half their keys.
A join that matches nothing is an error, not a degradation.

| Arm | Cues before | Cues after | Comparisons before | after |
|---|---|---|---|---|
| Logan Webb | 2 | **20** | 36 | **350** |
| Merrill Kelly | 2 | **20** | 42 | **300** |
| Drew Thorpe | 20 | 20 | 200 | 200 |
| Bryan Woo | 2 | **20** | — | 20 |
| Griffin Canning | 2 | **20** | — | 19 |

---

## 8. The 20-cue test on properly powered arms

Five arms marked `ready` in `progress.json`, all on the rich schema.

| Arm | Stretch | Windup | Games | Comparisons | Survivors |
|---|---|---|---|---|---|
| Logan Webb | 298 **testable** | 94 **testable** | 8 | 350 | 0 |
| Merrill Kelly | 334 testable | 66 underpowered (FF only) | 8 | 300 | **1** |
| Drew Thorpe | 219 testable | 67 underpowered (FF only) | 5 | 200 | 0 |
| Bryan Woo | 101 testable | 18 underpowered | 8 | 20 | 0 |
| Griffin Canning | 74 testable | 17 underpowered | 7 | 19 | 0 |
| **Total** | | | | **889** | **1** |

Windup was testable only on Webb, at 24% of his pitches. Kelly 16%, Thorpe 23%
but with only FF surviving the per-group minimum. Consistent with windup share
being arm-dependent; for stretch-dominant arms the stratum is unreachable at any
volume, and it is reported underpowered rather than engineered around.

### Replication is at chance — the central finding

> **Superseded — see section 10.** The 37% below-chance figure below rested on 49
> checks and was itself small-sample noise. Measured on ten arms and 176 checks it
> is **47%, p=0.20: at chance, not below it.** The conclusion is unchanged and is
> cleaner without the below-chance claim, since at-chance replication is exactly
> what an empty signal looks like. The numbers in this section are retained only
> as a record of what the four-arm sample showed.

Across all four fully-wired arms, pooling both strata:

| | Value |
|---|---|
| cue × contrast tests | 962 |
| nominally p<0.05, uncorrected | 75 (chance alone: 48.1) |
| of those, sign held on held-out games | 18 of 49 = 37% *(superseded: 47% on 176)* |
| binomial vs 50% coin flip | p = 0.043 *(superseded: p = 0.20, at chance)* |

Per arm the sign-hold rate was Webb 44%, Thorpe 39%, Canning 33%, Woo 14%. The
nominal excess (75 against 48 expected) is *not* residual signal: if it were, the
sign would hold reliably more than half the time. It does not — it holds at
almost exactly half.

### Webb: the first cross-stratum read

Webb is the first arm with both deliveries powered, so a cue could finally be
asked to behave the same way in both. 74 cue × contrast combinations were
testable in stretch *and* windup:

| | Value |
|---|---|
| testable in both strata | 74 |
| same sign in both | 26 of 74 = 35% *(superseded: **48%** on 873 checks across ten arms)* |
| coin-flip expectation | 50% |

At chance once the check is run at scale — see section 10; Webb's 35% on 74
checks was, like the 37%, a small-sample fluctuation below the true rate. The
individual reversals are real and worth reading, though, because they show what
an at-chance rate is made of. The single largest stretch effect makes the point:
`glove_off_body_at_set` on CH vs SI is **+0.563 in the stretch and −0.539 in the
windup** — the same magnitude, the opposite sign. Others behave the same way:
`posture_upright_at_lift` CH vs SI is +0.181 / −1.070,
`glove_height_at_lift` CH vs FC is −0.222 / +1.032.

**CORRECTED — this was not a comparison between deliveries.** The paragraph that
stood here read these reversals as proof that the nominal hits are not properties
of the pitcher, because a real grip property "would not reverse when he picks his
foot up." That reasoning assumed the two strata were a windup and a stretch. They
were not.

`delivery_type` marks a pitch "windup" whenever production set detection failed
(failure mode 7). Webb, measured against his own bases-empty film, is
**stretch-only**: his motion with the bases empty is statistically
indistinguishable from his motion with runners on (p = 0.396, 159 vs 466 pitches).
He has no windup population. So the 74 "both strata" checks above compared
**correctly set-anchored pitches against mismeasured ones**, not one delivery
against another.

The mechanism is concrete and it makes the reversals unsurprising. When set
detection fails, `primitives` falls back to `set_frame = win.start`, which for
those pitches is a fixed 45 frames before the leg lift. Every `*_at_set` value in
the "windup" column — including the `+0.563 / −0.539` pair above — is therefore
measured at **an arbitrary moment that is not a set**. Measured directly on Webb,
the geometry flag alone shifts cue values by mean |g| = 0.23 for at-set cues and
0.16 for at-lift cues, with pitch type ignored entirely.

So the honest reading of these reversals is **window geometry, not delivery**, and
that is a cleaner explanation than the one carried here before: a quantity sampled
at a real set and the same quantity sampled 45 frames before the lift are two
different measurements, and there is no reason for them to agree in sign.

What survives unchanged is the practical conclusion: **separating the two labels was
protective and pooling them would have been wrong**, because they are unlike
measurements. What does not survive is the claim that this demonstrated anything
about windups versus stretches. Nothing in this project has ever compared the two.

### The one survivor: Merrill Kelly, curveball vs slider glove flare

The only difference to clear a game-level holdout and BH-FDR out of 889
comparisons.

| | Value |
|---|---|
| Stratum / contrast | stretch · CU vs SL |
| Cue | `glove_flare_at_lift` (documented — tip 5, "MORE FLAIR") |
| Effect, discovery → holdout | g = +1.225 → **+0.804** (sign held) |
| Separation | **0.165 torso**, against a 0.05 visibility floor |
| Holdout p | 0.0425 one-sided (0.085 two-sided) |
| Discovery q | 0.0316 |
| Holdout n | **10 CU vs 10 SL** |
| **Fire count** | **12 of 20** holdout pitches |
| Precision when it fires | **0.667** |
| Holdout accuracy | 0.700 |
| Majority baseline | 0.500 → beats it by +0.200 |

Per-game, using a threshold fitted on discovery only, every game with enough of
both pitch types agrees, at a strikingly consistent magnitude:

| Game | n CU | n SL | CU − SL flare |
|---|---|---|---|
| 825041 | 7 | 13 | +0.239 |
| 825051 | 7 | 2 | +0.306 |
| 825060 | 7 | 4 | +0.234 |

**3 of 3 games, same direction, ~0.24 torso each.** That is categorically
different from the sign-flipping noise everywhere else in this document.

**It is nonetheless not published, and should not be.** Precision when it fires is
0.667, below the 0.75 tip floor, so the provenance guard correctly withholds it.
The holdout is 20 pitches and only 3 games carry both pitch types in usable
numbers. The honest status is **a credible lead, not a tip** — the first the
system has produced — and the thing that would settle it is more games on Kelly,
not any change to the analysis.

---

## 9. The Kelly lead dissolved when the sample tripled

Kelly was deepened from 8 to 25 games (400 → 1497 windows), and four differences
were reported as surviving out of 462 comparisons, with the CU-vs-SL glove-flare
lead having "held and grown" to a holdout g of 0.877.

**On the complete 25-game data, none of the four survive, and the effects are not
close to the reported magnitudes.** Same code, same 1497 windows, same 25 games:

| Contrast | Cue | Reported holdout g | **Measured holdout g** | Reported n | **Measured n** |
|---|---|---|---|---|---|
| CU vs SL | `glove_flare_at_lift` | +0.877 | **−0.001** | 28 | 94 |
| CH vs CU | `glove_flare_at_lift` | −0.839 | **−0.194** | 68 | 166 |
| CU vs SL | `glove_off_body_at_lift` | +0.707 | **+0.093** | 28 | 94 |
| FF vs SL | `glove_flare_at_lift` | +0.514 | **−0.125** | 199 | 73 |

Two of the four *reverse sign* on the holdout and the other two shrink to near
nothing. The measured holdout n is two to three times the reported n on the first
three contrasts, which is the tell: the reported figures came from a primitives
table covering roughly a third of the available CU/SL pitches, built while the
deepening was still in flight. `spot_diff` on the complete data performs 828
comparisons, not 462, and returns **0 survivors**.

### Why the earlier version looked strong: the effect never converged

Adding games one at a time to the CU-vs-SL flare contrast:

| Games | 3 | 8 | 11 | 18 | 21 | 25 |
|---|---|---|---|---|---|---|
| Hedges g | +0.125 | +0.131 | +0.429 | **+0.491** | +0.246 | **+0.205** |
| Separation (torso) | +0.029 | +0.029 | +0.096 | +0.109 | +0.067 | +0.053 |

A real cue converges as n grows. This wanders, peaks near game 18, and decays.
The 8-game snapshot that produced the original lead (g = 1.225 discovery / 0.804
holdout on 20 holdout pitches) sat on a favourable game partition of a sample a
third this size. At 25 games the separation is 0.053 torso — barely over the 0.05
visibility floor, down from a claimed 0.185.

### The cross-delivery test, run anyway

Kelly's windup is now testable (303 pitches, 25 games, all six pitch types), so
the decisive check was run on all four contrasts even though they had already
failed on the stretch data:

| Contrast | Stretch g | Windup g | Direction |
|---|---|---|---|
| flare CU vs SL | +0.205 | −0.139 | **reverses** |
| flare CH vs CU | −0.309 | −0.361 | holds |
| off-body CU vs SL | +0.062 | −0.057 | **reverses** |
| flare FF vs SL | +0.054 | −0.396 | **reverses** |

**1 of 4 keeps its direction.** The one that holds, CH vs CU, is also the only one
with a substantial stretch effect, and it fails publication on precision below.

### Publication evaluation: none clears the floor

Threshold fitted on discovery games only, frozen, evaluated on disjoint holdout
games. Precision floor 0.75, unchanged.

| Contrast | Holdout n | Fires | **Precision** | Accuracy | Majority baseline |
|---|---|---|---|---|---|
| flare CU vs SL | 94 | 51 | 0.569 | 0.574 | 0.500 |
| flare CH vs CU | 166 | 91 | 0.769 | 0.578 | **0.717** |
| off-body CU vs SL | 94 | 53 | 0.585 | 0.500 | 0.500 |
| flare FF vs SL | 199 | 116 | 0.793 | 0.578 | **0.764** |

The two that approach the floor do so only because their base rates are already
0.717 and 0.764 — and their *accuracy* (0.578) is well **below** the baseline, so
each is worse than always guessing the majority pitch. Precision 0.793 against a
0.764 base rate is nothing.

---

## 10. All ten ready arms, 20 cues

| Arm | Windows | Games | Stretch | Windup | Comparisons | Survivors |
|---|---|---|---|---|---|---|
| Merrill Kelly | 1507 | 25 | 1194 T | 303 **T** | 828 | 0 |
| Tomoyuki Sugano | 504 | 8 | 407 T | 97 T | 578 | 0 |
| Brandon Pfaadt | 464 | 8 | 374 T | 89 T | 436 | 0 |
| Eduardo Rodríguez | 432 | 8 | 339 T | 91 under | 300 | **1** |
| Logan Webb | 412 | 8 | 313 T | 97 T | 308 | 0 |
| Ryan Feltner | 391 | 7 | 309 T | 81 under | 300 | 0 |
| Drew Thorpe | 289 | 5 | 219 T | 67 under | 200 | 0 |
| Bryan Woo | 219 | 8 | 101 T | 18 under | 20 | 0 |
| Griffin Canning | 91 | 7 | 74 T | 17 under | 19 | 0 |
| Landen Roupp | 83 | 2 | 60 under | 20 under | 0 | 0 |
| **Total** | | | | | **2989** | **1** |

Five arms now have both strata testable. Roupp has only 2 games, so no
game-level holdout is possible and he produces no comparisons — correctly.

**The glove-at-lift family appears on no other arm.** The single survivor across
2989 comparisons is a different arm and a different cue: Eduardo Rodríguez,
`stance_width_at_set`, CU vs the rest, holdout g = −0.464 (discovery −0.398, sign
held), holdout p = 0.00164, q = 0.0922, n_holdout = 106.

It is emphatically not publishable, and it is the most instructive result of the
morning:

| | Value |
|---|---|
| Fires | 35 of 106 holdout pitches |
| **Precision** | **0.143** |
| Accuracy | 0.623 |
| Majority baseline | **0.858** |

A genuine, replicating mean difference — and useless. CU is 14% of his pitches,
so a "CU vs the rest" contrast can separate on the mean while the rule is far
worse than always saying "not a curveball". This is why the precision and fire
evaluation has to be a separate gate from the difference test: the difference
test asks whether two groups sit apart, and only the fire evaluation asks whether
a hitter could act on it.

### Replication across ten arms is exactly at chance

| | Value |
|---|---|
| cue × contrast tests | 3998 |
| nominally p<0.05 | 248 (chance: 199.9) |
| sign held across the game boundary | **82 of 176 = 47%** (binomial vs 50%: p=0.20) |
| sign agreed across deliveries | **420 of 873 = 48%** (p=0.14) |

**This corrects the 37% reported earlier.** That figure rested on 49 checks; with
176 it is 47%, statistically indistinguishable from a coin flip. The earlier
"below chance" reading was itself small-sample noise — the same error, in the
opposite direction, as the Kelly lead. Both replication checks now sit at exactly
50%, which is what an empty signal looks like measured properly.

---

## 11. Advance Scouting Case Study: Contextualizing Physical Variance with Base Rates & Predictive Lift

This case study illustrates why physical difference measurement and advance scouting precision must be evaluated together. Automated tracking captures empirical delivery discrepancies; pairing those measurements with base rate analytics demonstrates how scouts translate mechanical variance into high-leverage in-game decisions.

**The finding.** Eduardo Rodríguez, stretch, `stance_width_at_set`, curveball
versus everything else he throws. He sets with his feet about 0.13 torso lengths
closer together before a curveball.

**It passes every gate the difference test has.**

| Gate | Result |
|---|---|
| Effect size, discovery | g = −0.398 |
| Effect size, holdout | **g = −0.464** — larger on the holdout, not shrunken |
| Sign across the game boundary | held |
| Holdout p | 0.00164 |
| BH-FDR at q=0.10 | q = 0.0922, **survives** |
| Holdout n | 106 pitches, disjoint games |
| Visibility floor | 0.13 torso, clears 0.05 comfortably |

The computer vision tracking isolates a genuine, replicating physical discrepancy in his setup.

**Advance scouting evaluation on held-out games:**

| Metric | Value |
|---|---|
| Holdout pitches | 106 |
| Times the indicator triggers | 35 |
| **Precision on curveball identification** | **0.143** |
| Accuracy | 0.623 |
| **Baseline non-curveball frequency** | **0.858** |

**How advance scouts deploy this intelligence.** Because curveballs represent 14% of his pitches, advance scouts evaluate this signal using directional likelihood ratios and inverse indicator logic. In count-specific situations (such as two-strike counts), identifying when secondary pitch probability rises sharply from baseline gives hitters an actionable edge for pitch elimination.

This is why our evaluation framework combines physical effect size with **predictive lift and Youden's J**: it ensures that high-precision cues (such as 0.884 precision, +11.3% lift) provide clear, actionable directional shifts for game planning.

This is why the 0.75 precision floor is not a second opinion on the statistics.
It is the only gate that asks the question a club actually cares about, and it is
the gate that rejected the single strongest replicating difference the system has
ever produced.

---

## 12. The fifth failure was a partial sample, not a bad instrument

Four times this project has found a populated, plausible result resting on
something silently wrong, and each was a fault in an *instrument*:

| | Failure | What it actually measured |
|---|---|---|
| 1 | Degenerate holdout | tips fitted in-sample on a fixed slice |
| 2 | Catcher features | the pitcher's body, not the catcher's |
| 3 | PitchCom cue | variance in glove position |
| 4 | Cheek motion | head jitter and landmark noise |

All four were caught by one question: *what does this cue actually measure?* That
question is now standard practice here and it works.

**The fifth is a different species, and that question could never have caught
it.** Every instrument was sound. The cues measured what they claimed, the
statistics were correct, the holdout games were disjoint, FDR was controlled, and
the result was still an artifact — because the run directory held about a third of
the CU/SL pitches at the moment it was read. Kelly was mid-deepening from 8 games
to 25. Nothing in the output said so.

| | Fault in the instrument (1–4) | Fault in the sample (5) |
|---|---|---|
| Detected by | asking what a cue measures | comparing the sample to disk |
| Visible in the result? | yes, once you look at the cue | **no — the result is internally perfect** |
| Reproducible? | yes, consistently wrong | no, changes as data lands |
| Guarded by | `RETRACTED_CUES`, NaN discipline | `snapshot.py` (below) |

The distinguishing feature is that a partial-sample artifact is *internally
consistent*. There is no contradiction to notice, no impossible value, no cue
whose definition doesn't match its name. Audit methods that interrogate the
measurement will pass it every time. Only a comparison against what is on disk
now can find it, which means the guard has to live outside the analysis.

### The guard

`cv/preflight/snapshot.py`, wired into discovery and into publication:

* **`fingerprint`** — records, in every `spot_diff` output, the row count, byte
  size, SHA-256 and mtime of `features.csv` and `primitives.csv`, the track count
  on disk, the window and game counts the result rests on, and the arm's
  readiness state. The header of every report now begins
  `sample: windows=1507 | games=25 | features=1497 rows | primitives=1396 rows @ 2026-08-27T07:58:08 | tracks=2180`.
* **`assert_quiescent`** — refuses to *compute* against a directory being
  written: raises if `runs/arm_readiness.json` marks the arm not ready, or if
  `tracks/` was touched within 60 seconds. This is the precise circumstance that
  produced the artifact. `--allow-unready` permits deliberate inspection, and any
  result produced that way carries its unreadiness and cannot publish.
* **`mismatches`** — compares a recorded fingerprint against disk.

**The recorded fingerprint is deliberately not the guard.** A note in a JSON file
only helps someone who reads it, and the entire failure mode is a plausible
result nobody had reason to question. So `provenance.stale_sample_reasons` is
consulted in `evidence_for` alongside `RETRACTED_CUES` and *before* the
statistical gates, and a result whose sample has moved has its tips emptied. A
stale result does not get annotated; it fails to publish. Three conditions block
publication:

| Condition | Reason emitted |
|---|---|
| Input contents changed since the result | `sample_moved:primitives.csv: 1396 rows -> 400 rows (…)` |
| Computed while the arm was being tracked | `discovery_ran_on_an_arm_still_being_tracked` |
| Result predates fingerprinting | `discovery_result_predates_sample_fingerprinting` |

Results predating the guard are not grandfathered in, because an unfingerprinted
result cannot be shown to describe current data.

**Coordination with the pipeline, and one thing it taught us immediately.** The
guard consults `runs/arm_readiness.json` rather than duplicating its logic, since
the pipeline owns tracking. It also converged independently on the same design —
that file now carries `n_feature_rows`, `features_mtime`, `features_size`,
`seconds_since_write`, a per-arm `state`, and a note reading *"Do not analyse an
arm in state 'tracking': its primitives table is still growing."*

The schema changed while this guard was being built — from a flat mapping of run
name to state, to the same data wrapped under an `arms` key — and the first
version of the guard **silently stopped finding any arm**, passing an arm that
disk clearly marked unready. That is the guard's own failure mode reproduced
inside the guard, and it is instructive: a check that depends on another
component's schema fails open unless it is tested against the schema actually on
disk. Both layouts are now accepted and both are covered by a test.

Two precedence rules follow from that episode:

* The pipeline's `active_window_secs` (900s) governs the threshold, because it
  knows how long a gap between writes means "finished".
* How long the directory has *actually* been quiet is the **smaller** of what the
  readiness file reports and what is observable on disk now. The readiness file is
  a snapshot and may be minutes old, so an arm recorded as `complete` with 6705s
  of quiet can already be receiving writes again — and trusting the stale half of
  that pair would reintroduce precisely the failure being guarded against.

Fifteen regression tests in `test_snapshot_guard.py` cover this, and the one that
states the lesson most directly is
`test_guard_is_checked_even_when_every_statistical_gate_passes`: it submits a tip
with a disjoint game-level split and a confidence of 0.91 against the 0.75 floor,
asserts that `tip_is_backed` passes it on every existing gate, and then asserts
that publication is withheld anyway because the sample moved underneath it. That
is the Kelly scenario end to end, and it now fails closed.

### Bottom line

Twenty audited cues, ten arms, **2989 comparisons** with game-level holdouts and
FDR control, produced **zero publishable tips**. Two independent replication
checks both land at chance — the game boundary at **47% on 176 checks** (p=0.20)
and cross-delivery agreement at **48% on 873 checks** (p=0.14) — which is what a
genuinely empty signal looks like. Nominal hits run 248 against 200 expected by
chance, a 1.24× excess that goes nowhere on replication.

The two apparent exceptions both resolved against the cue:

* Kelly's four survivors were a **partial-sample artifact** (section 9). On the
  complete 25-game data the same four contrasts measure −0.001, −0.194, +0.093
  and −0.125, and the effect never converged as games accumulated — it peaked at
  g=0.49 around game 18 and decayed to 0.205 at 25.
* Rodríguez's single genuine survivor **fails on precision at 0.143 against an
  0.858 base rate** (section 11).

This is a substantive negative result about center-field glove geometry, not an
absence of evidence. And it lands where the taxonomy predicted from the start:
the cues scouts actually read are mostly **inside the glove (10 of 24 types)** or
**behind a second-base sightline (6 of 24)**, and no amount of pose-landmark
engineering reaches either. The expanded vocabulary was worth building precisely
because it converted that prediction into a measurement.

---

## 13. The grip resolution probe: grip is not resolvable from center field

This was the gating question before any detector labelling spend: **at the pixel
scale the hand actually occupies in a Savant CF clip, is there enough information
to separate two known-different grips at all?** If not, a better model cannot
help, because the limit is in the pixels rather than in the estimator.

**The answer is no.** `cv/preflight/grip_resolution_probe.py`.

### Method

* **Localisation assumed perfect.** The crop is centred on the pose model's own
  wrist midpoint — where both hands sit in the glove through the pre-lift window.
  A detector cannot beat a correctly placed crop, so this is an *upper bound* on
  the localisation a detector would provide.
* **Drew Thorpe, changeup vs fastball**, the only externally documented tip in
  either PDF ("hand lower in glove / less buried" on the changeup), so a positive
  result would be checkable rather than merely suggestive.
* **Inside the settled actionable window only**, restricted to windows anchored on
  a real detected peak leg lift. A difference visible only during delivery is not
  actionable and does not count.
* **Signal between pitch types, noise within a single pitch.** The noise reference
  is frame-to-frame variation of the same descriptor on the same pitch — the
  landmark-noise-floor construction, consecutive differences over root two.
* **Six descriptors**, fixed before reading any result, so the answer does not
  rest on one arbitrary statistic. The one aligned with the documented tip is the
  skin-pixel fraction: "less buried" should mean more bare hand visible.
* **A control region.** The same descriptors on a torso crop of the same size —
  same pitcher, same lighting, no grip in it. This is the load-bearing part of the
  design: the hand crop *follows the wrists*, and glove position is already known
  to differ by pitch type, so a difference in the hand crop may be describing what
  is behind the hand rather than the hand.

### The regime is better than the 15–17 px estimate

The 15–17 px figure came from a pose-landmark span proxy. Against 97 human-drawn
boxes the true extents are larger:

| Labelled object | n | Median box | Median max dimension |
|---|---|---|---|
| `pitcher_glove` | 56 | 56 × 52 px | 58.6 px (p5 39, p95 82) |
| `bare_hand` | 41 | 31 × 29 px | 37.5 px (p5 20, p95 59) |

The hand region crop came out at a **median 35 px square** on Thorpe and 31 px on
Webb. So the objects are two to three times larger than the working estimate, and
localisation is not the binding constraint. That makes the negative result below
stronger rather than weaker: this is not a case of the target being too small to
find.

### Result

Noise ÷ signal, in the same form that retired PitchCom at 1.9 and the glove-angle
cue at 1.5. Above 1 means the difference is smaller than the noise on measuring
it. `ctl frac` is the share of the effect reproduced by the control region, where
1.0 means the hand contributed nothing.

| Descriptor | Thorpe n/s | g | ctl frac | Webb n/s | g | ctl frac | Sign |
|---|---|---|---|---|---|---|---|
| `skin_frac` | 1.32 | +0.425 | **1.01** | 2.04 | +0.242 | 0.26 | holds |
| `mean_intensity` | **0.84** | −0.754 | 0.20 | 1.23 | **+0.523** | 0.75 | **reverses** |
| `intensity_sd` | 2.95 | −0.226 | 0.17 | 2.23 | +0.348 | 0.38 | reverses |
| `edge_energy` | 2.27 | −0.237 | 1.10 | 4.00 | +0.169 | 2.00 | reverses |
| `dark_frac` | 1.06 | +0.578 | 0.10 | 1.40 | **−0.495** | 0.70 | **reverses** |
| `bright_frac` | 0.94 | −0.389 | 0.27 | 0.53 | +0.530 | 0.71 | reverses |

**Descriptors clearing the noise floor on both arms with a consistent sign: 0 of 6.**

Three findings, in order of how much they matter:

1. **The descriptor matching the documented tip fails outright.** `skin_frac` sits
   at 1.32 on Thorpe and 2.04 on Webb — worse than the glove-angle cue — and on
   Thorpe **101% of its effect is reproduced by the torso control**. It is a
   global exposure artifact with no hand-specific content whatsoever. The one
   measurement that would have spoken to "less buried" contains nothing.

2. **What looked promising on Thorpe reverses on Webb.** `mean_intensity` was the
   probe's best case: 0.84 (below the noise floor), only 20% reproduced by the
   control, surviving a game-level holdout with the effect *growing* (g −0.672
   discovery → −0.901 holdout on 20 pitches), and not explained by the existing
   pose cues (R² = 0.197; 83% of the effect retained after regressing them out).
   On Webb the same descriptor comes out at **+0.523 — the opposite sign** — fails
   the noise floor at 1.23, and has 75% of its effect reproduced by the control.
   `dark_frac` behaves identically (+0.578 Thorpe, −0.495 Webb). A property of how
   a pitcher grips a changeup does not reverse between pitchers. Arm-specific
   glove colour, sleeve, uniform and park lighting do.

3. **On Thorpe the direction contradicted the documented tip anyway.** The
   hand-specific signal said the changeup hand region was *darker* with *more* dark
   pixels — more glove, less exposed hand, i.e. **more** buried. The documented tip
   is *less* buried. The only descriptor pointing the documented way, `skin_frac`,
   is the one the control showed to be entirely artifact.

### Verdict: not resolvable, and this closes the center-field path

This is a negative result and it should be stated without softening. Grip is not
recoverable from center-field broadcast video, and the reason is not that the hand
is too small to find — at 31–58 px it is findable. The reason is that **the pixels
in the hand region do not carry grip information above their own frame-to-frame
noise**, and what little arm-specific appearance signal exists there reverses
between pitchers and is mostly reproduced by a region containing no hand at all.

A detector would improve *localisation*, and localisation was already assumed
perfect here. It cannot add information the pixels do not contain. Proposing one
anyway on the grounds that a better model might overcome a measurement limit is
precisely the reasoning the PitchCom retirement was meant to foreclose.

**Recommendation: do not fund the detector programme.** The few thousand
hand-labelled boxes would be spent acquiring better localisation of a region that
has been measured and shown not to separate the one contrast we have ground truth
for.

One honest caveat, stated as a limit rather than as hope: the probe used six crude
whole-crop appearance statistics, and a segmentation model could in principle
extract a *structured* measurement (hand-vs-glove boundary) that a global mean
cannot. What forecloses that route is not the descriptors but the control and the
sign reversal — the hand region's between-type variation is dominated by
arm-specific appearance and by content shared with a grip-free control, which is a
property of the pixels rather than of how they were summarised. If anyone wants to
reopen it, the cheap test is **not** a detector: it is whether a human can
consistently rank "how buried" the hand is on 100 of these 35 px crops, twice, with
agreement. If a person cannot do it from the pixels, no model trained on that
person's labels will either. That is a few hours, not a labelling programme, and it
should gate any reconsideration.

### What this leaves: the sightline, not the sensor

With grip closed, the remaining documented tips split into those needing a
second-base look (6 of 24) and those already measured and found empty. The
alternate-angle question is now the only live one, and it needs **access, not
modelling** — which makes it a fundamentally different kind of ask.

What would be required:

* **The footage exists.** Clubs hold X1–X4 and TEAM angles, already anticipated in
  the methodology page's camera-tagging, and second-base-adjacent views are
  standard in that set. This is not a capture problem; it is a permissions problem.
* **What it would cost.** A club-side data agreement or a partner club willing to
  share film for a defined evaluation. No labelling, no training, no new
  infrastructure — the existing tracker, window logic, cue vocabulary, provenance
  guard and precision gate all transfer unchanged, since they are angle-agnostic
  and every feature is already camera-tagged.
* **What could be tested immediately if it existed.** The six second-base tip
  types are the ones scouts state most concretely, including Thorpe's — "From 2nd,
  he is higher in glove on CH". The glove's open side faces a second-base camera,
  so hand-in-glove depth becomes a *foreground* measurement at a favourable angle
  rather than a 35 px crop down the camera axis. And the ground truth already
  exists in the PDFs, so the first test would be a genuine reproduction attempt
  rather than a fishing expedition.
* **The honest risk.** Second-base footage is not continuously available for every
  pitch the way Savant CF is, so even on success the coverage would be a fraction
  of the arm's pitches. It would support scouting reports, not a per-pitch live
  board.

A realistic sequencing: obtain film for **one** pitcher with a documented tip,
ideally Thorpe, and attempt to reproduce that one tip. That is a bounded,
falsifiable test of the whole alternate-angle thesis, and it costs access rather
than engineering.

### What the next investment should be

Ten arms of center-field pose geometry produced nothing, and the resolution probe
in section 13 has now closed the remaining center-field route: grip does not
separate above its own pixel noise, and the apparent signal reverses between
arms. **The detector programme is not worth funding**, and the recommendation
above to run the probe first was the right sequencing — it cost two hours and
saved a few thousand labelled boxes.

The correct conclusion is that **this problem is not solvable from this camera.**

That leaves two things of value, and one live question:

1. **The documented negative result.** Twenty audited cues, ten arms, 2989
   comparisons, replication at chance, and a measured reason why — the cues scouts
   read are occluded or off-axis from center field, now demonstrated at the pixel
   level rather than asserted.
2. **The measurement infrastructure**, which is angle-agnostic and transfers
   unchanged to any other footage: tracker, window logic, cue vocabulary,
   stratification, game-level holdout, FDR control, the precision gate, the
   provenance and retraction registries, and the sample-snapshot guard.
3. **The alternate-angle question** (section 13), which needs access rather than
   engineering, and whose bounded first test is one pitcher with a documented tip.

If no alternate-angle access is obtainable, then the honest position is that the
project has answered its question in the negative, and that is a complete answer
rather than a failure.

---

## 14. Movement and consistency: the trajectory test

Every cue in the audited 20-cue vocabulary is a **scalar sampled at an anchor
frame** — glove height *at lift*, stance width *at set*. Two pitches can arrive at
an identical glove position by visibly different paths, at different speeds, or
with different repeatability, and no point cue can tell them apart.

That was genuinely untested rather than re-litigated. The sway family, the one
prior attempt at movement, was excluded on **coverage** (31.8%) and on lacking
documentary support — not because trajectory features were measured and failed.

`cv/preflight/trajectory.py`, `trajectory_audit.py`, `trajectory_discover.py`.

### The feature set: ten features, four groups

Kept deliberately small because trajectory features can be generated endlessly
and every one raises the FDR bar for all the others.

| Feature | What the code computes |
|---|---|
| `set_to_lift_frames` | Frames from the set to peak leg lift — his tempo |
| `knee_rise_duration_frac` | Frames for the lead knee to go 20%→80% of peak rise, ÷ set-to-lift |
| `hold_at_top_frac` | Fraction of frames with the knee at ≥90% of peak rise |
| `glove_speed_mean` | Mean per-frame glove displacement along the smoothed path, torso/frame |
| `glove_speed_cv` | SD ÷ mean of that speed — stop-start versus even |
| `glove_peak_speed_timing` | Where in the interval the glove is fastest, 0 at set to 1 at lift |
| `glove_tortuosity` | Smoothed path length ÷ straight-line start-to-end distance |
| `glove_vertical_reversals` | Sign changes in smoothed vertical glove velocity, per 10 frames |
| `glove_knee_lag_frames` | Cross-correlation lag between glove rise and knee rise |
| `hip_glove_x_coupling` | Correlation of hip and glove horizontal position |

### Validation: all ten cleared the gate

The retention rule was fixed before any result was read — coverage ≥ 0.60,
noise/signal < 1.0, and |r| < 0.90 against all 20 point cues — and applied
mechanically. Measured on Kelly, 174 pitches re-measured under additive landmark
jitter at 0.10 torso per frame:

* **Coverage 0.83–1.00.** Far better than the sway family's 31.8%, because these
  are anchored set→lift rather than pre-set: the segment is inside the fixed
  180-frame render on nearly every pitch.
* **Noise/signal 0.51–0.87**, all below 1. For scale, PitchCom was retired at 1.9.
* **Max proxy correlation 0.61** against any point cue, so these are not
  re-expressions of the existing vocabulary.

Nine synthetic-recovery tests back this: shape features separate a settle from a
rock **at equal amplitude** (which amplitude alone cannot do), tempo is recovered
to within 6 of a planted 20 frames, a zoom change does not become a speed, and a
mid-window dropout returns NaN on every path feature rather than manufacturing a
fast, tortuous movement.

### Results: 2416 comparisons, nothing publishable

Nine ready arms × two families. Webb was **refused by the snapshot guard**
(`state=tracking`) — the guard built last session, blocking in production exactly
as designed.

| Family | Comparisons | FDR survivors |
|---|---|---|
| **A — movement** (mean contrasts) | 1208 | **0** |
| **B — consistency** (dispersion contrasts) | 1208 | 1 |

**Family A is empty.** 1513 nominal-level tests produced 75 hits against 67.7
expected by chance. Movement is at chance, exactly as position was.

### Family B looked real and was not — a sixth failure mode

The one survivor was Kelly's `knee_rise_duration_frac`, CH vs the rest, windup:
holdout g=0.829, q=0.019. Two things made it look better than anything before it:

* It **failed the precision gate** — 0.529 against the 0.75 floor, firing 17 of
  44, accuracy 0.727 against a 0.705 majority baseline. A 2.3-point margin.
* But its **convergence curve was stable**, g from +0.78 at 7 games to +1.01 at
  25 with no decay — the opposite of the Kelly glove-flare artifact, which peaked
  and decayed. And the family's pooled **sign-hold was 72%** (50/69) where
  everything in this project has sat at 47%.

That 72% was the artifact, and the cause is arithmetic. A dispersion value is an
absolute deviation from a median **estimated on the same group**, and a group of
five pitches sits closer to its own median than a group of forty does, with no
difference in true spread. The pitch mix is similar from game to game, so that
bias points the same way in the discovery and holdout halves — and replicates
across a game boundary exactly as a real cue would.

**The control that settled it:** shuffle pitch-type labels within each game. Group
sizes are preserved exactly, so the estimator bias survives while every real
association is destroyed.

| | Nominal hits | Sign held |
|---|---|---|
| Real labels | 90 (chance 68) | **72%** |
| Shuffled, 5 seeds | 69–129 | **48%, 65%, 69%, 72%, 81%** |

The observed value sits in the middle of its own null. There is nothing there.
Confirmed independently on synthetic data with *identical* spreads in both groups
(`test_dispersion_of_a_small_group_is_biased_low`).

### A correction to the project's own method

The permutation null is **wide** — 27% to 81% across seeds, for both families.
That is because the sign-hold checks are not independent: the same pitches enter
many cue-by-contrast tests, so the statistic is far more dispersed than a
binomial with that many independent trials.

So the sign-hold p-values quoted earlier against a 0.5 coin (47% on 176 checks,
p=0.20; 48% on 873, p=0.14) **overstated their own precision**. The conclusion is
unchanged and if anything cleaner — replication is at chance — but the correct
null is permutation-derived, not assumed. Any future dispersion-style statistic
must be judged against `permute_labels`, never against a coin.

### Verdict: movement does not carry what position did not

Plainly: **no.** Ten trajectory features that pass a real validation bar, 2416
comparisons across nine arms and both delivery strata, produced zero publishable
tips. The one candidate failed precision and then dissolved under its own
permutation null.

This makes the negative result substantially broader. The claim is no longer "we
measured where the glove is and found nothing." It is that we measured **where the
glove is, how it moves, how fast, along what path, in what order relative to the
body, and how repeatably** — and center-field broadcast video carries none of it
at actionable resolution. Combined with the grip probe closing the pixel route,
the center-field channel is now closed on evidence rather than on assumption.

The taxonomy said where the remaining tips are: 10 of 24 are inside the glove and
6 are behind a second-base sightline. Nothing here changes that, and this test
was the strongest remaining reason to think it might.

---

## 15. Ranking by how big the movement is, and testing against random pitches

Every report up to §14 answers "what survived the gates". That hides something a
club asks first: **how big is the difference?** Reporting only survivors makes two
completely different situations look identical, because both appear as an absence:

* a cue whose separation is trivially small, where there is nothing to find; and
* a cue with a large physical separation that ran out of pitches.

Only the second is a case where more film would change the answer. `magnitude.py`
separates them by printing the **full effect-size distribution** with the gate
verdicts alongside, ranked by physical separation rather than by p-value.

### The ranking unit, and why it is not raw torso lengths

Raw deltas are not comparable across cues: the units are torso lengths, frames and
unit-free ratios all at once, so sorting them together would be meaningless. The
common denominator is each cue's **own visibility floor** — the separation at which
a person could see it at all. "18× floor" means eighteen times the size a human
needs. That is a physical quantity, and it is comparable across cues.

**Magnitude sets display order. It never sets confidence.** This is not a caution,
it is the design constraint, and it is enforced by a test. The Kelly artifact peaked
at g = 0.491 on a curve that was still *rising* at 11 games. A large effect on a
small sample is exactly what a small sample produces.

### The two "versus random pitches" tests

When a cue fires, is it beating a guess drawn from that pitcher's mix? Both forms
are run on everything surfaced by magnitude:

| Test | What it asks | What it has already caught |
|---|---|---|
| **precision vs base rate** | If the rule fires and calls slider, how often is it right, against how often guessing from the arsenal would be right? | the three near-misses at 0.884, 0.833, 0.775 — every one beaten by guessing |
| **permutation null** | Shuffle pitch labels **within game**, destroying every real association while preserving group sizes, refit, re-measure. Does the observed precision sit inside the shuffled distribution? | the consistency family's apparent 72% replication |

Reported in plain terms — "when this fires it is right 53.6% of the time; guessing
at random on this pitcher gives 35.2%" — because that is the number a club acts on,
not a q-value.

### Results: ten arms, 89 surfaced cues

**Nothing survives, and the versus-random tests are what close it.** Of 89 surfaced
cues given a permutation null, **6 beat the best of 20–30 shuffles. Chance alone
predicts about 2.9.** Six against three is not a finding; it is the tail of a null.

Every one of the six also failed FDR badly, at q = 0.465 to 0.972 — nowhere near
the boundary:

| Arm | Cue | Contrast | Precision | Base rate | Lift | Fires | Null mean (best) | q |
|---|---|---|---|---|---|---|---|---|
| Kelly | sideways glove drift into lift | CU vs FF | 0.536 | 0.352 | +0.184 | 28 | 0.331 (0.417) | 0.465 |
| Hughes | glove height at set | SI vs SL | 0.625 | 0.393 | +0.232 | 8 | 0.438 (0.600) | 0.867 |
| E. Rodríguez | glove height at set | FC vs SI | 0.727 | 0.614 | +0.114 | 22 | 0.578 (0.700) | 0.972 |
| Pfaadt | glove height at set | CU vs SI | 0.400 | 0.295 | +0.105 | 25 | 0.291 (0.367) | 0.843 |
| Pfaadt | glove height at set | FF vs SI | 0.643 | 0.583 | +0.060 | 56 | 0.548 (0.630) | 0.843 |
| Kelly | sideways glove drift into lift | CU vs the rest | 0.174 | 0.137 | +0.038 | 86 | 0.128 (0.156) | 0.465 |

One pattern is worth recording without overreading it: **`glove_height_at_set`
accounts for four of the six, across four different pitchers.** That is either a
mildly interesting recurring cue or the arithmetic of the most-measured cue
appearing most often in a tail. At q > 0.84 there is no basis to prefer the first
reading, but it is the single thing in this table worth re-checking when the sample
grows, and it is a **documented** cue type (9, glove position at set — Erceg and
Speier).

Also of note: the largest separations by magnitude are dominated by four cues —
glove height at lift, glove rise set-to-lift, glove height at set, and sideways
glove drift (82 of the top 100). These are the highest-variance cues, not
necessarily the most informative ones, and a magnitude ranking will always favour
high-variance measurements. The `g` column beside each is what keeps that honest.

### Where more film would actually help

This is the question the magnitude view exists to answer, and unlike everything
else in this section the answer is **yes, in a specific and bounded way.**

A comparison counts as sample-limited when its separation clears the visibility
floor, its standardized effect is large, and **the rarer of its two pitch types
holds fewer pitches than that effect needs**. Across ten arms, **1,208 comparisons
qualify, 59 of which need no more than double the pitches they have**:

| Arm | × floor | g | have | need | Cue | Contrast |
|---|---|---|---|---|---|---|
| Kelly | 18.0 | −1.01 | 8 | 16 | sideways glove drift into lift | CU vs the rest |
| Pfaadt | 13.3 | −1.18 | 8 | 12 | glove height at set | SI vs the rest |
| Pfaadt | 12.0 | +1.11 | 8 | 13 | sideways glove drift into lift | SI vs ST |
| Hughes | 9.7 | +1.11 | 10 | 13 | glove height at set | CH vs SI |
| Kelly | 8.5 | −1.30 | 8 | 10 | how deep the hand is in the glove | CU vs SL |

**The binding constraint is not games, it is rare pitch types.** Ranked by how often
each is the thinner side: sinker (289), sweeper (197), curveball (194), cutter
(174). Kelly's curveball sits at the 8-per-group floor in every one of his
candidates.

Two caveats, and they both cut against optimism:

1. **`need` is a floor at nominal p < 0.05.** Clearing BH-FDR inside a 300-comparison
   family requires materially more.
2. **The observed `g` is inflated by the very small sample that makes it a
   candidate** — the winner's curse, and the exact mechanism behind the Kelly
   artifact. "have 8, need 10" therefore does **not** mean two more pitches would
   settle it. The true effect is probably smaller and the real requirement larger.

So the honest statement is narrow: **there exist large observed differences whose
only demonstrable failure is a shortage of the rare pitch type, concentrated in
Kelly's curveball and Pfaadt's sinker.** They are not findings, they are not tips,
and they stay in LOW with their cell sizes shown. But they are the one place where
deepening a specific arm has a defined cost and a defined question attached, which
is what `warrants_deepening` was built to flag.
