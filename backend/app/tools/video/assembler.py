"""Final video assembly: background b-roll + voiceover + burned captions → short.mp4.

Pure sync function — the assembler node calls it via asyncio.to_thread because
write_videofile blocks for the whole render.
"""
from pathlib import Path

from moviepy import AudioFileClip, CompositeVideoClip

from .captions import build_caption_clips
from .compositing import TARGET_H, TARGET_W, build_background


def assemble(
    broll_paths: list[Path],
    audio_path: Path,
    script_text: str,
    out_path: Path,
    font_path: Path,
    scene_seconds: float = 5.0,
) -> dict:
    audio = AudioFileClip(str(audio_path))
    duration = audio.duration

    background = build_background(broll_paths, duration, scene_seconds)
    captions = build_caption_clips(script_text, duration, font_path)

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
