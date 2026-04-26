from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cfboundary.http import FetchError, FetchResponse, fetch


def run(coro):
    return asyncio.run(coro)


def test_fetch_response_text_json_and_raise_for_status() -> None:
    response = FetchResponse(200, b'{"ok": true}', {"content-type": "application/json"}, "https://e.test")
    assert response.text == '{"ok": true}'
    assert response.final_url == "https://e.test"
    assert response.json() == {"ok": True}
    response.raise_for_status()


def test_fetch_response_raise_for_status_error() -> None:
    response = FetchResponse(500, b"x" * 600, {}, "https://e.test")
    with pytest.raises(FetchError) as exc:
        response.raise_for_status()
    assert exc.value.status_code == 500
    assert len(exc.value.message) < 530


def test_fetch_cpython_json_body() -> None:
    raw = MagicMock()
    raw.status_code = 201
    raw.content = b"created"
    raw.headers = {"x-test": "yes"}
    raw.url = "https://api.test/items"

    client = AsyncMock()
    client.request = AsyncMock(return_value=raw)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=client):
        response = run(fetch("https://api.test/items", method="POST", json={"name": "a"}))

    assert response.status_code == 201
    assert response.text == "created"
    client.request.assert_awaited_once()
    kwargs = client.request.await_args.kwargs
    assert kwargs["headers"]["Content-Type"] == "application/json"
    assert kwargs["content"] == '{"name": "a"}'


def test_fetch_cpython_form_body_and_redirect_option() -> None:
    raw = MagicMock(status_code=200, content=b"ok", headers={}, url="https://api.test")
    client = AsyncMock()
    client.request = AsyncMock(return_value=raw)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=client) as cls:
        run(fetch("https://api.test", method="POST", form={"a": "b"}, follow_redirects=False))

    assert cls.call_args.kwargs["follow_redirects"] is False
    assert client.request.await_args.kwargs["content"] == "a=b"


def test_fetch_pyodide_without_body_and_cpython_missing_httpx(monkeypatch) -> None:
    import cfboundary.http as http

    class Headers:
        def entries(self):
            return self

        def next(self):
            return type("Entry", (), {"done": True})()

    class Response:
        status = 204
        url = ""
        headers = Headers()

        async def text(self):
            return ""

    async def js_fetch(url, options):
        assert "body" not in options
        return Response()

    monkeypatch.setattr(http, "HAS_PYODIDE", True)
    monkeypatch.setattr(http, "js_fetch", js_fetch)
    response = run(fetch("https://worker.test"))
    assert response.status_code == 204
    assert response.url == "https://worker.test"

    monkeypatch.setattr(http, "HAS_PYODIDE", False)
    monkeypatch.setattr(http, "httpx", None)
    with pytest.raises(RuntimeError):
        run(fetch("https://worker.test"))


def test_fetch_cpython_errors_are_pythonic() -> None:
    import httpx

    client = AsyncMock()
    client.request = AsyncMock(side_effect=httpx.TimeoutException("slow"))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=client):
        with pytest.raises(TimeoutError):
            run(fetch("https://slow.test"))

    client.request = AsyncMock(side_effect=httpx.ConnectError("down"))
    with patch("httpx.AsyncClient", return_value=client):
        with pytest.raises(ConnectionError):
            run(fetch("https://down.test"))
