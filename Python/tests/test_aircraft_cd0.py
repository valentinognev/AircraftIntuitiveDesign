import numpy as np

from aid.aircraft import load_mat
from aid.atmosphere import atmosphere
from aid.drag import aircraft_cd0, drag
from aid.paths import matlab_code


def _freestream(ac):
    return atmosphere(float(np.asarray(ac.AERO["ALT"]).reshape(-1)[0]))


def _sref(ac) -> float:
    return float(np.asarray(ac.WG["S"]).reshape(-1)[-1])


def _included_cd0(ac) -> list[float]:
    """Same parts aircraft_cd0 sums: plot_cmp primaries, then non-empty NP/NB."""
    atm = _freestream(ac)
    sref = _sref(ac)
    parts = [drag(dict(ac.WG), ac.unit, atm, sref)["CD0"]]
    if ac.plot_cmp[1]:
        parts.append(drag(dict(ac.HT), ac.unit, atm, sref)["CD0"])
    if ac.plot_cmp[2]:
        parts.append(drag(dict(ac.VT), ac.unit, atm, sref)["CD0"])
    if ac.plot_cmp[3]:
        parts.append(drag(dict(ac.BD), ac.unit, atm, sref)["CD0"])
    for pt in list(ac.NP or [])[:4]:
        if isinstance(pt, dict) and pt:
            cd0 = drag(dict(pt), ac.unit, atm, sref)["CD0"]
            if pt.get("Y"):
                cd0 *= 2
            parts.append(cd0)
    for pt in list(ac.NB or [])[:2]:
        if isinstance(pt, dict) and pt:
            cd0 = drag(dict(pt), ac.unit, atm, sref)["CD0"]
            if pt.get("Y0"):
                cd0 *= 2
            parts.append(cd0)
    return parts


def test_cessna_cd0_is_interference_times_component_sum():
    ac = load_mat(matlab_code() / "Models" / "Cessna 172.mat")
    total = aircraft_cd0(ac)
    assert abs(total - 1.25 * sum(_included_cd0(ac))) < 1e-9
    assert abs(float(ac.WG["CD0"]) - _included_cd0(ac)[0]) < 1e-9


def test_wing_off_drops_wing_cd0():
    ac = load_mat(matlab_code() / "Models" / "Cessna 172.mat")
    ac.plot_cmp[0] = 0
    on = aircraft_cd0(ac)
    ac.plot_cmp[0] = 1
    both = aircraft_cd0(ac)
    assert both > on


def test_offset_nacelle_cd0_is_doubled():
    ac = load_mat(matlab_code() / "Models" / "Cessna 172.mat")
    ac.plot_cmp = [0, 0, 0, 0]
    ac.NP = [None, None, None, None]
    nacelle = dict(ac.BD)
    nacelle["Y0"] = 12
    ac.NB = [nacelle, None]
    total = aircraft_cd0(ac)
    one = drag(dict(ac.BD), ac.unit, _freestream(ac), _sref(ac))["CD0"]
    assert abs(total - 1.25 * 2 * one) < 1e-9
    assert abs(float(nacelle["CD0"]) - 2 * one) < 1e-9
