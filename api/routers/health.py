"""GET /api/health and /api/version -- liveness/readiness for a load balancer
or a `docker` HEALTHCHECK, plus a small provenance string an operator can
paste into a bug report."""
from __future__ import annotations

import re

from fastapi import APIRouter

from ..db import database_ok
from ..schemas import HealthResponse, VersionResponse
from ..settings import ROOT, TESTS_BADGE

router = APIRouter(tags=["health"])

API_VERSION = "0.2.0"

_REV_RE = re.compile(r"^# rev (\d+) [—-]\s*(.+?)\s*\(", re.MULTILINE)


def _tests_badge() -> str:
    # Single source of truth: api/settings.py's TESTS_BADGE (README.md and
    # ml/README.md are kept in sync with it by hand). Previously this parsed
    # dashboard/README.md's badge text, which meant three places (this API,
    # the top-level README, ml/README.md) could each say a different count.
    return TESTS_BADGE


def _physics_rev() -> str | None:
    try:
        text = (ROOT / "params" / "CHANGELOG.md").read_text(encoding="utf-8")
        matches = _REV_RE.findall(text)
        if matches:
            n, title = matches[-1]
            return f"rev {n} — {title.strip()}"
    except OSError:
        pass
    return None


@router.get("/health", response_model=HealthResponse, summary="Liveness/readiness check")
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=API_VERSION,
        physics_rev=_physics_rev(),
        tests_badge=_tests_badge(),
        db_ok=database_ok(),
    )


@router.get("/version", response_model=VersionResponse, summary="API + physics provenance")
def version() -> VersionResponse:
    return VersionResponse(api_version=API_VERSION, physics_rev=_physics_rev(), tests_badge=_tests_badge())
