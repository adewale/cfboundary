from __future__ import annotations
from pathlib import Path
from .common import Finding

def check_handler_consistency(paths: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for root in paths:
        files = [root] if root.is_file() else list(root.rglob("*.py"))
        for path in files:
            text = path.read_text(errors="ignore")
            if "class Default" in text and "SafeEnv" not in text:
                findings.append(Finding(path, 1, "warning", "GSK020", "Worker entrypoint should wrap env with SafeEnv"))
    return findings
