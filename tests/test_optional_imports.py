from __future__ import annotations

import builtins
import importlib
import sys
from types import ModuleType

import pytest


def test_safe_env_reraises_nested_module_import_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    old_module = sys.modules.get("cfboundary.ffi.safe_env")
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "js":
            return ModuleType("js")
        if name == "pyodide.ffi":
            raise ModuleNotFoundError("No module named 'broken_runtime_dependency'", name="broken_runtime_dependency")
        return original_import(name, globals, locals, fromlist, level)

    try:
        sys.modules.pop("cfboundary.ffi.safe_env", None)
        monkeypatch.setattr(builtins, "__import__", fake_import)
        with pytest.raises(ModuleNotFoundError, match="broken_runtime_dependency"):
            importlib.import_module("cfboundary.ffi.safe_env")
    finally:
        monkeypatch.setattr(builtins, "__import__", original_import)
        if old_module is not None:
            sys.modules["cfboundary.ffi.safe_env"] = old_module
        else:
            sys.modules.pop("cfboundary.ffi.safe_env", None)


def test_http_reraises_nested_js_import_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    old_module = sys.modules.get("cfboundary.http")
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "js":
            raise ModuleNotFoundError("No module named 'broken_js_dependency'", name="broken_js_dependency")
        return original_import(name, globals, locals, fromlist, level)

    try:
        sys.modules.pop("cfboundary.http", None)
        monkeypatch.setattr(builtins, "__import__", fake_import)
        with pytest.raises(ModuleNotFoundError, match="broken_js_dependency"):
            importlib.import_module("cfboundary.http")
    finally:
        monkeypatch.setattr(builtins, "__import__", original_import)
        if old_module is not None:
            sys.modules["cfboundary.http"] = old_module
        else:
            sys.modules.pop("cfboundary.http", None)
