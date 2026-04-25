from __future__ import annotations

from gasket.ffi import SafeEnv, _is_js_undefined, _to_py_safe, d1_null, get_js_null, is_js_null
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


def test_to_py_safe_converts_nested_js_proxy_values() -> None:
    with patch_pyodide_runtime():
        jsnull = get_js_null()
        proxy = FakeJsProxy({"ok": True, "none": jsnull, "nested": [FakeJsProxy({"x": 1})]})
        assert _to_py_safe(proxy) == {"ok": True, "none": None, "nested": [{"x": 1}]}


def test_pyodide_null_and_undefined_semantics() -> None:
    with patch_pyodide_runtime():
        assert is_js_null(get_js_null()) is True
        assert is_js_null(None) is False
        assert _is_js_undefined(None) is True


def test_d1_null_preserves_non_none_values() -> None:
    assert d1_null("x") == "x"
    assert d1_null(0) == 0
