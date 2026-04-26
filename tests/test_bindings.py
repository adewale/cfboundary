from __future__ import annotations

import asyncio
from types import SimpleNamespace

from cfboundary.ffi import (
    SafeAI,
    SafeAnalyticsEngine,
    SafeCache,
    SafeD1,
    SafeDurableObjectNamespace,
    SafeKV,
    SafeQueue,
    SafeR2,
    SafeService,
    SafeVectorize,
)


def run(coro):
    return asyncio.run(coro)


class D1Statement:
    def __init__(self):
        self.bound = None

    def bind(self, *args):
        self.bound = args
        return self

    async def first(self, column=None):
        if column:
            return "value"
        return {"answer": 42}

    async def all(self):
        return {"results": [{"a": 1}, {"a": 2}]}

    async def run(self):
        return {"success": True, "meta": {"changes": 1}}


class D1DB:
    def __init__(self):
        self.statement = D1Statement()

    def prepare(self, sql):
        self.sql = sql
        return self.statement

    async def exec(self, sql):
        return {"sql": sql}

    async def batch(self, statements):
        return [{"success": True} for _ in statements]


def test_safe_d1_statement_contract() -> None:
    db = SafeD1(D1DB())
    stmt = db.prepare("select ?")
    assert stmt.bind(None)._stmt.bound == (None,)
    assert run(stmt.first()) == {"answer": 42}
    assert run(stmt.first("answer")) == "value"
    assert run(stmt.all()) == [{"a": 1}, {"a": 2}]
    assert run(stmt.run()) == {"success": True, "meta": {"changes": 1}}
    assert run(db.exec("select 1")) == {"sql": "select 1"}
    assert run(db.batch([stmt])) == [{"success": True}]


class R2Object:
    size = 5
    httpMetadata = {"contentType": "text/plain"}

    async def text(self):
        return "hello"


class R2Bucket:
    def __init__(self):
        self.put_args = None
        self.deleted = None

    async def get(self, key):
        return None if key == "missing" else R2Object()

    async def put(self, *args):
        self.put_args = args
        return {"ok": True}

    async def delete(self, key):
        self.deleted = key
        return None

    async def list(self, options):
        return {"objects": [{"key": "a"}], "truncated": True, "cursor": "next"}


def test_safe_r2_contract() -> None:
    raw = R2Bucket()
    bucket = SafeR2(raw)
    obj = run(bucket.get("present"))
    assert obj is not None
    assert obj.size == 5
    assert run(obj.text()) == "hello"
    assert run(bucket.get("missing")) is None
    assert run(bucket.put("k", b"body", http_metadata={"contentType": "text/plain"})) == {"ok": True}
    assert raw.put_args[0] == "k"
    result = run(bucket.list(prefix="p", limit=1, cursor="c"))
    assert result.objects == [{"key": "a"}]
    assert result.truncated is True
    assert result.cursor == "next"


class KVNamespace:
    def __init__(self):
        self.values = {}

    async def get(self, key, options=None):
        return self.values.get(key)

    async def put(self, key, value, options=None):
        self.values[key] = value
        self.options = options

    async def delete(self, key):
        self.values.pop(key, None)

    async def list(self, options):
        return {"keys": [{"name": "a"}], "list_complete": True}


def test_safe_kv_contract() -> None:
    kv = SafeKV(KVNamespace())
    assert run(kv.get("missing")) is None
    run(kv.put("a", "b", expiration_ttl=60))
    assert run(kv.get("a")) == "b"
    assert run(kv.list(prefix="a"))["keys"] == [{"name": "a"}]


class Queue:
    async def send(self, *args):
        self.sent = args

    async def sendBatch(self, messages):
        self.batch = messages


def test_safe_queue_contract() -> None:
    raw = Queue()
    queue = SafeQueue(raw)
    run(queue.send({"type": "job"}))
    assert raw.sent[0] == {"type": "job"}
    assert raw.sent[1] == {"contentType": "json"}
    run(queue.send_batch([{"body": {"x": 1}}, "plain"]))
    assert raw.batch == [{"body": {"x": 1}}, {"body": "plain"}]


class AI:
    async def run(self, model, inputs):
        return {"model": model, "inputs": inputs}


def test_safe_ai_contract() -> None:
    assert run(SafeAI(AI()).run("@model", {"prompt": "hi"})) == {
        "model": "@model",
        "inputs": {"prompt": "hi"},
    }


class Vectorize:
    async def query(self, vector, options):
        return {"matches": [{"id": "a", "score": 0.5}], "options": options}

    async def insert(self, items):
        return {"count": len(items)}

    async def upsert(self, items):
        return {"count": len(items)}

    async def deleteByIds(self, ids):
        return {"ids": ids}


def test_safe_vectorize_contract() -> None:
    index = SafeVectorize(Vectorize())
    assert run(index.query([0.1], top_k=1)) == [{"id": "a", "score": 0.5}]
    assert run(index.insert([{"id": "a"}])) == {"count": 1}
    assert run(index.upsert([{"id": "a"}])) == {"count": 1}
    assert run(index.delete(["a"])) == {"ids": ["a"]}


class Service:
    value = {"wrapped": True}

    async def fetch(self, url, options=None):
        return SimpleNamespace(url=url, options=options)

    async def add(self, a, b):
        return {"result": a + b}


def test_safe_service_contract() -> None:
    service = SafeService(Service())
    response = run(service.fetch("https://example.com", method="GET"))
    assert response.url == "https://example.com"
    assert run(service.add(1, 2)) == {"result": 3}
    assert service.value == {"wrapped": True}


class DurableNamespace:
    def idFromName(self, name):
        return f"name:{name}"

    def idFromString(self, value):
        return f"id:{value}"

    def newUniqueId(self, options=None):
        return ("new", options)

    def get(self, object_id):
        return Service()


def test_safe_durable_object_namespace_contract() -> None:
    ns = SafeDurableObjectNamespace(DurableNamespace())
    assert ns.id_from_name("a") == "name:a"
    assert ns.id_from_string("123") == "id:123"
    assert ns.new_unique_id(jurisdiction="eu") == ("new", {"jurisdiction": "eu"})
    assert isinstance(ns.get("id"), SafeService)


class AnalyticsDataset:
    def writeDataPoint(self, payload):
        self.payload = payload
        return "ok"


def test_safe_analytics_contract() -> None:
    raw = AnalyticsDataset()
    assert SafeAnalyticsEngine(raw).write_data_point(blobs=["a"], doubles=[1.0]) == "ok"
    assert raw.payload == {"blobs": ["a"], "doubles": [1.0], "indexes": []}


class Cache:
    async def match(self, request, options=None):
        return None if request == "missing" else "response"

    async def put(self, request, response):
        self.stored = (request, response)

    async def delete(self, request, options=None):
        return True


def test_safe_cache_contract() -> None:
    cache = SafeCache(Cache())
    assert run(cache.match("missing")) is None
    assert run(cache.match("present")) == "response"
    run(cache.put("request", "response"))
    assert run(cache.delete("request")) is True
