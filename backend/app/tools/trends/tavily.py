"""Primary trend source: Tavily search (requires TAVILY_API_KEY)."""
from ...core.config import settings
from ...domain.models import TrendCandidate

QUERIES = [
    "trending {niche} topics this week",
    "viral {niche} news today",
]


async def get_topic_context(topic: str, max_chars: int = 1500) -> str:
    """Fresh facts about the chosen topic, for grounding the script writer.
    LLM training data is months stale; this is what keeps scripts factual."""
    from tavily import AsyncTavilyClient

    client = AsyncTavilyClient(api_key=settings.tavily_api_key)
    results = await client.search(query=topic, max_results=3, search_depth="advanced")

    chunks = []
    for r in results.get("results", []):
        content = r.get("content", "").strip()
        if content:
            chunks.append(f"[{r.get('title', 'source')}] {content}")
    return "\n".join(chunks)[:max_chars]


async def get_tavily_candidates(n: int = 8) -> list[TrendCandidate]:
    # Guarded import: tavily-python may be absent; service falls through on any error
    from tavily import AsyncTavilyClient

    client = AsyncTavilyClient(api_key=settings.tavily_api_key)
    candidates: list[TrendCandidate] = []
    seen: set[str] = set()

    for template in QUERIES:
        query = template.format(niche=settings.niche)
        results = await client.search(query=query, max_results=n // 2 + 1, search_depth="basic")
        for r in results.get("results", []):
            title = r.get("title", "").strip()
            if len(title) < 10 or title in seen:
                continue
            seen.add(title)
            candidates.append(
                TrendCandidate(
                    title=title,
                    url=r.get("url", ""),
                    snippet=r.get("content", "")[:300],
                    source="tavily",
                    score=float(r.get("score", 0.5)),
                )
            )

    if not candidates:
        raise RuntimeError("Tavily returned no usable results")
    return candidates[:n]
