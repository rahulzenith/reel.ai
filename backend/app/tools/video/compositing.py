"""B-roll compositing: crop/resize clips to 9:16 and concatenate to cover the
audio duration. MoviePy 2.x API.
"""
from pathlib import Path

from moviepy import ColorClip, VideoClip, VideoFileClip, concatenate_videoclips

TARGET_W, TARGET_H = 1080, 1920


def _fit_to_vertical(clip: VideoFileClip) -> VideoClip:
    """Scale so the frame fully covers 1080x1920, then center-crop the excess."""
    scale = max(TARGET_W / clip.w, TARGET_H / clip.h)
    clip = clip.resized(scale)
    return clip.cropped(
        x_center=clip.w / 2, y_center=clip.h / 2, width=TARGET_W, height=TARGET_H
    )


def build_background(broll_paths: list[Path], duration: float) -> VideoClip:
    segments: list[VideoClip] = []
    covered = 0.0

    # Loop over the clips repeatedly until the audio duration is covered
    i = 0
    while covered < duration and broll_paths:
        path = broll_paths[i % len(broll_paths)]
        i += 1
        if i > len(broll_paths) * 10:  # safety valve against zero-length clips
            break
        try:
            clip = VideoFileClip(str(path)).without_audio()
            clip = _fit_to_vertical(clip)
            take = min(clip.duration, duration - covered)
            if take <= 0.1:
                clip.close()
                continue
            segments.append(clip.subclipped(0, take))
            covered += take
        except Exception:
            continue

    if not segments:
        return ColorClip(size=(TARGET_W, TARGET_H), color=(12, 12, 24), duration=duration)

    background = concatenate_videoclips(segments, method="compose")
    return background.with_duration(min(background.duration, duration))
