"""Primary TTS: Cartesia SSE API. Streams audio + word-level timestamps so
captions can be synced to the actual speech (the /tts/bytes endpoint returns
audio only — no timing — which is why proportional captions drift).

Returns (path, word_timings) where word_timings is
[{"word": str, "start": float, "end": float}, ...] in seconds, or [] if the
provider didn't return any.
"""
import asyncio
import base64
import json
import subprocess
from pathlib import Path

import httpx
import imageio_ffmpeg

from ...core.config import settings

API_URL = "https://api.cartesia.ai/tts/sse"
CARTESIA_VERSION = "2024-11-13"
# the SSE endpoint only supports a raw container, so we stream PCM and encode
SAMPLE_RATE = 44100


def _encode_mp3(pcm: bytes, out_path: Path) -> None:
    """Encode raw signed-16-bit little-endian mono PCM to mp3 via ffmpeg."""
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [ffmpeg, "-y", "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1",
         "-i", "pipe:0", "-b:a", "128k", str(out_path)],
        input=pcm, check=True, capture_output=True,
    )


async def cartesia_synthesize(
    text: str, out_path: Path, language: str = "en"
) -> tuple[Path, list[dict]]:
    # sonic-3 is multilingual — the main voice speaks Hindi too; a dedicated
    # Hindi voice is an optional override
    voice_id = settings.cartesia_voice_id
    if language == "hi" and settings.cartesia_voice_id_hi:
        voice_id = settings.cartesia_voice_id_hi

    payload = {
        "model_id": settings.cartesia_model_id,
        "transcript": text,
        "voice": {"mode": "id", "id": voice_id},
        "language": language,
        "output_format": {"container": "raw", "encoding": "pcm_s16le", "sample_rate": SAMPLE_RATE},
        "add_timestamps": True,
    }
    headers = {
        "X-API-Key": settings.cartesia_api_key,
        "Cartesia-Version": CARTESIA_VERSION,
        "Content-Type": "application/json",
    }

    audio = bytearray()
    words: list[str] = []
    starts: list[float] = []
    ends: list[float] = []

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", API_URL, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                event = json.loads(line[len("data:"):].strip())
                etype = event.get("type")
                if etype == "chunk" and event.get("data"):
                    audio.extend(base64.b64decode(event["data"]))
                elif etype == "timestamps":
                    wt = event.get("word_timestamps") or {}
                    words.extend(wt.get("words", []))
                    starts.extend(wt.get("start", []))
                    ends.extend(wt.get("end", []))
                elif etype == "error":
                    raise RuntimeError(f"Cartesia SSE error: {event.get('error')}")

    if not audio:
        raise RuntimeError("Cartesia returned empty audio")
    await asyncio.to_thread(_encode_mp3, bytes(audio), out_path)
    if out_path.stat().st_size == 0:
        raise RuntimeError("Cartesia encode produced empty audio")

    word_timings = [
        {"word": w, "start": s, "end": e}
        for w, s, e in zip(words, starts, ends)
    ]
    return out_path, word_timings
