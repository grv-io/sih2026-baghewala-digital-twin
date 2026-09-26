"""GET/DELETE /api/runs -- simulate history (the `Run` table)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from ..db import Run, engine
from ..schemas import RunOut

router = APIRouter(prefix="/runs", tags=["runs"])


def _run_out(run: Run) -> RunOut:
    return RunOut(
        id=run.id, steam_t=run.steam_t, soak_days=run.soak_days, cutoff_m3d=run.cutoff_m3d,
        spm=run.spm, summary=run.summary(), source=run.source, created_at=run.created_at.isoformat(),
    )


@router.get("", response_model=list[RunOut], summary="List recent simulate runs")
def list_runs(limit: int = 50):
    with Session(engine) as session:
        stmt = select(Run).order_by(Run.created_at.desc()).limit(limit)
        return [_run_out(r) for r in session.exec(stmt)]


@router.get("/{run_id}", response_model=RunOut, summary="Get one run")
def get_run(run_id: int):
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"run {run_id} not found")
        return _run_out(run)


@router.delete("/{run_id}", summary="Delete one run")
def delete_run(run_id: int):
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"run {run_id} not found")
        session.delete(run)
        session.commit()
        return {"deleted": run_id}
