# Contributing

Thanks for considering a contribution to gasket.

## Design rules

Gasket must stay generic:

- Do not add application-specific binding names such as `DB`, `CONTENT`, or `SEARCH_INDEX` to the library surface.
- Do not add product-specific row factories, route helpers, auth/session code, feed/article/theme logic, or deployment topology.
- Prefer binding-kind APIs such as `SafeEnv.d1(name)`, `SafeEnv.r2(name)`, and `SafeEnv.service(name)`.
- Add new Cloudflare API wrappers only when there is a reusable FFI boundary pattern.

## Local checks

```bash
python3 -m compileall -q gasket
python3 -m gasket.cli doctor
```

If optional development tools are installed, also run:

```bash
ruff check .
pytest
```

## Documentation

Any public API change should update:

- `README.md`
- `CHANGELOG.md`
- relevant files under `docs/`
- examples under `examples/` when useful
