from pathlib import Path

from .config import settings


def run_dir(run_id: str) -> Path:
    d = settings.outputs_path / run_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def broll_dir(run_id: str) -> Path:
    d = run_dir(run_id) / "broll"
    d.mkdir(parents=True, exist_ok=True)
    return d
