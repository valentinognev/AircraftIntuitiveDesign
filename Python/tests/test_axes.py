"""Pin ``aid.axes._SIGN_MAP``, including the keys that must NOT be flipped.

Every fixture value is non-zero on purpose. A ``0.0`` fixture cannot falsify a
sign: ``-0.0 == 0.0``, and ``-0.0 == pytest.approx(0.0)`` is also ``True``, so
any mutation of that key's sign or membership would survive.
"""

import numpy as np
import pytest

from aid.axes import from_frd, to_frd

SOLVERS = ("avl", "datcom", "tornado", "flow5")


def _negated(value):
    return [-v for v in value] if isinstance(value, list) else -value


def test_datcom_flips_axial_and_normal_only():
    raw = {"alpha": [1.0, 2.0], "cd": [0.02, 0.03], "cl": [0.1, 0.2],
           "cm": [0.01, -0.02], "cn": [0.1, 0.2], "ca": [0.02, 0.01],
           "xcp": [0.1, 0.05], "cla": [0.09, 0.09], "cyb": [-0.01, -0.01],
           "cnb": [0.001, 0.001], "clb": [-0.002, -0.002]}
    got = to_frd("datcom", raw)
    assert got["ca"] == [-0.02, -0.01]
    assert got["cn"] == [-0.1, -0.2]
    for key in ("cd", "cl", "cm", "xcp", "cla", "cyb", "cnb", "clb", "alpha"):
        assert got[key] == raw[key], key
        assert got[key] is raw[key], key
    assert raw["ca"] == [0.02, 0.01], "to_frd must not mutate its input"


def test_tornado_flips_axial_normal_roll_yaw_and_their_non_rate_derivatives():
    raw = {"CX": -0.04, "CY": 0.12, "CZ": 0.54, "Cl": 0.003, "Cm": -0.95, "Cn": -0.027,
           "CX_a": -0.2, "CY_a": 0.31, "CZ_a": 4.2, "Cl_a": 0.01, "Cm_a": -1.4, "Cn_a": -0.07,
           "CY_b": -0.3, "CY_R": 0.4, "CC": 0.02,
           "Cl_b": 0.05, "Cn_b": -0.25,
           "Cl_P": -0.49, "Cl_Q": -0.15, "Cl_R": 0.04,
           "Cm_Q": -8.0, "Cn_P": 0.07, "Cn_Q": -0.09, "Cn_R": -0.29,
           "CX_d": [-1.0], "CZ_d": [-2.0], "Cl_d": [0.5], "Cn_d": [0.6],
           "CY_d": [0.1]}
    got = to_frd("tornado", raw)
    flipped = ("CX", "CZ", "Cl", "Cn", "CX_a", "CZ_a", "Cl_a", "Cn_a",
               "Cl_b", "Cn_b", "CX_d", "CZ_d", "Cl_d", "Cn_d")
    for key in flipped:
        assert got[key] == pytest.approx(_negated(raw[key])), key
    # The rate derivatives land standard: raw Tornado Cl_P -0.486 already agrees
    # with AVL's Clp -0.470, so no -1 may be applied to them.
    not_flipped = ("CY", "Cm", "CY_a", "CY_b", "CY_R", "CC", "Cm_a",
                   "Cl_P", "Cl_Q", "Cl_R", "Cm_Q", "Cn_P", "Cn_Q", "Cn_R")
    for key in not_flipped:
        assert got[key] == pytest.approx(raw[key]), key
    assert got["Cl_d"] == [-0.5] and got["Cn_d"] == [-0.6]
    assert got["CY_d"] == [0.1]


def test_avl_is_identity():
    raw = {"CXtot": 0.03, "CZtot": -0.6, "CYtot": -0.02, "Cltot": 0.014,
           "Cmtot": -0.2, "Cntot": 0.031, "Clp": -0.47, "CYb": -0.3,
           "Cnb": 0.17, "Clb": -0.028}
    got = to_frd("avl", raw)
    assert got == raw
    for key in raw:
        assert got[key] is raw[key], key


def test_flow5_flips_the_four_lateral_channels_and_nothing_else():
    # R18. flow5 does NOT flip the way Tornado does: the two agree on the force
    # channels (Cx/Cz are raw aft/up-positive) and disagree on the moment ones.
    # Cl/Cn come from polar vars 12/13 (Cli/Cni), which are mirrored -- raw Cl
    # +0.0047339 at beta = +5, alpha = 0, against Clb*beta = -0.0046262. Everything
    # else takes no entry: computeStabilityDerivatives projects onto the
    # stability axes (panelanalysis.cpp:845-846), already Forward-Right-Down, so
    # CXa (which is CL - dCD/dalpha, not a bare -dCD/dalpha), CZa (already
    # -5.2562), CYb, Clb, Cnb and the rate derivatives all pass through.
    raw = {"Cx": -0.031, "Cz": 0.544, "Cl": 0.0047, "Cn": -0.0143,
           "CXa": 0.0595, "CZa": -5.2562, "CY": 0.06, "Cm": -0.95,
           "CYb": -0.4107, "Clb": -0.053, "Cnb": 0.1685,
           "Clp": -0.5385, "Cnr": -0.206}
    got = to_frd("flow5", raw)
    for key in ("Cx", "Cz", "Cl", "Cn"):
        assert got[key] == pytest.approx(-raw[key]), key
    for key in ("CXa", "CZa", "CY", "Cm", "CYb", "Clb", "Cnb", "Clp", "Cnr"):
        assert got[key] == pytest.approx(raw[key]), key
        assert got[key] is raw[key], key
    assert raw["Cl"] == 0.0047, "to_frd must not mutate its input"


def test_cy_and_cc_are_never_flipped():
    """The Global Constraint: ``CY`` and ``CC`` pass through every solver."""
    raw = {"CY": -0.31, "CC": 0.017, "CY_a": 0.42, "CY_b": -0.28,
           "CY_R": 0.19, "CY_d": [-0.06], "CYtot": -0.09,
           "Cltot": 0.021, "Cntot": -0.044}
    for solver in SOLVERS:
        got = to_frd(solver, raw)
        assert got == raw, solver
        for key in raw:
            assert got[key] == raw[key], (solver, key)
            assert got[key] is raw[key], (solver, key)


def test_round_trip_is_identity_for_every_solver():
    raw = {"CX": -0.04, "CZ": 0.54, "Cl": 0.003, "Cn": -0.027,
           "cn": 0.1, "ca": 0.02, "CXtot": 0.03, "Cltot": 0.014, "CZa": -5.2562}
    for solver in SOLVERS:
        assert from_frd(solver, to_frd(solver, raw)) == raw, solver


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