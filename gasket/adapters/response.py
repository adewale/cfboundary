"""Response helpers for Python Workers."""
from __future__ import annotations
from typing import Any
from gasket.ffi.safe_env import HAS_PYODIDE, _to_js_value, js

async def full_response(
    body: bytes | str | object,
    *,
    media_type: str = "application/octet-stream",
    headers: dict[str, str] | None = None,
    cache_control: str | None = None,
) -> Any:
    """Return a JS Response with a fully buffered body.

    Avoid ASGI StreamingResponse in Workers for multi-chunk bodies.
    """
    final_headers = {"Content-Type": media_type, **(headers or {})}
    if cache_control:
        final_headers["Cache-Control"] = cache_control
    if HAS_PYODIDE and js is not None:
        return js.Response.new(body, _to_js_value({"headers": final_headers}))
    return {"body": body, "headers": final_headers, "status": 200}
