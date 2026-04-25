# Application adapters

Gasket is generic. Application-specific compatibility belongs in the application.

## Why adapters are needed

Real Workers often start with a local `wrappers.py` that mixes two concerns:

1. Generic Cloudflare/Pyodide boundary mechanics.
2. Application semantics such as binding names, row factories, auth/session helpers, model coercion, observability hooks, and route-specific response shapes.

Only the first category belongs in gasket. During migration, keep a small app-local adapter for the second category.

## Recommended pattern

```python
from gasket.ffi import SafeEnv


class AppEnv(SafeEnv):
    @property
    def database(self):
        return self.d1("DATABASE")

    @property
    def object_store(self):
        return self.r2("OBJECTS")
```

If an existing application has public names that many call sites use, keep those names locally until each call site is migrated:

```python
class LegacyEnv(SafeEnv):
    def __init__(self, raw_env):
        super().__init__(raw_env)
        self.DB = self.d1("DATABASE")
        self.CONTENT = self.r2("OBJECTS")
```

## What should stay in the app

- Binding-name properties.
- Row factories and model coercion.
- Auth/session helpers.
- Product-specific validators.
- Observability/event hooks.
- Route-specific response objects.
- Deployment topology and theme/template checks.

## What should move to gasket

- JS null/undefined handling.
- `to_py` / `to_js` conversion.
- D1 bind conversion.
- Generic D1/R2/KV/Queue/AI/Vectorize/service binding wrappers.
- Generic runtime probes.
- Generic smoke-test and deploy-validation primitives.

## Migration rule

A migration PR should not replace a mature local wrapper with a thin shim unless the app's full test suite stays green. Prefer incremental delegation from the compatibility adapter to gasket.
