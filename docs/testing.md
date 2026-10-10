# Testing

CFBoundary uses `uv`, `pytest`, `hypothesis`, `ruff`, and `pytest-cov`.

## Local checks

```bash
uv run ruff check .
uv run pytest
uv run pytest --cov=cfboundary --cov-branch --cov-report=term-missing --cov-fail-under=100
uv run python -m compileall -q cfboundary
uv build
```

## Real Pyodide tests

The fake runtime in `cfboundary.testing` is an identity stub: its `to_js` returns its input, so it cannot show what real Pyodide does at the boundary. `tests/pyodide/` runs the unmodified library inside real Pyodide in Node, with no Cloudflare credentials, and checks the conversions against the real `JsProxy`, `jsnull`, `to_js`, `Uint8Array` and `ReadableStream`:

```bash
npm ci --prefix tests/pyodide
npm test --prefix tests/pyodide
```

Each `check_*` function in `tests/pyodide/real_runtime_checks.py` becomes one `node:test` case. The Pyodide version is pinned in `tests/pyodide/package.json`; bump it deliberately and let these checks tell you what changed. CI runs this tier as steps in the existing `python` job (about 4 s, including `npm ci`); there is no separate job.

## Property-based tests

The conversion boundary is tested with Hypothesis to verify invariants such as:

- `to_py(value) == value` for plain Python (JSON-shaped) values.
- `to_js(value) == value` in CPython fallback mode.
- `d1_null(value) == value` for non-`None` values.

## Live E2E tests

Live tests are skipped by default and run only when a deployed Worker URL is provided:

```bash
CFBOUNDARY_E2E_BASE_URL=https://your-worker.example.workers.dev uv run pytest tests/e2e
```

The live Worker fixture lives in `examples/live_worker/` and verifies CFBoundary against real Cloudflare D1, R2, KV, conversion, and null/missing-value behavior.

A manual GitHub Actions workflow, `.github/workflows/e2e.yml`, runs the same tests against a provided deployed Worker URL.

## Coverage status

Unit/property/contract coverage is enforced at 100% line and branch coverage for the `cfboundary` package. The test doubles in `cfboundary/testing/fakes.py` are excluded from the measurement (`[tool.coverage.run] omit` in `pyproject.toml`), so the number describes the library code only:

```bash
uv run pytest --cov=cfboundary --cov-branch --cov-report=term-missing --cov-fail-under=100
```

The live E2E tests are intentionally skipped unless `CFBOUNDARY_E2E_BASE_URL` is set, so normal local and CI coverage measures the package code without requiring Cloudflare credentials. Real-platform confidence comes from running the E2E workflow against a deployed `examples/live_worker` instance.
