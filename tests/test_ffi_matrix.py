from __future__ import annotations

import pytest

from gasket.ffi import (
    _to_js_value,
    _to_py_safe,
    d1_null,
    get_js_null,
    is_js_null,
    is_js_null_or_undefined,
)
from gasket.testing.fakes import FakeJsProxy, patch_pyodide_runtime


@pytest.mark.parametrize("runtime", ["cpython", "pyodide-fake"])
def test_null_undefined_matrix(runtime: str) -> None:
    context = patch_pyodide_runtime() if runtime == "pyodide-fake" else _null_context()
    with context:
        js_null = get_js_null()
        assert is_js_null(None) is False
        assert is_js_null_or_undefined(None) is True
        if runtime == "pyodide-fake":
            assert is_js_null(js_null) is True
            assert d1_null(None) is js_null
        else:
            assert js_null is None
            assert d1_null(None) is None


@pytest.mark.parametrize("runtime", ["cpython", "pyodide-fake"])
def test_conversion_matrix(runtime: str) -> None:
    context = patch_pyodide_runtime() if runtime == "pyodide-fake" else _null_context()
    with context:
        js_null = get_js_null()
        value = {"a": FakeJsProxy({"b": js_null}) if runtime == "pyodide-fake" else {"b": None}}
        assert _to_py_safe(value) == {"a": {"b": None}}
        assert _to_js_value({"x": [1, 2]}) == {"x": [1, 2]}


class _null_context:
    def __enter__(self):
        return None

    def __exit__(self, *args):
        return False
