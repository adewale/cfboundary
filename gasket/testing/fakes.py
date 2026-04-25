"""CPython fakes for testing Pyodide branches."""
from __future__ import annotations
from contextlib import contextmanager
from typing import Any

class JsNull: pass
class JsUndefined: pass

class FakeJsProxy:
    def __init__(self, value: Any): self._value = value
    def to_py(self) -> Any: return self._value
    def __getattr__(self, name: str) -> Any:
        if isinstance(self._value, dict): return self._value[name]
        return getattr(self._value, name)
    def __getitem__(self, key: Any) -> Any: return self._value[key]

class _JSON:
    @staticmethod
    def parse(value: str) -> Any:
        return JsNull() if value == "null" else value

class _Object:
    @staticmethod
    def fromEntries(entries: Any) -> dict: return dict(entries)

class FakeJsModule:
    JSON = _JSON()
    Object = _Object()
    undefined = JsUndefined()

@contextmanager
def patch_pyodide_runtime(*, with_module: FakeJsModule | None = None):
    import gasket.ffi.safe_env as target
    old = (target.HAS_PYODIDE, target.js, target.JsProxy, target.to_js)
    target.HAS_PYODIDE = True
    target.js = with_module or FakeJsModule()
    target.JsProxy = FakeJsProxy
    target.to_js = lambda value, **kwargs: value
    try:
        yield
    finally:
        target.HAS_PYODIDE, target.js, target.JsProxy, target.to_js = old
