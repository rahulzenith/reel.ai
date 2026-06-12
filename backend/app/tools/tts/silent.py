"""Fallback TTS: a silent track sized to the script's natural speaking time.

Keeps the pipeline alive when ElevenLabs fails — captions still get timed.
"""
from pathlib import Path

import numpy as np
from moviepy import AudioArrayClip

WORDS_PER_SECOND = 2.5
SAMPLE_RATE = 44100


def silent_synthesize(text: str, out_path: Path) -> Path:
    duration = max(len(text.split()) / WORDS_PER_SECOND, 5.0)
    samples = np.zeros((int(duration * SAMPLE_RATE), 2), dtype=np.float32)
    clip = AudioArrayClip(samples, fps=SAMPLE_RATE)
    clip.write_audiofile(str(out_path), logger=None)
    return out_path
