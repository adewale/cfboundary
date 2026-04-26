# Deep audit: CFBoundary library and application impact

Date: 2026-04-25

Scope: the `cfboundary` package, examples, tests, documentation, and migration impact on the two current consumers: `tasche` and `planet_cf`.

Method: used the `adewale/audit-skill` audit skill and applied its deep-dive categories across code quality, docs-code sync, language best practices, resource management, test quality, feature completeness, security, and consumer integration impact.

## Executive summary

Verdict: **Minor findings only** after the fixes made during this audit.

CFBoundary is credible for its current narrow purpose: generic Cloudflare Python Workers FFI and binding-boundary mechanics. The strongest evidence is the combination of real provenance from Tasche/Planet CF, 100% package line/branch coverage, property-based conversion tests, fake-Pyodide branch tests, a real deployable Cloudflare Worker fixture, and successful live E2E tests against Cloudflare D1/R2/KV.

The remaining risks are adoption risks rather than evidence of a broken library: Tasche and Planet CF have not yet fully delegated their `wrappers.py` internals to CFBoundary, and live E2E does not yet cover every Cloudflare binding class.

## Validation performed

```text
cd cfboundary && uv run ruff check .
cd cfboundary && uv run pytest --cov=cfboundary --cov-branch --cov-report=term-missing --cov-fail-under=100 -q
cd cfboundary && CFBOUNDARY_E2E_BASE_URL=https://cfboundary-live-worker.<subdomain>.workers.dev uv run pytest tests/e2e -q
cd cfboundary && uvx vulture cfboundary tests --min-confidence 80
cd tasche && uv run --group test pytest -q
cd planet_cf && uv run --all-extras pytest -q
```

Results:

```text
cfboundary ruff: pass
cfboundary package coverage: 100% line, 100% branch; 70 passed, 5 skipped
cfboundary live E2E: 5 passed against deployed Cloudflare Worker
cfboundary vulture: no production findings after fixes
tasche: 1243 passed, 35 skipped, 2 warnings
planet_cf: 1426 passed, 107 skipped, 1 RuntimeWarning
```

The Planet CF warning is the known un-awaited `AsyncMock` warning. Its reported location has moved between full-suite runs, which supports the diagnosis that another test creates an un-awaited `AsyncMock` coroutine that is later garbage-collected during unrelated code.

## Findings fixed during this audit

### 1. `full_response()` could not set an HTTP status

Severity: Medium

Before this audit, `cfboundary.adapters.response.full_response()` always returned status 200 in CPython and constructed JS `Response` options with headers only. The live Worker attempted a 404 via a `Status` header, which is not how the Workers `Response` API sets status.

Fix:

- Added `status: int = 200` to `full_response()`.
- Passed `status` through to `js.Response.new(..., {headers, status})`.
- Updated the live Worker fallback route to call `full_response(..., status=404)`.
- Added/updated tests while preserving 100% coverage.

Files:

- `cfboundary/adapters/response.py`
- `examples/live_worker/src/entry.py`
- `tests/test_adapters_checks_cli.py`

### 2. `SafeQueue.send()` accepted but ignored `content_type`

Severity: Medium

`SafeQueue.send()` exposed a `content_type` parameter but never included it in the Queue send options. This meant callers could believe they were changing queue serialization while the option was silently dropped.

Fix:

- `SafeQueue.send()` now sends `{"contentType": content_type, **kwargs}` as the options object.
- Tests assert the options object is passed.

Files:

- `cfboundary/ffi/safe_env.py`
- `tests/test_bindings.py`
- `tests/test_safe_env_edges.py`

### 3. `validate_ready(required_secrets=...)` accepted but ignored secret requirements

Severity: Low/Medium

`validate_ready()` accepted `required_secrets` but did nothing with it. CFBoundary cannot generically prove remote Worker secrets exist without Cloudflare API/application-specific checks, but silently ignoring the argument was misleading.

