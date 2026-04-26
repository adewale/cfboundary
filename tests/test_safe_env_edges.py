from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from cfboundary.ffi import SafeAI, SafeD1, SafeKV, SafeQueue, SafeR2, SafeService, SafeVectorize
from cfboundary.ffi.safe_env import SafeR2Object, _headers_to_dict, _to_py_safe, d1_rows, to_py, to_py_bytes


def run(coro):
    return asyncio.run(coro)


def test_to_py_depth_bad_proxy_tuple_and_fallback_object() -> None:
    class BadProxy:
        def to_py(self):
            raise RuntimeError("bad")

    class Plain:
        pass

    assert to_py(BadProxy()) is None
    assert to_py((1, 2)) == [1, 2]
    obj = Plain()
    assert to_py(obj) is obj
    assert _to_py_safe({"x": 1}, _depth=999) == {"x": 1}
    assert to_py_bytes(bytearray(b"abc")) == b"abc"
    assert to_py_bytes(memoryview(b"abc")) == b"abc"
    assert d1_rows(None) == []
    assert d1_rows({"results": None}) == []
    with pytest.raises(TypeError):
        to_py_bytes(object())


class ArrayBufferLike:
    async def arrayBuffer(self):
        return [120, 121, 122]


class PutBucket:
    def __init__(self):
        self.calls = []

    async def put(self, *args):
        self.calls.append(args)
        return "ok"

    async def delete(self, key):
        self.deleted = key

    async def list(self, opts):
        self.opts = opts
        return {}


def test_r2_put_without_options_delete_and_list_defaults() -> None:
    raw = PutBucket()
    bucket = SafeR2(raw)
    assert run(bucket.put("k", "text")) == "ok"
    assert raw.calls[-1] == ("k", "text")
    run(bucket.delete(["a", "b"]))
    assert raw.deleted == ["a", "b"]
    result = run(bucket.list())
    assert result.objects == []
    assert raw.opts == {"limit": 1000}


class KV:
    async def get(self, key, opts=None):
        self.get_opts = opts
        return b"bytes"

    async def put(self, *args):
        self.put_args = args

    async def delete(self, key):
        self.deleted = key

    async def list(self, opts):
        self.list_opts = opts
        return {"keys": []}


def test_kv_options_bytes_delete_and_list_defaults() -> None:
    raw = KV()
    kv = SafeKV(raw)
    assert run(kv.get("k", type="arrayBuffer")) == b"bytes"
    assert raw.get_opts == {"type": "arrayBuffer"}
    run(kv.put("k", b"v"))
    assert raw.put_args == ("k", b"v")
    run(kv.delete("k"))
    assert raw.deleted == "k"
    assert run(kv.list()) == {"keys": []}
    assert raw.list_opts == {}


class Queue:
    async def send(self, *args):
        self.args = args


def test_queue_send_without_kwargs() -> None:
    raw = Queue()
    run(SafeQueue(raw).send("body"))
    assert raw.args == ("body", {"contentType": "json"})


def test_safe_env_returns_existing_wrappers_and_missing_none() -> None:
    raw = SimpleNamespace(
        D1=SafeD1(object()),
        R2=SafeR2(object()),
        KV=SafeKV(object()),
        Q=SafeQueue(object()),
        AI=SafeAI(object()),
        V=SafeVectorize(object()),
        S=SafeService(object()),
    )
    from cfboundary.ffi import SafeEnv

    env = SafeEnv(raw)
    assert env.d1("D1") is raw.D1
    assert env.r2("R2") is raw.R2
    assert env.kv("KV") is raw.KV
    assert env.queue("Q") is raw.Q
    assert env.ai("AI") is raw.AI
    assert env.vectorize("V") is raw.V
    assert env.service("S") is raw.S
    assert env.d1("MISSING") is None
    assert SafeEnv(env).get("D1") is raw.D1
    assert env.D1 is raw.D1


def test_r2_object_bytes_text_fallback_and_stream() -> None:
    raw = ArrayBufferLike()
    obj = SafeR2Object(raw)
    assert run(obj.bytes()) == b"xyz"
    assert run(obj.text()) == "xyz"
    assert obj.stream() is raw

    raw_with_body = SimpleNamespace(body="stream", size=1, http_metadata={"a": "b"})
    obj_with_body = SafeR2Object(raw_with_body)
    assert obj_with_body.stream() == "stream"
    assert obj_with_body.http_metadata == {"a": "b"}


def test_assets_and_headers_to_dict() -> None:
    class Assets:
        async def fetch(self, request):
            return f"asset:{request}"

    from cfboundary.ffi import SafeAssets

    assert run(SafeAssets(Assets()).fetch("req")) == "asset:req"
    assert _headers_to_dict(None) == {}
    assert _headers_to_dict({"X": "Y"}) == {"x": "Y"}

    class Entries:
        def __init__(self):
            self.items = [("A", "B")]

        def next(self):
            if self.items:
                return SimpleNamespace(done=False, value=self.items.pop(0))
            return SimpleNamespace(done=True)

    assert _headers_to_dict(SimpleNamespace(entries=lambda: Entries())) == {"a": "B"}
    assert _headers_to_dict(SimpleNamespace(entries=lambda: (_ for _ in ()).throw(RuntimeError()))) == {}
