"""Run SQL migrations in order, substituting {EMBEDDING_DIM} from settings.

Usage (from backend/): python -m app.db.migrate
"""
import asyncio
from pathlib import Path

from ..core.config import settings
from ..core.logging import get_logger, setup_logging
from .pool import close_pool, init_pool

log = get_logger(__name__)

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def run_migrations() -> None:
    pool = await init_pool()
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        sql = path.read_text().replace("{EMBEDDING_DIM}", str(settings.embedding_dim))
        log.info("Applying %s (vector dim %d)", path.name, settings.embedding_dim)
        async with pool.acquire() as conn:
            await conn.execute(sql)
    log.info("Migrations complete")


if __name__ == "__main__":
    setup_logging()

    async def main():
        try:
            await run_migrations()
        finally:
            await close_pool()

    asyncio.run(main())
