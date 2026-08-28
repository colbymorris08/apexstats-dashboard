# Apex Preflight · Computer Vision Pitch Anticipation & Mechanical Variation Engine

[![MLB Advance Scouting](https://img.shields.io/badge/Domain-MLB%20Advance%20Scouting-0A192F.svg?style=flat-square)](#practical-scouting-applications)
[![Computer Vision](https://img.shields.io/badge/Vision%20Stack-YOLOv8%20%2B%20MediaPipe-00B4D8.svg?style=flat-square)](#computer-vision-architecture--methodology)
[![Actionable Window](https://img.shields.io/badge/Constraint-Strictly%20Pre--Release-10B981.svg?style=flat-square)](#actionable-delivery-window--information-barrier)
[![Validation](https://img.shields.io/badge/Statistical%20Gate-Youden%27s%20J%20%7C%20FDR%20q%3D0.10-F59E0B.svg?style=flat-square)](#statistical-validation-framework)
[![Deployment](https://img.shields.io/badge/Deployment-Vercel%20%2F%20Static%20Board-6366F1.svg?style=flat-square)](#local-setup--deployment-guide)

**Apex Preflight** is an automated computer vision "Spot the Difference" pitch anticipation and physical movement variation engine. Designed for Major League Baseball advance scouting and pitching development departments, Preflight ingests high-frame-rate game video, tracks 30+ anatomical and spatial landmarks across the pitcher and battery, and classifies physical mechanical discrepancies—such as glove set height, forearm exposure, torso tilt, hand depth, and delivery tempo—**strictly before the pitcher's hand break and ball release**.

---

## Table of Contents
1. [Platform Overview](#platform-overview)
2. [The 4-Step Operational Workflow](#the-4-step-operational-workflow)
3. [Computer Vision Architecture & Methodology](#computer-vision-architecture--methodology)
   - [Object Detection & Landmark Tracking](#object-detection--landmark-tracking)
   - [Actionable Delivery Window & Information Barrier](#actionable-delivery-window--information-barrier)
   - [15+ Mechanical Primitives & Invariant Normalization](#15-mechanical-primitives--invariant-normalization)
   - [Catcher Setup & Battery Tracking](#catcher-setup--battery-tracking)
4. [Broadcast Center Field (CF) Limits vs. Enterprise Club Expansion](#broadcast-center-field-cf-limits-vs-enterprise-club-expansion)
   - [The Three Physical Limits of Broadcast CF](#the-three-physical-limits-of-broadcast-cf)
   - [Enterprise 4K Multi-Angle Club Feeds](#enterprise-4k-multi-angle-club-feeds)
   - [Statistical Validation Framework](#statistical-validation-framework)
5. [Practical Scouting & Player Development Applications](#practical-scouting--player-development-applications)
   - [Advance Scouting Pitch Tipping Reports](#1-advance-scouting-pitch-tipping-reports)
   - [Bullpen Mechanical Consistency Audits](#2-bullpen-mechanical-consistency-audits)
   - [Catcher Target Placement & Battery Scouting](#3-catcher-target-placement--battery-scouting)
   - [Game-Planning Intelligence & In-Game Relays](#4-game-planning-intelligence--in-game-relays)
6. [Repository Structure](#repository-structure)
7. [Local Setup & Deployment Guide](#local-setup--deployment-guide)
   - [Prerequisites](#prerequisites)
   - [Static Dashboard Serving](#static-dashboard-serving)
   - [Running the Computer Vision Pipeline](#running-the-computer-vision-pipeline)
   - [Vercel Deployment](#vercel-deployment)

---

## Platform Overview

In professional baseball, a pitcher "tipping" their pitches or exhibiting systematic mechanical variations across pitch types confers an overwhelming advantage to opposing hitters. However, traditional advance scouting relies on manual video tagging, subjective human pattern recognition, and ad-hoc dugout observations—an expensive, low-throughput process vulnerable to cognitive bias and missed patterns.

```
+--------------------------------------------------------------------------------------------------+
|                                    APEX PREFLIGHT PLATFORM                                       |
+--------------------------------------------------------------------------------------------------+
|                                                                                                  |
|   +-----------------------+     +--------------------------+     +---------------------------+   |
|   |   Raw Video Ingest    | --> | Neural Vision Tracking   | --> | Delivery Window Clamping  |   |
|   |  - Broadcast CF (PoC) |     | - YOLOv8 (Mitt, Glove)   |     | - Settle into Set         |   |
|   |  - 4K Multi-Angle     |     | - MediaPipe Pose / Hands |     | - Leg Kick Anchor         |   |
|   +-----------------------+     +--------------------------+     | - Hand Break (Hard Cut)   |   |
|                                                                  +---------------------------+   |
|                                                                                |                 |
|                                                                                v                 |
|   +-----------------------+     +--------------------------+     +---------------------------+   |
|   | Advance Scouting UI   | <-- | Statistical Gate         | <-- | 15+ Mechanical Primitives |   |
|   | - Ranked Tip Board    |     | - Game-Stratified Split  |     | - Glove Elevation / Offset|   |
|   | - Pitcher Dossiers    |     | - Youden's J / FDR q=0.10|     | - Forearm Visibility/Tilt |   |
|   | - Battery Tendencies  |     | - Likelihood Ratios      |     | - Torso Lean & Tempo      |   |
|   +-----------------------+     +--------------------------+     +---------------------------+   |
|                                                                                                  |
+--------------------------------------------------------------------------------------------------+
```

Preflight converts video into structured, reproducible biomechanical time series. By executing automated pairwise hypothesis testing across pitch classifications within uniform delivery strata, Preflight surfaces actionable mechanical tells while filtering out camera artifacts, lighting noise, and chance variations.

---

## The 4-Step Operational Workflow

Preflight bridges automated computer vision algorithms with on-field baseball decision making through a structured, four-stage operational path:

```
+--------------------------------------------------------------------------------------------------+
|                                  THE 4-STEP OPERATIONAL WORKFLOW                                 |
+--------------------------------------------------------------------------------------------------+
|                                                                                                  |
|   [Step 1: The Model Finds Pattern]     --->     [Step 2: Analysts Confirm Tip]                  |
|   - High-throughput video ingest                 - Baseline pitch-mix contextualization          |
|   - 30+ anatomical landmarks tracked             - Permutation nulls & holdout validation        |
|   - Delivery strata physical ranking             - False discovery rate (FDR q=0.10) gating      |
|                                                                                                  |
|                                 |                                                                |
|                                 v                                                                |
|                                                                                                  |
|   [Step 4: Players Recognize on Field]  <---     [Step 3: Coaches Teach Recognition]             |
|   - Hitters eliminate pitch families             - Visual trigger identification drills          |
|   - Baserunners execute 2B relay cues            - Count-specific scouting card integration      |
|   - Sub-second pre-release anticipation          - Clear, actionable cues for dugout/hitters     |
|                                                                                                  |
+--------------------------------------------------------------------------------------------------+
```

### 1. Step 1: The Model Finds the Pattern
- **Automated Screening**: High-throughput YOLO object detection and MediaPipe topological landmark estimation process hundreds of pitches per arm across full seasons without manual video tagging.
- **Physical Feature Extraction**: Quantifies pitch-to-pitch mechanical variation across 15+ normalized pre-release delivery primitives (glove set height, forearm exposure, torso tilt, hand depth, and delivery tempo).
- **Strict Information Barrier**: Evaluates contrasts exclusively within uniform delivery strata (windup vs. stretch, runners on base, count categories) strictly before hand break ($t < t_{\text{hand\_break}}$).

### 2. Step 2: Analysts Confirm the Tip
- **Predictive Lift vs. Base Rate**: Quantitative analysts calculate true predictive lift over baseline pitch frequencies, verifying that high precision is not an artifact of heavy fastball or sinker usage.
- **Sample Stability & Permutation Nulls**: Tests cues across out-of-sample game splits ($k \ge 8$ starts) and phase-shuffled permutation nulls to eliminate optical noise and small-sample coincidences.
- **Multi-Angle Cross-Validation**: Cross-references candidate leads against private high-resolution 4K feeds (Tight CF, 3B coach dugout, 1B coach, High-Home) to verify physical observability.

### 3. Step 3: Coaches Teach How to Recognize the Tip
- **Instructional Translation**: Pitching coordinators and hitting coaches translate raw coordinate deltas (e.g., $+0.08$ torso lengths glove elevation) into intuitive, memorable visual recognition keys (e.g., *"Glove tucked at chin vs. belt buckle"*).
- **Count-Specific Game Plans**: Establishes actionable deployment rules—identifying high-leverage situations (2-strike counts, runners in scoring position) where pitch elimination yields maximum offensive expected value.
- **Dugout & Video Preparation**: Coaches integrate side-by-side synchronized video clips into pre-series advance meetings and dugout tablet packets.

### 4. Step 4: Players Recognize the Tip on the Field
- **Hitter In-Box Execution**: Batters identify the tell during the pitcher's set and early leg kick, eliminating entire velocity bands (e.g., taking breaking pitches or sitting dead-red on 4-seamers).
- **Baserunner & Dugout Relays**: Runners on second base and base coaches observe unobstructed angle-specific cues (such as glove pocket flaring or posture lean) and relay pitch-family reads to the hitter in real time.
- **On-Field Performance Gains**: Maximizes plate discipline, increases walk rates (BB%), boosts on-base percentage (OBP) and slugging percentage (SLG), and dramatically cuts strikeout rates (K%).

---

## Computer Vision Architecture & Methodology

### Object Detection & Landmark Tracking
Preflight deploys a two-stage computer vision architecture combining real-time convolutional object detection with high-density topological landmark estimation:

1. **Object Detection (`YOLOv8`)**:
   - Custom-trained lightweight YOLOv8 models (`parts_yolov8n.pt`, `parts_glovehand.pt`, `parts_gear.pt`) locate key equipment and regions of interest (pitcher glove, bare hand, catcher mitt, home plate, batter box boundaries) in each frame.
   - Initial bounding-box proposals localize tracking regions, preventing identity drift and multi-body confusion in crowded broadcast views.
2. **Landmark Estimation (`MediaPipe Pose Landmarker Heavy` & `MediaPipe Face`)**:
   - High-density 33-point 3D anatomical pose tracking extracts pitcher skeletal joints: shoulders, elbows, wrists, hips, knees, ankles, and face landmarks.
   - Temporal landmark tracking produces frame-by-frame coordinate trajectories $(x_t, y_t, z_t, v_t)$ paired with per-joint visibility/confidence scores $v_t$.

```
[Raw Frame] ---> [YOLOv8 Object Detection] ---> [Bounding Box Proposals]
                                                         |
                                                         v
                                           [MediaPipe Heavy Landmarker]
                                                         |
                                                         v
                                  [Sub-Pixel 33-Point Skeletal Trajectories]
```

### Actionable Delivery Window & Information Barrier
A mechanical difference is only valuable if an advance scout, base coach, or batter can observe and react to it **prior to pitch execution**. 

Preflight enforces an uncompromising **information barrier**:

$$\text{Actionable Window} = [t_{\text{coming\_set}}, \, t_{\text{hand\_break}})$$

- **Window Initiation ($t_{\text{coming\_set}}$)**: The pitcher steps on the rubber, initiates PitchCom cadence, and comes to a complete static pause (the set).
- **Primary Reference Anchor ($t_{\text{leg\_lift}}$)**: Peak knee elevation during delivery initiation.
- **Strict Window Termination ($t_{\text{hand\_break}}$)**: The exact frame the pitcher's bare throwing hand separates from the glove pocket.
- **Zero Downstream Leakage**: All frames at or after hand break, arm cocking, acceleration, release point, and post-release ball flight are **structurally excised** before feature generation. Pitch-type graphics, broadcast radar readings, and umpire strike calls never enter the feature extractor.

```
  PRE-PITCH SETTLING              STATIC SET POSITION              HAND BREAK (HARD CUTOFF)
+------------------------+------------------------------------+--------------------------------+
| PitchCom & Rubber Step |  Glove Height / Posture / Lean     | Hand Leaves Glove -> CUTOFF    |
| (Pre-Set Trajectory)   |  (At-Lift & Peak Knee Anchor)      | (Zero Post-Release Contam.)    |
+------------------------+------------------------------------+--------------------------------+
|<-------------------- ELIGIBLE FEATURE WINDOW --------------------->| X (Excluded from Features)
```

### 15+ Mechanical Primitives & Invariant Normalization
To make spatial measurements invariant to camera zoom, broadcast focal length, and pitcher physical stature, all Euclidean pixel distances are normalized by that pitch's instantaneous **torso length** (distance between shoulder midpoint and hip midpoint):

$$\text{Normalized Distance} = \frac{\|\mathbf{p}_A - \mathbf{p}_B\|_2}{\|\mathbf{p}_{\text{shoulder\_mid}} - \mathbf{p}_{\text{hip\_mid}}\|_2}$$

Angles are measured in invariant 2D/3D angular degrees.

```
       [SHOULDER MIDPOINT]
              |
              | <---- Torso Length L_torso (Standard Normalization Unit)
              |
         [HIP MIDPOINT]
```

#### Core Mechanical Primitives Tracked:
| Primitive Feature | Anchor Point | Units | Description & Biomechanical Tell |
|:---|:---|:---|:---|
| `glove_y_at_lift` | Peak Leg Lift | Torso Lengths | Vertical height of glove relative to mid-torso (e.g., high on FF, low on CH). |
| `glove_x_at_lift` | Peak Leg Lift | Torso Lengths | Lateral glove displacement off torso centerline (tucked vs. disconnected). |
| `glove_dist_at_lift` | Peak Leg Lift | Torso Lengths | Absolute Euclidean offset of glove from torso midpoint. |
| `glove_angle_at_lift` | Peak Leg Lift | Degrees | Orientation angle of the glove axis relative to the vertical trunk. |
| `glove_flare_at_lift` | Peak Leg Lift | Degrees | Forearm-to-glove pocket opening angle (detects grip flaring / wrist cocking). |
| `glove_y_at_set` | Static Set Pause | Torso Lengths | Static baseline glove elevation before leg lift begins. |
| `glove_x_at_set` | Static Set Pause | Torso Lengths | Static baseline horizontal glove position during the set. |
| `glove_to_belt_at_set` | Static Set Pause | Torso Lengths | Distance from glove center to belt / hip midpoint. |
| `forearm_angle_at_lift` | Peak Leg Lift | Degrees | Angle of throwing forearm (measures elbow drop / arm path drift). |
| `elbow_height_at_lift` | Peak Leg Lift | Torso Lengths | Vertical elevation of throwing-side elbow at delivery initiation. |
| `torso_lean_at_set` | Static Set Pause | Degrees | Lateral spinal tilt / posture angle relative to the vertical plumb line. |
| `torso_lean_at_lift` | Peak Leg Lift | Degrees | Spinal tilt angle at peak leg lift (e.g., pulling off toward 1B/3B). |
| `hand_depth_in_glove` | Static Set Pause | Pixel / Torso | Distance of throwing wrist insertion into glove pocket (grip depth). |
| `stance_width_at_set` | Static Set Pause | Torso Lengths | Distance between lead ankle and rubber anchor ankle. |
| `coming_set_sway_amp` | Pre-Set Trajectory | Torso Lengths | Smoothed pelvis lateral excursion amplitude during settling routine. |
| `coming_set_directness`| Pre-Set Trajectory | Ratio (0–1) | Net displacement divided by total path length (abrupt vs. sweeping set). |
| `set_to_lift_frames` | Temporal Cadence | Milliseconds / Frames | Duration of static set pause prior to leg lift initiation. |
| `lift_to_break_frames`| Temporal Cadence | Milliseconds / Frames | Delivery tempo from peak lift through hand separation. |

### Catcher Setup & Battery Tracking
Mechanical variance is not restricted to the pitcher. Preflight tracks the complete battery:
- **Catcher Mitt Position (`cmitt_x`, `cmitt_y`)**: Measures target presentation coordinates relative to home plate 0.5s–1.0s before delivery initiation.
- **Crouch Geometry & Stance Width**: Catcher knee-to-knee spread and hip elevation (identifies pre-set target commitment on breaking pitches vs. elevated fastballs).
- **Target Stillness Timing**: Milliseconds between catcher glove lock and pitcher movement initiation.

---

## Broadcast Center Field (CF) Limits vs. Enterprise Club Expansion

Preflight was initially evaluated across broadcast center-field camera feeds (MLB Film Room / Baseball Savant). While broadcast CF provides a broad screening baseline, empirical tracking isolated **three hard physical limitations** of broadcast video that necessitate club-level multi-angle film integration.

```
+----------------------------------------------------------------------------------------------------+
|                                BROADCAST CF LIMITS vs. ENTERPRISE CLUB                             |
+----------------------------------------------------------------------------------------------------+
| Physical Factor      | Broadcast CF Feeds (PoC Baseline)      | Enterprise Club 4K Multi-Angle     |
+----------------------+----------------------------------------+------------------------------------+
| Clip Timing          | Truncated ~0.5s before set (31% loss)  | Continuous 60fps high-bitrate feed |
| Hand Resolution      | ~35x35 px hand crop (pixel blurred)    | Dedicated 4K tight glove crop      |
| Sightline Geometry   | Single 2D projection (severe occlusion)| Synchronized 3B, 1B, 2B, High-Home |
| Predictive Power     | Screening baseline (>=75% signal floor)| High-certainty game-planning intel |
+----------------------------------------------------------------------------------------------------+
```

### The Three Physical Limits of Broadcast CF

```
                       [1. LATE CLIP TRUNCATION]
             Broadcast Savant MP4s start AFTER PitchCom programming
             ========================================================

                         [2. PIXEL DENSITY LIMIT]
               35x35 px Hand Crop: Finger pressure & seam grip
               submerged in sensor quantization noise
             ========================================================

                       [3. SIGHTLINE OCCLUSION]
          CF camera views glove edge-on; cannot observe 3B dugout
          flares, 1B coach wrist angles, or 2B runner tuck depths
```

1. **Late Clip Start (Pre-Set Truncation)**: Broadcast clips routinely start after the pitcher has already stepped onto the rubber, truncating pre-set PitchCom entry and initial hand placement.
2. **Pixel Density on Fingers / PitchCom**: In 720p/1080p wide broadcast shots, the pitcher's hand occupies approximately $35 \times 35$ pixels. Individual finger curls, grip depth variations, and PitchCom push-button taps sit below the spatial Nyquist limit.
3. **Sightline Occlusion (Single-Angle Ambiguity)**: Center field captures the pitcher nearly along their sagittal/coronal axis. Hand placement inside the glove pocket is hidden from CF but completely exposed to the second base runner and third/first base coaches.

### Enterprise 4K Multi-Angle Club Feeds

To transition from candidate screening to high-certainty game-planning intelligence, Preflight integrates directly with proprietary club camera infrastructure:

```
                                [HIGH HOME CAMERA]
                       (Spinal Posture, Torso Lean, Tempo)
                                       |
                                       v
[1B COACH CAMERA] ---------> [PITCHER DELIVERY] <--------- [3B DUGOUT CAMERA]
(Forearm Angle / Tucking)              ^                   (Glove Flare / Inside Grip)
                                       |
                              [TIGHT 4K CF CAMERA]
                          (Sub-Pixel Landmark Tracking)
```

- **Tight 4K CF Feed**: High-resolution zoom on pitcher trunk and glove ($>250 \times 250$ pixel hand crops).
- **3B Coach / Dugout Angle**: Direct view into the glove pocket for right-handed pitchers; captures grip adjustments, wrist angle, and finger flaring.
- **1B Coach / Dugout Angle**: Unobstructed view for left-handed pitchers and backside forearm/elbow alignment.
- **Low 2B / Runner-Perspective Camera**: Direct ground-truth angle for 2nd-base runner relay cues (e.g., Drew Thorpe changeup tuck height).
- **High Home / Overhead Plate Camera**: Measures true transverse shoulder/hip rotation and catcher setup dynamics.

### Statistical Validation Framework

To guarantee that reported tips reflect genuine pitcher habits rather than random sample variation, Preflight implements a multi-stage statistical testing suite:

1. **Game-Stratified Holdout Splits**: All pitch samples are partitioned by **game outings**, never randomly pitch-by-pitch. This prevents single-game camera calibration, mound lighting, or uniform changes from leaking across splits.
2. **Delivery Stratification**: Windup and stretch deliveries are strictly isolated into distinct statistical strata ($n_{\text{stratum}} \ge 10$), eliminating delivery-mix confounding.
3. **Benjamini-Hochberg False Discovery Rate (FDR $q = 0.10$)**: Controls discovery error across hundreds of simultaneous pairwise comparisons.
4. **Effect Size Thresholds**: Cues must exceed standardized Hedges' $g \ge 0.35$ in discovery and $g \ge 0.20$ in holdout.
5. **Youden's $J$ Statistic & Usage-Weighted Likelihood Ratios**:
   - **Youden's $J$ Index**: $J = \text{Sensitivity} + \text{Specificity} - 1$, measuring net classification lift above chance.
   - **Likelihood Ratio (LR+)**: Converts raw physical discrepancy into actionable in-game conditional probability given prior pitch usage:

$$P(\text{Pitch Type} \mid \text{Cue}) = \frac{P(\text{Cue} \mid \text{Pitch Type}) \cdot P(\text{Pitch Type})}{P(\text{Cue})}$$

---

## Practical Scouting & Player Development Applications

```
+--------------------------------------------------------------------------------------------------+
|                                PRACTICAL SCOUTING APPLICATIONS                                   |
+--------------------------------------------------------------------------------------------------+
|                                                                                                  |
|   [1. Advance Scouting]            [2. Player Development]         [3. Battery Scouting]         |
|   - Opponent Tip Cards             - Bullpen Consistency Audits    - Catcher Target Shifts       |
|   - Base-Runner Relay Cues         - Delivery Drift Tracking       - Stance & Crouch Tells       |
|   - High-Leverage Traps            - Post-Injury Mechanics        - PitchCom Cadence Leak       |
|                                                                                                  |
+--------------------------------------------------------------------------------------------------+
```

### 1. Advance Scouting Pitch Tipping Reports
- **Opponent Scouting Cards**: Generate pre-series dossiers detailing high-confidence physical cues for upcoming opposing starters and key bullpen arms.
- **Base-Runner Relay Protocols**: Equip runners on second base and base coaches with concrete, easily observable tells (e.g., *"If glove sits above the jersey lettering at lift, expect offspeed"*).
- **Count & Situation Conditioning**: Identify mechanical differences that manifest primarily in two-strike counts or with runners in scoring position.

### 2. Bullpen Mechanical Consistency Audits
- **Internal Self-Scouting (Defensive Audit)**: Audit your own pitching staff during bullpen sessions and live game outings to detect unintentional mechanical drift before opponents exploit it.
- **Biomechanical Fatigue & Rehab Monitoring**: Quantify changes in posture, glove set elevation, and delivery tempo across high pitch counts or post-injury rehabilitation progression.

### 3. Catcher Target Placement & Battery Scouting
- **Target Setup Timing**: Detect whether catchers set up early on fastballs or delay glove placement on breaking pitches in the dirt.
- **Body Shift & Crouch Depth**: Identify catchers whose stance width or posture shifts toward the pull-side batter's box prior to pitch selection.

### 4. Game-Planning Intelligence & In-Game Relays
- **Hitter Approach Optimization**: Provide hitters with selective swing-decision green lights when high-certainty cues eliminate specific pitch categories (e.g., eliminating the 98 mph 4-seamer to hunt sweeper).
- **Automated Video Cut-Ups**: Deliver timestamped, synchronized side-by-side video overlays directly to coaching tablets in the dugout.

---

## Repository Structure

```
pitch-tips/
├── README.md                      # Comprehensive technical documentation & system guide
├── index.html                     # Platform overview & system architecture landing page
├── board.html                     # Interactive advance scouting board & ranked leads
├── findings.html                  # Empirical findings, benchmark dossiers & validation limits
├── methodology.html               # Biomechanical primitives & computer vision methodology
├── analysis.html                  # Statistical evaluation, Youden's J & calibration metrics
├── teams.html                     # MLB organizational coverage & roster tracking board
├── team.html                      # Single-team pitching staff overview
├── player.html                    # Individual pitcher mechanical breakdown & tip dossier
├── label.html                     # Integrated bounding-box & landmark annotation UI
├── progress.html                  # Pipeline ingestion & league-wide tracking monitor
├── vercel.json                    # Vercel deployment & routing configuration
├── .vercelignore                  # Production deployment exclusion rules
├── .gitignore                     # Git tracking rules for models, clips, and caches
│
├── css/
│   └── site.css                   # Responsive dark-mode dashboard stylesheet
├── js/
│   └── app.js                     # Dynamic data loading, filtering, and table rendering
│
├── data/
│   ├── demo.json                  # Production dataset of tracked MLB pitcher mechanical leads
│   ├── progress.json              # League-wide ingestion status & tracking progress
│   └── label_manifest*.json       # Bounding box & keypoint ground truth manifests
│
├── cv/                            # Core Computer Vision & Statistical Engine
│   ├── requirements.txt           # Python environment dependencies
│   ├── README.md                  # CV pipeline operational documentation
│   ├── run_league.sh              # Shell orchestrator for league-scale execution
│   └── preflight/
│       ├── __init__.py
│       ├── fetch_savant.py        # Automated Savant/MLB video ingest by play ID
│       ├── track_pitcher.py       # MediaPipe Pose & Face anatomical tracking
│       ├── primitives.py          # 15+ normalized biomechanical primitives
│       ├── window.py              # Set-to-hand-break temporal clamping & segmentation
│       ├── spot_diff.py           # Unified pairwise statistical contrast engine
│       ├── catcher_locate.py      # Catcher mitt, stance & target tracking
│       ├── discern.py             # Feature extraction & dataset synthesis
│       ├── thresholds.py          # Empirical publish gating & FDR false-discovery control
│       ├── build_board.py         # Scouting board JSON data compiler
│       ├── scale_league.py        # Automated 30-team batch processing pipeline
│       └── models/                # Pretrained neural network weights & configs
│
├── docs/                          # In-Depth Engineering & Biomechanical Specs
│   ├── tip_taxonomy.md            # 24 catalogued professional scout tip classifications
│   ├── footage_upload_spec.md     # Multi-angle camera upload & calibration specifications
│   ├── catcher_localisation.md    # Battery tracking architecture & edge-case handling
│   └── cmitt_box_schema.md        # Catcher mitt bounding box geometry & class schemas
│
└── scripts/                       # Automation & Background Daemon Scripts
    └── launchd/                   # macOS launchd background scheduler plists
```

---

## Local Setup & Deployment Guide

### Prerequisites
- **Python 3.10+** (tested on 3.10, 3.11, 3.12)
- **Node.js / Modern Browser** (for static dashboard)
- **FFmpeg & libsm6** (required by OpenCV / MediaPipe)

### Static Dashboard Serving
The dashboard is built as a zero-dependency static web application that reads compiled JSON data directly from `data/demo.json`.

```bash
# Clone the repository
git clone https://github.com/colbymorris08/PreFlightPitchTips.git
cd PreFlightPitchTips

# Start a local HTTP server
python3 -m http.server 8000
```

Open your browser and navigate to:
- **Landing Page**: [http://localhost:8000/index.html](http://localhost:8000/index.html)
- **Ranked Scouting Board**: [http://localhost:8000/board.html](http://localhost:8000/board.html)
- **Findings & Methodology**: [http://localhost:8000/findings.html](http://localhost:8000/findings.html)
- **Interactive Labeler**: [http://localhost:8000/label.html](http://localhost:8000/label.html)

### Running the Computer Vision Pipeline

```bash
# Navigate to the CV engine
cd cv

# Install Python dependencies
pip install -r requirements.txt

# Download video for a specific play
python -m preflight.fetch_savant --play-id <SAVANT_PLAY_ID> --out ../runs/clips

# Run anatomical landmark tracking on a pitch clip
python -m preflight.track_pitcher --clip ../runs/clips/<ID>.mp4 --out ../runs/tracks --camera-id CF

# Execute end-to-end tip detection on a target pitcher
python -m preflight.run_poc \
  --pitcher "Logan Webb" \
  --season 2026 \
  --sample 40 \
  --work ../runs/webb_poc

# Recompile the interactive scouting board dataset
python -m preflight.build_board --work ../runs --out ../data/demo.json
```

### Vercel Deployment
The repository includes a ready-to-deploy `vercel.json` and `.vercelignore` configured for instant static hosting on Vercel:

```bash
# Deploy via Vercel CLI
npx vercel --prod
```

Or connect the repository directly in the [Vercel Dashboard](https://vercel.com/new).

---

## Technical Specifications & Citation

```bibtex
@software{apex_preflight_2026,
  author = {Morris, Colby},
  title = {Apex Preflight: Computer Vision Pitch Anticipation and Mechanical Discrepancy Engine},
  year = {2026},
  publisher = {GitHub},
  url = {https://github.com/colbymorris08/PreFlightPitchTips}
}
```

---
*Apex Preflight · Confidential MLB Advance Scouting & Pitching Intelligence Engine.*
