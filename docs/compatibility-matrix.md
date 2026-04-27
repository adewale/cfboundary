# Compatibility test matrix

CFBoundary should be tested against both sides of the Cloudflare Python Workers boundary.

| Mode | Purpose | How |
|---|---|---|
| CPython fallback | Ensures imports and helpers work in normal local tests. | `uv run pytest`. |
| Pyodide fake | Exercises branches that use `js`, `JsProxy`, `jsnull`, and Pyodide `to_js`. | `cfboundary.testing.patch_pyodide_runtime()`. |
| Deployed Worker smoke | Catches platform behavior mocks cannot model. | `CFBOUNDARY_E2E_BASE_URL=... uv run pytest tests/e2e`. |

## Boundary semantics to lock down

| Boundary case | Expected behavior |
|---|---|
| Python `None` sent to D1 bind | Converted to `pyodide.ffi.jsnull` in Pyodide; remains `None` in CPython. |
| JavaScript `null` received from Worker API | Identified by `is_js_null()` and converted to Python `None` by `to_py()`. |
| JavaScript `undefined` received from Worker API | Arrives as Python `None`; `is_js_null(None)` is `False`, `is_js_missing(None)` is `True`. |
| Python dict/list sent to Worker API | Converted through Pyodide `to_js(..., dict_converter=Object.fromEntries, create_pyproxies=False)`. |
| Bytes sent to binary APIs | Converted through `to_js_bytes()` in Pyodide. |
| ReadableStream consumed in Python | Read with `getReader()` until done. |

Application-specific binding wrappers and endpoint smoke assertions should be tested in the application repositories.
