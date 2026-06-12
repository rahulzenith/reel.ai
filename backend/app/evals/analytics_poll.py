"""YouTube Analytics poller: ~48h after a live publish, fetch real CTR and
average-view-percentage, write them onto the run row, and distill a learning.

Dormant while PUBLISH_MODE=dry_run (nothing is published, nothing to measure).
Wire `poll_analytics` into the scheduler as a daily job when going live.
"""
from ..core.config import settings
from ..core.logging import get_logger
from ..db.pool import get_pool
from ..memory.semantic import store_learning

log = get_logger(__name__)


async def poll_analytics() -> int:
    if settings.publish_mode != "live":
        log.info("Analytics poll skipped — PUBLISH_MODE=%s", settings.publish_mode)
        return 0

    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT id, topic, youtube_id, hook_score, script
        FROM runs
        WHERE youtube_id IS NOT NULL
          AND ctr_48h IS NULL
          AND finished_at < now() - interval '48 hours'
        """
    )
    if not rows:
        return 0

    # TODO(live): call YouTube Analytics API (yt-analytics.readonly scope) for
    # impressions CTR + averageViewPercentage per video, then:
    #   await update_run(run_id, ctr_48h=..., avg_view_pct=...)
    #   await store_learning(run_id, distilled_insight, kind="analytics")
    log.warning(
        "Analytics poll found %d videos awaiting metrics — implement the "
        "YouTube Analytics API call before relying on the learning loop.",
        len(rows),
    )
    return len(rows)