Fix:

- `validate_ready()` now emits `GSK103` warnings for required secrets, explicitly telling callers to verify those in application-specific deploy checks.
- Tests cover this behavior.

Files:

- `cfboundary/deploy/validator.py`
- `tests/test_coverage_edges.py`

### 4. Test artifact with impossible branch

Severity: Low

Vulture found an intentionally unreachable ternary in a coverage-edge test. It did not affect production code, but it made audit output noisy.

Fix:

- Replaced it with a straightforward SafeEnv wrapping assertion.

File:

- `tests/test_more_coverage.py`

## Code quality audit

### Strengths

- The public package is small and focused.
- App-specific concepts are absent from CFBoundary internals.
- The preferred public names are tested through export-surface tests.
- The live Worker caught real deployment/tooling issues that CPython tests could not catch.

### Remaining concerns

#### `safe_env.py` is still a consolidation hotspot

Severity: Low

`cfboundary/ffi/safe_env.py` contains primitives, conversion helpers, D1, R2, KV, Queues, AI, Vectorize, services, Durable Objects, Analytics Engine, Cache, Assets, and Env wrappers in one module. It is well tested, but it is now the main maintenance risk because unrelated binding changes touch the same file.

Recommendation:

Split gradually without changing public exports:

- `cfboundary/ffi/primitives.py`
- `cfboundary/ffi/conversion.py`
- `cfboundary/bindings/d1.py`
- `cfboundary/bindings/r2.py`
- `cfboundary/bindings/kv.py`
- `cfboundary/bindings/queues.py`
- `cfboundary/bindings/vectorize.py`
- keep `cfboundary.ffi.__all__` as the compatibility export surface.

#### Some wrapper methods return `None` for missing required bindings

Severity: Low

`SafeEnv.d1("DATABASE")` returns `SafeD1 | None`, but examples often use the result immediately. This is Pythonic for optional access, but apps may want a fail-fast helper for required bindings.

Recommendation:

Consider adding generic required helpers later, e.g. `env.require_d1("DATABASE")`, only if both apps independently need it.

## Documentation and docs-code sync audit

### Fixed/updated

- README now states the trust model and limits explicitly.
- README examples list the live Worker fixture.
- Live Worker README now documents that deploy should use `pywrangler`, not plain `wrangler`, for this Python Worker fixture.

### Remaining concerns

#### Some docs still describe broad Cloudflare binding coverage more strongly than live E2E proves

Severity: Low

The package has local/fake coverage for many bindings, but live E2E currently covers only D1, R2, KV, response creation, and compatibility probes.

Recommendation:

When docs list binding wrappers, keep distinguishing between:

- locally/fake-Pyodide tested wrappers; and
- live Cloudflare-tested wrappers.

#### Basic examples assume bindings exist

Severity: Low

Examples are concise, but `safe.d1(...)`, `safe.kv(...)`, and `safe.r2(...)` can return `None` if bindings are missing.

Recommendation:

Add one fail-fast example or point users to app-local adapters that enforce required bindings.

## Language best practices audit

### Strengths

- Public functions/classes are type-hinted.
- `py.typed` is present.
- Async APIs are used consistently for Workers operations.
- `uv` and locked dependency workflows are in place.

### Remaining concerns

#### No static type checker is enforced

Severity: Low

The package advertises typing, but CI currently enforces Ruff and tests, not mypy/pyright.

Recommendation:

Add pyright or mypy once the public API stabilizes enough that type-checking false positives do not slow down migration.

## Resource management audit

### Strengths

- ReadableStream readers release locks in `finally` blocks.
- HTTPX clients are scoped with `async with`.
- Live deploy generated files are ignored and can be safely removed.

### Remaining concerns

No blocking resource leaks found.

## Test quality audit

### Strengths

