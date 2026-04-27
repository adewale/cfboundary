# Contributing

Thanks for considering a contribution to cfboundary.

## Design rules

CFBoundary must stay generic:

- Do not add application-specific binding names such as `DB`, `CONTENT`, or `SEARCH_INDEX` to the library surface.
- Do not add product-specific row factories, route helpers, auth/session code, feed/article/theme logic, or deployment topology.
- Keep binding-name and binding-wrapper semantics in application projects; CFBoundary should stay focused on generic FFI conversion/runtime helpers.
- Add new Cloudflare API wrappers only when there is a reusable FFI boundary pattern.

## Local checks

This project uses `uv`.

```bash
uv sync --group dev
uv run python -m compileall -q cfboundary
uv run pytest --cov=cfboundary --cov-branch --cov-report=term-missing --cov-fail-under=100
```

If you are changing style-sensitive code, also run:

```bash
uv run ruff check .
```

## Documentation

Any public API change should update:

- `README.md`
- `CHANGELOG.md`
- relevant files under `docs/`
- examples under `examples/` when useful
