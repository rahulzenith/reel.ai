import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...memory.episodic import get_run, recent_runs
from ...pipeline.runner import is_running, run_pipeline

router = APIRouter()

MAX_CONTENT_CHARS = 4000


class RunRequest(BaseModel):
    topic: str | None = None
    content: str | None = None  # pasted source material


@router.post("/run")
async def trigger_run(req: RunRequest | None = None):
    if is_running():
        raise HTTPException(status_code=409, detail="A pipeline run is already in progress")

    topic = (req.topic or "").strip() if req else ""
    content = (req.content or "").strip()[:MAX_CONTENT_CHARS] if req else ""

    asyncio.create_task(run_pipeline(
        trigger="manual",
        user_topic=topic or None,
        user_content=content or None,
    ))
    return {"status": "started", "mode": "manual-topic" if (topic or content) else "auto"}


@router.get("/history")
async def history(limit: int = 20):
    return await recent_runs(min(limit, 100))


@router.get("/runs/{run_id}")
async def run_detail(run_id: str):
    run = await get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
