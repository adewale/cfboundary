"""Deployable Worker used by Gasket live E2E tests.

Before deploying, install gasket into this Worker project or copy the package into
its module search path. The endpoints intentionally exercise real Cloudflare
bindings instead of mocks.
"""

from __future__ import annotations

import time
from typing import Any

from gasket.adapters.response import full_response
from gasket.compat import run_all_probes
from gasket.ffi import SafeEnv

try:
    from workers import WorkerEntrypoint  # type: ignore[import-not-found]
except ImportError:

    class WorkerEntrypoint:  # type: ignore[no-redef]
        env: object = None


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Any:
        url = str(getattr(request, "url", ""))
        path = "/" + url.split("/", 3)[3].split("?", 1)[0] if "://" in url and url.count("/") >= 3 else "/"
        env = SafeEnv(self.env)

        if path == "/health":
            return await full_response("ok", media_type="text/plain")
        if path == "/d1-null":
            return await self._d1_null(env)
        if path == "/r2":
            return await self._r2(env)
        if path == "/kv":
            return await self._kv(env)
        if path == "/compat":
            import json

            return await full_response(json.dumps(await run_all_probes()), media_type="application/json")
        return await full_response("not found", media_type="text/plain", status=404)

    async def _d1_null(self, env: SafeEnv) -> Any:
        db = env.d1("DATABASE")
        key = f"probe-{int(time.time() * 1000)}"
        await db.prepare("INSERT INTO null_probe (id, value) VALUES (?, ?)").bind(key, None).run()
        row = await db.prepare("SELECT value FROM null_probe WHERE id = ?").bind(key).first()
        await db.prepare("DELETE FROM null_probe WHERE id = ?").bind(key).run()
        return await full_response("null-ok" if row and row.get("value") is None else "null-failed", media_type="text/plain")

    async def _r2(self, env: SafeEnv) -> Any:
        bucket = env.r2("OBJECTS")
        key = f"probe/{int(time.time() * 1000)}.txt"
        await bucket.put(key, b"r2-ok", http_metadata={"contentType": "text/plain"})
        obj = await bucket.get(key)
        text = await obj.text() if obj else "missing"
        await bucket.delete(key)
        return await full_response(text, media_type="text/plain")

    async def _kv(self, env: SafeEnv) -> Any:
        kv = env.kv("SESSION_STORE")
        key = f"probe-{int(time.time() * 1000)}"
        await kv.put(key, "kv-ok", expiration_ttl=60)
        value = await kv.get(key)
        await kv.delete(key)
        return await full_response(str(value), media_type="text/plain")
