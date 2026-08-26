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
    subprocess.run([str(datcom_wrapper())], cwd=workdir, check=True, timeout=120)
    return parse_for006((workdir / "for006.dat").read_text())
