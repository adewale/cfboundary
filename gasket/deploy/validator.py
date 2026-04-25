from __future__ import annotations

import json
import re
from pathlib import Path

from gasket.checks.common import Finding
from gasket.checks.vendor import check_vendor


def validate_ready(
    project_root: Path,
    *,
    wrangler_config: Path = Path("wrangler.jsonc"),
    required_secrets: list[str] | None = None,
) -> list[Finding]:
    findings = []
    config = project_root / wrangler_config
    if not config.exists():
        findings.append(Finding(config, 1, "error", "GSK100", "wrangler config missing"))
    else:
        try:
            json.loads(re.sub(r"//.*$", "", config.read_text(), flags=re.MULTILINE))
        except Exception as exc:
            findings.append(
                Finding(config, 1, "error", "GSK101", f"wrangler config is not valid JSONC: {exc}")
            )
    mig = project_root / "migrations"
    if mig.exists() and not list(mig.glob("*.sql")):
        findings.append(Finding(mig, 1, "warning", "GSK102", "migrations directory has no sql files"))
    findings.extend(check_vendor(project_root))
    return findings
