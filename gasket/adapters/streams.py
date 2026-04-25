"""Streaming helpers that keep large binary payloads on the JavaScript side."""
from __future__ import annotations
from typing import Any
from gasket.ffi.safe_env import HAS_PYODIDE, SafeEnv, _to_js_value, is_js_null, js

async def serve_r2_object_via_js(
    env: object,
    bucket: str,
    key: str,
    *,
    headers: dict[str, str] | None = None,
) -> Any | None:
    """Return a JS Response streaming an R2 object's body, or None if absent."""
    raw_env = env._env if isinstance(env, SafeEnv) else env  # type: ignore[attr-defined]
    binding = getattr(raw_env, bucket)
    r2_obj = await binding.get(key)
    if r2_obj is None or is_js_null(r2_obj):
        return None
    if not HAS_PYODIDE or js is None:
        return r2_obj
    return js.Response.new(getattr(r2_obj, "body", r2_obj), _to_js_value({"headers": headers or {}}))
