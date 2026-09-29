# ingest.py

import sqlite3
import requests
from datetime import datetime, timezone


def fetch_statuses():
    url = "https://api.tfl.gov.uk/Line/Mode/tube,dlr,overground,elizabeth-line/Status"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"Fetch failed: {e}")
        return None


def is_good_service(line):
    return all(status["statusSeverity"] == 10 for status in line["lineStatuses"])


def status_summary(line):
    return "; ".join(s["statusSeverityDescription"] for s in line["lineStatuses"])


def parse(line):
    return {
        "line_id": line["id"],
        "line_name": line["name"],
        "mode": line["modeName"],
        "is_good": is_good_service(line),
        "status_description": status_summary(line),
    }


def save(rows):
    conn = sqlite3.connect("tfl.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS status_snapshots (
            id INTEGER PRIMARY KEY,
            fetched_at TEXT NOT NULL,
            line_id TEXT NOT NULL,
            line_name TEXT NOT NULL,
            mode TEXT NOT NULL,
            is_good INTEGER NOT NULL,
            status_description TEXT NOT NULL
        )
    """)

    fetched_at = datetime.now(timezone.utc).isoformat()

    for row in rows:
        cursor.execute(
            "INSERT INTO status_snapshots (fetched_at, line_id, line_name, mode, is_good, status_description) VALUES (?, ?, ?, ?, ?, ?)",
            (fetched_at, row["line_id"], row["line_name"], row["mode"], row["is_good"], row["status_description"])
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    lines = fetch_statuses()
    if lines:
        rows = [parse(line) for line in lines]
        save(rows)
        print(f"Saved {len(rows)} rows")
    else:
        print("Skipping save, fetch failed")