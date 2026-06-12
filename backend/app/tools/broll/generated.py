"""Fallback B-roll: generated 9:16 gradient clips.

Used when Pexels is unavailable so the assembler always has visual input.
"""
import colorsys
from pathlib import Path

import numpy as np
from moviepy import ImageClip

WIDTH, HEIGHT = 1080, 1920
CLIP_SECONDS = 6

HUES = [0.58, 0.75, 0.92, 0.08, 0.33]  # blue, purple, pink, orange, green


def _gradient_frame(hue: float) -> np.ndarray:
    top = np.array(colorsys.hsv_to_rgb(hue, 0.75, 0.55)) * 255
    bottom = np.array(colorsys.hsv_to_rgb((hue + 0.08) % 1.0, 0.85, 0.20)) * 255
    t = np.linspace(0, 1, HEIGHT)[:, None, None]
    frame = top[None, None, :] * (1 - t) + bottom[None, None, :] * t
    return np.broadcast_to(frame, (HEIGHT, WIDTH, 3)).astype(np.uint8)


def generate_fallback_clips(n: int, out_dir: Path) -> list[Path]:
    clips: list[Path] = []
    for i in range(n):
        clip = ImageClip(_gradient_frame(HUES[i % len(HUES)])).with_duration(CLIP_SECONDS)
        path = out_dir / f"generated_{i}.mp4"
        clip.write_videofile(str(path), fps=24, codec="libx264", audio=False, logger=None)
        clips.append(path)
    return clips
