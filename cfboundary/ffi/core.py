"""Generic FFI conversion helpers for Cloudflare Python Workers."""

from __future__ import annotations

from importlib import import_module
from typing import Any, cast

try:  # pragma: no cover - exercised only inside the Pyodide/Workers runtime
    js: Any = import_module("js")
    pyodide_ffi: Any = import_module("pyodide.ffi")
    JsException: Any = pyodide_ffi.JsException
    JsProxy: Any = pyodide_ffi.JsProxy
    jsnull: Any = pyodide_ffi.jsnull
    _pyodide_to_js: Any = pyodide_ffi.to_js
    HAS_PYODIDE = True
except ModuleNotFoundError as exc:
    if exc.name not in {"js", "pyodide", "pyodide.ffi"}:
        raise
    js: Any = None
    JsProxy: Any = None
    jsnull: Any = None
    _pyodide_to_js: Any = None
    HAS_PYODIDE = False

    class JsException(Exception):
        """Stub outside Pyodide."""


MAX_CONVERSION_DEPTH = 50


def configure_runtime(
    *,
    has_pyodide: bool | None = None,
    js_module: Any = None,
    js_proxy_type: Any = None,
    js_null_value: Any = None,
    to_js_func: Any = None,
) -> None:
    """Internal runtime override used by :func:`cfboundary.testing.patch_pyodide_runtime`."""
    global HAS_PYODIDE, js, JsProxy, jsnull, _pyodide_to_js
    if has_pyodide is not None:
        HAS_PYODIDE = has_pyodide
    if js_module is not None:
        js = js_module
    if js_proxy_type is not None:
        JsProxy = js_proxy_type
    if js_null_value is not None:
        jsnull = js_null_value
    if to_js_func is not None:
        _pyodide_to_js = to_js_func


def is_pyodide_runtime() -> bool:
    """Return whether the active runtime configuration is Pyodide/Workers."""
    return HAS_PYODIDE


def js_null() -> Any:
    """Return JavaScript ``null`` in Workers; ``None`` in CPython tests."""
    return jsnull if HAS_PYODIDE else None


def is_js_null(value: Any) -> bool:
    """Return True only for JavaScript ``null``."""
    if value is None:
        return False
    if HAS_PYODIDE and jsnull is not None and value is jsnull:
        return True
    return type(value).__name__ == "JsNull"


def is_js_missing(value: Any) -> bool:
    """Return True for Python ``None``/JS ``undefined`` or JS ``null``."""
    return value is None or is_js_null(value)


def d1_null(value: Any = None) -> Any:
    """Convert Python ``None`` to JavaScript ``null`` for D1 bind values."""
    return js_null() if value is None else value


def to_js(value: Any) -> Any:
    """Convert Python values to JavaScript values suitable for Workers APIs."""
    if not HAS_PYODIDE or _pyodide_to_js is None:
        return value
    js_module = cast(Any, js)
    try:
        return _pyodide_to_js(value, dict_converter=js_module.Object.fromEntries, create_pyproxies=False)
    except TypeError:
        return _pyodide_to_js(value, dict_converter=js_module.Object.fromEntries)


def to_js_bytes(data: bytes | bytearray | memoryview) -> Any:
    """Convert Python bytes-like values to a JS Uint8Array in Workers."""
    if not HAS_PYODIDE or _pyodide_to_js is None:
        return data
    return _pyodide_to_js(data)


def to_py(value: Any, depth: int = 0, *, _depth: int | None = None) -> Any:
    """Recursively convert JsProxy, JS null, and missing values to native Python."""
    if _depth is not None:
        depth = _depth
    if depth >= MAX_CONVERSION_DEPTH:
        return value
    if is_js_missing(value):
        return None
    if isinstance(value, int | float | str | bool | bytes):
        return value
    if (HAS_PYODIDE and JsProxy is not None and isinstance(value, JsProxy)) or hasattr(value, "to_py"):
        try:
            return to_py(value.to_py(), depth + 1)
        except Exception:
            return None
    if isinstance(value, dict):
        return {k: to_py(v, depth + 1) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [to_py(v, depth + 1) for v in value]
    if isinstance(value, memoryview | bytearray):
        return list(value)
    return value


def to_py_bytes(value: Any) -> bytes:
    """Convert ArrayBuffer/Uint8Array/memoryview-ish values to bytes."""
    value = to_py(value)
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    if isinstance(value, list):
        return bytes(value)
    return bytes(value)


async def consume_readable_stream(value: Any) -> bytes:
    """Consume a JS ReadableStream/ArrayBuffer into Python bytes."""
    if value is not None and hasattr(value, "getReader"):
        reader = value.getReader()
        parts: list[bytes] = []
        try:
            while True:
                result = await reader.read()
                if getattr(result, "done", True):
                    break
                chunk = getattr(result, "value", None)
                if chunk is not None:
                    parts.append(to_py_bytes(chunk))
        finally:
            reader.releaseLock()
        return b"".join(parts)
    if value is not None and hasattr(value, "arrayBuffer"):
        value = await value.arrayBuffer()
    return to_py_bytes(value)


async def stream_r2_body(r2_obj: Any) -> Any:
    """Yield Python byte chunks from an R2 object's body."""
    body = getattr(r2_obj, "body", None)
    if body is not None and hasattr(body, "getReader"):
        reader = body.getReader()
        try:
            while True:
                result = await reader.read()
                if getattr(result, "done", True):
                    break
                chunk = getattr(result, "value", None)
                if chunk is not None:
                    yield to_py_bytes(chunk)
        finally:
            reader.releaseLock()
    else:
        yield await consume_readable_stream(r2_obj)


def get_r2_size(r2_obj: Any) -> int | None:
    """Return an R2 object's size when available."""
    size = getattr(r2_obj, "size", None)
    if is_js_missing(size):
        return None
    concrete_size = cast(Any, size)
    return int(concrete_size)


__all__ = [
    "JsException",
    "MAX_CONVERSION_DEPTH",
    "is_pyodide_runtime",
    "js_null",
    "is_js_null",
    "is_js_missing",
    "d1_null",
    "to_py",
    "to_js",
    "to_js_bytes",
    "to_py_bytes",
    "consume_readable_stream",
    "stream_r2_body",
    "get_r2_size",
]
