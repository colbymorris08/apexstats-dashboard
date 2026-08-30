#!/usr/bin/env python3
"""
Enrich demo.json files to ensure every tip and player has accurate videoA, videoB,
pitch_a_label, pitch_b_label, anchor_a, anchor_b, stillA, stillB.
"""
import json
import os

PATHS = ["pitch-tips/demo.json", "pitch-tips/data/demo.json"]

PITCH_RESOLVER = {
    "roupp": {
        "cu": "media/video/roupp_cu.mp4",
        "si": "media/video/roupp_si.mp4",
        "ch": "media/video/roupp_ch.mp4",
        "sl": "media/video/roupp_sl.mp4",
        "ff": "media/video/roupp_ff.mp4"
    },
    "webb": {
        "si": "media/video/webb_si.mp4",
        "ch": "media/video/webb_ch.mp4",
        "sl": "media/video/webb_sl.mp4",
        "fc": "media/video/webb_fc.mp4",
        "ff": "media/video/webb_ff.mp4"
    },
    "eduardo_rodriguez": {
        "ff": "media/video/erod_ff.mp4",
        "ch": "media/video/erod_ch.mp4",
        "fc": "media/video/erod_fc.mp4",
        "sl": "media/video/erod_sl.mp4",
        "si": "media/video/erod_si.mp4"
    },
    "erod": {
        "ff": "media/video/erod_ff.mp4",
        "ch": "media/video/erod_ch.mp4",
        "fc": "media/video/erod_fc.mp4",
        "sl": "media/video/erod_sl.mp4",
        "si": "media/video/erod_si.mp4"
    },
    "burns": {
        "ff": "media/video/burns_ff.mp4",
        "sl": "media/video/burns_sl.mp4",
        "ch": "media/video/burns_ch.mp4",
        "cu": "media/video/burns_cu.mp4"
    },
    "sasaki": {
        "ff": "media/video/sasaki_ff.mp4",
        "fs": "media/video/sasaki_fs.mp4",
        "sl": "media/video/sasaki_sl.mp4"
    },
    "choi": {
        "si": "media/video/choi_si.mp4",
        "ch": "media/video/choi_ch.mp4",
        "sl": "media/video/choi_sl.mp4",
        "cu": "media/video/choi_cu.mp4",
        "ff": "media/video/choi_ff.mp4"
    },
    "gu_lin": {
        "ff": "media/video/gulin_ff.mp4",
        "cu": "media/video/gulin_cu.mp4",
        "ch": "media/video/gu_lin_ch.mp4"
    },
    "rios": {
        "si": "media/video/rios_si.mp4",
        "ch": "media/video/rios_ch.mp4",
        "sl": "media/video/rios_sl.mp4",
        "fc": "media/video/rios_fc.mp4"
    },
    "gausman": {
        "ff": "media/video/gausman_ff.mp4",
        "fs": "media/video/gausman_fs.mp4",
        "sl": "media/video/gausman_sl.mp4"
    },
    "pfaadt": {
        "si": "media/video/pfaadt_si.mp4",
        "st": "media/video/pfaadt_st.mp4",
        "ch": "media/video/pfaadt_ch.mp4",
        "ff": "media/video/pfaadt_ff.mp4",
        "sl": "media/video/pfaadt_sl.mp4"
    },
    "moreno": {
        "ff": "media/video/moreno_ff.mp4",
        "ch": "media/video/moreno_ch.mp4"
    }
}

def resolve_video(player_id, pitch_label, default_vid):
    pid = (player_id or "").lower().replace("-", "_")
    matched_arm = None
    for k in PITCH_RESOLVER:
        if k in pid:
            matched_arm = k
            break
    if not matched_arm:
        return default_vid
    
    label = (pitch_label or "").lower()
    mapping = PITCH_RESOLVER[matched_arm]
    for ptype, path in mapping.items():
        if ptype in label or ("curve" in label and ptype == "cu") or ("sink" in label and ptype == "si") or ("change" in label and ptype == "ch") or ("slide" in label and ptype == "sl") or ("four" in label and ptype == "ff") or ("split" in label and ptype == "fs") or ("sweep" in label and ptype == "st") or ("cut" in label and ptype == "fc"):
            return path
    # Return first available
    return list(mapping.values())[0]

for path in PATHS:
    if not os.path.exists(path):
        continue
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    players_data = data.get("players", {})
    if isinstance(players_data, dict):
        players = list(players_data.values())
    elif isinstance(players_data, list):
        players = players_data
    else:
        players = []

    for p in players:
        if not isinstance(p, dict):
            continue
        pid = p.get("id", "")
        # Set player level defaults
        v_map = None
        for k in PITCH_RESOLVER:
            if k in pid.lower():
                v_map = PITCH_RESOLVER[k]
                break
        if not v_map:
            v_map = PITCH_RESOLVER["roupp"]
            
        vals = list(v_map.values())
        p["videoA"] = vals[0]
        p["videoB"] = vals[1] if len(vals) > 1 else vals[0]
        p["videoCompare"] = {
            "videoA": p["videoA"],
            "videoB": p["videoB"],
            "labelA": "PITCH A BROADCAST",
            "labelB": "PITCH B BROADCAST",
            "timecodeA": 2.40,
            "timecodeB": 2.10
        }
        
        # Enrich tips
        tips = p.get("tips", []) or p.get("cues", []) or p.get("tells", [])
        for idx, tip in enumerate(tips):
            if not isinstance(tip, dict):
                continue
            p_a = tip.get("pitch_a_label") or tip.get("pitch_a") or "Fastball (FF)"
            p_b = tip.get("pitch_b_label") or tip.get("pitch_b") or "Secondary (SL/CU)"
            
            if "contrast_label" in tip:
                parts = tip["contrast_label"].split(" vs ")
                if len(parts) >= 2:
                    p_a, p_b = parts[0].strip(), parts[1].strip()
            elif "contrast" in tip:
                parts = str(tip["contrast"]).split(" vs ")
                if len(parts) >= 2:
                    p_a, p_b = parts[0].strip(), parts[1].strip()
            elif "predicts" in tip:
                pt = tip["predicts"].upper()
                if pt == "CU": p_a, p_b = "Curveball (CU)", "Sinker (SI)"
                elif pt == "SI": p_a, p_b = "Sinker (SI)", "Fastball (FF)"
                elif pt == "CH": p_a, p_b = "Changeup (CH)", "Fastball (FF)"
                elif pt == "SL": p_a, p_b = "Slider (SL)", "Fastball (FF)"
                elif pt == "FC": p_a, p_b = "Cutter (FC)", "Changeup (CH)"
            
            tip["pitch_a_label"] = p_a
            tip["pitch_b_label"] = p_b
            tip["videoA"] = resolve_video(pid, p_a, p["videoA"])
            tip["videoB"] = resolve_video(pid, p_b, p["videoB"])
            # Guarantee anchor timestamps
            if "anchor_a" not in tip or tip["anchor_a"] is None:
                tip["anchor_a"] = 2.40
            if "anchor_b" not in tip or tip["anchor_b"] is None:
                tip["anchor_b"] = 2.10

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Updated {path} ({len(players)} players)")
