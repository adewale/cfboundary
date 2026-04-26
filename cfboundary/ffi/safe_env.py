"""Generic FFI boundary layer for Cloudflare Python Workers.

CFBoundary centralizes conversion at the JavaScript/Python boundary.  The module is
intentionally binding-name agnostic: applications choose their binding names and
request wrappers through :class:`SafeEnv` methods such as ``env.d1("DB")`` or
``env.r2("ASSETS_BUCKET")``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

try:  # pragma: no cover - exercised only inside the Pyodide/Workers runtime
    import js  # type: ignore[import-not-found]
    from pyodide.ffi import (  # type: ignore[import-not-found]
        JsException,
        JsProxy,
        jsnull,
        to_js as _pyodide_to_js,
    )

    HAS_PYODIDE = True
except ModuleNotFoundError as exc:
    if exc.name not in {"js", "pyodide"}:
        raise
    js = None  # type: ignore[assignment]
    JsProxy = None  # type: ignore[assignment,misc]
    jsnull = None  # type: ignore[assignment]
    _pyodide_to_js = None  # type: ignore[assignment]
    HAS_PYODIDE = False

    class JsException(Exception):  # type: ignore[no-redef]
        """Stub outside Pyodide."""

MAX_CONVERSION_DEPTH = 50


def configure_runtime(
    *,
    has_pyodide: bool | None = None,
    js_module: Any = None,
    js_proxy_type: Any = None,
    js_null_value: Any = None,
    to_js_func: Any = None,
) -> None:
    """Override the runtime bridge used by conversion helpers.

    This is primarily for application compatibility layers and tests that
    already monkeypatch their own Pyodide fakes. Production Workers normally use
    the module-level imports populated by Pyodide.
    """
    global HAS_PYODIDE, js, JsProxy, jsnull, _pyodide_to_js
    if has_pyodide is not None:
        HAS_PYODIDE = has_pyodide
    if js_module is not None:
        js = js_module
    if js_proxy_type is not None:
        JsProxy = js_proxy_type
    if js_null_value is not None:
        jsnull = js_null_value
    if to_js_func is not None:
        _pyodide_to_js = to_js_func


def js_null() -> Any:
    """Return JavaScript ``null`` in Workers; ``None`` in CPython tests.

    Pyodide exposes the singleton as ``pyodide.ffi.jsnull``. Avoid creating
    null via ``js.eval()`` or ``JSON.parse("null")``.
    """
    return jsnull if HAS_PYODIDE else None


def is_js_null(value: Any) -> bool:
    """Return True only for JavaScript ``null``.

    In current Pyodide, JavaScript ``undefined`` arrives in Python as ``None``;
    it is not a separate ``JsUndefined`` singleton.
    """
    if value is None:
        return False
    if HAS_PYODIDE and jsnull is not None and value is jsnull:
        return True
    return type(value).__name__ == "JsNull"


def is_js_missing(value: Any) -> bool:
    """Return True for JS null or JS undefined crossing into Python.

    JS undefined is represented as Python ``None`` by Pyodide.
    """
    if value is None or is_js_null(value):
        return True
    if HAS_PYODIDE and js is not None:
        try:
            return value is js.undefined
        except AttributeError:
            return False
    return False


def d1_null(value: Any = None) -> Any:
    """Convert Python ``None`` to JavaScript ``null`` for D1 bind values."""
    return js_null() if value is None else value


def _to_js_value(value: Any) -> Any:
    """Convert Python containers to JavaScript values suitable for Workers APIs.

    Dicts are converted to plain JS Objects, not Maps, and PyProxy creation is
    disabled so unsupported values fail fast rather than leaking proxies.
    """
    if not HAS_PYODIDE or _pyodide_to_js is None:
        return value
    try:
        return _pyodide_to_js(value, dict_converter=js.Object.fromEntries, create_pyproxies=False)
    except TypeError:
        return _pyodide_to_js(value, dict_converter=js.Object.fromEntries)


def to_js_bytes(data: bytes | bytearray | memoryview) -> Any:
    """Convert Python bytes-like values to a JS Uint8Array in Workers."""
    if not HAS_PYODIDE or _pyodide_to_js is None:
        return data
    return _pyodide_to_js(data)


def to_js(value: Any) -> Any:
    """Convert Python values to JavaScript values suitable for Workers APIs."""
    return _to_js_value(value)


def _to_py_safe(value: Any, depth: int = 0, *, _depth: int | None = None) -> Any:
    """Recursively convert JsProxy/null/undefined values to native Python."""
    if _depth is not None:
        depth = _depth
    if depth >= MAX_CONVERSION_DEPTH:
        return value
    if is_js_missing(value):
        return None
    if isinstance(value, int | float | str | bool | bytes):
        return value
    if HAS_PYODIDE and JsProxy is not None and isinstance(value, JsProxy) or hasattr(value, "to_py"):
        try:
            return _to_py_safe(value.to_py(), depth + 1)
        except Exception:
            return None
    if isinstance(value, dict):
        return {k: _to_py_safe(v, depth + 1) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_to_py_safe(v, depth + 1) for v in value]
    if isinstance(value, memoryview | bytearray):
        return list(value)
    return value


def to_py(value: Any) -> Any:
    """Public alias for JavaScript → Python conversion."""
    return _to_py_safe(value)


def to_py_bytes(value: Any) -> bytes:
    """Convert ArrayBuffer/Uint8Array/memoryview-ish values to bytes."""
    value = _to_py_safe(value)
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    if isinstance(value, list):
        return bytes(value)
    return bytes(value)


async def consume_readable_stream(value: Any) -> bytes:
    """Consume a JS ReadableStream/ArrayBuffer into Python bytes."""
    if value is not None and hasattr(value, "getReader"):
        reader = value.getReader()
        parts: list[bytes] = []
        try:
            while True:
                result = await reader.read()
                if getattr(result, "done", True):
                    break
                chunk = getattr(result, "value", None)
                if chunk is not None:
                    parts.append(to_py_bytes(chunk))
        finally:
            reader.releaseLock()
        return b"".join(parts)
    if value is not None and hasattr(value, "arrayBuffer"):
        value = await value.arrayBuffer()
    return to_py_bytes(value)


async def stream_r2_body(r2_obj: Any) -> Any:
    """Yield Python byte chunks from an R2 object's body."""
    body = getattr(r2_obj, "body", None)
    if body is not None and hasattr(body, "getReader"):
        reader = body.getReader()
        try:
            while True:
                result = await reader.read()
                if getattr(result, "done", True):
                    break
                chunk = getattr(result, "value", None)
                if chunk is not None:
                    yield to_py_bytes(chunk)
        finally:
            reader.releaseLock()
    else:
        yield await consume_readable_stream(r2_obj)


