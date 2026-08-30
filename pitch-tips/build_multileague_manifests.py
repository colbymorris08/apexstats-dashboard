#!/usr/bin/env python3
"""
Generate multi-league calibration manifests and representative frame visuals
for Preflight Computer Vision angle calibration across 5 leagues:
- NCAA D1 (College)
- NPB (Japan)
- KBO (Korea)
- CPBL (Taiwan)
- LMB (Mexico)
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media", "detection")
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)
for sub in ["ncaa", "npb", "kbo", "cpbl", "lmb"]:
    os.makedirs(os.path.join(MEDIA_DIR, sub), exist_ok=True)

CLASSES = [
    {"id": "pitcher_glove", "label": "Pitcher glove", "color": "#ff8c00"},
    {"id": "bare_hand", "label": "Bare hand (visible / in-glove burial)", "color": "#f0c040"},
    {"id": "pitcher_torso", "label": "Pitcher torso / chest alignment", "color": "#5ec8ff"},
    {"id": "pitcher_head", "label": "Pitcher head / cheek", "color": "#ff6b9d"},
    {"id": "knee", "label": "Knee / leg lift apex", "color": "#9b8cff"},
    {"id": "forearm", "label": "Throwing forearm / wrist angle", "color": "#3ecf8e"},
    {"id": "catcher_mitt", "label": "Catcher mitt / target", "color": "#70af5f"},
    {"id": "catcher_mask", "label": "Catcher mask / helmet", "color": "#c0c0c0"},
    {"id": "catcher_shin", "label": "Catcher shin guard", "color": "#88a0b8"},
    {"id": "plate", "label": "Home plate", "color": "#ffffff"}
]

LEAGUE_FRAMES = {
    "ncaa": [
        {
            "id": "ncaa_chase_burns_wake_01",
            "pitcher": "Chase Burns",
            "team": "Wake Forest (ACC)",
            "league": "NCAA",
            "stadium": "David F. Couch Ballpark · Winston-Salem, NC",
            "lighting": "Sunny Day (High Sun)",
            "jersey": "Black / Vegas Gold (#111111 / #c5a059)",
            "throws": "RHP",
            "angle": "High 3/4 Center-Field",
            "pitchType": "4-Seam Fastball (FF)",
            "delivery": "Stretch Set (Upper Chest Anchor)",
            "windowPos": 0.25,
            "filename": "ncaa/ncaa_chase_burns_f104.svg",
            "gloveX": 645, "gloveY": 348, "handX": 655, "handY": 352,
            "torsoX": 640, "torsoY": 370, "headX": 640, "headY": 295,
            "kneeX": 635, "kneeY": 445, "catcherX": 730, "catcherY": 380,
            "bgTheme": "day_turf", "skyColor": "#2a4d69", "fieldColor": "#1e3a1e"
        },
        {
            "id": "ncaa_chase_burns_wake_02",
            "pitcher": "Chase Burns",
            "team": "Wake Forest (ACC)",
            "league": "NCAA",
            "stadium": "David F. Couch Ballpark · Winston-Salem, NC",
            "lighting": "Day Sun · Contrast Shadow",
            "jersey": "Black / Vegas Gold (#111111 / #c5a059)",
            "throws": "RHP",
            "angle": "High 3/4 Center-Field",
            "pitchType": "Slider (SL)",
            "delivery": "Stretch Set (Belt Line Anchor)",
            "windowPos": 0.35,
            "filename": "ncaa/ncaa_chase_burns_f118.svg",
            "gloveX": 645, "gloveY": 382, "handX": 655, "handY": 385,
            "torsoX": 640, "torsoY": 370, "headX": 640, "headY": 295,
            "kneeX": 635, "kneeY": 445, "catcherX": 730, "catcherY": 385,
            "bgTheme": "day_turf", "skyColor": "#2a4d69", "fieldColor": "#1e3a1e"
        },
        {
            "id": "ncaa_hagen_smith_ark_01",
            "pitcher": "Hagen Smith",
            "team": "Arkansas (SEC)",
            "league": "NCAA",
            "stadium": "Baum-Walker Stadium · Fayetteville, AR",
            "lighting": "Night Floodlights (High Lux)",
            "jersey": "Cardinal Red / White (#9d2235 / #ffffff)",
            "throws": "LHP",
            "angle": "Low Broadcast CF",
            "pitchType": "Slider (SL)",
            "delivery": "Deceptive Cross-Body Leg Kick",
            "windowPos": 0.65,
            "filename": "ncaa/ncaa_hagen_smith_f088.svg",
            "gloveX": 630, "gloveY": 340, "handX": 620, "handY": 345,
            "torsoX": 635, "torsoY": 365, "headX": 638, "headY": 290,
            "kneeX": 665, "kneeY": 410, "catcherX": 555, "catcherY": 380,
            "bgTheme": "night_stadium", "skyColor": "#0b1326", "fieldColor": "#142d14"
        },
        {
            "id": "ncaa_jac_caglianone_fla_01",
            "pitcher": "Jac Caglianone",
            "team": "Florida (SEC)",
            "league": "NCAA",
            "stadium": "Condron Family Ballpark · Gainesville, FL",
            "lighting": "Twilight Stadium Glow",
            "jersey": "Royal Blue / Orange (#0021a5 / #fa4616)",
            "throws": "LHP",
            "angle": "High Offset Center-Field",
            "pitchType": "4-Seam Fastball (FF 99mph)",
            "delivery": "Power Windup Peak Knee Lift",
            "windowPos": 0.82,
            "filename": "ncaa/ncaa_jac_caglianone_f072.svg",
            "gloveX": 625, "gloveY": 325, "handX": 618, "handY": 328,
            "torsoX": 630, "torsoY": 355, "headX": 632, "headY": 285,
            "kneeX": 670, "kneeY": 375, "catcherX": 550, "catcherY": 390,
            "bgTheme": "twilight", "skyColor": "#181f38", "fieldColor": "#183218"
        },
        {
            "id": "ncaa_paul_skenes_lsu_01",
            "pitcher": "Paul Skenes",
            "team": "LSU (SEC)",
            "league": "NCAA",
            "stadium": "Alex Box Stadium · Baton Rouge, LA",
            "lighting": "Night SEC Broadcast Lights",
            "jersey": "Purple / Gold (#461d7c / #fdd023)",
            "throws": "RHP",
            "angle": "Tight Center-Field Lens",
            "pitchType": "Splinker / 4-Seam (101mph)",
            "delivery": "High Set Presentation",
            "windowPos": 0.20,
            "filename": "ncaa/ncaa_paul_skenes_f094.svg",
            "gloveX": 642, "gloveY": 332, "handX": 650, "handY": 336,
            "torsoX": 638, "torsoY": 360, "headX": 638, "headY": 280,
            "kneeX": 632, "kneeY": 440, "catcherX": 735, "catcherY": 378,
            "bgTheme": "night_stadium", "skyColor": "#080e1e", "fieldColor": "#122a12"
        },
        {
            "id": "ncaa_trey_yesavage_ecu_01",
            "pitcher": "Trey Yesavage",
            "team": "East Carolina (AAC)",
            "league": "NCAA",
            "stadium": "Clark-LeClair Stadium · Greenville, NC",
            "lighting": "Overcast Afternoon",
            "jersey": "Purple / Gold (#592a8a / #fec923)",
            "throws": "RHP",
            "angle": "High Press Box Center-Field",
            "pitchType": "Spike Curveball (CU)",
            "delivery": "Over-the-Head High Arm Slot Set",
            "windowPos": 0.30,
            "filename": "ncaa/ncaa_trey_yesavage_f065.svg",
            "gloveX": 640, "gloveY": 328, "handX": 648, "handY": 330,
            "torsoX": 638, "torsoY": 358, "headX": 638, "headY": 288,
            "kneeX": 635, "kneeY": 435, "catcherX": 728, "catcherY": 382,
            "bgTheme": "day_overcast", "skyColor": "#323e4d", "fieldColor": "#1a351a"
        },
        {
            "id": "ncaa_brody_brecht_iowa_01",
            "pitcher": "Brody Brecht",
            "team": "Iowa (Big Ten)",
            "league": "NCAA",
            "stadium": "Duane Banks Field · Iowa City, IA",
            "lighting": "Day Turf Sunlight",
            "jersey": "Black / Gold (#000000 / #ffe100)",
            "throws": "RHP",
            "angle": "Standard CF Broadcast",
            "pitchType": "Slider (89mph)",
            "delivery": "Compact Stretch Lock",
            "windowPos": 0.40,
            "filename": "ncaa/ncaa_brody_brecht_f051.svg",
            "gloveX": 644, "gloveY": 355, "handX": 652, "handY": 358,
            "torsoX": 640, "torsoY": 372, "headX": 640, "headY": 295,
            "kneeX": 635, "kneeY": 448, "catcherX": 732, "catcherY": 385,
            "bgTheme": "day_turf", "skyColor": "#224263", "fieldColor": "#1e3c1e"
        },
        {
            "id": "ncaa_cam_caminiti_lsu_01",
            "pitcher": "Cam Caminiti",
            "team": "LSU / National (SEC)",
            "league": "NCAA",
            "stadium": "Alex Box Stadium · Baton Rouge, LA",
            "lighting": "Day Sun Pinstripe Glare",
            "jersey": "White Pinstripes / Purple (#ffffff / #461d7c)",
            "throws": "LHP",
            "angle": "High 3/4 Center-Field",
            "pitchType": "4-Seam Fastball (FF)",
            "delivery": "Smooth Early Leg Kick",
            "windowPos": 0.55,
            "filename": "ncaa/ncaa_cam_caminiti_f077.svg",
            "gloveX": 632, "gloveY": 344, "handX": 622, "handY": 348,
            "torsoX": 636, "torsoY": 368, "headX": 638, "headY": 292,
            "kneeX": 662, "kneeY": 425, "catcherX": 552, "catcherY": 382,
            "bgTheme": "day_sun", "skyColor": "#1d3d5e", "fieldColor": "#204220"
        },
        {
            "id": "ncaa_christian_coppola_rut_01",
            "pitcher": "Christian Coppola",
            "team": "Rutgers (Big Ten)",
            "league": "NCAA",
            "stadium": "Bainton Field · Piscataway, NJ",
            "lighting": "Night Lights Turf",
            "jersey": "Scarlet Red / Black (#cc0033 / #000000)",
            "throws": "RHP",
            "angle": "Elevated CF",
            "pitchType": "Cutter (FC)",
            "delivery": "Chest-Level Set Pause",
            "windowPos": 0.18,
            "filename": "ncaa/ncaa_christian_coppola_f043.svg",
            "gloveX": 643, "gloveY": 348, "handX": 651, "handY": 352,
            "torsoX": 639, "torsoY": 368, "headX": 639, "headY": 294,
            "kneeX": 634, "kneeY": 442, "catcherX": 730, "catcherY": 384,
            "bgTheme": "night_stadium", "skyColor": "#0c1524", "fieldColor": "#152d15"
        },
        {
            "id": "ncaa_josh_hartle_wake_01",
            "pitcher": "Josh Hartle",
            "team": "Wake Forest (ACC)",
            "league": "NCAA",
            "stadium": "David F. Couch Ballpark · Winston-Salem, NC",
            "lighting": "Afternoon Turf Glow",
            "jersey": "Vegas Gold / Black (#c5a059 / #000000)",
            "throws": "LHP",
            "angle": "Low Set Center-Field",
            "pitchType": "Cutter / Slider (FC/SL)",
            "delivery": "Cross-Fire Stretch Pause",
            "windowPos": 0.22,
            "filename": "ncaa/ncaa_josh_hartle_f086.svg",
            "gloveX": 634, "gloveY": 356, "handX": 625, "handY": 358,
            "torsoX": 638, "torsoY": 372, "headX": 640, "headY": 296,
            "kneeX": 658, "kneeY": 446, "catcherX": 556, "catcherY": 386,
            "bgTheme": "day_turf", "skyColor": "#244466", "fieldColor": "#1b3a1b"
        },
        {
            "id": "ncaa_ryan_johnson_dbu_01",
            "pitcher": "Ryan Johnson",
            "team": "Dallas Baptist (C-USA)",
            "league": "NCAA",
            "stadium": "Horner Ballpark · Dallas, TX",
            "lighting": "Texas Sunset Horizon",
            "jersey": "Navy / Red (#002d62 / #ba0c2f)",
            "throws": "RHP",
            "angle": "Standard CF Broadcast",
            "pitchType": "Power Sinker (SI 97mph)",
            "delivery": "Sidearm Drop Windup Set",
            "windowPos": 0.38,
            "filename": "ncaa/ncaa_ryan_johnson_f059.svg",
            "gloveX": 646, "gloveY": 365, "handX": 655, "handY": 368,
            "torsoX": 640, "torsoY": 375, "headX": 640, "headY": 298,
            "kneeX": 632, "kneeY": 448, "catcherX": 732, "catcherY": 385,
            "bgTheme": "twilight", "skyColor": "#1c223c", "fieldColor": "#163016"
        },
        {
            "id": "ncaa_thatcher_hurd_lsu_01",
            "pitcher": "Thatcher Hurd",
            "team": "LSU (SEC)",
            "league": "NCAA",
            "stadium": "Alex Box Stadium · Baton Rouge, LA",
            "lighting": "Night Shadows Under Lights",
            "jersey": "Gold / Purple (#fdd023 / #461d7c)",
            "throws": "RHP",
            "angle": "Deep Center-Field Offset",
            "pitchType": "Curveball (CU)",
            "delivery": "High Leg Kick Coil",
            "windowPos": 0.72,
            "filename": "ncaa/ncaa_thatcher_hurd_f114.svg",
            "gloveX": 641, "gloveY": 336, "handX": 649, "handY": 338,
            "torsoX": 637, "torsoY": 362, "headX": 637, "headY": 286,
            "kneeX": 612, "kneeY": 395, "catcherX": 730, "catcherY": 380,
            "bgTheme": "night_stadium", "skyColor": "#091020", "fieldColor": "#112611"
        }
    ],
    "npb": [
        {
            "id": "npb_roki_sasaki_chiba_01",
            "pitcher": "Roki Sasaki",
            "team": "Chiba Lotte Marines",
            "league": "NPB",
            "stadium": "ZOZO Marine Stadium · Chiba, Japan",
            "lighting": "Coastal Sea Breeze Night Lights",
            "jersey": "Black Pinstripes (#000000 / #ffffff)",
            "throws": "RHP",
            "angle": "Tight Center-Field Lens (NPB Savant)",
            "pitchType": "Forkball / Splitter (FS)",
            "delivery": "Deep Wrist Burial at Set (1.8in Penetration)",
            "windowPos": 0.22,
            "filename": "npb/npb_roki_sasaki_f142.svg",
            "gloveX": 644, "gloveY": 352, "handX": 654, "handY": 355,
            "torsoX": 640, "torsoY": 370, "headX": 640, "headY": 292,
            "kneeX": 634, "kneeY": 444, "catcherX": 732, "catcherY": 382,
            "bgTheme": "night_stadium", "skyColor": "#0a1322", "fieldColor": "#132d13"
        },
        {
            "id": "npb_roki_sasaki_chiba_02",
            "pitcher": "Roki Sasaki",
            "team": "Chiba Lotte Marines",
            "league": "NPB",
            "stadium": "ZOZO Marine Stadium · Chiba, Japan",
            "lighting": "Coastal Night Lighting",
            "jersey": "Black Pinstripes (#000000 / #ffffff)",
            "throws": "RHP",
            "angle": "Tight Center-Field Lens",
            "pitchType": "4-Seam Fastball (FF 102mph)",
            "delivery": "Upright Glove Thumb Set (Shallow Burial)",
            "windowPos": 0.24,
            "filename": "npb/npb_roki_sasaki_f156.svg",
            "gloveX": 644, "gloveY": 338, "handX": 652, "handY": 340,
            "torsoX": 640, "torsoY": 368, "headX": 640, "headY": 292,
            "kneeX": 634, "kneeY": 444, "catcherX": 732, "catcherY": 378,
            "bgTheme": "night_stadium", "skyColor": "#0a1322", "fieldColor": "#132d13"
        },
        {
            "id": "npb_yoshinobu_yamamoto_orix_01",
            "pitcher": "Yoshinobu Yamamoto",
            "team": "Orix Buffaloes",
            "league": "NPB",
            "stadium": "Kyocera Dome Osaka · Osaka, Japan",
            "lighting": "Indoor Dome Diffuse Lighting",
            "jersey": "Navy / Gold (#0b1f3a / #d4af37)",
            "throws": "RHP",
            "angle": "Mid Center-Field Angle",
            "pitchType": "Rainbow Curveball (CU)",
            "delivery": "Javelin Slide Step Quick Settle",
            "windowPos": 0.32,
            "filename": "npb/npb_yoshinobu_yamamoto_f096.svg",
            "gloveX": 642, "gloveY": 346, "handX": 650, "handY": 349,
            "torsoX": 639, "torsoY": 366, "headX": 639, "headY": 290,
            "kneeX": 636, "kneeY": 440, "catcherX": 730, "catcherY": 380,
            "bgTheme": "dome_indoor", "skyColor": "#1a2434", "fieldColor": "#1b351b"
        },
        {
            "id": "npb_shota_imanaga_dena_01",
            "pitcher": "Shota Imanaga",
            "team": "Yokohama DeNA BayStars",
            "league": "NPB",
            "stadium": "Yokohama Stadium · Kanagawa, Japan",
            "lighting": "Outdoor Night Lights",
            "jersey": "Yokohama Blue / White (#003b7a / #ffffff)",
            "throws": "LHP",
            "angle": "Low CF Broadcast Lens",
            "pitchType": "Rising 4-Seam (FF)",
            "delivery": "Compact Left-Handed Set Presentation",
            "windowPos": 0.28,
            "filename": "npb/npb_shota_imanaga_f082.svg",
            "gloveX": 632, "gloveY": 348, "handX": 622, "handY": 352,
            "torsoX": 636, "torsoY": 368, "headX": 638, "headY": 294,
            "kneeX": 660, "kneeY": 444, "catcherX": 554, "catcherY": 384,
            "bgTheme": "night_stadium", "skyColor": "#0c182b", "fieldColor": "#142c14"
        },
        {
            "id": "npb_hiroya_miyagi_orix_01",
            "pitcher": "Hiroya Miyagi",
            "team": "Orix Buffaloes",
            "league": "NPB",
            "stadium": "Kyocera Dome Osaka · Osaka, Japan",
            "lighting": "Dome Floodlights",
            "jersey": "Gold / Navy (#d4af37 / #0b1f3a)",
            "throws": "LHP",
            "angle": "Low 3/4 Release CF",
            "pitchType": "Slow Curveball (62mph)",
            "delivery": "High Front Knee Tuck",
            "windowPos": 0.76,
            "filename": "npb/npb_hiroya_miyagi_f105.svg",
            "gloveX": 630, "gloveY": 338, "handX": 620, "handY": 342,
            "torsoX": 634, "torsoY": 364, "headX": 636, "headY": 292,
            "kneeX": 672, "kneeY": 390, "catcherX": 550, "catcherY": 388,
            "bgTheme": "dome_indoor", "skyColor": "#192230", "fieldColor": "#1a331a"
        },
        {
            "id": "npb_shunpeita_yamashita_orix_01",
            "pitcher": "Shunpeita Yamashita",
            "team": "Orix Buffaloes",
            "league": "NPB",
            "stadium": "Kyocera Dome Osaka · Osaka, Japan",
            "lighting": "Dome Overhead Array",
            "jersey": "Navy / Gold (#0b1f3a / #d4af37)",
            "throws": "RHP",
            "angle": "High Power Angle CF",
            "pitchType": "Power Curveball (CU 86mph)",
            "delivery": "Chest-High Glove Tuck",
            "windowPos": 0.36,
            "filename": "npb/npb_shunpeita_yamashita_f068.svg",
            "gloveX": 643, "gloveY": 335, "handX": 651, "handY": 338,
            "torsoX": 639, "torsoY": 362, "headX": 639, "headY": 284,
            "kneeX": 634, "kneeY": 438, "catcherX": 730, "catcherY": 378,
            "bgTheme": "dome_indoor", "skyColor": "#1a2232", "fieldColor": "#1b331b"
        },
        {
            "id": "npb_kaima_taira_seibu_01",
            "pitcher": "Kaima Taira",
            "team": "Saitama Seibu Lions",
            "league": "NPB",
            "stadium": "Belluna Dome · Saitama, Japan",
            "lighting": "Semi-Open Dome Twilight Breeze",
            "jersey": "Legend Navy (#002244)",
            "throws": "RHP",
            "angle": "Standard CF Broadcast",
            "pitchType": "Splitter / Sinker (FS/SI)",
            "delivery": "Stocky Low Torso Coil",
            "windowPos": 0.44,
            "filename": "npb/npb_kaima_taira_f073.svg",
            "gloveX": 645, "gloveY": 362, "handX": 655, "handY": 366,
            "torsoX": 640, "torsoY": 374, "headX": 640, "headY": 298,
            "kneeX": 632, "kneeY": 446, "catcherX": 732, "catcherY": 386,
            "bgTheme": "twilight", "skyColor": "#151e2e", "fieldColor": "#163116"
        },
        {
            "id": "npb_hiromi_itoh_fighters_01",
            "pitcher": "Hiromi Itoh",
            "team": "Hokkaido Nippon-Ham Fighters",
            "league": "NPB",
            "stadium": "ES CON FIELD HOKKAIDO · Kitahiroshima, Japan",
            "lighting": "Retractable Roof Glass Sunlight",
            "jersey": "Fighters Blue / Black (#003366 / #111111)",
            "throws": "RHP",
            "angle": "High Center CF Lens",
            "pitchType": "Sweeper (ST)",
            "delivery": "Rosin Dust High Glove Tap",
            "windowPos": 0.16,
            "filename": "npb/npb_hiromi_itoh_f091.svg",
            "gloveX": 643, "gloveY": 326, "handX": 650, "handY": 328,
            "torsoX": 639, "torsoY": 358, "headX": 639, "headY": 286,
            "kneeX": 635, "kneeY": 436, "catcherX": 730, "catcherY": 378,
            "bgTheme": "dome_glass", "skyColor": "#223a54", "fieldColor": "#1d3a1d"
        },
        {
            "id": "npb_yuki_matsui_rakuten_01",
            "pitcher": "Yuki Matsui",
            "team": "Tohoku Rakuten Golden Eagles",
            "league": "NPB",
            "stadium": "Rakuten Mobile Park Miyagi · Sendai, Japan",
            "lighting": "Cold Outdoor Night Lights",
            "jersey": "Crimson Red / Gold (#860010 / #d4af37)",
            "throws": "LHP",
            "angle": "Standard CF Broadcast",
            "pitchType": "Splitter / Slider (FS/SL)",
            "delivery": "Deep Crouch Set Presentation",
            "windowPos": 0.26,
            "filename": "npb/npb_yuki_matsui_f062.svg",
            "gloveX": 632, "gloveY": 356, "handX": 622, "handY": 360,
            "torsoX": 636, "torsoY": 372, "headX": 638, "headY": 298,
            "kneeX": 660, "kneeY": 446, "catcherX": 554, "catcherY": 386,
            "bgTheme": "night_stadium", "skyColor": "#0a111e", "fieldColor": "#122712"
        },
        {
            "id": "npb_shinnosuke_ogasawara_dragons_01",
            "pitcher": "Shinnosuke Ogasawara",
            "team": "Chunichi Dragons",
            "league": "NPB",
            "stadium": "Vantelin Dome Nagoya · Nagoya, Japan",
            "lighting": "Dome Diffuse Glow",
            "jersey": "Dragons Royal Blue (#002b66)",
            "throws": "LHP",
            "angle": "3/4 Center-Field",
            "pitchType": "Changeup (CH)",
            "delivery": "Belt-Line Stretch Lock",
            "windowPos": 0.34,
            "filename": "npb/npb_shinnosuke_ogasawara_f054.svg",
            "gloveX": 634, "gloveY": 362, "handX": 624, "handY": 365,
            "torsoX": 638, "torsoY": 374, "headX": 639, "headY": 298,
            "kneeX": 658, "kneeY": 448, "catcherX": 556, "catcherY": 388,
            "bgTheme": "dome_indoor", "skyColor": "#17202e", "fieldColor": "#193119"
        },
        {
            "id": "npb_kodai_senga_hawks_01",
            "pitcher": "Kodai Senga",
            "team": "Fukuoka SoftBank Hawks",
            "league": "NPB",
            "stadium": "Mizuho PayPay Dome · Fukuoka, Japan",
            "lighting": "Dome Floodlights",
            "jersey": "Revolution Yellow / Black (#fdb913 / #000000)",
            "throws": "RHP",
            "angle": "Low CF Broadcast Lens",
            "pitchType": "Ghost Fork (FS 89mph)",
            "delivery": "Torso Twist Set Position",
            "windowPos": 0.29,
            "filename": "npb/npb_kodai_senga_f116.svg",
            "gloveX": 644, "gloveY": 344, "handX": 653, "handY": 348,
            "torsoX": 640, "torsoY": 368, "headX": 640, "headY": 292,
            "kneeX": 634, "kneeY": 442, "catcherX": 732, "catcherY": 382,
            "bgTheme": "dome_indoor", "skyColor": "#1c2230", "fieldColor": "#1d361d"
        },
        {
            "id": "npb_tomoyuki_sugano_giants_01",
            "pitcher": "Tomoyuki Sugano",
            "team": "Yomiuri Giants",
            "league": "NPB",
            "stadium": "Tokyo Dome · Tokyo, Japan",
            "lighting": "Bright Tokyo Dome Ceiling Lights",
            "jersey": "Giants Orange / Black (#ff6600 / #000000)",
            "throws": "RHP",
            "angle": "Standard CF Broadcast",
            "pitchType": "Cutter / Slider (FC/SL)",
            "delivery": "Traditional Veteran Settle",
            "windowPos": 0.21,
            "filename": "npb/npb_tomoyuki_sugano_f048.svg",
            "gloveX": 642, "gloveY": 350, "handX": 650, "handY": 353,
            "torsoX": 639, "torsoY": 370, "headX": 639, "headY": 294,
            "kneeX": 636, "kneeY": 444, "catcherX": 730, "catcherY": 384,
            "bgTheme": "dome_indoor", "skyColor": "#202838", "fieldColor": "#1f381f"
        }
    ],
    "kbo": [
        {
            "id": "kbo_won_tae_choi_lg_01",
            "pitcher": "Won-tae Choi",
            "team": "LG Twins",
            "league": "KBO",
            "stadium": "Jamsil Baseball Stadium · Seoul, Korea",
            "lighting": "Jamsil Night Broadcast Lights",
            "jersey": "Pinstripes / LG Crimson (#c5003e / #000000)",
            "throws": "RHP",
            "angle": "High Press Box Center-Field",
            "pitchType": "Circle-Changeup (CH)",
            "delivery": "14° Outward Glove Flare at Lift",
            "windowPos": 0.58,
            "filename": "kbo/kbo_won_tae_choi_f112.svg",
            "gloveX": 648, "gloveY": 348, "handX": 658, "handY": 352,
            "torsoX": 640, "torsoY": 368, "headX": 640, "headY": 294,
            "kneeX": 618, "kneeY": 412, "catcherX": 730, "catcherY": 382,
            "bgTheme": "night_stadium", "skyColor": "#0b1526", "fieldColor": "#142d14"
        },
        {
            "id": "kbo_won_tae_choi_lg_02",
            "pitcher": "Won-tae Choi",
            "team": "LG Twins",
            "league": "KBO",
            "stadium": "Jamsil Baseball Stadium · Seoul, Korea",
            "lighting": "Jamsil Night Lights",
            "jersey": "Pinstripes / LG Crimson (#c5003e / #000000)",
            "throws": "RHP",
            "angle": "High Press Box Center-Field",
            "pitchType": "2-Seam Sinker (SI)",
            "delivery": "Tight Vertical Glove Seam at Lift",
            "windowPos": 0.58,
            "filename": "kbo/kbo_won_tae_choi_f126.svg",
            "gloveX": 643, "gloveY": 348, "handX": 651, "handY": 350,
            "torsoX": 640, "torsoY": 368, "headX": 640, "headY": 294,
            "kneeX": 618, "kneeY": 412, "catcherX": 730, "catcherY": 382,
            "bgTheme": "night_stadium", "skyColor": "#0b1526", "fieldColor": "#142d14"
        },
        {
            "id": "kbo_kwang_hyun_kim_ssg_01",
            "pitcher": "Kwang-hyun Kim",
            "team": "SSG Landers",
            "league": "KBO",
            "stadium": "Incheon SSG Landers Field · Incheon, Korea",
            "lighting": "Incheon Night Floodlights",
            "jersey": "Landers Red / White (#bf1922 / #ffffff)",
            "throws": "LHP",
            "angle": "Low 3/4 CF Broadcast",
            "pitchType": "Signature Slider (SL)",
            "delivery": "Dynamic High Kick Dynamic Settle",
            "windowPos": 0.70,
            "filename": "kbo/kbo_kwang_hyun_kim_f084.svg",
            "gloveX": 630, "gloveY": 332, "handX": 620, "handY": 336,
            "torsoX": 635, "torsoY": 362, "headX": 637, "headY": 288,
            "kneeX": 674, "kneeY": 382, "catcherX": 552, "catcherY": 386,
            "bgTheme": "night_stadium", "skyColor": "#0c1424", "fieldColor": "#132c13"
        },
        {
            "id": "kbo_hyeong_jun_so_kt_01",
            "pitcher": "Hyeong-jun So",
            "team": "KT Wiz",
            "league": "KBO",
            "stadium": "Suwon KT Wiz Park · Suwon, Korea",
            "lighting": "Twilight Outdoor Sky",
            "jersey": "Black / Wiz Red (#111111 / #ec1c24)",
            "throws": "RHP",
            "angle": "Standard CF Broadcast",
            "pitchType": "Sinker (SI)",
            "delivery": "Mid-Chest Stretch Hold",
            "windowPos": 0.24,
            "filename": "kbo/kbo_hyeong_jun_so_f098.svg",
            "gloveX": 644, "gloveY": 352, "handX": 652, "handY": 355,
            "torsoX": 640, "torsoY": 370, "headX": 640, "headY": 294,
            "kneeX": 634, "kneeY": 444, "catcherX": 730, "catcherY": 384,
            "bgTheme": "twilight", "skyColor": "#171e32", "fieldColor": "#173117"
        },
        {
            "id": "kbo_dong_ju_moon_hanwha_01",
            "pitcher": "Dong-ju Moon",
            "team": "Hanwha Eagles",
            "league": "KBO",
            "stadium": "Daejeon Hanwha Life Ballpark · Daejeon, Korea",
            "lighting": "Sunny Afternoon Glare",
            "jersey": "Eagles Orange (#ff6600)",
            "throws": "RHP",
            "angle": "Center-Field Zoom",
            "pitchType": "4-Seam Fastball (100mph)",
            "delivery": "Explosive Athletic Lift Prep",
            "windowPos": 0.48,
            "filename": "kbo/kbo_dong_ju_moon_f066.svg",
            "gloveX": 642, "gloveY": 340, "handX": 650, "handY": 343,
            "torsoX": 639, "torsoY": 366, "headX": 639, "headY": 290,
            "kneeX": 624, "kneeY": 425, "catcherX": 732, "catcherY": 380,
            "bgTheme": "day_sun", "skyColor": "#224468", "fieldColor": "#1f3e1f"
        },
        {
            "id": "kbo_woo_suk_go_lg_01",
            "pitcher": "Woo-suk Go",
            "team": "LG Twins",
            "league": "KBO",
            "stadium": "Jamsil Baseball Stadium · Seoul, Korea",
            "lighting": "High Leverage 9th Inning Lights",
            "jersey": "LG Crimson Pinstripe (#c5003e)",
            "throws": "RHP",
            "angle": "Tight CF Lens",
            "pitchType": "Cutter / Fastball (FC/FF)",
            "delivery": "Deep Crouch Settle Position",
            "windowPos": 0.19,
            "filename": "kbo/kbo_woo_suk_go_f045.svg",
            "gloveX": 645, "gloveY": 358, "handX": 654, "handY": 362,
            "torsoX": 640, "torsoY": 372, "headX": 640, "headY": 298,
            "kneeX": 632, "kneeY": 448, "catcherX": 732, "catcherY": 386,
            "bgTheme": "night_stadium", "skyColor": "#080f1e", "fieldColor": "#112811"
        },
        {
            "id": "kbo_eui_lee_lee_kia_01",
            "pitcher": "Eui-lee Lee",
            "team": "KIA Tigers",
            "league": "KBO",
            "stadium": "Gwangju-Kia Champions Field · Gwangju, Korea",
            "lighting": "Night Lights",
            "jersey": "Tigers Red / Black (#c60c30 / #000000)",
            "throws": "LHP",
            "angle": "Low Left CF Angle",
            "pitchType": "Changeup (CH)",
            "delivery": "High Front Arm Shield Set",
            "windowPos": 0.31,
            "filename": "kbo/kbo_eui_lee_lee_f089.svg",
            "gloveX": 632, "gloveY": 345, "handX": 622, "handY": 349,
            "torsoX": 636, "torsoY": 368, "headX": 638, "headY": 292,
            "kneeX": 662, "kneeY": 442, "catcherX": 554, "catcherY": 384,
            "bgTheme": "night_stadium", "skyColor": "#0d1728", "fieldColor": "#142e14"
        },
        {
            "id": "kbo_young_pyo_ko_kt_01",
            "pitcher": "Young-pyo Ko",
            "team": "KT Wiz",
            "league": "KBO",
            "stadium": "Suwon KT Wiz Park · Suwon, Korea",
            "lighting": "Sunset Shadow Horizon",
            "jersey": "Black / White (#111111 / #ffffff)",
            "throws": "RHP Submarine",
            "angle": "Low Torso Submarine CF",
            "pitchType": "Changeup / Sinker (CH/SI)",
            "delivery": "Submarine Deep Torso Bend",
            "windowPos": 0.42,
            "filename": "kbo/kbo_young_pyo_ko_f078.svg",
            "gloveX": 646, "gloveY": 385, "handX": 656, "handY": 388,
            "torsoX": 642, "torsoY": 395, "headX": 642, "headY": 320,
            "kneeX": 630, "kneeY": 460, "catcherX": 734, "catcherY": 392,
            "bgTheme": "twilight", "skyColor": "#192238", "fieldColor": "#183218"
        },
        {
            "id": "kbo_jin_wook_kim_lotte_01",
            "pitcher": "Jin-wook Kim",
            "team": "Lotte Giants",
            "league": "KBO",
            "stadium": "Sajik Baseball Stadium · Busan, Korea",
            "lighting": "Busan Night Sea Breeze",
            "jersey": "Giants Navy / Red (#041e42 / #c8102e)",
            "throws": "LHP",
            "angle": "Standard CF Broadcast",
            "pitchType": "Slider (SL)",
            "delivery": "Smooth Pause at Hand Break",
            "windowPos": 0.88,
            "filename": "kbo/kbo_jin_wook_kim_f052.svg",
            "gloveX": 628, "gloveY": 342, "handX": 618, "handY": 346,
            "torsoX": 634, "torsoY": 366, "headX": 636, "headY": 290,
            "kneeX": 668, "kneeY": 415, "catcherX": 552, "catcherY": 384,
            "bgTheme": "night_stadium", "skyColor": "#091220", "fieldColor": "#122a12"
        },
        {
            "id": "kbo_seung_won_moon_ssg_01",
            "pitcher": "Seung-won Moon",
            "team": "SSG Landers",
            "league": "KBO",
            "stadium": "Incheon SSG Landers Field · Incheon, Korea",
            "lighting": "Day Turf Sunlight",
            "jersey": "Landers White / Red (#ffffff / #bf1922)",
            "throws": "RHP",
            "angle": "Elevated CF",
            "pitchType": "Curveball (CU)",
            "delivery": "High Glove Elevation at Sternum",
            "windowPos": 0.23,
            "filename": "kbo/kbo_seung_won_moon_f061.svg",
            "gloveX": 643, "gloveY": 336, "handX": 651, "handY": 339,
            "torsoX": 639, "torsoY": 364, "headX": 639, "headY": 288,
            "kneeX": 635, "kneeY": 440, "catcherX": 730, "catcherY": 380,
            "bgTheme": "day_sun", "skyColor": "#214266", "fieldColor": "#1e3c1e"
        },
        {
            "id": "kbo_min_woo_lee_hanwha_01",
            "pitcher": "Min-woo Lee",
            "team": "Hanwha Eagles",
            "league": "KBO",
            "stadium": "Daejeon Ballpark · Daejeon, Korea",
            "lighting": "Harsh Midday Shadows",
            "jersey": "Eagles Orange / Grey (#ff6600 / #888888)",
            "throws": "RHP",
            "angle": "Mid CF Angle",
            "pitchType": "Forkball (FS)",
            "delivery": "Deep Hand Burial at Chest",
            "windowPos": 0.27,
            "filename": "kbo/kbo_min_woo_lee_f071.svg",
            "gloveX": 644, "gloveY": 350, "handX": 653, "handY": 354,
            "torsoX": 640, "torsoY": 370, "headX": 640, "headY": 294,
            "kneeX": 633, "kneeY": 445, "catcherX": 731, "catcherY": 384,
            "bgTheme": "day_sun", "skyColor": "#264870", "fieldColor": "#214021"
        },
        {
            "id": "kbo_jae_young_jang_kiwoom_01",
            "pitcher": "Jae-young Jang",
            "team": "Kiwoom Heroes",
            "league": "KBO",
            "stadium": "Gocheok Sky Dome · Seoul, Korea",
            "lighting": "Gocheok Dome Bright Indoor Ceiling",
            "jersey": "Heroes Burgundy (#570514)",
            "throws": "RHP",
            "angle": "Center High CF",
            "pitchType": "4-Seam Fastball (98mph)",
            "delivery": "Tall High Release Angle Settle",
            "windowPos": 0.33,
            "filename": "kbo/kbo_jae_young_jang_f093.svg",
            "gloveX": 642, "gloveY": 332, "handX": 650, "handY": 335,
            "torsoX": 638, "torsoY": 360, "headX": 638, "headY": 282,
            "kneeX": 635, "kneeY": 438, "catcherX": 730, "catcherY": 378,
            "bgTheme": "dome_indoor", "skyColor": "#1e2636", "fieldColor": "#1c361c"
        }
    ],
    "cpbl": [
        {
            "id": "cpbl_gu_lin_ruei_yang_lions_01",
            "pitcher": "Gu Lin Ruei-Yang",
            "team": "Uni-President 7-Eleven Lions",
            "league": "CPBL",
            "stadium": "Taipei Dome · Taipei, Taiwan",
            "lighting": "Taipei Dome 4K LED Floodlights",
            "jersey": "Lions Orange / Green (#ff6600 / #006633)",
            "throws": "RHP",
            "angle": "High Center-Field Broadcast",
            "pitchType": "4-Seam Fastball (FF 98mph)",
            "delivery": "Chin-Height Glove Anchor (High Set)",
            "windowPos": 0.20,
            "filename": "cpbl/cpbl_gu_lin_ruei_yang_f128.svg",
            "gloveX": 644, "gloveY": 328, "handX": 652, "handY": 330,
            "torsoX": 640, "torsoY": 362, "headX": 640, "headY": 286,
            "kneeX": 634, "kneeY": 440, "catcherX": 732, "catcherY": 376,
            "bgTheme": "dome_indoor", "skyColor": "#1d2536", "fieldColor": "#1b351b"
        },
        {
            "id": "cpbl_gu_lin_ruei_yang_lions_02",
            "pitcher": "Gu Lin Ruei-Yang",
            "team": "Uni-President 7-Eleven Lions",
            "league": "CPBL",
            "stadium": "Taipei Dome · Taipei, Taiwan",
            "lighting": "Taipei Dome 4K LED Floodlights",
            "jersey": "Lions Orange / Green (#ff6600 / #006633)",
            "throws": "RHP",
            "angle": "High Center-Field Broadcast",
            "pitchType": "12-6 Curveball (CU)",
            "delivery": "Mid-Chest Lower Anchor + Elbow Tuck",
            "windowPos": 0.24,
            "filename": "cpbl/cpbl_gu_lin_ruei_yang_f140.svg",
            "gloveX": 644, "gloveY": 358, "handX": 652, "handY": 362,
            "torsoX": 640, "torsoY": 368, "headX": 640, "headY": 286,
            "kneeX": 634, "kneeY": 440, "catcherX": 732, "catcherY": 382,
            "bgTheme": "dome_indoor", "skyColor": "#1d2536", "fieldColor": "#1b351b"
        },
        {
            "id": "cpbl_jo_hsi_hsu_dragons_01",
            "pitcher": "Jo-Hsi Hsu",
            "team": "Wei Chuan Dragons",
            "league": "CPBL",
            "stadium": "Taipei Dome · Taipei, Taiwan",
            "lighting": "Dome Bright Overhead Array",
            "jersey": "Dragons Red / White (#d0021b / #ffffff)",
            "throws": "RHP",
            "angle": "Tight Center-Field Lens",
            "pitchType": "Splitter / Fastball (FS/FF 97mph)",
            "delivery": "Compact Power Set Position",
            "windowPos": 0.28,
            "filename": "cpbl/cpbl_jo_hsi_hsu_f090.svg",
            "gloveX": 642, "gloveY": 342, "handX": 651, "handY": 345,
            "torsoX": 639, "torsoY": 366, "headX": 639, "headY": 290,
            "kneeX": 636, "kneeY": 442, "catcherX": 730, "catcherY": 380,
            "bgTheme": "dome_indoor", "skyColor": "#1f2738", "fieldColor": "#1c371c"
        },
        {
            "id": "cpbl_kuan_yu_chen_monkeys_01",
            "pitcher": "Kuan-Yu Chen",
            "team": "Rakuten Monkeys",
            "league": "CPBL",
            "stadium": "Rakuten Taoyuan Baseball Stadium · Taoyuan, Taiwan",
            "lighting": "Outdoor Humid Night Lights",
            "jersey": "Monkeys Wine Red / Gold (#871822 / #d4af37)",
            "throws": "LHP",
            "angle": "Standard CF Broadcast",
            "pitchType": "Slider / Changeup (SL/CH)",
            "delivery": "Veteran Left-Handed Set Presentation",
            "windowPos": 0.22,
            "filename": "cpbl/cpbl_kuan_yu_chen_f076.svg",
            "gloveX": 632, "gloveY": 350, "handX": 622, "handY": 354,
            "torsoX": 636, "torsoY": 370, "headX": 638, "headY": 294,
            "kneeX": 660, "kneeY": 446, "catcherX": 554, "catcherY": 386,
            "bgTheme": "night_stadium", "skyColor": "#0b1422", "fieldColor": "#132b13"
        },
        {
            "id": "cpbl_chih_wei_hu_lions_01",
            "pitcher": "Chih-Wei Hu",
            "team": "Uni-President 7-Eleven Lions",
            "league": "CPBL",
            "stadium": "Tainan Municipal Stadium · Tainan, Taiwan",
            "lighting": "Southern Taiwan Bright Sun",
            "jersey": "Lions Orange / Black (#ff6600 / #000000)",
            "throws": "RHP",
            "angle": "High Sun Center-Field",
            "pitchType": "Changeup (CH)",
            "delivery": "Classic Palm-Ball Hand Burial",
            "windowPos": 0.36,
            "filename": "cpbl/cpbl_chih_wei_hu_f081.svg",
            "gloveX": 645, "gloveY": 356, "handX": 655, "handY": 360,
            "torsoX": 640, "torsoY": 372, "headX": 640, "headY": 296,
            "kneeX": 632, "kneeY": 448, "catcherX": 732, "catcherY": 385,
            "bgTheme": "day_sun", "skyColor": "#244a74", "fieldColor": "#224422"
        },
        {
            "id": "cpbl_jui_yang_huang_brothers_01",
            "pitcher": "Jui-Yang Huang",
            "team": "CTBC Brothers",
            "league": "CPBL",
            "stadium": "Taichung Intercontinental Stadium · Taichung, Taiwan",
            "lighting": "Night Floodlights",
            "jersey": "Brothers Bright Yellow (#fed100 / #041e42)",
            "throws": "RHP",
            "angle": "Mid Center-Field Angle",
            "pitchType": "Sinker / Fastball (SI/FF)",
            "delivery": "Yellow Uniform Contrast Stretch",
            "windowPos": 0.25,
            "filename": "cpbl/cpbl_jui_yang_huang_f064.svg",
            "gloveX": 643, "gloveY": 345, "handX": 651, "handY": 348,
            "torsoX": 639, "torsoY": 368, "headX": 639, "headY": 292,
            "kneeX": 635, "kneeY": 444, "catcherX": 730, "catcherY": 382,
            "bgTheme": "night_stadium", "skyColor": "#0d182a", "fieldColor": "#153015"
        },
        {
            "id": "cpbl_kai_wei_lin_dragons_01",
            "pitcher": "Kai-Wei Lin",
            "team": "Wei Chuan Dragons",
            "league": "CPBL",
            "stadium": "Tianmu Baseball Stadium · Taipei, Taiwan",
            "lighting": "Artificial Turf Night Glow",
            "jersey": "Dragons Red / White (#d0021b / #ffffff)",
            "throws": "RHP",
            "angle": "Low CF Broadcast Lens",
            "pitchType": "Sweeper (ST)",
            "delivery": "Wide Side Set Hold",
            "windowPos": 0.18,
            "filename": "cpbl/cpbl_kai_wei_lin_f055.svg",
            "gloveX": 646, "gloveY": 352, "handX": 656, "handY": 356,
            "torsoX": 641, "torsoY": 372, "headX": 641, "headY": 296,
            "kneeX": 633, "kneeY": 448, "catcherX": 732, "catcherY": 386,
            "bgTheme": "night_stadium", "skyColor": "#0c1524", "fieldColor": "#142d14"
        },
        {
            "id": "cpbl_yi_chung_chen_guardians_01",
            "pitcher": "Yi-Chung Chen",
            "team": "Fubon Guardians",
            "league": "CPBL",
            "stadium": "Xinzhuang Baseball Stadium · New Taipei, Taiwan",
            "lighting": "Evening Sunset Glare",
            "jersey": "Guardian Blue / White (#003865 / #ffffff)",
            "throws": "RHP",
            "angle": "Standard CF Broadcast",
            "pitchType": "Changeup (CH)",
            "delivery": "Mid Chest Set Position",
            "windowPos": 0.29,
            "filename": "cpbl/cpbl_yi_chung_chen_f070.svg",
            "gloveX": 644, "gloveY": 348, "handX": 653, "handY": 351,
            "torsoX": 640, "torsoY": 369, "headX": 640, "headY": 293,
            "kneeX": 634, "kneeY": 443, "catcherX": 731, "catcherY": 383,
            "bgTheme": "twilight", "skyColor": "#182035", "fieldColor": "#173117"
        },
        {
            "id": "cpbl_chun_lin_kuo_guardians_01",
            "pitcher": "Chun-Lin Kuo",
            "team": "Fubon Guardians",
            "league": "CPBL",
            "stadium": "Xinzhuang Stadium · New Taipei, Taiwan",
            "lighting": "Night Floodlights",
            "jersey": "Guardian Royal Blue (#003865)",
            "throws": "RHP",
            "angle": "High Offset Center-Field",
            "pitchType": "Slider (SL)",
            "delivery": "High Hand Presentation at Face",
            "windowPos": 0.15,
            "filename": "cpbl/cpbl_chun_lin_kuo_f049.svg",
            "gloveX": 642, "gloveY": 322, "handX": 650, "handY": 325,
            "torsoX": 638, "torsoY": 356, "headX": 638, "headY": 284,
            "kneeX": 635, "kneeY": 436, "catcherX": 730, "catcherY": 376,
            "bgTheme": "night_stadium", "skyColor": "#0b1220", "fieldColor": "#122812"
        },
        {
            "id": "cpbl_hao_chun_chiu_lions_01",
            "pitcher": "Hao-Chun Chiu",
            "team": "Uni-President 7-Eleven Lions",
            "league": "CPBL",
            "stadium": "Tainan Municipal Stadium · Tainan, Taiwan",
            "lighting": "Tainan Twilight Sky",
            "jersey": "Lions Orange / Black (#ff6600 / #000000)",
            "throws": "RHP",
            "angle": "Center Center-Field Angle",
            "pitchType": "Forkball (FS)",
            "delivery": "Low Settle Stretch Anchor",
            "windowPos": 0.33,
            "filename": "cpbl/cpbl_hao_chun_chiu_f085.svg",
            "gloveX": 645, "gloveY": 362, "handX": 654, "handY": 366,
            "torsoX": 641, "torsoY": 374, "headX": 641, "headY": 298,
            "kneeX": 633, "kneeY": 448, "catcherX": 732, "catcherY": 386,
            "bgTheme": "twilight", "skyColor": "#192238", "fieldColor": "#183218"
        },
        {
            "id": "cpbl_en_sih_huang_brothers_01",
            "pitcher": "En-Sih Huang",
            "team": "CTBC Brothers",
            "league": "CPBL",
            "stadium": "Taichung Intercontinental · Taichung, Taiwan",
            "lighting": "Day Sun High Angle",
            "jersey": "Brothers Yellow (#fed100)",
            "throws": "RHP",
            "angle": "High Press Box CF",
            "pitchType": "Curveball (CU)",
            "delivery": "Over-the-Head Windup Kick",
            "windowPos": 0.68,
            "filename": "cpbl/cpbl_en_sih_huang_f097.svg",
            "gloveX": 640, "gloveY": 334, "handX": 648, "handY": 337,
            "torsoX": 637, "torsoY": 360, "headX": 637, "headY": 285,
            "kneeX": 615, "kneeY": 402, "catcherX": 728, "catcherY": 380,
            "bgTheme": "day_sun", "skyColor": "#224268", "fieldColor": "#1f3c1f"
        },
        {
            "id": "cpbl_chen_hao_tseng_monkeys_01",
            "pitcher": "Chen-Hao Tseng",
            "team": "Rakuten Monkeys",
            "league": "CPBL",
            "stadium": "Rakuten Taoyuan Stadium · Taoyuan, Taiwan",
            "lighting": "Night Stadium Lights",
            "jersey": "Monkeys White / Wine Red (#ffffff / #871822)",
            "throws": "RHP",
            "angle": "Tight Set Center-Field",
            "pitchType": "Cutter (FC)",
            "delivery": "Sternum Set Tuck",
            "windowPos": 0.21,
            "filename": "cpbl/cpbl_chen_hao_tseng_f058.svg",
            "gloveX": 643, "gloveY": 344, "handX": 652, "handY": 347,
            "torsoX": 639, "torsoY": 367, "headX": 639, "headY": 292,
            "kneeX": 635, "kneeY": 443, "catcherX": 730, "catcherY": 382,
            "bgTheme": "night_stadium", "skyColor": "#0c1525", "fieldColor": "#142d14"
        }
    ],
    "lmb": [
        {
            "id": "lmb_trevor_bauer_mex_01",
            "pitcher": "Trevor Bauer",
            "team": "Diablos Rojos del México",
            "league": "LMB",
            "stadium": "Estadio Alfredo Harp Helú · Mexico City, CDMX",
            "lighting": "CDMX High-Altitude Night Stadium Lights",
            "jersey": "Diablos Crimson Red / White (#d0001f / #ffffff)",
            "throws": "RHP",
            "angle": "Elevated Center-Field Lens",
            "pitchType": "Sweep Slider (SL 84mph)",
            "delivery": "High Chin/Sternum Glove Tuck (+2.4in higher set on SL)",
            "windowPos": 0.38,
            "filename": "lmb/lmb_trevor_bauer_f155.svg",
            "gloveX": 645, "gloveY": 368, "handX": 655, "handY": 372,
            "torsoX": 640, "torsoY": 375, "headX": 640, "headY": 295,
            "kneeX": 633, "kneeY": 448, "catcherX": 732, "catcherY": 386,
            "bgTheme": "night_stadium", "skyColor": "#0b1222", "fieldColor": "#142c14"
        },
        {
            "id": "lmb_trevor_bauer_mex_02",
            "pitcher": "Trevor Bauer",
            "team": "Diablos Rojos del México",
            "league": "LMB",
            "stadium": "Estadio Alfredo Harp Helú · Mexico City, CDMX",
            "lighting": "CDMX Night Lights",
            "jersey": "Diablos Crimson Red / White (#d0001f / #ffffff)",
            "throws": "RHP",
            "angle": "Elevated Center-Field Lens",
            "pitchType": "4-Seam Fastball (FF 96mph)",
            "delivery": "Quick Rhythm Settle (Standard Chest Set)",
            "windowPos": 0.24,
            "filename": "lmb/lmb_trevor_bauer_f168.svg",
            "gloveX": 644, "gloveY": 342, "handX": 653, "handY": 345,
            "torsoX": 640, "torsoY": 368, "headX": 640, "headY": 295,
            "kneeX": 634, "kneeY": 444, "catcherX": 732, "catcherY": 380,
            "bgTheme": "night_stadium", "skyColor": "#0b1222", "fieldColor": "#142c14"
        },
        {
            "id": "lmb_wilmer_rios_monclova_01",
            "pitcher": "Wilmer Ríos",
            "team": "Acereros de Monclova",
            "league": "LMB",
            "stadium": "Estadio Monclova · Coahuila, Mexico",
            "lighting": "Desert Night Lighting",
            "jersey": "Acereros Blue / Orange (#002855 / #fa4616)",
            "throws": "RHP",
            "angle": "Standard CF Broadcast",
            "pitchType": "Sinker / Changeup (SI/CH)",
            "delivery": "Traditional Settle Pause",
            "windowPos": 0.26,
            "filename": "lmb/lmb_wilmer_rios_f074.svg",
            "gloveX": 643, "gloveY": 352, "handX": 651, "handY": 356,
            "torsoX": 639, "torsoY": 370, "headX": 639, "headY": 294,
            "kneeX": 635, "kneeY": 445, "catcherX": 730, "catcherY": 384,
            "bgTheme": "night_stadium", "skyColor": "#0c1526", "fieldColor": "#152e15"
        },
        {
            "id": "lmb_manny_barreda_tijuana_01",
            "pitcher": "Manny Barreda",
            "team": "Toros de Tijuana",
            "league": "LMB",
            "stadium": "Estadio Chevron · Tijuana, BC, Mexico",
            "lighting": "Border Stadium Evening Lights",
            "jersey": "Toros Black / Red (#000000 / #c8102e)",
            "throws": "RHP",
            "angle": "High Press Box Center-Field",
            "pitchType": "Changeup (CH)",
            "delivery": "Deep Hand Burial Behind Glove Web",
            "windowPos": 0.32,
            "filename": "lmb/lmb_manny_barreda_f092.svg",
            "gloveX": 645, "gloveY": 355, "handX": 655, "handY": 358,
            "torsoX": 640, "torsoY": 371, "headX": 640, "headY": 295,
            "kneeX": 633, "kneeY": 446, "catcherX": 732, "catcherY": 385,
            "bgTheme": "night_stadium", "skyColor": "#0d172a", "fieldColor": "#142d14"
        },
        {
            "id": "lmb_yoennis_yera_tabasco_01",
            "pitcher": "Yoennis Yera",
            "team": "Olmecas de Tabasco",
            "league": "LMB",
            "stadium": "Estadio Centenario 27 de Febrero · Villahermosa, Tabasco",
            "lighting": "Tropical Humid Night Sky",
            "jersey": "Olmecas Green / White (#005a36 / #ffffff)",
            "throws": "LHP",
            "angle": "Low CF Broadcast Lens",
            "pitchType": "Slider (SL)",
            "delivery": "Cross-Body Left Hand Delivery",
            "windowPos": 0.62,
            "filename": "lmb/lmb_yoennis_yera_f083.svg",
            "gloveX": 631, "gloveY": 340, "handX": 621, "handY": 344,
            "torsoX": 635, "torsoY": 365, "headX": 637, "headY": 290,
            "kneeX": 664, "kneeY": 415, "catcherX": 553, "catcherY": 383,
            "bgTheme": "night_stadium", "skyColor": "#081320", "fieldColor": "#112911"
        },
        {
            "id": "lmb_cesar_valdez_yucatan_01",
            "pitcher": "César Valdez",
            "team": "Leones de Yucatán",
            "league": "LMB",
            "stadium": "Parque Kukulcán Alamo · Mérida, Yucatán",
            "lighting": "Yucatán Night Humidity Glow",
            "jersey": "Leones Navy / Gold (#0b2240 / #e5a823)",
            "throws": "RHP Sidearm",
            "angle": "3/4 Center-Field",
            "pitchType": "Dead-Fish Changeup (CH 74mph)",
            "delivery": "Extreme Hesitation Deception Set",
            "windowPos": 0.45,
            "filename": "lmb/lmb_cesar_valdez_f101.svg",
            "gloveX": 646, "gloveY": 368, "handX": 656, "handY": 372,
            "torsoX": 641, "torsoY": 378, "headX": 641, "headY": 302,
            "kneeX": 631, "kneeY": 452, "catcherX": 733, "catcherY": 388,
            "bgTheme": "night_stadium", "skyColor": "#0a1426", "fieldColor": "#132c13"
        },
        {
            "id": "lmb_david_reyes_veracruz_01",
            "pitcher": "David Reyes",
            "team": "El Águila de Veracruz",
            "league": "LMB",
            "stadium": "Estadio Beto Ávila · Veracruz, Mexico",
            "lighting": "Coastal Twilight Horizon",
            "jersey": "El Águila Crimson Red (#c8102e)",
            "throws": "RHP",
            "angle": "Center Center-Field Angle",
            "pitchType": "Cutter / Fastball (FC/FF)",
            "delivery": "Upright High Set Stance",
            "windowPos": 0.20,
            "filename": "lmb/lmb_david_reyes_f067.svg",
            "gloveX": 643, "gloveY": 338, "handX": 651, "handY": 341,
            "torsoX": 639, "torsoY": 365, "headX": 639, "headY": 288,
            "kneeX": 635, "kneeY": 441, "catcherX": 730, "catcherY": 379,
            "bgTheme": "twilight", "skyColor": "#182136", "fieldColor": "#173017"
        },
        {
            "id": "lmb_erick_leal_mex_01",
            "pitcher": "Erick Leal",
            "team": "Diablos Rojos del México",
            "league": "LMB",
            "stadium": "Estadio Alfredo Harp Helú · Mexico City, CDMX",
            "lighting": "CDMX High Sun & Shadow",
            "jersey": "Diablos White / Red (#ffffff / #d0001f)",
            "throws": "RHP",
            "angle": "High Center-Field Lens",
            "pitchType": "Power Slider (SL)",
            "delivery": "Belt-Line Set Pause",
            "windowPos": 0.28,
            "filename": "lmb/lmb_erick_leal_f087.svg",
            "gloveX": 644, "gloveY": 358, "handX": 653, "handY": 362,
            "torsoX": 640, "torsoY": 372, "headX": 640, "headY": 296,
            "kneeX": 634, "kneeY": 446, "catcherX": 731, "catcherY": 385,
            "bgTheme": "day_sun", "skyColor": "#234670", "fieldColor": "#203f20"
        },
        {
            "id": "lmb_ariel_miranda_campeche_01",
            "pitcher": "Ariel Miranda",
            "team": "Piratas de Campeche",
            "league": "LMB",
            "stadium": "Estadio Nelson Barrera · Campeche, Mexico",
            "lighting": "Gulf Coast Sea Breeze Night",
            "jersey": "Piratas Navy / White (#002855 / #ffffff)",
            "throws": "LHP",
            "angle": "Low Angle CF Broadcast",
            "pitchType": "Splitter (FS)",
            "delivery": "High Front Knee Lift Top",
            "windowPos": 0.74,
            "filename": "lmb/lmb_ariel_miranda_f079.svg",
            "gloveX": 629, "gloveY": 334, "handX": 619, "handY": 338,
            "torsoX": 634, "torsoY": 362, "headX": 636, "headY": 288,
            "kneeX": 670, "kneeY": 388, "catcherX": 551, "catcherY": 385,
            "bgTheme": "night_stadium", "skyColor": "#0a1322", "fieldColor": "#132b13"
        },
        {
            "id": "lmb_jake_sanchez_tijuana_01",
            "pitcher": "Jake Sánchez",
            "team": "Toros de Tijuana",
            "league": "LMB",
            "stadium": "Estadio Chevron · Tijuana, BC, Mexico",
            "lighting": "9th Inning Closer Floodlights",
            "jersey": "Toros Black (#000000)",
            "throws": "RHP",
            "angle": "Tight CF Zoom Lens",
            "pitchType": "Cutter / Slider (FC/SL)",
            "delivery": "Aggressive Quick Come-Set",
            "windowPos": 0.17,
            "filename": "lmb/lmb_jake_sanchez_f046.svg",
            "gloveX": 645, "gloveY": 346, "handX": 654, "handY": 349,
            "torsoX": 640, "torsoY": 369, "headX": 640, "headY": 293,
            "kneeX": 633, "kneeY": 444, "catcherX": 732, "catcherY": 382,
            "bgTheme": "night_stadium", "skyColor": "#08101e", "fieldColor": "#122812"
        },
        {
            "id": "lmb_teddy_stankiewicz_tijuana_01",
            "pitcher": "Teddy Stankiewicz",
            "team": "Toros de Tijuana",
            "league": "LMB",
            "stadium": "Estadio Chevron · Tijuana, BC, Mexico",
            "lighting": "Border Twilight Sky",
            "jersey": "Toros Red / Black (#c8102e / #000000)",
            "throws": "RHP",
            "angle": "Mid Center-Field Angle",
            "pitchType": "Sinker (SI)",
            "delivery": "Traditional Tall Arm Slot Set",
            "windowPos": 0.27,
            "filename": "lmb/lmb_teddy_stankiewicz_f063.svg",
            "gloveX": 643, "gloveY": 344, "handX": 651, "handY": 347,
            "torsoX": 639, "torsoY": 367, "headX": 639, "headY": 291,
            "kneeX": 635, "kneeY": 443, "catcherX": 730, "catcherY": 381,
            "bgTheme": "twilight", "skyColor": "#161f34", "fieldColor": "#162f16"
        },
        {
            "id": "lmb_matt_dermody_tijuana_01",
            "pitcher": "Matt Dermody",
            "team": "Toros de Tijuana",
            "league": "LMB",
            "stadium": "Estadio Chevron · Tijuana, BC, Mexico",
            "lighting": "Night Floodlights",
            "jersey": "Toros Black / Red (#000000 / #c8102e)",
            "throws": "LHP",
            "angle": "High Left CF Angle",
            "pitchType": "Slider / Changeup (SL/CH)",
            "delivery": "Tall LHP Presentation",
            "windowPos": 0.23,
            "filename": "lmb/lmb_matt_dermody_f075.svg",
            "gloveX": 633, "gloveY": 338, "handX": 623, "handY": 342,
            "torsoX": 637, "torsoY": 364, "headX": 639, "headY": 286,
            "kneeX": 661, "kneeY": 440, "catcherX": 555, "catcherY": 380,
            "bgTheme": "night_stadium", "skyColor": "#0c1628", "fieldColor": "#142d14"
        }
    ]
}

def generate_svg_frame(f):
    """
    Generate an authentic 1280x720 center-field broadcast frame SVG
    with pitcher silhouette, jersey styling, mound, stadium backdrop,
    lighting environment, scoreboard bug, and telemetry metadata.
    """
    w, h = 1280, 720
    is_lhp = f["throws"] == "LHP"
    
    # Lighting & background colors
    sky = f.get("skyColor", "#0a1322")
    field = f.get("fieldColor", "#132d13")
    theme = f.get("bgTheme", "night_stadium")
    
    # Coordinates
    gx, gy = f["gloveX"], f["gloveY"]
    hx, hy = f["handX"], f["handY"]
    tx, ty = f["torsoX"], f["torsoY"]
    kx, ky = f["kneeX"], f["kneeY"]
    cx, cy = f["catcherX"], f["catcherY"]
    hdx, hdy = f["headX"], f["headY"]
    
    # Determine jersey colors
    jersey_str = f["jersey"]
    primary_color = "#e0e0e0"
    if "Black" in jersey_str: primary_color = "#181818"
    elif "Red" in jersey_str or "Crimson" in jersey_str: primary_color = "#ba0c2f"
    elif "Blue" in jersey_str: primary_color = "#003b7a"
    elif "Orange" in jersey_str: primary_color = "#ff6600"
    elif "Purple" in jersey_str: primary_color = "#461d7c"
    elif "Yellow" in jersey_str or "Gold" in jersey_str: primary_color = "#d4af37"
    elif "Green" in jersey_str: primary_color = "#005a36"
    elif "Burgundy" in jersey_str: primary_color = "#570514"
    elif "Navy" in jersey_str: primary_color = "#0b1f3a"
    
    # SVG string
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <defs>
    <radialGradient id="stadiumLights" cx="50%" cy="0%" r="80%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="{0.18 if theme=='night_stadium' else 0.08}"/>
      <stop offset="60%" stop-color="{sky}" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="{sky}" stop-opacity="1"/>
    </radialGradient>
    <linearGradient id="moundDirt" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#8c6239"/>
      <stop offset="70%" stop-color="#604224"/>
      <stop offset="100%" stop-color="#3d2a17"/>
    </linearGradient>
    <linearGradient id="grassGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{field}"/>
      <stop offset="100%" stop-color="#0a1a0a"/>
    </linearGradient>
  </defs>

  <!-- Sky & Stadium Backdrop -->
  <rect width="{w}" height="{h}" fill="url(#stadiumLights)" />
  
  <!-- Outfield wall & crowd silhouette -->
  <path d="M0,220 Q640,190 1280,220 L1280,310 L0,310 Z" fill="#080c14" opacity="0.95"/>
  <!-- Warning track & Outfield Grass -->
  <path d="M0,310 L1280,310 L1280,510 Q640,490 0,510 Z" fill="url(#grassGrad)"/>
  
  <!-- Infield & Mound Dirt -->
  <ellipse cx="640" cy="500" rx="340" ry="170" fill="url(#moundDirt)" />
  <ellipse cx="640" cy="460" rx="140" ry="65" fill="#a07242" opacity="0.6"/>
  <!-- Pitcher Rubber Plate -->
  <rect x="618" y="455" width="44" height="6" fill="#f0f0f0" rx="1"/>

  <!-- Home Plate Region in Background (Catcher & Umpire Base) -->
  <ellipse cx="{cx}" cy="{cy + 75}" rx="55" ry="22" fill="#50351d" opacity="0.75"/>
  <!-- Home Plate -->
  <polygon points="{cx-8},{cy+72} {cx+8},{cy+72} {cx+12},{cy+78} {cx},{cy+86} {cx-12},{cy+78}" fill="#ffffff" stroke="#999" stroke-width="1"/>
  
  <!-- Catcher Silhouette & Target -->
  <g id="catcher-silhouette" opacity="0.88">
    <!-- Catcher Body -->
    <ellipse cx="{cx}" cy="{cy+30}" rx="22" ry="28" fill="#1c2430"/>
    <!-- Catcher Helmet/Mask -->
    <circle cx="{cx}" cy="{cy}" r="12" fill="#3a4556" stroke="#c0c0c0" stroke-width="1.5"/>
    <!-- Catcher Shin Guards -->
    <rect x="{cx-16}" y="{cy+48}" width="12" height="26" fill="#2d3748" rx="3" stroke="#88a0b8" stroke-width="1"/>
    <rect x="{cx+4}" y="{cy+48}" width="12" height="26" fill="#2d3748" rx="3" stroke="#88a0b8" stroke-width="1"/>
    <!-- Catcher Target Mitt -->
    <circle cx="{cx + (-18 if is_lhp else 18)}" cy="{cy+24}" r="11" fill="#4a3728" stroke="#70af5f" stroke-width="2"/>
    <circle cx="{cx + (-18 if is_lhp else 18)}" cy="{cy+24}" r="5" fill="#70af5f" opacity="0.6"/>
  </g>

  <!-- Pitcher Silhouette & Anatomy Representation -->
  <g id="pitcher-anatomy">
    <!-- Shadow on Mound -->
    <ellipse cx="{tx}" cy="460" rx="42" ry="14" fill="#000000" opacity="0.45"/>
    
    <!-- Cleats & Lower Legs -->
    <line x1="{tx-10}" y1="{ty+40}" x2="{tx-12}" y2="455" stroke="#111111" stroke-width="10" stroke-linecap="round"/>
    <line x1="{tx+10}" y1="{ty+40}" x2="{kx}" y2="{ky}" stroke="#111111" stroke-width="10" stroke-linecap="round"/>
    <ellipse cx="{tx-12}" cy="455" rx="9" ry="4" fill="#222"/>
    <ellipse cx="{kx}" cy="{ky}" rx="9" ry="4" fill="#222"/>

    <!-- Pants / Hips (Belt) -->
    <polygon points="{tx-18},{ty+20} {tx+18},{ty+20} {tx+14},{ty+55} {tx-14},{ty+55}" fill="#e5e5e5" stroke="#999" stroke-width="1"/>
    <rect x="{tx-16}" y="{ty+18}" width="32" height="5" fill="#111" rx="1"/> <!-- Belt -->
    
    <!-- Torso / Jersey -->
    <path d="M{tx-22},{ty-25} L{tx+22},{ty-25} L{tx+18},{ty+20} L{tx-18},{ty+20} Z" fill="{primary_color}" stroke="#000000" stroke-width="1.5"/>
    
    <!-- Pitcher Head & Cap -->
    <circle cx="{hdx}" cy="{hdy}" r="14" fill="#d9a07a"/> <!-- Face / Cheek -->
    <path d="M{hdx-15},{hdy-6} Q{hdx},{hdy-24} {hdx+15},{hdy-6} L{hdx+20 if not is_lhp else hdx-20},{hdy-4} Z" fill="{primary_color}" stroke="#111" stroke-width="1"/> <!-- Cap & Bill -->

    <!-- Throwing Arm & Bare Hand -->
    <line x1="{tx + (16 if not is_lhp else -16)}" y1="{ty-18}" x2="{hx}" y2="{hy}" stroke="{primary_color}" stroke-width="8" stroke-linecap="round"/>
    <circle cx="{hx}" cy="{hy}" r="6" fill="#f0c040" stroke="#d9a07a" stroke-width="2"/> <!-- Bare hand inside/near glove -->

    <!-- Glove Arm & Pitcher Glove -->
    <line x1="{tx + (-16 if not is_lhp else 16)}" y1="{ty-18}" x2="{gx}" y2="{gy}" stroke="{primary_color}" stroke-width="8" stroke-linecap="round"/>
    <!-- Glove Bounding Shape -->
    <path d="M{gx-14},{gy-16} C{gx-18},{gy+10} {gx+10},{gy+16} {gx+16},{gy-8} C{gx+14},{gy-18} {gx},{gy-18} {gx-14},{gy-16} Z" fill="#6d4218" stroke="#ff8c00" stroke-width="2.5"/>
    <ellipse cx="{gx}" cy="{gy}" rx="7" ry="9" fill="#ff8c00" opacity="0.35"/>
  </g>

  <!-- Visual Broadcast Reticle Overlay (CF Optical Horizon) -->
  <g opacity="0.35">
    <line x1="0" y1="{gy}" x2="{w}" y2="{gy}" stroke="#ff8c00" stroke-dasharray="4,4" stroke-width="1"/>
    <line x1="{gx}" y1="0" x2="{gx}" y2="{h}" stroke="#ff8c00" stroke-dasharray="4,4" stroke-width="1"/>
  </g>

  <!-- Broadcast Scoreboard & Calibration Metadata Bug -->
  <rect x="24" y="24" width="460" height="96" fill="#080e18" fill-opacity="0.92" rx="6" stroke="#1f2c3f" stroke-width="1.5"/>
  <rect x="24" y="24" width="8" height="96" fill="#3d8bfd" rx="2"/>
  
  <text x="44" y="50" fill="#ffffff" font-family="Manrope, sans-serif" font-size="16" font-weight="700">{f["pitcher"]}</text>
  <text x="44" y="70" fill="#3ecf8e" font-family="IBM Plex Mono, monospace" font-size="12" font-weight="600">{f["team"]} · {f["league"]} · {f["throws"]}</text>
  <text x="44" y="90" fill="#a0aec0" font-family="IBM Plex Mono, monospace" font-size="11">{f["pitchType"]} · {f["angle"]}</text>
  <text x="44" y="108" fill="#e8a23a" font-family="IBM Plex Mono, monospace" font-size="10.5">{f["delivery"]} · WinPos: {int(f["windowPos"]*100)}%</text>

  <!-- Top Right League & Stadium Watermark -->
  <rect x="980" y="24" width="276" height="68" fill="#080e18" fill-opacity="0.92" rx="6" stroke="#1f2c3f" stroke-width="1.5"/>
  <text x="1000" y="48" fill="#3d8bfd" font-family="Manrope, sans-serif" font-size="14" font-weight="800">{f["league"]} ADVANCE CALIBRATION</text>
  <text x="1000" y="68" fill="#718096" font-family="IBM Plex Mono, monospace" font-size="10">{f["stadium"].split('·')[0].strip()}</text>
  <text x="1000" y="82" fill="#4a5568" font-family="IBM Plex Mono, monospace" font-size="9.5">{f["lighting"]}</text>

  <!-- Actionable Delivery Window Gauge (Bottom Left) -->
  <rect x="24" y="660" width="360" height="36" fill="#080e18" fill-opacity="0.92" rx="4" stroke="#1f2c3f" stroke-width="1"/>
  <text x="36" y="682" fill="#a0aec0" font-family="IBM Plex Mono, monospace" font-size="11">Window: Come-Set → Hand Break</text>
  <rect x="230" y="672" width="140" height="8" fill="#1a2636" rx="3"/>
  <rect x="230" y="672" width="{int(140 * f['windowPos'])}" height="8" fill="#3ecf8e" rx="3"/>

</svg>"""
    return svg

