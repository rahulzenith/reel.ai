"""Real B-roll source: Pexels portrait video search (requires PEXELS_API_KEY)."""
from pathlib import Path

import httpx

from ...core.config import settings

SEARCH_URL = "https://api.pexels.com/videos/search"


async def fetch_pexels_clips(keywords: list[str], n: int, out_dir: Path) -> list[Path]:
    """One search PER keyword (short queries match far better on Pexels than a
    single mashed query), 1-2 clips each, deduped across searches."""
    headers = {"Authorization": settings.pexels_api_key}
    per_keyword = max(1, -(-n // max(len(keywords), 1)))  # ceil division

    clips: list[Path] = []
    seen_ids: set[int] = set()

    async with httpx.AsyncClient(timeout=30) as client:
        for keyword in keywords:
            if len(clips) >= n:
                break
            try:
                resp = await client.get(
                    SEARCH_URL,
                    headers=headers,
                    params={"query": keyword, "per_page": 4,
                            "orientation": "portrait", "size": "medium"},
                )
                resp.raise_for_status()
                videos = resp.json().get("videos", [])
            except Exception:
                continue  # one bad keyword shouldn't sink the rest

            taken = 0
            for video in videos:
                if taken >= per_keyword or len(clips) >= n:
                    break
                if video.get("id") in seen_ids:
                    continue
                files = sorted(
                    (f for f in video.get("video_files", []) if f.get("width")),
                    key=lambda f: f["width"],
                )
                chosen = next((f for f in files if 540 <= f["width"] <= 1080),
                              files[-1] if files else None)
                if not chosen:
                    continue

                clip_path = out_dir / f"clip_{len(clips)}.mp4"
                try:
                    async with client.stream("GET", chosen["link"], follow_redirects=True) as dl:
                        dl.raise_for_status()
                        with open(clip_path, "wb") as fh:
                            async for chunk in dl.aiter_bytes():
                                fh.write(chunk)
                except Exception:
                    continue
                seen_ids.add(video.get("id"))
                clips.append(clip_path)
                taken += 1

    if not clips:
        raise RuntimeError(f"Pexels returned no usable portrait clips for {keywords}")
    return clips
