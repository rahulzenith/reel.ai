import operator
from typing import Annotated, TypedDict


class PipelineState(TypedDict, total=False):
    run_id: str
    trigger: str

    # trend_scout
    topic: str
    topic_source: str

    # script_writer / evaluator
    script: dict           # Script.model_dump()
    eval_result: dict      # EvalResult.model_dump() + "passed"
    eval_feedback: str
    retry_count: int

    # voice_generator ┐ parallel branches — disjoint keys, so no
    voiceover_path: str  # conflict; only logs/errors need reducers
    audio_duration: float
    voice_source: str

    # broll_selector ┘
    broll_paths: list[str]
    broll_source: str

    # assembler
    video_path: str

    # publisher
    publish_result: dict

    # reducer-merged: both parallel branches may append concurrently
    logs: Annotated[list[str], operator.add]
    errors: Annotated[list[str], operator.add]
