"""Node 5 (parallel with voice_generator): an LLM creative director plans one
scene per ~5s of speech, then one clip is fetched per scene. The assembler cuts
them into 5s segments in this order, so visuals track the narration.

Falls back to the script's own keywords if the planning call fails.
"""
import math

from pydantic import BaseModel, Field

from ...core.config import settings
from ...core.llm import get_chat_model
from ...core.paths import broll_dir
from ...prompts.broll_planner import HUMAN_TEMPLATE, SYSTEM
from ...tools.broll.service import fetch_broll
from ...ws import events
from .base import pipeline_node


class BrollPlan(BaseModel):
    queries: list[str] = Field(
        description="Stock footage search queries, one per scene, in narrative order"
    )


def scene_count() -> int:
    return math.ceil(settings.target_duration_seconds / settings.broll_scene_seconds)


@pipeline_node("broll_selector")
async def broll_selector(state: dict) -> dict:
    script = state["script"]
    n_scenes = scene_count()

    try:
        planner = get_chat_model(temperature=0.6, max_tokens=600).with_structured_output(BrollPlan)
        plan: BrollPlan = await planner.ainvoke([
            ("system", SYSTEM.format(n_scenes=n_scenes)),
            ("human", HUMAN_TEMPLATE.format(
                duration=settings.target_duration_seconds,
                full_text=script["full_text"],
                n_scenes=n_scenes,
            )),
        ])
        queries = [q.strip() for q in plan.queries if q.strip()][:n_scenes]
        plan_source = "llm-scenes"
    except Exception:
        queries = []
        plan_source = "script-keywords"

    if not queries:
        queries = script.get("keywords") or state["topic"].split()[:3]

    await events.emit(events.node_status(
        "broll_selector", "running",
        f"Scene plan ({plan_source}, {len(queries)} scenes): {' | '.join(queries)}",
    ))

    clips, source = await fetch_broll(queries, len(queries), broll_dir(state["run_id"]))

    await events.emit(events.node_status(
        "broll_selector", "running", f"{len(clips)} clips ready ({source})"
    ))
    return {
        "broll_paths": [str(p) for p in clips],
        "broll_source": source,
        "logs": [f"broll_selector: {len(clips)} {source} clips for {len(queries)} scenes"],
    }
