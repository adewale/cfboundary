from __future__ import annotations
import re
from pathlib import Path
from .common import Finding

_PATTERNS = [(re.compile(r"\bimport js\b|from js import"), "CFB001", "direct js import outside boundary"), (re.compile(r"from pyodide\.ffi import .*to_js|\bto_js\("), "CFB002", "direct to_js use; route through cfboundary"), (re.compile(r"\.to_py\("), "CFB003", "direct JsProxy conversion; route through cfboundary")]

def check_ffi_boundary(paths: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for root in paths:
        files = [root] if root.is_file() else list(root.rglob("*.py"))
        for path in files:
            if "cfboundary/ffi" in path.as_posix():
                continue
            try:
                lines = path.read_text().splitlines()
            except UnicodeDecodeError:
                continue
            for i, line in enumerate(lines, 1):
                for pattern, code, msg in _PATTERNS:
                    if pattern.search(line):
                        findings.append(Finding(path, i, "warning", code, msg))
    return findings
