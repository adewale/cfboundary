# gasket

Gasket is a generic Python toolkit for Cloudflare Python Workers. It focuses on the part that is easy to get wrong: the Python/Pyodide ↔ JavaScript/Workers boundary.

Gasket is intentionally **not** a framework and contains no application-specific binding names, models, routes, auth, feed logic, article logic, theme logic, or deployment topology.

## Install

During pre-1.0 development, pin a git tag or local path from applications:

```toml
"gasket @ git+https://github.com/adewale/gasket@v0.1.0"
```

## Core pattern

```python
from gasket.ffi import SafeEnv

async def fetch(request, env, ctx):
    safe = SafeEnv(env)
    db = safe.d1("DATABASE")
    kv = safe.kv("SESSION_STORE")
    bucket = safe.r2("OBJECTS")

    row = await db.prepare("select ? as value").bind(None).first()
    await kv.put("example", "ok", expiration_ttl=60)
    await bucket.put("example.txt", b"hello")
```

The binding names are yours. Gasket only knows the binding *kind*.

## What gasket wraps

- D1: `SafeD1`, `SafeD1Statement`
- R2: `SafeR2`, `SafeR2Object`, `SafeR2List`
- KV: `SafeKV`
- Queues: `SafeQueue`
- Workers AI: `SafeAI`
- Vectorize: `SafeVectorize`
- Service bindings / Fetcher bindings: `SafeService`, `SafeFetcher`
- Durable Object namespaces: `SafeDurableObjectNamespace`
- Analytics Engine: `SafeAnalyticsEngine`
- Cache API: `SafeCache`
- Static Assets: `SafeAssets`
- Scheduled events: `gasket.adapters.scheduled`
- Responses and R2 streaming: `gasket.adapters.response`, `gasket.adapters.streams`
- Testing and smoke tests: `gasket.testing`
- Checks and deploy readiness: `gasket.checks`, `gasket.deploy`

See [`docs/api-surface-audit.md`](docs/api-surface-audit.md) for the full surface audit.

## Why it exists

Cloudflare Python Workers run on Pyodide. Values crossing the Python/JavaScript boundary need explicit handling:

- Python `None` becomes JS `undefined`, but D1 requires JS `null` for SQL `NULL`.
- Python dicts can become JS Maps unless converted to plain JS Objects.
- JsProxy/null/undefined values can leak into business logic unless converted at the boundary.
- Large binary streams should not round-trip through Python memory.
- Unit tests in CPython can accidentally exercise only fallback paths.

Gasket centralizes these rules.

## Documentation

- [`docs/index.md`](docs/index.md)
- [`docs/api-surface-audit.md`](docs/api-surface-audit.md)
- [`docs/wrapper-audit.md`](docs/wrapper-audit.md)
- [`docs/rationale.md`](docs/rationale.md)

## Examples

- [`examples/basic_worker/README.md`](examples/basic_worker/README.md)
- [`examples/testing/README.md`](examples/testing/README.md)

## CLI

```bash
gasket check .
gasket doctor
gasket deploy .
```

The CLI is intentionally standalone. It is not a Ruff plugin.

## Project status

Pre-1.0. The public surface is intentionally small and generic; new Cloudflare products are added only after a reusable FFI boundary pattern is proven.

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md).
