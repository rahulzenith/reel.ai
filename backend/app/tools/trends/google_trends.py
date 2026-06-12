"""Keyless trend source: Google Trends daily RSS feed."""
import asyncio

import feedparser
import httpx

from ...domain.models import TrendCandidate

RSS_URL = "https://trends.google.com/trending/rss?geo=US"


async def get_rss_candidates(n: int = 8) -> list[TrendCandidate]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(RSS_URL, follow_redirects=True)
        resp.raise_for_status()

    feed = await asyncio.to_thread(feedparser.parse, resp.text)
    candidates = []
    for entry in feed.entries[:n]:
        title = getattr(entry, "title", "").strip()
        if len(title) < 4:
            continue
        candidates.append(
            TrendCandidate(
                title=title,
                url=getattr(entry, "link", ""),
                snippet=getattr(entry, "summary", "")[:300],
                source="google-trends",
                score=0.6,
            )
        )
    if not candidates:
        raise RuntimeError("Google Trends RSS returned no entries")
    return candidates
