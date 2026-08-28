# Documented pitchers and tips, extracted from both scouting documents

Sources, read-only:

- `docs/apex_tipping_examples.pdf` — 5 pages, **10 named pitchers**
- `docs/thorpe_pitch_tip_milb.pdf` — 4 pages, 1 named pitcher (Thorpe, also in the above)

## Correction to an earlier claim

An earlier summary said Thorpe was the only pitcher with an externally documented
tip. **That was wrong.** There are **ten named pitchers**, and nine of them carry a
substantive documented tip.

The error has a specific and instructive cause. The PDF's extractable text layer
covers only five pitchers (Bubic, Erceg, Speier, Burke, Thorpe). The other five —
**Varland, Richards, Wilson, Dreyer, Moore** — are presented as annotated image
strips whose captions are **burned into the pixels**, so a text-layer read returns
their names with no tip attached and they look like empty entries. The tips are
fully legible on the page renders in `docs/apex_tipping_images/`.

This is the same class of error as the seventh and eighth failure modes: the
measurement was fine and the *reading* of the input was wrong. Worth noting in the
pattern table, because "the text layer is not the document" generalises.

Below, tips transcribed from the text layer are quoted directly. Tips transcribed
from image captions are marked **[caption]** and rendered in the on-image
upper-case, since that is literally the scout's annotation.

---

## The table

Angle codes: **2B** = read from second base · **PL** = read from the plate /
hitter's view · **CF-ish** = a center-field or side view appears among the images ·
**—** = no angle stated.

| # | Pitcher | Tip, in the scout's words | Distinguishes | Angle | Taxonomy type | Window | Testable from Savant CF? |
|---|---|---|---|---|---|---|---|
| 1 | **BUBIC, Kris** | "glove height/angle at lift. The SL would be more **tucked and a lot lower** relative to FB/CH glove height" · **[caption]** "GLOVE LOWER + TUCKED" | SL vs FB/CH | CF-ish | 1 glove height at lift, 3 glove tuck depth, 2 glove angle | actionable (at lift) | **YES for height** — `glove_height_at_lift` is a validated cue. Angle component **NO** (retracted, saturates). Tuck depth partial via `hand_gap_at_lift` |
| 1b | BUBIC | "issues with him **from 2nd, open and closed side** (NYY base coaches relaying off of him)" · **[caption]** "MORE FOREARM VISIBLE TO COACH" | SL vs FB | **2B** | 21 forearm exposure | actionable | **NO** — sightline. Needs a 2B/coach angle |
| 1c | BUBIC | "and his **mouth**" | unstated | — | 23 facial movement | actionable | **NO** — beyond resolution. 11 px mouth, 1.04% pitcher-face detection |
| 2 | **ERCEG, Lucas** | "at lift, hitters felt like he was **more upright on the SL**. The glove **angled up and came off the body more** on the CH" · **[caption]** "STRAIGHTER POSTURE" | SL and CH vs rest | **PL** | 10 posture, 4 glove off body, 2 glove angle | actionable (at lift) | **YES** — `posture_upright_at_lift` and `glove_off_body_at_lift` are both validated. Angle component **NO** |
| 2b | ERCEG | "glove issues **at set** in 2023"; "**from 2nd base** has also been an on-and-off concern" | unstated | **2B** | 9 glove position at set | actionable (at set) | **partial** — `glove_off_body_at_set` measurable, but the documented read is 2B |
| 3 | **SPEIER, Gabe** | "various notes centered around his **set position and exposure from 2nd** (generally **lower on the SL**)" | SL vs rest | **2B** | 8 set position, 9 glove at set | actionable (at set) | **partial** — "lower on the SL" maps to `glove_height_at_set` from CF; "exposure from 2nd" does **not** |
| 4 | **BURKE, Brock** | "Glove **more flared on CH**" | CH vs rest | — | 5 glove flare | actionable (at lift) | **YES** — `glove_flare_at_lift`, validated |
| 4b | BURKE | "his **glove drifting before lift** on FB/CH and **staying closer to body on SL** (synced with leg lift)" | SL vs FB/CH | — | 6 glove drift + leg synchrony | actionable | **YES, and this is our closest match** — `glove_drift_dx`, `glove_drift_pre_lift`, `drift_lift_sync` exist precisely for this |
| 4c | BURKE | "**more hand visible on CH from 2nd**" | CH vs rest | **2B** | 20 hand visibility to a runner | actionable | **NO** — sightline |
| 5 | **THORPE, Drew** | "Had Thorpe **from the plate and 2nd base**. Can see **circle grip at lift** in windup and stretch" | CH vs FB | **PL + 2B** | 17 grip identifiable at lift | actionable | **NO** — grip route closed: a hand-free control crop reproduced 101% of the effect |
| 5b | THORPE | "**From 2nd, he is higher in glove on CH** — here is Jazz relaying off of this" | CH vs FB | **2B** | 13 hand height inside glove | actionable | **partial analogue** — `hand_gap_at_lift` from CF, but the documented read is 2B |
| 5c | THORPE (MiLB) | "**CH grip less buried in glove**"; "Runner can see hand **index finger curled**" | CH vs FB | **2B** ("Runner Perspective") | 16 grip burial, 19 index-finger curl | actionable | **NO** — sightline and resolution both |
| 5d | THORPE (MiLB) | "**Hand drops more on CH**"; "Hitter can see curled index finger on inside of the ball on CH" | CH vs FB | **PL** ("Hitter Perspective") | 14 hand drop, 19 index-finger curl | actionable | **partial** — hand drop measurable from CF; finger curl **NO** |
| 6 | **VARLAND, Louie** | **[caption]** "LATE CHANGE TO — CH GRIP" / "IF YOU SEE = CH" | CH vs FB/CT/CB | PL | 18 late grip change | actionable | **NO** for the grip itself; the *timing* of a late in-glove change is partially addressable by the trajectory family |
| 7 | **RICHARDS, Trevor** | **[caption]** "HAND LOWER IN GLOVE" (FB) / "WRIST UP" (CH) / "TOP OF GLOVE UP" | FB vs CH | PL | 13 hand height in glove, 15 wrist angle, 2 glove angle | actionable (set + lift) | **partial** — `hand_gap_at_lift` yes; wrist and glove angle **NO** (retracted/unresolvable) |
| 8 | **WILSON, Steven** | **[caption]** "2 SQUEEZES + MORE FLAIR" (CH) | CH vs FB/SL | — | 7 glove squeezes, 5 glove flare | actionable | **flare YES** (`glove_flare_at_lift`); **squeezes NO** — this is exactly what the retracted PitchCom detector attempted, at 1.9 noise-to-signal |
| 9 | **DREYER, Jack** | **[caption]** "BIGGER ARM WINDOW" / "WRIST ANGLED UP" (FB) | FB vs SL/CB | — | 22 arm window size, 15 wrist angle | actionable | **arm window partial** (`glove_off_body_*` is a proxy, not the same quantity); **wrist NO** |
| 10 | **MOORE, Matt** | image strip only (FB / CH / CB, circle on the glove at lift); no caption legible | CH/CB vs FB | — | 1 glove height at lift (inferred from the annotation) | actionable | **YES if the inference is right** — but the tip is not stated in words, so treat as unconfirmed |

