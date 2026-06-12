"""Node 7: publish (dry-run or live), record the topic for dedup, finalize run."""
from pathlib import Path

from ...core.config import settings
from ...memory.episodic import update_run
from ...memory.semantic import record_published
from ...tools.publish.service import publish
from ...ws import events
from .base import pipeline_node


@pipeline_node("publisher")
async def publisher(state: dict) -> dict:
    script = state["script"]
    title = script["title"][:100]
    description = script["full_text"] + "\n\n#Shorts"
    tags = ["shorts", "ai", *script.get("keywords", [])][:10]

    result = await publish(Path(state["video_path"]), title, description, tags)

    # Record even dry runs so topic dedup works before going live
    await record_published(state["topic"], title, result.youtube_id, settings.publish_mode)
    await update_run(
        state["run_id"],
        youtube_id=result.youtube_id,
        youtube_url=result.url,
        publish_mode="live" if not result.dry_run else "dry_run",
    )

    return {"publish_result": result.model_dump(),
            "logs": [f"publisher: {'uploaded ' + str(result.url) if not result.dry_run else 'dry run — metadata saved'}"]}
