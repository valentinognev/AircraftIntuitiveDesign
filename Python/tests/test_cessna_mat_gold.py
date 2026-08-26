import json
import subprocess

from aid.paths import matlab_code

MATLAB = "/home/valentin/ProgramFiles/MB2025b/bin/matlab"
MAT = matlab_code() / "Models" / "Cessna 172.mat"


def test_cessna_matlab_load_gold():
    cmd = (
        f"S=load('{MAT}'); "
        "fprintf('%s\\n',jsonencode(struct("
        "'CHRDR',S.WG.CHRDR,'SSPN',S.WG.SSPN,'S',S.WG.S,"
        "'unit',S.unit,'ALSCHD',S.AERO.ALSCHD,'MACH',S.AERO.MACH(1),'XCG',S.AERO.XCG)));"
    )
    r = subprocess.run([MATLAB, "-batch", cmd], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    line = [ln for ln in r.stdout.splitlines() if ln.startswith("{")][-1]
    d = json.loads(line)
    assert d["CHRDR"] == 2
    assert d["SSPN"] == 6
    assert d["S"] == 24
    assert d["unit"] == "ft"
    alschd = d["ALSCHD"]
    if isinstance(alschd, list) and alschd and isinstance(alschd[0], list):
        alschd = [x[0] if isinstance(x, list) else x for x in alschd]
    assert alschd == [-4, 0, 4, 8, 12]
    assert abs(d["MACH"] - 0.03) < 1e-9
    assert abs(d["XCG"] - 2.94) < 1e-9
