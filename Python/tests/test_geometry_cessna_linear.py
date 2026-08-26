# Python/tests/test_geometry_cessna_linear.py
import numpy as np
from aid.aircraft import load_mat
from aid.geometry import geometry
from aid.paths import matlab_code


def test_cessna_wing_area_cbar_ar():
    ac = load_mat(matlab_code() / "Models" / "Cessna 172.mat")
    wg = dict(ac.WG)
    out = geometry(wg, angl=False)
    assert abs(float(np.asarray(out["S"]).reshape(-1)[-1]) - 24.0) < 1e-6
    assert abs(float(np.asarray(out["cbar"]).reshape(-1)[-1]) - 2.0) < 1e-6
    assert abs(float(np.asarray(out["AR"]).reshape(-1)[-1]) - 6.0) < 1e-4
