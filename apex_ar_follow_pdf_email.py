#!/usr/bin/env python3
"""
Build and email a separate PDF for AR follow players flagged Private in ARFollow.xlsx.

Uses the same SMTP settings as apex_last_night_pdf_email.py but sends only to
APEX_AR_EMAIL_TO (default: colbym@apexbaseball.com,alecr@apexbaseball.com).

Input: apex_dashboard_data.json (run apex_dashboard_builder.py first).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from apex_last_night_pdf_email import (
    OUT_JSON,
    _draw_data_row,
    _draw_header_row,
    _fmt_avg,
    _fmt_era,
    _fmt_num,
    _fmt_ops,
    _org_cell,
    _pdf_row_view,
    _pdf_usable_width,
    _player_cell,
    _pos_short,
    _scale_cols,
    _send_pdf_smtp,
    _sort_rows_by_name,
    _stat_val,
    pdf_row_for_last_night_email,
)

DEFAULT_AR_TO = "colbym@apexbaseball.com,alecr@apexbaseball.com"


def _watch_row_to_pdf_row(row: dict[str, Any], report_date: str) -> dict[str, Any]:
    pos = str(row.get("position") or "")
    is_pitcher = bool(row.get("is_pitcher")) or bool(
        __import__("re").search(r"\b(RHP|LHP|SP|RP|P)\b", pos, __import__("re").I)
    )
    summer_ln = row.get("summer_last_night") or {}
    school_ln = row.get("last_night") or {}
    summer_se = row.get("summer_season") or {}
    school_se = row.get("season") or {}
    team = str(row.get("summer_team") or row.get("program") or row.get("school") or "").strip()
    return {
        "name": row.get("name", ""),
        "position": pos or ("P" if is_pitcher else "H"),
        "organization": team,
        "current_team": team,
        "is_pitcher": is_pitcher,
        "stats_context": "summer" if summer_se or summer_ln else "",
        "season": summer_se if summer_se else school_se,
        "month_to_date": row.get("month_to_date") or {},
        "last_night": summer_ln if summer_ln else school_ln,
        "summer_season": summer_se,
        "summer_last_night": summer_ln,
        "last_night_date": report_date,
    }


def _season_ops(se: dict[str, Any]) -> Any:
    obp, slg, ops = se.get("obp"), se.get("slg"), se.get("ops")
    if (ops in (None, "", 0)) and obp not in (None, "") and slg not in (None, ""):
        try:
            return float(obp) + float(slg)
        except Exception:
            return ops
    return ops


def write_ar_follow_pdf(rows: list[dict[str, Any]], data: dict[str, Any], out_path: Path) -> None:
    try:
        from fpdf import FPDF
    except ImportError as e:  # pragma: no cover
        raise SystemExit(
            "Missing fpdf2. Install: pip install fpdf2\n"
            "Or: pip install -r apex_dashboard_requirements.txt"
        ) from e

    report_date = str(data.get("last_night_date") or "").strip()
    generated = str(data.get("generated_at") or "")[:19]
    pdf_rows = [_pdf_row_view(_watch_row_to_pdf_row(r, report_date)) for r in rows]
    ln_rows = [r for r in pdf_rows if pdf_row_for_last_night_email(r, report_date)]
    has_season = [r for r in pdf_rows if (r.get("season") or {})]

    pdf = FPDF(orientation="L", unit="mm", format="Legal")
    pdf.set_margins(4, 8, 4)
    pdf.set_auto_page_break(auto=True, margin=8)
    pdf.add_page()
    usable_w = _pdf_usable_width(pdf)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, f"Apex AR Follow - travel/summer ({report_date or 'report'})", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 5, f"Generated {generated}   |   Private AR follow list", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    b_headers = [
        "Player",
        "Program / School",
        "Pos",
        "AB",
        "R",
        "H",
        "RBI",
        "BB",
        "K",
        "HR",
        "2B",
        "SB",
        "AVG",
        "OPS",
    ]
    b_base = [34, 52, 9, 8, 7, 7, 8, 7, 7, 7, 7, 7, 9, 9]
    b_w = _scale_cols(b_base, usable_w)
    b_align = ["L", "L", "C"] + ["C"] * (len(b_headers) - 3)

    p_headers = ["Player", "Program / School", "Pos", "IP", "H", "R", "ER", "BB", "K", "HR", "ERA"]
    p_base = [34, 52, 9, 8, 7, 7, 7, 7, 7, 7, 9]
    p_w = _scale_cols(p_base, usable_w)
    p_align = ["L", "L", "C"] + ["C"] * (len(p_headers) - 3)

    def batter_cells(r: dict[str, Any], *, last_night: bool) -> list[str]:
        block = r.get("last_night") if last_night else r.get("season")
        block = block or {}
        se = r.get("season") or {}
        return [
            _player_cell(r),
            _org_cell(r),
            _pos_short(str(r.get("position") or "")),
            _fmt_num(_stat_val(block, "atBats")),
            _fmt_num(_stat_val(block, "runs")),
            _fmt_num(_stat_val(block, "hits")),
            _fmt_num(_stat_val(block, "rbi")),
            _fmt_num(_stat_val(block, "baseOnBalls")),
            _fmt_num(_stat_val(block, "strikeOuts")),
            _fmt_num(_stat_val(block, "homeRuns")),
            _fmt_num(_stat_val(block, "doubles")),
            _fmt_num(_stat_val(block, "stolenBases")),
            _fmt_avg(block.get("avg") if last_night else se.get("avg")),
            _fmt_ops(_season_ops(block if last_night else se)),
        ]

    def pitcher_cells(r: dict[str, Any], *, last_night: bool) -> list[str]:
        block = r.get("last_night") if last_night else r.get("season")
        block = block or {}
        se = r.get("season") or {}
        return [
            _player_cell(r),
            _org_cell(r),
            _pos_short(str(r.get("position") or "")),
            _fmt_num(_stat_val(block, "inningsPitched")),
            _fmt_num(_stat_val(block, "hits")),
            _fmt_num(_stat_val(block, "runs")),
            _fmt_num(_stat_val(block, "earnedRuns")),
            _fmt_num(_stat_val(block, "baseOnBalls")),
            _fmt_num(_stat_val(block, "strikeOuts")),
            _fmt_num(_stat_val(block, "homeRuns")),
            _fmt_era(block.get("era") if last_night else se.get("era")),
        ]

    row_zebra = 0

    if ln_rows:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Last Night", new_x="LMARGIN", new_y="NEXT")
        hitters = [r for r in ln_rows if not r.get("is_pitcher")]
        pitchers = [r for r in ln_rows if r.get("is_pitcher")]
        if hitters:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "Hitters", new_x="LMARGIN", new_y="NEXT")
            _draw_header_row(pdf, b_headers, b_w)
            for r in _sort_rows_by_name(hitters):
                _draw_data_row(pdf, batter_cells(r, last_night=True), b_w, bool(row_zebra % 2), b_align)
                row_zebra += 1
            pdf.ln(2)
        if pitchers:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "Pitchers", new_x="LMARGIN", new_y="NEXT")
            _draw_header_row(pdf, p_headers, p_w)
            for r in _sort_rows_by_name(pitchers):
                _draw_data_row(pdf, pitcher_cells(r, last_night=True), p_w, bool(row_zebra % 2), p_align)
                row_zebra += 1
            pdf.ln(2)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Season", new_x="LMARGIN", new_y="NEXT")
    season_hitters = [r for r in has_season if not r.get("is_pitcher")]
    season_pitchers = [r for r in has_season if r.get("is_pitcher")]
    if season_hitters:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Hitters", new_x="LMARGIN", new_y="NEXT")
        _draw_header_row(pdf, b_headers, b_w)
        for r in _sort_rows_by_name(season_hitters):
            _draw_data_row(pdf, batter_cells(r, last_night=False), b_w, bool(row_zebra % 2), b_align)
            row_zebra += 1
        pdf.ln(2)
    if season_pitchers:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Pitchers", new_x="LMARGIN", new_y="NEXT")
        _draw_header_row(pdf, p_headers, p_w)
        for r in _sort_rows_by_name(season_pitchers):
            _draw_data_row(pdf, pitcher_cells(r, last_night=False), p_w, bool(row_zebra % 2), p_align)
            row_zebra += 1
        pdf.ln(2)

    if not ln_rows and not has_season:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, "No stats available yet for private AR follow players.", new_x="LMARGIN", new_y="NEXT")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))


def _ar_email_sent_marker_path() -> Path:
    return Path(os.environ.get("APEX_AR_EMAIL_SENT_FILE", str(OUT_JSON.parent / ".apex_ar_email_sent_date")))


def _already_sent_for_report_date(report_date: str) -> bool:
    if os.environ.get("APEX_FORCE_AR_EMAIL", "").strip().lower() in ("1", "true", "yes"):
        return False
    try:
        return _ar_email_sent_marker_path().read_text(encoding="utf-8").strip() == report_date
    except OSError:
        return False


def _mark_sent_for_report_date(report_date: str) -> None:
    _ar_email_sent_marker_path().write_text(report_date, encoding="utf-8")


def main() -> int:
    if not OUT_JSON.is_file():
        print(f"Missing {OUT_JSON}", file=sys.stderr)
        return 1

    with open(OUT_JSON, encoding="utf-8") as f:
        data = json.load(f)

    ar_rows = [
        r
        for r in ((data.get("watch_list") or {}).get("AR") or [])
        if isinstance(r, dict) and r.get("private_email")
    ]
    if not ar_rows:
        print("No private AR follow players in JSON; skipping AR PDF.")
        return 0

    last_date = str(data.get("last_night_date") or "unknown").replace("/", "-")
    out_dir = Path(os.environ.get("APEX_PDF_OUT_DIR", str(OUT_JSON.parent))).resolve()
    pdf_path = out_dir / f"apex_ar_follow_{last_date}.pdf"

    write_ar_follow_pdf(ar_rows, data, pdf_path)
    print(f"Wrote {pdf_path} ({len(ar_rows)} private AR row(s))")

    if _already_sent_for_report_date(last_date):
        print(
            f"Already emailed AR follow for last_night_date={last_date}; skipping send "
            f"(set APEX_FORCE_AR_EMAIL=1 to send again)."
        )
        return 0

    to_addr = os.environ.get("APEX_AR_EMAIL_TO", DEFAULT_AR_TO).strip() or DEFAULT_AR_TO
    prev_to = os.environ.get("APEX_PDF_EMAIL_TO")
    os.environ["APEX_PDF_EMAIL_TO"] = to_addr
    subject = f"Apex AR follow - travel/summer ({last_date})"
    body = (
        f"Private AR follow list for {last_date}.\n"
        f"Data generated_at: {data.get('generated_at')}\n\n"
        f"PDF attached: {pdf_path.name}\n"
    )
    try:
        _send_pdf_smtp(pdf_path, subject, body)
    except Exception as e:
        print(f"AR follow email failed: {e}", file=sys.stderr)
        return 2
    finally:
        if prev_to is None:
            os.environ.pop("APEX_PDF_EMAIL_TO", None)
        else:
            os.environ["APEX_PDF_EMAIL_TO"] = prev_to

    _mark_sent_for_report_date(last_date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
