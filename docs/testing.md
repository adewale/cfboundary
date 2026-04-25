# Testing

Gasket uses `uv`, `pytest`, `hypothesis`, `ruff`, and `pytest-cov`.

## Local checks

```bash
uv run ruff check .
uv run pytest
uv run pytest --cov=gasket --cov-branch --cov-report=term-missing
uv run python -m compileall -q gasket
```

## Property-based tests

The conversion boundary is tested with Hypothesis to verify invariants such as:

- `to_py(to_py(value)) == to_py(value)` for Python values.
- `to_js(value) == value` in CPython fallback mode.
- `d1_null(value) == value` for non-`None` values.

## Live E2E tests

Live tests are skipped by default and run only when a deployed Worker URL is provided:

```bash
GASKET_E2E_BASE_URL=https://your-worker.example.workers.dev uv run pytest tests/e2e
```

The live Worker must implement the fixture documented in `examples/live_worker/README.md`.

## Coverage status

Current coverage is measured honestly and is not configured to exclude broad parts of the package. The latest local run reports 76% line/branch coverage. The path to 100% is:

1. Add Pyodide-fake tests for JS `Response` creation and R2 JS-side streaming.
2. Add direct tests for every branch in `gasket.checks`.
3. Add CLI tests for `check`, `plan-deploy`, invalid commands, and `__main__` execution.
4. Add deploy validator tests for valid JSONC, invalid JSONC, migration directories, and vendor propagation.
5. Add HTTP Pyodide-branch tests by faking `js.fetch`.
6. Add tests for `gasket.ffi.primitives` re-exports.
7. Add stream tests for `getReader()` success, `arrayBuffer()` fallback, and reader release on exceptions.
8. Add branch tests for service, cache, assets, env optional/missing bindings, and CPython/Pyodide import branches.

Once these are in place, CI should enforce:

```bash
uv run pytest --cov=gasket --cov-branch --cov-fail-under=100
```
