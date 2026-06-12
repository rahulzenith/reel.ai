"""In-memory snapshot of the current run so GET /status can rehydrate a
dashboard that connects (or reloads) mid-run.
"""
from typing import Any

MAX_LOGS = 200


class RunStatusRegistry:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.run_id: str | None = None
        self.run_status: str = "idle"  # idle | running | completed | failed
        self.topic: str | None = None
        self.topic_source: str | None = None
        self.nodes: dict[str, str] = {}
        self.script: dict[str, Any] | None = None
        self.scores: dict[str, float] | None = None
        self.eval_feedback: str | None = None
        self.retry_count: int = 0
        self.video_path: str | None = None
        self.youtube_url: str | None = None
        self.logs: list[str] = []

    def start_run(self, run_id: str) -> None:
        self.reset()
        self.run_id = run_id
        self.run_status = "running"

    def apply(self, event: dict[str, Any]) -> None:
        """Fold a WS event into the snapshot. Mirrors what the frontend reducer does."""
        etype = event.get("type")
        if etype == "node_status":
            self.nodes[event["node"]] = event["status"]
        elif etype == "topic_selected":
            self.topic = event.get("topic")
            self.topic_source = event.get("source")
        elif etype == "script_preview":
            self.script = event.get("script")
        elif etype == "eval_scores":
            self.scores = event.get("scores")
            self.retry_count = event.get("retry_count", 0)
            self.eval_feedback = event.get("feedback")
        elif etype == "run_complete":
            self.run_status = "completed"
            self.video_path = event.get("video_path")
            self.youtube_url = event.get("youtube_url")
        elif etype == "run_error":
            self.run_status = "failed"
        if log_line := event.get("log"):
            self.logs.append(log_line)
            del self.logs[:-MAX_LOGS]

    def snapshot(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_status": self.run_status,
            "topic": self.topic,
            "topic_source": self.topic_source,
            "nodes": self.nodes,
            "script": self.script,
            "scores": self.scores,
            "eval_feedback": self.eval_feedback,
            "retry_count": self.retry_count,
            "video_path": self.video_path,
            "youtube_url": self.youtube_url,
            "logs": self.logs,
        }


registry = RunStatusRegistry()
