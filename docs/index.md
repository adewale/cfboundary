# Gasket documentation

Gasket is a generic toolkit for Cloudflare Python Workers. These docs explain the design constraints, migration strategy, and current API coverage.

## Guides

- [Rationale](rationale.md) — why gasket exists and what it deliberately does not do.
- [API surface audit](api-surface-audit.md) — Cloudflare Developer Platform surfaces covered by gasket and known gaps.
- [Compatibility test matrix](compatibility-matrix.md) — the CPython, Pyodide-fake, and deployed-worker coverage expected for gasket and apps.
- [Application adapters](application-adapters.md) — how to keep app-specific compatibility out of gasket.
- [Surface polish backlog](surface-polish.md) — Pythonic API improvements implemented and still planned.
- [Wrapper audit](wrapper-audit.md) — lessons from the source wrappers and improvements made during extraction.
- [Migrating from local wrappers](migrating-from-local-wrappers.md) — moving a project with a local FFI wrapper to gasket.
- [Migrating from product-specific wrappers](migrating-from-product-specific-wrappers.md) — splitting generic boundary code from app/product semantics.

## Examples

- [Basic Worker](../examples/basic_worker/README.md)
- [Testing Pyodide branches from CPython](../examples/testing/README.md)
