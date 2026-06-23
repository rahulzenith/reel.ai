"""Caption generation: word-by-word "karaoke" captions, timed across the audio.

Two styles:
  - "highlight": a short rolling window of words; the currently-spoken word is
    accented (bright color) while neighbours stay white. The dominant viral look.
  - "pop": one large word centered at a time, punching in with a scale + fade.
  - "block" (legacy): the original static 3-4 word chunks, kept as a fallback.

Timing is proportional (each word gets an equal slice of the duration) unless a
caller supplies real per-word timings via ``word_timings`` — the builder then
syncs to those timestamps. No timing data exists in the pipeline today, so the
proportional path is what runs; the hook is here so true word-sync can drop in
later with no rewrite.

MoviePy 2.x TextClip API. Per-word layout needs method="label" (so .w/.h are
populated at construction and we can measure word widths); method="caption"
wraps to a fixed box and can't be measured.
"""
from pathlib import Path

from moviepy import TextClip, vfx

WIDTH = 1080
HEIGHT = 1920
CHUNK_SIZE = 4  # legacy "block" style

# highlight style
HIGHLIGHT_WINDOW = 3          # words visible on screen at once
HIGHLIGHT_FONT_SIZE = 80
HIGHLIGHT_GAP = 8            # px between word boxes (boxes already carry margin)
ACCENT_COLOR = "#FFE34D"      # active word colour
CAPTION_Y = 0.68             # relative vertical position of the caption line
# generous box padding so Devanagari conjuncts / matras and the stroke outline
# are never clipped by MoviePy's tight label box (Latin just gets padding)
LABEL_MARGIN = (24, 24)

# pop style
POP_FONT_SIZE = 130
POP_RISE = 0.18              # seconds the scale-in takes

MAX_LINE_WIDTH = WIDTH - 80   # shrink-to-fit threshold
MIN_SLICE = 0.05             # floor on a single word's on-screen time


def chunk_words(text: str, size: int = CHUNK_SIZE) -> list[str]:
    words = text.split()
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size)]


def _word_schedule(
    text: str, duration: float, word_timings: list[dict] | None
) -> list[tuple[str, float, float]]:
    """(word, start, end) per word. When real per-word timings are supplied they
    are the source of truth (their own word list + times), and each word is held
    until the next one starts so a <break> pause keeps the caption on screen
    instead of flashing blank. Otherwise words are spaced evenly over duration."""
    if word_timings:
        raw = [
            (t["word"], float(t.get("start", 0.0)), float(t.get("end", 0.0)))
            for t in word_timings
            if t.get("word")
        ]
        if raw:
            sched: list[tuple[str, float, float]] = []
            for i, (w, start, end) in enumerate(raw):
                nxt = raw[i + 1][1] if i + 1 < len(raw) else duration
                sched.append((w, start, max(end, nxt)))  # fill the pause to next word
            return sched

    words = text.split()
    n = max(len(words), 1)
    step = duration / n
    return [(w, i * step, (i + 1) * step) for i, w in enumerate(words)]


def _label(text: str, font_path: Path, font_size: int, accent: bool) -> TextClip:
    """A single measurable word clip (method="label" => .w populated now)."""
    return TextClip(
        font=str(font_path),
        text=text,
        font_size=font_size,
        color=ACCENT_COLOR if accent else "white",
        stroke_color="black",
        stroke_width=5,
        method="label",
        margin=LABEL_MARGIN,
    )


def _layout_line(
    words: list[str], font_path: Path, font_size: int, accent_idx: int | None
) -> tuple[list[tuple[TextClip, int]], int]:
    """Lay words left-to-right as one centered line. Returns [(clip, x_px), ...]
    plus the (possibly shrunk) font size. Recurses smaller if the line overflows."""
    clips = [
        _label(w.upper(), font_path, font_size, accent=(i == accent_idx))
        for i, w in enumerate(words)
    ]
    total = sum(c.w for c in clips) + HIGHLIGHT_GAP * (len(clips) - 1)
    if total > MAX_LINE_WIDTH and font_size > 24:
        shrink = max(0.5, MAX_LINE_WIDTH / total)
        return _layout_line(words, font_path, int(font_size * shrink), accent_idx)

    placed: list[tuple[TextClip, int]] = []
    x = (WIDTH - total) / 2
    for c in clips:
        placed.append((c, int(x)))
        x += c.w + HIGHLIGHT_GAP
    return placed, font_size


