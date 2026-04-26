# Surface polish backlog

These are the API-polish ideas being implemented with red-green-refactor and property-based tests.

## Implemented in the current pass

1. Prefer public conversion names over underscore-prefixed helpers:
   - `to_py()`
   - `to_js()`
   - `js_null()`
   - `is_js_missing()`
2. Remove backwards-compatibility names from the public package surface; underscore-prefixed helpers remain implementation details only.
3. Prefer Pythonic method names over JavaScript-style names:
   - `SafeVectorize.delete_by_ids()` is the public method; JavaScript-style `deleteByIds()` is not exposed on CFBoundary wrappers.
4. Use Pythonic result object names:
   - `R2ListResult` is the public result type returned by `SafeR2.list()`.
5. Add property-based tests for conversion idempotence and CPython `to_js()` identity behavior.
6. Add broader wrapper contract tests for D1, R2, KV, Queue, AI, Vectorize, Service, Durable Objects, Analytics Engine, and Cache.

## Remaining polish candidates

1. Finish splitting the large `ffi.safe_env` implementation into `ffi.primitives`, `ffi.env`, and `bindings.*` modules. HTTP fetch has moved to `cfboundary.http`.
2. Normalize result envelopes for D1 run results, KV list results, Vectorize query results, and HTTP responses.
3. Continue improving `cfboundary.http.fetch` to mirror the useful parts of `requests`/`httpx` without becoming a full HTTP client.
4. Rename or alias the `Safe*` classes to cleaner nouns before `v1.0`.
5. Continue expanding honest planning APIs such as `plan_deploy()` instead of adding mutation-heavy deploy commands before the behavior is proven.
6. Drive line and branch coverage to 100% across the package, including checks, CLI, adapters, compatibility probes, deploy planning, and all Pyodide fake branches.
