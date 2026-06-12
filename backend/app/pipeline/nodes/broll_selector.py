"""Node 5 (parallel with voice_generator): LLM plans 4-5 B-roll scenes in
narrative order, then one clip is fetched per scene. The assembler concatenates
clips in this order, so visuals roughly track the narration.

Falls back to the script's own keywords if the planning call fails.
"""
from pydantic import BaseModel, Field

from ...core.config import settings
from ...core.llm import get_chat_model
from ...core.paths import broll_dir
from ...prompts.broll_planner import HUMAN_TEMPLATE, SYSTEM
from ...tools.broll.service import fetch_broll
from ...ws import events
from .base import pipeline_node

MAX_SCENES = 5


class BrollPlan(BaseModel):
    queries: list[str] = Field(
        description="4-5 stock footage search queries, one per scene, in narrative order"
    )


@pipeline_node("broll_selector")
async def broll_selector(state: dict) -> dict:
    script = state["script"]

    try:
        planner = get_chat_model(temperature=0.4, max_tokens=300).with_structured_output(BrollPlan)
        plan: BrollPlan = await planner.ainvoke([
            ("system", SYSTEM),
            ("human", HUMAN_TEMPLATE.format(
                duration=settings.target_duration_seconds,
                full_text=script["full_text"],
            )),
        ])
        queries = [q.strip() for q in plan.queries if q.strip()][:MAX_SCENES]
        plan_source = "llm-scenes"
    except Exception:
        queries = []
        plan_source = "script-keywords"

    if not queries:
        queries = script.get("keywords") or state["topic"].split()[:3]

    await events.emit(events.node_status(
        "broll_selector", "running", f"Scene plan ({plan_source}): {' | '.join(queries)}"
    ))

    clips, source = await fetch_broll(queries, len(queries), broll_dir(state["run_id"]))

    await events.emit(events.node_status(
        "broll_selector", "running", f"{len(clips)} clips ready ({source})"
    ))
    return {
        "broll_paths": [str(p) for p in clips],
        "broll_source": source,
        "logs": [f"broll_selector: {len(clips)} {source} clips for scenes: {', '.join(queries)}"],
    }
