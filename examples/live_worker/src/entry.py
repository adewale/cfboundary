"""Deployable Worker used by CFBoundary live E2E tests."""

from __future__ import annotations

import json
import time
from typing import Any

from cfboundary.ffi import d1_null, is_js_missing, is_pyodide_runtime, to_js, to_js_bytes, to_py

try:
    import js  # type: ignore[import-not-found]
    from workers import WorkerEntrypoint  # type: ignore[import-not-found]
except ImportError:
    js = None  # type: ignore[assignment]

    class WorkerEntrypoint:  # type: ignore[no-redef]
        env: object = None


async def response(body: str, *, media_type: str = "text/plain", status: int = 200) -> Any:
    if js is None:
        return {"body": body, "headers": {"Content-Type": media_type}, "status": status}
    return js.Response.new(body, to_js({"status": status, "headers": {"Content-Type": media_type}}))


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Any:
        url = str(getattr(request, "url", ""))
        path = "/" + url.split("/", 3)[3].split("?", 1)[0] if "://" in url and url.count("/") >= 3 else "/"

        if path == "/health":
            return await response("ok")
        if path == "/d1-null":
            return await self._d1_null()
        if path == "/r2":
            return await self._r2()
        if path == "/kv":
            return await self._kv()
        if path == "/compat":
            probes = {"pyodide_runtime": is_pyodide_runtime()}
            return await response(json.dumps(probes), media_type="application/json")
        return await response("not found", status=404)

    async def _d1_null(self) -> Any:
        db = self.env.DATABASE
        key = f"probe-{int(time.time() * 1000)}"
        await db.prepare("INSERT INTO null_probe (id, value) VALUES (?, ?)").bind(key, d1_null()).run()
        row = to_py(await db.prepare("SELECT value FROM null_probe WHERE id = ?").bind(key).first())
        await db.prepare("DELETE FROM null_probe WHERE id = ?").bind(key).run()
        return await response("null-ok" if row and row.get("value") is None else "null-failed")

    async def _r2(self) -> Any:
        bucket = self.env.OBJECTS
        key = f"probe/{int(time.time() * 1000)}.txt"
        await bucket.put(key, to_js_bytes(b"r2-ok"), to_js({"httpMetadata": {"contentType": "text/plain"}}))
        obj = await bucket.get(key)
        text = await obj.text() if not is_js_missing(obj) else "missing"
        await bucket.delete(key)
        return await response(str(text))

    async def _kv(self) -> Any:
        kv = self.env.SESSION_STORE
        key = f"probe-{int(time.time() * 1000)}"
        await kv.put(key, "kv-ok", to_js({"expirationTtl": 60}))
        value = await kv.get(key)
        await kv.delete(key)
        return await response(str(value))
