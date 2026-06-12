"""Seed the viral_patterns table from seed/seed_hooks.json. Idempotent.

Usage (from backend/): python -m app.rag.ingest
"""
import asyncio
import json
from pathlib import Path

import numpy as np

from ..core.embeddings import embed_documents
from ..core.logging import get_logger, setup_logging
from ..db.pool import close_pool, init_pool

log = get_logger(__name__)

SEED_FILE = Path(__file__).parent / "seed" / "seed_hooks.json"


async def ingest_seed_hooks() -> int:
    hooks = json.loads(SEED_FILE.read_text())
    pool = await init_pool()

    # Skip hooks already present so re-runs don't re-embed everything
    existing = {
        r["hook_text"]
        for r in await pool.fetch("SELECT hook_text FROM viral_patterns")
    }
    new_hooks = [h for h in hooks if h["hook_text"] not in existing]
    if not new_hooks:
        log.info("All %d seed hooks already ingested", len(hooks))
        return 0

    log.info("Embedding %d new hooks via Azure...", len(new_hooks))
    vectors = await embed_documents([h["hook_text"] for h in new_hooks])

    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO viral_patterns (hook_text, category, why_it_works, embedding)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (hook_text) DO NOTHING
            """,
            [
                (h["hook_text"], h["category"], h["why_it_works"], np.array(v))
                for h, v in zip(new_hooks, vectors)
            ],
        )
    log.info("Ingested %d hooks", len(new_hooks))
    return len(new_hooks)


if __name__ == "__main__":
    setup_logging()

    async def main():
        try:
            await ingest_seed_hooks()
        finally:
            await close_pool()

    asyncio.run(main())
