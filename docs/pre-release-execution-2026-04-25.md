# Pre-release checklist execution: 2026-04-25

This historical report records the 2026-04-25 checklist run. The public API has since been narrowed to the used shared FFI core; use the current `README.md` and `docs/pre-release-checklist.md` for release guidance.

## Summary

Verdict: **ready for GitHub project creation**.

All code, package, live E2E, and consumer regression checks passed. No tracked secrets were found. The PyPI names `cfboundary` and `cf-boundary` both returned 404 at check time, so the chosen project name is available for package publication.

## Commands and results

### Repository hygiene

Generated artifacts were removed after validation:

```bash
rm -f cfboundary/.coverage
rm -rf cfboundary/.pytest_cache cfboundary/.ruff_cache cfboundary/.hypothesis cfboundary/.venv cfboundary/dist
rm -rf cfboundary/examples/live_worker/.venv-workers cfboundary/examples/live_worker/.venv cfboundary/examples/live_worker/.wrangler
rm -rf cfboundary/examples/live_worker/python_modules cfboundary/examples/live_worker/src/cfboundary
rm -f cfboundary/examples/live_worker/wrangler.deploy.jsonc
find cfboundary tasche planet_cf -type d -name __pycache__ -prune -exec rm -rf {} +
```

### Secret scan

```bash
cd cfboundary
uvx detect-secrets scan --all-files
```

Result:

```text
files_with_findings 0
```

Targeted grep also found no real secrets. Matches were documentation/API terms such as `secret`, `token`, and synthetic test values.

### Static checks, tests, package build

```bash
cd cfboundary
uv run ruff check .
uv run pytest --cov=cfboundary --cov-branch --cov-report=term-missing --cov-fail-under=100 -q
uv run python -m compileall -q cfboundary
uv build
uvx twine check dist/*
uvx vulture cfboundary tests --min-confidence 80
```

Results from the original run:

```text
ruff: pass
pytest: 70 passed, 5 skipped
coverage: 100% line, 100% branch
twine: source distribution and wheel passed
vulture: no production findings
```

Current local validation after trimming unused APIs:

```text
pytest: 23 passed, 5 skipped
coverage: 100% line, 100% branch
```

### Live Cloudflare E2E

The live Worker was already deployed at the configured Workers URL. The latest code path was verified with:

```bash
cd cfboundary
CFBOUNDARY_E2E_BASE_URL=https://cfboundary-live-worker.<subdomain>.workers.dev uv run pytest tests/e2e -q
```

Result:

```text
5 passed
```

The live fixture verifies:

- `/health`
- `/d1-null`
- `/r2`
- `/kv`
- `/compat` runtime detection

### Consumer regression suites

```bash
cd tasche && uv run --group test pytest -q
cd ../planet_cf && uv run --all-extras pytest -q
```

Results:

```text
tasche: 1243 passed, 35 skipped, 2 warnings
planet_cf: 1426 passed, 107 skipped, 1 warning
```

Known warnings:

- Tasche has unregistered `pytest.mark.e2e` warnings.
- Planet CF still has the known un-awaited `AsyncMock` RuntimeWarning.

### Documentation link check

```bash
cd cfboundary
python - <<'PY'
from pathlib import Path
import re
bad=[]
for md in Path('.').rglob('*.md'):
    if any(part in {'.venv','dist'} for part in md.parts):
        continue
    text = md.read_text()
    for link in re.findall(r'\]\(([^)#][^)]+)\)', text):
        if link.startswith(('http://', 'https://', 'mailto:')):
            continue
        target = link.split('#', 1)[0]
        if not target:
            continue
        path = (md.parent / target).resolve()
        if not path.exists():
            bad.append((str(md), link))
for b in bad:
    print(f'{b[0]}: broken link {b[1]}')
print('broken_count', len(bad))
raise SystemExit(1 if bad else 0)
PY
```

Result:

```text
broken_count 0
```

### PyPI name check

```bash
python3 - <<'PY'
import urllib.request, urllib.error
for name in ['cfboundary', 'cf-boundary']:
    try:
        with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/json', timeout=10) as r:
            print(name, 'TAKEN', r.status)
    except urllib.error.HTTPError as e:
        print(name, 'AVAILABLE' if e.code == 404 else f'HTTP {e.code}')
PY
```

Result:

```text
cfboundary AVAILABLE
cf-boundary AVAILABLE
```

Implication: the chosen package name is available at the time of this check.

### Dependency audit note

A requirements-based `pip-audit` attempt failed because the audit tool's temporary Python 3.13 virtualenv hit an `ensurepip` crash in this local environment. A previous environment-level audit only reported a vulnerability in ambient `pip`, not a declared CFBoundary runtime dependency.

For release, run dependency audit again in CI or a clean local environment against the exported runtime requirements.

## Checklist status

- [x] Repository hygiene checked.
- [x] Generated artifacts removed.
- [x] Formal secret scan passed.
- [x] Targeted secret grep reviewed.
- [x] Ruff passed.
- [x] Tests passed with 100% package line/branch coverage.
- [x] `compileall` passed.
- [x] Source distribution and wheel built.
- [x] `twine check` passed.
- [x] Vulture produced no production findings.
- [x] Live Cloudflare E2E passed.
- [x] Tasche regression suite passed.
- [x] Planet CF regression suite passed.
- [x] Markdown link check passed.
- [x] GitHub issue/PR templates added.
- [x] Code of conduct added.
- [x] PyPI name availability checked.
- [x] PyPI package name strategy decided: `cfboundary`.

## Recommendation

Create the GitHub project now, keeping the project explicitly pre-1.0. The selected PyPI distribution/import package name is `cfboundary`.
