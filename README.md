# TfL reliability tracker
# TfL Reliability Tracker

A full-stack app that tracks the live status of London's tube, DLR, Overground and Elizabeth line, and shows how reliable each line has been over time.

## What it does

- **Ingests** live line status from the [TfL Unified API](https://api.tfl.gov.uk) on a schedule, and stores a snapshot of every line's status in a SQLite database.
- **Serves** two JSON endpoints via FastAPI: the current status of every line, and each line's "good service" percentage over a configurable time window.
- **Displays** the current status as a table and the reliability figures as a simple bar chart, in a single static HTML/JS page.

## Stack

- **Backend:** Python, FastAPI, SQLite
- **Scheduling:** APScheduler, running in-process (no external cron or Task Scheduler needed)
- **Front end:** plain HTML, CSS and JavaScript (`fetch`, no framework)

## Project structure

```
tfl-tracker/
├── ingest.py       # fetch, parse and save one snapshot of line statuses
├── app.py          # FastAPI app: serves /status and /reliability, runs ingest on a schedule
├── index.html      # front end: status table and reliability chart
├── app.js          # front end logic, calls the API
├── explore.py      # scratch file used to inspect the raw TfL API response
├── tfl.db          # SQLite database (not committed — created on first run)
└── requirements.txt
```

## Running it locally

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows PowerShell
pip install -r requirements.txt

uvicorn app:app
```

On startup, the app immediately fetches and saves one snapshot, then repeats every 30 minutes for as long as the server keeps running. `tfl.db` is created automatically on first run.

Open `index.html` directly in a browser (with the server still running) to see the status table and reliability chart. The front end calls the API at `http://127.0.0.1:8000`.

API docs (interactive): `http://127.0.0.1:8000/docs`

## API

### `GET /status`
Returns the latest known status for every line.

```json
[
  {
    "line_id": "bakerloo",
    "line_name": "Bakerloo",
    "mode": "tube",
    "is_good": 1,
    "status_description": "Good Service",
    "fetched_at": "2026-09-29T13:17:00.692811+00:00"
  }
]
```

### `GET /reliability?days=7`
Returns the percentage of checks in the last `days` (default 7) where each line was on "Good Service".

```json
[
  {
    "line_id": "central",
    "line_name": "Central",
    "pct_good": 94.3,
    "sample_count": 88
  }
]
```

## Design decisions worth noting

- **A line can report more than one status at once.** For example, the Metropolitan line can show "Minor Delays" on one section and "Severe Delays" on another at the same time, since the API returns a list of statuses per line rather than a single value. A line is only counted as "good service" if *every* reported status for it is severity 10 (`is_good_service`); otherwise all of its current status descriptions are joined together for display (`status_summary`).
- **One `fetched_at` timestamp per ingest run**, shared across all 19 lines, so reliability can be calculated consistently across a single point in time rather than per-line timestamps drifting apart.
- **Ingest is scheduled in-process** with APScheduler rather than an OS-level tool like Windows Task Scheduler or cron, so the whole app — data collection included — runs from a single command and would behave the same way if deployed elsewhere.
- **The reliability percentage measures how often the API reported "Good Service" when checked**, not train punctuality or a TfL-official reliability metric — it's a proxy based on sampling frequency (currently every 30 minutes).

## A note on deployment

This README assumes the FastAPI backend and SQLite database run on a server that stays on (a VM, a small always-on host, etc.), since it needs to actually execute Python on a schedule and persist a local database file. A static host such as Netlify can serve `index.html` and `app.js`, but not `app.py` — the backend needs to be hosted separately (for example, on Render, Fly.io or a small VPS), and `app.js` should point `API_BASE` at that backend's public URL instead of `http://127.0.0.1:8000`.

## Possible next steps

- Automated tests (`pytest`) for `is_good_service`, `status_summary` and `parse`
- Switch from SQLite to PostgreSQL for a hosted deployment
- Add a longer-range reliability view (30/90 days) once more history has built up
