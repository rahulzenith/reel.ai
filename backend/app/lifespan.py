import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .core.config import settings
from .core.logging import get_logger, setup_logging
from .db.pool import close_pool, init_pool
from .scheduler.scheduler import start_scheduler, stop_scheduler

log = get_logger(__name__)


def _configure_langsmith() -> None:
    # langchain reads these from os.environ; pydantic-settings only read .env
    if settings.langsmith_api_key and settings.langsmith_tracing:
        os.environ.setdefault("LANGSMITH_TRACING", "true")
        os.environ.setdefault("LANGSMITH_API_KEY", settings.langsmith_api_key)
        os.environ.setdefault("LANGSMITH_PROJECT", settings.langsmith_project)
        os.environ.setdefault("LANGSMITH_ENDPOINT", settings.langsmith_endpoint)
        log.info("LangSmith tracing enabled (project: %s)", settings.langsmith_project)
    else:
        os.environ.setdefault("LANGSMITH_TRACING", "false")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    _configure_langsmith()
    pool = await init_pool()
    # Runs can only execute inside this process — anything still marked
    # 'running' at startup was orphaned by a previous shutdown
    orphaned = await pool.execute(
        "UPDATE runs SET status='failed', error='orphaned by server restart', "
        "finished_at=now() WHERE status='running'"
    )
    if orphaned != "UPDATE 0":
        log.warning("Marked orphaned runs as failed (%s)", orphaned)
    settings.outputs_path.mkdir(parents=True, exist_ok=True)
    start_scheduler()
    log.info("Shorts Factory backend ready (PUBLISH_MODE=%s)", settings.publish_mode)
    yield
    stop_scheduler()
    await close_pool()
