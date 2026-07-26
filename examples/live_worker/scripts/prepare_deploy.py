#!/usr/bin/env python3
"""Prepare an untracked deployable copy of the live Worker fixture.

The example Worker imports ``cfboundary``. Cloudflare Python Workers upload modules
from the Worker project, so this script vendors the local checkout into
``src/cfboundary`` without committing generated files.

It also writes ``wrangler.deploy.jsonc`` from ``wrangler.jsonc`` with resource
IDs supplied via environment variables. Resource IDs are not API secrets, but the
generated file is ignored so local deployment details are not accidentally
committed.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = Path(__file__).resolve().parents[1]
SOURCE_PACKAGE = ROOT / "cfboundary"
TARGET_PACKAGE = EXAMPLE / "src" / "cfboundary"
TEMPLATE = EXAMPLE / "wrangler.jsonc"
GENERATED = EXAMPLE / "wrangler.deploy.jsonc"


def main() -> int:
    if TARGET_PACKAGE.exists():
        shutil.rmtree(TARGET_PACKAGE)
    shutil.copytree(
        SOURCE_PACKAGE,
        TARGET_PACKAGE,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    d1_id = os.environ.get("CFBOUNDARY_LIVE_D1_DATABASE_ID", "REPLACE_WITH_D1_DATABASE_ID")
    kv_id = os.environ.get("CFBOUNDARY_LIVE_KV_NAMESPACE_ID", "REPLACE_WITH_KV_NAMESPACE_ID")
    rendered = TEMPLATE.read_text().replace("REPLACE_WITH_D1_DATABASE_ID", d1_id).replace(
        "REPLACE_WITH_KV_NAMESPACE_ID", kv_id
    )
    GENERATED.write_text(rendered)
    print(f"Vendored {SOURCE_PACKAGE} -> {TARGET_PACKAGE}")
    print(f"Wrote {GENERATED}")
    if "REPLACE_WITH_" in rendered:
        print("Set CFBOUNDARY_LIVE_D1_DATABASE_ID and CFBOUNDARY_LIVE_KV_NAMESPACE_ID before deploying.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
