# Cloudflare Developer Platform Surface Audit

Gasket's scope is the Python/JavaScript FFI boundary for Cloudflare Python Workers. It does not replace Wrangler, framework routing, auth, app models, or product-specific provisioning.

## Covered directly

| Cloudflare surface | Gasket abstraction | Notes |
|---|---|---|
| Environment vars/secrets | `SafeEnv.var()`, `SafeEnv.secret()` | Converts null/undefined and enforces required secrets. |
| D1 | `SafeD1`, `SafeD1Statement` | Covers `prepare`, `bind`, `first`, `all`, `run`, `exec`, `batch`; converts `None` to JS `null`. |
| R2 | `SafeR2`, `SafeR2Object`, `R2ListResult` | Covers `get`, `put`, `delete`, `list`, bytes/text/stream access. |
| KV | `SafeKV` | Covers `get`, `put`, `delete`, `list`. |
| Queues producers | `SafeQueue` | Covers `send`, `send_batch`. Consumer dispatch remains framework/application code. |
| Workers AI | `SafeAI` | Covers `run` with input conversion. |
| Vectorize | `SafeVectorize` | Covers `query`, `insert`, `upsert`, `delete`, and `delete_by_ids`. |
| Service bindings / Fetcher | `SafeService`, `SafeFetcher` | Covers `fetch` and generic RPC method conversion. |
| Durable Objects namespace | `SafeDurableObjectNamespace` | Covers ID creation and stub retrieval. Stub methods use `SafeService`. |
| Analytics Engine | `SafeAnalyticsEngine` | Covers `writeDataPoint`. |
| Cache API | `SafeCache` | Covers `match`, `put`, `delete`. |
| Static Assets binding | `SafeAssets` | Covers `fetch`. |
| Scheduled events | `gasket.adapters.scheduled` | Normalizes scheduled event metadata and wraps env. |
| Responses | `gasket.adapters.response.full_response` | Avoids ASGI StreamingResponse truncation for fully-buffered responses. |
| Large R2 streaming | `gasket.adapters.streams.serve_r2_object_via_js` | Keeps large payloads on the JS side. |
| HTTP fetch | `gasket.http.fetch`, `FetchResponse` | Normalizes Workers `fetch` and CPython `httpx` for tests/tools. |
| Runtime probes | `gasket.compat.probes` | Detects Pyodide/Workers restrictions. |
| Local testing | `gasket.testing.fakes`, `gasket.testing.smoke` | Tests production branches from CPython and validates deployed workers. |

## Intentionally not abstracted

- Routing/framework APIs (`fetch`, FastAPI, itty-router style dispatch): app-specific.
- Authentication/session strategy: app-specific.
- Wrangler project generation, multi-instance provisioning, and DNS: app/product-specific.
- D1 schema management policy: gasket validates readiness but does not decide migration ordering for an app.
- Browser Rendering, Workflows, Hyperdrive, Images, Turnstile, Email Routing, Pub/Sub, and Calls: these either do not have stable Python Workers bindings in the source projects or require product-specific semantics. Gasket can add wrappers once a source app proves a reusable boundary pattern.

## Missing abstractions identified and added in this pass

- Generic `SafeService` RPC wrapper instead of app-specific service wrappers.
- Generic `SafeFetcher` alias for service/fetch bindings.
- Generic Durable Object namespace wrapper.
- Generic Analytics Engine writer.
- Generic Cache API wrapper.
- Generic Static Assets wrapper.
- Binding-name-agnostic `SafeEnv`; app-specific binding names now live in application shims, not gasket.

## Remaining follow-up candidates

- Queue consumer message wrappers once both source apps converge on a shared consumer pattern.
- Durable Object state/storage wrappers if a source app uses Python Durable Objects directly.
- Typed wrappers for Hyperdrive and Workflows after production usage proves the boundary requirements.
- A `wrangler.toml/jsonc` parser that preserves comments and validates all binding kinds, not just generic JSONC parseability.
