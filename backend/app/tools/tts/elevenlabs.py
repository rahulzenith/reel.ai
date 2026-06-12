"""Real TTS: ElevenLabs async client."""
from pathlib import Path

from elevenlabs.client import AsyncElevenLabs

from ...core.config import settings


async def elevenlabs_synthesize(text: str, out_path: Path) -> Path:
    client = AsyncElevenLabs(api_key=settings.elevenlabs_api_key)
    stream = client.text_to_speech.convert(
        voice_id=settings.elevenlabs_voice_id,
        text=text,
        model_id=settings.elevenlabs_model_id,
        output_format="mp3_44100_128",
    )
    with open(out_path, "wb") as fh:
        async for chunk in stream:
            if chunk:
                fh.write(chunk)

    if out_path.stat().st_size == 0:
        raise RuntimeError("ElevenLabs returned empty audio")
    return out_path
