"""Pitch-preserving audio speed-up via ffmpeg atempo — the hard ceiling that
guarantees the video never exceeds MAX_VIDEO_SECONDS regardless of how slowly
the TTS voice happened to speak.
"""
import subprocess
from pathlib import Path

import imageio_ffmpeg


def compress_to_fit(audio_path: Path, duration: float, max_seconds: float) -> tuple[Path, float]:
    """If audio exceeds max_seconds, re-encode it sped up just enough to fit.
    Returns (path, new_duration)."""
    if duration <= max_seconds:
        return audio_path, duration

    factor = duration / max_seconds
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    out_path = audio_path.with_name(audio_path.stem + "_fit.mp3")

    subprocess.run(
        [ffmpeg, "-y", "-i", str(audio_path),
         "-filter:a", f"atempo={factor:.4f}", "-b:a", "128k", str(out_path)],
        check=True, capture_output=True,
    )
    return out_path, duration / factor
