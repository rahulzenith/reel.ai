"""Node decorator: broadcasts running/done/error around each node and captures
exceptions. Fatal nodes re-raise (the run cannot continue without them);
non-fatal nodes degrade by returning an errors entry.
"""
import functools
from typing import Any, Awaitable, Callable

from ...core.logging import get_logger
from ...ws import events

log = get_logger(__name__)

NodeFn = Callable[[dict], Awaitable[dict]]


def pipeline_node(name: str, fatal: bool = True) -> Callable[[NodeFn], NodeFn]:
    def decorator(fn: NodeFn) -> NodeFn:
        @functools.wraps(fn)
        async def wrapper(state: dict) -> dict[str, Any]:
            await events.emit(events.node_status(name, "running", f"{name}: started"))
            try:
                result = await fn(state)
            except Exception as e:
                log.exception("Node %s failed", name)
                await events.emit(events.node_status(name, "error", f"{name}: {e}"))
                if fatal:
                    raise
                return {"errors": [f"{name}: {e}"]}
            await events.emit(events.node_status(name, "done"))
            return result

        return wrapper

    return decorator
