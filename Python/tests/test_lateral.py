import math

from aid.aircraft import Aircraft
from aid.lateral import lateral_dynamic, lateral_static


def _lat() -> Aircraft:
    return Aircraft(
        WG={"a": 0.1, "S": [20.0], "cbar": [2.0], "b": 10.0, "AR": [5.0], "TR": [1.0],
            "swp": __import__("numpy").zeros((4, 1)), "gamma": 0.0, "SSPN": 5.0,
            "Z": 1.0, "X": 4.0, "CHRDR": 2.0, "x_ac": 0.25, "xmac": 0.5, "CL": 0.4},
        HT={"a": 0.08, "a0": [6.0], "S": [4.0], "Z": 1.0, "DHDADI": 0.0, "DHDADO": 0.0,
            "SSPNOP": 0.0, "SSPN": 2.0},
        VT={"AR": [1.5], "TR": [0.6], "S": [2.0], "b": 2.0, "Z": 0.5, "X": 10.0,
            "cbar": [1.0], "xmac": 0.3, "ymac": 0.4},
        F={}, A={}, E={}, R={},
        BD={"X": [0.0, 5.0, 12.0], "ZU": [0.2, 0.8, 0.3], "ZL": [-0.2, -0.6, -0.2],
            "R": [0.2, 0.7, 0.25], "S": [0.1, 1.5, 0.2], "NX": 3, "dk": 1.0, "d_eq": 1.0,
            "Cnb": 0.0},
        NP=[], NB=[],
        AERO={"MACH": [0.2], "ZCG": 0.0, "XCG": 4.5},
        plot_cmp=[1, 1, 1, 1], unit="ft",
    )


def test_static_placeholders_are_point_one():
    out = lateral_static(_lat(), angl=True, cl=0.4)
    assert out["Clda"] == 0.1
    assert out["Cnda"] == 0.1
    assert "CYb" in out and "Clb" in out and "Cnb" in out


def test_dynamic_matches_closed_form():
    ac = _lat()
    ac.VT["a"] = 0.05
    ac.VT["swash"] = 1.0
    ac.VT["S"] = [2.0]
    ac.VT["l"] = 4.0
    ac.VT["h"] = 1.0
    ac.VT["hp"] = 1.0
    ac.WG["a"] = 0.1
    ac.WG["TR"] = [1.0]
    ac.WG["AR"] = [5.0]
    ac.WG["swp"] = __import__("numpy").zeros((4, 1))
    ac.WG["b"] = 10.0
    ac.WG["S"] = [20.0]
    out = lateral_dynamic(ac, cl=0.4, cyb=-0.01)
    # Clp = -a/12 * (1+3*TR)/(1+TR) = -0.1/12 * 4/2
    assert abs(out["Clp"] - (-0.1 / 12 * 2)) < 1e-12
    # Cnr = -2*a*swash*Sv/Sw*(l/b)^2
    expect = -2 * 0.05 * 1.0 * 2.0 / 20.0 * (4.0 / 10.0) ** 2
    assert abs(out["Cnr"] - expect) < 1e-12
