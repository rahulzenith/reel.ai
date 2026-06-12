"""Node 3: LLM-as-judge quality gate. Routing happens in routing.py based on
eval_result["passed"] and retry_count.
"""
from ...domain.models import Script
from ...evals.hook_scorer import score
from ...memory.episodic import update_run
from ...ws import events
from .base import pipeline_node


@pipeline_node("evaluator")
async def evaluator(state: dict) -> dict:
    script = Script.model_validate(state["script"])
    result, passed = await score(script)
    retry_count = state.get("retry_count", 0) + 1

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
