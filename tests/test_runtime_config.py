from __future__ import annotations

import pytest

import cfboundary.ffi as ffi
import cfboundary.ffi.safe_env as safe_env


def test_configure_runtime_overrides_and_restores_conversion_globals() -> None:
    original = (
        safe_env.HAS_PYODIDE,
        safe_env.js,
        safe_env.JsProxy,
        safe_env.jsnull,
        safe_env._pyodide_to_js,
    )

    class Proxy:
        def __init__(self, value):
            self.value = value

        def to_py(self):
            return self.value

    class JsNull:
        pass

    sentinel = JsNull()
    other_null = JsNull()
    undefined = object()

    def fake_to_js(value, **kwargs):
        return {"value": value, "kwargs": kwargs}

    ffi.configure_runtime(
        has_pyodide=True,
        js_module=type("JS", (), {"Object": type("Object", (), {"fromEntries": object()}), "undefined": undefined})(),
        js_proxy_type=Proxy,
        js_null_value=sentinel,
        to_js_func=fake_to_js,
    )
    try:
        assert ffi.js_null() is sentinel
        assert ffi.to_py(Proxy({"x": sentinel, "y": other_null, "z": undefined})) == {
            "x": None,
            "y": None,
            "z": None,
        }
        assert ffi.to_js({"a": 1})["value"] == {"a": 1}
        ffi.configure_runtime()
        assert safe_env.HAS_PYODIDE is True
        assert ffi.is_pyodide_runtime() is True
        ffi.configure_runtime(js_module=object())
        assert ffi.is_js_missing(object()) is False
    finally:
        ffi.configure_runtime(
            has_pyodide=original[0],
            js_module=original[1],
            js_proxy_type=original[2],
            js_null_value=original[3],
            to_js_func=original[4],
        )


def test_to_js_runtime_override_supports_legacy_fake_without_create_pyproxies() -> None:
    original = (safe_env.HAS_PYODIDE, safe_env.js, safe_env._pyodide_to_js)

    def legacy_to_js(value, *, dict_converter=None):
        return {"value": value, "dict_converter": dict_converter}

    ffi.configure_runtime(
        has_pyodide=True,
        js_module=type("JS", (), {"Object": type("Object", (), {"fromEntries": object()})})(),
        to_js_func=legacy_to_js,
    )
    try:
        assert ffi.to_js({"a": 1})["value"] == {"a": 1}
    finally:
        ffi.configure_runtime(has_pyodide=original[0], js_module=original[1], to_js_func=original[2])


def test_to_js_runtime_override_reraises_non_signature_type_error() -> None:
    original = (safe_env.HAS_PYODIDE, safe_env.js, safe_env._pyodide_to_js)

    def bad_to_js(value, **kwargs):
        raise TypeError("bad value")

    ffi.configure_runtime(
        has_pyodide=True,
        js_module=type("JS", (), {"Object": type("Object", (), {"fromEntries": object()})})(),
        to_js_func=bad_to_js,
    )
    try:
        with pytest.raises(TypeError):
            ffi.to_js({"a": 1})
    finally:
        ffi.configure_runtime(has_pyodide=original[0], js_module=original[1], to_js_func=original[2])
