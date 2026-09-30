# ingest.py

import os
import requests
from datetime import datetime, timezone
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")


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


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def save(rows):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS status_snapshots (
            id SERIAL PRIMARY KEY,
            fetched_at TIMESTAMPTZ NOT NULL,
            line_id TEXT NOT NULL,
            line_name TEXT NOT NULL,
            mode TEXT NOT NULL,
            is_good BOOLEAN NOT NULL,
            status_description TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_snap_line_time
        ON status_snapshots (line_id, fetched_at)
    """)

    fetched_at = datetime.now(timezone.utc)

    for row in rows:
        cursor.execute(
            "INSERT INTO status_snapshots (fetched_at, line_id, line_name, mode, is_good, status_description) VALUES (%s, %s, %s, %s, %s, %s)",
            (fetched_at, row["line_id"], row["line_name"], row["mode"], row["is_good"], row["status_description"])
        )

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    lines = fetch_statuses()
    if lines:
        rows = [parse(line) for line in lines]
        save(rows)
        print(f"Saved {len(rows)} rows")
    else:
        print("Skipping save, fetch failed")