import asyncio

from fastapi import APIRouter, HTTPException

from ...memory.episodic import get_run, recent_runs
from ...pipeline.runner import is_running, run_pipeline

router = APIRouter()


@router.post("/run")
async def trigger_run():
    if is_running():
        raise HTTPException(status_code=409, detail="A pipeline run is already in progress")
    asyncio.create_task(run_pipeline(trigger="manual"))
    return {"status": "started"}


@router.get("/history")
async def history(limit: int = 20):
    return await recent_runs(min(limit, 100))


@router.get("/runs/{run_id}")
async def run_detail(run_id: str):
    run = await get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
