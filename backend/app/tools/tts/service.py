"""TTS facade: ElevenLabs → silent track. Returns (path, source)."""
import asyncio
from pathlib import Path

from ...core.logging import get_logger
from .elevenlabs import elevenlabs_synthesize
from .silent import silent_synthesize

log = get_logger(__name__)


async def synthesize(text: str, out_path: Path) -> tuple[Path, str]:
    try:
        await elevenlabs_synthesize(text, out_path)
        return out_path, "elevenlabs"
    except Exception as e:
        log.warning("ElevenLabs failed (%s) — writing silent fallback track", e)

    await asyncio.to_thread(silent_synthesize, text, out_path)
    return out_path, "silent"
