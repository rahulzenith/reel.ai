"""Node 5 (parallel with voice_generator): fetch B-roll using the script's
visual keywords. No extra LLM call — keywords come from the Script output.
"""
from ...core.paths import broll_dir
from ...tools.broll.service import fetch_broll
from ...ws import events
from .base import pipeline_node

CLIP_COUNT = 4


@pipeline_node("broll_selector")
async def broll_selector(state: dict) -> dict:
    keywords = state["script"].get("keywords") or state["topic"].split()[:3]
    clips, source = await fetch_broll(keywords, CLIP_COUNT, broll_dir(state["run_id"]))

    await events.emit(events.node_status(
        "broll_selector", "running",
        f"{len(clips)} clips ready ({source}) for keywords: {', '.join(keywords[:4])}",
    ))
    return {
        "broll_paths": [str(p) for p in clips],
        "broll_source": source,
        "logs": [f"broll_selector: {len(clips)} {source} clips"],
    }
