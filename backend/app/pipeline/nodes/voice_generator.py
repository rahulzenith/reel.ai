"""Node 4 (parallel with broll_selector): synthesize the voiceover and measure
its duration — caption timing and b-roll length both key off it.
"""
import asyncio

from moviepy import AudioFileClip

from ...core.paths import run_dir
from ...tools.tts.service import synthesize
from ...ws import events
from .base import pipeline_node


def _measure(path: str) -> float:
    clip = AudioFileClip(path)
    duration = clip.duration
    clip.close()
    return duration


@pipeline_node("voice_generator")
async def voice_generator(state: dict) -> dict:
    out_path = run_dir(state["run_id"]) / "voiceover.mp3"
    path, source = await synthesize(state["script"]["full_text"], out_path)
    duration = await asyncio.to_thread(_measure, str(path))

    await events.emit(events.node_status(
        "voice_generator", "running",
        f"Voiceover ready ({source}, {duration:.1f}s)",
    ))
    return {
        "voiceover_path": str(path),
        "audio_duration": duration,
        "voice_source": source,
        "logs": [f"voice_generator: {source} audio, {duration:.1f}s"],
    }
