from fastapi import APIRouter

from ...core.config import settings
from ...scheduler.scheduler import next_run_time
from ...ws.registry import registry

router = APIRouter()


@router.get("/status")
async def status():
    return registry.snapshot() | {
        "publish_mode": settings.publish_mode,
        "next_scheduled_run": next_run_time(),
    }


@router.get("/health")
async def health():
    return {"status": "ok"}
