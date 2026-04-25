from __future__ import annotations

import argparse
from pathlib import Path

from gasket.checks import (
    check_ffi_boundary,
    check_handler_consistency,
    check_pyodide_pitfalls,
    check_vendor,
)
from gasket.deploy import plan_deploy


def _print(findings):
    for f in findings:
        print(f"{f.path}:{f.line}: {f.severity}: {f.code} {f.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gasket")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check")
    p_check.add_argument("paths", nargs="*", default=["."])

    sub.add_parser("doctor")

    p_deploy = sub.add_parser("plan-deploy")
    p_deploy.add_argument("project_root", nargs="?", default=".")
    p_deploy.add_argument("--environment", default="production")

    args = parser.parse_args(argv)
    if args.cmd == "doctor":
        from gasket.ffi.runtime import is_workers_runtime

        print(f"workers_runtime={is_workers_runtime()}")
        return 0
    if args.cmd == "plan-deploy":
        plan = plan_deploy(Path(args.project_root), environment=args.environment)
        _print(plan.findings)
        print(f"can_deploy={plan.can_deploy}")
        print(f"pending_migrations={len(plan.pending_migrations)}")
        return 0 if plan.can_deploy else 1

    paths = [Path(p) for p in args.paths]
    findings = []
    findings += check_ffi_boundary(paths)
    findings += check_pyodide_pitfalls(paths)
    findings += check_handler_consistency(paths)
    if Path("python_modules").exists() or Path("pyproject.toml").exists():
        findings += check_vendor(Path("."))
    _print(findings)
    return 1 if any(f.severity == "error" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
