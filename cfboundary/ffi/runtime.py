"""Runtime detection helpers for Cloudflare Python Workers."""

import time

from .safe_env import is_pyodide_runtime

_STARTED_AT = time.monotonic()


def is_workers_runtime() -> bool:
    return is_pyodide_runtime()


def is_cold_start(window_s: float = 5.0) -> bool:
    return (time.monotonic() - _STARTED_AT) <= window_s


async def await_js(promise: object) -> object:
    return await promise  # type: ignore[misc]
