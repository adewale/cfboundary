"""The shipped CPython fakes must fail the way real Pyodide does.

Expected values were observed in real Pyodide 0.28.3 (npm ``pyodide``) running in Node:
a missing attribute on a JS object proxy raises ``AttributeError``, so
``getattr(proxy, name, default)`` returns the default, and ``jsnull`` is falsy.
"""

from __future__ import annotations

import pytest

from cfboundary.ffi import get_r2_size, js_null
from cfboundary.testing import FakeJsProxy, JsNull, patch_pyodide_runtime


def test_fake_proxy_missing_attribute_raises_attribute_error() -> None:
    proxy = FakeJsProxy({"present": 1})
    assert proxy.present == 1
    with pytest.raises(AttributeError):
        _ = proxy.absent
    assert getattr(proxy, "absent", "default") == "default"


def test_get_r2_size_on_fake_proxy_without_size_is_none() -> None:
    assert get_r2_size(FakeJsProxy({})) is None
    assert get_r2_size(FakeJsProxy({"size": 7})) == 7


def test_fake_js_null_is_falsy_like_real_jsnull() -> None:
    assert not JsNull()
    with patch_pyodide_runtime():
        assert not js_null()
