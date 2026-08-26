# Python/tests/test_aircraft_load_mat.py
from pathlib import Path
from aid.aircraft import load_mat
from aid.paths import matlab_code

MAT = matlab_code() / "Models" / "Cessna 172.mat"

def test_load_mat_cessna():
    ac = load_mat(MAT)
    assert ac.unit == "ft"
    assert abs(ac.WG["CHRDR"] - 2.0) < 1e-9
    assert list(ac.AERO["ALSCHD"]) == [-4, 0, 4, 8, 12]
    data = ac.WG["DATA"]
    assert isinstance(data, list) and isinstance(data[0], list)
    assert len(data) == 101
    assert len(data[0]) == 2
