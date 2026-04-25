"""Low-level Python/JavaScript FFI conversion helpers."""
from .safe_env import (  # noqa: F401
    HAS_PYODIDE,
    _is_js_null_or_undefined,
    _to_js_value,
    _to_py_safe,
    consume_readable_stream,
    d1_null,
    get_js_null,
    is_js_null,
    stream_r2_body,
    to_js_bytes,
    to_py_bytes,
)

is_js_null_or_undefined = _is_js_null_or_undefined
to_py = _to_py_safe
to_js = _to_js_value

def is_js_proxy(x: object) -> bool:
    return HAS_PYODIDE and hasattr(x, "to_py")

def js_object(d: dict) -> object:
    return _to_js_value(d)
