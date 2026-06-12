"""Node 3: LLM-as-judge quality gate. Routing happens in routing.py based on
eval_result["passed"] and retry_count.
"""
from ...domain.models import Script
from ...evals.hook_scorer import score
from ...memory.episodic import update_run
from ...ws import events
from .base import pipeline_node
from .script_writer import word_range


@pipeline_node("evaluator")
async def evaluator(state: dict) -> dict:
    script = Script.model_validate(state["script"])
    result, passed = await score(script)
    retry_count = state.get("retry_count", 0) + 1

    # Deterministic length gate — the LLM judge can't count words reliably
    word_min, word_max = word_range()
    words = len(script.full_text.split())
    if words < word_min:
        passed = False
        result.feedback = (
            f"Script is only {words} words — it must be {word_min}-{word_max} words "
            f"to fill the video. Expand the body with one more concrete example "
            f"or detail. Also: {result.feedback}"
        )
    elif words > word_max:
        passed = False
        result.feedback = (
            f"Script is {words} words — over the {word_max}-word ceiling, the video "
            f"would exceed its time slot. Cut filler and weaker points; keep the "
            f"strongest example. Also: {result.feedback}"
        )

    scores = {
        "hook_score": result.hook_score,
        "retention_score": result.retention_score,
        "clarity_score": result.clarity_score,
    }
    await events.emit(events.eval_scores(scores, passed, retry_count, result.feedback))
    await update_run(
        state["run_id"],
        hook_score=result.hook_score,
        retention_score=result.retention_score,
        clarity_score=result.clarity_score,
        eval_feedback=result.feedback,
        retry_count=retry_count,
    )

    return {
        "eval_result": result.model_dump() | {"passed": passed},
        "eval_feedback": result.feedback,
        "retry_count": retry_count,
    }
