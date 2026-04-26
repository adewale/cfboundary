# Migrating an application from local wrappers to cfboundary

This guide uses the source application as an example, but the migration pattern is generic.

1. Add a pinned `cfboundary` dependency.
2. Keep an application-local compatibility shim for existing binding names.
3. In that shim, subclass or compose `cfboundary.ffi.SafeEnv` and map app-specific properties to generic methods such as `d1(name)`, `r2(name)`, `kv(name)`, and `queue(name)`.
4. Replace imports from the old local wrapper with direct `cfboundary.ffi` imports where no app-specific binding names are needed.
5. Replace direct stream/response work with `cfboundary.adapters.streams` and `cfboundary.adapters.response` where appropriate.
6. Run unit tests and deployed smoke tests.
7. Delete the compatibility shim once all code uses generic cfboundary APIs or app-local adapters.

Application-specific row factories, route helpers, model conversions, and binding names should stay in the application, not in cfboundary.
