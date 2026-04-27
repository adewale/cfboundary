from __future__ import annotations

from cfboundary.ffi import d1_null, is_js_missing, is_js_null, js_null, to_py
from cfboundary.testing.fakes import FakeJsProxy, patch_pyodide_runtime


def test_to_py_converts_nested_js_proxy_values() -> None:
    with patch_pyodide_runtime():
        jsnull = js_null()
        proxy = FakeJsProxy({"ok": True, "none": jsnull, "nested": [FakeJsProxy({"x": 1})]})
        assert to_py(proxy) == {"ok": True, "none": None, "nested": [{"x": 1}]}


def test_pyodide_null_and_undefined_semantics() -> None:
    with patch_pyodide_runtime():
        assert is_js_null(js_null()) is True
        assert is_js_null(None) is False
        assert is_js_missing(None) is True


def test_d1_null_preserves_non_none_values() -> None:
    assert d1_null("x") == "x"
    assert d1_null(0) == 0