def get_r2_size(r2_obj: Any) -> int | None:
    size = getattr(r2_obj, "size", None)
    return None if is_js_missing(size) else int(size)


def d1_rows(results: Any) -> list[dict[str, Any]]:
    if is_js_missing(results):
        return []
    converted = _to_py_safe(results)
    rows = converted.get("results", converted) if isinstance(converted, dict) else getattr(converted, "results", converted)
    if rows is None:
        return []
    return list(rows)


def d1_first(result: Any) -> dict[str, Any] | None:
    converted = _to_py_safe(result)
    return converted if isinstance(converted, dict) else None


class SafeD1Statement:
    def __init__(self, stmt: Any) -> None:
        self._stmt = stmt

    def bind(self, *args: Any) -> "SafeD1Statement":
        self._stmt = self._stmt.bind(*[d1_null(_to_py_safe(a)) for a in args])
        return self

    async def first(self, column: str | None = None) -> Any:
        if column is None:
            return d1_first(await self._stmt.first())
        return _to_py_safe(await self._stmt.first(column))

    async def all(self) -> list[dict[str, Any]]:
        return d1_rows(await self._stmt.all())

    async def run(self) -> dict[str, Any]:
        return _to_py_safe(await self._stmt.run()) or {}


class SafeD1:
    def __init__(self, db: Any) -> None:
        self._db = db

    def prepare(self, sql: str) -> SafeD1Statement:
        return SafeD1Statement(self._db.prepare(sql))

    async def exec(self, sql: str) -> Any:
        return _to_py_safe(await self._db.exec(sql))

    async def batch(self, stmts: list[SafeD1Statement]) -> list[Any]:
        raw = [s._stmt for s in stmts]
        return _to_py_safe(await self._db.batch(_to_js_value(raw))) or []


