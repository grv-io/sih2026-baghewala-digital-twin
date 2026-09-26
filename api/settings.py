"""Runtime configuration, read from the environment (and an optional .env
file) via pydantic-settings. Every setting has a sane local-dev default so
`uvicorn api.main:app` works with zero configuration.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root -- resolved from this file's location, not the process cwd, so
# behaviour is identical whether launched as `python api/main.py`,
# `uvicorn api.main:app`, from a Docker WORKDIR, or from a test runner.
ROOT = Path(__file__).resolve().parents[1]

# Single source of truth for the "tests passing" badge surfaced by
# GET /api/health and GET /api/version (api/routers/health.py). Update this
# one string after a full-suite run instead of duplicating the count in
# README.md's Quickstart/Status sections -- keep those in sync by hand from
# this value.
TESTS_BADGE = "263 passed · 2 xfail (soak; steam optimum at the mid-range diesel price) — 27 Sep 2026"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # SQLite by default (see api/db.py for how a relative sqlite:/// path is
    # resolved against ROOT); point at postgresql+psycopg://... for Postgres.
    database_url: str = "sqlite:///./data/twin.db"

    # Comma-separated list, or "*" for any origin (the local/demo default).
    cors_origins: str = "*"

    params_path: Path = ROOT / "params" / "field_params.json"

    env: str = "development"
    port: int = 8000

    # Test-only knobs (never read outside tests/test_api.py): let the test
    # suite shrink the Bayesian optimizer's search budget so `/api/optimize`
    # job tests finish in well under 5 s instead of ml/optimize.py's default
    # N_CALLS=60/N_INITIAL_POINTS=15 full search.
    optimize_n_calls: int | None = None
    optimize_n_initial_points: int | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
