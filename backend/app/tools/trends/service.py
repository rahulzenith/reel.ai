"""Trend source facade: Tavily → Google Trends RSS → curated list.

Never raises — always returns at least the curated candidates.
"""
from ...core.config import settings
from ...core.logging import get_logger
from ...domain.models import TrendCandidate
from .curated import get_curated_candidates
from .google_trends import get_rss_candidates

log = get_logger(__name__)


async def search_trends(n: int = 8) -> list[TrendCandidate]:
    if settings.has_tavily:
        try:
            from .tavily import get_tavily_candidates

            return await get_tavily_candidates(n)
        except Exception as e:
            log.warning("Tavily failed (%s) — falling back to Google Trends RSS", e)

    try:
        return await get_rss_candidates(n)
    except Exception as e:
        log.warning("Google Trends RSS failed (%s) — using curated topics", e)

    return get_curated_candidates(n)
