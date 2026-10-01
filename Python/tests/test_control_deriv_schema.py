from copy import deepcopy

from aid.aircraft import Aircraft
from aid.control_deriv import (
    COEFFS,
    DEFAULT_DELTAS_DEG,
    H_DEG,
    blank_row,
    central_difference,
    iter_rows,
    with_probe,
)


def _ac() -> Aircraft:
    z = {"SPANFI": 1.0, "SPANFO": 4.0, "CHRDFI": 1.0, "CHRDFO": 0.6, "DELTA": 0.0}
    a = {"SPANFI": 6.0, "SPANFO": 8.0, "CHRDFI": 0.5, "CHRDFO": 0.4, "DELTAL": 0.0, "DELTAR": 0.0}
    return Aircraft(
        WG={}, HT={}, VT={}, F=dict(z), A=dict(a), E=dict(z), R=dict(z),
        BD={}, NP=[], NB=[], AERO={}, plot_cmp=[1, 1, 1, 1], unit="ft",
    )


def test_default_probes_include_zero_and_a_nonzero_point():
    assert DEFAULT_DELTAS_DEG == (0.0, 5.0)
    assert H_DEG == 1.0
    pairs = iter_rows(None)
    assert pairs[0] == ("flap", 0.0)
    assert ("aileron", 5.0) in pairs
    assert [p[0] for p in pairs].count("rudder") == 2


def test_central_difference_is_per_degree():
    plus = {"CL": 0.12, "CD": 0.02, "Cm": -0.04, "CY": 0.0, "Cl": 0.01, "Cn": -0.01}
    minus = {"CL": 0.08, "CD": 0.02, "Cm": -0.02, "CY": 0.0, "Cl": -0.01, "Cn": 0.01}
    slope = central_difference(plus, minus, 1.0)
    assert slope["CL"] == (0.12 - 0.08) / 2.0
    assert slope["CD"] == 0.0
    assert set(slope) == set(COEFFS)


def test_blank_row_uses_null_coefficients():
    row = blank_row("rudder", 5.0, available=False, reason="datcom has no rudder namelist")
    assert row["available"] is False
    assert row["CL"] is None and row["Cn"] is None


def test_with_probe_does_not_mutate_stored_zero():
    ac = _ac()
    probed = with_probe(ac, "aileron", 5.0)
    assert ac.A["DELTAL"] == 0.0 and ac.A["DELTAR"] == 0.0
    assert ac.F["DELTA"] == 0.0
    assert probed.A["DELTAR"] == 5.0 and probed.A["DELTAL"] == -5.0
    assert probed.F["DELTA"] == 0.0
    flap = with_probe(ac, "flap", 5.0)
    assert flap.F["DELTA"] == 5.0 and ac.F["DELTA"] == 0.0
    assert deepcopy(ac.E)["DELTA"] == 0.0
