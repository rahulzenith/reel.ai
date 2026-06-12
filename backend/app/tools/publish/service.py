"""Publish facade: dry_run unless PUBLISH_MODE=live AND OAuth creds exist."""
import asyncio
from pathlib import Path

from ...core.config import settings
from ...core.logging import get_logger
from ...domain.models import PublishResult
from .dry_run import dry_run_publish

log = get_logger(__name__)


async def publish(video_path: Path, title: str, description: str, tags: list[str]) -> PublishResult:
    if settings.publish_mode == "live" and settings.has_youtube_creds:
        try:
            from .youtube import youtube_upload

            # Blocking OAuth + resumable upload — keep it off the event loop
            return await asyncio.to_thread(youtube_upload, video_path, title, description, tags)
        except Exception as e:
            log.error("YouTube upload failed (%s) — falling back to dry-run metadata", e)
    elif settings.publish_mode == "live":
        log.warning("PUBLISH_MODE=live but %s missing — dry-run instead",
                    settings.youtube_client_secret_file)

    return dry_run_publish(video_path, title, description, tags)