- 100% line and branch coverage is enforced.
- Property-based tests cover conversion invariants.
- Fake Pyodide tests exercise branches unavailable in CPython.
- Live E2E tests passed against a real deployed Cloudflare Worker.
- Tests caught actual bugs during development.

### Remaining concerns

#### Live E2E coverage is intentionally narrow

Severity: Low/Medium

The live Worker does not yet verify Queues, AI, Vectorize, Durable Objects, Cache, Analytics Engine, or service bindings.

Recommendation:

Add live fixtures opportunistically as the two applications actually depend on those bindings through CFBoundary.

## Feature completeness audit

### Implemented and verified

- Generic FFI conversion helpers.
- D1/R2/KV wrappers with live Cloudflare verification.
- Queue/AI/Vectorize/service/Durable Object/Analytics/Cache/Assets wrappers with local/fake coverage.
- CLI checks and deploy-planning helpers.
- Live Worker fixture and manual E2E workflow.

### Not yet complete by design

- No app-specific wrapper migration in CFBoundary itself.
- No generic deploy orchestration that mutates Cloudflare resources; `plan_deploy()` is intentionally a planning API.
- No broad framework routing/auth/session abstractions.

## Security audit

### Secrets

No Cloudflare API token, OAuth token, `.env`, `.dev.vars`, generated deployment config, D1 ID, or KV namespace ID is tracked in the CFBoundary repo after cleanup.

The repository ignores:

- `.env*`
- `.dev.vars*`
- `.wrangler/`
- `.venv-workers/`
- `python_modules/`
- `examples/live_worker/wrangler.deploy.jsonc`
- `examples/live_worker/src/cfboundary/`

### Dependency audit note

`uvx pip-audit --strict --desc` reported a vulnerability in the ambient `pip` package version used by the audit environment. It did not identify an application dependency in CFBoundary's declared runtime dependency set.

Recommendation:

Do dependency audits in a clean project environment during release, not against unrelated global tooling packages.

## Impact on Tasche

Current impact: **low risk**.

- Tasche does not import CFBoundary directly in runtime code yet.
- `tasche/src/wrappers.py` remains the app-local compatibility layer.
- The full test suite passes: `1243 passed, 35 skipped`.
- The current strategy is correct: migrate internals behind Tasche's existing wrapper API rather than forcing application call sites to change at the same time.

Primary migration risks:

1. Tasche's historical JS null helper still documents `js.JSON.parse("null")`; CFBoundary uses `pyodide.ffi.jsnull`. Migration must preserve the corrected semantics.
2. Tasche has app-specific helpers such as readability, response shapes, and binding-name properties that must remain local.
3. Tasche E2E marks are unregistered, causing warnings; unrelated to CFBoundary but worth cleaning separately.

## Impact on Planet CF

Current impact: **low risk**.

- Planet CF does not import CFBoundary directly in runtime code yet.
- `planet_cf/src/wrappers.py` remains app-local.
- The full test suite passes: `1426 passed, 107 skipped`.
- The known `AsyncMock` RuntimeWarning remains unrelated to CFBoundary.

Primary migration risks:

1. Planet CF's wrapper layer includes app-specific row conversion, auth/session/feed/search concerns, and observability behavior that must not move into CFBoundary.
2. Vectorize and HTTP behavior should be migrated carefully because Planet CF has production search and fetch workflows.
3. The un-awaited `AsyncMock` warning should be fixed in Planet CF to keep warning noise from hiding future migration regressions.

## Recommended next steps

1. Keep the CFBoundary API pre-1.0 until both apps delegate meaningful wrapper internals to it.
2. Add live E2E coverage for Queue and Vectorize once a consumer migration needs them.
3. Split `safe_env.py` into smaller modules while preserving `cfboundary.ffi` exports.
4. Add a required-binding helper only if both apps independently need the pattern.
5. Add a static type-checking job once the module split stabilizes.
6. Fix Planet CF's un-awaited `AsyncMock` warning outside the CFBoundary migration.
