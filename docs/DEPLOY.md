# Deploying the Baghewala Digital Twin

One process (FastAPI + Uvicorn) serves both the `/api/...` backend and the
dashboard (`dashboard/`) at `/`. SQLite by default; no external service
required for a demo deployment.

## Local run

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
node dashboard/build.js
.venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000
```
or on Windows: `.\scripts\dev.ps1` (rebuilds the dashboard, then runs the server).
Open `http://127.0.0.1:8000/`. `GET /api/health` and `/docs` (OpenAPI) confirm it's up.

## Docker

```
docker build -t baghewala-digital-twin .
docker run --rm -p 8000:8000 -v twin-data:/app/data baghewala-digital-twin
```
or `docker compose up` (add `--profile postgres` to also start a Postgres
container -- see "Switching to Postgres" below). The image runs as a
non-root user, has a `HEALTHCHECK` against `/api/health`, and excludes
`.venv/`, `ppt/` and `docs/study/` from the build context (`.dockerignore`).

## Render

`render.yaml` defines a single Docker web service with `healthCheckPath:
/api/health` and a 1 GB persistent disk mounted at `/app/data` (so
`data/twin.db` survives restarts/redeploys). In the Render dashboard: **New
+ → Blueprint**, point at this repo, accept the plan. Free-tier services
spin down on idle -- see "Known limits" below.

## Railway

`railway.json` points Railway at the same `Dockerfile` and healthcheck.
`railway up` (or connect the repo in the Railway dashboard) deploys it
directly; add a volume at `/app/data` for persistence, or switch to Postgres.

## Fly.io

```
fly launch --no-deploy   # detects fly.toml, keep the settings it finds
fly volumes create twin_data --size 1 --region bom
fly deploy
```
`fly.toml` scales to zero machines when idle (`min_machines_running = 0`) --
expect a cold start on the first request after a quiet period.

## VPS (systemd)

```
git clone <repo> && cd sih-baghewala
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
node dashboard/build.js
```
Unit file:
```ini
[Unit]
Description=Baghewala Digital Twin
After=network.target

[Service]
WorkingDirectory=/opt/sih-baghewala
Environment=PORT=8000
ExecStart=/opt/sih-baghewala/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
User=www-data

[Install]
WantedBy=multi-user.target
```
`systemctl enable --now baghewala-twin`, then put nginx/Caddy in front for TLS.

## Environment variables

`.env.example` (copy to `.env` for local overrides, or set as process env
vars on each platform above):

| Var | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/twin.db` | relative sqlite paths resolve against the repo root, not cwd |
| `CORS_ORIGINS` | `*` | comma-separated allowed origins, or `*` |
| `PARAMS_PATH` | `params/field_params.json` | |
| `ENV` | `development` | informational only today |
| `PORT` | `8000` | |

## Switching to Postgres

Set `DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname` and
`pip install psycopg[binary]` (not in `requirements.txt` by default, to keep
the SQLite-only path dependency-free). `api/db.py`'s
`SQLModel.metadata.create_all()` creates the same tables (`Run`,
`Recommendation`, `Calibration`, `Job`) on first start; no migration step.

## What is persisted

`data/twin.db` (SQLite): simulate-run history (`/api/runs`), saved
recommendations/calibrations, and the background-job table
(`/api/jobs/{id}`). Nothing else — `params/field_params.json` is read fresh
from disk on every request; the trained ML models under `ml/models/*` are
loaded from the image/checkout, not the database.

## Known limits

- **Single process.** Background jobs (`/api/optimize`,
  `/api/recommend/physics`, `/api/calibrate`) run in-process via FastAPI
  `BackgroundTasks` — fine for one demo instance, but jobs are lost on
  restart mid-run and there is no multi-worker fan-out (a real
  multi-instance deployment would need Celery/RQ + a shared broker instead).
- **Cold start on free tiers.** Render's free plan and Fly's scale-to-zero
  both spin the container down on idle; the first request after that takes
  several seconds longer than `/api/health` alone would suggest.
- **`/api/optimize` takes 10–20 s** (skopt `gp_minimize`, 60 calls);
  `/api/recommend/physics` is a similar order (a 15×15×7 physics grid) —
  both run as jobs for this reason; poll `GET /api/jobs/{id}` rather than
  expecting a synchronous response.
- SQLite has no built-in replication — fine for a demo, not for multi-region
  or high-write-concurrency production use (switch to Postgres above).
