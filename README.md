# TfL Reliability Tracker

A full-stack app that tracks the live status of London's tube, DLR, Overground and Elizabeth line, and shows how reliable each line has been over time.

**Live:** [Netlify front end](tfl-tracker.netlify.app) · [API base](https://tfl-tracker.onrender.com)

## What it does

- **Ingests** live line status from the [TfL Unified API](https://api.tfl.gov.uk) on a schedule, and stores a snapshot of every line's status in a Postgres database.
- **Serves** two JSON endpoints via FastAPI: the current status of every line, and each line's "good service" percentage over a configurable time window.
- **Displays** the current status as a table and the reliability figures as a simple bar chart, in a single static HTML/JS page.

## Stack

- **Backend:** Python, FastAPI, PostgreSQL (via `psycopg2`)
- **Scheduling:** APScheduler, running in-process — no external cron or Task Scheduler needed
- **Front end:** plain HTML, CSS and JavaScript (`fetch`, no framework)
- **Hosting:** backend on Render (web service + managed Postgres), front end on Netlify

## Project structure

```
tfl-tracker/
├── ingest.py       # fetch, parse and save one snapshot of line statuses
├── app.py          # FastAPI app: serves /status and /reliability, runs ingest on a schedule
├── index.html      # front end: status table and reliability chart
├── app.js          # front end logic, calls the API
├── explore.py      # scratch file used to inspect the raw TfL API response
└── requirements.txt
```

## Running it locally

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows PowerShell
pip install -r requirements.txt
```

Set the database connection string for your session (use a Postgres instance — Render's free tier works, or a local Postgres install):

```powershell
$env:DATABASE_URL = "postgresql://user:password@host:port/dbname"
```

Then run the app:

```powershell
uvicorn app:app
```

On startup, the app immediately fetches and saves one snapshot, then repeats every 30 minutes for as long as the server keeps running. The `status_snapshots` table is created automatically on first run if it doesn't already exist.

Open `index.html` directly in a browser (with the server still running) to see the status table and reliability chart. In local development, `app.js` needs `API_BASE` set to `http://127.0.0.1:8000`; in production it points at the deployed Render URL instead.

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
    "is_good": true,
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
- **Ingest is scheduled in-process** with APScheduler rather than an OS-level tool like Windows Task Scheduler or cron, so the whole app — data collection included — runs from a single command and behaves the same way locally as it does deployed.
- **Postgres over SQLite**, specifically to survive deployment. The app started on SQLite during local development, but Render's free web service tier has an ephemeral filesystem — any local file gets wiped on restart or scale-to-zero — so accumulated history would be lost repeatedly. Render's managed Postgres persists independently of the web service's own restarts.
- **The reliability percentage measures how often the API reported "Good Service" when checked**, not train punctuality or a TfL-official reliability metric — it's a proxy based on sampling frequency (currently every 30 minutes).

## Deployment notes

- **Backend:** hosted on Render as a web service, started with `uvicorn app:app --host 0.0.0.0 --port $PORT`. The connection string is injected via the `DATABASE_URL` environment variable, pointing at a Render-managed Postgres instance in the same region.
- **Database:** Render PostgreSQL (free tier), connected over Render's internal network for the deployed service, and via the external connection string for local development. First load may take up to a minute if the backend has been idle due to using the free tier hosting.
- **Front end:** hosted on Netlify as a static site (no build step). `app.js` points `API_BASE` at the live Render URL in production.

## Possible next steps

- Automated tests (`pytest`) for `is_good_service`, `status_summary` and `parse`
- A longer-range reliability view (30/90 days) once more history has built up
- A "worst line this week" or trend indicator, now that history persists reliably
