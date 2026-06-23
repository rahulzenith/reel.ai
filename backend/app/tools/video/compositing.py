"""B-roll compositing: cut clips into short scene segments (a fresh visual every
few seconds), apply a slow Ken Burns zoom to each so nothing sits static,
crossfade between them, and cover the audio duration. MoviePy 2.x API.

Scene cuts can be aligned to caption phrase boundaries (passed in by the
assembler) so the visual changes land on the spoken beat instead of a blind
timer.
"""
from pathlib import Path

from moviepy import (
    ColorClip,
    CompositeVideoClip,
    VideoClip,
    VideoFileClip,
    concatenate_videoclips,
    vfx,
)

TARGET_W, TARGET_H = 1080, 1920
CROSSFADE = 0.25
DEFAULT_SCENE_SECONDS = 3.0
KEN_BURNS_MAX_ZOOM = 1.12


def _fit_to_vertical(clip: VideoFileClip) -> VideoClip:
    """Scale so the frame fully covers 1080x1920, then center-crop the excess."""
    scale = max(TARGET_W / clip.w, TARGET_H / clip.h)
    clip = clip.resized(scale)
    return clip.cropped(
        x_center=clip.w / 2, y_center=clip.h / 2, width=TARGET_W, height=TARGET_H
    )


def _ken_burns(clip: VideoClip, zoom_in: bool, max_zoom: float = KEN_BURNS_MAX_ZOOM) -> VideoClip:
    """Slow continuous zoom over the clip's duration. The zoom factor stays >= 1.0
    the whole time so the frame always covers 1080x1920 (no black edges); we
    can't time-vary a crop in MoviePy, so the over-scaled clip is centered on a
    fixed-size composite canvas which does the clipping."""
    dur = clip.duration
    if not dur or dur <= 0:
        return clip
    span = max_zoom - 1.0
    if zoom_in:
        zoom = lambda t: 1.0 + span * (t / dur)
    else:
        zoom = lambda t: max_zoom - span * (t / dur)
    zoomed = clip.resized(zoom).with_position(("center", "center"))
    return CompositeVideoClip([zoomed], size=(TARGET_W, TARGET_H)).with_duration(dur)


def _scene_marks(
    duration: float, scene_seconds: float, scene_boundaries: list[float] | None
) -> list[float]:
    """The cut points (in seconds) bounding each scene. With boundaries supplied,
    use those that fall inside the clip; otherwise a fixed grid."""
    if scene_boundaries:
        inner = sorted(b for b in scene_boundaries if 0.0 < b < duration)
        marks = [0.0, *inner, duration]
    else:
        n = int(duration // scene_seconds)
        marks = [min(k * scene_seconds, duration) for k in range(n + 1)] + [duration]
    return sorted(set(marks))


def build_background(
    broll_paths: list[Path],
    duration: float,
    scene_seconds: float = DEFAULT_SCENE_SECONDS,
    scene_boundaries: list[float] | None = None,
    max_zoom: float = KEN_BURNS_MAX_ZOOM,
) -> VideoClip:
    """One Ken Burns segment per scene, in plan order, looping through the clips
    if there are fewer than scenes. Scenes are bounded by ``scene_boundaries``
    when given (caption beats), else by a fixed ``scene_seconds`` grid."""
    sources: list[VideoClip] = []
    for path in broll_paths:
        try:
            sources.append(VideoFileClip(str(path)).without_audio())
        except Exception:
            continue

    if not sources:
        return ColorClip(size=(TARGET_W, TARGET_H), color=(12, 12, 24), duration=duration)

    marks = _scene_marks(duration, scene_seconds, scene_boundaries)
    segments: list[VideoClip] = []
    i = 0
    for a, b in zip(marks, marks[1:]):
        take = b - a
        if take <= 0.1:
            continue
        clip = sources[i % len(sources)]
        take = min(take, max(clip.duration, 0.5))
        segment = _fit_to_vertical(clip.subclipped(0, min(take, clip.duration)))
        segment = _ken_burns(segment, zoom_in=(len(segments) % 2 == 0), max_zoom=max_zoom)
        if segments:  # crossfade into every segment after the first
            segment = segment.with_effects([vfx.CrossFadeIn(CROSSFADE)])
        segments.append(segment)
        i += 1
        if i > 400:  # safety valve
            break

    if not segments:  # degenerate (e.g. near-zero duration) — flat fill, never crash
        return ColorClip(size=(TARGET_W, TARGET_H), color=(12, 12, 24), duration=duration)

    background = concatenate_videoclips(segments, method="compose", padding=-CROSSFADE)
    return background.with_duration(min(background.duration, duration))
