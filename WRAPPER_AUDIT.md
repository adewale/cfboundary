# Migration Spec and Wrapper Approach Audit

## Spec audit

The original `gasket.md` correctly identified the highest-value reusable pieces: FFI conversion, Safe* wrappers, response/streaming adapters, deployment readiness, smoke checks, and Pyodide probes. The most important correction is scope discipline: gasket must stay generic. Source applications may inspire APIs, but application binding names, row factories, routes, feed validators, article/audio concepts, theme checks, and multi-instance assumptions must remain outside the library.

## Improvements made to the extraction approach

- Replaced binding-name-specific `SafeEnv` attributes with binding-name-agnostic methods: `d1(name)`, `r2(name)`, `kv(name)`, `queue(name)`, `ai(name)`, `vectorize(name)`, `service(name)`, `durable_object(name)`, `analytics_engine(name)`, `fetcher(name)`, and `assets(name)`.
- Removed the extracted Planet-CF compatibility module from gasket. Planet-specific row factories and feed helpers belong in Planet CF.
- Removed Tasche-specific service wrapper naming from gasket. A generic `SafeService` now handles fetch and RPC-style service methods.
- Added a Cloudflare API surface audit documenting what is covered, what is intentionally out of scope, and what should wait for proven production usage.
- Added examples, changelog, and migration documentation.

## Audit of original wrappers.py pattern

### Strengths to preserve

1. **Single boundary module.** Both applications benefited from concentrating Pyodide weirdness in one place.
2. **Conversion in both directions.** The wrappers correctly treat FFI as a write problem and a read problem.
3. **D1 null handling.** Python `None` must become JS `null`, not JS `undefined`, for D1 binds.
4. **Dict conversion to plain JS objects.** `to_js(..., dict_converter=Object.fromEntries)` avoids Map/LiteralMap surprises.
5. **CPython fallback.** Import guards make business logic importable in tests.
6. **ReadableStream caution.** Reading with `getReader()` avoids truncated multi-chunk streams.
7. **Safe* construction.** Wrapping bindings early prevents business logic from seeing raw JsProxy values.

### Problems found

1. **Application-specific names leaked into the shared layer.** `DB`, `CONTENT`, `ARTICLE_QUEUE`, `READABILITY`, `SEARCH_INDEX`, etc. are app choices, not library concepts.
2. **Application-specific helpers were mixed with generic boundary helpers.** Planet row factories and feed bind helpers are model-layer code.
3. **Some wrappers returned raw JS objects where conversion was expected.** For example, AI/R2/service APIs need a deliberate choice between raw passthrough and Python conversion.
4. **Wrapper return shapes diverged.** One project's `SafeD1Statement.all()` returned a list; another returned a D1-like object with `.results`. Gasket should document one generic shape and applications can adapt if needed.
5. **Observability hooks were embedded in wrappers.** Metrics are valuable, but app-specific event systems should be injected or layered outside generic wrappers.
6. **Tests encouraged private-name coupling.** `_to_py_safe` and `_to_js_value` are useful compatibility exports, but public aliases should be preferred for new code.
7. **Deploy checks were product-specific.** Theme/template/example checks are Planet CF checks, not gasket checks. Gasket should provide primitives and generic validations.

### Recommended migration style

1. Keep app-specific compatibility shims in each app.
2. Move generic imports to `gasket.ffi` incrementally.
3. Move app-specific row factories and binding-name adapters to app modules.
4. Replace direct JS API use with gasket wrappers where the boundary is generic.
5. Add project-specific deployment validators by composing `gasket.deploy.validate_ready` with local checks.
6. Only add new gasket abstractions after a real app proves the boundary pattern.

## Missing abstractions now covered

- Durable Object namespace and stub access.
- Analytics Engine writes.
- Cache API access.
- Static Assets fetch.
- Generic service/RPC binding wrapper.
- Generic Fetcher wrapper.

## Still intentionally missing

- App-specific schema migration policy.
- Product-specific route/request/response framework wrappers.
- Typed wrappers for Cloudflare products not yet used by these applications.
- Multi-instance provisioning.
