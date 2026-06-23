"""Dev-only offline preview for the video assembler.

Synthesizes inputs (solid-color b-roll clips + a silent audio track) so the
caption / Ken Burns / beat-cut changes can be eyeballed with NO API keys, DB, or
real assets. Renders one short per caption style.

Run from backend/ with the venv:
    .venv/bin/python -m scripts.preview_assembler
    .venv/bin/python -m scripts.preview_assembler --style pop --duration 12

Outputs land in backend/outputs/preview/.
"""
import argparse
from pathlib import Path

import numpy as np
from moviepy import AudioArrayClip, ColorClip

from app.core.config import settings
from app.tools.video.assembler import assemble

OUT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "preview"
WORK = OUT_DIR / "_work"

# distinct colors so scene cuts are obvious; clip count < scenes to prove looping
COLORS = [(28, 30, 64), (96, 24, 48), (24, 72, 64), (72, 56, 16), (40, 40, 40)]

SCRIPT = (
    "You have been lied to about productivity your entire life. "
    "Most apps just add more noise to your day. "
    "But here is the part nobody mentions: focus is a subtraction game. "
    "Cut three things today and watch what happens. "
    "Which one are you cutting first?"
)


def _make_broll(clip_seconds: float) -> list[Path]:
    WORK.mkdir(parents=True, exist_ok=True)
    paths = []
    for idx, color in enumerate(COLORS):
        p = WORK / f"broll_{idx}.mp4"
        clip = ColorClip(size=(720, 1280), color=color, duration=clip_seconds)
        clip.write_videofile(str(p), fps=30, codec="libx264", logger=None)
        clip.close()
        paths.append(p)
    return paths


def _make_audio(duration: float) -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    p = WORK / "voice.wav"  # wav preserves duration; mp3 encoders drop pure silence
    fps = 44100
    n = int(duration * fps)
    # a faint 220Hz tone — non-silent so the duration survives encoding
    samples = 0.01 * np.sin(2 * np.pi * 220 * np.arange(n) / fps)
    arr = np.column_stack([samples, samples])  # stereo
    audio = AudioArrayClip(arr, fps=fps)
    audio.write_audiofile(str(p), logger=None)
    audio.close()
    return p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default=settings.caption_style,
                    choices=["highlight", "pop", "block"])
    ap.add_argument("--duration", type=float, default=14.0)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    broll = _make_broll(clip_seconds=4.0)
    audio = _make_audio(args.duration)
    out = OUT_DIR / f"preview_{args.style}.mp4"

    result = assemble(
        broll_paths=broll,
        audio_path=audio,
        script_text=SCRIPT,
        out_path=out,
        font_path=settings.caption_font,
        scene_seconds=settings.broll_scene_seconds,
        caption_style=args.style,
        max_zoom=settings.ken_burns_max_zoom,
    )
    print(f"\n✓ rendered {result['video_path']}")
    print(f"  duration={result['duration']:.1f}s  captions={result['caption_count']}  style={args.style}")


if __name__ == "__main__":
    main()
