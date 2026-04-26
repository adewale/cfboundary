# cfboundary

[![CI](https://github.com/adewale/cfboundary/actions/workflows/ci.yml/badge.svg)](https://github.com/adewale/cfboundary/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Generic Cloudflare Python Workers boundary helpers extracted from real working Workers projects.

CFBoundary handles the awkward Python/Pyodide ↔ JavaScript/Cloudflare Workers FFI boundary so your application code can work with normal Python values.

## Why cfboundary exists

Cloudflare Python Workers run on Pyodide. That means values crossing between Python and JavaScript need explicit, consistent handling:

- Python `None` becomes JavaScript `undefined`, but D1 needs JavaScript `null` for SQL `NULL`.
- Python dictionaries can become JavaScript `Map`-like values unless converted to plain JavaScript objects.
- `JsProxy` and JavaScript `null` can leak into business logic unless converted at the boundary; JavaScript `undefined` arrives as Python `None`.
- Large binary streams should not round-trip through Python memory.
- CPython tests can accidentally exercise only fallback code and miss production Pyodide branches.

CFBoundary centralizes those rules in a small, generic toolkit.

## Trust model

CFBoundary is trustworthy for its current, deliberately narrow scope: generic Cloudflare Python Workers boundary mechanics. It is not yet a broad Workers framework or a long-lived, battle-hardened ecosystem package.

Why the current scope is credible:

- **Extracted from real Workers**: the first abstractions came from Tasche and Planet CF rather than speculative framework design.
- **Generic by construction**: application binding names, route logic, auth/session behavior, row factories, feeds/articles/themes, and deployment topology stay out of CFBoundary.
- **Tight public API**: preferred names such as `js_null()`, `is_js_missing()`, `to_py()`, `to_js()`, `R2ListResult`, `cfboundary.http.fetch()`, and `plan_deploy()` are tested; removed compatibility names are intentionally not exported.
- **100% package line and branch coverage**: CI enforces `pytest --cov=cfboundary --cov-branch --cov-fail-under=100` without broad package exclusions.
- **Property-based tests**: conversion invariants are tested with Hypothesis across nested Python values.
- **Pyodide-specific semantics are locked down**: JavaScript `null` is `pyodide.ffi.jsnull`; JavaScript `undefined` arrives as Python `None`; D1 binds Python `None` as JS `null`.
- **Real Cloudflare E2E exists**: `examples/live_worker/` is deployable with `pywrangler` and has passed live tests against D1, R2, KV, response creation, and compatibility probes.
- **Consumer suites still pass**: Tasche and Planet CF keep their app-local wrapper APIs during migration, and their existing test suites pass unchanged.

Remaining limits:

- Tasche and Planet CF have not fully delegated their wrapper internals to CFBoundary yet, so migration should stay incremental behind each app's existing `wrappers.py` API.
- Live E2E currently covers D1/R2/KV/responses/compat probes, not every Cloudflare binding such as Queues, AI, Vectorize, Durable Objects, Analytics Engine, or Cache.
- Cloudflare Python Workers tooling changes quickly; keep running live E2E after changes to `pywrangler`, `workers-py`, compatibility flags, or packaging.
- 100% coverage proves all current local code paths are exercised; it does not replace staging/prod smoke tests for real app behavior.

## Provenance

CFBoundary is not speculative framework code. Its first abstractions were extracted from two real Cloudflare Python Workers applications:

- **Tasche** contributed the core FFI boundary patterns:
  - Safe D1/R2/KV/Queue/AI wrappers;
  - D1 `None` → `pyodide.ffi.jsnull` handling;
  - safe JavaScript → Python conversion;
  - bytes → JavaScript typed-array conversion;
  - ReadableStream consumption;
  - R2 JavaScript-side streaming patterns;
  - CPython fakes for testing Pyodide branches.
- **Planet CF** contributed production deployment and compatibility patterns:
  - Vectorize boundary handling;
  - vendored Python module checks;
  - deploy-readiness validation ideas;
  - deployed-worker smoke verification patterns;
  - Pyodide compatibility probes;
  - Cloudflare Workers type stubs.

The library surface is deliberately generic. Application binding names, row factories, route handlers, auth/session strategies, feed/article/theme logic, and deployment topology stay in applications.

## Install

CFBoundary is pre-1.0. During early development, pin a tag or local path from applications:

```toml
# pyproject.toml
[project]
dependencies = [
    "cfboundary @ git+https://github.com/adewale/cfboundary@v0.1.0",
]
```

For local development in a sibling checkout:

```bash
uv pip install -e ../cfboundary
```

For cfboundary development:

```bash
uv sync --group dev
uv run pytest
CFBOUNDARY_E2E_BASE_URL=https://your-worker.example.workers.dev uv run pytest tests/e2e
```

## Quick start

Wrap the raw Workers `env` once, then access bindings by kind and by your binding name.

```python
from cfboundary.ffi import SafeEnv
from cfboundary.adapters.response import full_response


async def fetch(request, env, ctx):
    safe = SafeEnv(env)

    db = safe.d1("DATABASE")
    kv = safe.kv("SESSION_STORE")
    bucket = safe.r2("OBJECTS")

    row = await db.prepare("select ? as value").bind(None).first()
    await kv.put("last_value", "ok", expiration_ttl=60)
    await bucket.put("hello.txt", b"hello from cfboundary")

    return await full_response("ok", media_type="text/plain")
```

The binding names are yours. CFBoundary only knows the binding **kind**.

## What cfboundary provides

### FFI and binding wrappers

- D1: `SafeD1`, `SafeD1Statement`
- R2: `SafeR2`, `SafeR2Object`, `R2ListResult`
- KV: `SafeKV`
- Queues: `SafeQueue`
- Workers AI: `SafeAI`
- Vectorize: `SafeVectorize`
- Service bindings / Fetcher bindings: `SafeService`, `SafeFetcher`
- Durable Object namespaces: `SafeDurableObjectNamespace`
- Analytics Engine: `SafeAnalyticsEngine`
- Cache API: `SafeCache`
- Static Assets: `SafeAssets`

### Worker adapters

- `cfboundary.adapters.response.full_response()` for fully-buffered JavaScript `Response` objects.
- `cfboundary.adapters.streams.serve_r2_object_via_js()` for keeping large R2 payloads on the JavaScript side.
- `cfboundary.adapters.scheduled.ScheduledHandler` for cron-triggered Workers.

### Testing, checks, and deploy helpers

- `cfboundary.testing.fakes` for exercising Pyodide branches from CPython.
- `cfboundary.testing.smoke.SmokeBase` for deployed-worker smoke checks.
- `cfboundary.checks` for FFI-boundary, Pyodide-pitfall, handler, and vendor checks.
- `cfboundary.deploy.validate_ready()` and `cfboundary.deploy.plan_deploy()` for generic deploy-readiness planning.
- `cfboundary.http.fetch()` for Workers/CPython HTTP fetch normalization.
- `cfboundary.compat.probes` for runtime compatibility probes.

See [`docs/api-surface-audit.md`](docs/api-surface-audit.md) for the full Cloudflare Developer Platform surface audit.

## Example: application-local binding names

Keep project-specific names in your app, not in cfboundary:

```python
from cfboundary.ffi import SafeEnv


class AppEnv(SafeEnv):
    @property
    def database(self):
        return self.d1("DATABASE")

    @property
    def object_store(self):
        return self.r2("OBJECTS")
```

## CLI

```bash
uv run cfboundary check .
uv run cfboundary doctor
uv run cfboundary plan-deploy .
```

The CLI is standalone. It is not a Ruff plugin.

## Documentation

- [`docs/index.md`](docs/index.md)
- [`docs/rationale.md`](docs/rationale.md)
- [`docs/api-surface-audit.md`](docs/api-surface-audit.md)
- [`docs/testing.md`](docs/testing.md)
- [`docs/compatibility-matrix.md`](docs/compatibility-matrix.md)
- [`docs/application-adapters.md`](docs/application-adapters.md)
- [`docs/before-after.md`](docs/before-after.md)
- [`docs/surface-polish.md`](docs/surface-polish.md)
- [`docs/wrapper-audit.md`](docs/wrapper-audit.md)
- [`docs/deep-audit-2026-04-25.md`](docs/deep-audit-2026-04-25.md)
- [`docs/pre-release-checklist.md`](docs/pre-release-checklist.md)
- [`docs/pre-release-execution-2026-04-25.md`](docs/pre-release-execution-2026-04-25.md)
- [`docs/migrating-from-local-wrappers.md`](docs/migrating-from-local-wrappers.md)
- [`docs/migrating-from-product-specific-wrappers.md`](docs/migrating-from-product-specific-wrappers.md)

## Examples

- [`examples/basic_worker/README.md`](examples/basic_worker/README.md)
- [`examples/live_worker/README.md`](examples/live_worker/README.md)
- [`examples/testing/README.md`](examples/testing/README.md)

## Project status

Pre-1.0. Breaking changes are allowed before the public API settles. New Cloudflare products are added only after a reusable FFI boundary pattern is proven in real code.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The most important rule: cfboundary must stay generic.

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md).

## License

MIT. See [`LICENSE`](LICENSE).
