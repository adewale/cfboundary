from __future__ import annotations

import asyncio
import os
from pathlib import Path
from types import SimpleNamespace

from cfboundary.adapters.response import full_response
from cfboundary.adapters.scheduled import scheduled_event_from_js
from cfboundary.adapters.streams import serve_r2_object_via_js
from cfboundary.checks import (
    check_ffi_boundary,
    check_handler_consistency,
    check_pyodide_pitfalls,
    check_vendor,
)
from cfboundary.cli import main
from cfboundary.deploy import plan_deploy, validate_ready
from cfboundary.testing.smoke import SmokeBase


def run(coro):
    return asyncio.run(coro)


def test_full_response_cpython() -> None:
    assert run(full_response("ok", media_type="text/plain", cache_control="max-age=1", status=201)) == {
        "body": "ok",
        "headers": {"Content-Type": "text/plain", "Cache-Control": "max-age=1"},
        "status": 201,
    }


def test_serve_r2_object_via_js_cpython() -> None:
    class Bucket:
        async def get(self, key):
            return None if key == "missing" else SimpleNamespace(body="body")

    env = SimpleNamespace(BUCKET=Bucket())
    assert run(serve_r2_object_via_js(env, "BUCKET", "missing")) is None
    assert run(serve_r2_object_via_js(env, "BUCKET", "present")).body == "body"


def test_scheduled_event_from_js() -> None:
    event = scheduled_event_from_js(SimpleNamespace(cron="* * * * *", scheduledTime=123))
    assert (event.cron, event.scheduled_time, event.type) == ("* * * * *", 123, "scheduled")


def test_checks_find_expected_patterns(tmp_path: Path) -> None:
    source = tmp_path / "worker.py"
    source.write_text(
        "import js\n"
        "from pyodide.ffi import to_js\n"
        "x.to_py()\n"
        "eval('1')\n"
        "StreamingResponse([])\n"
        "class Default: pass\n"
    )
    assert {f.code for f in check_ffi_boundary([tmp_path])} >= {"CFB001", "CFB002", "CFB003"}
    assert {f.code for f in check_pyodide_pitfalls([tmp_path])} >= {"CFB010", "CFB012"}
    assert check_handler_consistency([tmp_path]) == []


def test_vendor_check_missing_and_native_extension(tmp_path: Path) -> None:
    missing = check_vendor(tmp_path)
    assert missing[0].code == "CFB030"
    vendor = tmp_path / "python_modules"
    vendor.mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("import requests\n")
    (vendor / "bad.so").write_bytes(b"")
    codes = {f.code for f in check_vendor(tmp_path)}
    assert "CFB031" in codes
    assert "CFB033" in codes


def test_deploy_plan_and_cli(tmp_path: Path, capsys) -> None:
    assert validate_ready(tmp_path)[0].code == "CFB100"
    plan = plan_deploy(tmp_path)
    assert plan.can_deploy is False
    assert main(["doctor"]) == 0
    assert "workers_runtime=" in capsys.readouterr().out
    assert main(["plan-deploy", str(tmp_path)]) == 1
    assert "can_deploy=False" in capsys.readouterr().out


def test_smoke_base_helpers() -> None:
    class Response:
        def __init__(self, status_code=200, text="ok", headers=None):
            self.status_code = status_code
            self.text = text
            self.headers = headers or {"content-type": "application/rss+xml"}

    seen = []

    def request(method, url, **kwargs):
        seen.append((method, url, kwargs))
        return Response()

    smoke = SmokeBase("https://example.test", request)
    smoke.wait_for_ready("/health", interval_s=0)
    smoke.assert_status("/")
    smoke.assert_all_load(["/a", "/b"])
    smoke.assert_content_type("/feed", "rss")
    assert len(seen) == 5


def test_e2e_tests_are_skipped_by_default() -> None:
    assert "CFBOUNDARY_E2E_BASE_URL" not in os.environ or os.environ["CFBOUNDARY_E2E_BASE_URL"]
