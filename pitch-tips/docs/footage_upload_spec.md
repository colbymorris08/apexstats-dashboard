# The pivot: upload film for a few arms, not the league

The centre-field run answered its question. Ten arms, 2989 point-cue comparisons
and 2416 trajectory comparisons, replication at chance, and — the part that
matters here — **five separately measured limits that are all limits of the
film, not of the method**:

| Limit | Measurement | Fixed by better film? |
|---|---|---|
| Grip / hand-in-glove (10 of 24 tip types) | hand crop 35 px; 0 of 6 descriptors clear the noise floor; best one reverses sign between arms; 101% of the leading effect reproduced by a hand-free control crop | partly — see §5 |
| Sightline (6 of 24 types) | recorded verbatim as second-base reads | **yes, entirely** — geometry, no modelling |
| Pre-set coverage | need 90 frames of lead-in at 60 fps; median clip gives 25; ~31% give none | **yes, entirely** |
| PitchCom | wrist jitter 0.116 torso/frame against a 0.060 maximum plausible tap | only with a tight, high-rate camera |
| Face | 11 px mouth; pitcher's face found in 1.04% of frames | only with a dedicated tight shot |

So the product changes from "score the league from the one angle that is free"
to **"upload everything you have on this pitcher before you face him"**. A
club's own film is continuous, higher-resolution, multi-angle, and complete for
its own games. That removes the acquisition limit rather than working around it.

The centre-field result is not discarded. It becomes the documented baseline —
the measured reason better film is required — and it is the reason a club should
believe this evaluation rather than a demo.

---

# Part 1 — What to upload

Hand this section to whoever controls the film. Everything in it is derived from
a measurement above or from the quota arithmetic in `quota_select.py`.

## 1.1 Angles, ranked by what each one unlocks

Tag every file with which of these it is. The pipeline is already camera-tagged;
it is not already camera-*calibrated* (§7).

| Rank | Angle | What it buys | Why |
|---|---|---|---|
| 1 | **Second base / low centre behind the pitcher, at runner eye height** | 6 tip types nothing else can reach: hand height in glove (13), grip burial (16), index-finger curl (19), hand visibility (20), forearm exposure (21), and the "exposure from 2nd" reading of set position (8/9) | Nine of eleven scouted pitcher notes name a viewing angle, and six name second base. It is also the operational definition of a tip used throughout this project: a runner or base coach can see it and relay it. Thorpe's documented tip is explicitly "From 2nd". |
| 2 | **Open side** (third-base side for a RHP, first-base side for a LHP), roughly perpendicular to the pitcher's forward axis | Glove interior, hand-in-glove depth, wrist angle (15), glove tuck (3), arm window (22) | Centre field sees the glove edge-on with its open side pointing away, and sees every informative segment foreshortened down the camera axis. That is exactly why `glove_angle_at_lift` had to be retracted: 96% of its variance was the sign of the vertical component, because the horizontal leg of the arctangent is never observed from CF. A perpendicular view observes it directly. |
| 3 | **Closed side** (glove side) | The other half of the glove-flare / tuck / squeeze family; disambiguates "flared" from "turned" | Bubic's note is "from 2nd, **open and closed side**" — the scouts use both. Also the only way to tell a real cue from a per-camera appearance artifact by geometry rather than by statistics. |
| 4 | **High home / press-box behind the plate** | Posture, lean, sway, tempo, stride and the whole set-position family, with the pre-set period intact | Redundant with CF for content but far better for the pre-set window, and a useful cross-check that a cue is not camera-specific. |
| 5 | **Tight framing on the glove/hand only**, any position, if such a feed exists | The only realistic path to grip (17, 18), squeezes (7) and face (23) | These need pixels on the hand, and pixels come from framing, not from resolution alone (§1.4). |
| 6 | Centre field | Baseline and continuity with everything already measured | Include it — it costs nothing and it makes the new angles comparable to 2989 existing comparisons. |

**If only one alternate angle is obtainable, take the second-base look.** It is
worth six tip types with no modelling work at all, and it is where the ground
truth was written from.

