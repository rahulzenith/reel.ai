"""Dry-run publisher: writes the would-be upload metadata next to the video."""
import json
from datetime import datetime, timezone
from pathlib import Path

from ...domain.models import PublishResult


def dry_run_publish(video_path: Path, title: str, description: str, tags: list[str]) -> PublishResult:
    metadata = {
        "mode": "dry_run",
        "title": title,
        "description": description,
        "tags": tags,
        "video_path": str(video_path),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "note": "Set PUBLISH_MODE=live and add Google OAuth credentials to upload for real.",
    }
    meta_path = video_path.parent / "publish_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))
    return PublishResult(youtube_id=None, url=None, dry_run=True, metadata=metadata)
