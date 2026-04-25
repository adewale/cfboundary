from __future__ import annotations
import importlib

async def probe_eval_blocked() -> bool:
    try:
        from gasket.ffi.safe_env import js
        js.eval("1+1")
        return False
    except Exception:
        return True

async def probe_function_constructor_blocked() -> bool:
    try:
        from gasket.ffi.safe_env import js
        js.Function("return 1")()
        return False
    except Exception:
        return True

async def probe_module_importable(module: str) -> bool:
    try:
        importlib.import_module(module)
        return True
    except Exception:
        return False

async def run_all_probes() -> dict[str, bool]:
    return {"eval_blocked": await probe_eval_blocked(), "function_constructor_blocked": await probe_function_constructor_blocked()}
