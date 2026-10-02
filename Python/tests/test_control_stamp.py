from aid.aircraft import Aircraft
from aid.handbook_controls import stamp_control_geometry


def test_flap_tau_and_lever_are_written():
    ac = Aircraft(
        WG={"a": 0.1, "S": [20.0], "cbar": [2.0], "b": 10.0, "SSPN": 5.0, "TR": 1.0,
            "X": 1.0, "xmac": 0.5},
        HT={"a": 0.08, "S": [4.0], "eta": 0.9, "l": 8.0},
        VT={"a": 0.05, "S": [2.0], "k": 1.0, "swash": 1.0, "h": 1.0, "l": 8.0},
        F={"SPANFI": 0.0, "SPANFO": 2.0, "CHRDFI": 0.4, "CHRDFO": 0.4},
        A={"SPANFI": 3.0, "SPANFO": 4.5, "CHRDFI": 0.3, "CHRDFO": 0.25},
        E={"SPANFI": 0.0, "SPANFO": 1.0, "CHRDFI": 0.4, "CHRDFO": 0.4},
        R={"SPANFI": 0.0, "SPANFO": 1.0, "CHRDFI": 0.4, "CHRDFO": 0.4},
        BD={}, NP=[], NB=[],
        AERO={"XCG": 2.0}, plot_cmp=[1, 1, 1, 1], unit="ft",
    )
    stamp_control_geometry(ac)
    # area = 0.5*(0.4+0.4)*(2-0) = 0.8; ratio = 0.8/20 = 0.04 → tau table clamps toward 0.1 bin
    assert ac.F["tau"] > 0.0
    assert abs(ac.F["x_ac"] - (2.0 - 0.4)) < 1e-12
    # x_cg = (2.0 - 1.0 - 0.5) / 2.0 = 0.25
    assert abs(ac.F["l"] - (ac.F["x_ac"] - 0.25)) < 1e-12
    assert "Kb" in ac.A
    assert ac.E["tau"] > 0.0
    assert ac.R["tau"] > 0.0


def _plane(**overrides) -> Aircraft:
    ac = Aircraft(
        WG={"a": 0.1, "S": [20.0], "cbar": [2.0], "b": 10.0, "SSPN": 5.0, "TR": 1.0,
            "X": 1.0, "xmac": 0.5},
        HT={"a": 0.08, "S": [4.0], "eta": 0.9, "l": 8.0},
        VT={"a": 0.05, "S": [2.0], "k": 1.0, "swash": 1.0, "h": 1.0, "l": 8.0},
        F={"SPANFI": 0.0, "SPANFO": 2.0, "CHRDFI": 0.4, "CHRDFO": 0.4},
        A={"SPANFI": 3.0, "SPANFO": 4.5, "CHRDFI": 0.3, "CHRDFO": 0.25},
        E={"SPANFI": 0.0, "SPANFO": 1.0, "CHRDFI": 0.4, "CHRDFO": 0.4},
        R={"SPANFI": 0.0, "SPANFO": 1.0, "CHRDFI": 0.4, "CHRDFO": 0.4},
        BD={}, NP=[], NB=[],
        AERO={"XCG": 2.0}, plot_cmp=[1, 1, 1, 1], unit="ft",
    )
    for block, fields in overrides.items():
        getattr(ac, block).update(fields)
    return ac


def test_flap_lever_uses_absolute_cg_not_quarter_chord_default():
    ac = _plane(AERO={"XCG": 4.0})
    stamp_control_geometry(ac)
    # x_cg = (4.0 - 1.0 - 0.5) / 2.0 = 1.25; x_ac = 1.6
    assert abs(ac.F["l"] - (1.6 - 1.25)) < 1e-12


def test_flap_lever_falls_back_to_wg_x_cg_then_quarter_chord():
    wg_only = _plane()
    del wg_only.WG["X"]
    wg_only.WG["x_cg"] = 0.4
    stamp_control_geometry(wg_only)
    assert abs(wg_only.F["l"] - (1.6 - 0.4)) < 1e-12

    default = _plane()
    del default.WG["X"]
    del default.WG["xmac"]
    stamp_control_geometry(default)
    assert abs(default.F["l"] - (1.6 - 0.25)) < 1e-12


def test_stamped_rudder_tau_uses_rudder_area_not_elevator_area():
    ac = _plane(E={"CHRDFI": 0.05, "CHRDFO": 0.05})
    stamp_control_geometry(ac)
    # rudder area 0.4 / VT.S 2.0 = 0.2 → tau 0.4; elevator area must not be used
    assert abs(ac.R["tau"] - 0.4) < 1e-12
    assert ac.E["tau"] != ac.R["tau"]


def test_illegal_span_leaves_that_surface_unchanged():
    ac = _plane()
    ac.F["SPANFO"] = ac.F["SPANFI"]
    ac.F["tau"] = -1.0
    ac.F["x_ac"] = -2.0
    ac.F["l"] = -3.0
    ac.A["SPANFO"] = ac.A["SPANFI"]
    ac.E["CHRDFO"] = None
    ac.R["SPANFO"] = ac.R["SPANFI"]
    stamp_control_geometry(ac)
    assert ac.F["tau"] == -1.0
    assert ac.F["x_ac"] == -2.0
    assert ac.F["l"] == -3.0
    assert "Kb" not in ac.A
    assert "tau" not in ac.E
    assert "tau" not in ac.R
