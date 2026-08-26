# Python/tests/test_drag_cessna.py
import numpy as np
from aid.aircraft import load_mat
from aid.atmosphere import atmosphere
from aid.drag import drag
from aid.paths import matlab_code


def test_drag_adds_cd0_field():
    ac = load_mat(matlab_code() / "Models" / "Cessna 172.mat")
    atm = atmosphere(float(np.asarray(ac.AERO["ALT"]).reshape(-1)[0]))
    out = drag(dict(ac.WG), ac.unit, atm, float(ac.WG["S"]))
    assert "CD0" in out
    if "CD0" in ac.WG:
        assert abs(out["CD0"] - float(ac.WG["CD0"])) < 1e-3
