"""Checks that run cfboundary inside real Pyodide (Node), not the CPython fakes.

``run_real_pyodide.test.mjs`` loads the pinned ``pyodide`` npm package, mounts
this repository, and runs every ``check_*`` function below as a separate
``node:test`` case. Nothing here is collected by pytest under CPython.

Each check pins a boundary semantic against the real ``JsProxy``/``jsnull``/
``to_js`` implementation, usually next to the raw Pyodide behaviour that
cfboundary exists to smooth over, so a Pyodide upgrade that changes either side
fails here instead of in a deployed Worker.
"""

from __future__ import annotations

from importlib import import_module
from types import SimpleNamespace
from typing import Any

import cfboundary
from cfboundary.ffi import (
    consume_readable_stream,
    core,
    d1_null,
    get_r2_size,
    is_js_missing,
    is_js_null,
    js_null,
    stream_r2_body,
    to_js,
    to_js_bytes,
    to_py,
    to_py_bytes,
)

js: Any = import_module("js")
pyodide_ffi: Any = import_module("pyodide.ffi")


def _js(expression: str) -> Any:
    """Evaluate a JavaScript expression and return the (proxied) result."""
    return js.Function.new(f"return ({expression});")()


def _tag(value: Any) -> str:
    return str(js.Object.prototype.toString.call(value))


def check_runtime_is_real_pyodide() -> None:
    assert cfboundary.__file__.startswith("/repo/cfboundary/"), cfboundary.__file__
    assert core.HAS_PYODIDE is True
    assert core.jsnull is pyodide_ffi.jsnull
    assert core.JsProxy is pyodide_ffi.JsProxy
    assert core._pyodide_to_js is pyodide_ffi.to_js


def check_js_null_and_d1_null_return_real_jsnull() -> None:
    assert js_null() is pyodide_ffi.jsnull
    assert d1_null(None) is pyodide_ffi.jsnull
    assert d1_null(0) == 0
    assert d1_null("") == ""
    assert d1_null(False) is False


def check_jsnull_is_falsy_and_named_jsnull() -> None:
    assert not pyodide_ffi.jsnull
    assert type(pyodide_ffi.jsnull).__name__ == "JsNull"


def check_js_null_and_undefined_arrive_differently() -> None:
    value = _js("{present_null: null, present_undefined: undefined}")
    # JS null arrives as jsnull; undefined arrives as Python None.
    assert value.present_null is pyodide_ffi.jsnull
    assert value.present_undefined is None
    assert is_js_null(value.present_null) is True
    assert is_js_null(value.present_undefined) is False
    assert is_js_missing(value.present_null) is True
    assert is_js_missing(value.present_undefined) is True
    # An absent property raises AttributeError, so callers need getattr(obj, name, None).
    assert getattr(value, "absent", None) is None


def check_to_py_normalises_nested_js_values() -> None:
    value = _js("{a: null, b: undefined, c: [1, null, {d: 'x'}], e: new Uint8Array([1, 2, 3])}")
    assert isinstance(value, pyodide_ffi.JsProxy)
    # Raw Pyodide keeps jsnull and a memoryview; cfboundary normalises both.
    raw = value.to_py()
    assert raw["a"] is pyodide_ffi.jsnull
    assert raw["c"][1] is pyodide_ffi.jsnull
    assert isinstance(raw["e"], memoryview)
    assert to_py(value) == {"a": None, "b": None, "c": [1, None, {"d": "x"}], "e": [1, 2, 3]}


def check_to_js_turns_dicts_into_plain_objects() -> None:
    # Raw to_js turns a dict into a JS Map, which JSON.stringify and most Workers APIs ignore.
    assert _tag(pyodide_ffi.to_js({"a": 1})) == "[object Map]"
    converted = to_js({"a": 1, "nested": {"b": [1, 2]}})
    assert _tag(converted) == "[object Object]"
    assert str(js.JSON.stringify(converted)) == '{"a":1,"nested":{"b":[1,2]}}'


def check_to_js_none_dict_value_becomes_undefined_and_leaves_json() -> None:
    converted = to_js({"k": None, "n": [1, None], "j": js_null()})
    # The key survives on the JS object, but its value is undefined, not null...
    assert list(js.Object.keys(converted).to_py()) == ["k", "n", "j"]
    assert js.Object.getOwnPropertyDescriptor(converted, "k").value is None
    assert converted.j is pyodide_ffi.jsnull
    # ...so JSON.stringify drops it. Use d1_null()/js_null() when the key must stay as null.
    assert str(js.JSON.stringify(converted)) == '{"n":[1,null],"j":null}'


def check_to_js_rejects_unconvertible_values_with_conversion_error() -> None:
    class Opaque:
        pass

    try:
        to_js({"value": Opaque()})
    except pyodide_ffi.ConversionError as exc:
        # Not a TypeError: a retry-on-TypeError fallback would never run here.
        assert not isinstance(exc, TypeError)
    else:
        raise AssertionError("to_js accepted a value it cannot convert without a PyProxy")


def check_bytes_round_trip_through_uint8array() -> None:
    converted = to_js_bytes(b"abc")
    assert _tag(converted) == "[object Uint8Array]"
    assert to_py_bytes(converted) == b"abc"
    assert to_py_bytes(_js("new Uint8Array([104, 105]).buffer")) == b"hi"


async def check_consume_readable_stream_reads_real_streams() -> None:
    chunked = _js(
        "new ReadableStream({start(c) {"
        " c.enqueue(new Uint8Array([97, 98]));"
        " c.enqueue(new Uint8Array([99]));"
        " c.close(); }})"
    )
    assert await consume_readable_stream(chunked) == b"abc"
    assert await consume_readable_stream(js.Response.new("hello").body) == b"hello"
    # A Response has no getReader(), so this exercises the arrayBuffer() path.
    assert await consume_readable_stream(js.Response.new("buffered")) == b"buffered"


async def check_stream_r2_body_yields_real_chunks() -> None:
    body = _js(
        "new ReadableStream({start(c) {"
        " c.enqueue(new Uint8Array([1, 2]));"
        " c.enqueue(new Uint8Array([3]));"
        " c.close(); }})"
    )
    chunks = [chunk async for chunk in stream_r2_body(SimpleNamespace(body=body))]
    assert chunks == [b"\x01\x02", b"\x03"]


def check_get_r2_size_treats_js_null_and_undefined_as_missing() -> None:
    assert get_r2_size(_js("{size: 5}")) == 5
    assert get_r2_size(_js("{size: null}")) is None
    assert get_r2_size(_js("{}")) is None