## 1.2 Pitchers — 3 to 5, and one of them should be Drew Thorpe

1. **Drew Thorpe — first, if obtainable.** He is the only arm anywhere in this
   project with an externally documented tip: `HAND LOWER IN GLOVE`, "From 2nd,
   he is higher in glove on CH", "CH grip less buried in glove", with a whole
   MiLB deck page titled "Runner Perspective". That makes him the one case where
   the POC is **checkable**: we know the pitch type, the direction, and the
   vantage in advance, so we can pre-register the hypothesis and either reproduce
   it or not. A POC that reproduces a written-down tip is worth far more than one
   that discovers a novel effect, because a novel effect from a new data source
   has no way to distinguish itself from the Kelly artifact.
2. **One arm from the scouted set with a documented tip but a different cue
   family** — Bubic (2nd, open and closed side), Erceg or Speier (set position
   and exposure from 2nd), Burke ("more hand visible on CH from 2nd"). A second
   documented case tests whether a positive Thorpe result is a property of the
   angle or a property of Thorpe.
3. **One arm already deeply measured from CF** — Kelly (25 games, 1507 windows)
   or Webb. This is the paired-angle control: the same pitches, two cameras. It
   is the only way to say "this cue is visible from 2nd and invisible from CF"
   rather than "this cue appears in this new dataset".
4. **One arm with no documented tip, chosen before any analysis.** The negative
   control. If everything produces a hit, including this one, the finding is the
   pipeline and not the pitcher.
5. (Optional) **One left-hander.** Handedness folding is CF-specific and will be
   removed for side views; a LHP is the cheapest test that the generalisation is
   right.

Order matters more than count: Thorpe alone, done properly, is a decisive test.
Five arms done shallowly is not.

## 1.3 How much per pitcher

Derived from the same arithmetic as `quota_select.py`, which is fixed and should
not be renegotiated to fit whatever film happens to exist.

The unit is a **cell** = (pitch type × delivery × angle). Requirements per cell:

- **10 usable windows per half**, 20 per cell. A 10-pitch cell splits 5/5 and is
  untestable by construction.
- **≥4 distinct outings per cell**, so each side of the game-level split stands
  on at least two games. Kelly's flare effect looked real at 8 games because two
  games can carry a result.
- Window yield on Savant CF was 0.63–0.70. Continuous club film should do better
  because the two big loss channels — clip starting after the set, and the render
  cutting the lead-in — disappear. Budget **0.80** and verify on the first
  outing; if it comes in below 0.70, the shortfall is an ingestion bug, not
  natural loss.

That gives, per pitcher per angle:

| | Pitches per pitch type | Total (4–5 types) | Outings |
|---|---|---|---|
| **Minimum for a decisive test** | 25 (→ ~20 usable, 10/half) | 100–125 | **4** |
| **Comfortable** | 40 | 160–200 | 6 |
| **Diminishing returns beyond** | 60 | 240–300 | **8–10** |

In practice the clean ask is simpler: **4–6 complete starts per pitcher, every
camera, uncut.** A start is 80–100 pitches, so 4–6 starts delivers every cell at
once, including the rare pitch types and both delivery strata, with the outing
diversity built in. Asking for "25 changeups" invites a hand-picked subset,
which is the one thing that would poison the sample.

**What the volume does and does not buy.** At 10 per half a one-sided test at
80% power detects an effect of about g = 0.9 — a large, obvious tip, which is
what a documented scouted cue should be. Detecting a moderate g = 0.5 needs ~50
per half, i.e. 10–12 starts. And the *precision* gate is hungrier than the
difference test: distinguishing a 0.75 precision from a 0.60 with any confidence
needs on the order of 100 firings, which is why 8–10 starts is the point where
more film stops changing conclusions rather than the point where the test
becomes possible.

## 1.4 Technical requirements

