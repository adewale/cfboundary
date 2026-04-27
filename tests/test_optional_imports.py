from __future__ import annotations

import importlib
import sys
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest


def _restore_core(old_module: ModuleType | None) -> None:
    if old_module is not None:
        sys.modules["cfboundary.ffi.core"] = old_module
        import cfboundary.ffi as ffi

        setattr(ffi, "core", old_module)
    else:
        sys.modules.pop("cfboundary.ffi.core", None)


def test_core_reraises_nested_module_import_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    old_module = sys.modules.get("cfboundary.ffi.core")
    original_import_module = importlib.import_module

    def fake_import_module(name: str, package: str | None = None) -> Any:
        if name == "js":
            return ModuleType("js")
        if name == "pyodide.ffi":
            raise ModuleNotFoundError(
                "No module named 'broken_runtime_dependency'", name="broken_runtime_dependency"
            )
        return original_import_module(name, package)

    try:
        sys.modules.pop("cfboundary.ffi.core", None)
        monkeypatch.setattr(importlib, "import_module", fake_import_module)
        with pytest.raises(ModuleNotFoundError, match="broken_runtime_dependency"):
            original_import_module("cfboundary.ffi.core")
    finally:
        monkeypatch.setattr(importlib, "import_module", original_import_module)
        _restore_core(old_module)


def test_core_imports_fake_pyodide_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    old_module = sys.modules.get("cfboundary.ffi.core")
    original_import_module = importlib.import_module
    js_module = SimpleNamespace(Object=SimpleNamespace(fromEntries=dict))
    pyodide_ffi = SimpleNamespace(
        JsException=RuntimeError,
        JsProxy=object,
        jsnull=object(),
        to_js=lambda value, **kwargs: value,
    )

    def fake_import_module(name: str, package: str | None = None) -> Any:
        if name == "js":
            return js_module
        if name == "pyodide.ffi":
            return pyodide_ffi
        return original_import_module(name, package)

    try:
        sys.modules.pop("cfboundary.ffi.core", None)
        monkeypatch.setattr(importlib, "import_module", fake_import_module)
        module = original_import_module("cfboundary.ffi.core")
        assert module.HAS_PYODIDE is True
        assert module.js is js_module
        assert module.jsnull is pyodide_ffi.jsnull
    finally:
        monkeypatch.setattr(importlib, "import_module", original_import_module)
        _restore_core(old_module)
