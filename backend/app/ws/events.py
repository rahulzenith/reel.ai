"""Typed WS event builders + a single emit() that broadcasts and updates the
status registry in one call. Every pipeline broadcast goes through here.
"""
from typing import Any

from .manager import manager
from .registry import registry


async def emit(event: dict[str, Any]) -> None:
    registry.apply(event)
    await manager.broadcast(event)


def node_status(node: str, status: str, log: str | None = None) -> dict:
    return {"type": "node_status", "node": node, "status": status, "log": log}


def topic_selected(topic: str, source: str) -> dict:
    return {"type": "topic_selected", "topic": topic, "source": source,
            "log": f"Topic selected ({source}): {topic}"}


def script_preview(script: dict) -> dict:
    return {"type": "script_preview", "script": script,
            "log": f"Script ready — hook: \"{script.get('hook', '')[:80]}\""}


def eval_scores(scores: dict, passed: bool, retry_count: int, feedback: str) -> dict:
    return {
        "type": "eval_scores", "scores": scores, "passed": passed,
        "retry_count": retry_count, "feedback": feedback,
        "log": (
            f"Eval — hook {scores['hook_score']:.2f} | retention {scores['retention_score']:.2f} "
            f"| clarity {scores['clarity_score']:.2f} → {'PASS' if passed else 'RETRY'}"
        ),
    }


def run_started(run_id: str, trigger: str) -> dict:
    return {"type": "run_started", "run_id": run_id, "trigger": trigger,
            "log": f"Run started ({trigger})"}


def run_complete(run_id: str, video_path: str | None, youtube_url: str | None, dry_run: bool) -> dict:
    suffix = youtube_url if youtube_url else f"{video_path} (dry run — not uploaded)"
    return {"type": "run_complete", "run_id": run_id, "video_path": video_path,
            "youtube_url": youtube_url, "dry_run": dry_run,
            "log": f"Run complete: {suffix}"}


def run_error(run_id: str, error: str) -> dict:
    return {"type": "run_error", "run_id": run_id, "error": error,
            "log": f"Run failed: {error}"}
