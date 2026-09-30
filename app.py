# app.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

import sqlite3
from fastapi import FastAPI

app = FastAPI()

DB_PATH = "tfl.db"


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