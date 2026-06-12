"""TTS facade: Cartesia → ElevenLabs → silent track. Returns (path, source)."""
import asyncio
from pathlib import Path

from ...core.config import settings
from ...core.logging import get_logger
from .silent import silent_synthesize

log = get_logger(__name__)


async def synthesize(text: str, out_path: Path, language: str = "en") -> tuple[Path, str]:
    if settings.has_cartesia:
        try:
            from .cartesia import cartesia_synthesize

            await cartesia_synthesize(text, out_path, language)
            return out_path, "cartesia"
        except Exception as e:
            log.warning("Cartesia failed (%s) — trying ElevenLabs", e)

    if settings.elevenlabs_api_key:
        try:
            from .elevenlabs import elevenlabs_synthesize

            await elevenlabs_synthesize(text, out_path)
            return out_path, "elevenlabs"
        except Exception as e:
            log.warning("ElevenLabs failed (%s) — writing silent fallback track", e)

    await asyncio.to_thread(silent_synthesize, text, out_path)
    return out_path, "silent"
