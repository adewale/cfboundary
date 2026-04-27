from __future__ import annotations
import ast
from pathlib import Path
from .common import Finding

_STDLIB_LIKE = {"__future__", "typing", "pathlib", "dataclasses", "json", "re", "sys", "os", "time", "asyncio", "urllib", "logging", "datetime", "collections", "itertools", "functools", "math", "random", "secrets", "hashlib", "hmac", "base64", "email", "html", "xml", "sqlite3"}

def _imports_under(src: Path) -> set[str]:
    names: set[str] = set()
    for path in src.rglob("*.py") if src.exists() else []:
        try:
            tree = ast.parse(path.read_text())
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names.add(node.module.split(".")[0])
    return {n for n in names if n not in _STDLIB_LIKE and n not in {"src", "cfboundary", "js", "pyodide", "workers"}}

def check_vendor(project_root: Path, *, vendor_dir: Path = Path("python_modules"), lock_file: Path = Path("uv.lock")) -> list[Finding]:
    """Generic validation for vendored pure-Python modules used by Workers.

    Reports a missing vendor directory when a project has one configured by convention,
    missing top-level imported packages, stale vendor mtime versus lock file, and native
    extension files that cannot run in Python Workers.
    """
    findings: list[Finding] = []
    vendor = project_root / vendor_dir
    if not vendor.exists():
        return [Finding(vendor, 1, "warning", "CFB030", "vendor directory missing; skip if project does not vendor Python packages")]
    for name in sorted(_imports_under(project_root / "src")):
        if not (vendor / name).exists() and not any(vendor.glob(f"{name}-*.dist-info")):
            findings.append(Finding(vendor, 1, "warning", "CFB031", f"imported package may be missing from vendor dir: {name}"))
    if (project_root / lock_file).exists() and vendor.stat().st_mtime < (project_root / lock_file).stat().st_mtime:
        findings.append(Finding(vendor, 1, "warning", "CFB032", "vendor directory older than lock file"))
    for ext in list(vendor.rglob("*.so")) + list(vendor.rglob("*.pyd")) + list(vendor.rglob("*.dylib")):
        findings.append(Finding(ext, 1, "error", "CFB033", "native extension file is not supported by Python Workers"))
    return findings
