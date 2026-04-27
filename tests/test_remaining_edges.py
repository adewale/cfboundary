from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from cfboundary.adapters.scheduled import scheduled_event_from_js
from cfboundary.http import fetch
from cfboundary.testing.fakes import FakeJsProxy, FakeJsModule, patch_pyodide_runtime
from cfboundary.testing.smoke import SmokeBase


def run(coro):
    return asyncio.run(coro)


def test_scheduled_event_from_js_accepts_pythonic_name() -> None:
    event = scheduled_event_from_js(SimpleNamespace(cron="0 * * * *", scheduled_time=456))
    assert event.cron == "0 * * * *"
    assert event.scheduled_time == 456


def test_fake_js_proxy_and_module_edges() -> None:
    proxy = FakeJsProxy(SimpleNamespace(value=1))
    assert proxy.value == 1
    assert FakeJsProxy({"x": 2}).x == 2
    assert FakeJsProxy(["a"])[0] == "a"
    assert FakeJsModule.Object.fromEntries([("a", 1)]) == {"a": 1}


def test_smoke_failure_paths() -> None:
    class Response:
        status_code = 500
        headers = {}
        text = "not xml"

    def request(method, url, **kwargs):
        return Response()

    smoke = SmokeBase("https://example.test", request)
    with pytest.raises(AssertionError):
        smoke.wait_for_ready(max_attempts=1, interval_s=0)
    with pytest.raises(AssertionError):
        smoke.assert_status("/", status=200)

    class OK(Response):
        status_code = 200

    def ok_request(method, url, **kwargs):
        return OK()

    smoke = SmokeBase("https://example.test", ok_request)
    with pytest.raises(AssertionError):
        smoke.assert_content_type("/", "json")


def test_http_pyodide_fetch_branch(monkeypatch) -> None:
    import cfboundary.http as http

    class Headers:
        def __init__(self):
            self.items = [("Content-Type", "text/plain")]

        def entries(self):
            return self

        def next(self):
            if self.items:
                return SimpleNamespace(done=False, value=self.items.pop(0))
            return SimpleNamespace(done=True)

    class Response:
        status = 202
        url = "https://worker.test/final"
        headers = Headers()

        async def text(self):
            return "accepted"

    async def js_fetch(url, options):
        assert options["method"] == "POST"
        assert options["body"] == "a=b"
        return Response()

    monkeypatch.setattr(http, "js_fetch", js_fetch)
    with patch_pyodide_runtime():
        response = run(fetch("https://worker.test", method="POST", data={"a": "b"}, follow_redirects=False))
    assert response.status_code == 202
    assert response.text == "accepted"
    assert response.headers == {"content-type": "text/plain"}
    assert response.url == "https://worker.test/final"