**Continuous, not pre-cut.** This is the whole point. If the film has been cut
into per-pitch clips by someone else, we inherit their cut point, which is the
exact defect being escaped: Savant's fixed ~7 s render begins **after** the
pitcher has settled. If pre-cut clips are the only option, each clip must start
**≥5 s before first movement** and run to ≥1 s after release. Continuous
half-inning or full-outing files are strictly better and easier for everyone.

**The pre-set period must be included.** Non-negotiable. The window design needs
1.5 s of lead-in before the set (90 frames at 60 fps); the sway family sits at
32% coverage today purely because 92 of 381 tracks have fewer than 8 frames
before the set. Continuous footage makes this free.

**Frame rate: 60 fps minimum, 120 fps preferred** for the tight/hand angle. 60
is enough for position, posture and tempo. Taps and squeezes are 0.1–0.2 s
events and 60 fps gives 6–12 samples of one; that is why the PitchCom cue was
retired at a noise-to-signal of 1.9. Anything at 30 fps is usable but halves
every temporal margin — flag it, because the window constants are per-clip
rate-inferred and 30 fps footage will need its own threshold derivation.

**Resolution — and the thing most people get wrong about it.** Resolution alone
does less than framing. A hand is ~9 cm on a 190 cm body, so the hand box is
roughly 5% of the pitcher's height in pixels whatever the sensor. Today: 720p
CF, pitcher spans ~700 px, hand box 31–58 px. A 4K *wide* tactical view gets the
hand to perhaps 70–110 px — better, roughly 2×. Getting the hand to the 150+ px
where hand-versus-glove boundary becomes a structured measurement requires the
**pitcher to fill a large fraction of the frame**, i.e. a zoomed camera, not
just a bigger sensor. So:

- 1080p60 is the floor for any angle.
- **4K where available**, especially the second-base and open-side looks.
- One **tightly framed** feed (pitcher filling ≥half the frame height) is worth
  more for the glove-interior questions than three wide 4K angles.
- **No re-encode, no letterboxing, no reframing.** Original bitrate,
  original crop. H.264/H.265 mp4 or mov is fine. Aggressive compression destroys
  exactly the low-contrast glove-interior detail at issue.
- **Fixed zoom and fixed position, or logged if not.** An operator zooming
  mid-outing changes the pixels-per-metre scale, which is what the
  torso-normalisation exists to absorb — but torso length itself changes with
  lean, so a second scale reference is needed (below). Auto-tracking robotic
  cameras are the worst case: they break both the scale and the subject-selection
  ROI. If a feed is operator-panned, say so.

**Timing and sync.** In order of preference:

1. **Embedded timecode** on every camera, genlocked or at least clock-synced.
   This is the whole problem solved.
2. **A shared visible sync event** at the start of each file — a clapper, a
   strobe, a scoreboard clock visible in frame, anything simultaneously visible
   in two cameras.
3. **Nothing.** Recoverable, because the release is a sharp event visible from
   every angle, so pitches can be aligned per-pitch on release rather than
   globally. This works but costs accuracy and engineering time, and a global
   clock removes a whole class of failure. Ask for timecode.

**Calibration reference.** Cheap and high value:

- Any frame per camera per game showing the **pitching rubber (24 × 6 in)**,
  the **plate (17 in)** or a **measured pole placed on the mound pre-game**.
  Ten seconds of pre-game footage per camera is enough.
- A note of the camera's approximate position and height.
- Do this once per camera per park. It converts torso-normalised units into real
  distances and lets a cue measured from 2B be compared with the same cue from
  CF instead of being a separate incomparable quantity.

**Metadata, per pitch — required, not nice to have.** Without this the film is
unusable, and this is the single most likely cause of an uninteresting POC
failure. One CSV per outing:

`game_id, game_date, pitcher_id, pitcher_name, pitcher_throws, outing_pitch_index, inning, top_bot, batter_id, batter_side, balls, strikes, outs, on_1b, on_2b, on_3b, pitch_type, release_speed, result, timecode_or_seconds_from_file_start`

Notes on three of those:

- **`pitch_type` must be the club's own truth**, from its tracking system — not a
  broadcast overlay, and not read off the video. The existing fetch path is
  explicit about ignoring Savant's overlay for exactly this reason.
