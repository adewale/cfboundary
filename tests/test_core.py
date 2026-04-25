from __future__ import annotations

from gasket.ffi import SafeEnv, d1_null, is_js_missing, is_js_null, js_null, to_py
from gasket.testing.fakes import FakeJsProxy, patch_pyodide_runtime


def test_safe_env_is_binding_name_agnostic() -> None:
    class RawEnv:
        DATABASE = object()
        OBJECTS = object()
        SESSION_STORE = object()

    env = SafeEnv(RawEnv())

    assert env.d1("DATABASE") is not None
    assert env.r2("OBJECTS") is not None
    assert env.kv("SESSION_STORE") is not None
    assert env.get("MISSING") is None


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
