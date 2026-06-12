"""Primary TTS: Cartesia REST API. Key, model, and voice ID come from config."""
from pathlib import Path

import httpx

from ...core.config import settings

API_URL = "https://api.cartesia.ai/tts/bytes"
CARTESIA_VERSION = "2024-11-13"


async def cartesia_synthesize(text: str, out_path: Path) -> Path:
    payload = {
        "model_id": settings.cartesia_model_id,
        "transcript": text,
        "voice": {"mode": "id", "id": settings.cartesia_voice_id},
        "language": "en",
        "output_format": {"container": "mp3", "bit_rate": 128000, "sample_rate": 44100},
    }
    headers = {
        "X-API-Key": settings.cartesia_api_key,
        "Cartesia-Version": CARTESIA_VERSION,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(API_URL, json=payload, headers=headers)
        resp.raise_for_status()
        out_path.write_bytes(resp.content)

    if out_path.stat().st_size == 0:
        raise RuntimeError("Cartesia returned empty audio")
    return out_path