- **Base state is required**, because delivery stratification and the
  runner-on-second cells key on it. It is stated factually by the feed; the
  delivery itself is read from the tracked window afterwards, never inferred.
- **A time reference per pitch** — even "seconds from file start", even
  approximate to ±3 s — turns segmentation from a detection problem into a
  verification problem and removes the pickoff/warm-up contamination risk
  entirely. This is the highest-value single field in the file.

Also per camera, once: `camera_id, position description, resolution, fps, fixed
or operated, codec, timecode present y/n, calibration frame filename`.

## 1.5 What makes the POC decisive rather than suggestive

Pre-registered before any film is processed, and written down where it cannot be
edited afterwards:

**Primary hypothesis, one test.** Thorpe, second-base angle, changeup versus
fastball, hand height inside the glove, **directional**: hand sits *higher /
less buried* on the changeup. One test, one-sided, no FDR dilution. Everything
else in the run is secondary and reported as exploratory.

Decisive requires **all** of:

1. Effect in the pre-registered direction, on the pre-registered cue and angle.
2. Sign holds across a **disjoint-outing** holdout, with ≥10 per half.
3. Separation above the **per-camera** noise floor, re-measured on that camera
   (§7) — not the CF 0.05-torso figure carried over.
4. **Precision ≥ 0.75 when the rule fires**, with accuracy above the base rate.
   Rodríguez's stance-width survivor demonstrates why: pairing physical separation
   with predictive lift ensures high-precision signals provide decisive in-game leverage.
5. **Control region reproduces < 30%** of the effect. On CF, 101% of the leading
   grip effect was reproduced by a hand-free torso crop. This test must be run
   again on every new angle, every time.
6. **Not reproduced by the CF camera on the same pitches.** This is what the
   paired-angle arm is for, and it is what converts "we found something in new
   data" into "this cue is visible from second base and invisible from centre
   field", which is the actual product claim.
7. For any appearance-based descriptor, **sign consistent across two arms**.
   `mean_intensity` looked like the best result in the project until it reversed
   between Thorpe and Webb, which is what uniform, glove colour and park lighting
   do.

Suggestive-only, and should be labelled as such: any hit found by scanning many
cues across many angles; any effect from a single outing; any effect on a cell
below 10 per half; any effect whose control fraction was not measured.

---

# Part 2 — Ingestion architecture

Everything currently built assumes: one pitch per clip, pre-cut, single fixed
camera, keyed on Statcast `playId`, and thresholds tuned on 720p CF at 60 fps.
Continuous multi-angle club film breaks all four. The new keying is:

```
pitch_uid = (game_id, pitcher_id, outing_pitch_index)     # replaces play_id
observation = (pitch_uid, camera_id)                      # one tracked view
```

Features become per-observation; every existing gate operates per-observation and
per-camera. `play_id` remains valid as an alias when Statcast coverage exists.

## 2.1 Pitch event detection in continuous video — the core new component

This is genuinely new. Design it as **proposal → refinement → reconciliation**,
and make the last stage fail closed.

**Stage 1, proposal.** Cheap pass over the whole file: pose or motion energy
inside the pitcher ROI (from the camera profile, §2.3), find sustained-motion
onsets, apply a refractory period (no two deliveries within ~8 s), emit candidate
delivery times. Deliberately over-generates.

**Stage 2, refinement.** For each candidate, cut a generous ±12 s span and run
the **existing** logic unchanged: track, then `window.py` locates the set, hand
break, peak leg lift and delivery onset from the tracked columns and infers fps
per clip. A candidate that yields no coherent delivery structure is dropped. This
is the important design point — segmentation does not need to be precise, because
the anchor detection that already exists is what actually places the window.

**Stage 3, reconciliation against metadata, and this is the guard.** The outing
CSV says how many pitches there were and (ideally) roughly when. Then:

- Detected count must equal metadata count. A mismatch **raises**; it is not
  reconciled by taking the best N. Same discipline as the join that now raises
  when two tables share fewer than half their keys.
