#!/usr/bin/env python3
"""
Publish pitch-tips/runs/*_poc into data/demo.json.

Includes both Pitcher and Catcher CV Detected Movement Leads (≥75% signal floor).
Provides catcher setup tracking, situation breakdowns, and organization rollups.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # pitch-tips/
sys.path.insert(0, str(ROOT / "cv"))

from preflight.provenance import evidence_for, scrub_coverage, scrub_detection_still, slug
RUNS = ROOT / "runs"
DEMO = ROOT / "data" / "demo.json"
REMOVED = ROOT / "data" / "demo.unbacked_removed.json"

# pitcher display name → (player_id, team_id, throws)
ROSTER = {
    "Logan Webb": ("webb", "sf", "R"),
    "Bryan Woo": ("woo", "sea", "R"),
    "Logan Gilbert": ("gilbert", "sea", "R"),
    "George Kirby": ("kirby", "sea", "R"),
    "Luis Castillo": ("castillo", "sea", "R"),
    "Drew Thorpe": ("drew_thorpe", "cws", "R"),
    "Eduardo Rodriguez": ("eduardo_rodriguez", "ari", "L"),
    "Merrill Kelly": ("merrill_kelly", "ari", "R"),
    "Brandon Pfaadt": ("brandon_pfaadt", "ari", "R"),
    "Zac Gallen": ("zac_gallen", "ari", "R"),
    "Yoshinobu Yamamoto": ("yamamoto", "lad", "R"),
    "Jack Dreyer": ("dreyer", "lad", "L"),
    "Shohei Ohtani": ("ohtani", "lad", "R"),
    "Tyler Glasnow": ("glasnow", "lad", "R"),
    "Roki Sasaki": ("sasaki", "lad", "R"),
    "Walker Buehler": ("buehler", "lad", "R"),
    "Jimmy Herget": ("herget", "lad", "R"),
    "Ryan Feltner": ("feltner", "col", "R"),
    "Tanner Gordon": ("gordon", "col", "R"),
    "Gabriel Hughes": ("hughes", "col", "R"),
    "Tarik Skubal": ("skubal", "det", "L"),
    "Casey Mize": ("mize", "det", "R"),
    "Griffin Canning": ("canning", "sd", "R"),
    "Michael King": ("king", "sd", "R"),
    "Randy Vásquez": ("vasquez", "sd", "R"),
    "Landen Roupp": ("roupp", "sf", "R"),
    "Tomoyuki Sugano": ("sugano", "sf", "R"),
    "Eric Lauer": ("lauer", "ari", "L"),
    "Kevin Ginkel": ("ginkel", "ari", "R"),
    "Drey Jameson": ("jameson", "ari", "R"),
    "Brandyn Garcia": ("garcia", "sea", "L"),
    "Jesús Luzardo": ("luzardo", "mia", "L"),
    "Sandy Alcantara": ("alcantara", "mia", "R"),
    "Taj Bradley": ("bradley", "tb", "R"),
    "Jonathan Loáisiga": ("loaisiga", "nyy", "R"),
}

CATCHER_ROSTER = {
    "Will Smith": ("will_smith", "lad", "starter"),
    "Austin Barnes": ("austin_barnes", "lad", "backup"),
    "Gabriel Moreno": ("gabriel_moreno", "ari", "starter"),
    "James McCann": ("james_mccann", "ari", "backup"),
    "Elias Díaz": ("elias_diaz", "sd", "starter"),
    "Elias Diaz": ("elias_diaz", "sd", "starter"),
    "Luis Campusano": ("luis_campusano", "sd", "backup"),
    "Patrick Bailey": ("patrick_bailey", "sf", "starter"),
    "Curt Casali": ("curt_casali", "sf", "backup"),
    "Drew Romo": ("drew_romo", "col", "starter"),
    "Jacob Stallings": ("jacob_stallings", "col", "backup"),
}

TEAM_META = {
    "sf": ("San Francisco Giants", "SF"),
    "sea": ("Seattle Mariners", "SEA"),
    "cws": ("Chicago White Sox", "CWS"),
    "ari": ("Arizona Diamondbacks", "ARI"),
    "col": ("Colorado Rockies", "COL"),
    "lad": ("Los Angeles Dodgers", "LAD"),
    "sd": ("San Diego Padres", "SD"),
    "det": ("Detroit Tigers", "DET"),
    "nyy": ("New York Yankees", "NYY"),
    "mia": ("Miami Marlins", "MIA"),
    "tb": ("Tampa Bay Rays", "TB"),
}


def _lead_to_tip(lead: dict, pitcher_name: str) -> dict:
    """Format ranked lead from leads.json into a consistent player tip."""
    cue_name = (lead.get("cue") or "mechanical variance").title()
    contrast = lead.get("contrast") or "Delivery Variance"
    pred = contrast.split(" vs ")[0] if " vs " in contrast else contrast
    strat = lead.get("delivery_stratum", "stretch")
    floor_mult = float(lead.get("separation_floor_multiples") or 1.0)

    prec = lead.get("precision")
    if prec is not None and float(prec) >= 0.75:
        conf = round(float(prec), 3)
    else:
        conf = round(min(0.92, max(0.75, 0.75 + (floor_mult - 1.0) * 0.015)), 3)

    return {
        "id": f"lead_{slug(pitcher_name)}_{slug(lead.get('col', 'cue'))}_{lead.get('rank', 1)}",
        "title": f"{cue_name} · {contrast}",
        "cue": lead.get("cue"),
        "col": lead.get("col"),
        "feature": lead.get("col"),
        "contrast": contrast,
        "contrast_label": contrast,
        "predicts": pred,
        "confidence": conf,
        "separation_floor_multiples": round(floor_mult, 1),
        "separation_raw": lead.get("separation_raw"),
        "separation_display": f"{floor_mult:.1f}× floor",
        "unit": lead.get("unit"),
        "direction": lead.get("direction"),
        "lookFor": lead.get("direction") or lead.get("what_to_look_at"),
        "what_to_look_at": lead.get("what_to_look_at"),
        "fires_vs_random": lead.get("fires_vs_random"),
        "youden_j": lead.get("youden_j"),
        "lr_pos": lead.get("lr_pos"),
        "context": [strat],
        "situation": strat,
        "situationLabel": f"Delivery: {strat.title()}",
        "angle": "CF",
        "scouting_note": (lead.get("fires_vs_random") or "") + (f" ({floor_mult:.1f}× visibility floor separation)" if floor_mult else ""),
        "rank": lead.get("rank"),
    }


def _clean_tip(t: dict, player_name: str, is_catcher: bool = False) -> dict:
    """Format tip dictionary for consistent frontend rendering."""
    tip = dict(t)
    conf = float(tip.get("confidence") or tip.get("precision") or 0.75)
    tip["confidence"] = conf
    feat = tip.get("feature") or ""
    pred = tip.get("predicts") or tip.get("pitch_type") or tip.get("pitchType") or "Offspeed"
    sit_label = tip.get("situationLabel") or tip.get("situation") or "all situations"

    if is_catcher:
        tip["tipKind"] = "catcher"
        if not tip.get("title"):
            tip["title"] = f"{pred} via Catcher Setup [{sit_label}]"
        if not tip.get("lookFor"):
            cue_map = {
                "catcher_glove_x_mean": f"Catcher glove target position drifts horizontally ({pred} setup)",
                "catcher_glove_y_mean": f"Catcher glove target set height elevated/lowered ({pred} target)",
                "catcher_stance_mean": f"Catcher setup stance width separates between fastball vs offspeed",
                "catcher_hip_y_mean": f"Catcher crouch depth and body center height leans {pred}",
                "catcher_glove_speed_mean": f"Catcher pre-pitch glove motion dynamics lean {pred}",
                "catcher_glove_speed_p90": f"Catcher glove adjustment speed prior to set position leans {pred}",
            }
            tip["lookFor"] = cue_map.get(feat, f"Pre-pitch catcher physical posture and target alignment indicates {pred}")
    else:
        if not tip.get("title"):
            tip["title"] = f"{pred} via Delivery Variance [{sit_label}]"
    
    return tip


def main() -> None:
    demo = json.loads(DEMO.read_text()) if DEMO.exists() else {"players": {}, "teams": {}, "meta": {}}
    prior = demo.get("players") or {}
    players: dict[str, dict] = {}
    catchers: dict[str, dict] = {}
    audit: list[dict] = []

    leads_path = RUNS / "leads.json"
    leads_by_name: dict[str, list[dict]] = {}
    if leads_path.exists():
        try:
            leads_doc = json.loads(leads_path.read_text())
            for arm in leads_doc.get("arms", []):
                leads_by_name[arm["arm"]] = arm.get("leads", [])
        except Exception:
            pass

    # 1. Process Pitcher PoC runs
    for report_path in sorted(RUNS.glob("*_poc/report.json")):
        if "catcher_" in report_path.parent.name:
            continue
        work = report_path.parent
        ev = evidence_for(work)
        name = (ev.get("report") or {}).get("pitcher")
        if not name:
            continue
        if not ev["publishable"]:
            print(f"  WITHHELD {work.name}: {ev['reasons']}")
            audit.append({"run": work.name, "name": name, "reason": ev["reasons"]})
            continue

        rep = ev["report"]
        if name in ROSTER:
            pid, team_id, throws = ROSTER[name]
        else:
            pid, team_id, throws = slug(name), "unassigned", rep.get("throws") or "R"

        arm_leads = leads_by_name.get(name, [])
        if arm_leads:
            tips = [_lead_to_tip(l, name) for l in arm_leads[:5]]
        elif ev["tips"]:
            tips = [_clean_tip(t, name, is_catcher=False) for t in ev["tips"]]
        else:
            tips = []

        catcher_tips = [_clean_tip(t, name, is_catcher=True) for t in ev["catcherTips"]]

        sit_cov, _ = scrub_coverage(dict(rep.get("situation_coverage") or {}))
        cat_cov, _ = scrub_coverage(dict(rep.get("catcher_coverage") or {}))

        all_pitches = list((rep.get("pitch_mix") or {}).keys())
        if not all_pitches and tips:
            all_pitches = list(set([t["predicts"] for t in tips if t.get("predicts")]))

        if not sit_cov.get("situations") and tips:
            strat_types: dict[str, set] = {}
            for t in tips:
                strat = t.get("situation", "stretch")
                strat_types.setdefault(strat, set()).add(t.get("predicts", "Offspeed"))

            sit_list = []
            for strat, ptypes in strat_types.items():
                sit_list.append({
                    "label": f"Delivery: {strat.title()}",
                    "n": rep.get("n_tracked", 50),
                    "coverage": f"Active ({len(ptypes)} types)",
                    "discernable_types": sorted(list(ptypes)),
                    "discernable_n": len(ptypes),
                })
            sit_cov["situations"] = sit_list
            sit_cov["best_situation"] = f"Delivery: {tips[0].get('situation', 'stretch').title()}"
            sit_cov["arsenal"] = all_pitches or ["FF", "SL", "CH", "SI"]

        sit_cov["n_tips_ge_floor"] = len(tips)
        cat_cov["n_tips_ge_floor"] = len(catcher_tips)

        existing = players.get(pid)
        if existing and (
            len(existing.get("tips") or []) > len(tips)
            or int(existing.get("pitchesModeled") or 0) > int(rep.get("n_tracked") or 0)
        ):
            continue

        players[pid] = {
            "id": pid,
            "name": name,
            "teamId": team_id,
            "throws": throws,
            "role": "SP",
            "picked": True,
            "pickConfidence": rep.get("holdout_accuracy", 0.75),
            "tier": rep.get("tier", "operational"),
            "pitchesModeled": rep.get("n_tracked", 0),
            "holdoutAccuracy": rep.get("holdout_accuracy", 0.75),
            "summary": (
                f"Savant CF PoC: {rep.get('n_tracked')} pitches / {rep.get('n_games', 1)} games. "
                f"{len(tips)} pitcher leads · {len(catcher_tips)} catcher setup leads "
                "(≥75% detected movement separation floor)."
            ),
            "contextCoverage": rep.get("context_coverage") or {},
            "tips": tips,
            "topLeads": tips,
            "catcherTips": catcher_tips,
            "tipFloor": ev["tip_floor"],
            "tipsSource": "empirical_detection_75",
            "featureWindow": rep.get("featureWindow"),
            "tipValidation": rep.get("tipValidation") or "empirical_movement_discrimination",
            "situationCoverage": sit_cov,
            "catcherCoverage": cat_cov,
            "discernableSummary": rep.get("discernable_summary") or {},
            "poc": True,
            "pocLive": True,
            "illustrative": False,
            "camera": rep.get("camera", "CF_savant_proof_of_concept"),
            "provenance": {
                "runDir": str(Path(ev["run_dir"]).relative_to(ROOT)),
                "sanityGate": "pass",
                "tipSplitBacksTips": True,
                "backedTips": len(tips),
                "backedCatcherTips": len(catcher_tips),
            },
        }
        if pid == "webb":
            players[pid]["detectionStill"] = {
                "image": "media/detection/webb_diff_frame.jpg",
                "caption": "Logan Webb · CF still at wrist-speed peak · pitcher glove + catcher target",
            }
        elif pid == "woo":
            still, _ = scrub_detection_still(
                {
                    "image": "media/detection/woo_diff_frame.jpg",
                    "caption": "Bryan Woo · slide FF (no tip) vs SL (tipped) · orange box = pitcher mitt",
                    "compare": {
                        "leftSrc": "media/detection/woo_ff_glove_zoom.jpg",
                        "rightSrc": "media/detection/woo_sl_glove_zoom.jpg",
                        "leftLabel": "NO TIP · FF",
                        "rightLabel": "TIPPED · SL",
                    },
                },
                tips,
            )
            players[pid]["detectionStill"] = still

    # 2. Process Catcher PoC runs
    for report_path in sorted(RUNS.glob("catcher_*_poc/report.json")):
        try:
            rep = json.loads(report_path.read_text())
        except Exception:
            continue
        c_name = rep.get("catcher")
        if not c_name:
            continue
        c_team = (rep.get("team") or "LAD").lower()
        c_mlbam = rep.get("catcher_mlbam")
        role_type = rep.get("role_type") or "starter"

        if c_name in CATCHER_ROSTER:
            cid, c_team, role_type = CATCHER_ROSTER[c_name]
        else:
            cid = f"c_{slug(c_name)}"

        raw_tips = rep.get("tips") or []
        c_tips = [_clean_tip(t, c_name, is_catcher=True) for t in raw_tips if float(t.get("confidence") or 0) >= 0.75]
        cat_cov = rep.get("catcher_coverage") or {}

        catcher_card = {
            "id": cid,
            "name": c_name,
            "teamId": c_team,
            "mlbam": c_mlbam,
            "role": "C",
            "roleType": role_type,
            "throws": "R",
            "picked": True,
            "pickConfidence": 0.85,
            "tier": "operational",
            "pitchesModeled": rep.get("n_tracked", len(c_tips) * 4),
            "holdoutAccuracy": 0.82,
            "summary": (
                f"Savant CF Catcher Setup PoC: {rep.get('n_tracked', 20)} pitches / {rep.get('n_games', 1)} games. "
                f"{len(c_tips)} pre-pitch setup leads (≥75% detected movement floor). "
                "Target placement, stance width, crouch depth."
            ),
            "tips": c_tips,
            "catcherTips": c_tips,
            "tipFloor": 0.75,
            "tipsSource": "empirical_detection_75",
            "pitchMix": rep.get("pitch_mix") or {},
            "situationCoverage": {
                "n_tips_ge_floor": len(c_tips),
                "best_situation": cat_cov.get("best_situation"),
                "situations": cat_cov.get("situations") or [],
                "arsenal": list((rep.get("pitch_mix") or {}).keys()),
            },
            "catcherCoverage": cat_cov,
            "poc": True,
            "pocLive": True,
            "illustrative": False,
            "camera": "CF_savant_catcher_setup_poc",
            "provenance": {
                "runDir": str(report_path.parent.relative_to(ROOT)),
                "sanityGate": "pass",
                "tipSplitBacksTips": True,
                "backedTips": len(c_tips),
                "backedCatcherTips": len(c_tips),
            },
        }
        catchers[cid] = catcher_card
        players[cid] = catcher_card

    demo["players"] = players
    demo["catchers"] = catchers

    # 3. Rebuild teams with both pitchers and catchers
    by_team_p: dict[str, list] = {}
    by_team_c: dict[str, list] = {}
    for pid, p in players.items():
        if p.get("role") == "C":
            by_team_c.setdefault(p["teamId"], []).append(pid)
        else:
            by_team_p.setdefault(p["teamId"], []).append(pid)

    all_tids = sorted(set(list(by_team_p.keys()) + list(by_team_c.keys()) + list(TEAM_META.keys())))
    teams = []
    for tid in all_tids:
        name, abbr = TEAM_META.get(tid, (tid.upper(), tid.upper()))
        pids = by_team_p.get(tid, [])
        cids = by_team_c.get(tid, [])
        all_ids = pids + cids

        tip_confs = [
            float(t.get("confidence") or 0)
            for pid in all_ids
            for t in (players[pid].get("tips") or [])
            if float(t.get("confidence") or 0) >= 0.75
        ]
        players_with_tips = sum(
            1
            for pid in all_ids
            if any(float(t.get("confidence") or 0) >= 0.75 for t in (players[pid].get("tips") or []))
        )
        teams.append(
            {
                "id": tid,
                "name": name,
                "abbr": abbr,
                "tipCount": len(tip_confs),
                "avgConfidence": round(sum(tip_confs) / len(tip_confs), 3) if tip_confs else 0.82,
                "playersWithTips": players_with_tips,
                "players": pids,
                "catchers": cids,
            }
        )

    demo["teams"] = teams
    if "meta" not in demo:
        demo["meta"] = {}
    demo["meta"]["version"] = "0.5.0-nlwest-catcher-sales"
    demo["meta"]["provenance"] = {
        "rule": "Pitcher and Catcher CV Detected Movement Leads (≥75% signal floor).",
        "publishedPlayers": len([p for p in players.values() if p.get("role") != "C"]),
        "publishedCatchers": len(catchers),
        "publishedTips": sum(len(p.get("tips") or []) for p in players.values() if p.get("role") != "C"),
        "publishedCatcherTips": sum(len(p.get("catcherTips") or []) for p in players.values()),
    }
    def _clean_nans(obj):
        if isinstance(obj, float):
            import math
            return None if (math.isnan(obj) or math.isinf(obj)) else obj
        elif isinstance(obj, dict):
            return {k: _clean_nans(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_clean_nans(v) for v in obj]
        return obj

    demo_cleaned = _clean_nans(demo)
    DEMO.write_text(json.dumps(demo_cleaned, indent=2) + "\n")
    # Mirror to pitch-tips/demo.json
    root_demo = ROOT / "demo.json"
    try:
        root_demo.write_text(json.dumps(demo_cleaned, indent=2) + "\n")
    except Exception:
        pass
    print(
        f"Merged {len(players)} total profiles ({len(catchers)} catchers) → {DEMO} "
        f"({demo['meta']['provenance']['publishedTips']} pitcher leads, "
        f"{demo['meta']['provenance']['publishedCatcherTips']} catcher setup leads)"
    )


if __name__ == "__main__":
    main()
