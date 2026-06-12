"""Caption generation: chunk the script into 3-4 word segments and time them
proportionally across the audio duration. MoviePy 2.x TextClip API.
"""
from pathlib import Path

from moviepy import TextClip

WIDTH = 1080
CHUNK_SIZE = 4


def chunk_words(text: str, size: int = CHUNK_SIZE) -> list[str]:
    words = text.split()
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size)]


def build_caption_clips(text: str, duration: float, font_path: Path) -> list[TextClip]:
    chunks = chunk_words(text)
    if not chunks:
        return []

    total_words = len(text.split())
    clips: list[TextClip] = []
    cursor = 0.0
    for chunk in chunks:
        chunk_duration = duration * (len(chunk.split()) / total_words)
        clip = (
            TextClip(
                font=str(font_path),
                text=chunk.upper(),
                font_size=72,
                color="white",
                stroke_color="black",
                stroke_width=4,
                method="caption",
                size=(WIDTH - 160, None),
                text_align="center",
            )
            .with_start(cursor)
            .with_duration(chunk_duration)
            .with_position(("center", 0.68), relative=True)
        )
        clips.append(clip)
        cursor += chunk_duration
    return clips
