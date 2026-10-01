from copy import deepcopy

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid.tornado.control_deriv import tornado_controls
from aid.tornado_io import tornado_io


def test_force_controls_off_matches_zero_deflection_lattice():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    geo_default, _ = tornado_io(ac, ("4", "2"))
    # Cessna stored flap/aileron deflections are zero, so the default lattice has no flap panels.
    import numpy as np

    assert float(np.sum(np.asarray(geo_default["flapped"]))) == 0.0


def test_zero_stored_angle_probe_at_five_degrees_is_finite():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    delta_before = deepcopy(ac.F["DELTA"])
    rows = tornado_controls(ac, [5.0], mesh=("4", "2"))
    flap = next(r for r in rows if r["surface"] == "flap")
    assert flap["available"] is True
    assert flap["delta_deg"] == 5.0
    assert flap["CL"] is not None and abs(flap["CL"]) < 1.0
    rudder = next(r for r in rows if r["surface"] == "rudder")
    assert rudder["available"] is True and rudder["Cn"] is not None
    assert ac.F["DELTA"] == delta_before
