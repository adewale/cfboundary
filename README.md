# CFBoundary

CFBoundary is a small Cloudflare Python Workers FFI helper library. It now keeps only the APIs that are used by the downstream `tasche` and `planet_cf` migrations, plus the shared CPython testing hook.

## Install

```bash
uv add 'cfboundary @ git+https://github.com/adewale/cfboundary@v0.1.11'
```

## Public API

### `cfboundary.ffi`

```python
from cfboundary.ffi import (
    JsException,
    MAX_CONVERSION_DEPTH,
    consume_readable_stream,
    d1_null,
    get_r2_size,
    is_js_missing,
    is_js_null,
    is_pyodide_runtime,
    js_null,
    stream_r2_body,
    to_js,
    to_js_bytes,
    to_py,
    to_py_bytes,
)
```

These helpers cover the generic Pyodide/JavaScript boundary only:

- JavaScript `null` as `pyodide.ffi.jsnull` and JavaScript `undefined` as Python `None`;
- Python ↔ JavaScript value conversion;
- D1 `None` → JS `null` bind values;
- byte and stream conversion helpers used by R2-style bodies;
- runtime detection.

### `cfboundary.testing`

```python
from cfboundary.testing import FakeJsModule, FakeJsProxy, JsNull, patch_pyodide_runtime
```

Use `patch_pyodide_runtime()` in CPython tests to exercise Pyodide branches without exposing mutable runtime configuration as a production API.

## What is intentionally not here anymore

The following were removed because neither downstream app consumed them directly and the apps need app-specific semantics instead:

- `SafeEnv` and all `Safe*` binding wrappers;
- `cfboundary.http`;
- `cfboundary.adapters`;
- `cfboundary.checks` and the `cfboundary` CLI;
- `cfboundary.deploy`;
- `cfboundary.compat`;
- `cfboundary.testing.smoke`.

App projects should keep boundary classes, deployment checks, smoke tests, row factories, cache/session/feed/search behavior, and binding-name policy in their own code.

## Validation

Current package tests run with 100% line/branch coverage:

```bash
uv run ruff check .
uv run pytest --cov=cfboundary --cov-branch --cov-report=term-missing --cov-fail-under=100 -q
uv build
```
