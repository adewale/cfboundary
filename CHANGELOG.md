# Changelog

All notable changes to gasket are documented here.

## 0.1.0 - 2026-04-25

### Added

- Generic Cloudflare Python Workers FFI boundary helpers.
- Correct Pyodide null handling via `pyodide.ffi.jsnull`; JavaScript `undefined` is treated as Python `None`.
- Binding-name-agnostic `SafeEnv` with wrappers for D1, R2, KV, Queues, Workers AI, Vectorize, service bindings, Durable Objects, Analytics Engine, Cache API, Fetcher/service bindings, and Static Assets.
- Response, stream, and scheduled-event adapters.
- CPython/Pyodide test fakes and smoke-test helpers.
- Static checks for FFI boundary leaks, Pyodide pitfalls, handler consistency, and vendored Python modules.
- Deployment readiness validator and deployment orchestration result types.
- Compatibility probes for blocked `eval`, blocked `Function`, and module importability.
- Cloudflare Workers type stubs copied from the source applications and made generic.

### Changed

- The library surface was made application-agnostic: no Tasche- or Planet-CF-specific binding names, row factories, routes, model helpers, or deployment assumptions belong in gasket.
