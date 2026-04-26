"""Low-level Python/JavaScript FFI conversion helpers."""

from .safe_env import (  # noqa: F401
    consume_readable_stream,
    d1_null,
    is_js_missing,
    is_js_null,
    is_pyodide_runtime,
    js_null,
    stream_r2_body,
    to_js,
    to_js_bytes,
    to_py,
    to_py_bytes,
)


def is_js_proxy(x: object) -> bool:
    return is_pyodide_runtime() and hasattr(x, "to_py")


def js_object(d: dict) -> object:
    return to_js(d)
