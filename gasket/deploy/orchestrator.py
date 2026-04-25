from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from gasket.checks.common import Finding

from .validator import validate_ready


@dataclass(frozen=True)
class DeployPlan:
    """Result of generic deploy readiness planning.

    Gasket does not run Wrangler or mutate Cloudflare resources. Applications
    compose this generic plan with their own migration/deploy commands.
    """

    project_root: Path
    environment: str
    findings: list[Finding]
    pending_migrations: list[Path]

    @property
    def can_deploy(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)


def plan_deploy(project_root: Path, *, environment: str = "production") -> DeployPlan:
    migrations = sorted((project_root / "migrations").glob("*.sql"))
    return DeployPlan(
        project_root=project_root,
        environment=environment,
        findings=validate_ready(project_root),
        pending_migrations=migrations,
    )