def build_manifest_frames(league_key):
    frames = []
    items = LEAGUE_FRAMES[league_key]
    for item in items:
        # relative path from pitch-tips/
        src_path = f"media/detection/{item['filename']}"
        f_entry = {
            "id": item["id"],
            "src": src_path,
            "pitcher": item["pitcher"],
            "team": item["team"],
            "league": item["league"],
            "pitchType": item["pitchType"],
            "angle": item["angle"],
            "stadium": item["stadium"],
            "lighting": item["lighting"],
            "throws": item["throws"],
            "delivery": item["delivery"],
            "windowPos": item["windowPos"],
            "gloveConf": 0.0,
            "handConf": 0.0,
            "boundsMethod": "calibrated_cf_keypoints"
        }
        frames.append(f_entry)
    return frames

def main():
    print("Generating frame SVG visual assets...")
    total_svgs = 0
    all_multileague_frames = []

    for league, items in LEAGUE_FRAMES.items():
        league_frames = []
        for item in items:
            svg_content = generate_svg_frame(item)
            file_path = os.path.join(MEDIA_DIR, item["filename"])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(svg_content)
            total_svgs += 1

        league_frames = build_manifest_frames(league)
        all_multileague_frames.extend(league_frames)

        # Write per-league manifest
        league_manifest = {
            "version": 2,
            "league": league.upper(),
            "angle": "CF_multileague_calibration",
            "mode": "multi_part_fine_tune",
            "classes": CLASSES,
            "ordering": "round_robin_by_pitcher",
            "note": f"{league.upper()} Calibration Dataset: Diverse lighting (day/night/dome), stadium backgrounds, jersey colors, and camera elevation angles for fine-tuning pre-release landmark detection.",
            "frames": league_frames
        }
        manifest_path = os.path.join(DATA_DIR, f"label_manifest_{league}.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(league_manifest, f, indent=2)
        print(f"  Wrote {manifest_path} ({len(league_frames)} frames)")

    # Combined multi-league manifest
    combined_manifest = {
        "version": 2,
        "league": "MULTI_LEAGUE",
        "angle": "CF_multileague_calibration",
        "mode": "multi_part_fine_tune",
        "classes": CLASSES,
        "ordering": "round_robin_by_league_pitcher",
        "note": "Combined Multi-League Calibration Dataset (NCAA, NPB, KBO, CPBL, LMB): 60 representative frames across 5 professional and collegiate leagues. Calibrates center-field camera angles, stadium lighting (open-air sun, shadows, night floodlights, dome lighting), and uniform contrasts.",
        "frames": all_multileague_frames
    }
    combined_path = os.path.join(DATA_DIR, "label_manifest_multileague.json")
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(combined_manifest, f, indent=2)
    print(f"  Wrote {combined_path} ({len(all_multileague_frames)} total frames across 5 leagues)")
    print(f"Total SVGs created: {total_svgs}")

if __name__ == "__main__":
    main()
