# Python/tests/test_run_aid_batch_helpers.py
import subprocess
from aid.paths import matlab_code

MATLAB = "/home/valentin/ProgramFiles/MB2025b/bin/matlab"

def test_run_aid_batch_file_exists():
    p = matlab_code() / "run_aid_batch.m"
    assert p.is_file()
    t = p.read_text()
    assert "function write_json" in t
    assert "function strip_datcom" in t