- With a per-pitch time reference, matching is a nearest-neighbour assignment and
  the detector only has to get within a few seconds.
- **Pickoffs, step-offs, warm-ups and between-inning throws are the specific
  hazard**, and pickoffs are worst because they occur precisely in the
  runner-on-second situations the cells care about. Metadata matching removes
  them; without metadata they must be classified, which is real extra work and a
  real extra error source. This alone justifies asking for the time field.

Expect to write ~600–900 lines plus tests, including synthetic-recovery tests in
the style of the trajectory audit: plant known deliveries in a synthetic file and
require they be found, require a planted pickoff to be rejected, require a
mid-file dropout to produce a refusal rather than a shifted assignment.

## 2.2 Multi-angle association and sync

- **With timecode:** trivial. Convert each camera's file-relative time to
  absolute, associate observations to `pitch_uid` by the reference camera's
  match, done.
- **Without timecode:** derive a per-file offset from a shared sync event, then
  refine **per pitch on the release frame**, which is sharp and mutually visible
  from every angle. Store the per-pitch residual offset; a drifting residual
  means a frame-rate or dropped-frame problem and should surface as a warning
  rather than be absorbed.
- Association is stored explicitly (`pitch_uid → {camera_id: (file, frame_start,
  frame_end, sync_confidence)}`), never re-derived at analysis time, and carries
  into the snapshot fingerprint so a result records which association it rested
  on.
- **Frame-accurate sync is not required for most cues.** Nearly every cue is a
  scalar at an anchor the tracker finds independently in each view; cross-camera
  agreement is checked at the level of "same pitch", not "same frame". Only
  genuinely cross-camera measurements would need frame accuracy, and none are
  planned for the POC. Worth stating, because sync anxiety is the most common
  reason multi-camera projects stall.

## 2.3 Per-camera calibration and subject selection

**This is where the CF-specific code actually lives**, and it is smaller than it
looks — one function.

`track_pitcher.pitcher_score` hard-codes CF-view geometry: normalised torso
extent 0.05–0.22, hip_y band 0.20–0.80, and a tiebreak preferring the pose
nearest frame centre because "the catcher and hitter sit off-centre and lower in
the CF framing". None of that is true from second base or from the open side.
The catcher rule (lowest hips among non-pitcher poses) is likewise CF-specific.

Replace with a **camera profile** per (park, camera, season):

```
camera_id, angle_class, pitcher_roi, torso_px_range, expected_facing,
scale_reference (rubber width in px), fps, resolution, zoom_fixed,
subject_correct_rate, noise_floor_torso, jitter_per_frame
```

Two of those fields are the ones that must be *measured*, not declared:

- **`subject_correct_rate`** — hand-check ~50 frames per camera that the tracked
  body is the pitcher. The catcher family produced 106 published assertions off
  the wrong body while having the *lowest* noise-to-signal in the whole system
  (0.02–0.04), because the pitcher is a large, well-lit, reliably-detected
  subject. A statistical gate cannot catch a subject error; only looking can.
- **`noise_floor_torso` and `jitter_per_frame`** — re-run
  `landmark_noise_probe.py` per camera over the set interval, where the pitcher
  is still by construction. **Every threshold in the system is calibrated to
  720p CF at 60 fps**: the 0.05-torso visibility floor, `MIN_ANGLE_SEGMENT =
  0.28` (derived as 0.05/tan 10°), `QUIET_SPEED = 0.020`, `BREAK_RADIUS =
  0.055`. Carrying those onto a 4K second-base feed unchanged would be the same
  category of error as the 30-versus-60 fps units bug. They must be re-derived
  per camera and the placement statistics re-validated, as was done when the
  boundary was first set.

**One primitives change, and it is an upside.** Handedness folding and the
"fold for handedness" step in the glove-angle family exist because CF sees
everything down the forward axis; folding costs the open-versus-closed side,
"which was the scouting content of the shoulder cue in the first place". From a
side or second-base view, **do not fold** — direction is the signal, and the
retracted `glove_angle_at_lift` becomes a genuinely measurable quantity rather
than one bit wearing a degrees label.

