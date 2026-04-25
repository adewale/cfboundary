# Live Worker E2E fixture

This directory documents the minimal deployed Worker expected by Gasket's live E2E tests.

The tests are skipped unless `GASKET_E2E_BASE_URL` is set:

```bash
GASKET_E2E_BASE_URL=https://your-worker.example.workers.dev uv run pytest tests/e2e
```

The deployed Worker should expose:

- `GET /health` → `200 text/plain` body `ok`
- `GET /d1-null` → binds Python `None` through Gasket/D1 and returns `null-ok`
- `GET /r2` → writes bytes through Gasket/R2, reads them back, and returns `r2-ok`

A concrete Wrangler project can be kept outside this repository or added later once the package has a public import location stable enough for Cloudflare's build step.
