# Pre-release checklist execution: 2026-04-25

This records execution of `docs/pre-release-checklist.md` for the current pre-GitHub Gasket state.

## Summary

Verdict: **ready for GitHub project creation after choosing a package publishing name strategy**.

All code, package, live E2E, and consumer regression checks passed. No tracked secrets were found. The only release-planning blocker discovered is that the PyPI name `gasket` is already occupied by an unrelated historical package, so PyPI publication should use a different distribution name unless ownership is resolved.

## Commands and results

### Repository hygiene

Generated artifacts were removed after validation:

```bash
rm -f gasket/.coverage
rm -rf gasket/.pytest_cache gasket/.ruff_cache gasket/.hypothesis gasket/.venv gasket/dist
rm -rf gasket/examples/live_worker/.venv-workers gasket/examples/live_worker/.venv gasket/examples/live_worker/.wrangler
rm -rf gasket/examples/live_worker/python_modules gasket/examples/live_worker/src/gasket
rm -f gasket/examples/live_worker/wrangler.deploy.jsonc
find gasket tasche planet_cf -type d -name __pycache__ -prune -exec rm -rf {} +
```

### Secret scan

```bash
cd gasket
uvx detect-secrets scan --all-files
```

Result:

```text
files_with_findings 0
```

Targeted grep also found no real secrets. Matches were documentation/API terms such as `secret`, `token`, and synthetic test values.

### Static checks, tests, package build

```bash
cd gasket
uv run ruff check .
uv run pytest --cov=gasket --cov-branch --cov-report=term-missing --cov-fail-under=100 -q
uv run python -m compileall -q gasket
uv build
uvx twine check dist/*
uvx vulture gasket tests --min-confidence 80
```

Results:

```text
ruff: pass
pytest: 70 passed, 5 skipped
coverage: 100% line, 100% branch
twine: source distribution and wheel passed
vulture: no production findings
```

### Live Cloudflare E2E

The live Worker was already deployed at the configured Workers URL. The latest code path was verified with:

```bash
cd gasket
GASKET_E2E_BASE_URL=https://gasket-live-worker.<subdomain>.workers.dev uv run pytest tests/e2e -q
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
- `/compat`

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
cd gasket
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
import json, urllib.request
j=json.load(urllib.request.urlopen('https://pypi.org/pypi/gasket/json',timeout=10))
print(j['info'].get('summary'))
print(j['info'].get('version'))
print(j['info'].get('home_page'))
PY
```

Result:

```text
Simple note taking aplication for gnome
0.1
http://joey101.net/gasket/
```

Implication: GitHub repo name `gasket` is fine, but PyPI publication needs a name strategy such as `gasket-workers` or `cloudflare-gasket`, unless the existing PyPI project can be transferred.

### Dependency audit note

A requirements-based `pip-audit` attempt failed because the audit tool's temporary Python 3.13 virtualenv hit an `ensurepip` crash in this local environment. A previous environment-level audit only reported a vulnerability in ambient `pip`, not a declared Gasket runtime dependency.

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
- [ ] PyPI package name strategy decided.

## Recommendation

Create the GitHub project now, keeping the project explicitly pre-1.0. Before publishing to PyPI, choose a distribution name that does not collide with the existing `gasket` package.
