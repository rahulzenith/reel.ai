"""Node 1: find candidate topics, skip recently-covered ones, LLM-pick the best."""
from pydantic import BaseModel, Field

from ...core.config import settings
from ...core.llm import get_chat_model
from ...memory.episodic import update_run
from ...memory.semantic import is_topic_recent
from ...prompts.trend_ranker import HUMAN_TEMPLATE, SYSTEM
from ...tools.trends.service import search_trends
from ...ws import events
from .base import pipeline_node


class TopicPick(BaseModel):
    title: str = Field(description="The chosen candidate's title, verbatim")
    reason: str = Field(description="One sentence on why it wins")


@pipeline_node("trend_scout")
async def trend_scout(state: dict) -> dict:
    candidates = await search_trends(n=8)

    fresh = []
    for c in candidates:
        if await is_topic_recent(c.title):
            await events.emit(events.node_status(
                "trend_scout", "running", f"Skipping (covered recently): {c.title[:60]}"
            ))
            continue
        fresh.append(c)
    if not fresh:
        fresh = candidates  # everything is recent — better to repeat than to stall

    ranker = get_chat_model(temperature=0.2, max_tokens=300).with_structured_output(TopicPick)
    listing = "\n".join(f"- {c.title} ({c.source}) {c.snippet[:120]}" for c in fresh)
    pick: TopicPick = await ranker.ainvoke([
        ("system", SYSTEM.format(niche=settings.niche)),
        ("human", HUMAN_TEMPLATE.format(candidates=listing)),
    ])

    chosen = next((c for c in fresh if c.title == pick.title), fresh[0])
    await events.emit(events.topic_selected(chosen.title, chosen.source))
    await update_run(state["run_id"], topic=chosen.title, topic_source=chosen.source)

    return {"topic": chosen.title, "topic_source": chosen.source,
            "logs": [f"trend_scout: {pick.reason}"]}