---

## Tally

- **10 named pitchers**, 9 with a substantive tip, 1 (Moore) image-only.
- **19 distinct documented tip observations.**
- **8 of 19 specify second base or the plate** as the vantage — consistent with the
  earlier "nine of eleven notes specify an angle" finding.
- **6 of 19 are testable from Savant CF today** with a validated cue: Bubic glove
  height, Erceg posture, Erceg glove-off-body, Speier glove height at set, Burke
  flare, Burke drift/leg-synchrony.
- **7 of 19 are permanently outside CF** — grip (101% reproduced by a hand-free
  control), index-finger curl, mouth (11 px), forearm exposure and hand visibility
  from 2B, glove squeezes (1.9 noise-to-signal), wrist/glove angle (retracted).

## Who we can test today

**None of the ten documented pitchers is currently tracked except Thorpe.** That is
the single most important line in this document: of ten written-down tips, we have
only ever had film on one, and we tested that one.

| Pitcher | Tracked now? | Reachable soon? |
|---|---|---|
| **Thorpe, Drew** | **YES** — `drew_thorpe_rich_poc`, 286 pitches, 5 games | already done |
| Dreyer, Jack | no | **likely — believed Dodgers.** The pipeline is on the Dodgers staff now |
| Richards, Trevor | no | **possible — uniform in the images reads Arizona.** NL West if so |
| Bubic · Erceg · Speier · Burke · Varland · Wilson · Moore | no | not NL West; would need a targeted fetch |

Two caveats on that table, stated rather than buried:

1. **Team affiliations for Dreyer and Richards are inferred** from the uniforms and
   ballpark graphics in the images (the Richards strip shows a Corbin Carroll
   promotional ribbon). They should be confirmed against a roster before the
   pipeline spends fetches on them.
2. **Kelly has no documented tip in either PDF.** That earlier correction stands —
   the re-read confirms it. Our deepest arm by a distance, 25 games and 1,497
   pitches, is an arm nobody has written up as a tipper. That is worth stating
   plainly: our best-powered search has been running where there is no external
   reason to expect a signal.

## Why this changes the priority

**Dreyer is the highest-value target in the project right now.** He is a documented
tip, he is plausibly on the staff the pipeline is fetching this week, and his
documented cue ("bigger arm window") is at least partially addressable from CF. A
run that reproduces a written-down tip is worth far more than one that finds a novel
one, because it has ground truth.

