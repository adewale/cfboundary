# Changelog

All notable changes to gasket are documented here.

## 0.1.0 - 2026-04-25

### Added

- Generic Cloudflare Python Workers FFI boundary helpers.
- 100% line and branch coverage enforcement for the `gasket` package.
- Deployable live Worker fixture for real Cloudflare D1/R2/KV/response/compat E2E verification.
- Manual GitHub Actions live E2E workflow for running tests against a deployed Worker URL.
- Dedicated `gasket.http.fetch()` API with `FetchResponse` and `FetchError`.
- Pre-release checklist, code of conduct, and GitHub issue/PR templates.
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
- Removed backwards-compatibility names from the public `gasket.ffi` export surface in favor of `js_null`, `is_js_missing`, `to_py`, `to_js`, `R2ListResult`, `gasket.http.fetch`, and `plan_deploy`.
- `full_response()` now accepts an explicit `status` argument.
- `SafeQueue.send()` now forwards its `content_type` argument to Cloudflare Queue options.
- `validate_ready(required_secrets=...)` now emits `GSK103` warnings instead of silently ignoring required secret checks.
