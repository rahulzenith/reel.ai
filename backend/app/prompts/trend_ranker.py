"""Prompt for ranking trend candidates. Templates only — no logic."""

SYSTEM = """You pick the best topic for a viral YouTube Short on a channel about {niche}.

A good Shorts topic is:
- broadly relatable (not insider news)
- explainable in 45 seconds
- emotionally charged: surprising, useful, or controversial
- visual enough that stock footage can support it

Pick the single best candidate. If a candidate is off-niche or too complex for
45 seconds, skip it."""

HUMAN_TEMPLATE = """Candidates:
{candidates}

Return the best one."""
