import math

import numpy as np

from aid.longitudinal_dynamic import longitudinal_dynamic

def test_cxu_uses_three_cd_for_prop():
    cd0, k, cl = 0.02, 0.05, 0.5
    cd = cd0 + k * cl**2
    cda = 2 * k * cl * 0.08
    out = longitudinal_dynamic({
        "WT": 3217.0, "YI": 1000.0, "MACH": 0.2, "ALT": 0.0,
        "Q": 50.0, "a_sound": 1000.0, "S": 20.0, "cbar": 2.0,
        "CD0": cd0, "K": k, "CL": cl, "CLa": 0.08, "Cma": -0.01,
        "CLde": 0.01, "Cmde": -0.02, "ht_a": 0.07, "eta": 0.9,
        "ht_V": 0.5, "dwash": 0.4, "ht_l": 8.0,
    })
    # CXu = -0 - 3*CD; Xu = CXu * Q * S / (m * U); m = WT/32.17; U = M*a
    cxu = -3 * cd
    m = 3217.0 / 32.17
    u = 0.2 * 1000.0
    expect = cxu * 50.0 * 20.0 / (m * u)
    assert abs(out["Xu"] - expect) < 1e-9
    assert out["A"].shape == (4, 4)
    assert out["B"].shape == (4, 1)
    assert out["short_period"].shape == (2,)
    assert out["phugoid"].shape == (2,)
    assert np.all(np.isfinite(out["short_period"]))
