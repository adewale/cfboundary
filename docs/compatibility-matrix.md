# Compatibility test matrix

CFBoundary should be tested against both sides of the Cloudflare Python Workers boundary.

| Mode | Purpose | How | In CI? |
|---|---|---|---|
| CPython fallback | Ensures imports and helpers work in normal local tests. | `uv run pytest`. | Yes |
| Pyodide fake | Exercises branches that use `js`, `JsProxy`, `jsnull`, and Pyodide `to_js`. The fakes are identity stubs: they check which calls are made, not what real Pyodide returns. | `cfboundary.testing.patch_pyodide_runtime()`. | Yes |
| Real Pyodide in Node | Runs the unmodified library against the real `JsProxy`, `jsnull`, `to_js`, `Uint8Array` and `ReadableStream`, with no Cloudflare credentials. Pins the semantics in the table below. | `npm ci --prefix tests/pyodide && npm test --prefix tests/pyodide` (Pyodide version pinned in `tests/pyodide/package.json`). | Yes (`real-pyodide` job) |
| Deployed Worker smoke | Catches platform behavior Pyodide-in-Node cannot model (D1, R2, KV bindings). | `CFBOUNDARY_E2E_BASE_URL=... uv run pytest tests/e2e`. | Manual (`e2e.yml`, `workflow_dispatch`) |

The real-Pyodide tier uses the npm `pyodide` package, not the exact build a Worker runs, so it catches semantics that belong to Pyodide itself. Bindings and Workers-only globals still need the deployed smoke.

## Boundary semantics to lock down

| Boundary case | Expected behavior |
|---|---|
| Python `None` sent to D1 bind | Converted to `pyodide.ffi.jsnull` in Pyodide; remains `None` in CPython. |
| JavaScript `null` received from Worker API | Identified by `is_js_null()` and converted to Python `None` by `to_py()`. |
| JavaScript `undefined` received from Worker API | Arrives as Python `None`; `is_js_null(None)` is `False`, `is_js_missing(None)` is `True`. A property that is absent altogether raises `AttributeError` on attribute access, so read optional fields with `getattr(obj, name, None)`. |
| Python dict/list sent to Worker API | Converted through Pyodide `to_js(..., dict_converter=Object.fromEntries, create_pyproxies=False)` into a plain JS `Object` (raw `to_js` would give a `Map`). |
| Python `None` as a dict value sent through `to_js()` | Becomes JS `undefined`, not `null`. The key exists on the object, but `JSON.stringify` drops it: `to_js({"k": None, "j": js_null()})` serialises as `{"j":null}`. Use `js_null()`/`d1_null()` for values that must stay `null`. `None` inside a list also becomes `undefined`, which `JSON.stringify` writes as `null`. |
| Value `to_js()` cannot convert without a PyProxy | Raises `pyodide.ffi.ConversionError` (not a `TypeError`). |
| Bytes sent to binary APIs | Converted through `to_js_bytes()` in Pyodide. |
| ReadableStream consumed in Python | Read with `getReader()` until done. |

Every row above is checked against real Pyodide by `tests/pyodide/real_runtime_checks.py`. For the D1 row that means the `jsnull` conversion; the bind itself needs the deployed smoke.

Application-specific binding wrappers and endpoint smoke assertions should be tested in the application repositories.
