# app.py

import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from ingest import fetch_statuses, parse, save

DB_PATH = "tfl.db"


def run_ingest():
    lines = fetch_statuses()
    if lines:
        rows = [parse(line) for line in lines]
        save(rows)
        print(f"[scheduler] Saved {len(rows)} rows")
    else:
        print("[scheduler] Skipping save, fetch failed")


scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_ingest()  # one immediate run on startup
    scheduler.add_job(run_ingest, "interval", minutes=30)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/status")
def current_status():
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.line_id, s.line_name, s.mode, s.is_good, s.status_description, s.fetched_at
        FROM status_snapshots s
        WHERE s.fetched_at = (
            SELECT MAX(fetched_at) FROM status_snapshots WHERE line_id = s.line_id
        )
        ORDER BY s.line_name
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/reliability")
def reliability(days: int = 7):
    conn = get_connection()
    rows = conn.execute("""
        SELECT line_id, line_name,
               ROUND(100.0 * SUM(is_good) / COUNT(*), 1) AS pct_good,
               COUNT(*) AS sample_count
        FROM status_snapshots
        WHERE fetched_at >= datetime('now', ?)
        GROUP BY line_id
        ORDER BY line_name
    """, (f"-{days} days",)).fetchall()
    conn.close()
    return [dict(row) for row in rows]