## 2.4 Pitch labelling

Without `playId` there is no Statcast join, so pitch type, base state and batter
side come from the club CSV in §1.4 and nowhere else. Requirements:

- Labels are ingested into the same `features.csv` / `primitives.csv` shape, so
  `spot_diff`, the strata, the holdout and the gates are untouched.
- **Never read a label off the video**, including any burned-in overlay. The
  existing fetch path already refuses this.
- A row missing `pitch_type` or base state is **dropped**, not imputed. Delivery
  is still read from the tracked window, never from the runner state — the
  inference is known to be wrong often enough to matter, and `delivery_type`
  silently marking a pitch "windup" whenever set detection failed is what
  produced the Webb cross-stratum confusion.
- Manual entry is acceptable for a POC (100–500 rows per pitcher is a couple of
  hours) but it must be entered from the club's pitch log, not from watching the
  film, or the labels inherit whatever a human thinks a changeup looks like —
  which is circular with the thing being tested.

## 2.5 What transfers unchanged, and what does not

**Transfers unchanged — this is the asset.** All of it is angle-agnostic,
operates on the tracked table rather than on pixels, and is already
camera-tagged:

- `window.py` — the whole actionable-window boundary: coming set → set → hand
  break → peak leg lift, with per-clip fps inference and seconds-declared
  durations.
- The 20-cue audited vocabulary and the 10 trajectory features, in
  torso-normalised units, with `PRIMITIVE_STATUS` and the validated /
  under-covered / resolution-limited classification.
- Delivery stratification, situation tags, the cell design and quota arithmetic.
- **Game-level (here outing-level) holdout**, BH-FDR, and the permutation null
  for any dispersion-style statistic — never a coin.
- **The precision-and-fire gate with base rate and lift**, separate from the
  difference test. The single most valuable component in the system: it is what
  rejected the strongest replicating difference ever produced.
- `provenance.RETRACTED_CUES`, the NaN discipline (no fabricated zeros, no
  silent fallbacks, `cheek_source`-style "why is this blank" columns), and the
  `snapshot.py` fingerprint / `assert_quiescent` / `mismatches` guard. All of
  these become *more* important with a heterogeneous multi-camera corpus, not
  less.
- The measurement-audit practice itself: name the physical quantity, verify the
  feature responds to it and not to a proxy, confirm it clears the noise floor
  for that body part. Six failure modes were found this way and all six would
  recur in new film.

**Does not transfer:**

- `pitcher_score` and the catcher rule in `track_pitcher.py` — CF geometry.
- `playId` keying and `fetch_savant.py` — replaced by `pitch_uid` and file
  ingestion.
- The one-pitch-per-clip assumption throughout the run layout (`clips/<play_id>.mp4`,
  `tracks/<play_id>_tracks.csv`).
- Every numeric threshold tuned on 720p CF 60 fps (§2.3).
- Handedness folding, which should be *removed* for side views.
- `MAX_TRACK_FRAMES = 240` and `PRESET_LOOKBACK = 45` — both exist to fit a
  fixed render and should be re-derived once lead-in is actually available.
- **One statistical consequence, easy to miss:** adding three angles roughly
  triples the comparison count, which raises the FDR bar for everything. The
  answer is the pre-registered primary hypothesis in §1.5, not a quiet loosening
  of q.

---

# Part 3 — Honest risk assessment

## 3.1 What genuinely resolves, and what might not

**Resolves outright:**

- **Pre-set coverage.** Continuous film contains the lead-in by construction.
  The sway family goes from 32% coverage to near-full, and the cues measured on
  0–25 frames of lead-in — reported as underpowered by coverage rather than as
  tested negatives — become actually testable. This is the cleanest win and it
  needs no new modelling at all.
- **Sightline, 6 tip types.** A second-base camera *is* the vantage the scouting
  notes are written from. Nothing about it is a modelling question.
