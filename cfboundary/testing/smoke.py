"""HTTP-client-agnostic smoke test helpers."""
from __future__ import annotations
import time
from typing import Callable, Any
from urllib.parse import urljoin

class SmokeBase:
    def __init__(self, base_url: str, request: Callable[..., Any], *, default_headers: dict[str, str] | None = None):
        self.base_url = base_url.rstrip("/") + "/"
        self.request = request
        self.default_headers = default_headers or {}

    def _url(self, path: str) -> str:
        return urljoin(self.base_url, path.lstrip("/"))

    def wait_for_ready(self, path: str = "/", *, accept_statuses: set[int] = {200}, max_attempts: int = 10, interval_s: float = 3.0) -> None:
        last = None
        for _ in range(max_attempts):
            last = self.request("GET", self._url(path), headers=self.default_headers)
            if last.status_code in accept_statuses:
                return
            time.sleep(interval_s)
        raise AssertionError(f"not ready: last status {getattr(last, 'status_code', None)}")

    def assert_status(self, path: str, *, status: int = 200, method: str = "GET", **kwargs: Any) -> Any:
        headers = {**self.default_headers, **kwargs.pop("headers", {})}
        resp = self.request(method, self._url(path), headers=headers, **kwargs)
        assert resp.status_code == status, f"{path}: expected {status}, got {resp.status_code}"
        return resp

    def assert_all_load(self, paths: list[str], *, status: int = 200) -> None:
        for path in paths:
            self.assert_status(path, status=status)

    def assert_content_type(self, path: str, expected: str) -> None:
        resp = self.assert_status(path)
        assert expected in resp.headers.get("content-type", resp.headers.get("Content-Type", ""))
