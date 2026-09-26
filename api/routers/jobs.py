"""GET /api/jobs/{id} -- poll a background job started by /api/optimize,
/api/recommend/physics, /api/calibrate or a live POST /api/uq."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import jobs as jobs_module
from ..schemas import JobResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobResponse, summary="Poll a background job")
def get_job(job_id: str):
    job = jobs_module.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"job {job_id} not found")
    return jobs_module.job_to_dict(job)


@router.get("", response_model=list[JobResponse], summary="List recent background jobs")
def list_jobs(limit: int = 50):
    return [jobs_module.job_to_dict(j) for j in jobs_module.list_jobs(limit=limit)]