- **Direction of angular cues.** The retracted glove angle becomes measurable
  from a perpendicular view, because the horizontal leg of the arctangent is
  finally observed.

**Probably resolves, with a caveat that must be tested rather than assumed:**

- **Hand-in-glove depth and grip burial (types 13, 16, 3).** The geometry
  genuinely changes: the glove's open side faces a second-base camera, so this
  becomes a foreground measurement instead of a 35 px crop down the camera axis,
  and pixels increase with tighter framing. But the CF grip probe failed for two
  reasons and only one of them was pixel count. The other was that the hand
  region's between-type variation was dominated by **arm-specific appearance**
  and by content shared with a **grip-free control crop** — a property of the
  pixels, not of how they were summarised. Better geometry plausibly fixes that;
  it is not guaranteed to. Hence requirements 5, 6 and 7 in §1.5. And the cheap
  human check still applies: if a person cannot consistently rank "how buried"
  from the new crops, twice, with agreement, no model trained on their labels
  will either. Run that before building anything.

**Probably does not resolve:**

- **PitchCom taps.** Needs the jitter below 0.060 torso/frame against 0.116
  today. That is a factor of two in pixel scale *plus* a higher frame rate,
  achievable only on a dedicated tight feed. Do not promise it.
- **Facial movement.** An 11 px mouth needs roughly an order of magnitude more
  pixels on the head. Only a dedicated tight face shot does that, and clubs
  rarely have one. Leave it retracted.
- **Index-finger curl (19).** A 4.7–5.1 px span today. Even 5× pixel scale puts
  it at ~25 px, which is marginal for finger pose. Treat as out of scope.
- **Contextualizing rare-pitch contrasts with base rates.** When evaluating rare pitches (e.g. curveballs at 14% mix), directional likelihood ratios and inverse indicators provide the actionable mechanism for advance scouting pitch elimination.

## 3.2 The per-pitch caveat, and why the user's framing may dissolve it

The recorded risk was: alternate-angle footage is not continuously available for
every pitch the way Savant CF is, so even on success coverage would be a
fraction of an arm's pitches — supporting scouting reports, not a live board.

**"Upload all your video before this game" largely sidesteps that, and the
reason is worth being precise about.** Split it:

- **For the club's own pitchers, on its own film: complete.** A club has every
  pitch of its own home games from its own installed cameras. Self-scouting —
  "does my starter tip?" — is fully per-pitch, and it is arguably the more
  sellable product anyway, because a tip you own is actionable immediately and
  requires no opponent cooperation.
- **For an opponent's starter: complete for the games played against you**, from
  your own installed cameras, which for a division opponent is 6–13 starts a
  season. That is more than the 4–6 needed, and it is exactly the pre-game
  workflow the user describes.
- **Genuinely incomplete only for arms you have never faced** at a park where
  you have no cameras. There the honest answer stays "CF only", which is the
  documented negative.

So the caveat downgrades from a structural limit to a **coverage-by-opponent**
statement. What remains true: at prediction time the pipeline needs the *same*
angle it was fitted on. A cue found from your second-base camera in your park
predicts pitches seen from that camera. Whether it transfers to a different park
with a differently-placed camera is an empirical question the POC should test
directly — fit on one park, evaluate on another — and if it does not transfer, the
product is per-park rather than per-pitcher, which is a materially weaker but
still real proposition.

## 3.3 Ways the POC fails for uninteresting reasons

Listed so they get prevented in the upload spec instead of discovered afterwards.
Each maps to a §1.4 requirement.

