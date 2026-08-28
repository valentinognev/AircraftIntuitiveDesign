import numpy as np

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid.scale_geom import scale_aircraft


def test_scale_two_doubles_lengths_not_angles():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    savsi0 = ac.WG["SAVSI"]
    chrdr0 = ac.WG["CHRDR"]
    xcg0 = ac.AERO["XCG"]
    scale_aircraft(ac, 2.0)
    assert ac.WG["CHRDR"] == chrdr0 * 2
    assert ac.WG["SSPN"] == 12
    assert ac.WG["SAVSI"] == savsi0
    assert ac.AERO["XCG"] == xcg0 * 2
    assert float(np.asarray(ac.AERO["MACH"]).reshape(-1)[0]) == 0.03


def test_scale_factor_zero_is_noop():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    chrdr0 = ac.WG["CHRDR"]
    scale_aircraft(ac, 0)
    assert ac.WG["CHRDR"] == chrdr0
