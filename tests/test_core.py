from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from cfboundary.ffi import (
    MAX_CONVERSION_DEPTH,
    consume_readable_stream,
    d1_null,
    get_r2_size,
    js_null,
    stream_r2_body,
    to_py,
)
from cfboundary.testing.fakes import FakeJsProxy, patch_pyodide_runtime


def test_to_py_converts_nested_js_proxy_values() -> None:
    with patch_pyodide_runtime():
        jsnull = js_null()
        proxy = FakeJsProxy({"ok": True, "none": jsnull, "nested": [FakeJsProxy({"x": 1})]})
        assert to_py(proxy) == {"ok": True, "none": None, "nested": [{"x": 1}]}


def test_d1_null_preserves_non_none_values() -> None:
    assert d1_null("x") == "x"
    assert d1_null(0) == 0


def test_to_py_terminates_on_cyclic_values() -> None:
    # A JS object graph can refer to itself; conversion must stop instead of recursing forever.
    cycle: list = []
    cycle.append(cycle)
    node = to_py(cycle)
    levels = 0
    while node is not cycle:
        node = node[0]
        levels += 1
    assert 0 < levels <= MAX_CONVERSION_DEPTH

    entries: dict = {}
    proxy_cycle = FakeJsProxy(entries)
    entries["self"] = proxy_cycle
    assert set(to_py(proxy_cycle)) == {"self"}


def test_get_r2_size_treats_js_null_as_missing_and_keeps_zero() -> None:
    with patch_pyodide_runtime():
        assert get_r2_size(SimpleNamespace(size=js_null())) is None
    assert get_r2_size(SimpleNamespace(size=0)) == 0


class _FailingReader:
    def __init__(self) -> None:
        self.released = False

    async def read(self):
        raise RuntimeError("stream errored")

    def releaseLock(self) -> None:
        self.released = True


class _Stream:
    def __init__(self, reader) -> None:
        self.reader = reader

    def getReader(self):
        return self.reader


class _ChunkReader(_FailingReader):
    def __init__(self, chunks) -> None:
        super().__init__()
        self.chunks = list(chunks)

    async def read(self):
        if self.chunks:
            return SimpleNamespace(done=False, value=self.chunks.pop(0))
        return SimpleNamespace(done=True, value=None)


async def _collect(iterator):
    return [chunk async for chunk in iterator]


def test_consume_readable_stream_releases_lock_when_read_fails() -> None:
    reader = _FailingReader()
    with pytest.raises(RuntimeError, match="stream errored"):
        asyncio.run(consume_readable_stream(_Stream(reader)))
    assert reader.released is True


def test_stream_r2_body_releases_lock_after_success_and_failure() -> None:
    reader = _ChunkReader([[1], [2]])
    assert asyncio.run(_collect(stream_r2_body(SimpleNamespace(body=_Stream(reader))))) == [
        b"\x01",
        b"\x02",
    ]
    assert reader.released is True

    failing = _FailingReader()
    with pytest.raises(RuntimeError, match="stream errored"):
        asyncio.run(_collect(stream_r2_body(SimpleNamespace(body=_Stream(failing)))))
    assert failing.released is True
