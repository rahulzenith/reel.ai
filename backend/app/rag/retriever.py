"""Hybrid retrieval over viral_patterns: pgvector cosine + Postgres full-text
search, fused with Reciprocal Rank Fusion in a single SQL query.
"""
import numpy as np

from ..core.embeddings import embed_query
from ..db.pool import get_pool
from ..domain.models import RetrievedDoc

RRF_K = 60

HYBRID_SQL = """
WITH dense AS (
    SELECT id, row_number() OVER (ORDER BY embedding <=> $1) AS rnk
    FROM viral_patterns
    ORDER BY embedding <=> $1
    LIMIT 20
),
lexical AS (
    SELECT id, row_number() OVER (
        ORDER BY ts_rank_cd(tsv, plainto_tsquery('english', $2)) DESC
    ) AS rnk
    FROM viral_patterns
    WHERE tsv @@ plainto_tsquery('english', $2)
    LIMIT 20
)
SELECT vp.hook_text, vp.category, vp.why_it_works,
       COALESCE(1.0 / ($4 + d.rnk), 0) + COALESCE(1.0 / ($4 + l.rnk), 0) AS rrf_score
FROM viral_patterns vp
LEFT JOIN dense d ON d.id = vp.id
LEFT JOIN lexical l ON l.id = vp.id
WHERE d.id IS NOT NULL OR l.id IS NOT NULL
ORDER BY rrf_score DESC
LIMIT $3
"""


async def hybrid_search(query: str, k: int = 5) -> list[RetrievedDoc]:
    vector = np.array(await embed_query(query))
    pool = get_pool()
    rows = await pool.fetch(HYBRID_SQL, vector, query, k, RRF_K)
    return [
        RetrievedDoc(
            hook_text=r["hook_text"],
            category=r["category"] or "",
            why_it_works=r["why_it_works"] or "",
            score=float(r["rrf_score"]),
        )
        for r in rows
    ]


def format_patterns(docs: list[RetrievedDoc]) -> str:
    if not docs:
        return "No patterns available yet."
    return "\n".join(
        f"- [{d.category}] \"{d.hook_text}\" — {d.why_it_works}" for d in docs
    )
