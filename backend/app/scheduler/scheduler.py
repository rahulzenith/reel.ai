"""Daily cron: runs the pipeline in-process at SCHEDULE_HOUR:SCHEDULE_MINUTE."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..core.config import settings
from ..core.logging import get_logger
from ..pipeline.runner import run_pipeline

log = get_logger(__name__)

scheduler = AsyncIOScheduler()


async def _daily_job() -> None:
    log.info("Scheduler firing daily pipeline run")
    await run_pipeline(trigger="cron")


def start_scheduler() -> None:
    if not settings.scheduler_enabled:
        log.info("Scheduler disabled (SCHEDULER_ENABLED=false)")
        return
    scheduler.add_job(
        _daily_job,
        CronTrigger(hour=settings.schedule_hour, minute=settings.schedule_minute,
                    timezone=settings.tz),
        id="daily_shorts_run",
        replace_existing=True,
    )
    scheduler.start()
    log.info("Scheduler started — daily run at %02d:%02d %s",
             settings.schedule_hour, settings.schedule_minute, settings.tz)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


def next_run_time() -> str | None:
    if not scheduler.running:
        return None
    job = scheduler.get_job("daily_shorts_run")
    return job.next_run_time.isoformat() if job and job.next_run_time else None
