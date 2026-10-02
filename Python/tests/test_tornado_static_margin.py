import numpy as np
import pytest

from aid.tornado.static_margin import StaticMarginError, find_static_margin

def test_newton_stops_when_cm_over_cl_is_tiny():
    geo = {"ref_point": np.array([1.0, 0.0, 0.0], dtype=float), "CG": np.array([0.5, 0.0, 0.0])}
    state = {}
    calls = {"n": 0}

    def run(g, s):
        calls["n"] += 1
        x = float(g["ref_point"][0])
        # Cm_a/CL_a = 0.2*(x-1.5) so the root is x=1.5. CL_a stays 1.
        return {"CL_a": 1.0, "Cm_a": 0.2 * (x - 1.5), "C_mac": 2.0}

    out = find_static_margin(geo, state, run=run)
    assert abs(out["ac"][0] - 1.5) < 1e-4
    assert abs(out["h"][0] - (1.5 - 0.5) / 2.0) < 1e-4
    assert calls["n"] < 10

def test_ten_misses_raise():
    geo = {"ref_point": np.array([0.0, 0.0, 0.0], dtype=float), "CG": np.zeros(3)}

    def run(g, s):
        return {"CL_a": 1.0, "Cm_a": 1.0, "C_mac": 1.0}

    with pytest.raises(StaticMarginError):
        find_static_margin(geo, state={}, run=run)
