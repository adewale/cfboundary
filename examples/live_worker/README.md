# Live Worker E2E fixture

This is a minimal Cloudflare Python Worker for verifying Gasket against real Cloudflare bindings.

It intentionally exercises:

- `full_response()`
- D1 `None` → JS `null` bind behavior
- D1 read conversion back to Python `None`
- R2 bytes write/read/delete
- KV put/get/delete
- runtime compatibility probes

## Secret-safety notes

Do not commit Cloudflare API tokens, `.dev.vars`, `.env` files, generated Wrangler config, or vendored deployment output. The repository `.gitignore` excludes:

- `.dev.vars*`
- `.env*`
- `.wrangler/`
- `.venv-workers/`
- `node_modules/`
- `python_modules/`
- `examples/live_worker/wrangler.deploy.jsonc`
- `examples/live_worker/src/gasket/`

`database_id`, KV namespace IDs, and bucket names are resource identifiers rather than API secrets, but this fixture still keeps the generated deployment config untracked.

## Configure Cloudflare resources

Authenticate Wrangler locally first:

```bash
npx wrangler login
npx wrangler whoami
```

Create resources:

```bash
npx wrangler d1 create gasket-live-worker-db
npx wrangler r2 bucket create gasket-live-worker-objects
npx wrangler kv namespace create SESSION_STORE
```

Export the IDs returned by Wrangler:

```bash
export GASKET_LIVE_D1_DATABASE_ID=<database_id>
export GASKET_LIVE_KV_NAMESPACE_ID=<kv_namespace_id>
```

Prepare untracked deployment files and vendor the local checkout of Gasket into the Worker project:

```bash
python3 scripts/prepare_deploy.py
```

Apply migrations using the generated config:

```bash
npx wrangler d1 migrations apply gasket-live-worker-db --remote --config wrangler.deploy.jsonc
```

## Deploy

```bash
uv run --group workers pywrangler deploy --config wrangler.deploy.jsonc
```

## Run E2E tests

```bash
GASKET_E2E_BASE_URL=https://gasket-live-worker.<subdomain>.workers.dev uv run pytest tests/e2e
```

Expected endpoints:

- `GET /health` → `200 text/plain` body `ok`
- `GET /d1-null` → `200 text/plain` body `null-ok`
- `GET /r2` → `200 text/plain` body `r2-ok`
- `GET /kv` → `200 text/plain` body `kv-ok`
- `GET /compat` → `200 application/json` runtime probe map
