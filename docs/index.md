# CFBoundary documentation

CFBoundary is now intentionally small: it contains only shared Cloudflare Python Workers FFI conversion/runtime helpers and CPython fake-runtime testing support.

## Guides

- [Rationale](rationale.md) — why cfboundary exists and what it deliberately does not do.
- [Testing](testing.md) — local, property-based, coverage, and live E2E testing.
- [Compatibility test matrix](compatibility-matrix.md) — CPython, Pyodide-fake, and deployed-worker expectations.
- [Pre-release checklist](pre-release-checklist.md) — release-readiness checks before GitHub tags or package publication.
- [Pre-release execution, 2026-04-25](pre-release-execution-2026-04-25.md) — latest checklist run and release-readiness result.

## Examples

- [Live Worker E2E fixture](../examples/live_worker/README.md)