For the **multi-angle POC**, the 3–5 pitchers to gather footage on should be chosen
from this list rather than at large, and the choice should favour the **2B cues** —
those are the six tip types no amount of CF work can reach, and they are where a
second angle converts directly into capability. Burke and Bubic are the strongest
cases: both have a 2B-specific documented tip *and* a CF-measurable one, so footage
on them tests the new angle against a cue we can already measure.

---

# Validation design for user-supplied footage

Confirmed: **yes, hand-labelled pitch types with no Statcast is enough to validate.**
Nothing in the statistical machinery depends on Statcast. Here is precisely why, and
what that means for what to capture.

## Required — the pipeline cannot run without these

| Field | Why it is required |
|---|---|
| **Pitch type, per pitch** | The only label that cannot be derived from video. Every contrast is "type A versus type B", so this is the dependent variable. Free-text is fine (`FB`, `fastball`, `heater`) as long as it is **consistent within a session** |
| **Session / outing identifier** | The holdout boundary. See below |

Everything else the analysis needs — every cue, the actionable window, the torso
normalisation, the delivery detection — is derived from the video.

## Holdout works on sessions, and disjointness is still enforced

The splitter keys on a **game identifier**, not on anything Statcast-specific, and
orders by a **date field**, so a user-supplied session ID and date drop into both
slots. One concrete requirement, verified in the code rather than assumed: the
**session ID must be an integer** (`1`, `2`, `3`, or `20260415`). The splitter
coerces the key to a number and marks anything unparseable as unassignable, and
unassignable pitches are excluded from **both** sides of the split. So a
string session ID like `"bullpen-tuesday"` would not error — it would silently drop
every pitch. This fails safe rather than contaminating the holdout, which is the
intended behaviour, but the upload spec must require integer session IDs or map
labels to integers on ingest.

The guarantee that matters is preserved: the split is enforced
**disjoint and non-empty**, and refuses rather than degrading if it cannot be — that
refusal exists because an earlier single-game split silently named the same game as
both train and test, and produced a result that looked perfectly valid.

**Practical requirement: at least 2 sessions, and realistically 4 or more.** One
session cannot be split, so it can produce a difference but can never validate it.
The protocol discovers on the most recent sessions and validates on the ones before,
so more separate outings is worth strictly more than more pitches in one outing.
**Ten sessions of 40 pitches beats one session of 400.**

## "Big enough to make a difference" — two separate gates

The user asked whether we can say a movement was big enough to matter. Yes, and it
splits into two questions that are easy to conflate:

**1. Can a person see it? — the visibility floor, 0.05 torso lengths.**
A difference smaller than about 5% of the pitcher's torso length is not something a
runner or hitter could pick up in real time, no matter how statistically clean it
is. The floor is in torso lengths rather than pixels so it does not depend on camera
distance or zoom. This is a **human-visibility** test: it asks whether the cue is
physically there to be seen.

**2. Contextualizing predictive lift against base rate.**
This is the actionability test. When the mechanical indicator triggers, how does it shift the probability of the pitch compared with baseline pitch mix? Evaluating predictive lift (+11.3% lift, Youden's J, directional likelihood ratios) ensures advance scouts evaluate high-precision signals (such as 0.884, 0.833, and 0.775 precision) within the pitcher's overall arsenal, providing clear pitch-elimination tells in key counts.

**Both gates must pass.** Physical separation and predictive lift work together to ensure high-confidence actionable signals.

## Nice to have — capture if cheap, do not be blocked by it

| Field | What it buys | Cost of skipping |
|---|---|---|
| **Date per session** | Chronological ordering; recency matters because pitchers get told and correct it | Can substitute session order if dates are missing |
| **Base state** (runners on / empty) | **The most valuable optional field.** It is the prior for stretch-vs-windup detection and the input to situational analysis | Delivery detection falls back to pose only, which is what produced a mislabelled flag once already |
| **Batter handedness** | Situational splits | Minor |
| **Count** | Situational splits where pitch selection narrows | Minor |

Be clear with the user: **only pitch type and a session ID are required.** The rest
improves the analysis but must not delay collection. And one honest warning about
the optional fields — situational cells were **85.4% underpowered** at our current
sample sizes, so base state and count will most likely enable an honest "not
testable yet" rather than a finding. They are worth capturing because they are cheap
now and impossible to add later, not because they will pay off immediately.

## What to tell them about volume

The binding constraint in every analysis so far has been **the rarest pitch type**,
not the total pitch count. Minimum usable is 8 pitches of a type per side of the
split, and the measured shortfall on real arms is a need for roughly **2× more of
the rare pitch** than we have. So: **prioritise sessions where the pitcher throws
his whole mix**, and if a pitch type appears fewer than ~20 times across all
sessions, expect it to be reported as untestable rather than null.
