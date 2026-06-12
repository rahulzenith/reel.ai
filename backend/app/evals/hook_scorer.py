"""LLM-as-judge: scores a script against the evaluator rubric."""
from ..core.config import settings
from ..core.llm import get_chat_model
from ..domain.models import EvalResult, Script
from ..prompts.evaluator import HUMAN_TEMPLATE, SYSTEM


async def score(script: Script) -> tuple[EvalResult, bool]:
    judge = get_chat_model(temperature=0.0, max_tokens=400).with_structured_output(EvalResult)
    result: EvalResult = await judge.ainvoke([
        ("system", SYSTEM),
        ("human", HUMAN_TEMPLATE.format(hook=script.hook, body=script.body, cta=script.cta)),
    ])
    passed = result.hook_score >= settings.hook_score_threshold
    return result, passed
