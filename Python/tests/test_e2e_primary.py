# Python/tests/test_e2e_primary.py
import os
import subprocess

import pytest

from aid.paths import matlab_code

MATLAB = "/home/valentin/ProgramFiles/MB2025b/bin/matlab"


def test_matlab_batch_cessna_still_ok():
    r = subprocess.run(
        [MATLAB, "-batch", f"cd('{matlab_code()}'); run_aid_batch('Cessna 172')"],
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert r.returncode == 0


def test_python_primary_compare_suite():
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    r = subprocess.run(
        [
            "python",
            "-m",
            "pytest",
            "tests/test_compare_primary.py",
            "tests/test_gui_window.py",
            "-q",
        ],
        cwd=matlab_code().parents[2] / "Python",
        env=env,
    )
    assert r.returncode == 0
