# Rationale

Gasket is an extraction of code already proven in the two applications:

- Tasche contributed the core FFI boundary and Safe* wrapper design, including explicit conversion in both directions, D1 `None` → JS `null`, R2 byte conversion, ReadableStream consumption, and direct JS Response streaming for large R2 payloads.
- Planet CF contributed Vectorize usage, vendor/deploy readiness checks, deployment verification patterns, type stubs, and Pyodide compatibility probes.

The library deliberately avoids a framework abstraction. It sits below FastAPI/custom Worker handlers and centralizes the parts that are easy to get wrong at the Python/JavaScript boundary.
