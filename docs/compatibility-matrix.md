# Compatibility test matrix

Gasket should be tested against both sides of the Cloudflare Python Workers boundary.

## Runtime modes

| Mode | Purpose | How |
|---|---|---|
| CPython fallback | Ensures gasket and applications import and run in normal local tests. | `uv run pytest` without Pyodide modules. |
| Pyodide fake | Exercises the production branches that use `js`, `pyodide.ffi.JsProxy`, `pyodide.ffi.jsnull`, and `to_js`. | `gasket.testing.fakes.patch_pyodide_runtime()`. |
| Deployed Worker smoke | Catches platform behavior that mocks cannot model. | Application-specific smoke tests composed with `gasket.testing.smoke.SmokeBase`. |

## Boundary semantics to lock down

| Boundary case | Expected behavior |
|---|---|
| Python `None` sent to D1 bind | Converted to `pyodide.ffi.jsnull` in Pyodide; remains `None` in CPython fakes. |
| JavaScript `null` received from Worker API | Identified by `is_js_null()` and converted to Python `None` by `to_py`. |
| JavaScript `undefined` received from Worker API | Arrives as Python `None`; `is_js_null(None)` is `False`, `is_js_null_or_undefined(None)` is `True`. |
| Python dict/list sent to Worker API | Converted through `to_js(..., dict_converter=Object.fromEntries, create_pyproxies=False)` in Pyodide. |
| Bytes sent to binary APIs | Converted through `to_js_bytes()` in Pyodide. |
| ReadableStream consumed in Python | Read with `getReader()` until done, not a single `arrayBuffer()` read for streams. |

## Binding wrappers under test

Every binding wrapper should have CPython and Pyodide-fake coverage for its conversion contract:

- D1: `prepare`, `bind`, `first`, `all`, `run`, `exec`, `batch`.
- R2: `get`, `put`, `delete`, `list`, object `bytes`, `text`, `stream`.
- KV: `get`, `put`, `delete`, `list`.
- Queue: `send`, `send_batch`.
- AI: `run`.
- Vectorize: `query`, `insert`, `upsert`, `delete`.
- Service bindings: `fetch` and RPC-style methods.
- Durable Object namespace: ID creation and stub retrieval.
- Analytics Engine: `write_data_point`.
- Cache: `match`, `put`, `delete`.
- Static Assets: `fetch`.

## Application migration matrix

Applications should run their existing test suites in addition to gasket's suite:

| Application state | Required check |
|---|---|
| Existing local wrapper retained | Full app tests must pass unchanged. |
| Generic helper delegated to gasket | Existing app tests plus gasket tests pass. |
| Call site migrated to direct gasket import | App tests pass and no app-specific names were added to gasket. |
| Deployment scripts composed with gasket | Dry-run/validation tests pass before live deploy. |

This matrix is intentionally stricter than unit tests alone because CPython-only tests can miss Pyodide production branch bugs.
