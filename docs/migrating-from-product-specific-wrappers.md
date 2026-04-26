# Migrating an application with product-specific wrappers to cfboundary

Some applications combine reusable FFI code with product-specific helpers in one `wrappers.py`. During migration, split those responsibilities.

1. Add a pinned `cfboundary` dependency.
2. Move generic boundary behavior to `cfboundary.ffi` imports.
3. Keep row factories, model coercion, feed/page validators, theme checks, and deployment topology checks in the application.
4. Compose `cfboundary.deploy.validate_ready` with application-specific deployment checks instead of moving those checks into cfboundary.
5. Compose `cfboundary.testing.smoke.SmokeBase` with application-specific endpoint assertions.
6. Gradually replace old wrapper imports with either direct `cfboundary.ffi` imports or application-local adapters.
7. Delete the old monolithic wrapper only after all generic and application-specific responsibilities have been separated.

The key rule: cfboundary owns Cloudflare/Pyodide boundary mechanics; the application owns product semantics.
