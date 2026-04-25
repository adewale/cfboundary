# Testing Pyodide branches from CPython

```python
from gasket.ffi import d1_null, _to_py_safe
from gasket.testing.fakes import FakeJsProxy, JsNull, patch_pyodide_runtime


def test_js_null_converts_to_none():
    with patch_pyodide_runtime():
        assert _to_py_safe(JsNull()) is None
        assert _to_py_safe(FakeJsProxy({"ok": True})) == {"ok": True}
        assert d1_null(None) is not None  # a JS-null sentinel in the fake runtime
```

Smoke helpers are HTTP-client agnostic:

```python
import requests
from gasket.testing.smoke import SmokeBase

smoke = SmokeBase("https://example.workers.dev", requests.request)
smoke.wait_for_ready("/api/health")
smoke.assert_all_load(["/", "/static/style.css"])
```
