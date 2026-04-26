# Before and after examples

CFBoundary is meant to replace repeated application-local Cloudflare Python Workers boundary code with a small generic layer. Application semantics stay in each app.

## 1. D1 nullable bind values

Before, apps often had to remember that Python `None` becomes JavaScript `undefined`, while D1 needs JavaScript `null` for SQL `NULL`:

```python
# app-local wrapper code
try:
    import js
    HAS_PYODIDE = True
    JS_NULL = js.JSON.parse("null")
except ImportError:
    HAS_PYODIDE = False
    JS_NULL = None


def d1_null(value):
    if value is None:
        return JS_NULL if HAS_PYODIDE else None
    return value

row = await db.prepare("select ? as value").bind(d1_null(None)).first()
```

After, bind through `SafeD1Statement`; `None` is converted at the boundary:

```python
from cfboundary.ffi import SafeEnv

safe = SafeEnv(env)
row = await safe.d1("DATABASE").prepare("select ? as value").bind(None).first()
```

## 2. JavaScript values leaking into app logic

Before, every app wrapper needed its own recursive `JsProxy`/null conversion:

```python
def to_py_safe(value):
    if value is None or is_js_null(value):
        return None
    if hasattr(value, "to_py"):
        value = value.to_py()
    if isinstance(value, dict):
        return {k: to_py_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_py_safe(v) for v in value]
    return value
```

After, generic boundary conversion is centralized:

```python
from cfboundary.ffi import to_py

py_value = to_py(worker_api_result)
```

Application-specific row shaping still belongs in the application:

```python
from cfboundary.ffi import to_py


def feed_row_from_d1(row):
    row = to_py(row) or {}
    return {
        "id": str(row["id"]),
        "title": str(row.get("title") or ""),
    }
```

## 3. Binding-name adapters stay local

Before, application code might expose project-specific binding properties directly in a large generic wrapper module:

```python
class SafeEnv:
    @property
    def DB(self):
        return SafeD1(self._env.DB)

    @property
    def CONTENT(self):
        return SafeR2(self._env.CONTENT)
```

After, CFBoundary supplies generic binding-kind access, and the app keeps names in a thin local adapter:

```python
from cfboundary.ffi import SafeEnv


class AppEnv(SafeEnv):
    @property
    def database(self):
        return self.d1("DB")

    @property
    def content_bucket(self):
        return self.r2("CONTENT")
```

This is the recommended migration pattern for Tasche and Planet CF: preserve each app's existing `wrappers.py` API while delegating generic boundary mechanics to CFBoundary internally.

## 4. R2 bytes and streams

Before, app code had to know how to consume JavaScript `ReadableStream` objects and convert typed arrays:

```python
reader = r2_object.body.getReader()
parts = []
try:
    while True:
        result = await reader.read()
        if result.done:
            break
        parts.append(bytes(result.value.to_py()))
finally:
    reader.releaseLock()
body = b"".join(parts)
```

After, use the wrapper object:

```python
from cfboundary.ffi import SafeEnv

obj = await SafeEnv(env).r2("OBJECTS").get("path/file.txt")
body = await obj.bytes()
text = await obj.text()
```

For large response bodies that should remain on the JavaScript side, use the stream adapter:

```python
from cfboundary.adapters.streams import serve_r2_object_via_js

return await serve_r2_object_via_js(env, "OBJECTS", "path/file.txt")
```

## 5. HTTP fetch

Before, apps often duplicated separate Workers `js.fetch` and CPython `httpx` branches:

```python
if HAS_PYODIDE:
    response = await js_fetch(url, to_js(options))
    text = await response.text()
else:
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, headers=headers, content=body)
```

After, use CFBoundary's normalized fetch helper:

```python
from cfboundary.http import fetch

response = await fetch(url, method="POST", json={"ok": True})
response.raise_for_status()
data = response.json()
```

## 6. Response construction

Before, Workers response construction leaked JavaScript globals or attempted to encode status through headers:

```python
return js.Response.new("not found", to_js({"headers": {"Content-Type": "text/plain"}}))
```

After, use the response adapter:

```python
from cfboundary.adapters.response import full_response

return await full_response("not found", media_type="text/plain", status=404)
```

## 7. Deployment readiness

Before, deployment checks were often app scripts with generic checks mixed into product-specific requirements.

After, compose CFBoundary's generic checks with app-local checks:

```python
from pathlib import Path
from cfboundary.deploy import validate_ready

findings = validate_ready(Path("."), required_secrets=["GITHUB_CLIENT_SECRET"])
findings += validate_app_routes()
findings += validate_app_seed_data()
```

CFBoundary intentionally does not deploy or verify app-specific secrets by itself; it reports generic readiness findings that applications can compose.
