# Live Worker E2E fixture

This is a minimal Cloudflare Python Worker for verifying Gasket against real Cloudflare bindings.

It intentionally exercises:

- `full_response()`
- D1 `None` → JS `null` bind behavior
- D1 read conversion back to Python `None`
- R2 bytes write/read/delete
- KV put/get/delete
- runtime compatibility probes

## Configure Cloudflare resources

Create resources and replace placeholders in `wrangler.jsonc`:

```bash
npx wrangler d1 create gasket-live-worker-db
npx wrangler r2 bucket create gasket-live-worker-objects
npx wrangler kv namespace create SESSION_STORE
```

Apply migrations:

```bash
npx wrangler d1 migrations apply gasket-live-worker-db --remote
```

## Make Gasket importable

Until Gasket is published, install/copy it into this Worker project using your preferred Workers Python packaging flow. The important requirement is that `import gasket` works in the deployed Worker.

## Deploy

```bash
npx wrangler deploy
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
