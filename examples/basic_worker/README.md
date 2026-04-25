# Basic Worker example

This example shows the intended pattern: wrap the raw Worker `env` once, then access bindings by name and kind.

```python
from gasket.ffi import SafeEnv
from gasket.adapters.response import full_response

async def fetch(request, env, ctx):
    safe = SafeEnv(env)
    db = safe.d1("DATABASE")
    bucket = safe.r2("OBJECTS")
    sessions = safe.kv("SESSION_STORE")

    row = await db.prepare("select ? as message").bind("hello from D1").first()
    await sessions.put("last_message", row["message"], expiration_ttl=60)
    await bucket.put("hello.txt", row["message"].encode("utf-8"))

    return await full_response(row["message"], media_type="text/plain")
```

For application-specific convenience names, keep adapters in the application:

```python
class AppEnv(SafeEnv):
    @property
    def DB(self):
        return self.d1("DB")
```

Do not add project binding names to gasket itself; they are application choices.
