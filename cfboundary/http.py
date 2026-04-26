"""HTTP fetch helpers for Cloudflare Python Workers and CPython tests."""

from __future__ import annotations

import json as jsonlib
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlencode

from cfboundary.ffi.safe_env import HAS_PYODIDE, _headers_to_dict, to_js

try:  # pragma: no cover - exercised only inside the Pyodide/Workers runtime
    from js import fetch as js_fetch  # type: ignore[import-not-found]
except ModuleNotFoundError as exc:
    if exc.name != "js":
        raise
    js_fetch = None  # type: ignore[assignment]

try:  # pragma: no cover - absence is covered by monkeypatching httpx to None
    import httpx
except ModuleNotFoundError as exc:  # pragma: no cover
    if exc.name != "httpx":
        raise
    httpx = None  # type: ignore[assignment]


class FetchError(Exception):
    def __init__(self, status_code: int, message: str, url: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.url = url


@dataclass(frozen=True)
class FetchResponse:
    status_code: int
    content: bytes
    headers: dict[str, str]
    url: str = ""

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")

    @property
    def final_url(self) -> str:
        return self.url

    def json(self) -> Any:
        return jsonlib.loads(self.text)

    def raise_for_status(self) -> None:
        if self.status_code < 400:
            return
        body = self.text[:500]
        raise FetchError(self.status_code, f"HTTP {self.status_code}: {body}", self.url)


async def fetch(
    url: str,
    *,
    method: str = "GET",
    headers: Mapping[str, str] | None = None,
    data: Mapping[str, Any] | str | bytes | None = None,
    json: Any = None,
    form: Mapping[str, Any] | None = None,
    timeout: float | None = 30.0,
    follow_redirects: bool = True,
) -> FetchResponse:
    request_headers = dict(headers or {})
    body: str | bytes | None = None
    if json is not None:
        body = jsonlib.dumps(json)
        request_headers.setdefault("Content-Type", "application/json")
    elif form is not None:
        body = urlencode(form)
        request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
    elif isinstance(data, Mapping):
        body = urlencode(data)
    else:
        body = data

    if HAS_PYODIDE and js_fetch is not None:
        options: dict[str, Any] = {
            "method": method,
            "headers": request_headers,
            "redirect": "follow" if follow_redirects else "manual",
        }
        if body is not None:
            options["body"] = body
        response = await js_fetch(url, to_js(options))
        text = await response.text()
        return FetchResponse(
            int(response.status),
            str(text).encode("utf-8"),
            _headers_to_dict(response.headers),
            str(getattr(response, "url", url) or url),
        )

    if httpx is None:
        raise RuntimeError("httpx is required for cfboundary.http.fetch outside Pyodide")
    try:
        async with httpx.AsyncClient(follow_redirects=follow_redirects, timeout=timeout) as client:
            response = await client.request(method, url, headers=request_headers, content=body)
    except httpx.TimeoutException as exc:
        raise TimeoutError(str(exc)) from exc
    except httpx.ConnectError as exc:
        raise ConnectionError(str(exc)) from exc
    return FetchResponse(response.status_code, response.content, dict(response.headers), str(response.url))
