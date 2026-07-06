#!/usr/bin/env python3
"""Rebuild summer HS + AR stats for a report date and write preview PDFs (no email)."""
from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apex_ar_follow_pdf_email import write_ar_follow_pdf
from apex_dashboard_builder import (
    AR_FOLLOW_SOURCE_XLSX,
    HS_SOURCE_XLSX,
    OUT_JSON,
    GameChangerIndex,
    _norm_player_name,
    _norm_token,
    attach_summer_travel_stats,
    build_ar_follow_rows,
    build_high_school_payloads,
    get_gamechanger_client,
    load_high_school_clients,
    report_anchor_date,
)
from apex_last_night_pdf_email import pdf_row_for_last_night_email, write_last_night_pdf


def main() -> int:
    report = (sys.argv[1] if len(sys.argv) > 1 else "2026-07-03").strip()
    os.environ["APEX_REPORT_DATE"] = report[:10]

    gc = get_gamechanger_client()
    idx = GameChangerIndex.build(gc, _norm_player_name, _norm_token) if gc else None

    hs_rows: list[dict] = []
    for entry in load_high_school_clients(HS_SOURCE_XLSX):
        rows = build_high_school_payloads(entry)
        attach_summer_travel_stats(rows, entry, gc, idx)
        for row in rows:
            row["last_night_date"] = report_anchor_date().isoformat()
        hs_rows.extend(rows)

    ar_rows = build_ar_follow_rows(AR_FOLLOW_SOURCE_XLSX, gc_client=gc, gc_index=idx)

    data: dict = {}
    if OUT_JSON.is_file():
        data = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    data["last_night_date"] = report[:10]
    data["generated_at"] = datetime.now(UTC).isoformat()
    data["high_school_clients"] = hs_rows
    watch = data.get("watch_list") if isinstance(data.get("watch_list"), dict) else {}
    watch["AR"] = ar_rows
    data["watch_list"] = watch

    out_dir = Path(os.environ.get("APEX_PDF_OUT_DIR", str(ROOT))).resolve()
    preview_json = out_dir / f"apex_dashboard_preview_{report[:10]}.json"
    preview_json.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")

    main_pdf = out_dir / f"apex_last_night_{report[:10]}_PREVIEW.pdf"
    ar_pdf = out_dir / f"apex_ar_follow_{report[:10]}_PREVIEW.pdf"
    write_last_night_pdf(data, main_pdf)
    ar_priv = [r for r in ar_rows if isinstance(r, dict) and r.get("private_email")]
    write_ar_follow_pdf(ar_priv, data, ar_pdf)

    anchor = report[:10]
    hs_ln = [
        r
        for r in hs_rows
        if isinstance(r, dict) and pdf_row_for_last_night_email(r, anchor)
    ]
    ar_ln = [
        r
        for r in ar_priv
        if (r.get("summer_last_night") or r.get("last_night"))
    ]

    print(f"Report date: {anchor}")
    print(f"JSON: {preview_json}")
    print(f"Main PDF: {main_pdf}  ({len(hs_ln)} HS summer last-night row(s))")
    print(f"AR PDF:   {ar_pdf}  ({len(ar_ln)} private AR row(s) with lines)")
    for r in hs_ln:
        print(f"  HS: {r.get('name')} — {r.get('summer_team') or r.get('current_team')}")
    for r in ar_priv:
        sln = r.get("summer_last_night") or {}
        if sln:
            print(f"  AR: {r.get('name')} — {r.get('summer_team') or r.get('program')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
