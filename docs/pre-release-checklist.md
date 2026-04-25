# Pre-release checklist

Use this checklist before publishing a GitHub release, creating a tag, or publishing a package.

## 1. Repository hygiene

- [ ] `git status --short` is clean except intentional release changes.
- [ ] Generated artifacts are removed or ignored:
  - `.coverage`
  - `.pytest_cache/`
  - `.ruff_cache/`
  - `.hypothesis/`
  - `dist/`
  - `.venv/`
  - `examples/live_worker/.venv/`
  - `examples/live_worker/.venv-workers/`
  - `examples/live_worker/.wrangler/`
  - `examples/live_worker/python_modules/`
  - `examples/live_worker/src/gasket/`
  - `examples/live_worker/wrangler.deploy.jsonc`
- [ ] No generated deployment config or vendored Worker package is staged.

## 2. Secret scan

Run at least one formal scanner plus targeted grep:

```bash
uvx detect-secrets scan --all-files
rg -n "CLOUDFLARE_API_TOKEN|BEGIN .*PRIVATE KEY|AKIA|sk_live|AIza|password|secret|token" . \
  --glob '!uv.lock' \
  --glob '!examples/live_worker/uv.lock' \
  --glob '!dist/**'
```

Expected result: no real secrets. Test fixture words such as `SECRET="s"` are acceptable if clearly synthetic.

## 3. Static checks and tests

```bash
uv run ruff check .
uv run pytest --cov=gasket --cov-branch --cov-report=term-missing --cov-fail-under=100
uv run python -m compileall -q gasket
uv build
uvx twine check dist/*
uvx vulture gasket tests --min-confidence 80
```

Expected result: all pass, 100% package line/branch coverage, no production dead-code findings.

## 4. Live Cloudflare E2E

Deploy the live Worker fixture using untracked generated config:

```bash
cd examples/live_worker
export GASKET_LIVE_D1_DATABASE_ID=<database_id>
export GASKET_LIVE_KV_NAMESPACE_ID=<kv_namespace_id>
python3 scripts/prepare_deploy.py
npx wrangler d1 migrations apply gasket-live-worker-db --remote --config wrangler.deploy.jsonc
uv run --group workers pywrangler deploy --config wrangler.deploy.jsonc
```

Run E2E:

```bash
cd ../..
GASKET_E2E_BASE_URL=https://gasket-live-worker.<subdomain>.workers.dev uv run pytest tests/e2e -q
```

Expected result: all live tests pass.

## 5. Consumer regression suites

From the parent workspace:

```bash
cd tasche && uv run --group test pytest -q
cd ../planet_cf && uv run --all-extras pytest -q
```

Expected result: both suites pass. Known warning classes should be documented in the release notes if still present.

## 6. Documentation and examples

- [ ] README installation instructions reference a real tag, branch, or commit.
- [ ] README project status is honest about pre-1.0 compatibility.
- [ ] Live Worker README uses `pywrangler`, not plain `wrangler`, for deployment.
- [ ] Live Worker docs do not publish personal resource IDs or generated config.
- [ ] Documentation distinguishes live-tested bindings from locally/fake-tested bindings.
- [ ] New public APIs are documented and included in tests.

Optional local Markdown link check:

```bash
python - <<'PY'
from pathlib import Path
import re

for md in Path('.').rglob('*.md'):
    text = md.read_text()
    for link in re.findall(r'\]\(([^)#][^)]+)\)', text):
        if link.startswith(('http://', 'https://', 'mailto:')):
            continue
        target = link.split('#', 1)[0]
        if not target:
            continue
        path = (md.parent / target).resolve()
        if not path.exists():
            print(f'{md}: broken link {link}')
PY
```

## 7. Packaging metadata

- [ ] `pyproject.toml` version matches the intended release.
- [ ] `CHANGELOG.md` has a release section for the version.
- [ ] `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, and `CODE_OF_CONDUCT.md` are present.
- [ ] GitHub issue and PR templates are present.
- [ ] If publishing to PyPI, the package name is available or the package name strategy is documented.

## 8. Tag and release

```bash
git tag vX.Y.Z
git push origin main --tags
```

For a pre-1.0 release, release notes should say:

- breaking changes are allowed before 1.0;
- Gasket is generic boundary tooling, not an application framework;
- Tasche and Planet CF migrations remain incremental behind app-local wrappers;
- live E2E was run against Cloudflare for D1/R2/KV/response/compat behavior.

## 9. Post-release cleanup

Remove generated local deployment artifacts:

```bash
rm -rf examples/live_worker/.venv examples/live_worker/.venv-workers examples/live_worker/.wrangler
rm -rf examples/live_worker/python_modules examples/live_worker/src/gasket
rm -f examples/live_worker/wrangler.deploy.jsonc .coverage
```

Confirm:

```bash
git status --short --ignored
```
