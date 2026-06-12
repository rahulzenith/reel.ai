"""B-roll compositing: cut clips into ~5s scene segments (guaranteeing a visual
change every few seconds), crossfade between them, cover the audio duration.
MoviePy 2.x API.
"""
from pathlib import Path

from moviepy import ColorClip, VideoClip, VideoFileClip, concatenate_videoclips, vfx

TARGET_W, TARGET_H = 1080, 1920
CROSSFADE = 0.25


def _fit_to_vertical(clip: VideoFileClip) -> VideoClip:
    """Scale so the frame fully covers 1080x1920, then center-crop the excess."""
    scale = max(TARGET_W / clip.w, TARGET_H / clip.h)
    clip = clip.resized(scale)
    return clip.cropped(
        x_center=clip.w / 2, y_center=clip.h / 2, width=TARGET_W, height=TARGET_H
    )


def build_background(broll_paths: list[Path], duration: float, scene_seconds: float = 5.0) -> VideoClip:
    """One ~scene_seconds segment per clip, in plan order, looping through the
    clips if there are fewer than needed — a fresh visual every <=scene_seconds."""
    sources: list[VideoClip] = []
    for path in broll_paths:
        try:
            sources.append(VideoFileClip(str(path)).without_audio())
        except Exception:
            continue

    if not sources:
        return ColorClip(size=(TARGET_W, TARGET_H), color=(12, 12, 24), duration=duration)

    segments: list[VideoClip] = []
    covered = 0.0
    i = 0
    while covered < duration:
        clip = sources[i % len(sources)]
        take = min(scene_seconds, max(clip.duration, 0.5), duration - covered)
        if take <= 0.1:
            break
        segment = _fit_to_vertical(clip.subclipped(0, min(take, clip.duration)))
        if segments:  # crossfade into every segment after the first
            segment = segment.with_effects([vfx.CrossFadeIn(CROSSFADE)])
        segments.append(segment)
        covered += take - (CROSSFADE if len(segments) > 1 else 0)
        i += 1
        if i > 200:  # safety valve
            break

    background = concatenate_videoclips(segments, method="compose", padding=-CROSSFADE)
    return background.with_duration(min(background.duration, duration))
