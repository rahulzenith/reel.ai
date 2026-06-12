"""Procedural memory: the style_profile table — the channel's standing rules."""
import json
from typing import Any

from ..db.pool import get_pool


async def get_style_profile() -> dict[str, Any]:
    pool = get_pool()
    rows = await pool.fetch("SELECT key, value FROM style_profile")
    return {r["key"]: r["value"] for r in rows}


async def update_style_profile(key: str, value: Any) -> None:
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO style_profile (key, value, updated_at) VALUES ($1, $2, now())
        ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = now()
        """,
        key, json.dumps(value),
    )


def format_style(profile: dict[str, Any]) -> str:
    if not profile:
        return "No specific style constraints."
    lines = []
    for key, value in profile.items():
        rendered = ", ".join(value) if isinstance(value, list) else str(value)
        lines.append(f"- {key}: {rendered}")
    return "\n".join(lines)
