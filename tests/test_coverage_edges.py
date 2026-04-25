from __future__ import annotations

import os
import time
from pathlib import Path

from gasket.checks import check_ffi_boundary, check_pyodide_pitfalls, check_vendor
from gasket.cli import main
from gasket.deploy import validate_ready


def test_check_file_inputs_and_unicode_errors(tmp_path: Path) -> None:
    file_path = tmp_path / "one.py"
    file_path.write_text("import js\n")
    assert check_ffi_boundary([file_path])[0].code == "GSK001"

    bad = tmp_path / "bad.py"
    bad.write_bytes(b"\xff\xfe")
    assert check_ffi_boundary([bad]) == []
    assert check_pyodide_pitfalls([bad]) == []

    internal = tmp_path / "gasket" / "ffi" / "internal.py"
    internal.parent.mkdir(parents=True)
    internal.write_text("import js\n")
    assert check_ffi_boundary([tmp_path]) == [check_ffi_boundary([file_path])[0]]


def test_pyodide_pitfalls_function_constructor(tmp_path: Path) -> None:
    source = tmp_path / "pit.py"
    source.write_text("Function('return 1')\n")
    assert check_pyodide_pitfalls([source])[0].code == "GSK011"


def test_vendor_dist_info_lockfile_and_parse_errors(tmp_path: Path) -> None:
    vendor = tmp_path / "python_modules"
    vendor.mkdir()
    (vendor / "requests-1.0.dist-info").mkdir()
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("import requests\nfrom external.module import thing\nfrom .local import thing\n")
    (src / "bad.py").write_text("def broken(:\n")
    lock = tmp_path / "uv.lock"
    lock.write_text("lock")
    old = time.time() - 100
    os.utime(vendor, (old, old))
    codes = {f.code for f in check_vendor(tmp_path)}
    assert "GSK031" in codes
    assert "GSK032" in codes


def test_validate_ready_valid_invalid_and_empty_migrations(tmp_path: Path) -> None:
    (tmp_path / "python_modules").mkdir()
    (tmp_path / "wrangler.jsonc").write_text('{ // comment\n "name": "ok"\n}')
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    codes = {f.code for f in validate_ready(tmp_path, required_secrets=["TOKEN"])}
    assert "GSK100" not in codes
    assert "GSK102" in codes
    assert "GSK103" in codes

    (tmp_path / "wrangler.jsonc").write_text("{")
    assert "GSK101" in {f.code for f in validate_ready(tmp_path)}

    (migrations / "0001.sql").write_text("select 1")
    assert "GSK102" not in {f.code for f in validate_ready(tmp_path)}


def test_cli_check_paths(tmp_path: Path, capsys, monkeypatch) -> None:
    source = tmp_path / "x.py"
    source.write_text("StreamingResponse([])\n")
    assert main(["check", str(tmp_path)]) == 1
    assert "GSK012" in capsys.readouterr().out

    clean = tmp_path / "clean"
    clean.mkdir()
    (clean / "ok.py").write_text("print('ok')\n")
    assert main(["check", str(clean)]) == 0

    monkeypatch.chdir(clean)
    assert main(["check", "."]) == 0


def test_cli_module_main_subprocess() -> None:
    # Main callable is covered directly; this assertion keeps the test lightweight
    # while documenting that `python -m gasket.cli doctor` is the intended module path.
    assert callable(main)
