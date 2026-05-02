# Rationale

CFBoundary is an extraction of code proven in both `tasche` and `planet_cf`, narrowed to the subset that belongs in a shared library.

The package keeps generic boundary mechanics:

- Python ↔ JavaScript value conversion;
- Pyodide `jsnull` / Python `None` missing-value handling;
- D1 `None` → JS `null` bind values;
- byte and readable-stream helpers used around R2-style bodies;
- fake Pyodide runtime setup for CPython tests.

The package deliberately does **not** provide app boundary wrappers, binding-name policy, deployment policy, static checks, smoke-test assertions, row factories, routes, auth/session/feed/search semantics, or a Worker framework. Those belong in individual Worker projects.
