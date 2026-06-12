"""Semantic memory: learnings (lessons from real performance) and
channel_history (published topics, powering 30-day dedup).
"""
from uuid import UUID

import numpy as np

from ..core.config import settings
from ..core.embeddings import embed_query
from ..db.pool import get_pool


async def store_learning(run_id: str | None, learning: str, kind: str = "analytics") -> None:
    vector = np.array(await embed_query(learning))
    pool = get_pool()
    await pool.execute(
        "INSERT INTO learnings (run_id, learning, kind, embedding) VALUES ($1, $2, $3, $4)",
        UUID(run_id) if run_id else None, learning, kind, vector,
    )


async def recall_learnings(query: str, k: int = 3) -> list[str]:
    pool = get_pool()
    if await pool.fetchval("SELECT count(*) FROM learnings") == 0:
        return []
    vector = np.array(await embed_query(query))
    rows = await pool.fetch(
        "SELECT learning FROM learnings ORDER BY embedding <=> $1 LIMIT $2",
        vector, k,
    )
    return [r["learning"] for r in rows]


async def is_topic_recent(topic: str) -> bool:
    """True if the topic is semantically close to something covered recently."""
    pool = get_pool()
    vector = np.array(await embed_query(topic))
    row = await pool.fetchrow(
        """
        SELECT 1 FROM channel_history
        WHERE embedding <=> $1 < $2
          AND published_at > now() - make_interval(days => $3)
        LIMIT 1
        """,
        vector, settings.topic_dedup_distance, settings.topic_dedup_days,
    )
    return row is not None


async def record_published(topic: str, title: str, youtube_id: str | None, publish_mode: str) -> None:
    """Record even dry-run topics so dedup works before going live."""
    vector = np.array(await embed_query(topic))
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO channel_history (topic, title, youtube_id, publish_mode, embedding)
        VALUES ($1, $2, $3, $4, $5)
        """,
        topic, title, youtube_id, publish_mode, vector,
    )
