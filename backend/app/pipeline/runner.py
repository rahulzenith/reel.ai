"""Pipeline entrypoint shared by the API (POST /run) and the daily cron job."""
import asyncio

from ..core.logging import get_logger
from ..memory.episodic import create_run, finish_run
from ..ws import events
from ..ws.registry import registry
from .graph import graph

log = get_logger(__name__)

_run_lock = asyncio.Lock()


def is_running() -> bool:
    return _run_lock.locked()


async def run_pipeline(trigger: str = "manual") -> str | None:
    if _run_lock.locked():
        log.warning("Run requested (%s) but a pipeline is already running", trigger)
        return None

    async with _run_lock:
        run_id = await create_run(trigger)
        registry.start_run(run_id)
        await events.emit(events.run_started(run_id, trigger))

        try:
            final_state = await graph.ainvoke(
                {"run_id": run_id, "trigger": trigger, "retry_count": 0,
                 "logs": [], "errors": []},
                config={"configurable": {"thread_id": run_id}, "run_name": f"shorts-run-{run_id[:8]}"},
            )
        except Exception as e:
            log.exception("Pipeline run %s failed", run_id)
            await finish_run(run_id, "failed", str(e))
            await events.emit(events.run_error(run_id, str(e)))
            return run_id

        publish_result = final_state.get("publish_result", {})
        await finish_run(run_id, "completed")
        await events.emit(events.run_complete(
            run_id,
            final_state.get("video_path"),
            publish_result.get("url"),
            publish_result.get("dry_run", True),
        ))
        return run_id
