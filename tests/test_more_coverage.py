from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

import cfboundary.ffi.primitives as primitives
from cfboundary.adapters import response as response_mod
from cfboundary.adapters import streams as streams_mod
from cfboundary.deploy.verifier import SmokeBase as VerifierSmokeBase
from cfboundary.ffi import SafeEnv, consume_readable_stream, get_r2_size, stream_r2_body, to_js_bytes, to_py_bytes
from cfboundary.testing.fakes import FakeJsModule, patch_pyodide_runtime


def run(coro):
    return asyncio.run(coro)


def test_primitives_reexports() -> None:
    assert primitives.js_object({"a": 1}) == {"a": 1}
    assert primitives.is_js_proxy(SimpleNamespace()) is False
    assert primitives.to_py({"a": 1}) == {"a": 1}
    assert primitives.to_js({"a": 1}) == {"a": 1}


def test_verifier_reexport() -> None:
    assert VerifierSmokeBase.__name__ == "SmokeBase"


def test_to_py_bytes_all_shapes() -> None:
    assert to_py_bytes(None) == b""
    assert to_py_bytes(b"abc") == b"abc"
    assert to_py_bytes(bytearray(b"abc")) == b"abc"
    assert to_py_bytes(memoryview(b"abc")) == b"abc"
    assert to_py_bytes([97, 98, 99]) == b"abc"


class Reader:
    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.released = False

    async def read(self):
        if not self.chunks:
            return SimpleNamespace(done=True)
        return SimpleNamespace(done=False, value=self.chunks.pop(0))

    def releaseLock(self):
        self.released = True


class Stream:
    def __init__(self, chunks):
        self.reader = Reader(chunks)

    def getReader(self):
        return self.reader


class ArrayBufferLike:
    async def arrayBuffer(self):
        return [120, 121, 122]


def test_stream_consumption_reader_and_arraybuffer() -> None:
    stream = Stream([[97], None, [98, 99]])
    assert run(consume_readable_stream(stream)) == b"abc"
    assert stream.reader.released is True
    assert run(consume_readable_stream(ArrayBufferLike())) == b"xyz"
    with pytest.raises(TypeError):
        run(consume_readable_stream(object()))


def test_stream_r2_body_reader_and_fallback() -> None:
    stream = Stream([[97], None, [98]])
    obj = SimpleNamespace(body=stream)
    assert run(_collect(stream_r2_body(obj))) == b"ab"
    assert stream.reader.released is True
    assert run(_collect(stream_r2_body(ArrayBufferLike()))) == b"xyz"


async def _collect(aiter):
    parts = []
    async for chunk in aiter:
        parts.append(chunk)
    return b"".join(parts)


def test_r2_size_missing_null_and_valid() -> None:
    assert get_r2_size(SimpleNamespace()) is None
    assert get_r2_size(SimpleNamespace(size=None)) is None
    assert get_r2_size(SimpleNamespace(size="12")) == 12


def test_safe_env_all_binding_methods_and_vars() -> None:
    raw = SimpleNamespace(
        D1=object(),
        R2=object(),
        KV=object(),
        QUEUE=object(),
        AI=object(),
        VEC=object(),
        SVC=object(),
        DO=object(),
        AE=object(),
        FETCH=object(),
        ASSETS=object(),
        SECRET="s",
        VAR="v",
    )
    env = SafeEnv(raw)
    assert env.d1("D1") is not None
    assert env.r2("R2") is not None
    assert env.kv("KV") is not None
    assert env.queue("QUEUE") is not None
    assert env.ai("AI") is not None
    assert env.vectorize("VEC") is not None
    assert env.service("SVC") is not None
    assert env.durable_object("DO") is not None
    assert env.analytics_engine("AE") is not None
    assert env.fetcher("FETCH") is not None
    assert env.assets("ASSETS") is not None
    assert env.secret("SECRET") == "s"
    assert env.var("VAR") == "v"
    assert env.var("MISSING", "d") == "d"
    with pytest.raises(KeyError):
        env.secret("MISSING")
    with pytest.raises(AttributeError):
        env._private


def test_wrapping_safe_env_preserves_raw_environment() -> None:
    raw = SimpleNamespace(D1=object(), R2=object(), KV=object(), QUEUE=object(), AI=object(), VEC=object(), SVC=object())
    env = SafeEnv(raw)
    assert SafeEnv(env).get("D1") is raw.D1


def test_pyodide_fake_to_js_bytes_and_adapters(monkeypatch) -> None:
    calls = []

    class Response:
        @staticmethod
        def new(body, init=None):
            calls.append((body, init))
            return {"body": body, "init": init}

    module = FakeJsModule()
    module.Response = Response
    with patch_pyodide_runtime(js_module=module):
        assert to_js_bytes(b"abc") == b"abc"
        monkeypatch.setattr(response_mod, "js", module)
        monkeypatch.setattr(streams_mod, "js", module)
        assert run(response_mod.full_response("ok", media_type="text/plain"))["body"] == "ok"
        bucket = SimpleNamespace(get=lambda key: _await(SimpleNamespace(body="stream")))
        env = SimpleNamespace(BUCKET=bucket)
        assert run(streams_mod.serve_r2_object_via_js(env, "BUCKET", "key"))["body"] == "stream"


def _await(value):
    async def inner():
        return value

    return inner()


