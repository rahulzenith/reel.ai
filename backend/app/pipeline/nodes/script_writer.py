"""Node 2: write the script using RAG patterns + learnings + style profile.
On retry, the evaluator's feedback is injected into the prompt.
"""
from ...core.config import settings
from ...core.llm import get_chat_model
from ...domain.models import Script
from ...memory.episodic import update_run
from ...memory.procedural import format_style, get_style_profile
from ...memory.semantic import recall_learnings
from ...prompts.script_writer import HUMAN_TEMPLATE, RETRY_ADDENDUM, SYSTEM_TEMPLATE
from ...rag.retriever import format_patterns, hybrid_search
from ...ws import events
from .base import pipeline_node

WORD_TARGET = 130


@pipeline_node("script_writer")
async def script_writer(state: dict) -> dict:
    topic = state["topic"]

    patterns = await hybrid_search(topic, k=5)
    learnings = await recall_learnings(topic, k=3)
    style = await get_style_profile()

    system = SYSTEM_TEMPLATE.format(
        niche=settings.niche,
        style=format_style(style),
        patterns=format_patterns(patterns),
        learnings="\n".join(f"- {l}" for l in learnings) or "- (no performance data yet)",
        word_target=WORD_TARGET,
        duration=settings.target_duration_seconds,
    )
    human = HUMAN_TEMPLATE.format(topic=topic)
    if state.get("retry_count", 0) > 0 and state.get("eval_feedback"):
        human += RETRY_ADDENDUM.format(
            feedback=state["eval_feedback"],
            rejected_hook=state.get("script", {}).get("hook", ""),
        )

    writer = get_chat_model(temperature=0.85, max_tokens=1200).with_structured_output(Script)
    script: Script = await writer.ainvoke([("system", system), ("human", human)])

    script_dict = script.model_dump()
    await events.emit(events.script_preview(script_dict))
    await update_run(state["run_id"], script=script_dict)

    return {"script": script_dict}
