from __future__ import annotations

import pytest

import cfboundary.ffi as ffi
import cfboundary.ffi.core as core


def test_configure_runtime_overrides_and_restores_conversion_globals() -> None:
    original = (
        core.HAS_PYODIDE,
        core.js,
        core.JsProxy,
        core.jsnull,
        core._pyodide_to_js,
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

    core.configure_runtime(
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
        core.configure_runtime()
        assert core.HAS_PYODIDE is True
        assert ffi.is_pyodide_runtime() is True
        core.configure_runtime(js_module=object())
        assert ffi.is_js_missing(object()) is False
    finally:
        core.configure_runtime(
            has_pyodide=original[0],
            js_module=original[1],
            js_proxy_type=original[2],
            js_null_value=original[3],
            to_js_func=original[4],
        )


def test_to_js_runtime_override_supports_legacy_fake_without_create_pyproxies() -> None:
    original = (core.HAS_PYODIDE, core.js, core._pyodide_to_js)

    def legacy_to_js(value, *, dict_converter=None):
        return {"value": value, "dict_converter": dict_converter}

    core.configure_runtime(
        has_pyodide=True,
        js_module=type("JS", (), {"Object": type("Object", (), {"fromEntries": object()})})(),
        to_js_func=legacy_to_js,
    )
    try:
        assert ffi.to_js({"a": 1})["value"] == {"a": 1}
    finally:
        core.configure_runtime(has_pyodide=original[0], js_module=original[1], to_js_func=original[2])


def test_to_js_runtime_override_reraises_non_signature_type_error() -> None:
    original = (core.HAS_PYODIDE, core.js, core._pyodide_to_js)

    def bad_to_js(value, **kwargs):
        raise TypeError("bad value")

    core.configure_runtime(
        has_pyodide=True,
        js_module=type("JS", (), {"Object": type("Object", (), {"fromEntries": object()})})(),
        to_js_func=bad_to_js,
    )
    try:
        with pytest.raises(TypeError):
            ffi.to_js({"a": 1})
    finally:
        core.configure_runtime(has_pyodide=original[0], js_module=original[1], to_js_func=original[2])
