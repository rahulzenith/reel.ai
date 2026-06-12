"""B-roll facade: Pexels → generated gradient clips. Always returns ≥1 clip."""
import asyncio
from pathlib import Path

from ...core.config import settings
from ...core.logging import get_logger
from .generated import generate_fallback_clips

log = get_logger(__name__)


async def fetch_broll(keywords: list[str], n: int, out_dir: Path) -> tuple[list[Path], str]:
    """Returns (clip_paths, source) where source is 'pexels' or 'generated'."""
    out_dir.mkdir(parents=True, exist_ok=True)

    if settings.has_pexels:
        try:
            from .pexels import fetch_pexels_clips

            clips = await fetch_pexels_clips(keywords, n, out_dir)
            return clips, "pexels"
        except Exception as e:
            log.warning("Pexels failed (%s) — generating fallback clips", e)

    clips = await asyncio.to_thread(generate_fallback_clips, n, out_dir)
    return clips, "generated"
