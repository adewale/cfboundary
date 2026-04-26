## Summary

Describe the change and why it belongs in CFBoundary rather than an application-local wrapper.

## Scope check

- [ ] This keeps CFBoundary generic: no app-specific binding names, routes, row factories, auth/session/feed/theme logic, or deployment topology.
- [ ] Public API changes are documented.
- [ ] Migration impact on Tasche and Planet CF is considered.

## Validation

- [ ] `uv run ruff check .`
- [ ] `uv run pytest --cov=cfboundary --cov-branch --cov-report=term-missing --cov-fail-under=100`
- [ ] `uv run python -m compileall -q cfboundary`
- [ ] `uv build`
- [ ] Live E2E run, or explanation for why it is not needed.

## Notes

Mention any follow-up work or known limitations.
