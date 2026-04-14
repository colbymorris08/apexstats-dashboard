#!/usr/bin/env python3
from __future__ import annotations

import json
import threading
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, send_from_directory

from apex_dashboard_builder import OUT_JSON, write_dashboard_data

APP_DIR = Path("/Users/colbymorris/apexstats")
REFRESH_HOURS = 6

app = Flask(__name__, static_folder=str(APP_DIR), static_url_path="")
lock = threading.Lock()
scheduler = BackgroundScheduler()


def refresh_data_job() -> None:
    with lock:
        write_dashboard_data(OUT_JSON)


@app.get("/api/data")
def api_data():
    if not OUT_JSON.is_file():
        refresh_data_job()
    return jsonify(json.loads(OUT_JSON.read_text()))


@app.post("/api/refresh")
def api_refresh():
    refresh_data_job()
    return jsonify({"ok": True, "file": str(OUT_JSON)})


@app.get("/")
def index():
    return send_from_directory(str(APP_DIR), "apex_dashboard.html")


def start_scheduler() -> None:
    scheduler.add_job(refresh_data_job, "interval", hours=REFRESH_HOURS, id="refresh", replace_existing=True)
    scheduler.start()


if __name__ == "__main__":
    if not OUT_JSON.is_file():
        refresh_data_job()
    start_scheduler()
    app.run(host="0.0.0.0", port=8011, debug=False)
