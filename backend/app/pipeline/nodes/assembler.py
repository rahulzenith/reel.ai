"""Node 6: render the final 9:16 video. Joins the voice + broll branches.
The render blocks for its full duration, so it runs in a worker thread.
"""
import asyncio
from pathlib import Path

from ...core.config import settings
from ...core.paths import run_dir
from ...memory.episodic import update_run
from ...tools.video.assembler import assemble
from ...ws import events
from .base import pipeline_node


@pipeline_node("assembler")
async def assembler(state: dict) -> dict:
    out_path = run_dir(state["run_id"]) / "short.mp4"

    await events.emit(events.node_status(
        "assembler", "running", "Rendering video (this takes a minute)..."
    ))
    # Anton has no Devanagari glyphs — Hindi captions need the Mukta font
    font = settings.caption_font_hindi if state.get("language") == "hi" else settings.caption_font

    result = await asyncio.to_thread(
        assemble,
        [Path(p) for p in state["broll_paths"]],
        Path(state["voiceover_path"]),
        state["script"]["full_text"],
        out_path,
        font,
        settings.broll_scene_seconds,
    )

    await update_run(state["run_id"], video_path=str(out_path))
    return {
        "video_path": str(out_path),
        "logs": [f"assembler: rendered {result['duration']:.1f}s video, "
                 f"{result['caption_count']} caption segments"],
    }
