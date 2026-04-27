# Changelog

All notable changes to cfboundary are documented here.

## 0.1.8 - 2026-04-26

### Changed

- Removed feed-specific smoke assertions from generic testing helpers.
- Replaced the scheduled-handler subclass scaffold with a small scheduled-event normalization helper.
- Changed check codes from `GSK*` to `CFB*`.
- Deprecated the generic handler-consistency check as an app-policy no-op.

## 0.1.7 - 2026-04-26

### Changed

- Moved runtime override use to `cfboundary.testing.patch_pyodide_runtime()`.
- Removed `HAS_PYODIDE` and `configure_runtime()` from the public `cfboundary.ffi` export surface.
- Replaced internal snapshot `HAS_PYODIDE` imports with live runtime checks.

## 0.1.6 - 2026-04-26

### Added

- Added `is_pyodide_runtime()` as a live runtime-state helper for consumers and tests.

## 0.1.5 - 2026-04-26

### Changed

- Tightened optional runtime imports to catch only missing optional top-level modules, avoiding accidental masking of broken transitive imports.

## 0.1.4 - 2026-04-26

### Added

- Added `cfboundary.ffi.configure_runtime()` so app compatibility layers and tests can inject Pyodide/fake runtime globals before delegating to CFBoundary.

### Changed

- Improved fake-runtime null/undefined detection for app migration tests.
- Supported legacy Pyodide fake `to_js()` adapters that do not accept `create_pyproxies`.

## 0.1.0 - 2026-04-25

### Added

- Generic Cloudflare Python Workers FFI boundary helpers.
- 100% line and branch coverage enforcement for the `cfboundary` package.
- Deployable live Worker fixture for real Cloudflare D1/R2/KV/response/compat E2E verification.
- Manual GitHub Actions live E2E workflow for running tests against a deployed Worker URL.
- Dedicated `cfboundary.http.fetch()` API with `FetchResponse` and `FetchError`.
- Pre-release checklist, code of conduct, and GitHub issue/PR templates.
- Correct Pyodide null handling via `pyodide.ffi.jsnull`; JavaScript `undefined` is treated as Python `None`.
- Binding-name-agnostic `SafeEnv` with wrappers for D1, R2, KV, Queues, Workers AI, Vectorize, service bindings, Durable Objects, Analytics Engine, Cache API, Fetcher/service bindings, and Static Assets.
- Response, stream, and scheduled-event adapters.
- CPython/Pyodide test fakes and smoke-test helpers.
- Static checks for FFI boundary leaks, Pyodide pitfalls, and vendored Python modules.
- Deployment readiness validator and deployment orchestration result types.
- Compatibility probes for blocked `eval`, blocked `Function`, and module importability.
- Cloudflare Workers type stubs copied from the source applications and made generic.

### Changed

- The library surface was made application-agnostic: no Tasche- or Planet-CF-specific binding names, row factories, routes, model helpers, or deployment assumptions belong in cfboundary.
- Removed backwards-compatibility names from the public `cfboundary.ffi` export surface in favor of `js_null`, `is_js_missing`, `to_py`, `to_js`, `R2ListResult`, `cfboundary.http.fetch`, and `plan_deploy`.
- `full_response()` now accepts an explicit `status` argument.
- `SafeQueue.send()` now forwards its `content_type` argument to Cloudflare Queue options.
- `validate_ready(required_secrets=...)` now emits `CFB103` warnings instead of silently ignoring required secret checks.
