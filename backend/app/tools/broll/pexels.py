"""Real B-roll source: Pexels portrait video search (requires PEXELS_API_KEY)."""
from pathlib import Path

import httpx

from ...core.config import settings

SEARCH_URL = "https://api.pexels.com/videos/search"


async def fetch_pexels_clips(keywords: list[str], n: int, out_dir: Path) -> list[Path]:
    query = " ".join(keywords[:3])
    headers = {"Authorization": settings.pexels_api_key}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            SEARCH_URL,
            headers=headers,
            params={"query": query, "per_page": n + 2, "orientation": "portrait", "size": "medium"},
        )
        resp.raise_for_status()
        videos = resp.json().get("videos", [])

        clips: list[Path] = []
        for i, video in enumerate(videos):
            if len(clips) >= n:
                break
            # Smallest portrait file that's still HD-ish keeps downloads fast
            files = sorted(
                (f for f in video.get("video_files", []) if f.get("width")),
                key=lambda f: f["width"],
            )
            chosen = next((f for f in files if 540 <= f["width"] <= 1080), files[-1] if files else None)
            if not chosen:
                continue

            clip_path = out_dir / f"clip_{i}.mp4"
            async with client.stream("GET", chosen["link"], follow_redirects=True) as dl:
                dl.raise_for_status()
                with open(clip_path, "wb") as fh:
                    async for chunk in dl.aiter_bytes():
                        fh.write(chunk)
            clips.append(clip_path)

    if not clips:
        raise RuntimeError(f"Pexels returned no usable portrait clips for '{query}'")
    return clips
