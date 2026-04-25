from __future__ import annotations

import os
import urllib.request

import pytest


BASE_URL = os.environ.get("GASKET_E2E_BASE_URL")


pytestmark = pytest.mark.skipif(
    not BASE_URL,
    reason="set GASKET_E2E_BASE_URL to a deployed gasket example Worker to run live E2E tests",
)


def _get(path: str) -> tuple[int, str, dict[str, str]]:
    url = BASE_URL.rstrip("/") + path
    request = urllib.request.Request(url, headers={"User-Agent": "gasket-live-e2e/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.status, response.read().decode("utf-8"), dict(response.headers)


def test_live_worker_health() -> None:
    status, body, headers = _get("/health")
    assert status == 200
    assert body == "ok"
    assert "text/plain" in headers.get("Content-Type", headers.get("content-type", ""))


def test_live_worker_d1_null_roundtrip() -> None:
    status, body, _ = _get("/d1-null")
    assert status == 200
    assert body == "null-ok"


def test_live_worker_r2_roundtrip() -> None:
    status, body, _ = _get("/r2")
    assert status == 200
    assert body == "r2-ok"


def test_live_worker_kv_roundtrip() -> None:
    status, body, _ = _get("/kv")
    assert status == 200
    assert body == "kv-ok"


def test_live_worker_compat_probes() -> None:
    status, body, headers = _get("/compat")
    assert status == 200
    assert "application/json" in headers.get("Content-Type", headers.get("content-type", ""))
    assert "eval_blocked" in body
