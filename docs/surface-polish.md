# Surface polish backlog

These are the API-polish ideas being implemented with red-green-refactor and property-based tests.

## Implemented in the current pass

1. Prefer public conversion names over underscore-prefixed helpers:
   - `to_py()`
   - `to_js()`
   - `js_null()`
   - `is_js_missing()`
2. Keep old private helpers importable from implementation modules, but remove them from the package star-export surface.
3. Prefer Pythonic method names over JavaScript-style names:
   - `SafeVectorize.delete_by_ids()` is the documented alias; `deleteByIds()` remains compatibility-only.
4. Add Pythonic result aliases for documentation:
   - `R2ListResult` aliases the existing `SafeR2List` implementation.
5. Add property-based tests for conversion idempotence and CPython `to_js()` identity behavior.
6. Add broader wrapper contract tests for D1, R2, KV, Queue, AI, Vectorize, Service, Durable Objects, Analytics Engine, and Cache.

## Remaining polish candidates

1. Split the large `ffi.safe_env` implementation into `ffi.primitives`, `ffi.env`, `bindings.*`, and `http.fetch` modules.
2. Normalize result envelopes for D1 run results, KV list results, Vectorize query results, and HTTP responses.
3. Move `http_fetch()` to `gasket.http.fetch` and make it more `requests`/`httpx` shaped.
4. Rename or alias the `Safe*` classes to cleaner nouns before `v1.0`.
5. Replace the experimental `deploy()` with honest planning APIs such as `plan_deploy()` until command execution is implemented.
6. Drive line and branch coverage to 100% across the package, including checks, CLI, adapters, compatibility probes, deploy planning, and all Pyodide fake branches.
