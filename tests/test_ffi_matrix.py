from __future__ import annotations

from cfboundary.ffi import d1_null, is_js_missing, is_js_null, js_null
from cfboundary.testing.fakes import patch_pyodide_runtime


def test_cpython_fallback_uses_none_for_js_null() -> None:
    assert js_null() is None
    assert d1_null(None) is None
    assert is_js_null(None) is False
    assert is_js_missing(None) is True


def test_pyodide_runtime_binds_none_as_the_runtime_js_null() -> None:
    sentinel = object()
    with patch_pyodide_runtime(js_null_value=sentinel):
        assert js_null() is sentinel
        assert d1_null(None) is sentinel
        assert is_js_null(sentinel) is True
        assert is_js_missing(sentinel) is True
        assert is_js_null(None) is False
        assert is_js_missing(None) is True
