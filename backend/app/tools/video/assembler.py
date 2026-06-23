"""Final video assembly: background b-roll + voiceover + burned captions → short.mp4.

Pure sync function — the assembler node calls it via asyncio.to_thread because
write_videofile blocks for the whole render.
"""
from pathlib import Path

from moviepy import AudioFileClip, CompositeVideoClip

from .captions import build_caption_clips
from .compositing import (
    DEFAULT_SCENE_SECONDS,
    KEN_BURNS_MAX_ZOOM,
    TARGET_H,
    TARGET_W,
    build_background,
)


def _scene_cuts(
    boundaries: list[tuple[float, float]], duration: float, target: float
) -> list[float]:
    """Pick a subset of caption word-end times ~target seconds apart, so each
    b-roll scene change lands on a caption beat instead of a blind timer."""
    cuts: list[float] = []
    last = 0.0
    for _, end in boundaries:
        if end - last >= target and duration - end > target * 0.5:
            cuts.append(end)
            last = end
    return cuts


def assemble(
    broll_paths: list[Path],
    audio_path: Path,
    script_text: str,
    out_path: Path,
    font_path: Path,
    scene_seconds: float = DEFAULT_SCENE_SECONDS,
    caption_style: str = "highlight",
    max_zoom: float = KEN_BURNS_MAX_ZOOM,
    word_timings: list[dict] | None = None,
) -> dict:
    audio = AudioFileClip(str(audio_path))
    duration = audio.duration

    captions, boundaries = build_caption_clips(
        script_text, duration, font_path, style=caption_style, word_timings=word_timings
    )
    scene_cuts = _scene_cuts(boundaries, duration, scene_seconds)
    background = build_background(
        broll_paths, duration, scene_seconds, scene_boundaries=scene_cuts, max_zoom=max_zoom
    )

    final = (
        CompositeVideoClip([background, *captions], size=(TARGET_W, TARGET_H))
        .with_duration(duration)
        .with_audio(audio)
    )
    final.write_videofile(
        str(out_path),
        fps=30,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        logger=None,
    )
    final.close()
    audio.close()

    return {"duration": duration, "caption_count": len(captions), "video_path": str(out_path)}
