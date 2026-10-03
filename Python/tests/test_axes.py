import numpy as np
import pytest

from aid.axes import from_frd, to_frd


def test_datcom_flips_axial_and_normal_only():
    raw = {"alpha": [0.0, 2.0], "cd": [0.02, 0.03], "cl": [0.1, 0.2],
           "cm": [0.01, 0.0], "cn": [0.1, 0.2], "ca": [0.02, 0.01],
           "xcp": [0.1, 0.0], "cla": [0.09, 0.09], "cyb": [-0.01, -0.01],
           "cnb": [0.001, 0.001], "clb": [-0.002, -0.002]}
    got = to_frd("datcom", raw)
    assert got["ca"] == [-0.02, -0.01]
    assert got["cn"] == [-0.1, -0.2]
    for key in ("cd", "cl", "cm", "xcp", "cla", "cyb", "cnb", "clb", "alpha"):
        assert got[key] == raw[key]
    assert raw["ca"] == [0.02, 0.01], "to_frd must not mutate its input"


def _negated(value):
    return [-v for v in value] if isinstance(value, list) else -value


def test_tornado_flips_axial_normal_roll_yaw_and_their_derivatives():
    raw = {"CX": -0.04, "CY": 0.0, "CZ": 0.54, "Cl": 0.003, "Cm": -0.95, "Cn": -0.027,
           "CX_a": -0.2, "CZ_a": 4.2, "Cl_a": 0.01, "Cn_a": -0.07,
           "CY_a": 0.0, "CY_b": -0.3, "CY_R": 0.4, "CC": -0.0,
           "Cl_b": 0.05, "Cn_b": -0.25,
           "Cl_P": -0.49, "Cl_Q": 0.0, "Cl_R": 0.04,
           "Cn_P": 0.07, "Cn_Q": 0.0, "Cn_R": -0.29,
           "CX_d": [-1.0], "CZ_d": [-2.0], "Cl_d": [0.5], "Cn_d": [0.6],
           "CY_d": [0.1]}
    got = to_frd("tornado", raw)
    for key in ("CX", "CZ", "Cl", "Cn", "CX_a", "CZ_a", "Cl_a", "Cn_a",
                "Cl_b", "Cn_b", "Cl_P", "Cl_Q", "Cl_R", "Cn_P", "Cn_Q", "Cn_R",
                "CX_d", "CZ_d", "Cl_d", "Cn_d"):
        assert got[key] == pytest.approx(_negated(raw[key])), key
    for key in ("CY", "Cm", "CY_a", "CY_b", "CY_R", "CC", "CY_d"):
        assert got[key] == pytest.approx(raw[key]), key
    assert got["Cl_d"] == [-0.5] and got["Cn_d"] == [-0.6]
    assert got["CY_d"] == [0.1]


def test_avl_and_flow5_are_identity():
    raw = {"CXtot": 0.03, "CZtot": -0.6, "CYtot": 0.0, "Cltot": 0.0,
           "Cmtot": -0.2, "Cntot": 0.0, "CYb": -0.3, "Cnb": 0.17, "Clb": -0.03}
    for solver in ("avl", "flow5"):
        assert to_frd(solver, raw) == raw


def test_round_trip_is_identity_for_every_solver():
    raw = {"CX": -0.04, "CZ": 0.54, "Cl": 0.003, "Cn": -0.027,
           "cn": 0.1, "ca": 0.02, "CXtot": 0.03}
    for solver in ("avl", "datcom", "tornado", "flow5"):
        assert from_frd(solver, to_frd(solver, raw)) == raw


def test_unknown_solver_raises():
    with pytest.raises(KeyError):
        to_frd("handbook", {"CL": 1.0})
    with pytest.raises(KeyError):
        from_frd("vlm2", {"CL": 1.0})


def test_missing_key_is_absent_not_zero():
    got = to_frd("tornado", {"CL": 0.5})
    assert got == {"CL": 0.5}
    assert "CZ" not in got


def test_structured_values_pass_through_by_identity():
    surface = [{"name": "aileron", "angle": 0.0}]
    high_lift = [{"config": "flap 10", "delta": 10.0, "dcl": [0.3]}]
    cp = np.zeros((4, 3))
    raw = {"surface": surface, "high_lift": high_lift, "cp": cp, "CZ": 0.5}
    got = to_frd("tornado", raw)
    assert got["surface"] is surface
    assert got["high_lift"] is high_lift
    assert got["cp"] is cp
    assert got["CZ"] == -0.5


def test_nd_sentinel_keeps_its_magnitude():
    raw = {"ca": [0.02, 99999.0], "cn": [99999.0, 0.1], "cd": [0.02, 99999.0]}
    got = to_frd("datcom", raw)
    assert got["ca"] == [-0.02, -99999.0]
    assert got["cn"] == [-99999.0, -0.1]
    assert got["cd"] == [0.02, 99999.0]
    masked = np.abs(np.asarray(got["ca"], dtype=float)) >= 99998
    assert list(masked) == [False, True], "a negated ND must still mask"


def test_numpy_arrays_stay_arrays():
    raw = {"CZ": np.array([0.5, 0.6])}
    got = to_frd("tornado", raw)
    assert isinstance(got["CZ"], np.ndarray)
    assert got["CZ"].tolist() == [-0.5, -0.6]