class SafeR2Object:
    def __init__(self, obj: Any) -> None:
        self._obj = obj
        self.size = get_r2_size(obj) or 0
        self.http_metadata = _to_py_safe(getattr(obj, "httpMetadata", getattr(obj, "http_metadata", {}))) or {}

    async def bytes(self) -> bytes:
        return await consume_readable_stream(self._obj)

    async def text(self) -> str:
        if hasattr(self._obj, "text"):
            return str(await self._obj.text())
        return (await self.bytes()).decode("utf-8")

    def stream(self) -> object:
        return getattr(self._obj, "body", self._obj)


@dataclass
class R2ListResult:
    objects: list[Any]
    truncated: bool = False
    cursor: str | None = None


class SafeR2:
    def __init__(self, bucket: Any) -> None:
        self._bucket = bucket

    async def get(self, key: str) -> SafeR2Object | None:
        result = await self._bucket.get(key)
        return None if is_js_missing(result) else SafeR2Object(result)

    async def put(self, key: str, body: bytes | bytearray | memoryview | str, *, http_metadata: dict | None = None, **kwargs: Any) -> Any:
        if isinstance(body, bytes | bytearray | memoryview):
            body = to_js_bytes(body)
        options = dict(kwargs)
        if http_metadata is not None:
            options["httpMetadata"] = http_metadata
        if options:
            return await self._bucket.put(key, body, _to_js_value(options))
        return await self._bucket.put(key, body)

    async def delete(self, key: str | list[str]) -> Any:
        return await self._bucket.delete(_to_js_value(key))

    async def list(self, *, prefix: str | None = None, limit: int = 1000, cursor: str | None = None, **kwargs: Any) -> R2ListResult:
        opts = {"limit": limit, **kwargs}
        if prefix is not None:
            opts["prefix"] = prefix
        if cursor is not None:
            opts["cursor"] = cursor
        result = _to_py_safe(await self._bucket.list(_to_js_value(opts))) or {}
        return R2ListResult(result.get("objects", []), bool(result.get("truncated", False)), result.get("cursor"))


class SafeKV:
    def __init__(self, namespace: Any) -> None:
        self._kv = namespace

    async def get(self, key: str, *, type: str = "text", **kwargs: Any) -> Any | None:
        result = await self._kv.get(key, {"type": type, **kwargs} if kwargs or type != "text" else None)
        return None if is_js_missing(result) else _to_py_safe(result)

    async def put(self, key: str, value: bytes | str, *, expiration_ttl: int | None = None, **kwargs: Any) -> Any:
        opts = dict(kwargs)
        if expiration_ttl is not None:
            opts["expirationTtl"] = expiration_ttl
        if isinstance(value, bytes | bytearray | memoryview):
            value = to_js_bytes(value)
        return await self._kv.put(key, value, _to_js_value(opts)) if opts else await self._kv.put(key, value)

    async def delete(self, key: str) -> Any:
        return await self._kv.delete(key)

    async def list(self, *, prefix: str | None = None, **kwargs: Any) -> dict[str, Any]:
        opts = dict(kwargs)
        if prefix is not None:
            opts["prefix"] = prefix
        return _to_py_safe(await self._kv.list(_to_js_value(opts))) or {}


