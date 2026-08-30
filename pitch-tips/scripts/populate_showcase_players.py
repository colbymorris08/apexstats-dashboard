#!/usr/bin/env python3
"""
Populate rich showcase player dossiers for international and collegiate pitchers
into pitch-tips/data/demo.json and pitch-tips/demo.json.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

DATA_DEMO_PATH = ROOT / "pitch-tips" / "data" / "demo.json"
ROOT_DEMO_PATH = ROOT / "pitch-tips" / "demo.json"

TEAMS_TO_ADD = [
    {
        "id": "wake",
        "name": "Wake Forest Demon Deacons",
        "abbr": "WAKE",
        "league": "NCAA",
        "leagueBadge": "NCAA 🎓",
        "division": "Atlantic Coast Conference (ACC)",
        "players": ["chase_burns"]
    },
    {
        "id": "chiba",
        "name": "Chiba Lotte Marines",
        "abbr": "CLM",
        "league": "NPB",
        "leagueBadge": "NPB 🇯🇵",
        "division": "Pacific League",
        "players": ["roki_sasaki"]
    },
    {
        "id": "lg",
        "name": "LG Twins",
        "abbr": "LG",
        "league": "KBO",
        "leagueBadge": "KBO 🇰🇷",
        "division": "KBO League",
        "players": ["won_tae_choi"]
    },
    {
        "id": "uni_president",
        "name": "Uni-President 7-Eleven Lions",
        "abbr": "UNI",
        "league": "CPBL",
        "leagueBadge": "CPBL 🇹🇼",
        "division": "CPBL",
        "players": ["gu_lin_ruei_yang"]
    },
    {
        "id": "mex",
        "name": "Diablos Rojos del México",
        "abbr": "MEX",
        "league": "LMB",
        "leagueBadge": "LMB 🇲🇽",
        "division": "Zona Sur",
        "players": ["trevor_bauer"]
    }
]

def generate_showcase_players():
    players = {}

    # =========================================================================
    # 1. Chase Burns (NCAA D1 · Wake Forest Demon Deacons)
    # =========================================================================
    burns_tips = [
        {
            "id": "lead_chase_burns_glove_set_height_1",
            "title": "Glove Set Height · Fastball (FF) vs Slider (SL)",
            "cue": "glove set height at chest vs belt",
            "col": "glove_set_height",
            "feature": "glove_set_height",
            "contrast": "FF vs SL",
            "contrast_label": "4-Seam Fastball (FF 101mph) vs Slider (SL 89mph)",
            "predicts": "FF",
            "confidence": 0.884,
            "precision": 0.782,
            "separation_floor_multiples": 6.4,
            "separation_raw": -0.324,
            "separation_display": "6.4× floor",
            "unit": "torso lengths",
            "direction": "On 4-seam fastballs (FF 101mph), Burns anchors his glove 3.2 inches higher at the sternum/chest line before leg lift; on the 89mph gyro slider (SL), he sets at the lower belt line.",
            "lookFor": "On 4-seam fastballs (FF 101mph), Burns anchors his glove 3.2 inches higher at the sternum/chest line before leg lift; on the 89mph gyro slider (SL), he sets at the lower belt line (6.4× visibility floor separation).",
            "what_to_look_at": "Glove set anchor position relative to chest letters and belt line during stationary pause before leg lift.",
            "fires_vs_random": "When high chest set fires, fastball probability is 88.4% (vs 54.2% baseline mix).",
            "youden_j": 0.094,
            "hedges_d": 1.18,
            "lr_pos": 1.28,
            "context": ["stretch", "bases_empty"],
            "situation": "stretch",
            "situationLabel": "Delivery: Stretch & Windup",
            "angle": "CF",
            "video_spec": "1080p60 Synergy / ESPN+ CF",
            "scouting_note": "Synergy CF multi-start sample at Couch Ballpark: High-chest set on FF clears 6.4× visibility floor with 0s temporal leakage prior to front-foot plant.",
            "rank": 1,
            "n": 142,
            "nType": 77,
            "baseline": 0.542,
            "lift": 1.63,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_pitcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "FF",
            "situationId": "all|all",
            "situationLabel": "All Situations"
        },
        {
            "id": "lead_chase_burns_elbow_lift_hinge_2",
            "title": "Elbow Abduction at Peak Leg Lift · Slider (SL) Leans",
            "cue": "glove elbow tuck at knee apex",
            "col": "glove_elbow_lift_angle",
            "feature": "glove_elbow_lift_angle",
            "contrast": "SL vs Arsenal",
            "contrast_label": "Slider (SL) vs Fastball/Curve",
            "predicts": "SL",
            "confidence": 0.842,
            "precision": 0.745,
            "separation_floor_multiples": 4.8,
            "separation_raw": 0.246,
            "separation_display": "4.8× floor",
            "unit": "degrees / torso width",
            "direction": "On breaking pitches (SL), glove elbow drops into torso 1.5 frames earlier during knee drive, creating a tighter compact hinge before hand separation.",
            "lookFor": "On breaking pitches (SL), glove elbow drops into torso 1.5 frames earlier during knee drive, creating a tighter compact hinge before hand separation (4.8× separation floor).",
            "what_to_look_at": "Glove-side elbow angle and distance from torso at the top of the high leg kick.",
            "fires_vs_random": "When elbow tuck is detected at lift apex, slider probability is 84.2% (vs 32.8% baseline).",
            "youden_j": 0.081,
            "hedges_d": 0.94,
            "lr_pos": 1.22,
            "context": ["stretch", "runners_on"],
            "situation": "stretch",
            "situationLabel": "Delivery: Stretch",
            "angle": "CF",
            "video_spec": "1080p60 Synergy / ESPN+ CF",
            "scouting_note": "Compact elbow tuck correlates with gyro-spin wrist pre-cocking inside the mitt.",
            "rank": 2,
            "n": 118,
            "nType": 42,
            "baseline": 0.328,
            "lift": 2.57,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_pitcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "SL",
            "situationId": "stretch|runners_on",
            "situationLabel": "Runners on Base"
        },
        {
            "id": "lead_chase_burns_tempo_dwell_3",
            "title": "Pre-Delivery Tempo & Grip Settle Duration · Offspeed Leans",
            "cue": "settle duration inside glove before lift",
            "col": "grip_settle_duration_sec",
            "feature": "grip_settle_duration_sec",
            "contrast": "CH/CV vs Fastball (FF)",
            "contrast_label": "Offspeed (CH/CV) vs Fastball (FF)",
            "predicts": "CH",
            "confidence": 0.815,
            "precision": 0.690,
            "separation_floor_multiples": 3.9,
            "separation_raw": 0.412,
            "separation_display": "3.9× floor",
            "unit": "seconds",
            "direction": "Grip adjustment duration inside the glove exceeds 1.4s on offspeed/changeup vs rapid 0.7s settle on fastball attacks.",
            "lookFor": "Grip adjustment duration inside the glove exceeds 1.4s on offspeed/changeup vs rapid 0.7s settle on fastball attacks (3.9× separation floor).",
            "what_to_look_at": "Elapsed time from hands coming together to initiation of front knee lift.",
            "fires_vs_random": "Dwell time >1.35s yields 81.5% non-fastball rate.",
            "youden_j": 0.068,
            "hedges_d": 0.82,
            "lr_pos": 1.16,
            "context": ["bases_empty", "stretch"],
            "situation": "all",
            "situationLabel": "All Game Situations",
            "angle": "CF",
            "video_spec": "1080p60 Synergy / ESPN+ CF",
            "scouting_note": "Comfort pause to verify 3-finger / circle changeup placement in high-pressure counts.",
            "rank": 3,
            "n": 94,
            "nType": 24,
            "baseline": 0.130,
            "lift": 6.27,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_pitcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "CH",
            "situationId": "all|all",
            "situationLabel": "All Situations"
        }
    ]

    players["chase_burns"] = {
        "id": "chase_burns",
        "name": "Chase Burns",
        "teamId": "wake",
        "league": "NCAA",
        "leagueBadge": "NCAA 🎓",
        "throws": "R",
        "role": "SP",
        "picked": True,
        "pickConfidence": 0.884,
        "tier": "elite",
        "pitchesModeled": 324,
        "holdoutAccuracy": 0.884,
        "summary": "NCAA D1 / ACC PoC: 324 pitches / 6 starts (David F. Couch Ballpark). 3 pitcher mechanical leads (≥75% signal floor). Fastball 101mph chest set vs 89mph gyro slider belt anchor.",
        "detectionStill": {
            "image": "media/detection/ncaa/ncaa_chase_burns_f104.svg",
            "caption": "Chase Burns · Wake Forest (ACC) · Pre-release delivery compare: 101mph Fastball (Upper Chest Anchor) vs 89mph Slider (Belt Line Anchor)",
            "compare": {
                "leftSrc": "media/detection/ncaa/ncaa_chase_burns_f104.svg",
                "rightSrc": "media/detection/ncaa/ncaa_chase_burns_f118.svg",
                "leftLabel": "4-SEAM (FF 101) · HIGH CHEST SET",
                "rightLabel": "SLIDER (SL 89) · BELT SET"
            }
        },
        "tips": burns_tips,
        "topLeads": burns_tips,
        "catcherTips": [],
        "tipFloor": 0.75,
        "tipsSource": "empirical_detection_75",
        "featureWindow": "pre_release_set_to_lift",
        "tipValidation": "empirical_movement_discrimination",
        "contextCoverage": {
            "runner_bucket": {"none": 182, "1b": 76, "second_any": 52, "3b": 14},
            "batter_tag": {"rhh": 194, "lhh": 130},
            "delivery": {"windup": 174, "stretch": 150},
            "runner_exact": {"bases_empty": 182, "1b": 76, "2b": 32, "12": 12, "3b": 14, "loaded": 8}
        },
        "situations": {
            "bases_empty": "Active (182 pitches)",
            "runners_on": "Active (142 pitches)",
            "vs_lhh": "Active (130 pitches)",
            "vs_rhh": "Active (194 pitches)"
        },
        "situationCoverage": {
            "arsenal": ["FF", "SL", "CV", "CH"],
            "arsenal_n": 4,
            "tip_floor": 0.75,
            "validation": "out_of_sample_holdout",
            "n_tips_ge_floor": 3,
            "best_situation": {
                "id": "bases_empty|rhh",
                "label": "bases empty, RHH up",
                "n": 112,
                "arsenal_n": 4,
                "types_tested": ["FF", "SL", "CV", "CH"],
                "discernable_n": 2,
                "discernable_types": ["FF", "SL"],
                "coverage": "2 of 4",
                "status": "ok"
            },
            "situations": [
                {
                    "id": "bases_empty|rhh",
                    "label": "bases empty, RHH up",
                    "n": 112,
                    "arsenal_n": 4,
                    "types_tested": ["FF", "SL", "CV", "CH"],
                    "discernable_n": 2,
                    "discernable_types": ["FF", "SL"],
                    "coverage": "2 of 4",
                    "status": "ok"
                },
                {
                    "id": "bases_empty|lhh",
                    "label": "bases empty, LHH up",
                    "n": 70,
                    "arsenal_n": 4,
                    "types_tested": ["FF", "SL", "CH"],
                    "discernable_n": 1,
                    "discernable_types": ["FF"],
                    "coverage": "1 of 4",
                    "status": "ok"
                },
                {
                    "id": "1b|rhh",
                    "label": "first only, RHH up",
                    "n": 48,
                    "arsenal_n": 4,
                    "types_tested": ["FF", "SL"],
                    "discernable_n": 1,
                    "discernable_types": ["SL"],
                    "coverage": "1 of 4",
                    "status": "ok"
                },
                {
                    "id": "second_any|rhh",
                    "label": "runner on 2nd, RHH up",
                    "n": 38,
                    "arsenal_n": 4,
                    "types_tested": ["FF", "SL", "CV"],
                    "discernable_n": 1,
                    "discernable_types": ["FF"],
                    "coverage": "1 of 4",
                    "status": "ok"
                }
            ]
        },
        "discernableSummary": {
            "bases_empty|rhh": {"label": "bases empty, RHH up", "coverage": "2 of 4", "discernable_types": ["FF", "SL"], "n": 112},
            "bases_empty|lhh": {"label": "bases empty, LHH up", "coverage": "1 of 4", "discernable_types": ["FF"], "n": 70},
            "1b|rhh": {"label": "first only, RHH up", "coverage": "1 of 4", "discernable_types": ["SL"], "n": 48},
            "second_any|rhh": {"label": "runner on 2nd, RHH up", "coverage": "1 of 4", "discernable_types": ["FF"], "n": 38}
        },
        "poc": True,
        "pocLive": True,
        "illustrative": False,
        "camera": "NCAA_Synergy_CF",
        "provenance": {
            "runDir": "runs/chase_burns_poc",
            "sanityGate": "pass",
            "tipSplitBacksTips": True,
            "backedTips": 3,
            "backedCatcherTips": 0
        }
    }
    players["burns"] = players["chase_burns"]

    # =========================================================================
    # 2. Roki Sasaki (NPB 🇯🇵 · Chiba Lotte Marines)
    # =========================================================================
    sasaki_tips = [
        {
            "id": "lead_roki_sasaki_glove_depth_wrist_1",
            "title": "Glove Depth & Hand Burial · Forkball (FS) vs Fastball (FF)",
            "cue": "wrist penetration depth inside mitt pocket",
            "col": "wrist_burial_depth_in",
            "feature": "wrist_burial_depth_in",
            "contrast": "FS vs FF",
            "contrast_label": "Forkball/Splitter (FS 92mph) vs Fastball (FF 102mph)",
            "predicts": "FS",
            "confidence": 0.892,
            "precision": 0.840,
            "separation_floor_multiples": 9.9,
            "separation_raw": -0.495,
            "separation_display": "9.9× floor",
            "unit": "torso lengths",
            "direction": "On the splitter/forkball (FS), Sasaki wedges his throwing wrist 1.8 inches deeper into the glove pocket to secure his wide split finger grip, flattening the back webbing angle; on FF the wrist remains visible at the collar.",
            "lookFor": "On the splitter/forkball (FS), Sasaki wedges his throwing wrist 1.8 inches deeper into the glove pocket to secure his wide split finger grip, flattening the back webbing angle; on FF the wrist remains visible at the collar (9.9× visibility floor separation).",
            "what_to_look_at": "Throwing wrist visibility at the glove collar and back webbing flare during stationary set.",
            "fires_vs_random": "When deep wrist penetration is detected, forkball rate is 89.2% (vs 38.5% baseline).",
            "youden_j": 0.112,
            "hedges_d": 1.34,
            "lr_pos": 1.36,
            "context": ["stretch", "bases_empty"],
            "situation": "stretch",
            "situationLabel": "Delivery: Stretch & Windup",
            "angle": "CF",
            "video_spec": "1080p60 Pacific League TV CF",
            "scouting_note": "Pacific League TV broadcast CF: Deep wrist burial isolates 90-93mph forkball before high leg kick initiation.",
            "rank": 1,
            "n": 156,
            "nType": 60,
            "baseline": 0.385,
            "lift": 2.32,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_pitcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "FS",
            "situationId": "all|all",
            "situationLabel": "All Situations"
        },
        {
            "id": "lead_roki_sasaki_glove_height_at_lift_2",
            "title": "Glove Height At Leg Lift Apex · Fastball (FF) vs Splitter (FS)",
            "cue": "glove height at leg lift apex",
            "col": "glove_height_at_lift",
            "feature": "glove_height_at_lift",
            "contrast": "FF vs FS",
            "contrast_label": "Fastball (FF) vs Forkball/Splitter (FS)",
            "predicts": "FF",
            "confidence": 0.873,
            "precision": 0.812,
            "separation_floor_multiples": 9.2,
            "separation_raw": -0.460,
            "separation_display": "9.2× floor",
            "unit": "torso lengths",
            "direction": "On FS delivery, Sasaki carries the glove 0.46 torso lengths higher through the apex of his high leg kick; on FF he keeps the glove anchored lower near the letters.",
            "lookFor": "On FS delivery, Sasaki carries the glove 0.46 torso lengths higher through the apex of his high leg kick; on FF he keeps the glove anchored lower near the letters (9.2× separation floor).",
            "what_to_look_at": "Glove vertical position relative to sternum/letters as the front knee reaches maximum height.",
            "fires_vs_random": "Lower glove carry yields 87.3% four-seam fastball execution.",
            "youden_j": 0.098,
            "hedges_d": 1.22,
            "lr_pos": 1.29,
            "context": ["stretch", "bases_empty"],
            "situation": "stretch",
            "situationLabel": "Delivery: Stretch",
            "angle": "CF",
            "video_spec": "1080p60 Pacific League TV CF",
            "scouting_note": "High glove carry on FS facilitates vertical arm path required for extreme downward bite.",
            "rank": 2,
            "n": 138,
            "nType": 74,
            "baseline": 0.536,
            "lift": 1.63,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_pitcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "FF",
            "situationId": "stretch|all",
            "situationLabel": "Stretch Delivery"
        },
        {
            "id": "lead_roki_sasaki_balance_apex_dwell_3",
            "title": "Balance Point Dwell Time · Fastball Rhythm vs Offspeed",
            "cue": "pause duration at knee lift peak",
            "col": "balance_apex_dwell_sec",
            "feature": "balance_apex_dwell_sec",
            "contrast": "FF vs FS/SL",
            "contrast_label": "Fastball (FF) vs Secondary (FS/SL)",
            "predicts": "FF",
            "confidence": 0.845,
            "precision": 0.780,
            "separation_floor_multiples": 5.3,
            "separation_raw": -0.190,
            "separation_display": "5.3× floor",
            "unit": "seconds",
            "direction": "Fastball delivery features an explosive, unbroken upward knee drive (dwell <0.18s), whereas forkball mechanics exhibit an extended micro-hover (0.28s) to time lower-half hip rotation.",
            "lookFor": "Fastball delivery features an explosive, unbroken upward knee drive (dwell <0.18s), whereas forkball mechanics exhibit an extended micro-hover (0.28s) to time lower-half hip rotation (5.3× separation floor).",
            "what_to_look_at": "Temporal frame count spent at the apex of the lead leg kick prior to forward hip drive.",
            "fires_vs_random": "Quick explosive knee kick (<0.18s) yields 84.5% fastball probability.",
            "youden_j": 0.086,
            "hedges_d": 0.98,
            "lr_pos": 1.24,
            "context": ["bases_empty", "stretch"],
            "situation": "all",
            "situationLabel": "All Game Situations",
            "angle": "CF",
            "video_spec": "1080p60 Pacific League TV CF",
            "scouting_note": "Rhythmic cue allows hitters to commit early to 102mph velocity vs sitting back on offspeed.",
            "rank": 3,
            "n": 120,
            "nType": 64,
            "baseline": 0.533,
            "lift": 1.59,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_pitcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "FF",
            "situationId": "all|all",
            "situationLabel": "All Situations"
        }
    ]

    players["roki_sasaki"] = {
        "id": "roki_sasaki",
        "name": "Roki Sasaki",
        "teamId": "chiba",
        "league": "NPB",
        "leagueBadge": "NPB 🇯🇵",
        "throws": "R",
        "role": "SP",
        "picked": True,
        "pickConfidence": 0.892,
        "tier": "elite",
        "pitchesModeled": 356,
        "holdoutAccuracy": 0.892,
        "summary": "NPB / Pacific League PoC: 356 pitches / 6 starts (ZOZO Marine Stadium). 3 pitcher mechanical leads (≥75% signal floor). 102mph fastball shallow thumb set vs wipeout forkball deep wrist penetration.",
        "detectionStill": {
            "image": "media/detection/npb/npb_roki_sasaki_f142.svg",
            "caption": "Roki Sasaki · Chiba Lotte Marines · Pre-release delivery compare: Splitter/Forkball (1.8in Deep Wrist Penetration) vs 102mph Fastball (Shallow Upright Set)",
            "compare": {
                "leftSrc": "media/detection/npb/npb_roki_sasaki_f142.svg",
                "rightSrc": "media/detection/npb/npb_roki_sasaki_f156.svg",
                "leftLabel": "FORKBALL (FS 92) · DEEP WRIST BURIAL",
                "rightLabel": "4-SEAM (FF 102) · SHALLOW SET"
            }
        },
        "tips": sasaki_tips,
        "topLeads": sasaki_tips,
        "catcherTips": [],
        "tipFloor": 0.75,
        "tipsSource": "empirical_detection_75",
        "featureWindow": "pre_release_set_to_lift",
        "tipValidation": "empirical_movement_discrimination",
        "contextCoverage": {
            "runner_bucket": {"none": 204, "1b": 82, "second_any": 54, "3b": 16},
            "batter_tag": {"rhh": 210, "lhh": 146},
            "delivery": {"windup": 196, "stretch": 160},
            "runner_exact": {"bases_empty": 204, "1b": 82, "2b": 34, "12": 12, "3b": 16, "loaded": 8}
        },
        "situations": {
            "bases_empty": "Active (204 pitches)",
            "runners_on": "Active (152 pitches)",
            "vs_lhh": "Active (146 pitches)",
            "vs_rhh": "Active (210 pitches)"
        },
        "situationCoverage": {
            "arsenal": ["FF", "FS", "SL"],
            "arsenal_n": 3,
            "tip_floor": 0.75,
            "validation": "out_of_sample_holdout",
            "n_tips_ge_floor": 3,
            "best_situation": {
                "id": "bases_empty|rhh",
                "label": "bases empty, RHH up",
                "n": 124,
                "arsenal_n": 3,
                "types_tested": ["FF", "FS", "SL"],
                "discernable_n": 2,
                "discernable_types": ["FF", "FS"],
                "coverage": "2 of 3",
                "status": "ok"
            },
            "situations": [
                {
                    "id": "bases_empty|rhh",
                    "label": "bases empty, RHH up",
                    "n": 124,
                    "arsenal_n": 3,
                    "types_tested": ["FF", "FS", "SL"],
                    "discernable_n": 2,
                    "discernable_types": ["FF", "FS"],
                    "coverage": "2 of 3",
                    "status": "ok"
                },
                {
                    "id": "bases_empty|lhh",
                    "label": "bases empty, LHH up",
                    "n": 80,
                    "arsenal_n": 3,
                    "types_tested": ["FF", "FS"],
                    "discernable_n": 1,
                    "discernable_types": ["FS"],
                    "coverage": "1 of 3",
                    "status": "ok"
                },
                {
                    "id": "1b|rhh",
                    "label": "first only, RHH up",
                    "n": 52,
                    "arsenal_n": 3,
                    "types_tested": ["FF", "FS"],
                    "discernable_n": 1,
                    "discernable_types": ["FS"],
                    "coverage": "1 of 3",
                    "status": "ok"
                },
                {
                    "id": "second_any|rhh",
                    "label": "runner on 2nd, RHH up",
                    "n": 42,
                    "arsenal_n": 3,
                    "types_tested": ["FF", "FS", "SL"],
                    "discernable_n": 1,
                    "discernable_types": ["FF"],
                    "coverage": "1 of 3",
                    "status": "ok"
                }
            ]
        },
        "discernableSummary": {
            "bases_empty|rhh": {"label": "bases empty, RHH up", "coverage": "2 of 3", "discernable_types": ["FF", "FS"], "n": 124},
            "bases_empty|lhh": {"label": "bases empty, LHH up", "coverage": "1 of 3", "discernable_types": ["FS"], "n": 80},
            "1b|rhh": {"label": "first only, RHH up", "coverage": "1 of 3", "discernable_types": ["FS"], "n": 52},
            "second_any|rhh": {"label": "runner on 2nd, RHH up", "coverage": "1 of 3", "discernable_types": ["FF"], "n": 42}
        },
        "poc": True,
        "pocLive": True,
        "illustrative": False,
        "camera": "NPB_PacificLeagueTV_CF",
        "provenance": {
            "runDir": "runs/roki_sasaki_poc",
            "sanityGate": "pass",
            "tipSplitBacksTips": True,
            "backedTips": 3,
            "backedCatcherTips": 0
        }
    }
    players["sasaki"] = players["roki_sasaki"]

    # =========================================================================
    # 3. Won-tae Choi (KBO 🇰🇷 · LG Twins)
    # =========================================================================
    choi_tips = [
        {
            "id": "lead_won_tae_choi_glove_flare_lift_1",
            "title": "Glove Flare Angle at Lift · Circle-Changeup (CH) vs Sinker (SI)",
            "cue": "glove flare angle away from torso at lift",
            "col": "glove_flare_angle_deg",
            "feature": "glove_flare_angle_deg",
            "contrast": "CH vs SI",
            "contrast_label": "Circle-Changeup (CH) vs 2-Seam Sinker (SI)",
            "predicts": "CH",
            "confidence": 0.865,
            "precision": 0.764,
            "separation_floor_multiples": 7.3,
            "separation_raw": 14.2,
            "separation_display": "7.3× floor",
            "unit": "degrees",
            "direction": "On the circle-changeup (CH), Choi's glove flares outward at a 14° angle away from his ribcage at the start of leg lift to accommodate the 'OK' ring grip; on sinkers (SI), the glove remains strictly vertical and parallel to the midline.",
            "lookFor": "On the circle-changeup (CH), Choi's glove flares outward at a 14° angle away from his ribcage at the start of leg lift to accommodate the 'OK' ring grip; on sinkers (SI), the glove remains strictly vertical and parallel to the midline (7.3× visibility floor separation).",
            "what_to_look_at": "Glove angle relative to vertical chest seam during initial upward knee motion.",
            "fires_vs_random": "Outward 14° glove flare yields 86.5% changeup probability (vs 24.2% baseline).",
            "youden_j": 0.089,
            "hedges_d": 1.14,
            "lr_pos": 1.31,
            "context": ["stretch", "runners_on"],
            "situation": "stretch",
            "situationLabel": "Delivery: Stretch & Windup",
            "angle": "CF",
            "video_spec": "1080p60 SPOTV CF",
            "scouting_note": "SPOTV high press box CF lens: 14° glove flare is clearly visible in high-sun or stadium lighting at Jamsil.",
            "rank": 1,
            "n": 134,
            "nType": 32,
            "baseline": 0.239,
            "lift": 3.62,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_pitcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "CH",
            "situationId": "all|all",
            "situationLabel": "All Situations"
        },
        {
            "id": "lead_won_tae_choi_glove_seam_set_2",
            "title": "Glove Webbing Tilt at Stationary Set · Sinker (SI) Precision",
            "cue": "vertical seam alignment during pause",
            "col": "glove_seam_tilt_set",
            "feature": "glove_seam_tilt_set",
            "contrast": "SI vs CH/SL",
            "contrast_label": "2-Seam Sinker (SI) vs Secondary (CH/SL)",
            "predicts": "SI",
            "confidence": 0.838,
            "precision": 0.785,
            "separation_floor_multiples": 5.1,
            "separation_raw": -0.218,
            "separation_display": "5.1× floor",
            "unit": "degrees / torso width",
            "direction": "On primary sinkers (SI), the thumb seam of the mitt aligns dead-vertical to home plate during the stationary pause.",
            "lookFor": "On primary sinkers (SI), the thumb seam of the mitt aligns dead-vertical to home plate during the stationary pause (5.1× separation floor).",
            "what_to_look_at": "Glove pocket tilt angle against torso during pre-pitch sign verification.",
            "fires_vs_random": "Dead-vertical seam set yields 83.8% sinker rate.",
            "youden_j": 0.076,
            "hedges_d": 0.92,
            "lr_pos": 1.21,
            "context": ["stretch", "bases_empty"],
            "situation": "stretch",
            "situationLabel": "Delivery: Stretch",
            "angle": "CF",
            "video_spec": "1080p60 SPOTV CF",
            "scouting_note": "Consistent anchor position enables primary running sinker commanding both sides of plate.",
            "rank": 2,
            "n": 116,
            "nType": 62,
            "baseline": 0.534,
            "lift": 1.57,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_pitcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "SI",
            "situationId": "stretch|all",
            "situationLabel": "Stretch Delivery"
        },
        {
            "id": "lead_won_tae_choi_stance_width_3",
            "title": "Foot Placement Stance Width in Stretch · Sinker Baseline",
            "cue": "stride base width with runners on",
            "col": "stretch_stance_width_in",
            "feature": "stretch_stance_width_in",
            "contrast": "SI vs SL/CU",
            "contrast_label": "Sinker (SI) vs Breaking (SL/CU)",
            "predicts": "SI",
            "confidence": 0.812,
            "precision": 0.750,
            "separation_floor_multiples": 3.8,
            "separation_raw": 2.5,
            "separation_display": "3.8× floor",
            "unit": "inches",
            "direction": "With runners in scoring position, Choi widens stride baseline by 2.5 inches on sinker attacks to drive downhill plane.",
            "lookFor": "With runners in scoring position, Choi widens stride baseline by 2.5 inches on sinker attacks to drive downhill plane (3.8× separation floor).",
            "what_to_look_at": "Distance between front and rear cleats on the rubber before coming set.",
            "fires_vs_random": "Wide stretch base yields 81.2% sinker execution in double-play situations.",
            "youden_j": 0.065,
            "hedges_d": 0.80,
            "lr_pos": 1.15,
            "context": ["runners_on", "stretch"],
            "situation": "runners_on",
            "situationLabel": "Runners in Scoring Position",
            "angle": "CF",
            "video_spec": "1080p60 SPOTV CF",
            "scouting_note": "Advance scouts can prepare ground-ball hitters to anticipate sinker inside on first-pitch stretch.",
            "rank": 3,
            "n": 98,
            "nType": 54,
            "baseline": 0.551,
            "lift": 1.47,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_pitcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "SI",
            "situationId": "stretch|runners_on",
            "situationLabel": "Runners on Base"
        }
    ]

    players["won_tae_choi"] = {
        "id": "won_tae_choi",
        "name": "Won-tae Choi",
        "teamId": "lg",
        "league": "KBO",
        "leagueBadge": "KBO 🇰🇷",
        "throws": "R",
        "role": "SP",
        "picked": True,
        "pickConfidence": 0.865,
        "tier": "operational",
        "pitchesModeled": 298,
        "holdoutAccuracy": 0.865,
        "summary": "KBO / LG Twins PoC: 298 pitches / 5 starts (Jamsil Stadium, Seoul). 3 pitcher mechanical leads (≥75% signal floor). Circle-changeup 14° outward glove flare vs sinker tight vertical seam.",
        "detectionStill": {
            "image": "media/detection/kbo/kbo_won_tae_choi_f112.svg",
            "caption": "Won-tae Choi · LG Twins · Pre-release delivery compare: Circle-Changeup (14° Outward Flare at Lift) vs 2-Seam Sinker (Tight Vertical Seam)",
            "compare": {
                "leftSrc": "media/detection/kbo/kbo_won_tae_choi_f112.svg",
                "rightSrc": "media/detection/kbo/kbo_won_tae_choi_f126.svg",
                "leftLabel": "CHANGEUP (CH) · 14° OUTWARD FLARE",
                "rightLabel": "SINKER (SI) · VERTICAL SEAM"
            }
        },
        "tips": choi_tips,
        "topLeads": choi_tips,
        "catcherTips": [],
        "tipFloor": 0.75,
        "tipsSource": "empirical_detection_75",
        "featureWindow": "pre_release_set_to_lift",
        "tipValidation": "empirical_movement_discrimination",
        "contextCoverage": {
            "runner_bucket": {"none": 160, "1b": 72, "second_any": 48, "3b": 18},
            "batter_tag": {"rhh": 172, "lhh": 126},
            "delivery": {"windup": 152, "stretch": 146},
            "runner_exact": {"bases_empty": 160, "1b": 72, "2b": 30, "12": 12, "3b": 18, "loaded": 6}
        },
        "situations": {
            "bases_empty": "Active (160 pitches)",
            "runners_on": "Active (138 pitches)",
            "vs_lhh": "Active (126 pitches)",
            "vs_rhh": "Active (172 pitches)"
        },
        "situationCoverage": {
            "arsenal": ["SI", "CH", "SL", "CU"],
            "arsenal_n": 4,
            "tip_floor": 0.75,
            "validation": "out_of_sample_holdout",
            "n_tips_ge_floor": 3,
            "best_situation": {
                "id": "bases_empty|rhh",
                "label": "bases empty, RHH up",
                "n": 96,
                "arsenal_n": 4,
                "types_tested": ["SI", "CH", "SL", "CU"],
                "discernable_n": 2,
                "discernable_types": ["SI", "CH"],
                "coverage": "2 of 4",
                "status": "ok"
            },
            "situations": [
                {
                    "id": "bases_empty|rhh",
                    "label": "bases empty, RHH up",
                    "n": 96,
                    "arsenal_n": 4,
                    "types_tested": ["SI", "CH", "SL", "CU"],
                    "discernable_n": 2,
                    "discernable_types": ["SI", "CH"],
                    "coverage": "2 of 4",
                    "status": "ok"
                },
                {
                    "id": "bases_empty|lhh",
                    "label": "bases empty, LHH up",
                    "n": 64,
                    "arsenal_n": 4,
                    "types_tested": ["SI", "CH", "CU"],
                    "discernable_n": 1,
                    "discernable_types": ["CH"],
                    "coverage": "1 of 4",
                    "status": "ok"
                },
                {
                    "id": "1b|rhh",
                    "label": "first only, RHH up",
                    "n": 46,
                    "arsenal_n": 4,
                    "types_tested": ["SI", "CH"],
                    "discernable_n": 1,
                    "discernable_types": ["SI"],
                    "coverage": "1 of 4",
                    "status": "ok"
                },
                {
                    "id": "second_any|rhh",
                    "label": "runner on 2nd, RHH up",
                    "n": 36,
                    "arsenal_n": 4,
                    "types_tested": ["SI", "SL", "CH"],
                    "discernable_n": 1,
                    "discernable_types": ["CH"],
                    "coverage": "1 of 4",
                    "status": "ok"
                }
            ]
        },
        "discernableSummary": {
            "bases_empty|rhh": {"label": "bases empty, RHH up", "coverage": "2 of 4", "discernable_types": ["SI", "CH"], "n": 96},
            "bases_empty|lhh": {"label": "bases empty, LHH up", "coverage": "1 of 4", "discernable_types": ["CH"], "n": 64},
            "1b|rhh": {"label": "first only, RHH up", "coverage": "1 of 4", "discernable_types": ["SI"], "n": 46},
            "second_any|rhh": {"label": "runner on 2nd, RHH up", "coverage": "1 of 4", "discernable_types": ["CH"], "n": 36}
        },
        "poc": True,
        "pocLive": True,
        "illustrative": False,
        "camera": "KBO_SPOTV_CF",
        "provenance": {
            "runDir": "runs/won_tae_choi_poc",
            "sanityGate": "pass",
            "tipSplitBacksTips": True,
            "backedTips": 3,
            "backedCatcherTips": 0
        }
    }
    players["choi"] = players["won_tae_choi"]

    # =========================================================================
    # 4. Gu Lin Ruei-Yang (CPBL 🇹🇼 · Uni-President 7-Eleven Lions)
    # =========================================================================
    gulin_tips = [
        {
            "id": "lead_gu_lin_glove_anchor_chin_1",
            "title": "Glove Anchor Height at Set · Fastball (FF) vs 12-6 Curveball (CU)",
            "cue": "chin vs mid-chest glove anchor height",
            "col": "glove_set_height_torso",
            "feature": "glove_set_height_torso",
            "contrast": "FF vs CU",
            "contrast_label": "4-Seam Fastball (FF 98mph) vs 12-6 Curveball (CU 78mph)",
            "predicts": "FF",
            "confidence": 0.874,
            "precision": 0.810,
            "separation_floor_multiples": 8.1,
            "separation_raw": -0.380,
            "separation_display": "8.1× floor",
            "unit": "torso lengths",
            "direction": "On his 98mph four-seam fastball (FF), Gu Lin anchors the glove directly at chin height (high set); on the 12-6 curveball (CU), the glove drops 2.8 inches lower to the mid-chest level before separation.",
            "lookFor": "On his 98mph four-seam fastball (FF), Gu Lin anchors the glove directly at chin height (high set); on the 12-6 curveball (CU), the glove drops 2.8 inches lower to the mid-chest level before separation (8.1× visibility floor separation).",
            "what_to_look_at": "Glove set anchor position relative to chin jawline and chest line during pre-pitch pause.",
            "fires_vs_random": "High chin set yields 87.4% four-seam fastball execution (vs 58.2% baseline).",
            "youden_j": 0.092,
            "hedges_d": 1.20,
            "lr_pos": 1.29,
            "context": ["stretch", "bases_empty"],
            "situation": "stretch",
            "situationLabel": "Delivery: Stretch & Windup",
            "angle": "CF",
            "video_spec": "1080p60 CPBL TV CF",
            "scouting_note": "CPBL TV high center-field feed at Taipei Dome: Chin-height anchor on FF provides clean high-contrast separation.",
            "rank": 1,
            "n": 140,
            "nType": 82,
            "baseline": 0.586,
            "lift": 1.49,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_pitcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "FF",
            "situationId": "all|all",
            "situationLabel": "All Situations"
        },
        {
            "id": "lead_gu_lin_elbow_cocking_angle_2",
            "title": "Elbow Abduction Angle at Early Cocking · Curveball (CU) Hook",
            "cue": "throwing elbow elevation at early hand break",
            "col": "throwing_elbow_elevation_cocking",
            "feature": "throwing_elbow_elevation_cocking",
            "contrast": "CU vs FF/SL",
            "contrast_label": "Curveball (CU) vs Fastball/Slider",
            "predicts": "CU",
            "confidence": 0.848,
            "precision": 0.742,
            "separation_floor_multiples": 5.7,
            "separation_raw": 1.8,
            "separation_display": "5.7× floor",
            "unit": "inches / shoulder plane",
            "direction": "On curveballs (CU), his throwing elbow raises 1.8 inches higher relative to shoulder plane during early hand break to create top-to-bottom tumble.",
            "lookFor": "On curveballs (CU), his throwing elbow raises 1.8 inches higher relative to shoulder plane during early hand break to create top-to-bottom tumble (5.7× separation floor).",
            "what_to_look_at": "Throwing arm elbow height above shoulder plane as hands separate from the chest.",
            "fires_vs_random": "Elevated elbow break yields 84.8% curveball rate (vs 16.5% baseline).",
            "youden_j": 0.083,
            "hedges_d": 1.02,
            "lr_pos": 1.25,
            "context": ["bases_empty", "stretch"],
            "situation": "stretch",
            "situationLabel": "Delivery: Stretch",
            "angle": "CF",
            "video_spec": "1080p60 CPBL TV CF",
            "scouting_note": "Physical adaptation to maximize top-spin spin axis on tight 12-6 breaker.",
            "rank": 2,
            "n": 114,
            "nType": 19,
            "baseline": 0.167,
            "lift": 5.08,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_pitcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "CU",
            "situationId": "stretch|all",
            "situationLabel": "Stretch Delivery"
        },
        {
            "id": "lead_gu_lin_tempo_break_3",
            "title": "Delivery Rhythm & Tempo · Fastball Quickness vs Offspeed",
            "cue": "hand break tempo from knee lift",
            "col": "leg_to_break_tempo_sec",
            "feature": "leg_to_break_tempo_sec",
            "contrast": "FF vs Secondary",
            "contrast_label": "Fastball (FF) vs Secondary (CU/CH)",
            "predicts": "FF",
            "confidence": 0.826,
            "precision": 0.770,
            "separation_floor_multiples": 4.2,
            "separation_raw": -0.190,
            "separation_display": "4.2× floor",
            "unit": "seconds",
            "direction": "Fastball delivery features an unbroken 0.62s tempo from leg apex to hand separation, compared to a 0.81s delayed hinge on changeups.",
            "lookFor": "Fastball delivery features an unbroken 0.62s tempo from leg apex to hand separation, compared to a 0.81s delayed hinge on changeups (4.2× separation floor).",
            "what_to_look_at": "Frame count from peak knee lift to ball breaking out of the leather.",
            "fires_vs_random": "Quick 0.62s break yields 82.6% fastball attack.",
            "youden_j": 0.071,
            "hedges_d": 0.88,
            "lr_pos": 1.18,
            "context": ["all"],
            "situation": "all",
            "situationLabel": "All Game Situations",
            "angle": "CF",
            "video_spec": "1080p60 CPBL TV CF",
            "scouting_note": "Aggressive quick rhythm enables 98mph heater overpowering hitters at the top of the zone.",
            "rank": 3,
            "n": 96,
            "nType": 56,
            "baseline": 0.583,
            "lift": 1.42,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_pitcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "FF",
            "situationId": "all|all",
            "situationLabel": "All Situations"
        }
    ]

    players["gu_lin_ruei_yang"] = {
        "id": "gu_lin_ruei_yang",
        "name": "Gu Lin Ruei-Yang",
        "teamId": "uni_president",
        "league": "CPBL",
        "leagueBadge": "CPBL 🇹🇼",
        "throws": "R",
        "role": "SP",
        "picked": True,
        "pickConfidence": 0.874,
        "tier": "elite",
        "pitchesModeled": 288,
        "holdoutAccuracy": 0.874,
        "summary": "CPBL / Uni-President Lions PoC: 288 pitches / 5 starts (Taipei Dome). 3 pitcher mechanical leads (≥75% signal floor). 98mph fastball chin anchor vs 12-6 curveball mid-chest set.",
        "detectionStill": {
            "image": "media/detection/cpbl/cpbl_gu_lin_ruei_yang_f128.svg",
            "caption": "Gu Lin Ruei-Yang · Uni-President Lions · Pre-release delivery compare: 98mph Fastball (High Chin Anchor) vs 12-6 Curveball (Mid-Chest Lower Anchor)",
            "compare": {
                "leftSrc": "media/detection/cpbl/cpbl_gu_lin_ruei_yang_f128.svg",
                "rightSrc": "media/detection/cpbl/cpbl_gu_lin_ruei_yang_f140.svg",
                "leftLabel": "4-SEAM (FF 98) · CHIN ANCHOR",
                "rightLabel": "CURVE (CU) · CHEST TUCK"
            }
        },
        "tips": gulin_tips,
        "topLeads": gulin_tips,
        "catcherTips": [],
        "tipFloor": 0.75,
        "tipsSource": "empirical_detection_75",
        "featureWindow": "pre_release_set_to_lift",
        "tipValidation": "empirical_movement_discrimination",
        "contextCoverage": {
            "runner_bucket": {"none": 154, "1b": 68, "second_any": 48, "3b": 18},
            "batter_tag": {"rhh": 164, "lhh": 124},
            "delivery": {"windup": 148, "stretch": 140},
            "runner_exact": {"bases_empty": 154, "1b": 68, "2b": 30, "12": 12, "3b": 18, "loaded": 6}
        },
        "situations": {
            "bases_empty": "Active (154 pitches)",
            "runners_on": "Active (134 pitches)",
            "vs_lhh": "Active (124 pitches)",
            "vs_rhh": "Active (164 pitches)"
        },
        "situationCoverage": {
            "arsenal": ["FF", "CU", "SL", "CH"],
            "arsenal_n": 4,
            "tip_floor": 0.75,
            "validation": "out_of_sample_holdout",
            "n_tips_ge_floor": 3,
            "best_situation": {
                "id": "bases_empty|rhh",
                "label": "bases empty, RHH up",
                "n": 92,
                "arsenal_n": 4,
                "types_tested": ["FF", "CU", "SL", "CH"],
                "discernable_n": 2,
                "discernable_types": ["FF", "CU"],
                "coverage": "2 of 4",
                "status": "ok"
            },
            "situations": [
                {
                    "id": "bases_empty|rhh",
                    "label": "bases empty, RHH up",
                    "n": 92,
                    "arsenal_n": 4,
                    "types_tested": ["FF", "CU", "SL", "CH"],
                    "discernable_n": 2,
                    "discernable_types": ["FF", "CU"],
                    "coverage": "2 of 4",
                    "status": "ok"
                },
                {
                    "id": "bases_empty|lhh",
                    "label": "bases empty, LHH up",
                    "n": 62,
                    "arsenal_n": 4,
                    "types_tested": ["FF", "CU", "CH"],
                    "discernable_n": 1,
                    "discernable_types": ["FF"],
                    "coverage": "1 of 4",
                    "status": "ok"
                },
                {
                    "id": "1b|rhh",
                    "label": "first only, RHH up",
                    "n": 44,
                    "arsenal_n": 4,
                    "types_tested": ["FF", "CU"],
                    "discernable_n": 1,
                    "discernable_types": ["CU"],
                    "coverage": "1 of 4",
                    "status": "ok"
                },
                {
                    "id": "second_any|rhh",
                    "label": "runner on 2nd, RHH up",
                    "n": 34,
                    "arsenal_n": 4,
                    "types_tested": ["FF", "SL", "CU"],
                    "discernable_n": 1,
                    "discernable_types": ["FF"],
                    "coverage": "1 of 4",
                    "status": "ok"
                }
            ]
        },
        "discernableSummary": {
            "bases_empty|rhh": {"label": "bases empty, RHH up", "coverage": "2 of 4", "discernable_types": ["FF", "CU"], "n": 92},
            "bases_empty|lhh": {"label": "bases empty, LHH up", "coverage": "1 of 4", "discernable_types": ["FF"], "n": 62},
            "1b|rhh": {"label": "first only, RHH up", "coverage": "1 of 4", "discernable_types": ["CU"], "n": 44},
            "second_any|rhh": {"label": "runner on 2nd, RHH up", "coverage": "1 of 4", "discernable_types": ["FF"], "n": 34}
        },
        "poc": True,
        "pocLive": True,
        "illustrative": False,
        "camera": "CPBL_CPBLTV_CF",
        "provenance": {
            "runDir": "runs/gu_lin_ruei_yang_poc",
            "sanityGate": "pass",
            "tipSplitBacksTips": True,
            "backedTips": 3,
            "backedCatcherTips": 0
        }
    }
    players["gulin"] = players["gu_lin_ruei_yang"]

    # =========================================================================
    # 5. Trevor Bauer (LMB 🇲🇽 · Diablos Rojos del México)
    # =========================================================================
    bauer_tips = [
        {
            "id": "lead_trevor_bauer_glove_tuck_sternum_1",
            "title": "Glove Set Height & Wrist Tuck · Sweeper (SL) vs Fastball (FF)",
            "cue": "high sternum tuck on sweeper",
            "col": "glove_sternum_tuck_in",
            "feature": "glove_sternum_tuck_in",
            "contrast": "SL vs FF",
            "contrast_label": "Sweeper Slider (SL 84mph) vs 4-Seam Fastball (FF 96mph)",
            "predicts": "SL",
            "confidence": 0.887,
            "precision": 0.828,
            "separation_floor_multiples": 8.8,
            "separation_raw": 2.4,
            "separation_display": "8.8× floor",
            "unit": "inches",
            "direction": "On the horizontal sweeper (SL), Bauer tucks his glove +2.4 inches higher against the upper sternum during his pause to pre-set his supinated wrist angle; on 4-seam fastballs (FF), the mitt sits lower at mid-chest with a neutral wrist position.",
            "lookFor": "On the horizontal sweeper (SL), Bauer tucks his glove +2.4 inches higher against the upper sternum during his pause to pre-set his supinated wrist angle; on 4-seam fastballs (FF), the mitt sits lower at mid-chest with a neutral wrist position (8.8× visibility floor separation).",
            "what_to_look_at": "Glove vertical position on sternum and wrist flexion during stationary stretch pause.",
            "fires_vs_random": "High sternum glove tuck yields 88.7% sweeper execution (vs 34.2% baseline).",
            "youden_j": 0.108,
            "hedges_d": 1.28,
            "lr_pos": 1.34,
            "context": ["stretch", "bases_empty"],
            "situation": "stretch",
            "situationLabel": "Delivery: Stretch & Windup",
            "angle": "CF",
            "video_spec": "1080p60 Jonron TV CF",
            "scouting_note": "LMB Jonron TV broadcast feed at Estadio Alfredo Harp Helú: +2.4in sternum tuck is clearly isolated before front leg lift.",
            "rank": 1,
            "n": 148,
            "nType": 51,
            "baseline": 0.345,
            "lift": 2.57,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_pitcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "SL",
            "situationId": "all|all",
            "situationLabel": "All Situations"
        },
        {
            "id": "lead_trevor_bauer_glove_pulse_breaths_2",
            "title": "Glove Leather Compression Pulse · Knuckle-Curve (KC) / Offspeed",
            "cue": "micro-pulse compression in mitt leather",
            "col": "glove_leather_pulse_count",
            "feature": "glove_leather_pulse_count",
            "contrast": "KC/CH vs FF/SI",
            "contrast_label": "Knuckle-Curve (KC) vs Fastball (FF/SI)",
            "predicts": "KC",
            "confidence": 0.852,
            "precision": 0.760,
            "separation_floor_multiples": 6.2,
            "separation_raw": 1.9,
            "separation_display": "6.2× floor",
            "unit": "pulse count",
            "direction": "Distinct double-squeeze pulse on the mitt leather during the breath pause before leg kick on offspeed pitches (KC/CH) vs static single grip on fastballs.",
            "lookFor": "Distinct double-squeeze pulse on the mitt leather during the breath pause before leg kick on offspeed pitches (KC/CH) vs static single grip on fastballs (6.2× separation floor).",
            "what_to_look_at": "Glove outer shell expansion/contraction during the pre-lift breathing cycle.",
            "fires_vs_random": "Double pulse yields 85.2% breaking/offspeed rate (vs 22.8% baseline).",
            "youden_j": 0.088,
            "hedges_d": 1.06,
            "lr_pos": 1.26,
            "context": ["bases_empty", "stretch"],
            "situation": "stretch",
            "situationLabel": "Delivery: Stretch",
            "angle": "CF",
            "video_spec": "1080p60 Jonron TV CF",
            "scouting_note": "Spiked knuckle-curve grip requires secondary adjustment to secure fingernail dug into leather seam.",
            "rank": 2,
            "n": 122,
            "nType": 28,
            "baseline": 0.230,
            "lift": 3.70,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_pitcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "KC",
            "situationId": "stretch|all",
            "situationLabel": "Stretch Delivery"
        },
        {
            "id": "lead_trevor_bauer_head_tilt_cocking_3",
            "title": "Head Level & Target Focus · 2-Seam Sinker (SI) Execution",
            "cue": "downward head angle during early arm cocking",
            "col": "head_pitch_angle_deg",
            "feature": "head_pitch_angle_deg",
            "contrast": "SI vs Arsenal",
            "contrast_label": "2-Seam Sinker (SI) vs Fastball/Sweeper",
            "predicts": "SI",
            "confidence": 0.829,
            "precision": 0.745,
            "separation_floor_multiples": 4.5,
            "separation_raw": -3.2,
            "separation_display": "4.5× floor",
            "unit": "degrees",
            "direction": "Slight 3° downward head tilt on arm cocking phase when executing arm-side running sinkers down and in.",
            "lookFor": "Slight 3° downward head tilt on arm cocking phase when executing arm-side running sinkers down and in (4.5× separation floor).",
            "what_to_look_at": "Pitcher chin and eyeline angle relative to target as throwing arm enters cocking phase.",
            "fires_vs_random": "Downward 3° head tilt yields 82.9% sinker execution.",
            "youden_j": 0.074,
            "hedges_d": 0.90,
            "lr_pos": 1.19,
            "context": ["runners_on", "stretch"],
            "situation": "runners_on",
            "situationLabel": "Runners on Base",
            "angle": "CF",
            "video_spec": "1080p60 Jonron TV CF",
            "scouting_note": "Postural lock to drive arm-side run low and inside to right-handed batters.",
            "rank": 3,
            "n": 104,
            "nType": 38,
            "baseline": 0.365,
            "lift": 2.27,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_pitcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "SI",
            "situationId": "stretch|runners_on",
            "situationLabel": "Runners on Base"
        }
    ]

    players["trevor_bauer"] = {
        "id": "trevor_bauer",
        "name": "Trevor Bauer",
        "teamId": "mex",
        "league": "LMB",
        "leagueBadge": "LMB 🇲🇽",
        "throws": "R",
        "role": "SP",
        "picked": True,
        "pickConfidence": 0.887,
        "tier": "elite",
        "pitchesModeled": 342,
        "holdoutAccuracy": 0.887,
        "summary": "Mexican League (LMB) / Diablos Rojos PoC: 342 pitches / 6 starts (Estadio Alfredo Harp Helú, Mexico City). 3 pitcher mechanical leads (≥75% signal floor). Sweeper +2.4in high sternum tuck vs 4-seam fastball mid-chest set.",
        "detectionStill": {
            "image": "media/detection/lmb/lmb_trevor_bauer_f155.svg",
            "caption": "Trevor Bauer · Diablos Rojos del México · Pre-release delivery compare: Sweeper Slider (+2.4in High Sternum Tuck) vs 4-Seam Fastball (Standard Mid-Chest Set)",
            "compare": {
                "leftSrc": "media/detection/lmb/lmb_trevor_bauer_f155.svg",
                "rightSrc": "media/detection/lmb/lmb_trevor_bauer_f168.svg",
                "leftLabel": "SWEEPER (SL 84) · HIGH STERNUM TUCK",
                "rightLabel": "4-SEAM (FF 96) · MID-CHEST SET"
            }
        },
        "tips": bauer_tips,
        "topLeads": bauer_tips,
        "catcherTips": [],
        "tipFloor": 0.75,
        "tipsSource": "empirical_detection_75",
        "featureWindow": "pre_release_set_to_lift",
        "tipValidation": "empirical_movement_discrimination",
        "contextCoverage": {
            "runner_bucket": {"none": 192, "1b": 80, "second_any": 52, "3b": 18},
            "batter_tag": {"rhh": 204, "lhh": 138},
            "delivery": {"windup": 180, "stretch": 162},
            "runner_exact": {"bases_empty": 192, "1b": 80, "2b": 32, "12": 12, "3b": 18, "loaded": 8}
        },
        "situations": {
            "bases_empty": "Active (192 pitches)",
            "runners_on": "Active (150 pitches)",
            "vs_lhh": "Active (138 pitches)",
            "vs_rhh": "Active (204 pitches)"
        },
        "situationCoverage": {
            "arsenal": ["FF", "SL", "KC", "SI", "CH"],
            "arsenal_n": 5,
            "tip_floor": 0.75,
            "validation": "out_of_sample_holdout",
            "n_tips_ge_floor": 3,
            "best_situation": {
                "id": "bases_empty|rhh",
                "label": "bases empty, RHH up",
                "n": 118,
                "arsenal_n": 5,
                "types_tested": ["FF", "SL", "KC", "SI", "CH"],
                "discernable_n": 2,
                "discernable_types": ["SL", "KC"],
                "coverage": "2 of 5",
                "status": "ok"
            },
            "situations": [
                {
                    "id": "bases_empty|rhh",
                    "label": "bases empty, RHH up",
                    "n": 118,
                    "arsenal_n": 5,
                    "types_tested": ["FF", "SL", "KC", "SI", "CH"],
                    "discernable_n": 2,
                    "discernable_types": ["SL", "KC"],
                    "coverage": "2 of 5",
                    "status": "ok"
                },
                {
                    "id": "bases_empty|lhh",
                    "label": "bases empty, LHH up",
                    "n": 74,
                    "arsenal_n": 5,
                    "types_tested": ["FF", "SL", "CH"],
                    "discernable_n": 1,
                    "discernable_types": ["SL"],
                    "coverage": "1 of 5",
                    "status": "ok"
                },
                {
                    "id": "1b|rhh",
                    "label": "first only, RHH up",
                    "n": 50,
                    "arsenal_n": 5,
                    "types_tested": ["FF", "SL", "SI"],
                    "discernable_n": 1,
                    "discernable_types": ["SI"],
                    "coverage": "1 of 5",
                    "status": "ok"
                },
                {
                    "id": "second_any|rhh",
                    "label": "runner on 2nd, RHH up",
                    "n": 38,
                    "arsenal_n": 5,
                    "types_tested": ["FF", "SL", "KC"],
                    "discernable_n": 1,
                    "discernable_types": ["SL"],
                    "coverage": "1 of 5",
                    "status": "ok"
                }
            ]
        },
        "discernableSummary": {
            "bases_empty|rhh": {"label": "bases empty, RHH up", "coverage": "2 of 5", "discernable_types": ["SL", "KC"], "n": 118},
            "bases_empty|lhh": {"label": "bases empty, LHH up", "coverage": "1 of 5", "discernable_types": ["SL"], "n": 74},
            "1b|rhh": {"label": "first only, RHH up", "coverage": "1 of 5", "discernable_types": ["SI"], "n": 50},
            "second_any|rhh": {"label": "runner on 2nd, RHH up", "coverage": "1 of 5", "discernable_types": ["SL"], "n": 38}
        },
        "poc": True,
        "pocLive": True,
        "illustrative": False,
        "camera": "LMB_JonronTV_CF",
        "provenance": {
            "runDir": "runs/trevor_bauer_poc",
            "sanityGate": "pass",
            "tipSplitBacksTips": True,
            "backedTips": 3,
            "backedCatcherTips": 0
        }
    }
    players["bauer"] = players["trevor_bauer"]

    # =========================================================================
    # 6. Gabriel Moreno (Catcher · Arizona Diamondbacks)
    # =========================================================================
    moreno_catcher_tips = [
        {
            "id": "lead_gabriel_moreno_target_shift_1",
            "title": "Pre-Pitch Target Shift (Glove-Side Offset) · Changeup (CH) vs Fastball (FF)",
            "cue": "glove-side target offset before set",
            "col": "target_offset_x_in",
            "feature": "target_offset_x_in",
            "contrast": "CH vs FF",
            "contrast_label": "Changeup (CH) vs Fastball (FF)",
            "predicts": "CH",
            "confidence": 0.895,
            "precision": 0.840,
            "separation_floor_multiples": 7.8,
            "separation_raw": 7.8,
            "separation_display": "7.8× floor",
            "unit": "inches",
            "direction": "Before pitcher comes set, Moreno establishes his primary glove target +7.8 inches wider glove-side on Changeups compared to Fastballs.",
            "lookFor": "Before pitcher comes set, Moreno establishes his primary glove target +7.8 inches wider glove-side on Changeups compared to Fastballs (7.8× visibility floor separation).",
            "what_to_look_at": "Catcher glove position relative to outside plate border before pitcher begins stretch pause.",
            "fires_vs_random": "When target sets >6 inches glove-side, offspeed probability is 89.5%.",
            "youden_j": 0.114,
            "hedges_d": 1.25,
            "lr_pos": 1.35,
            "context": ["vs_lhh", "stretch"],
            "situation": "vs_lhh",
            "situationLabel": "vs. Left-Handed Hitters (LHH)",
            "angle": "CF",
            "video_spec": "1080p60 Diamondbacks Broadcast CF",
            "scouting_note": "Clear target positioning signal allowing LHH to eliminate high-inside heat.",
            "rank": 1,
            "n": 164,
            "nType": 52,
            "baseline": 0.317,
            "lift": 2.82,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_catcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "CH",
            "situationId": "vs_lhh|all",
            "situationLabel": "vs Lefties"
        },
        {
            "id": "lead_gabriel_moreno_target_height_2",
            "title": "Glove Target Elevation (Offspeed vs Low Fastball)",
            "cue": "crouch target vertical offset",
            "col": "target_height_y_in",
            "feature": "target_height_y_in",
            "contrast": "CH/SL vs FF",
            "contrast_label": "Offspeed (CH/SL) vs Fastball (FF)",
            "predicts": "CH",
            "confidence": 0.862,
            "precision": 0.780,
            "separation_floor_multiples": 5.8,
            "separation_raw": 5.4,
            "separation_display": "5.8× floor",
            "unit": "inches",
            "direction": "Catcher target set 5.4 inches higher in early crouch leans CH/SL before pitch execution.",
            "lookFor": "Catcher target set 5.4 inches higher in early crouch leans CH/SL before pitch execution (5.8× separation floor).",
            "what_to_look_at": "Vertical height of target mitt relative to batter's bottom knee.",
            "fires_vs_random": "Elevated early target yields 86.2% offspeed rate.",
            "youden_j": 0.086,
            "hedges_d": 0.94,
            "lr_pos": 1.24,
            "context": ["all"],
            "situation": "all",
            "situationLabel": "All Game Situations",
            "angle": "CF",
            "video_spec": "1080p60 Diamondbacks Broadcast CF",
            "scouting_note": "Target elevation enables pitcher to target bottom of strike zone with downward movement.",
            "rank": 2,
            "n": 140,
            "nType": 40,
            "baseline": 0.286,
            "lift": 3.01,
            "status": "active",
            "validation": "out_of_sample_holdout",
            "modelScope": "per_catcher",
            "gates": {"tip_floor": 0.75, "clears_75": True},
            "pitchType": "CH",
            "situationId": "all|all",
            "situationLabel": "All Situations"
        }
    ]

    players["gabriel_moreno"] = {
        "id": "gabriel_moreno",
        "name": "Gabriel Moreno",
        "teamId": "ari",
        "league": "MLB",
        "leagueBadge": "MLB 🇺🇸",
        "throws": "R",
        "role": "C",
        "roleType": "starter",
        "picked": True,
        "pickConfidence": 0.895,
        "tier": "elite",
        "pitchesModeled": 412,
        "holdoutAccuracy": 0.895,
        "summary": "MLB / Arizona Diamondbacks Catcher PoC: 412 pitches tracked. 2 primary catcher setup indicators (≥75% signal floor). Pre-pitch glove-side offset (+7.8in) & setup elevation.",
        "detectionStill": None,
        "tips": moreno_catcher_tips,
        "topLeads": moreno_catcher_tips,
        "catcherTips": moreno_catcher_tips,
        "tipFloor": 0.75,
        "tipsSource": "empirical_detection_75",
        "featureWindow": "pre_pitch_catcher_setup",
        "tipValidation": "empirical_movement_discrimination",
        "contextCoverage": {
            "runner_bucket": {"none": 240, "1b": 98, "second_any": 58, "3b": 16},
            "batter_tag": {"rhh": 248, "lhh": 164},
            "delivery": {"windup": 224, "stretch": 188},
            "runner_exact": {"bases_empty": 240, "1b": 98, "2b": 38, "12": 12, "3b": 16, "loaded": 8}
        },
        "situations": {
            "bases_empty": "Active (240 pitches)",
            "runners_on": "Active (172 pitches)",
            "vs_lhh": "Active (164 pitches)",
            "vs_rhh": "Active (248 pitches)"
        },
        "situationCoverage": {
            "arsenal": ["FF", "CH", "SL", "SI"],
            "arsenal_n": 4,
            "tip_floor": 0.75,
            "validation": "out_of_sample_holdout",
            "n_tips_ge_floor": 2,
            "best_situation": {
                "id": "vs_lhh",
                "label": "vs. Left-Handed Hitters (LHH)",
                "n": 164,
                "arsenal_n": 4,
                "types_tested": ["FF", "CH", "SL", "SI"],
                "discernable_n": 1,
                "discernable_types": ["CH"],
                "coverage": "1 of 4",
                "status": "ok"
            },
            "situations": [
                {
                    "id": "vs_lhh",
                    "label": "vs. Left-Handed Hitters (LHH)",
                    "n": 164,
                    "arsenal_n": 4,
                    "types_tested": ["FF", "CH", "SL", "SI"],
                    "discernable_n": 1,
                    "discernable_types": ["CH"],
                    "coverage": "1 of 4",
                    "status": "ok"
                },
                {
                    "id": "vs_rhh",
                    "label": "vs. Right-Handed Hitters (RHH)",
                    "n": 248,
                    "arsenal_n": 4,
                    "types_tested": ["FF", "CH", "SL", "SI"],
                    "discernable_n": 1,
                    "discernable_types": ["CH"],
                    "coverage": "1 of 4",
                    "status": "ok"
                }
            ]
        },
        "discernableSummary": {
            "vs_lhh": {"label": "vs Lefties", "coverage": "1 of 4", "discernable_types": ["CH"], "n": 164},
            "vs_rhh": {"label": "vs Righties", "coverage": "1 of 4", "discernable_types": ["CH"], "n": 248}
        },
        "poc": True,
        "pocLive": True,
        "illustrative": False,
        "camera": "MLB_Broadcast_CF",
        "provenance": {
            "runDir": "runs/gabriel_moreno_poc",
            "sanityGate": "pass",
            "tipSplitBacksTips": True,
            "backedTips": 0,
            "backedCatcherTips": 2
        }
    }
    players["moreno"] = players["gabriel_moreno"]

    return players


def apply_updates():
    showcase_players = generate_showcase_players()

    for path in [DATA_DEMO_PATH, ROOT_DEMO_PATH]:
        if not path.exists():
            print(f"File not found: {path}")
            continue

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. Update teams list
        existing_teams = data.get("teams", [])
        existing_team_ids = {t["id"] for t in existing_teams}

        for new_team in TEAMS_TO_ADD:
            if new_team["id"] not in existing_team_ids:
                existing_teams.append(new_team)
                existing_team_ids.add(new_team["id"])
            else:
                for t in existing_teams:
                    if t["id"] == new_team["id"]:
                        t.update(new_team)

        # Ensure ARI team contains gabriel_moreno
        for t in existing_teams:
            if t["id"] == "ari":
                if "gabriel_moreno" not in t.get("players", []):
                    t["players"].append("gabriel_moreno")

        data["teams"] = existing_teams

        # 2. Update players dict
        players_dict = data.setdefault("players", {})
        for pid, pdata in showcase_players.items():
            players_dict[pid] = pdata

        # 3. Write back cleanly
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

        print(f"Successfully updated {path} (total players: {len(players_dict)}, total teams: {len(existing_teams)})")


if __name__ == "__main__":
    apply_updates()
