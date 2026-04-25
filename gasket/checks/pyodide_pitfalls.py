from __future__ import annotations

import re
from pathlib import Path

from .common import Finding

_PATTERNS = [
    (re.compile(r"js\.eval\(|\beval\("), "GSK010", "eval is blocked in Workers/Pyodide"),
    (re.compile(r"Function\("), "GSK011", "Function constructor is blocked in Workers/Pyodide"),
    (
        re.compile(r"StreamingResponse"),
        "GSK012",
        "StreamingResponse may truncate; use gasket.adapters.response.full_response",
    ),
]


def check_pyodide_pitfalls(paths: list[Path]) -> list[Finding]:
    out: list[Finding] = []
    for root in paths:
        files = [root] if root.is_file() else list(root.rglob("*.py"))
        for path in files:
            try:
                lines = path.read_text().splitlines()
            except UnicodeDecodeError:
                continue
            for i, line in enumerate(lines, 1):
                for pat, code, msg in _PATTERNS:
                    if pat.search(line):
                        out.append(Finding(path, i, "error", code, msg))
    return out