class SafeQueue:
    def __init__(self, queue: Any) -> None:
        self._queue = queue

    async def send(self, body: Any, *, content_type: Literal["json", "text", "bytes", "v8"] = "json", **kwargs: Any) -> Any:
        options = {"contentType": content_type, **kwargs}
        return await self._queue.send(_to_js_value(body), _to_js_value(options))

    async def send_batch(self, messages: list[Any]) -> Any:
        payload = [{"body": m} if not isinstance(m, dict) or "body" not in m else m for m in messages]
        return await self._queue.sendBatch(_to_js_value(payload))


class SafeAI:
    def __init__(self, ai: Any) -> None:
        self._ai = ai

    async def run(self, model: str, inputs: dict[str, Any]) -> Any | None:
        result = await self._ai.run(model, _to_js_value(inputs))
        return None if is_js_missing(result) else _to_py_safe(result)


class SafeVectorize:
    def __init__(self, index: Any) -> None:
        self._index = index

    async def query(self, vector: list[float], *, top_k: int = 10, return_metadata: bool = False, **options: Any) -> list[dict[str, Any]]:
        opts = {"topK": top_k, "returnMetadata": return_metadata, **options}
        result = _to_py_safe(await self._index.query(_to_js_value(vector), _to_js_value(opts))) or {}
        return result.get("matches", result if isinstance(result, list) else [])

    async def insert(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return _to_py_safe(await self._index.insert(_to_js_value(items))) or {}

    async def upsert(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return _to_py_safe(await self._index.upsert(_to_js_value(items))) or {}

    async def delete(self, ids: list[str]) -> dict[str, Any]:
        return await self.delete_by_ids(ids)

    async def delete_by_ids(self, ids: list[str]) -> dict[str, Any]:
        method = getattr(self._index, "deleteByIds", getattr(self._index, "delete", None))
        return _to_py_safe(await method(_to_js_value(ids))) or {}


class SafeService:
    """Generic wrapper for service/RPC bindings.

    ``fetch`` is exposed explicitly; other async methods are wrapped through
    ``__getattr__`` so service-binding RPC return values are converted to Python.
    """

    def __init__(self, binding: Any) -> None:
        self._binding = binding

    async def fetch(self, url: str, **kwargs: Any) -> Any:
        return await self._binding.fetch(url, _to_js_value(kwargs)) if kwargs else await self._binding.fetch(url)

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._binding, name)
        if not callable(attr):
            return _to_py_safe(attr)

        async def call(*args: Any, **kwargs: Any) -> Any:
            result = await attr(*[_to_js_value(a) for a in args], **{k: _to_js_value(v) for k, v in kwargs.items()})
            return _to_py_safe(result)

        return call


class SafeFetcher(SafeService):
    pass


class SafeDurableObjectNamespace:
    def __init__(self, namespace: Any) -> None:
        self._namespace = namespace

    def id_from_name(self, name: str) -> Any:
        return self._namespace.idFromName(name)

    def id_from_string(self, id_string: str) -> Any:
        return self._namespace.idFromString(id_string)

    def new_unique_id(self, **options: Any) -> Any:
        return self._namespace.newUniqueId(_to_js_value(options)) if options else self._namespace.newUniqueId()

    def get(self, object_id: Any) -> SafeService:
        return SafeService(self._namespace.get(object_id))


class SafeAnalyticsEngine:
    def __init__(self, dataset: Any) -> None:
        self._dataset = dataset

    def write_data_point(self, *, blobs: list[str] | None = None, doubles: list[float] | None = None, indexes: list[str] | None = None) -> Any:
        payload = {"blobs": blobs or [], "doubles": doubles or [], "indexes": indexes or []}
        return self._dataset.writeDataPoint(_to_js_value(payload))


class SafeCache:
    def __init__(self, cache: Any) -> None:
        self._cache = cache

    async def match(self, request: Any, **options: Any) -> Any | None:
        result = await self._cache.match(request, _to_js_value(options)) if options else await self._cache.match(request)
        return None if is_js_missing(result) else result

    async def put(self, request: Any, response: Any) -> Any:
        return await self._cache.put(request, response)

    async def delete(self, request: Any, **options: Any) -> bool:
        return bool(await self._cache.delete(request, _to_js_value(options)) if options else await self._cache.delete(request))


class SafeAssets:
    def __init__(self, assets: Any) -> None:
        self._assets = assets

    async def fetch(self, request: Any) -> Any:
        return await self._assets.fetch(request)


class SafeEnv:
    """Binding-name-agnostic access to Cloudflare Worker environment values."""

    def __init__(self, raw_env: Any) -> None:
        self._env = raw_env._env if isinstance(raw_env, SafeEnv) else raw_env

    def get(self, name: str, default: Any = None) -> Any:
        try:
            value = getattr(self._env, name)
        except AttributeError:
            return default
        return default if is_js_missing(value) else value

    def d1(self, name: str) -> SafeD1 | None:
        value = self.get(name)
        return None if value is None else value if isinstance(value, SafeD1) else SafeD1(value)

    def r2(self, name: str) -> SafeR2 | None:
        value = self.get(name)
        return None if value is None else value if isinstance(value, SafeR2) else SafeR2(value)

    def kv(self, name: str) -> SafeKV | None:
        value = self.get(name)
        return None if value is None else value if isinstance(value, SafeKV) else SafeKV(value)

    def queue(self, name: str) -> SafeQueue | None:
        value = self.get(name)
        return None if value is None else value if isinstance(value, SafeQueue) else SafeQueue(value)

    def ai(self, name: str) -> SafeAI | None:
        value = self.get(name)
        return None if value is None else value if isinstance(value, SafeAI) else SafeAI(value)

    def vectorize(self, name: str) -> SafeVectorize | None:
        value = self.get(name)
        return None if value is None else value if isinstance(value, SafeVectorize) else SafeVectorize(value)

    def service(self, name: str) -> SafeService | None:
        value = self.get(name)
        return None if value is None else value if isinstance(value, SafeService) else SafeService(value)

    def durable_object(self, name: str) -> SafeDurableObjectNamespace | None:
        value = self.get(name)
        return None if value is None else SafeDurableObjectNamespace(value)

    def analytics_engine(self, name: str) -> SafeAnalyticsEngine | None:
        value = self.get(name)
        return None if value is None else SafeAnalyticsEngine(value)

    def fetcher(self, name: str) -> SafeFetcher | None:
        value = self.get(name)
        return None if value is None else SafeFetcher(value)

    def assets(self, name: str = "ASSETS") -> SafeAssets | None:
        value = self.get(name)
        return None if value is None else SafeAssets(value)

    def secret(self, name: str) -> str:
        value = self.get(name)
        if value is None:
            raise KeyError(name)
        return str(value)

    def var(self, name: str, default: str | None = None) -> str | None:
        value = self.get(name, default)
        return None if value is None else str(value)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self._env, name)


