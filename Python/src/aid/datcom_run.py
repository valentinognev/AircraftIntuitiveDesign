"""Run DATCOM subprocess for an aircraft configuration."""

from __future__ import annotations

import subprocess
from pathlib import Path

from aid.aircraft import Aircraft
from aid.datcom_io import write_for005
from aid.datcom_parse import parse_for006
from aid.paths import datcom_wrapper


def run_datcom(ac: Aircraft, workdir: Path) -> dict:
    workdir.mkdir(parents=True, exist_ok=True)
    write_for005(ac, workdir / "for005.dat", unit=ac.unit)
    proc = subprocess.run([str(datcom_wrapper())], cwd=workdir, check=False, timeout=120)
    out = workdir / "for006.dat"
    if not out.is_file():
        dumped = workdir / "datcom.out"
        if dumped.is_file():
            out = dumped
    if out.is_file():
        try:
            return parse_for006(out.read_text())
        except ValueError:
            if proc.returncode:
                proc.check_returncode()
            raise
    proc.check_returncode()
    raise FileNotFoundError(f"DATCOM produced no output in {workdir}")
