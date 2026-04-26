"""CPython fakes for testing Pyodide branches."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator


class JsNull:
    """Fake for ``pyodide.ffi.jsnull``."""


class FakeJsProxy:
    def __init__(self, value: Any):
        self._value = value

    def to_py(self) -> Any:
        return self._value

    def __getattr__(self, name: str) -> Any:
        if isinstance(self._value, dict):
            return self._value[name]
        return getattr(self._value, name)

    def __getitem__(self, key: Any) -> Any:
        return self._value[key]


class _Object:
    @staticmethod
    def fromEntries(entries: Any) -> dict:
        return dict(entries)


class FakeJsModule:
    Object = _Object()
    undefined = None


@contextmanager
def patch_pyodide_runtime(
    *,
    has_pyodide: bool = True,
    js_module: Any | None = None,
    js_proxy_type: Any | None = None,
    js_null_value: Any | None = None,
    to_js_func: Any | None = None,
) -> Iterator[Any]:
    """Temporarily install a fake CFBoundary Pyodide runtime for tests."""
    import cfboundary.ffi.safe_env as target

    runtime_js = js_module or FakeJsModule()
    runtime_jsnull = js_null_value if js_null_value is not None else JsNull()
    runtime_proxy = js_proxy_type or FakeJsProxy
    runtime_to_js = to_js_func or (lambda value, **kwargs: value)
    old = (target.HAS_PYODIDE, target.js, target.JsProxy, target.jsnull, target._pyodide_to_js)
    target.configure_runtime(
        has_pyodide=has_pyodide,
        js_module=runtime_js,
        js_proxy_type=runtime_proxy,
        js_null_value=runtime_jsnull,
        to_js_func=runtime_to_js,
    )
    try:
        yield runtime_js
    finally:
        target.configure_runtime(
            has_pyodide=old[0],
            js_module=old[1],
            js_proxy_type=old[2],
            js_null_value=old[3],
            to_js_func=old[4],
        )
