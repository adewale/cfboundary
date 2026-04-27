from __future__ import annotations

import asyncio
from types import SimpleNamespace

from cfboundary.ffi import (
    MAX_CONVERSION_DEPTH,
    consume_readable_stream,
    get_r2_size,
    stream_r2_body,
    to_js,
    to_js_bytes,
    to_py,
    to_py_bytes,
)
from cfboundary.testing import FakeJsModule, FakeJsProxy, patch_pyodide_runtime


def run(coro):
    return asyncio.run(coro)


def test_to_js_pyodide_paths() -> None:
    calls = []

    def converter(value, **kwargs):
        calls.append(kwargs)
        if "create_pyproxies" in kwargs:
            raise TypeError("legacy")
        return {"converted": value}

    with patch_pyodide_runtime(to_js_func=converter):
        assert to_js({"x": 1}) == {"converted": {"x": 1}}
        assert calls[0]["dict_converter"] is FakeJsModule.Object.fromEntries
        assert calls[0]["create_pyproxies"] is False
        assert calls[1] == {"dict_converter": FakeJsModule.Object.fromEntries}


def test_to_js_bytes_pyodide_and_cpython_paths() -> None:
    assert to_js_bytes(b"abc") == b"abc"
    with patch_pyodide_runtime(to_js_func=lambda value, **kwargs: memoryview(value)):
        assert bytes(to_js_bytes(b"abc")) == b"abc"


def test_to_py_edges_and_fake_proxy_access() -> None:
    assert FakeJsProxy({"x": 1}).x == 1
    assert FakeJsProxy(["a"])[0] == "a"
    assert FakeJsProxy(SimpleNamespace(y=2)).y == 2
    assert FakeJsModule.Object.fromEntries([("a", 1)]) == {"a": 1}
    opaque = object()
    assert to_py({"x": bytearray([1, 2]), "y": (memoryview(b"a"),)}) == {"x": [1, 2], "y": [[97]]}
    assert to_py("x", _depth=MAX_CONVERSION_DEPTH) == "x"
    assert to_py(opaque) is opaque

    class BadProxy:
        def to_py(self):
            raise RuntimeError("boom")

    assert to_py(BadProxy()) is None


def test_to_py_bytes_edges() -> None:
    assert to_py_bytes(None) == b""
    assert to_py_bytes(b"x") == b"x"
    assert to_py_bytes([65, 66]) == b"AB"
    assert to_py_bytes(bytearray(b"z")) == b"z"
    assert to_py_bytes(memoryview(b"m")) == b"m"

    class BytesLike:
        def __bytes__(self):
            return b"custom"

    assert to_py_bytes(BytesLike()) == b"custom"


class Reader:
    def __init__(self, values):
        self.values = list(values)
        self.released = False

    async def read(self):
        if self.values:
            return SimpleNamespace(done=False, value=self.values.pop(0))
        return SimpleNamespace(done=True, value=None)

    def releaseLock(self):
        self.released = True


class Stream:
    def __init__(self, values):
        self.reader = Reader(values)

    def getReader(self):
        return self.reader


class Buffer:
    async def arrayBuffer(self):
        return [1, 2, 3]


def test_stream_consumption_edges() -> None:
    stream = Stream([[65], None, [66]])
    assert run(consume_readable_stream(stream)) == b"AB"
    assert stream.reader.released is True
    assert run(consume_readable_stream(Buffer())) == b"\x01\x02\x03"
    assert run(consume_readable_stream([4, 5])) == b"\x04\x05"

    r2 = SimpleNamespace(body=Stream([[67], None, [68]]))
    assert run(_collect(stream_r2_body(r2))) == [b"C", b"D"]
    assert run(_collect(stream_r2_body(Buffer()))) == [b"\x01\x02\x03"]


async def _collect(iterator):
    return [chunk async for chunk in iterator]


def test_get_r2_size_edges() -> None:
    assert get_r2_size(SimpleNamespace(size="12")) == 12
    assert get_r2_size(SimpleNamespace()) is None
