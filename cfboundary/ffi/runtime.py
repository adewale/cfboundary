"""Runtime detection helpers for Cloudflare Python Workers."""
import time
from .safe_env import HAS_PYODIDE

_STARTED_AT = time.monotonic()

def is_workers_runtime() -> bool:
    return HAS_PYODIDE

def is_cold_start(window_s: float = 5.0) -> bool:
    return (time.monotonic() - _STARTED_AT) <= window_s

async def await_js(promise: object) -> object:
    return await promise  # type: ignore[misc]
