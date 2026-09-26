"""Pydantic request/response models for every endpoint -- typed, with
OpenAPI examples, so `/docs` is a usable contract instead of `dict[str, Any]`
everywhere. Nothing here computes anything; it only shapes what
twin/ml already returned (see docs/SPEC.md for the underlying schema).
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    error: str


# ---------------------------------------------------------------------------
# /api/params
# ---------------------------------------------------------------------------
class ParamsResponse(BaseModel):
    """The full params/field_params.json tree, passed through verbatim --
    its shape is defined by that file, not by this API."""
    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# /api/simulate
# ---------------------------------------------------------------------------
class SimulateQuery(BaseModel):
    steam_t: float = Field(..., description="Steam volume injected, tonnes", examples=[1300.0])
    soak_days: float = Field(..., description="Soak period, days", examples=[10.0])
    cutoff: float = Field(..., description="Economic cutoff oil rate, m3/d", examples=[1.3])
    spm: float = Field(..., description="Sucker-rod pump strokes per minute", examples=[5.0])
    stroke_in: float | None = Field(
        default=None,
        description="Polished-rod stroke length, in -- one of the six API Spec 11E "
        "sizes (64/74/86/100/120/144). Omit to use the params' own stroke.",
        examples=[64.0],
    )
    p_wellhead_kgf_cm2: float | None = Field(
        default=None,
        description="Injection (wellhead) pressure, kgf/cm2 g -- CONFIRMED range "
        "85-97. Omit to use the params' own pressure.",
        examples=[85.0],
    )


class SimulateResponse(BaseModel):
    summary: dict[str, Any]
    series: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# /api/optimize (surrogate, async job) and /api/recommend/physics (grid, async job)
# ---------------------------------------------------------------------------
class OptimizeRequest(BaseModel):
    fixed: dict[str, float | str] | None = Field(
        default=None,
        description="Hold these of {steam_t, soak_days, cutoff_m3d, spm, "
        "p_wellhead_kgf_cm2, stroke_in, float_policy} constant (collapses that "
        "dimension out of the search). float_policy (rev 13) is a string: one "
        "of pull / vfd_hold / vfd_then_pull.",
        examples=[{"soak_days": 10.0, "float_policy": "vfd_hold"}],
    )
    spm_band: tuple[float, float] | None = Field(
        default=None,
        description="Override the SPM search band (default: params.srp.spm_practice_band).",
        examples=[[3.0, 6.0]],
    )


class RecommendPhysicsRequest(OptimizeRequest):
    objective: str = Field(
        default="margin_incremental_inr_per_cycle_day",
        description="Key of the physics-verified summary to maximise.",
    )
    grid: dict[str, int] | None = Field(
        default=None,
        description="Point counts {steam_t, cutoff_m3d, spm}; default 15/15/7.",
    )


# ---------------------------------------------------------------------------
# /api/calibrate
# ---------------------------------------------------------------------------
class CalibrateJsonRequest(BaseModel):
    rows: list[dict[str, Any]] | None = None


class CalibrateResponse(BaseModel):
    fitted_params: dict[str, float]
    bounds: dict[str, list[float]]
    residual_table: list[dict[str, Any]]
    rmse: dict[str, float]
    identifiability: dict[str, Any]
    n_cycles: int
    recommendation: dict[str, Any] | None = None
    recommendation_before_calibration: dict[str, Any] | None = None
    recommendation_after_calibration: dict[str, Any] | None = None
    hidden_truth: dict[str, float] | None = None


# ---------------------------------------------------------------------------
# /api/uq
# ---------------------------------------------------------------------------
class UqLiveRequest(BaseModel):
    n_draws: int = Field(default=200, le=300, ge=10, description="Monte Carlo draws, capped at 300 for a live run.")
    seed: int = Field(default=42)


# ---------------------------------------------------------------------------
# /api/dyno/cards
# ---------------------------------------------------------------------------
class DynoCardsQuery(BaseModel):
    spm: float = Field(..., description="Strokes per minute")
    mu_cP: float = Field(..., description="Oil viscosity, cP")
    fillage: float = Field(default=1.0, description="Plunger fill fraction (0-1]")
    water_cut: float = Field(default=0.85, description="Tubing-liquid water cut")


class DynoCardsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# /api/dyno/classify -- measured surface dynamometer card, 27 Sep 2026
# ---------------------------------------------------------------------------
class DynoClassifyRequest(BaseModel):
    """JSON body for POST /api/dyno/classify (a multipart CSV upload -- field
    'file' -- is accepted as an alternative, with no JSON body)."""
    position: list[float] = Field(..., description="Polished-rod position samples (any consistent unit)")
    load: list[float] = Field(..., description="Polished-rod load samples (any consistent unit)")
    units: str | dict[str, str] | None = Field(
        default=None,
        description="'position,load' (e.g. 'in,klbf') or {'position':.., 'load':..}; "
        "omitted/unrecognised axes are auto-detected by magnitude.",
        examples=["m,kN"],
    )


class DynoClassifyResponse(BaseModel):
    card_type: str
    probabilities: dict[str, float]
    fillage_est: float
    peak_kN: float
    min_kN: float
    sentence_en: str
    sentence_hi: str
    quality_flags: dict[str, Any]
    model_caveat: str


class DynoClassifyDemoResponse(BaseModel):
    scenario: str
    cards: list[dict[str, Any]]
# /api/schedule -- field-level steam scheduler (ml.schedule)
# ---------------------------------------------------------------------------
class ScheduleRequest(BaseModel):
    wells: list[dict[str, Any]] | None = Field(
        default=None,
        description="One dict per well, same columns as "
        "data/external/field_wells_synthetic.csv (well_id and "
        "days_since_last_cycle required; other columns fall back to "
        "params/field_params.json field-wide defaults if omitted).",
    )
    csv_text: str | None = Field(
        default=None,
        description="Alternative to `wells`: the wells CSV as raw text.",
    )
    grid: dict[str, int] | None = Field(
        default=None,
        description="Override the per-well physics search grid point counts "
        "{steam_t, cutoff_m3d, spm}; default is a reduced 6x6x4 (144 pts/well).",
    )
    horizon_days: float = Field(default=365.0, description="Scheduling horizon, days.")


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------
JobStatus = Literal["pending", "running", "done", "error"]


class JobResponse(BaseModel):
    id: str
    kind: str
    status: JobStatus
    result: Any | None = None
    error: str | None = None
    created_at: str
    updated_at: str


class JobCreatedResponse(BaseModel):
    job_id: str
    status_url: str


# ---------------------------------------------------------------------------
# /api/runs
# ---------------------------------------------------------------------------
class RunOut(BaseModel):
    id: int
    steam_t: float
    soak_days: float
    cutoff_m3d: float
    spm: float
    summary: dict[str, Any]
    source: str
    created_at: str


# ---------------------------------------------------------------------------
# /api/health, /api/version
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    version: str
    physics_rev: str | None = None
    tests_badge: str
    db_ok: bool


class VersionResponse(BaseModel):
    api_version: str
    physics_rev: str | None = None
    tests_badge: str
