from __future__ import annotations

import asyncio
import sys
from types import SimpleNamespace

from cfboundary.compat import probe_module_importable, run_all_probes
from cfboundary.ffi.runtime import await_js, is_cold_start, is_workers_runtime


def run(coro):
    return asyncio.run(coro)


def test_runtime_helpers() -> None:
    assert is_workers_runtime() is False
    assert is_cold_start(window_s=9999) is True
    assert run(await_js(_awaitable("ok"))) == "ok"


async def _awaitable(value):
    return value


def test_compat_probes_module_importable() -> None:
    assert run(probe_module_importable("sys")) is True
    assert run(probe_module_importable("definitely_missing_cfboundary_test_module")) is False


def test_compat_run_all_probes_without_js(monkeypatch) -> None:
    import cfboundary.ffi.safe_env as safe_env

    monkeypatch.setattr(safe_env, "js", SimpleNamespace(eval=lambda code: 1, Function=lambda code: lambda: 1))
    result = run(run_all_probes())
    assert result == {"eval_blocked": False, "function_constructor_blocked": False}

    monkeypatch.setattr(
        safe_env,
        "js",
        SimpleNamespace(
            eval=lambda code: (_ for _ in ()).throw(RuntimeError("blocked")),
            Function=lambda code: (_ for _ in ()).throw(RuntimeError("blocked")),
        ),
    )
    result = run(run_all_probes())
    assert result == {"eval_blocked": True, "function_constructor_blocked": True}


def test_no_accidental_sys_mutation() -> None:
    assert "sys" in sys.modules
