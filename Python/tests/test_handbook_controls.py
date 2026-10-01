import math

from aid.aircraft import Aircraft
from aid.control_deriv import COEFFS
from aid.handbook_controls import handbook_controls


def _plane() -> Aircraft:
    return Aircraft(
        WG={"a": 0.1, "S": [10.0, 20.0], "cbar": [1.0, 2.0], "b": 10.0, "SSPN": 5.0, "TR": 0.6, "x_cg": 0.25},
        HT={"a": 0.08, "S": [4.0], "eta": 0.9, "l": 8.0},
        VT={"a": 0.05, "S": [2.0], "k": 1.0, "swash": 1.0, "h": 1.5, "l": 8.0},
        F={"SPANFI": 1.0, "SPANFO": 3.0, "CHRDFI": 0.4, "CHRDFO": 0.4, "DELTA": 0.0},
        A={"SPANFI": 3.0, "SPANFO": 4.5, "CHRDFI": 0.3, "CHRDFO": 0.25, "DELTAL": 0.0, "DELTAR": 0.0},
        E={"SPANFI": 0.2, "SPANFO": 1.5, "CHRDFI": 0.3, "CHRDFO": 0.2, "DELTA": 0.0},
        R={"SPANFI": 0.2, "SPANFO": 1.2, "CHRDFI": 0.35, "CHRDFO": 0.2, "DELTA": 0.0},
        BD={}, NP=[], NB=[], AERO={"XCG": 1.0}, plot_cmp=[1, 1, 1, 1], unit="ft",
    )


def test_zero_stored_deflection_still_returns_nonzero_probe():
    rows = handbook_controls(_plane(), [0.0, 5.0])
    flap = [r for r in rows if r["surface"] == "flap"]
    assert [r["delta_deg"] for r in flap] == [0.0, 5.0]
    assert flap[0]["CL"] == flap[1]["CL"]
    assert flap[0]["CL"] is not None and flap[0]["CL"] != 0.0
    assert flap[0]["CD"] is None


def test_rudder_tau_uses_rudder_area_not_elevator_area():
    ac = _plane()
    ac.E["SPANFO"] = 0.21  # elevator area near zero, rudder area is not
    rows = handbook_controls(ac, [5.0])
    rudder = next(r for r in rows if r["surface"] == "rudder")
    assert rudder["available"] is True
    assert rudder["CY"] is not None and rudder["Cn"] == -rudder["CY"] * 8.0 / 10.0


def test_aileron_cl_is_not_the_placeholder():
    rows = handbook_controls(_plane(), [5.0])
    ail = next(r for r in rows if r["surface"] == "aileron")
    assert ail["Cl"] not in (None, 0.1, 0.1 * math.pi / 180.0)
    assert ail["Cn"] is None


def test_stored_angles_stay_zero():
    ac = _plane()
    handbook_controls(ac, [5.0])
    assert ac.F["DELTA"] == 0.0 and ac.A["DELTAR"] == 0.0


def test_illegal_span_is_unavailable_and_other_surfaces_remain():
    ac = _plane()
    ac.F["SPANFO"] = ac.F["SPANFI"]
    rows = handbook_controls(ac, [0.0, 5.0])
    flaps = [r for r in rows if r["surface"] == "flap"]
    assert [r["delta_deg"] for r in flaps] == [0.0, 5.0]
    assert [r["available"] for r in flaps] == [False, False]
    for row in flaps:
        assert all(row[name] is None for name in COEFFS)
    others = [r for r in rows if r["surface"] != "flap"]
    assert [r["surface"] for r in others] == [
        "aileron", "aileron", "elevator", "elevator", "rudder", "rudder",
    ]
    assert all(r["available"] is True for r in others)
    assert next(r["CL"] for r in others if r["surface"] == "elevator") is not None

    missing = _plane()
    missing.A["CHRDFO"] = None
    rows_missing = handbook_controls(missing, [5.0])
    ail = next(r for r in rows_missing if r["surface"] == "aileron")
    assert ail["available"] is False
    assert all(ail[name] is None for name in COEFFS)
    assert next(r for r in rows_missing if r["surface"] == "flap")["CL"] is not None
    assert next(r for r in rows_missing if r["surface"] == "rudder")["available"] is True
