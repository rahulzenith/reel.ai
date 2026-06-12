"""Node 1: find candidate topics, skip recently-covered ones, LLM-pick the best."""
from pydantic import BaseModel, Field

from ...core.config import settings
from ...core.llm import get_chat_model
from ...memory.episodic import update_run
from ...memory.semantic import is_topic_recent
from ...prompts.trend_ranker import HUMAN_TEMPLATE, SYSTEM
from ...tools.trends.service import fetch_topic_context, search_trends
from ...ws import events
from .base import pipeline_node


class TopicPick(BaseModel):
    title: str = Field(description="The chosen candidate's title, verbatim")
    refined_topic: str = Field(
        description="The winner rewritten as a specific, curiosity-driven video topic"
    )
    reason: str = Field(description="One sentence on why it wins")


class DerivedTopic(BaseModel):
    topic: str = Field(description="The single best 45-second video angle, as one line")


async def _derive_topic_from_content(content: str) -> str:
    deriver = get_chat_model(temperature=0.4, max_tokens=150).with_structured_output(DerivedTopic)
    result: DerivedTopic = await deriver.ainvoke([
        ("system", "Given source material, state the single best topic/angle for a "
                   "45-second YouTube Short based on it. One line, specific, curiosity-driven."),
        ("human", content[:4000]),
    ])
    return result.topic.strip()


@pipeline_node("trend_scout")
async def trend_scout(state: dict) -> dict:
    # ── Manual mode: the user's brief is the whole story — no search, no
    # dedup, no ranking, no Tavily. Auto flow below is untouched. ──
    if state.get("user_topic") or state.get("user_content"):
        content = state.get("user_content", "")
        topic = state.get("user_topic", "")
        if not topic:
            topic = await _derive_topic_from_content(content)
        await events.emit(events.topic_selected(topic, "user"))
        await update_run(state["run_id"], topic=topic, topic_source="user")
        return {"topic": topic, "topic_source": "user", "topic_context": content,
                "logs": [f"trend_scout: user-provided brief — \"{topic}\""]}

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
    topic = pick.refined_topic.strip() or chosen.title
    await events.emit(events.topic_selected(topic, chosen.source))

    # Fresh facts so the script writer isn't limited by its training cutoff.
    # Search with the refined topic; the raw title's snippet is the fallback.
    context = await fetch_topic_context(topic, fallback_snippet=chosen.snippet)
    if context:
        await events.emit(events.node_status(
            "trend_scout", "running", f"Fetched {len(context)} chars of fresh topic context"
        ))

    await update_run(state["run_id"], topic=topic, topic_source=chosen.source,
                     meta={"raw_candidate": chosen.title})
    return {"topic": topic, "topic_source": chosen.source,
            "topic_context": context,
            "logs": [f"trend_scout: picked \"{chosen.title}\" → \"{topic}\" ({pick.reason})"]}
