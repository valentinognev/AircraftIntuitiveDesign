from aid.aircraft import Aircraft
from aid.trim import trim_incidence


def _craft() -> Aircraft:
    return Aircraft(
        WG={"a": 0.1, "alpha0L": 0.0, "i": 0.0, "Cm": 0.0, "x_ac": 0.25,
            "cbar": [1.0], "S": [10.0], "X": 0.0, "xmac": 0.0, "Z": 0.0},
        HT={"a": 0.1, "S": [2.0], "eta": 1.0, "dwash": 0.0, "l": 2.0, "i": 0.0,
            "cbar": [1.0], "x_ac": 0.25, "X": 0.0, "xmac": 0.0},
        VT={},
        F={"DELTA": 0.0, "tau": 0.0, "l": 0.0},
        A={},
        E={"DELTA": 0.0, "tau": 0.0},
        R={},
        BD={"Cm0": 0.0, "Cma": 0.0},
        NP=[], NB=[],
        AERO={"ALSCHD": [2.0], "ALT": [0.0], "MACH": [0.1], "WT": 500.0, "XCG": 0.25, "ZCG": 0.0},
        plot_cmp=[1, 1, 1, 0], unit="ft",
    )


def test_both_free_lift_and_moment_residuals_are_zero():
    ac = _craft()
    out = trim_incidence(ac, htail=True, body=False, fix="both")
    assert out["error"] == 0
    assert abs(out["alpha"] - 2.0) < 1e-9
    aw, tlt = 0.1, 0.02
    cl0 = aw * out["i_wg"] + tlt * out["i_ht"]
    cla = 0.1 + tlt
    assert abs(out["CL"] - (cl0 + cla * out["alpha"])) < 1e-8
    cm0_ht = -2.0 * (tlt * out["i_ht"])
    cma = -tlt * 2.0
    assert abs(cm0_ht + cma * out["alpha"]) < 1e-8


def test_huge_weight_trips_the_sixty_degree_guard():
    ac = _craft()
    ac.WG["a"] = 1e-6
    ac.HT["a"] = 1e-6
    ac.AERO["WT"] = 1e9
    out = trim_incidence(ac, htail=True, body=False, fix="both")
    assert out["error"] != 0
    assert out["i_wg"] == 0.0 or out["i_ht"] == 0.0
