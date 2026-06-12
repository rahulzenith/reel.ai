"""Conditional routing after the evaluator: retry the script or fan out to the
parallel voice + b-roll branches.
"""
from ..core.config import settings


def route_after_eval(state: dict) -> list[str] | str:
    passed = state.get("eval_result", {}).get("passed", False)
    if passed or state.get("retry_count", 0) >= settings.max_script_retries + 1:
        # retry_count includes the first attempt, so threshold is retries + 1
        return ["voice_generator", "broll_selector"]  # parallel fan-out
    return "script_writer"  # rewrite with evaluator feedback
