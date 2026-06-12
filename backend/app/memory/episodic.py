"""Episodic memory: the runs table — what happened, run by run."""
from typing import Any
from uuid import UUID

from ..db.pool import get_pool

# Whitelist guards the dynamic SET clause in update_run
UPDATABLE = {
    "finished_at", "status", "topic", "topic_source", "script",
    "hook_score", "retention_score", "clarity_score", "eval_feedback",
    "retry_count", "video_path", "youtube_id", "youtube_url",
    "publish_mode", "ctr_48h", "avg_view_pct", "error", "meta",
}


async def create_run(trigger: str) -> str:
    pool = get_pool()
    row = await pool.fetchrow(
        "INSERT INTO runs (trigger) VALUES ($1) RETURNING id", trigger
    )
    return str(row["id"])


async def update_run(run_id: str, **fields: Any) -> None:
    bad = set(fields) - UPDATABLE
    if bad:
        raise ValueError(f"Non-updatable run fields: {bad}")
    if not fields:
        return
    cols = list(fields)
    set_clause = ", ".join(f"{c} = ${i + 2}" for i, c in enumerate(cols))
    pool = get_pool()
    await pool.execute(
        f"UPDATE runs SET {set_clause} WHERE id = $1",
        UUID(run_id), *[fields[c] for c in cols],
    )


async def finish_run(run_id: str, status: str, error: str | None = None) -> None:
    pool = get_pool()
    await pool.execute(
        "UPDATE runs SET status = $2, error = $3, finished_at = now() WHERE id = $1",
        UUID(run_id), status, error,
    )


async def recent_runs(limit: int = 20) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT id, started_at, finished_at, status, trigger, topic, topic_source,
               hook_score, retention_score, clarity_score, retry_count,
               video_path, youtube_url, publish_mode, error
        FROM runs ORDER BY started_at DESC LIMIT $1
        """,
        limit,
    )
    return [dict(r) | {"id": str(r["id"])} for r in rows]


async def get_run(run_id: str) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow("SELECT * FROM runs WHERE id = $1", UUID(run_id))
    if row is None:
        return None
    d = dict(row)
    d["id"] = str(d["id"])
    d.pop("embedding", None)
    return d