def _headers_to_dict(headers: Any) -> dict[str, str]:
    out: dict[str, str] = {}
    if headers is None:
        return out
    if isinstance(headers, dict):
        return {str(k).lower(): str(v) for k, v in headers.items()}
    try:
        entries = headers.entries()
        while True:
            item = entries.next()
            if getattr(item, "done", True):
                break
            key, value = item.value[0], item.value[1]
            out[str(key).lower()] = str(value)
    except Exception:
        pass
    return out


__all__ = [
    "HAS_PYODIDE",
    "JsException",
    "configure_runtime",
    "MAX_CONVERSION_DEPTH",
    "js_null",
    "is_js_null",
    "is_js_missing",
    "d1_null",
    "to_py",
    "to_js",
    "to_js_bytes",
    "to_py_bytes",
    "consume_readable_stream",
    "stream_r2_body",
    "get_r2_size",
    "d1_rows",
    "d1_first",
    "SafeD1Statement",
    "SafeD1",
    "SafeR2Object",
    "R2ListResult",
    "SafeR2",
    "SafeKV",
    "SafeQueue",
    "SafeAI",
    "SafeVectorize",
    "SafeService",
    "SafeFetcher",
    "SafeDurableObjectNamespace",
    "SafeAnalyticsEngine",
    "SafeCache",
    "SafeAssets",
    "SafeEnv",
]
