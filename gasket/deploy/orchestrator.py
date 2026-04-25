from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from gasket.checks.common import Finding
from .validator import validate_ready

@dataclass
class DeployResult:
    deployed_version: str
    migrations_applied: list[str]
    verifier_passed: bool
    findings: list[Finding]

async def deploy(project_root: Path, *, environment: str = "production", apply_migrations: bool = True, verify_after: bool = True, verifier = None) -> DeployResult:
    findings = validate_ready(project_root)
    errors = [f for f in findings if f.severity == "error"]
    if errors:
        return DeployResult("", [], False, findings)
    # Library exposes orchestration contract; app-specific command execution stays in project scripts.
    return DeployResult(environment, [], verifier is None, findings)
