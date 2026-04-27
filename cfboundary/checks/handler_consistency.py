from __future__ import annotations

from pathlib import Path

from .common import Finding


def check_handler_consistency(paths: list[Path]) -> list[Finding]:
    """Deprecated no-op.

    Handler naming and application env-wrapper policies are project-specific.
    Keep this function as a compatibility shim for callers that imported it, but
    do not emit generic CFBoundary findings.
    """
    return []