| Failure | Prevention |
|---|---|
| **No per-pitch pitch-type truth.** Fatal — every contrast needs it. | Required field; club tracking system only; refuse the engagement without it. |
| **No time reference per pitch.** Segmentation becomes a detection problem, pickoffs contaminate the runner-on cells. | Ask for `timecode_or_seconds_from_file_start`, ±3 s is enough. |
| **Film pre-cut, and cut after the set.** Reproduces the exact defect being escaped. | Continuous files; if cut, ≥5 s pre-movement lead-in. |
| **Transcoded / reframed / letterboxed for distribution.** Destroys glove-interior detail and breaks the ROI. | Original files, original crop, original bitrate. |
| **Robotic or operator-panned camera with variable zoom.** Breaks scale and subject selection. | Prefer fixed; log if operated; per-game calibration frame. |
| **30 fps only.** Halves every temporal margin; taps and squeezes gone. | 60 fps minimum, and flag any 30 fps feed so its thresholds get derived separately. |
| **All from one or two outings.** No outing-level holdout; this is precisely how the Kelly artifact looked real. | ≥4 outings per cell, hard requirement, refuse to report otherwise. |
| **Only one angle, and it is centre field.** Nothing new is tested. | Second base is the minimum viable alternate angle. |
| **Hand-picked "good example" clips.** Selection makes any result unfalsifiable. | Ask for complete outings, never for specific pitches. |
| **No sync and no shared event.** Recoverable per-pitch on release, but costs time and adds an error term. | Timecode, or a clapper/strobe at file start. |
| **CF-tuned thresholds carried over silently.** Would produce plausible numbers on wrong window placement. | Per-camera noise-floor derivation and placement re-validation before any discovery run. |
| **Wrong subject tracked on a new angle.** The single most expensive failure this project has had, twice. | 50-frame hand-check per camera, recorded as `subject_correct_rate`. |
| **Cue scan across angles dilutes FDR.** Everything fails, including a real tip. | Pre-registered primary hypothesis; angles secondary and labelled exploratory. |

---

# Part 4 — Effort estimate

One engineer, sequential. "POC" means 3–5 pitchers, a handful of cameras, film
arriving as files with a metadata CSV.

| Component | POC | Notes |
|---|---|---|
| Pitch event detection + segmentation | **1.5–2.5 weeks** | The one genuinely new component. Includes synthetic-recovery tests and the fail-closed metadata reconciliation. Halve it if per-pitch time references are supplied. |
| Camera profiles + generalised subject selection | **1–1.5 weeks** | Replacing one CF-specific function, plus the 50-frame check per camera. |
| Per-camera threshold re-derivation and window placement re-validation | **1 week** | Not optional. Reuses `landmark_noise_probe.py` and the existing placement statistics. |
| Multi-angle association and sync | **3 days** with timecode, **1.5 weeks** without | Almost entirely a function of what the club supplies. |
| Label ingestion (`pitch_uid`, club CSV → features) | **3–5 days** | Mostly plumbing; the schema and the raise-on-bad-join discipline already exist. |
| Primitives generalisation (drop handedness folding, side-view open/closed cues) | **1 week** | Small code change, needs its own validation pass. |
| Run, analysis, write-up | **1 week** | Pipeline unchanged; this is compute and reading. |
| **Total** | **6–8 weeks** | Compute cost is negligible — a few hundred outings of tracking. |

Sequenced so the cheap decisive things come first: with timecode and per-pitch
times on **Thorpe from second base only**, a single pre-registered test is
reachable in **3–4 weeks**, before any of the generalisation work. That is the
version to do first.

**A productised "upload your video" service is a different animal — 6–9 months
beyond the POC**, and the extra work is almost all robustness rather than
method: auto-calibration for cameras nobody has profiled, ingestion for
arbitrary containers and unknown frame rates, drift and dropped-frame handling,
automatic pickoff/warm-up classification when metadata is absent, a QC dashboard
that surfaces subject-selection and window-placement failures per upload (because
nobody will run `landmark_noise_probe.py` by hand), throughput and storage,
per-tenant isolation and provenance, and versioned re-analysis so a claim can be
reproduced against the film it was made from. The measurement core carries over
untouched; everything around it has to become unattended, and every failure mode
in §3.3 has to become an automatic refusal rather than a note in a document.

---

# Note on the NL West run

It continues untouched and should. It is cheap, it completes the documented
centre-field negative across a full division, and that negative is the argument
for this pivot: better film is required because the current film has been
measured and shown insufficient, not because a better camera sounds nice. The
run is now the **baseline**, not the product.