def _highlight_clips(
    schedule: list[tuple[str, float, float]], font_path: Path
) -> list[TextClip]:
    """Rolling 3-word window; the spoken word is accented and nudged slightly up.
    Each window is re-laid for every word so the accent moves through the line."""
    words = [w for w, _, _ in schedule]
    y_px = int(CAPTION_Y * HEIGHT)
    clips: list[TextClip] = []
    half = HIGHLIGHT_WINDOW // 2
    for i, (_, start, end) in enumerate(schedule):
        lo = max(0, min(i - half, len(words) - HIGHLIGHT_WINDOW))
        lo = max(lo, 0)
        window = words[lo : lo + HIGHLIGHT_WINDOW]
        active = i - lo
        placed, _ = _layout_line(window, font_path, HIGHLIGHT_FONT_SIZE, active)
        dur = max(end - start, MIN_SLICE)
        for c, x in placed:
            clips.append(
                c.with_start(start).with_duration(dur).with_position((x, y_px))
            )
    return clips


def _pop_clips(
    schedule: list[tuple[str, float, float]], font_path: Path
) -> list[TextClip]:
    """One big centered word per slice, scaling + fading in."""
    clips: list[TextClip] = []
    for word, start, end in schedule:
        dur = max(end - start, MIN_SLICE)
        font_size = POP_FONT_SIZE
        # shrink very long words so they fit the frame width
        probe = _label(word.upper(), font_path, font_size, accent=False)
        if probe.w > MAX_LINE_WIDTH:
            font_size = max(40, int(font_size * MAX_LINE_WIDTH / probe.w))
        clip = TextClip(
            font=str(font_path),
            text=word.upper(),
            font_size=font_size,
            color="white",
            stroke_color="black",
            stroke_width=6,
            method="label",
            margin=LABEL_MARGIN,
        ).with_start(start).with_duration(dur)
        rise = min(POP_RISE, dur)
        clip = (
            clip.resized(lambda t, rise=rise: 0.72 + 0.28 * min(t / rise, 1.0))
            .with_effects([vfx.CrossFadeIn(min(0.12, dur / 2))])
            .with_position(("center", "center"))
        )
        clips.append(clip)
    return clips


def _block_clips(text: str, duration: float, font_path: Path) -> list[TextClip]:
    """Legacy: static 3-4 word chunks, proportionally timed."""
    chunks = chunk_words(text)
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
                margin=(8, 24),
                text_align="center",
            )
            .with_start(cursor)
            .with_duration(chunk_duration)
            .with_position(("center", CAPTION_Y), relative=True)
        )
        clips.append(clip)
        cursor += chunk_duration
    return clips


def build_caption_clips(
    text: str,
    duration: float,
    font_path: Path,
    style: str = "highlight",
    word_timings: list[dict] | None = None,
) -> tuple[list[TextClip], list[tuple[float, float]]]:
    """Build caption clips plus the (start, end) of each word — the boundaries
    let the compositor cut b-roll on caption beats.

    style: "highlight" (default) | "pop" | "block" (legacy static chunks).
    word_timings: optional [{"word","start","end"}]; when absent, even spacing.
    """
    if not text.split() and not word_timings:
        return [], []

    if style == "block":
        return _block_clips(text, duration, font_path), []

    schedule = _word_schedule(text, duration, word_timings)
    if not schedule:
        return [], []
    boundaries = [(start, end) for _, start, end in schedule]

    if style == "pop":
        clips = _pop_clips(schedule, font_path)
    else:  # "highlight" and any unknown value
        clips = _highlight_clips(schedule, font_path)
    return clips, boundaries
